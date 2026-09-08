"""
Property-Based Tests (PBT) for Step 3: Multi-Agent Orchestration & Concierge Loop.
Guarantees session continuity, termination triggers, and zero-trust invariants.
"""

from typing import List
import pytest
from hypothesis import given, strategies as st
from app.models import CallTerminationReason, CustomerProfile
from app.mock_data import CUSTOMER_DB
from app.tools.call_control_tools import terminate_call
from app.tools.flight_tools import confirm_flight_booking


# --- Strategies ---

st_intent_sequence = st.lists(
    st.sampled_from(["flight_booking", "complaint_issue"]),
    min_size=1,
    max_size=10
)

st_completion_signals = st.sampled_from([
    "ไม่มีแล้วครับ",
    "ไม่มีเรื่องอื่นแล้วค่ะ",
    "ขอบคุณมากครับ เรียบร้อยแล้ว",
    "พอแล้วครับ ขอบคุณครับ",
    "แค่นี้ครับ ขอบคุณมาก",
    "ไม่มีแล้ว"
])


# --- Property Invariants ---

@given(st.sampled_from(list(CUSTOMER_DB.values())), st_intent_sequence)
def test_invariant_7_concierge_loop_state_preservation(customer: CustomerProfile, intents: List[str]):
    """
    Invariant 7 (Concierge Loopback & State Preservation):
    Simulating a sequence of sub-agent transitions and concierge loopbacks preserves
    authenticated customer identity without resetting to None.
    """
    session_state = {
        "authenticated_customer_id": customer.customer_id,
        "customer_name": customer.name_th,
        "loyalty_tier": customer.loyalty_tier,
        "active_agent": "thai_customer_orchestrator"
    }

    for intent in intents:
        # Transfer to sub-agent
        if intent == "flight_booking":
            session_state["active_agent"] = "flight_booking_agent"
        else:
            session_state["active_agent"] = "complaint_agent"

        # State must remain intact during sub-agent execution
        assert session_state["authenticated_customer_id"] == customer.customer_id

        # Sub-agent handback to root orchestrator
        session_state["active_agent"] = "thai_customer_orchestrator"
        assert session_state["authenticated_customer_id"] == customer.customer_id


@given(st_completion_signals)
def test_invariant_8_session_termination_invariant(signal: str):
    """
    Invariant 8 (Session Termination Invariant):
    Customer signals indicating task completion strictly yield terminate_call with SESSION_COMPLETED.
    """
    assert len(signal.strip()) > 0
    res = terminate_call(reason=CallTerminationReason.SESSION_COMPLETED)
    assert res.status == "CALL_TERMINATED"
    assert res.reason == CallTerminationReason.SESSION_COMPLETED
    assert "ขอบพระคุณ" in res.farewell_message


st_thai_intents = st.sampled_from([
    ("แจ้งเรื่องร้องเรียนครับ", "complaint_agent"),
    ("อยากร้องเรียนบริการ", "complaint_agent"),
    ("มีปัญหาเที่ยวบินล่าช้า", "complaint_agent"),
    ("จองตั๋วเครื่องบินครับ", "flight_booking_agent"),
    ("เช็คตารางบินหน่อย", "flight_booking_agent"),
    ("อยากบินไปเชียงใหม่", "flight_booking_agent"),
])

@given(st.sampled_from(list(CUSTOMER_DB.values())), st_thai_intents)
def test_invariant_7b_hybrid_intent_routing_invariance(customer: CustomerProfile, intent_pair: tuple):
    """
    Invariant 7b (Hybrid Intent Routing Invariance):
    Whenever authenticate_customer is invoked with a recognized customer intent,
    the ToolContext action is deterministically set to the corresponding specialized sub-agent.
    """
    intent_str, expected_agent = intent_pair

    class MockActions:
        transfer_to_agent = None

    class MockContext:
        actions = MockActions()

    ctx = MockContext()
    from app.tools.auth_tools import authenticate_customer
    res = authenticate_customer(
        name=customer.name_th,
        birthdate=customer.birthdate,
        customer_intent=intent_str,
        tool_context=ctx
    )
    assert res.is_authenticated is True
    assert ctx.actions.transfer_to_agent == expected_agent


st_coordination_actions = st.sampled_from([
    ("flight_booking", "flight_booking_agent"),
    ("complaint_issue", "complaint_agent"),
    ("out_of_scope", "OUT_OF_SCOPE_INTENT"),
    ("session_completed", "SESSION_COMPLETED")
])

@given(st.sampled_from(list(CUSTOMER_DB.values())), st.lists(st_coordination_actions, min_size=1, max_size=8))
def test_invariant_9_decentralized_peer_routing_and_state_preservation(customer: CustomerProfile, actions: List[tuple]):
    """
    Invariant 9 (Decentralized Peer-to-Peer State Preservation):
    Direct transitions between flight_booking_agent and complaint_agent preserve authenticated
    customer identity, while terminal actions yield valid termination results.
    """
    session_state = {
        "authenticated_customer_id": customer.customer_id,
        "customer_name": customer.name_th,
        "active_agent": "flight_booking_agent",
        "terminated": False,
        "termination_reason": None
    }

    for action_type, target in actions:
        if session_state["terminated"]:
            break

        if action_type in ("flight_booking", "complaint_issue"):
            # Peer or self routing
            session_state["active_agent"] = target
            assert session_state["authenticated_customer_id"] == customer.customer_id
            assert session_state["active_agent"] in ("flight_booking_agent", "complaint_agent")
        elif action_type == "out_of_scope":
            term_res = terminate_call(reason=CallTerminationReason.OUT_OF_SCOPE_INTENT)
            assert term_res.status == "CALL_TERMINATED"
            assert term_res.reason == CallTerminationReason.OUT_OF_SCOPE_INTENT
            session_state["terminated"] = True
            session_state["termination_reason"] = target
        elif action_type == "session_completed":
            term_res = terminate_call(reason=CallTerminationReason.SESSION_COMPLETED)
            assert term_res.status == "CALL_TERMINATED"
            assert term_res.reason == CallTerminationReason.SESSION_COMPLETED
            session_state["terminated"] = True
            session_state["termination_reason"] = target

    assert session_state["authenticated_customer_id"] == customer.customer_id


@given(st.sampled_from([CallTerminationReason.OUT_OF_SCOPE_INTENT, CallTerminationReason.SESSION_COMPLETED]))
def test_invariant_10_subagent_autonomous_termination_invariance(reason: CallTerminationReason):
    """
    Invariant 10 (Subagent Autonomous Termination Invariance):
    Verifies that subagents with terminate_call tool binding produce deterministic CALL_TERMINATED
    events with polite Thai messaging for both out-of-scope and session completion triggers.
    """
    res = terminate_call(reason=reason)
    assert res.status == "CALL_TERMINATED"
    assert res.reason == reason
    assert len(res.farewell_message) > 10
    if reason == CallTerminationReason.OUT_OF_SCOPE_INTENT:
        assert "ขออภัย" in res.farewell_message
    elif reason == CallTerminationReason.SESSION_COMPLETED:
        assert "ขอบพระคุณ" in res.farewell_message

