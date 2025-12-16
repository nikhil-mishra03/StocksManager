import yfinance as yf

from app.core.logger_config import get_logger

logger = get_logger(__name__)


def get_company_overview(symbol: str) -> dict:
    """Fetch company overview using yfinance .get_info()."""
    ticker = yf.Ticker(symbol)
    try:
        info = ticker.get_info()
        if not info:
            logger.warning("No company overview for %s", symbol)
            return {}
        return {
            "symbol": info.get("symbol"),
            "name": info.get("shortName") or info.get("longName"),
            "currency": info.get("currency"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "pb_ratio": info.get("priceToBook"),
            "beta": info.get("beta"),
            "dividend_yield": info.get("dividendYield"),
            "profit_margin": info.get("profitMargins"),
            "return_on_equity": info.get("returnOnEquity"),
            "eps": info.get("trailingEps"),
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("Error fetching company overview for %s", symbol, exc_info=exc)
        raise


if __name__ == "__main__":
    print(get_company_overview("INFY"))