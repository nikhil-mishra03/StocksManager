from app.core.config import get_config
import requests
from datetime import datetime, timedelta
from app.core.logger_config import get_logger
# from float import float

logger = get_logger(__name__)

def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0

def get_profit_loss(symbol: str) -> dict:
    logger.info(f"Fetching profit loss data for {symbol}")
    settings = get_config()
    url = settings.alphavantage_base_url.strip("/")
    token = settings.alphavantage_api_key
    params = {
        'function': 'INCOME_STATEMENT',
        'symbol': symbol,
        'apikey': token
    }
    response = requests.get(url, params = params)
    data = response.json()
    pl_data = transform(data)
    return pl_data

def transform(data: dict) -> dict:
    annual_reports = data.get('annualReports', [])
    if not annual_reports:
        logger.error(f"Unexpected response: {data}")
        return []
    pl_data = []
    try:
        logger.info("Fetching profit loss data...")
        for annual_report in annual_reports:
            fiscalDataEnding = annual_report['fiscalDateEnding']
            # Skip reports older than 4 years
            fiscal_date = datetime.strptime(fiscalDataEnding, '%Y-%m-%d').date()
            if fiscal_date < datetime.now().date() - timedelta(days = 365*4):
                break
            
            reportedCurrency = annual_report.get('reportedCurrency', 0)
            sales = _to_float(annual_report.get('totalRevenue', 0))
            expenses = _to_float(annual_report.get('totalRevenue', 0)) - float(annual_report.get('operatingIncome',0))
            opm_percent = _to_float(annual_report.get('operatingIncome', 0)) / float(annual_report.get('totalRevenue', 1)) * 100
            pbt = _to_float(annual_report.get('incomeBeforeTax', 0))
            net_profit = _to_float(annual_report.get('netIncome', 0))
            pl_data.append({
                'fiscalDataEnding': fiscalDataEnding,
                'reportedCurrency': reportedCurrency,
                'sales': sales,
                'expenses': expenses,
                'opm_percent': opm_percent,
                'pbt': pbt,
                'net_profit': net_profit
            })
        return pl_data
    except ValueError:
        logger.error(f"Error tranforming profit loss data")
        raise ValueError(f"Error tranforming profit loss data")
    except Exception as e:
        logger.error(f"Error fetching profit loss data")
        raise e


# delete this later. only used for testing
# if __name__ == "__main__":
#     print(get_profit_loss('INFY'))




