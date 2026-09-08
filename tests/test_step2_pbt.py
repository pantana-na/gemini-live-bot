"""
Property-Based Tests (PBT) for Step 2: Domain Tools & Behavioral Invariants.
Guarantees mathematical and security invariants across randomized input spaces.
"""

from datetime import timedelta
import pytest
from hypothesis import given, strategies as st, settings
from app.models import CallTerminationReason, CustomerProfile, FollowupAction
from app.mock_data import CUSTOMER_DB
from app.tools.auth_tools import authenticate_customer
from app.tools.flight_tools import search_real_flights, confirm_flight_booking
from app.tools.complaint_tools import record_customer_complaint, generate_ticket_id
from app.tools.call_control_tools import terminate_call
from app.tools.coordination_tools import route_customer_followup


# --- Strategies ---

st_thai_cities = st.sampled_from(["กรุงเทพฯ", "เชียงใหม่", "ภูเก็ต", "หาดใหญ่", "เกาะสมุย", "BKK", "CNX", "HKT"])
st_destination_cities = st.sampled_from(["โตเกียว", "โอซาก้า", "โซล", "สิงคโปร์", "ลอนดอน", "NRT", "SIN", "ICN"])
st_dates = st.dates().map(lambda d: d.isoformat())

st_arbitrary_complaints = st.tuples(
    st.text(min_size=1, max_size=50),
    st.text(min_size=1, max_size=200),
    st.text(min_size=1, max_size=30),
    st.text(min_size=1, max_size=100),
    st.sampled_from(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
)


# --- Property Invariants ---

@given(st_thai_cities, st_destination_cities, st_dates)
def test_invariant_3_top3_flight_monotonicity(dep: str, arr: str, travel_date: str):
    """
    Invariant 3 (Top 3 Monotonicity):
    For any departure and arrival input, search_real_flights always returns <= 3 results.
    """
    flights = search_real_flights(departure_city=dep, arrival_city=arr, departure_date=travel_date)
    assert len(flights) <= 3
    for f in flights:
        assert f.price_thb > 0
        assert f.departure_date == travel_date


@settings(max_examples=50)
@given(st.integers(min_value=5, max_value=50))
def test_invariant_4_ticket_id_uniqueness(count: int):
    """
    Invariant 4 (Ticket ID Pairwise Disjoint Uniqueness):
    Generating K tickets yields exactly K unique IDs.
    """
    generated_ids = [generate_ticket_id() for _ in range(count)]
    assert len(set(generated_ids)) == count


@settings(max_examples=30)
@given(
    st.sampled_from(list(CUSTOMER_DB.values())),
    st.integers(min_value=1, max_value=365)
)
def test_invariant_5_auth_monotonicity_mutated_birthdates(customer: CustomerProfile, day_delta: int):
    """
    Invariant 5 (Auth Monotonicity Gate):
    Tampering with a valid customer's birthdate (+/- day_delta) strictly returns is_authenticated=False.
    """
    tampered_dob = (customer.birthdate + timedelta(days=day_delta)).isoformat()
    res = authenticate_customer(name=customer.name_th, birthdate=tampered_dob)
    assert res.is_authenticated is False
    assert res.customer_id is None


@given(st.sampled_from(list(CallTerminationReason)))
def test_invariant_6_scope_enforcement_and_termination_invariance(reason: CallTerminationReason):
    """
    Invariant 6 (Scope Enforcement & Termination Invariance):
    Invoking terminate_call strictly outputs CALL_TERMINATED with non-empty courteous Thai message.
    """
    res = terminate_call(reason=reason)
    assert res.status == "CALL_TERMINATED"
    assert res.reason == reason
    assert len(res.farewell_message) > 10


@given(
    st.from_regex(r"^[A-Z]{2}\d{3}$"),
    st.floats(min_value=1000.0, max_value=50000.0),
    st.sampled_from(["", "   ", None])
)
def test_invariant_9_zero_trust_unauthenticated_rejection(flight_num: str, price: float, invalid_cust_id):
    """
    Invariant 9 (Zero-Trust Gate):
    confirm_flight_booking strictly rejects unauthenticated customer IDs.
    """
    with pytest.raises(ValueError):
        confirm_flight_booking(
            flight_number=flight_num,
            airline="Thai Airways",
            price_thb=price,
            customer_id=invalid_cust_id,
            passenger_name="สมชาย ใจดี"
        )


@given(st.integers(min_value=1, max_value=5))
def test_invariant_5b_deterministic_failed_attempts_state_monotonicity(num_failures: int):
    """
    Invariant 5b (Deterministic Failed Attempts State Monotonicity):
    Executing num_failures invalid authentications monotonically increments auth_fail_count.
    For any num_failures >= 3, session_stage is strictly CALL_TERMINATED.
    """
    class MockContext:
        def __init__(self):
            self.state = {}
            self.actions = type("Actions", (), {"transfer_to_agent": None})()

    ctx = MockContext()
    for attempt in range(1, num_failures + 1):
        res = authenticate_customer(
            name="คนที่ไม่เคยมีตัวตน",
            birthdate="1900-01-01",
            tool_context=ctx
        )
        assert res.is_authenticated is False
        assert ctx.state["auth_fail_count"] == attempt

    if num_failures >= 3:
        assert ctx.state["session_stage"] == "CALL_TERMINATED"
        assert ctx.state["termination_reason"] == "AUTH_FAILURE_EXCEEDED"
        assert ctx.state["is_call_active"] is False


@given(st.sampled_from(list(CUSTOMER_DB.values())), st.from_regex(r"^[A-Z]{2}\d{3}$"), st.floats(min_value=1000.0, max_value=20000.0))
def test_invariant_9b_state_identity_preservation_and_fallback(customer: CustomerProfile, flight_num: str, price: float):
    """
    Invariant 9b (State Identity Preservation & Fallback):
    For any customer profile in state, booking and complaint tools deterministically preserve
    the authenticated customer identity without requiring explicit parameters.
    """
    class MockContext:
        def __init__(self):
            self.state = {
                "customer_id": customer.customer_id,
                "customer_name": customer.name_th,
                "loyalty_tier": customer.loyalty_tier
            }

    ctx = MockContext()
    booking = confirm_flight_booking(
        flight_number=flight_num,
        airline="Thai Airways",
        price_thb=price,
        customer_id=None,
        passenger_name=None,
        tool_context=ctx
    )
    assert booking.customer_id == customer.customer_id
    assert booking.passenger_name == customer.name_th
    assert ctx.state["session_stage"] == "BOOKING_CONFIRMED"

    complaint = record_customer_complaint(
        category="delay",
        situation_overview="Delayed flight",
        incident_datetime="2026-09-08",
        customer_request="Assistance",
        customer_id=None,
        customer_name=None,
        tool_context=ctx
    )
    assert complaint.customer_id == customer.customer_id
    assert complaint.customer_name == customer.name_th
    assert ctx.state["session_stage"] == "COMPLAINT_RECORDED"


@given(
    st.sampled_from(["ไม่มีแล้วครับ", "ขอบคุณมากครับ", "พอแล้วค่ะ", "เสร็จสิ้น", "bye"]),
    st.sampled_from(["flight_booking_agent", "complaint_agent"])
)
def test_invariant_11a_followup_completion_always_terminates(completion_msg: str, agent_name: str):
    """
    Invariant 11a (Completion Invariant):
    Any message expressing completion must deterministically lead to TERMINATE_SESSION_COMPLETED
    and deactivate call across both sub-agents.
    """
    class MockContext:
        def __init__(self):
            self.state = {"is_call_active": True, "session_stage": "TASK_DONE"}

    ctx = MockContext()
    res = route_customer_followup(completion_msg, current_agent=agent_name, tool_context=ctx)
    assert res.action == FollowupAction.TERMINATE_SESSION_COMPLETED
    assert res.target_agent is None
    assert ctx.state["is_call_active"] is False
    assert ctx.state["session_stage"] == "CALL_TERMINATED"
    assert ctx.state["termination_reason"] == "SESSION_COMPLETED"


@given(
    st.sampled_from(["อยากร้องเรียนครับ", "กระเป๋าหาย", "ไฟลท์ดีเลย์ล่าช้า"]),
    st.sampled_from(["flight_booking_agent", "complaint_agent"])
)
def test_invariant_11b_complaint_routing_invariant(complaint_msg: str, agent_name: str):
    """
    Invariant 11b (Complaint Routing Invariant):
    A complaint intent from flight_booking_agent must transfer to complaint_agent.
    A complaint intent already within complaint_agent must continue without unnecessary transfer.
    """
    class MockActions:
        transfer_to_agent = None

    class MockContext:
        def __init__(self):
            self.actions = MockActions()
            self.state = {}

    ctx = MockContext()
    res = route_customer_followup(complaint_msg, current_agent=agent_name, tool_context=ctx)
    if agent_name == "flight_booking_agent":
        assert res.action == FollowupAction.TRANSFER_TO_COMPLAINT
        assert res.target_agent == "complaint_agent"
        assert ctx.actions.transfer_to_agent == "complaint_agent"
        assert ctx.state["session_stage"] == "TRANSFERRING_TO_COMPLAINT"
    else:
        assert res.action == FollowupAction.CONTINUE_CURRENT_AGENT
        assert res.target_agent is None
        assert ctx.actions.transfer_to_agent is None
        assert ctx.state["session_stage"] == "COLLECTING_COMPLAINT_DETAILS"


@given(
    st.sampled_from(["อยากจองตั๋วครับ", "เช็คเที่ยวบินไปภูเก็ต", "หาตั๋วเครื่องบิน"]),
    st.sampled_from(["flight_booking_agent", "complaint_agent"])
)
def test_invariant_11c_flight_routing_invariant(flight_msg: str, agent_name: str):
    """
    Invariant 11c (Flight Routing Invariant):
    A flight intent from complaint_agent must transfer to flight_booking_agent.
    A flight intent already within flight_booking_agent must continue without unnecessary transfer.
    """
    class MockActions:
        transfer_to_agent = None

    class MockContext:
        def __init__(self):
            self.actions = MockActions()
            self.state = {}

    ctx = MockContext()
    res = route_customer_followup(flight_msg, current_agent=agent_name, tool_context=ctx)
    if agent_name == "complaint_agent":
        assert res.action == FollowupAction.TRANSFER_TO_FLIGHT
        assert res.target_agent == "flight_booking_agent"
        assert ctx.actions.transfer_to_agent == "flight_booking_agent"
        assert ctx.state["session_stage"] == "TRANSFERRING_TO_FLIGHT"
    else:
        assert res.action == FollowupAction.CONTINUE_CURRENT_AGENT
        assert res.target_agent is None
        assert ctx.actions.transfer_to_agent is None
        assert ctx.state["session_stage"] == "COLLECTING_FLIGHT_SEARCH"


