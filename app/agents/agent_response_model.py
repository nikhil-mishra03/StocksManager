from pydantic import BaseModel, Field
from typing import List

class QuantAgentResponse(BaseModel):
    symbol: str = Field(..., description = "Symbol of the instrument")
    current_gtt: float = Field(..., description = "Current GTT Order for the instrument")
    recommended_action: str = Field(..., description = "Recommended action for the GTT order. One of KEEP, MODIFY, CANCEL, NEW")
    buy_price: float | None = Field(None, description = "If recommended action is MODIFY, then this is the recommended buy or sell price. If recommended action is NEW, then this is the recommended buy or sell price. If recommended action is KEEP or CANCEL, then this is null.")
    rationale: str = Field(..., description = "Rationale for the recommended action")
    confidence: int = Field(..., description = "Confidence score for the recommended action. Value between 0 and 100")


class FundamentalAnalysisAgentResponse(BaseModel):
    symbol: str = Field(..., description = "Symbol of the instrument")
    recommended_action: str = Field(..., description = "Recommended action for the instrument. One of BUY, SELL, HOLD")
    buy_price: float | None = Field(None, description = "If recommended action is BUY, then this is the recommended buy price. If recommended action is SELL, then this is the recommended sell price. If recommended action is HOLD, then this is null.")
    rationale: str = Field(..., description = "Rationale for the recommended action")
    confidence: int = Field(..., description = "Confidence score for the recommended action. Value between 0 and 100")

class QuantAgentResponseList(BaseModel):
    items: List[QuantAgentResponse]

class FundamentalAnalysisAgentResponseList(BaseModel):
    items: List[FundamentalAnalysisAgentResponse]