import requests
from app.core.config import get_config
from app.core.logger_config import get_logger
from datetime import datetime, timedelta

logger = get_logger(__name__)

def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0

def get_balance_sheet(symbol: str) -> dict:
    settings = get_config()
    try:
        url = settings.alphavantage_base_url.strip("/")
        token = settings.alphavantage_api_key
        params = {
            'function': 'BALANCE_SHEET',
            'symbol': symbol,
            'apikey': token
        }
        response = requests.get(url, params = params)
        data = response.json()
        bs_data = transform(data)
        return bs_data
    except Exception as e:
        logger.error(f"Error fetching balance sheet data")
        raise e

def transform(data: dict) -> dict:
    annual_reports = data['annualReports']
    bs_data = []
    try:
        logger.info("Fetching balance sheet data...")
        for annual_report in annual_reports:
            fiscalDataEnding = annual_report['fiscalDateEnding']
            # Skip reports older than 4 years
            fiscal_date = datetime.strptime(fiscalDataEnding, '%Y-%m-%d').date()
            if fiscal_date < datetime.now().date() - timedelta(days = 365*4):
                break  
            total_assets = _to_float(annual_report.get('totalAssets', 0))
            total_liabilities = _to_float(annual_report.get('totalLiabilities', 0))  
            working_capital = total_assets - total_liabilities
            current_ratio = total_assets / total_liabilities if total_liabilities !=0 else 0
            net_cash = (
                    _to_float(annual_report.get("cashAndShortTermInvestments", 0))
                    + _to_float(annual_report.get("longTermInvestments", 0))
                    - (
                        _to_float(annual_report.get("shortTermDebt", 0))
                        + _to_float(annual_report.get("currentDebt", 0))
                        + _to_float(annual_report.get("currentLongTermDebt", 0))
                        + _to_float(annual_report.get("longTermDebtNoncurrent", 0))  # note: key is Noncurrent in the payload
                    )
                )

            debt_to_equity = total_liabilities / _to_float(annual_report.get('totalShareholderEquity', 0)) if  _to_float(annual_report.get('totalShareholderEquity', 0)) !=0 else 0
            bs_data.append({
                'fiscalDataEnding': fiscalDataEnding,
                'total_assets': total_assets,
                'total_liabilities': total_liabilities,
                'working_capital': working_capital,
                'current_ratio': current_ratio,
                'net_cash': net_cash,
                'debt_to_equity': debt_to_equity,
                # 'totalShareHolderEquity': _to_float(annual_report.get('totalShareholderEquity', 0))
            })
        return bs_data
    except ValueError:
        logger.error(f"Error tranforming balance sheet data")
        raise ValueError(f"Error tranforming balance sheet data")


# delete this later. only used for testing
if __name__ == "__main__":
    print(get_balance_sheet('INFY'))



