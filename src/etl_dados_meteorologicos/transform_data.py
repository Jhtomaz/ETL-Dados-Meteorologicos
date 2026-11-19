import json
import logging
from pathlib import Path

import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

path_name = Path(__file__).resolve().parents[2] / "data" / "weather_data.json"
columns_names_to_drop = ["weather", "weather_icon", "sys.type"]
columns_names_to_rename = {
    "base": "base",
    "visibility": "visibility",
    "dt": "datetime",
    "timezone": "timezone",
    "id": "city_id",
    "name": "city_name",
    "cod": "code",
    "coord.lon": "longitude",
    "coord.lat": "latitude",
    "main.temp": "temperature",
    "main.feels_like": "feels_like",
    "main.temp_min": "temp_min",
    "main.temp_max": "temp_max",
    "main.pressure": "pressure",
    "main.humidity": "humidity",
    "main.sea_level": "sea_level",
    "main.grnd_level": "grnd_level",
    "wind.speed": "wind_speed",
    "wind.deg": "wind_deg",
    "wind.gust": "wind_gust",
    "clouds.all": "clouds",
    "sys.type": "sys_type",
    "sys.id": "sys_id",
    "sys.country": "country",
    "sys.sunrise": "sunrise",
    "sys.sunset": "sunset",
}
columns_to_normalize_datetime = ["datetime", "sunrise", "sunset"]


def create_dataframe(path: Path) -> pd.DataFrame:
    logging.info("Carregando dados do arquivo %s", path)

    if not path.exists():
        raise FileNotFoundError(f"O arquivo {path} não foi encontrado.")

    with path.open(encoding="utf-8") as file:
        data = json.load(file)

    df = pd.json_normalize(data)
    logging.info("DataFrame criado com %s linha(s)", len(df))
    return df


def normalize_weather_columns(df: pd.DataFrame) -> pd.DataFrame:
    df_weather = pd.json_normalize(df["weather"].apply(lambda value: value[0]))
    df_weather = df_weather.rename(
        columns={
            "id": "weather_id",
            "main": "weather_main",
            "description": "weather_description",
            "icon": "weather_icon",
        }
    )

    df = pd.concat([df, df_weather], axis=1)
    logging.info("Colunas normalizadas: %s", list(df_weather.columns))
    return df


def drop_columns(df: pd.DataFrame, column_names: list[str]) -> pd.DataFrame:
    df = df.drop(columns=column_names, errors="ignore")
    logging.info("Colunas removidas: %s colunas restantes", len(df.columns))
    return df


def rename_columns(df: pd.DataFrame, column_names: dict[str, str]) -> pd.DataFrame:
    logging.info("Renomeando %s colunas...", len(column_names))
    return df.rename(columns=column_names)


def normalize_datetime_columns(
    df: pd.DataFrame,
    column_names: list[str],
) -> pd.DataFrame:
    for name in column_names:
        df[name] = pd.to_datetime(
            df[name], unit="s", utc=True
        ).dt.tz_convert("America/Sao_Paulo")

    logging.info("Colunas de data e hora normalizadas")
    return df


def data_transformations() -> pd.DataFrame:
    print("\nIniciando transformações de dados...")
    df = create_dataframe(path_name)
    df = normalize_weather_columns(df)
    df = drop_columns(df, columns_names_to_drop)
    df = rename_columns(df, columns_names_to_rename)
    df = normalize_datetime_columns(df, columns_to_normalize_datetime)
    print("\nTransformações de dados concluídas com sucesso!")
    return df
