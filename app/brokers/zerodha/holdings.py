from app.brokers.zerodha.auth_token import AuthorizationToken
from app.core.config import get_config
from app.core.logger_config import get_logger
import requests
import json


logger = get_logger(__name__)

def get_holding_snaphost():
    try:
        settings = get_config()
        auth_token = AuthorizationToken()
        token = auth_token.get_token()
        url = settings.kite_url.strip("/")
        url = f"{url}/portfolio/holdings"
        headers = {
            "Authorization": f"token {settings.kite_api_key}:{token}"
        }
        response = requests.get(url, headers = headers)
        data = response.json().get("data")
        if not data:
            logger.info("No holdings found")
            return []
        # data = json.loads(data)
        return data
    except Exception as e:
        logger.error(f"Error fetching holdings: {e}")
        raise e


    
