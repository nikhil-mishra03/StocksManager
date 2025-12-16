from datetime import date, datetime, timedelta
from typing import List, Optional

import pandas as pd
import yfinance as yf

from app.core.logger_config import get_logger

logger = get_logger(__name__)


def _to_float(v: Optional[float]) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _first_match(df: pd.DataFrame, labels: list[str]) -> pd.Series:
    for label in labels:
        if label in df.index:
            return df.loc[label]
    return pd.Series([0.0] * df.shape[1], index=df.columns)


def get_profit_loss(symbol: str) -> List[dict]:
    """Fetch and transform income statement data via yfinance."""
    ticker = yf.Ticker(symbol)
    income_df = ticker.get_income_stmt(freq="yearly")
    if income_df.empty:
        logger.warning("No income statement data for %s", symbol)
        return []
    
    # for idx in income_df.index:
    #     print(f'   {idx}')

    # Filter to last ~4 years
    cutoff = date.today() - timedelta(days=365 * 4)
    income_df.columns = pd.to_datetime(income_df.columns)
    income_df = income_df.loc[:, income_df.columns.date >= cutoff]

    revenue = _first_match(income_df, ["Total Revenue", "TotalRevenue"])
    op_income = _first_match(income_df, ["Operating Income", "OperatingIncome"])
    pbt = _first_match(income_df, ["PretaxIncome", "Pretax Income Loss", "Income Before Tax"])
    net_income = _first_match(income_df, ["Net Income", "Net Income Common Stockholders", "NetIncome"])

    currency = ticker.get_info().get("currency")
    pl_data: List[dict] = []
    for col in income_df.columns:
        sales_val = _to_float(revenue.get(col, 0))
        op_val = _to_float(op_income.get(col, 0))
        pbt_val = _to_float(pbt.get(col, 0))
        net_val = _to_float(net_income.get(col, 0))
        expenses_val = sales_val - op_val
        opm_percent = (op_val / sales_val * 100) if sales_val else 0.0

        pl_data.append(
            {
                "fiscalDateEnding": col.date().isoformat(),
                "reportedCurrency": currency,
                "sales": sales_val,
                "expenses": expenses_val,
                "opm_percent": opm_percent,
                "pbt": pbt_val,
                "net_profit": net_val,
            }
        )
    return pl_data


if __name__ == "__main__":
    print(get_profit_loss("INFY.NS"))



