import logging
import os
import ssl
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, MetaData, Table, create_engine, func, select, text
from sqlalchemy.engine import Engine


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

env_path = Path(__file__).resolve().parents[2] / "config" / ".env"
load_dotenv(env_path)


def get_engine() -> Engine:
    variables = {
        "DB_USER": os.getenv("DB_USER"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD"),
        "DB_NAME": os.getenv("DB_NAME"),
        "DB_HOST": os.getenv("DB_HOST"),
        "DB_PORT": os.getenv("DB_PORT"),
    }
    missing = [name for name, value in variables.items() if not value]

    if missing:
        raise ValueError(
            f"Variáveis ausentes em config/.env: {', '.join(missing)}"
        )

    database_url = URL.create(
        drivername="mysql+pymysql",
        username=variables["DB_USER"],
        password=variables["DB_PASSWORD"],
        host=variables["DB_HOST"],
        port=int(variables["DB_PORT"]),
        database=variables["DB_NAME"],
    )

    return create_engine(
        database_url,
        connect_args={
            "ssl": _create_ssl_context(),
            "connect_timeout": 10,
        },
        pool_pre_ping=True,
    )


def _create_ssl_context() -> ssl.SSLContext:
    ssl_mode = os.getenv("DB_SSLMODE", "require").lower()
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    if ssl_mode in {"verify_ca", "verify_identity"}:
        ca_path_value = os.getenv("DB_SSL_CA")
        if not ca_path_value:
            raise ValueError(
                "DB_SSL_CA é obrigatória para VERIFY_CA ou VERIFY_IDENTITY"
            )

        ca_path = Path(ca_path_value)
        if not ca_path.is_absolute():
            ca_path = Path(__file__).resolve().parents[2] / ca_path

        context.load_verify_locations(cafile=ca_path)
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = ssl_mode == "verify_identity"
    else:
        # Equivalente ao modo REQUIRE: usa TLS sem validar a CA/hostname.
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    return context


def load_weather_data(table_name: str, df: pd.DataFrame) -> None:
    if df.empty:
        logging.warning("DataFrame vazio. Nenhum dado será carregado.")
        return

    engine = get_engine()

    with engine.begin() as connection:
        connection.execute(text("SELECT 1"))
        df.to_sql(
            name=table_name,
            con=connection,
            if_exists="append",
            index=False,
        )

    logging.info("Dados carregados na tabela %s com sucesso!", table_name)

    with engine.connect() as connection:
        weather_table = Table(
            table_name,
            MetaData(),
            autoload_with=connection,
        )
        total = connection.execute(
            select(func.count()).select_from(weather_table)
        ).scalar_one()

    logging.info("Total de registros na tabela %s: %s", table_name, total)
