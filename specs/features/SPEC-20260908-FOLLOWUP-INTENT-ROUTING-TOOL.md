# Specification: [SPEC-20260908-FOLLOWUP-INTENT-ROUTING-TOOL]
# Deterministic Sub-Agent Follow-Up Intent Routing Tool (`route_customer_followup`)

## 1. Problem Statement & Objectives

### 1.1 Context & Motivation
Following the decentralization of sub-agent concierge coordination (`SPEC-20260908-DECENTRALIZED-SUBAGENT-COORDINATION`), sub-agents (`flight_booking_agent` and `complaint_agent`) prompt the customer: *"มีบริการอื่นใดให้ก้อย/ไอติมช่วยดูแลเพิ่มเติมอีกไหมคะ/ครับ?"*.

However, the subsequent transition (transferring to a peer agent, terminating on completion, or terminating on out-of-scope requests) still relies on the LLM's prompt generation to manually invoke `transfer_to_agent` or `terminate_call`. In real-time voice streaming:
- The LLM can output verbal filler while failing to emit the function call.
- The LLM can introduce redundant confirmation loops (*"ต้องการแจ้งเรื่องร้องเรียนใช่ไหมคะ?"*).
- The LLM can erroneously attempt cross-domain task execution itself.

### 1.2 Goals
1. Provide a single, deterministic dispatcher tool **`route_customer_followup(customer_response: str, current_agent: Optional[str] = None, tool_context: Optional[Any] = None) -> FollowupRouteResult`** for sub-agents.
2. The sub-agent invokes `route_customer_followup` immediately upon receiving the customer's answer to the concierge question.
3. The tool executes programmatic routing:
   - **Flight Request:** Sets `tool_context.actions.transfer_to_agent = "flight_booking_agent"` (if in complaint agent), or returns `CONTINUE_CURRENT_AGENT` (if in flight agent).
   - **Complaint Request:** Sets `tool_context.actions.transfer_to_agent = "complaint_agent"` (if in flight agent), or returns `CONTINUE_CURRENT_AGENT` (if in complaint agent).
   - **Completion Request:** Sets `tool_context.state["session_stage"] = "CALL_TERMINATED"`, sets `termination_reason = "SESSION_COMPLETED"`, and provides farewell message.
   - **Out-of-Scope Request:** Sets `tool_context.state["session_stage"] = "CALL_TERMINATED"`, sets `termination_reason = "OUT_OF_SCOPE_INTENT"`, and provides refusal message.

---

## 2. Data Models & Type Contracts

```python
class FollowupAction(str, Enum):
    CONTINUE_CURRENT_AGENT = "CONTINUE_CURRENT_AGENT"
    TRANSFER_TO_FLIGHT = "TRANSFER_TO_FLIGHT"
    TRANSFER_TO_COMPLAINT = "TRANSFER_TO_COMPLAINT"
    TERMINATE_SESSION_COMPLETED = "TERMINATE_SESSION_COMPLETED"
    TERMINATE_OUT_OF_SCOPE = "TERMINATE_OUT_OF_SCOPE"


class FollowupRouteResult(BaseModel):
    action: FollowupAction
    target_agent: Optional[str] = None
    farewell_message: Optional[str] = None
    message: str
```

---

## 3. Step-by-Step Implementation Plan & Test Design

### Step 1: Model Contracts
- Define `FollowupAction` and `FollowupRouteResult` in `app/models.py`.
- Unit test model validation.

### Step 2: Tool Implementation
- Implement `route_customer_followup` in `app/tools/coordination_tools.py`.
- Support keyword parsing, peer agent transfer setting via `tool_context.actions`, and state updating via `tool_context.state`.

### Step 3: Agent Integration & Server Wiring
- Bind `route_customer_followup` in `app/agent.py` to `flight_booking_agent` and `complaint_agent`.
- Update prompt instructions directing sub-agents to pass the customer's answer to `route_customer_followup`.
- Wire `route_customer_followup` in `app/server.py` `live_config.tools` and `tool_map`.

### Step 4: Unit & Property-Based Testing
- Unit tests in `tests/test_step2_tools.py` verifying all 5 `FollowupAction` branches.
- Property-based tests in `tests/test_step2_pbt.py` across generative Thai utterances.

### Step 5: Verification & Local Server Run
- Run full `pytest` suite.
- Synchronize specs and progress report.
- Start local server with uvicorn in background.
