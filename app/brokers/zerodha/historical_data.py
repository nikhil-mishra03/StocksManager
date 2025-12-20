from app.brokers.zerodha.auth_token import AuthorizationToken
from app.core.config import get_config
from app.core.logger_config import get_logger
from datetime import datetime, timedelta
import requests
from app.store.db import SessionLocal
from app.store.models import HistoricalData
from app.store.models import Instrument as InstrumentModel
from typing import Optional

logger = get_logger(__name__)
session = SessionLocal()

class HistoricalDataService:
    """Gets historical data from Zerodha and saves it to database"""
    def __init__(self):
        self.settings = get_config()
        self.token = AuthorizationToken().get_token()
        self.header = {
            "Authorization": f"token {self.settings.kite_api_key}:{self.token}"
        }

    def get_historical_data(self, interval: str, from_time: Optional[datetime] = None, to_time: Optional[datetime] = None):
        """Fetch historical data for all active instruments"""
        try:
            logger.info("Fetching historical data...")
            instruments = self.get_instruments()
            logger.info(f"Found {len(instruments)} instruments. Fetching data...")
            if to_time is None:
                to_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if from_time is None:
                from_time = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d %H:%M:%S')
            for instrument in instruments:
                instrument_token = instrument.token
                historical_data = self.get_instrument_data(instrument_token, interval, from_time, to_time)
                session.add_all(historical_data)
            session.commit()
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            raise e

    def get_instrument_data(self, instrument_token: int, interval: str, from_time: str, to_time: str) -> list[HistoricalData]:
        """Write Historical Data for a stock particular instrument to DB"""
        
        # instrument_token = instrument["token"]
        url = self.settings.kite_url.strip('/')
        url = f"{url}/instruments/historical/{instrument_token}/{interval}"
        params = {
            'from': from_time,
            'to': to_time
        }
        response = requests.get(url, headers = self.header, params = params)
        data = response.json().get("data")
        if not data:
            # logger.error(f"No data found for instrument {instrument['symbol']}")
            logger.error(f"No data found for instrument {instrument_token}")
            return []
        # exists = session.query(HistoricalData).filter_by(instrument_token = instrument_token).one_or_n
        records = []
        candles = data["candles"]
        for candle in candles:
            timestamp = candle[0]
            open = candle[1]
            high = candle[2]
            low = candle[3]
            close = candle[4]
            volume = candle[5]
            record = HistoricalData(
                instrument_token = instrument_token,
                timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S%z"),
                open = open,
                high = high,
                low = low,
                close = close,
                volume = volume
            )
            # return record
            records.append(record)
        return records

    def get_instruments(self):
        # fetch all instruments inside 
        try:
            instruments = session.query(InstrumentModel).all()
            return instruments
        except Exception as e:
            logger.error(f"Error fetching instruments: {e}")
            raise e





    
    

