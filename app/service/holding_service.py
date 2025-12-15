from app.brokers.zerodha.holdings import get_holding_snaphost
from langchain.tools import tool

# @tool
def get_holding_snapshot():
    """Get current Holding Snapshot from the Broker"""
    try:
        data = get_holding_snaphost()
        return data
    except Exception as e:
        raise e
    