from langchain.tools import tool
from app.service.instrument_service import get_all_instruments
from app.service.market_data import get_enriched_market_data, get_price_levels
from app.service.holding_service import get_holding_snapshot
from app.service.gtt_service import get_active_gtts_with_metrics, get_gtts_grouped_by_instrument
from fastapi.encoders import jsonable_encoder

@tool
def get_all_instruments_tool():
    """Get all instruments from the database"""
    try:
        instruments = get_all_instruments()
        return jsonable_encoder(instruments)
    except Exception as e:
        raise e
    

@tool
def get_gtts_grouped_by_instrument_tool():
    """Get all active GTT orders grouped by instrument"""
    try:
        gtts = get_gtts_grouped_by_instrument()
        return jsonable_encoder(gtts)
    except Exception as e:
        raise e
    
@tool
def get_active_gtts_with_metrics_tool():
    """Get all active GTT orders with computed metrics"""
    try:
        gtts = get_active_gtts_with_metrics()
        return jsonable_encoder(gtts)
    except Exception as e:
        raise e


@tool
def get_enriched_market_data_tool(instrument_token: int):
    """Get OHLCV data with computed technical indicators"""
    try:
        data = get_enriched_market_data(instrument_token)
        return jsonable_encoder(data)
    except Exception as e:
        raise e
    

@tool
def get_price_levels_tool(instrument_token: int):
    """Get key price levels for an instrument"""
    try:
        levels = get_price_levels(instrument_token)
        return jsonable_encoder(levels)
    except Exception as e:
        raise e

@tool
def get_holding_snapshot_tool():
    """Get current Holding Snapshot from the Broker"""
    try:
        data = get_holding_snapshot()
        return jsonable_encoder(data)
    except Exception as e:
        raise e
