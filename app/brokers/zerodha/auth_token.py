# check if token is set
# if not, get token
# if yes, check if valid
# if not valid, get token
# return token
from app.core.config import Config, get_config
from app.brokers.zerodha.auth import ZerodhaAuthBroker
from app.core.logger_config import get_logger
import requests

logger = get_logger(__name__)

class AuthorizationToken:
    def __init__(self):
        self.settings = get_config()
        self.token = self.settings.kite_access_token

    
    def get_token(self):
        if not self.token:
            logger.info("Access token not found. Getting new token...")
            self.token = self.get_new_token()
            return self.token
        else:
            logger.info("Access token found. Checking validity...")
            if self.is_valid():
                return self.token
            else:
                logger.info("Access token is invalid. Getting new token...")
                self.token = self.get_new_token()
                return self.token
            
    def get_new_token(self):
        client = ZerodhaAuthBroker.get_client()
        token = client.access_token

        # persist to .env file
        from dotenv import set_key  
        set_key(".env", "KITE_ACCESS_TOKEN", token)
        self.settings.kite_access_token = token
        return token
    
    def is_valid(self):
        url = self.settings.kite_url.strip("/")
        url = f"{url}/user/profile"
        headers = {
            "Authorization": f"token {self.settings.kite_api_key}:{self.token}"
        }
        response = requests.get(url, headers = headers)
        if response.status_code == 200:
            return True
        return False




