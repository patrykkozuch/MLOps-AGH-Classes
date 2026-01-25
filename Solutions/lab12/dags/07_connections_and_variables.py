import datetime
import json
import pendulum
from airflow.providers.postgres.hooks.postgres import PostgresHook

from airflow.providers.standard.operators.python import PythonOperator, PythonVirtualenvOperator
from dotenv import load_dotenv
from airflow import DAG

load_dotenv()

POSTGRES_CONN_ID = "postgres_storage"


def get_data(data_interval_start: pendulum.DateTime) -> dict:
    from twelvedata import TDClient
    from airflow.sdk import Variable

    td = TDClient(apikey=Variable.get("TWELVEDATA_API_KEY"))

    ts = td.exchange_rate(symbol="USD/EUR", date=data_interval_start.isoformat())
    data = ts.as_json()
    return data


def save_data(data: dict) -> None:
    print("Saving the data")

    if not data:
        raise ValueError("No data received")

    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    hook.insert_rows("exchange_rates", [(data["symbol"], data["rate"])], target_fields=["symbol", "rate"])


with DAG(
    dag_id="connections_and_variables_dataset_gathering",
    schedule=datetime.timedelta(minutes=10),
    start_date=pendulum.datetime(2026, 1, 17, 19, 15, 00, tz="UTC"),
    catchup=True
) as dag:
    get_data_op = PythonVirtualenvOperator(
        task_id="get_data",
        python_callable=get_data,
        serializer="cloudpickle",
        requirements=["twelvedata", "pendulum", "lazy_object_proxy"]
    )
    save_data_op = PythonOperator(
        task_id="save_data",
        python_callable=save_data,
        op_kwargs={"data": get_data_op.output},
    )

    get_data_op >> save_data_op
