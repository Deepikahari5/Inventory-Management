import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app import models
from app.database import Base, engine, get_db
from app.exceptions import AppError
from app.routers import categories, products, suppliers
from app.schemas import HealthResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("inventory_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database connected and tables are ready")
    except SQLAlchemyError as exc:
        logger.error(
            "Database initialization failed (%s). Check the DB_* values in your .env file "
            "and make sure MySQL is running.",
            exc.__class__.__name__,
        )
    yield


app = FastAPI(
    title="Inventory Management API",
    description="Manage products, categories and suppliers using FastAPI, SQLAlchemy and MySQL.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(OperationalError)
async def database_connection_handler(request: Request, exc: OperationalError):
    logger.error("Database connection error: %s", exc.__class__.__name__)
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Database connection failed. Check that MySQL is running and the "
            "credentials in the .env file are correct."
        },
    )


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, exc: SQLAlchemyError):
    logger.error("Database error: %s", exc.__class__.__name__)
    return JSONResponse(
        status_code=500,
        content={"detail": "A database error occurred while processing the request."},
    )


app.include_router(categories.router)
app.include_router(suppliers.router)
app.include_router(products.router)


@app.get("/", tags=["Root"])
def root():
    return {"message": "Inventory Management API is running", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse, tags=["Root"])
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return HealthResponse(status="ok", database="connected")
