from kiteconnect import KiteConnect
from app.core.logger_config import get_logger
from app.core.config import get_config
from .auth import ZerodhaAuthBroker
import requests
from app.store.db import SessionLocal
from .auth_token import AuthorizationToken
from app.store.models import GTTOrder as GTTOrderModel
from app.store.models import Instrument as InstrumentModel

session = SessionLocal()
logger = get_logger(__name__)


class GTTOrderService:
    def __init__(self):
        broker = ZerodhaAuthBroker()
        token = AuthorizationToken()
        self.token = token.get_token()
        self.settings = get_config()
        self.url = self.settings.kite_url
        self.header = {
            "Authorization": f"token {self.settings.kite_api_key}:{self.token}"
        }

    def transform(self, data):
        # logger.info(data)
        gtt_order = {
            "zerodha_id": data["id"],
            "instrument_token": data["condition"]["instrument_token"],
            "trigger_price": data["condition"]["trigger_values"][0],
            "transaction_type": data["orders"][0]["transaction_type"].lower(),
            "quantity": data["orders"][0]["quantity"],
            "status": data["status"],
            "updated_at": data["updated_at"],
            "expires_at": data["expires_at"],
            "created_at": data["created_at"],
            "symbol": data["orders"][0]["tradingsymbol"],
            "exchange": data["orders"][0]["exchange"]
        }
        return gtt_order

    def get_gtts(self):
        logger.info("Fetching GTT orders...")
        url = self.url.strip("/")
        url = f"{url}/gtt/triggers"
        logger.info(f"URL ... {url}")
        try:
            response = requests.get(url, headers = self.header)
            data = response.json().get("data")
            if not data:
                logger.info("No GTT orders found.")
                return
            gtt_orders = []
            instruments = []
            instrument_cache: dict[int, InstrumentModel] = {}
            for d in data:
                gtt_data = self.transform(d)
                token = gtt_data["instrument_token"]
                logger.info(f"Token: {token}")

                # De-duplicate instruments by token (in-memory & DB check)
                if token not in instrument_cache:
                    logger.info(f"Token {token} not in instrument cache. Checking DB...")
                    inst = session.query(InstrumentModel).filter_by(token=token).one_or_none()
                    logger.info(inst)
                    if inst is None:
                        logger.info(f"Token {token} not found in DB. Adding to cache...")
                        instrument = InstrumentModel(
                            symbol=gtt_data["symbol"],
                            exchange=gtt_data["exchange"],
                            token=gtt_data["instrument_token"],
                        )
                        instrument_cache[token] = instrument
                        instruments.append(instrument)
                        logger.info(f"Adding instrument {instrument.symbol} to DB")
                        session.add(instrument)
                        session.commit()
                    else:
                        logger.info(f"Token {token} found in DB. Adding to cache...")
                        instrument_cache[token] = inst

                # Upsert GTTOrder by zerodha_id: update if exists; otherwise create
                existing_order = (
                    session.query(GTTOrderModel)
                    .filter_by(zerodha_id=gtt_data["zerodha_id"])
                    .one_or_none()
                )

                if existing_order:
                    existing_order.instrument_token = gtt_data["instrument_token"]
                    existing_order.trigger_price = gtt_data["trigger_price"]
                    existing_order.transaction_type = gtt_data["transaction_type"]
                    existing_order.quantity = gtt_data["quantity"]
                    existing_order.status = gtt_data["status"]
                    existing_order.updated_at = gtt_data["updated_at"]
                    existing_order.expires_at = gtt_data["expires_at"]
                    gtt_orders.append(existing_order)
                else:
                    new_order = GTTOrderModel(
                        zerodha_id=gtt_data["zerodha_id"],
                        instrument_token=gtt_data["instrument_token"],
                        trigger_price=gtt_data["trigger_price"],
                        transaction_type=gtt_data["transaction_type"],
                        quantity=gtt_data["quantity"],
                        status=gtt_data["status"],
                        updated_at=gtt_data["updated_at"],
                        expires_at=gtt_data["expires_at"],
                        created_at=gtt_data["created_at"],
                    )
                    session.add(new_order)
                    gtt_orders.append(new_order)

            # if instruments:
            #     session.add_all(instruments)
            #     session.commit()

            if gtt_orders:
                session.commit()

            return gtt_orders
        except Exception as e:
            logger.error(f'Error fetching GTT orders: {e}')
            raise e
        






        
        

        


