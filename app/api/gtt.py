from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ..store import get_db_session
from ..store.models import GTTOrder as StoreGTTOrder

gtt_router = APIRouter(prefix="/api/gtt", tags=["GTT Orders"])


# Response Models
class GTTOrderResponse(BaseModel):
    """Response model for GTT Order"""
    id: int
    zerodha_id: int
    instrument_id: int
    trigger_price: float
    transaction_type: str
    order_price: float
    quantity: int
    status: str
    updated_at: datetime
    details: dict
    created_at: datetime

    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models


class GTTOrderCreateRequest(BaseModel):
    """Request model for creating GTT Order"""
    zerodha_id: int
    instrument_id: int
    trigger_price: float
    transaction_type: str  # 'buy' or 'sell'
    order_price: float
    quantity: int
    status: str = "active"
    details: dict = {}


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    status: str


# API Endpoints
@gtt_router.get("/", response_model=List[GTTOrderResponse])
async def get_all_gtts(session: Session = Depends(get_db_session)):
    """
    Get all GTT orders.
    Returns a list of GTT orders matching GTTOrderResponse schema.
    """
    gtt_orders = session.query(StoreGTTOrder).all()
    return gtt_orders


@gtt_router.get("/{gtt_id}", response_model=GTTOrderResponse)
async def get_gtt_by_id(gtt_id: int, session: Session = Depends(get_db_session)):
    """
    Get a specific GTT order by ID.
    Returns a single GTT order matching GTTOrderResponse schema.
    """
    gtt_order = session.query(StoreGTTOrder).filter(StoreGTTOrder.id == gtt_id).first()

    if not gtt_order:
        raise HTTPException(status_code=404, detail=f"GTT order with id {gtt_id} not found")

    return gtt_order


@gtt_router.post("/", response_model=GTTOrderResponse, status_code=201)
async def create_gtt(request: GTTOrderCreateRequest, session: Session = Depends(get_db_session)):
    """
    Create a new GTT order.
    Request body validated against GTTOrderCreateRequest.
    Response validated against GTTOrderResponse.
    """
    new_gtt = StoreGTTOrder(
        zerodha_id=request.zerodha_id,
        instrument_id=request.instrument_id,
        trigger_price=request.trigger_price,
        transaction_type=request.transaction_type,
        order_price=request.order_price,
        quantity=request.quantity,
        status=request.status,
        details=request.details,
        updated_at=datetime.now(),
        created_at=datetime.now()
    )

    session.add(new_gtt)
    session.commit()
    session.refresh(new_gtt)

    return new_gtt


@gtt_router.delete("/{gtt_id}", response_model=MessageResponse)
async def delete_gtt(gtt_id: int, session: Session = Depends(get_db_session)):
    """
    Delete a GTT order by ID.
    Returns a message response.
    """
    gtt_order = session.query(StoreGTTOrder).filter(StoreGTTOrder.id == gtt_id).first()

    if not gtt_order:
        raise HTTPException(status_code=404, detail=f"GTT order with id {gtt_id} not found")

    session.delete(gtt_order)
    session.commit()

    return {
        "message": f"GTT order {gtt_id} deleted successfully",
        "status": "success"
    }
