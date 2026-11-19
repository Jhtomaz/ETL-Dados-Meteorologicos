from datetime import timedelta
from pathlib import Path
import os
import sys

from airflow.sdk import dag, task
from dotenv import load_dotenv
from pendulum import datetime


sys.path.insert(0, "/opt/airflow/src")

from etl_dados_meteorologicos.extract_data import extract_weather_data
from etl_dados_meteorologicos.load_data import load_weather_data
from etl_dados_meteorologicos.transform_data import data_transformations


env_path = Path("/opt/airflow/config/.env")
load_dotenv(env_path)

API_KEY = os.getenv("API_KEY") or os.getenv("API_key")
URL = (
    "https://api.openweathermap.org/data/2.5/weather"
    f"?q=Sao Paulo,BR&units=metric&appid={API_KEY}"
)
TEMP_DATA_PATH = "/opt/airflow/data/temp_data.parquet"


@dag(
    dag_id="weather_pipeline",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    description="Pipeline de ETL para dados meteorológicos de São Paulo",
    schedule="0 * * * *",
    start_date=datetime(2026, 11, 19, tz="America/Sao_Paulo"),
    catchup=False,
    tags=["weather", "ETL", "OpenWeatherMap"],
)
def weather_pipeline():
    @task
    def extract():
        if not API_KEY:
            raise ValueError("API_KEY não encontrada em /opt/airflow/config/.env")
        return extract_weather_data(URL)

    @task
    def transform():
        df = data_transformations()
        df.to_parquet(TEMP_DATA_PATH, index=False)

    @task
    def load():
        import pandas as pd

        df = pd.read_parquet(TEMP_DATA_PATH)
        load_weather_data("sp_weather", df)

    extract_task = extract()
    transform_task = transform()
    load_task = load()

    extract_task >> transform_task >> load_task


weather_pipeline()
