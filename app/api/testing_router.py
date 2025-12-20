from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from ..brokers.zerodha.auth import ZerodhaAuthBroker
from ..brokers.zerodha.gtt import GTTOrderService
from ..core.logger_config import get_logger
from ..brokers.zerodha.historical_data import HistoricalDataService
from ..service.market_data import get_enriched_market_data, get_price_levels
from ..service.instrument_service import get_instrument_by_symbol
from ..service.holding_service import get_holding_snapshot
from ..agents.quant_agent import run_agent
from ..agents.fundamental_analysis_agent import run_agent as run_fundamental_analysis_agent
from ..agents.decision_agent import run_pipeline as run_decision_agent
# from app.fundamentals.fundamental_analysis import get_fundamental_analysis
from datetime import datetime, timedelta
import json

testing_router = APIRouter(prefix='/api/testing', tags=['Testing'])

logger = get_logger(__name__)

@testing_router.get('/auth')
async def test_client():
    try:
        client = ZerodhaAuthBroker().get_client()
        logger.info(client)
        return JSONResponse(status_code=200, 
                            content = {
                                'message': 'Authentication successful',
                                'status': 'success',
                                # 'client': client
                            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {e}")
    

@testing_router.get('/gtt')
async def test_gtt():
    try:
        gtt = GTTOrderService()
        data = gtt.get_gtts()
        logger.info(data)
        return JSONResponse(status_code=200,
                            content = {
                                'message': 'GTT orders fetched successfully',
                                'status': 'success',
                                # 'data': data
                            })
    except Exception as e:
        logger.error(f"Failed to fetch GTT orders: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch GTT orders: {e}")
    

@testing_router.get('/historical-data')
async def test_historical_data(
    interval: str,
    from_time: str = None,
    to_time: str = None,
):
    try:
        if not from_time:
            from_time = (datetime.now() - timedelta(days = 365)).strftime('%Y-%m-%d %H:%M:%S')
        if not to_time:
            to_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        historical_data = HistoricalDataService()
        data = historical_data.get_historical_data(interval, from_time, to_time)
        return JSONResponse(status_code=200,
                            content = {
                                'message': 'Historical data fetched successfully',
                                'status': 'success',
                                'data': data
                            })
    except Exception as e:
        logger.error(f"Failed to fetch historical data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch historical data: {e}")


@testing_router.get('/enriched-market-data')
async def test_enriched_market_data(
    instrument_symbol: str,
    from_time: str = None,
    to_time: str = None,
):
    try:
        if to_time is None:
            to_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if from_time is None:
            from_time = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d %H:%M:%S')
        instrument = get_instrument_by_symbol(instrument_symbol)
        instrument_token = instrument.token
        data = get_enriched_market_data(instrument_token, from_time, to_time)
        data = jsonable_encoder(data)
        data2 = get_price_levels(instrument_token)
        data2 = jsonable_encoder(data2)
        return JSONResponse(status_code = 200,
                            content = {
                                'message': 'Enriched market data price leve fetched successfully',
                                'status': 'success',
                                'data': data2
                            })
    except Exception as e:
        logger.error(f"Failed to fetch enriched market data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch enriched market data: {e}")
    

@testing_router.get("/holdings")
async def test_holding_snapshot():
    try:
        data = get_holding_snapshot()
        return JSONResponse(status_code = 200,
                            content = {
                                'message': 'Holding snapshot fetched successfully',
                                'status': 'success',
                                'data': data
                            })
    except Exception as e:
        logger.error(f"Failed to fetch holding snapshot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch holding snapshot: {e}")


@testing_router.get("/quant-agent-response")
async def test_quant_agent_response():
    try:
        data = run_agent()
        return JSONResponse(status_code = 200, 
                            content = {
                                'message': 'Quant agent response fetched successfully',
                                'status': 'success',
                                'data': jsonable_encoder(data)
                            })
    except Exception as e:
        logger.error(f"Failed to fetch quant agent response: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch quant agent response: {e}")


@testing_router.get('/fundamental-analysis')
async def test_fundamental_analysis(
):
    try:
        data = run_fundamental_analysis_agent()
        logger.info(data)
        return JSONResponse(status_code = 200,
                            content = {
                                'message': 'Fundamental analysis fetched successfully',
                                'status': 'success',
                                'data': jsonable_encoder(data)
                            })
    except Exception as e:
        logger.error(f"Failed to fetch fundamental analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch fundamental analysis: {e}")
    

@testing_router.get('/decision-agent-response')
async def test_decision_agent_response():
    try:
        data = run_decision_agent()
        return JSONResponse(status_code = 200,
                            content = {
                                'message': 'Decision agent response fetched successfully',
                                'status': 'success',
                                'data': jsonable_encoder(data)
                            })
    except Exception as e:
        logger.error(f"Failed to fetch decision agent response: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch decision agent response: {e}")
