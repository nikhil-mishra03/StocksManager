import requests
from app.core.config import get_config
from app.core.logger_config import get_logger

logger = get_logger(__name__)

def get_company_overview(symbol: str) -> dict:
    settings = get_config()
    try:
        url = settings.alphavantage_base_url.strip("/")
        token = settings.alphavantage_api_key
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol,
            'apikey': token
        }
        response = requests.get(url, params = params)
        data = response.json()
        return data
    except Exception as e:
        logger.error(f"Error fetching company overview data")
        raise e
