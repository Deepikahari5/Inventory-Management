import os

from dotenv import load_dotenv
from sqlalchemy.engine import URL, make_url

load_dotenv()


def get_database_url():
    direct_url = os.getenv("DATABASE_URL")
    if direct_url:
        return make_url(direct_url)

    values = {
        "DB_HOST": os.getenv("DB_HOST"),
        "DB_PORT": os.getenv("DB_PORT", "3306"),
        "DB_USER": os.getenv("DB_USER"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD", ""),
        "DB_NAME": os.getenv("DB_NAME"),
    }
    missing = [key for key in ("DB_HOST", "DB_USER", "DB_NAME") if not values[key]]
    if missing:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Copy .env.example to .env and fill in your MySQL details."
        )

    try:
        port = int(values["DB_PORT"])
    except ValueError:
        raise RuntimeError("DB_PORT must be a valid integer.")

    return URL.create(
        drivername="mysql+pymysql",
        username=values["DB_USER"],
        password=values["DB_PASSWORD"],
        host=values["DB_HOST"],
        port=port,
        database=values["DB_NAME"],
        query={"charset": "utf8mb4"},
    )


def sql_echo_enabled():
    return os.getenv("SQL_ECHO", "false").strip().lower() in {"1", "true", "yes"}
