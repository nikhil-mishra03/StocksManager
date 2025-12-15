from sqlalchemy import Boolean, CheckConstraint, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
import uuid

class Base(DeclarativeBase):
    pass

class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    exchange: Mapped[str] = mapped_column(String(32))
    token: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)

class HistoricalData(Base):
    __tablename__ = "historical_data"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    instrument_token: Mapped[int] = mapped_column(ForeignKey("instruments.token", ondelete="CASCADE"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(index=True)
    open: Mapped[float]
    high: Mapped[float]
    low: Mapped[float]
    close: Mapped[float]
    volume: Mapped[int]

class HoldingSnapshot(Base):
    __tablename__ = "holding_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    avg_price: Mapped[float] = mapped_column(nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(default=datetime.now())
    instrument: Mapped[Instrument] = relationship()
    __table_args__ = (UniqueConstraint("instrument_id", "snapshot_at"),)


class GTTOrder(Base):
    __tablename__ = "gtt_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    zerodha_id: Mapped[int] = mapped_column(unique=True, index=True)
    instrument_token: Mapped[int] = mapped_column(ForeignKey("instruments.token", ondelete="CASCADE"), nullable=False)
    trigger_price: Mapped[float]
    transaction_type: Mapped[str] = mapped_column(Enum('buy', 'sell', name='gtt_transaction_type'))
    quantity: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(Enum('active', 'triggered', 'cancelled', 'expired', 'error', name='gtt_status'))
    updated_at: Mapped[datetime]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)


class Proposal(Base):
    __tablename__ = "proposals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False)
    proposed_price: Mapped[float]
    quantity: Mapped[int] = mapped_column(Integer)
    proposal_type: Mapped[str] = mapped_column(Enum(
        "trail_stop","widen_stop","raise_target","lower_target","refresh","cancel",
        "early_buy_opportunity","risky_gtt_trigger", name="proposal_type"))
    confidence: Mapped[int] = mapped_column(Integer, CheckConstraint("confidence BETWEEN 0 AND 100"))
    before_state: Mapped[dict | None] = mapped_column(JSONB)
    after_state: Mapped[dict | None] = mapped_column(JSONB)
    rationale: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now())
    status: Mapped[str] = mapped_column(Enum("draft","applied","rejected","expired", name="proposal_status"), default="draft")
    instrument: Mapped[Instrument] = relationship()



class FundamentalAnalysis(Base):
    __tablename__ = "fundamental_analysis"
    id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), ForeignKey("instruments.symbol", ondelete="CASCADE"),unique=True, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(default=datetime.now())
    company_overview: Mapped[dict | None] = mapped_column(JSONB)
    profit_loss: Mapped[dict | None] = mapped_column(JSONB)
    balance_sheet: Mapped[dict | None] = mapped_column(JSONB)
    __table_args__ = (
        UniqueConstraint("symbol", "ingested_at"),
    )