from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from ..core.config import get_config
from ..core.logger_config import get_logger
from app.store.models import Base

logger = get_logger(__name__)

config = get_config()
DATABASE_URL = f"postgresql://{config.postgres_user}:{config.postgres_password}@{config.postgres_host}:{config.postgres_port}/{config.database_name}"

engine = create_engine(DATABASE_URL, future = True, pool_pre_ping=True)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine))

def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def db_connection():
    try:
        with engine.connect() as connection:
            return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False
    
def init_db():
    try:
        logger.info("Initializing database and creating tables if not exist...")
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

