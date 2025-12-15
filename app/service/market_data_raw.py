from app.store.models import HistoricalData as HistoricalDataModel
from app.store.db import SessionLocal
from app.core.logger_config import get_logger

logger = get_logger(__name__)
session = SessionLocal()

def get_historica_data(instrument_token: int) -> list[HistoricalDataModel]:
    try:
        data = session.query(HistoricalDataModel).filter_by(instrument_token = instrument_token).all()
        return data
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}")
        raise e
    
def get_historical_data(instrument_token: int, from_date: str) -> list[HistoricalDataModel]:
    try:
        data = session.query(HistoricalDataModel).filter_by(instrument_token = instrument_token).filter(HistoricalDataModel.timestamp >= from_date).all()
        return data
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}")
        raise e
