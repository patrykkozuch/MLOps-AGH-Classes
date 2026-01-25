import io

import pandas as pd
import pendulum
import requests
from airflow.sdk import ObjectStoragePath, dag, task

base = ObjectStoragePath("s3://nyc-taxi/", conn_id='aws_default')
base.mkdir(parents=True, exist_ok=True)


@task
def download_taxi_zones() -> pd.DataFrame:
    print("Downloading taxi zones data")

    taxi_zones_path = base / "taxi_zone_lookup.csv"

    if taxi_zones_path.exists():
        print("Taxi zones data already exists locally. Loading from storage.")
        with taxi_zones_path.open("rb") as file:
            df = pd.read_csv(file)
        return df

    print("Fetching taxi zones data from remote source")

    url = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
    resp = requests.get(url)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))

    with taxi_zones_path.open("wb") as file:
        df.to_csv(file, index=False)
        print("Taxi zones data saved to storage.")

    return df


@task
def download_taxi_data(logical_date: pendulum.DateTime) -> None:
    year = logical_date.year
    month = logical_date.month

    print(f"Downloading taxi data for {year}-{month:02}")

    taxi_data_path = base / f"yellow_tripdata_{year}-{month:02}.parquet"

    if taxi_data_path.exists():
        print("Taxi data already exists.")
        return

    print("Fetching taxi data from remote source")

    url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{year}-{month:02}.parquet"
    resp = requests.get(url)
    resp.raise_for_status()

    with taxi_data_path.open("wb") as file:
        file.write(resp.content)
        print("Taxi data saved to storage.")

@task.virtualenv(
    requirements=["polars", "s3fs", "pendulum", "lazy_object_proxy"],
    serializer="cloudpickle",
)
def process_taxi_data( storage_options: dict, logical_date: pendulum.DateTime) -> None:
    import polars as pl

    year = logical_date.year
    month = logical_date.month

    taxi_data_path = f"s3://nyc-taxi/yellow_tripdata_{year}-{month:02}.parquet"

    print("Loading taxi data...")

    df = pl.scan_parquet(taxi_data_path, storage_options=storage_options)
    df = df.with_columns(
        pl.col("tpep_pickup_datetime").dt.cast_time_unit("ms"),
        pl.col("tpep_dropoff_datetime").dt.cast_time_unit("ms"),
    )

    print("Loading taxi zones data...")

    df_taxi_zones = (
        pl.scan_csv("s3://nyc-taxi/taxi_zone_lookup.csv", storage_options=storage_options)
        .select(pl.all().name.to_lowercase())
    )

    print("Processing taxi data...")

    df_final = (
        df.select(pl.all().name.to_lowercase())
        .filter(
            (pl.col("tpep_pickup_datetime") >= pl.datetime(year, 1, 1))
            & (pl.col("tpep_pickup_datetime") <= pl.datetime(year + 1, 1, 1))
        ).cast({
            "vendorid": pl.UInt8,
            "passenger_count": pl.UInt8,
            "ratecodeid": pl.UInt8,
            "store_and_fwd_flag": pl.Categorical,
            "payment_type": pl.UInt8,
        })
        # 2. Data cleaning
        .with_columns(
            passenger_count=pl.col("passenger_count").fill_null(1),
            trip_time=(pl.col("tpep_dropoff_datetime") - pl.col("tpep_pickup_datetime")).dt.total_minutes()
        ).filter(
            pl.col("passenger_count") > 0,
            pl.col("trip_time") > 0,
            pl.col("trip_time") < 120
        ).with_columns(
            passenger_count=pl.when(pl.col("passenger_count") > 6).then(6).otherwise(pl.col("passenger_count")),
            extra=pl.col("extra").abs(),
            mta_tax=pl.col("mta_tax").abs(),
            tip_amount=pl.col("tip_amount").abs(),
            tolls_amount=pl.col("tolls_amount").abs(),
            improvement_surcharge=pl.col("improvement_surcharge").abs(),
            total_amount=pl.col("total_amount").abs(),
            congestion_surcharge=pl.col("congestion_surcharge").abs(),
            airport_fee=pl.col("airport_fee").abs(),
        ).remove(
            (pl.col("extra") > 1000)
            | (pl.col("mta_tax") > 1000)
            | (pl.col("tip_amount") > 1000)
            | (pl.col("tolls_amount") > 1000)
            | (pl.col("improvement_surcharge") > 1000)
            | (pl.col("total_amount") > 1000)
            | (pl.col("congestion_surcharge") > 1000)
            | (pl.col("airport_fee") > 1000)
            | (~pl.col("vendorid").is_in([1, 2, 6, 7]))
            | (~pl.col("ratecodeid").is_in([1, 2, 3, 4, 5, 6, 99]))
        )
        # 3. Data transformation
        .join(
            df_taxi_zones.rename({"borough": "puborough", "zone": "puzone"}), left_on="pulocationid",
            right_on="locationid"
        ).join(
            df_taxi_zones.rename({"borough": "doborough", "zone": "dozone"}), left_on="dolocationid",
            right_on="locationid"
        ).drop(
            "pulocationid", "dolocationid"
        ).with_columns(
            payment_type=pl.when(pl.col("payment_type").is_in([1, 2])).then(pl.col("payment_type")).otherwise(3),
            is_airport_ride=pl.when(pl.col("airport_fee") > 0).then(True).otherwise(False),
            is_rush_hour=pl.when(
                (
                    (
                        (pl.col("tpep_pickup_datetime").dt.time() >= pl.time(6, 30))
                        & (pl.col("tpep_pickup_datetime").dt.time() <= pl.time(9, 30))
                    )
                    |
                    (
                        (pl.col("tpep_pickup_datetime").dt.time() >= pl.time(15, 30))
                        & (pl.col("tpep_pickup_datetime").dt.time() <= pl.time(20, 0))
                    )
                )
                &
                (pl.col("tpep_pickup_datetime").dt.weekday() <= 4)
            ).then(True).otherwise(False),
        )
        # 4. Feature extraction
        .collect()
        .to_dummies(columns=["payment_type", "puborough", "doborough"])
        .lazy()
        .group_by(pl.col("tpep_pickup_datetime").dt.date().alias("date"))
        .agg(
            total_trips=pl.len(),
            airport_rides=pl.sum("is_airport_ride"),
            rush_hour_rides=pl.sum("is_rush_hour"),
            avg_fare_amount=pl.mean("fare_amount"),
            median_distance=pl.median("trip_distance"),
            sum_of_amounts=pl.sum("total_amount"),
            total_paid_by_cash=pl.when(pl.col("payment_type_1") == 1).then(pl.col("total_amount")).otherwise(0).sum(),
            total_paid_by_card=pl.when(pl.col("payment_type_2") == 1).then(pl.col("total_amount")).otherwise(0).sum(),
            total_paid_by_other=pl.when(pl.col("payment_type_3") == 1).then(pl.col("total_amount")).otherwise(0).sum(),
            total_congestion_surcharge=pl.sum("congestion_surcharge"),
            total_number_of_passengers=pl.sum("passenger_count"),
        ).with_columns(
            quarter=pl.col("date").dt.quarter().cast(pl.UInt8),
            month=pl.col("date").dt.month().cast(pl.UInt8),
            day_of_month=pl.col("date").dt.day().cast(pl.UInt8),
            day_of_week=pl.col("date").dt.weekday().cast(pl.UInt8),
            is_weekend=pl.when(pl.col("date").dt.weekday() >= 5).then(True).otherwise(False)
        ).sort("date")
        .collect()
    )


    df_final.write_parquet(
        f"s3://nyc-taxi/processed/taxi_data_summary_{year}-{month:02}.parquet",
        storage_options=storage_options
    )

    print("Processed taxi data saved to storage.")

@dag(
    dag_id="nyc_taxi_data_preparation",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    end_date=pendulum.datetime(2024, 12, 31, tz="UTC"),
    schedule="@monthly",
    catchup=True
)
def nyc_taxi_data_preparation_dag():
    download_taxi_zones()
    download_taxi_data()

    process_taxi_data(
        storage_options={
            "aws_access_key_id": "{{ conn.aws_default.login }}",
            "aws_secret_access_key": "{{ conn.aws_default.password }}",
            "endpoint_url": "{{ conn.aws_default.extra_dejson.endpoint_url }}",
            "region_name": "{{ conn.aws_default.extra_dejson.region_name }}",
        }
    )

nyc_taxi_data_preparation_dag()