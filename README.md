# Intelligent Stock Management

A sophisticated system leveraging Zerodha APIs and AI agents for intelligent stock analysis and automated GTT (Good Till Triggered) order management.

## 🔒 Security & Validation

Since this system handles financial commands, we prioritize safety and correctness to prevent "hallucinated" or malformed orders. 

We use **Pydantic** for rigorous schema enforcement. This ensures that every output from our AI agents adheres to a strict contract before any action is taken.

**Key Mechanisms:**
- **Strict Enums for Actions:** The `recommended_action` field is locked to a specific set of allowed values (`KEEP`, `MODIFY`, `CANCEL`, `NEW`). This prevents the agent from inventing invalid actions.
- **Type Constraints:** Fields like `confidence` are constrained (e.g., 0-100), and `buy_price` must be a valid float or null depending on the action.
- **Structured Rationale:** The agents must return structured reasoning (Fundamental vs. Technical analysis), ensuring that every decision is backed by specific data points rather than vague text.

**Example Pydantic Model (`DecisionAgentResponse`):**
```python
class DecisionAgentResponse(BaseModel):
    symbol: str
    recommended_action: Literal["KEEP", "MODIFY", "CANCEL", "NEW"]
    buy_price: float | None
    confidence: int = Field(ge=0, le=100)
    # ... strict validation ensures no hallucinations
```

## 🔄 GTT Lifecycle Management

We understand that GTT orders have a complex, asynchronous lifecycle. Our system mirrors the Zerodha GTT state machine to ensure accurate tracking and execution.

The Lifecycle states are:
1. **Active**: The order is placed and waiting in the Zerodha system. It monitors the market for the trigger price.
2. **Triggered**: The market price has hit the trigger price. The order is now sent to the exchange.
3. **Executed** (implied): Once triggered, the order eventually fills or executes at the exchange.
4. **Cancelled/Expired**: Terminal states if the user cancels or the order expires (1 year).

**Implementation Details:**
- **Synchronization:** The `GTTOrderService` (`app/brokers/zerodha/gtt.py`) periodically fetches the current state of all GTTs from Zerodha.
- **State Reconciliation:** It compares the fetched state with our local database (`GTTOrder` model) and updates the status (`active`, `triggered`, etc.) accordingly. This ensures our local decision engine always acts on the true state of the order.

## 👁️ Observability

We log agent activities and decisions using a standard logging configuration. You can see detailed logs of:
- GTT Order fetching and synchronization events.
- Agent pipeline execution steps (Fundamental -> Quant -> Decision).
- Errors and partial failures (e.g., missing data).

### ⚠️ Decision Audit Trail Status
**Current Status: NOT IMPLEMENTED**

While we have defined the `Proposal` schema in our database (`app/store/models.py`) to store elaborate decision trails (including `rationale`, `confidence`, `before_state`, `after_state`), **the logic to actively populate this table is currently missing.**

The agents currently run and return their decisions (visible in logs and API responses), but they do not yet persist these "proposals" to the `Proposal` table for long-term auditing.
