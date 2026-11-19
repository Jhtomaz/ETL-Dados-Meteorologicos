import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from etl_dados_meteorologicos.extract_data import extract_weather_data
from etl_dados_meteorologicos.load_data import load_weather_data
from etl_dados_meteorologicos.transform_data import data_transformations


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

env_path = Path(__file__).resolve().parent.parent / "config" / ".env"
load_dotenv(env_path)

# Mantém compatibilidade com o nome atual e também aceita o padrão em maiúsculas.
API_KEY = os.getenv("API_KEY") or os.getenv("API_key")
TABLE_NAME = "sp_weather"


def pipeline() -> None:
    if not API_KEY:
        raise ValueError("API_KEY não encontrada no arquivo config/.env")

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?q=Sao Paulo,BR&units=metric&appid={API_KEY}"
    )

    logging.info("ETAPA 1: EXTRACT")
    extract_weather_data(url)

    logging.info("ETAPA 2: TRANSFORM")
    df = data_transformations()

    logging.info("ETAPA 3: LOAD")
    load_weather_data(TABLE_NAME, df)

    print("\n" + "=" * 60)
    print("Pipeline concluído com sucesso!")
    print("=" * 60)


if __name__ == "__main__":
    pipeline()
