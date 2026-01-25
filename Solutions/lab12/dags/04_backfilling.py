import datetime
import os

import pandas as pd
import pendulum.time

import requests
from airflow.sdk import dag, task


def download_weather_data(date_interval_start: datetime.datetime, date_interval_end: datetime.datetime):
    """Download weather data from Open-Meteo API"""

    url = "https://historical-forecast-api.open-meteo.com/v1/forecast"
    params = {
        # New York's location
        "latitude": 40.7143,
        "longitude": -74.006,
        "start_date": date_interval_start.to_date_string(),
        "end_date": date_interval_end.to_date_string(),
        "daily": ["temperature_2m_max", "temperature_2m_min"],
        "timezone": "America/New_York",
    }
    response = requests.get(url=url, params=params)
    # Return response
    return response


def parse_response(response_data: dict):
    daily = response_data['daily']
    return dict(
        zip(
            daily['time'],
            [{'max': m, 'min': n} for m, n in zip(daily['temperature_2m_max'], daily['temperature_2m_min'])]
        )
    )


@dag(
    dag_id="new_york_weather",
    schedule=datetime.timedelta(weeks=1),
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    end_date=pendulum.datetime(2025, 1, 31, tz="UTC"),
    catchup=True
)
def new_york_weather_dag():
    @task
    def retrieve_data(logical_date: pendulum.DateTime):

        forecast = download_weather_data(
            date_interval_start=logical_date,
            date_interval_end=logical_date.add(days=6)
        )
        return parse_response(response_data=forecast.json())

    @task
    def save_as_csv(data: dict, logical_date: pendulum.DateTime):
        entries = []

        for date, record in data.items():
            entries.append({"Date": date, "Max": record['max'], "Min": record['min']})
        df = pd.DataFrame(data=entries, columns=["Date", "Max", "Min"])
        df.to_csv(os.path.dirname(__file__) + "/output/" + logical_date.to_date_string() + ".csv", index=False)

    data = retrieve_data()
    save_as_csv(data)

new_york_weather_dag()