from typing import Optional

from kiteconnect import KiteConnect
from  app.core.config import get_config
from app.core.logger_config import get_logger

logger = get_logger(__name__)
settings = get_config()
_client: Optional[KiteConnect] = None

class ZerodhaAuthBroker:
    @classmethod
    def get_login_url(cls) -> str:
        "Provide the URL user must visit to obtain the request token"
        global _client
        if _client is None:
            _client = KiteConnect(api_key=settings.kite_api_key)
        login_url = _client.login_url()
        return login_url
    

    @classmethod
    def establish_session(cls) -> KiteConnect:
        "Establish a session using the request token and return the client"
        global _client
        if _client is None:
            login_url = cls.get_login_url()
            logger.info(f"Please visit {login_url} to get request token.")
            request_token = input("Enter request token:")
        data = _client.generate_session(request_token, api_secret=settings.kite_api_secret)
        _client.set_access_token(data["access_token"])
        logger.info(f"Zerodha session established successfully.")
        return _client
    

    @classmethod
    def get_client(cls) -> KiteConnect:
        global _client
        if not _client:
            # raise ValueError("Zerodha session is not established.")
            logger.info("Zerodha session is not established. Establishing now...")
            _client = cls.establish_session()
        return _client
        



