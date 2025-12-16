from datetime import date, timedelta
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


def get_balance_sheet(symbol: str) -> List[dict]:
    """Fetch and transform balance sheet data via yfinance."""
    ticker = yf.Ticker(symbol)
    bs_df = ticker.get_balance_sheet(freq="yearly")
    if bs_df.empty:
        logger.warning("No balance sheet data for %s", symbol)
        return []
    # logger.info(bs_df).index

    cutoff = date.today() - timedelta(days=365 * 4)
    bs_df.columns = pd.to_datetime(bs_df.columns)
    bs_df = bs_df.loc[:, bs_df.columns.date >= cutoff]

    # yfinance returns camelCase field names (no spaces)
    total_assets = _first_match(bs_df, ["TotalAssets", "Total Assets"])
    total_liabilities = _first_match(bs_df, ["TotalLiabilitiesNetMinorityInterest", "Total Liabilities Net Minority Interest", "Total Liabilities"])
    current_assets = _first_match(bs_df, ["CurrentAssets", "Total Current Assets"])
    current_liabilities = _first_match(bs_df, ["CurrentLiabilities", "Total Current Liabilities"])
    cash_sti = _first_match(bs_df, ["CashCashEquivalentsAndShortTermInvestments", "CashAndCashEquivalents", "Cash And Short Term Investments", "Cash And Cash Equivalents"])
    lt_investments = _first_match(bs_df, ["InvestmentsAndAdvances", "LongTermInvestments", "Long Term Investments", "OtherInvestments"])
    short_term_debt = _first_match(bs_df, ["CurrentDebtAndCapitalLeaseObligation", "ShortLongTermDebtTotal", "Short Long Term Debt Total", "Short Term Debt"])
    current_debt = _first_match(bs_df, ["CurrentDebtAndCapitalLeaseObligation", "CurrentDebt", "Current Debt", "CurrentPortionOfLongTermDebt"])
    long_term_debt = _first_match(bs_df, ["LongTermDebtAndCapitalLeaseObligation", "LongTermDebt", "Long Term Debt", "Long Term Debt Noncurrent"])
    equity = _first_match(bs_df, ["TotalEquityGrossMinorityInterest", "StockholdersEquity", "CommonStockEquity", "Total Equity Gross Minority Interest", "Total Stockholder Equity"])
    net_receivables = _first_match(bs_df, ["Receivables", "AccountsReceivable", "Current Net Receivables"])

    currency = ticker.get_info().get("currency")
    bs_data: List[dict] = []
    for col in bs_df.columns:
        ta = _to_float(total_assets.get(col, 0))
        tl = _to_float(total_liabilities.get(col, 0))
        ca = _to_float(current_assets.get(col, 0))
        cl = _to_float(current_liabilities.get(col, 0))
        cash = _to_float(cash_sti.get(col, 0))
        lti = _to_float(lt_investments.get(col, 0))
        std = _to_float(short_term_debt.get(col, 0))
        cd = _to_float(current_debt.get(col, 0))
        ltd = _to_float(long_term_debt.get(col, 0))
        eq = _to_float(equity.get(col, 0))

        nr = _to_float(net_receivables.get(col, 0))

        working_capital = ca - cl
        current_ratio = (ca / cl) if cl else 0.0
        net_cash = cash + lti - (std + cd + ltd)
        debt_to_equity = (tl / eq) if eq else 0.0
        quick_ratio = ((cash + nr) / cl) if cl else 0.0

        bs_data.append(
            {
                "fiscalDateEnding": col.date().isoformat(),
                "reportedCurrency": currency,
                "total_assets": ta,
                "total_liabilities": tl,
                "working_capital": working_capital,
                "current_ratio": current_ratio,
                "net_cash": net_cash,
                "debt_to_equity": debt_to_equity,
                "quick_ratio": quick_ratio,
            }
        )
    return bs_data


if __name__ == "__main__":
    print(get_balance_sheet("INFY"))


