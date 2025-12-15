from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from app.store import get_db_session, connect_db_session, SessionLocal
from contextlib import asynccontextmanager
from app.core.logger_config import get_logger
from sqlalchemy.orm import Session
from app.core.config import get_config
from app.api.testing_router import testing_router

import uvicorn

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On application startup, verify database connection
    if not connect_db_session():
        logger.error("Database connection failed during startup.")
        raise RuntimeError("Failed to connect to the database.")
    logger.info("Database connection established successfully.")

    # When the application is shutting down - whether normally or due to an error, clear the db connection pool
    try:
        yield
    finally:
        SessionLocal.remove()
        logger.info("Shutting down application.")


app = FastAPI(lifespan = lifespan)
app.include_router(testing_router)
@app.get("/")
async def root():
    return {"message": "Intelligent Stock Management System is running."}

@app.get("/health")
async def health_check(session: Session = Depends(get_db_session)):
    session.execute("SELECT 1")      
    return {"status": "healthy", "mode": get_config().application_mode}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8008,
        reload=True,
    )
