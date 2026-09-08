"""
Unit Tests for Step 2: Domain Tools & Business Logic.
Tests authenticate_customer, flight tools, complaint tools, and call termination guardrails.
"""

import pytest
from app.models import CallTerminationReason, ComplaintCategory, ComplaintSeverity, FollowupAction
from app.tools.auth_tools import authenticate_customer, check_customer_status
from app.tools.flight_tools import search_real_flights, confirm_flight_booking, normalize_city_name
from app.tools.complaint_tools import record_customer_complaint, query_complaint_status, get_sla_timeframe
from app.tools.call_control_tools import terminate_call, STANDARD_FAREWELLS
from app.tools.coordination_tools import route_customer_followup


def test_authenticate_customer_happy_path():
    """Verify successful authentication against pre-seeded customer record."""
    res = authenticate_customer(name="สมชาย ใจดี", birthdate="15 มกราคม 2533")
    assert res.is_authenticated is True
    assert res.customer_id == "CUST-001"
    assert res.customer_name == "สมชาย ใจดี"
    assert res.loyalty_tier == "Gold"
    assert "ยืนยันตัวตนสำเร็จ" in res.message


def test_authenticate_customer_with_hybrid_intent_routing():
    """Verify authenticate_customer sets ToolContext transfer action and session_stage if intent is specified."""
    class MockActions:
        transfer_to_agent = None

    class MockToolContext:
        def __init__(self):
            self.actions = MockActions()
            self.state = {}

    # Case 1: Complaint intent ("ขอเคลมเงินคืน") triggers complaint_agent transfer & stage update
    ctx_comp = MockToolContext()
    res_comp = authenticate_customer(
        name="สมชาย ใจดี",
        birthdate="15 มกราคม 2533",
        customer_intent="ขอเคลมเงินคืนจากไฟลท์ดีเลย์ครับ",
        tool_context=ctx_comp
    )
    assert res_comp.is_authenticated is True
    assert ctx_comp.actions.transfer_to_agent == "complaint_agent"
    assert ctx_comp.state["session_stage"] == "TRANSFERRING_TO_COMPLAINT"

    # Case 2: Flight intent ("เช็คเที่ยวบิน") triggers flight_booking_agent transfer & stage update
    ctx_flight = MockToolContext()
    res_flight = authenticate_customer(
        name="สมชาย ใจดี",
        birthdate="15 มกราคม 2533",
        customer_intent="อยากเช็คเที่ยวบินไปภูเก็ต",
        tool_context=ctx_flight
    )
    assert res_flight.is_authenticated is True
    assert ctx_flight.actions.transfer_to_agent == "flight_booking_agent"
    assert ctx_flight.state["session_stage"] == "TRANSFERRING_TO_FLIGHT"


def test_authenticate_customer_failure_modes():
    """Verify rejection when name or birthdate does not match."""
    res_wrong_dob = authenticate_customer(name="สมชาย ใจดี", birthdate="1995-01-15")
    assert res_wrong_dob.is_authenticated is False
    assert res_wrong_dob.customer_id is None
    assert "ไม่พบข้อมูล" in res_wrong_dob.message

    res_unknown = authenticate_customer(name="คนแปลกหน้า", birthdate="1990-01-15")
    assert res_unknown.is_authenticated is False


def test_check_customer_status():
    """Verify retrieving customer details by customer ID."""
    res = check_customer_status("CUST-002")
    assert res["status"] == "FOUND"
    assert res["customer_id"] == "CUST-002"
    assert res["name_th"] == "วรรณภา สุขสมบูรณ์"
    assert res["loyalty_tier"] == "Platinum"

    res_missing = check_customer_status("NON_EXISTENT")
    assert res_missing["status"] == "NOT_FOUND"


def test_search_real_flights_top3_limit():
    """Verify search returns at most 3 curated flight options with valid attributes."""
    flights = search_real_flights(
        departure_city="กรุงเทพฯ",
        arrival_city="เชียงใหม่",
        departure_date="2026-09-20"
    )
    assert 0 < len(flights) <= 3
    for f in flights:
        assert len(f.flight_number) >= 4
        assert f.price_thb > 0
        assert "BKK" in f.departure_city or "DMK" in f.departure_city
        assert "CNX" in f.arrival_city


def test_confirm_flight_booking_success():
    """Verify confirmed reservation generates 6-character PNR code."""
    booking = confirm_flight_booking(
        flight_number="TG102",
        airline="Thai Airways",
        price_thb=2850.0,
        customer_id="CUST-001",
        passenger_name="สมชาย ใจดี"
    )
    assert len(booking.booking_reference) == 6
    assert booking.booking_reference.startswith("TH")
    assert booking.booking_status == "CONFIRMED"
    assert booking.customer_id == "CUST-001"


def test_confirm_flight_booking_zero_trust_unauthenticated_rejection():
    """Invariant 9: Unauthenticated sessions (missing customer_id) must fail safe."""
    with pytest.raises(ValueError, match="unauthenticated"):
        confirm_flight_booking(
            flight_number="TG102",
            airline="Thai Airways",
            price_thb=2850.0,
            customer_id="",
            passenger_name="สมชาย ใจดี"
        )


def test_record_and_query_complaint():
    """Verify ticket creation with TKT format, SLA estimation, and status retrieval."""
    rec = record_customer_complaint(
        category="กระเป๋าหาย",
        situation_overview="กระเป๋าไม่มากับสายพานหลังลงเครื่อง",
        incident_datetime="2026-09-07 19:30",
        customer_request="ติดตามกระเป๋าและนำส่งที่โรงแรม",
        severity="HIGH",
        customer_id="CUST-001",
        customer_name="สมชาย ใจดี"
    )
    assert rec.ticket_id.startswith("TKT-")
    assert rec.category == ComplaintCategory.LOST_BAGGAGE
    assert rec.severity == ComplaintSeverity.HIGH

    # Query status
    status_info = query_complaint_status(rec.ticket_id)
    assert status_info["status"] == "FOUND"
    assert status_info["ticket_id"] == rec.ticket_id
    assert "24 ชั่วโมง" in status_info["sla"]


def test_terminate_call_auth_failure_exceeded():
    """Guardrail 1A: Terminate call on 3 auth failures with polite security notice."""
    res = terminate_call(reason=CallTerminationReason.AUTH_FAILURE_EXCEEDED)
    assert res.status == "CALL_TERMINATED"
    assert res.reason == CallTerminationReason.AUTH_FAILURE_EXCEEDED
    assert "3 ครั้ง" in res.farewell_message
    assert "เพื่อความปลอดภัย" in res.farewell_message


def test_terminate_call_out_of_scope_intent():
    """Guardrail 1B: Terminate call on unauthorized / out-of-scope query with polite refusal."""
    res = terminate_call(reason="OUT_OF_SCOPE_INTENT")
    assert res.status == "CALL_TERMINATED"
    assert res.reason == CallTerminationReason.OUT_OF_SCOPE_INTENT
    assert "รองรับเฉพาะบริการสำรองที่นั่งตั๋วเครื่องบินและรับเรื่องร้องเรียนเท่านั้น" in res.farewell_message


def test_terminate_call_session_completed():
    """Guardrail 2: Terminate call on completion ('ไม่มีแล้ว') with warm farewell."""
    res = terminate_call(reason=CallTerminationReason.SESSION_COMPLETED)
    assert res.status == "CALL_TERMINATED"
    assert res.reason == CallTerminationReason.SESSION_COMPLETED
    assert "ขอบพระคุณ" in res.farewell_message
    assert "เดินทางโดยสวัสดิภาพ" in res.farewell_message


def test_tool_return_json_serializability_for_live_websocket():
    """Verify all tool return models serialize cleanly with json.dumps (no TypeError datetime)."""
    import json
    from google.genai import _common

    # 1. ComplaintRecord
    rec = record_customer_complaint(
        category="delay",
        situation_overview="Flight delayed 4 hours",
        incident_datetime="2026-09-08 10:00",
        customer_request="Hotel voucher",
        severity="MEDIUM",
        customer_id="CUST-001",
        customer_name="สมชาย ใจดี"
    )
    converted_complaint = _common.convert_to_dict({"result": rec}, convert_keys=True)
    serialized_complaint = json.dumps({"tool_response": converted_complaint})
    assert "ticket_id" in serialized_complaint
    assert "sla_timeframe" in serialized_complaint

    # 2. FlightBookingConfirmation
    booking = confirm_flight_booking(
        flight_number="TG102",
        airline="Thai Airways",
        price_thb=2850.0,
        customer_id="CUST-001",
        passenger_name="สมชาย ใจดี"
    )
    converted_booking = _common.convert_to_dict({"result": booking}, convert_keys=True)
    serialized_booking = json.dumps({"tool_response": converted_booking})
    assert "booking_reference" in serialized_booking


def test_authenticate_customer_deterministic_failed_attempts_counter():
    """Verify tool_context.state accurately tracks consecutive failed attempts and transitions to terminal state on 3rd attempt."""
    class MockContext:
        def __init__(self):
            self.state = {}
            self.actions = type("Actions", (), {"transfer_to_agent": None})()

    ctx = MockContext()
    # Attempt 1: Failed
    r1 = authenticate_customer(name="สมชาย ใจดี", birthdate="1999-01-01", tool_context=ctx)
    assert r1.is_authenticated is False
    assert ctx.state["auth_fail_count"] == 1

    # Attempt 2: Failed
    r2 = authenticate_customer(name="สมชาย ใจดี", birthdate="1999-01-01", tool_context=ctx)
    assert r2.is_authenticated is False
    assert ctx.state["auth_fail_count"] == 2

    # Attempt 3: Failed -> Terminal state reached
    r3 = authenticate_customer(name="สมชาย ใจดี", birthdate="1999-01-01", tool_context=ctx)
    assert r3.is_authenticated is False
    assert ctx.state["auth_fail_count"] == 3
    assert ctx.state["session_stage"] == "CALL_TERMINATED"
    assert ctx.state["termination_reason"] == "AUTH_FAILURE_EXCEEDED"
    assert ctx.state["is_call_active"] is False
    assert "ครบ 3 ครั้ง" in r3.message

    # Attempt 4: Success resets counter and ingests customer profile
    r4 = authenticate_customer(name="สมชาย ใจดี", birthdate="15 มกราคม 2533", tool_context=ctx)
    assert r4.is_authenticated is True
    assert ctx.state["auth_fail_count"] == 0
    assert ctx.state["is_authenticated"] is True
    assert ctx.state["customer_id"] == "CUST-001"
    assert ctx.state["customer_name"] == "สมชาย ใจดี"
    assert ctx.state["loyalty_tier"] == "Gold"
    assert ctx.state["session_stage"] == "AUTHENTICATED"


def test_confirm_flight_booking_deterministic_identity_fallback():
    """Verify confirm_flight_booking falls back to tool_context.state identity when arguments are None."""
    class MockContext:
        def __init__(self):
            self.state = {
                "customer_id": "CUST-002",
                "customer_name": "วรรณภา สุขสมบูรณ์"
            }

    ctx = MockContext()
    booking = confirm_flight_booking(
        flight_number="TG201",
        airline="Thai Airways",
        price_thb=3500.0,
        customer_id=None,
        passenger_name=None,
        tool_context=ctx
    )
    assert booking.customer_id == "CUST-002"
    assert booking.passenger_name == "วรรณภา สุขสมบูรณ์"
    assert ctx.state["session_stage"] == "BOOKING_CONFIRMED"
    assert ctx.state["last_booking_pnr"] == booking.booking_reference


def test_record_customer_complaint_deterministic_identity_fallback():
    """Verify record_customer_complaint falls back to tool_context.state identity when arguments are None."""
    class MockContext:
        def __init__(self):
            self.state = {
                "customer_id": "CUST-003",
                "customer_name": "กิตติศักดิ์ รัตนดิลก"
            }

    ctx = MockContext()
    rec = record_customer_complaint(
        category="กระเป๋าหาย",
        situation_overview="Luggage left in Tokyo",
        incident_datetime="2026-09-08",
        customer_request="Locate luggage",
        customer_id=None,
        customer_name=None,
        tool_context=ctx
    )
    assert rec.customer_id == "CUST-003"
    assert rec.customer_name == "กิตติศักดิ์ รัตนดิลก"
    assert ctx.state["session_stage"] == "COMPLAINT_RECORDED"
    assert ctx.state["last_ticket_id"] == rec.ticket_id


def test_terminate_call_and_search_stage_mutation():
    """Verify terminate_call and search_real_flights mutate tool_context.state accurately."""
    class MockContext:
        def __init__(self):
            self.state = {}

    ctx = MockContext()
    search_real_flights(
        departure_city="BKK",
        arrival_city="CNX",
        departure_date="2026-09-20",
        tool_context=ctx
    )
    assert ctx.state["session_stage"] == "FLIGHT_SEARCHED"

    terminate_call(reason=CallTerminationReason.SESSION_COMPLETED, tool_context=ctx)
    assert ctx.state["session_stage"] == "CALL_TERMINATED"
    assert ctx.state["termination_reason"] == "SESSION_COMPLETED"
    assert ctx.state["is_call_active"] is False


def test_route_customer_followup_completion():
    """Verify customer completion intent terminates session and updates tool_context."""
    class MockContext:
        def __init__(self):
            self.state = {}

    ctx = MockContext()
    res = route_customer_followup("ไม่มีอะไรแล้วครับ ขอบคุณมาก", current_agent="flight_booking_agent", tool_context=ctx)
    assert res.action == FollowupAction.TERMINATE_SESSION_COMPLETED
    assert res.target_agent is None
    assert "ขอบพระคุณ" in res.farewell_or_transition_message
    assert ctx.state["session_stage"] == "CALL_TERMINATED"
    assert ctx.state["termination_reason"] == "SESSION_COMPLETED"
    assert ctx.state["is_call_active"] is False


def test_route_customer_followup_transfer_to_complaint():
    """Verify complaint intent in flight_booking_agent triggers transfer to complaint_agent."""
    class MockActions:
        transfer_to_agent = None

    class MockContext:
        def __init__(self):
            self.actions = MockActions()
            self.state = {}

    ctx = MockContext()
    res = route_customer_followup("อยากร้องเรียนเรื่องกระเป๋าหายครับ", current_agent="flight_booking_agent", tool_context=ctx)
    assert res.action == FollowupAction.TRANSFER_TO_COMPLAINT
    assert res.target_agent == "complaint_agent"
    assert ctx.actions.transfer_to_agent == "complaint_agent"
    assert ctx.state["session_stage"] == "TRANSFERRING_TO_COMPLAINT"


def test_route_customer_followup_transfer_to_flight():
    """Verify flight intent in complaint_agent triggers transfer to flight_booking_agent."""
    class MockActions:
        transfer_to_agent = None

    class MockContext:
        def __init__(self):
            self.actions = MockActions()
            self.state = {}

    ctx = MockContext()
    res = route_customer_followup("อยากจองตั๋วเครื่องบินไปเชียงใหม่ครับ", current_agent="complaint_agent", tool_context=ctx)
    assert res.action == FollowupAction.TRANSFER_TO_FLIGHT
    assert res.target_agent == "flight_booking_agent"
    assert ctx.actions.transfer_to_agent == "flight_booking_agent"
    assert ctx.state["session_stage"] == "TRANSFERRING_TO_FLIGHT"


def test_route_customer_followup_continue_same_agent():
    """Verify same-domain requests continue within current agent without unnecessary transfer."""
    class MockActions:
        transfer_to_agent = None

    class MockContext:
        def __init__(self):
            self.actions = MockActions()
            self.state = {}

    # In flight_booking_agent, asking for another flight
    ctx1 = MockContext()
    res1 = route_customer_followup("อยากจองตั๋วเพิ่มอีกใบไปภูเก็ตครับ", current_agent="flight_booking_agent", tool_context=ctx1)
    assert res1.action == FollowupAction.CONTINUE_CURRENT_AGENT
    assert res1.target_agent is None
    assert ctx1.actions.transfer_to_agent is None
    assert ctx1.state["session_stage"] == "COLLECTING_FLIGHT_SEARCH"

    # In complaint_agent, asking for another complaint
    ctx2 = MockContext()
    res2 = route_customer_followup("อยากร้องเรียนการบริการของเจ้าหน้าที่ด้วยครับ", current_agent="complaint_agent", tool_context=ctx2)
    assert res2.action == FollowupAction.CONTINUE_CURRENT_AGENT
    assert res2.target_agent is None
    assert ctx2.actions.transfer_to_agent is None
    assert ctx2.state["session_stage"] == "COLLECTING_COMPLAINT_DETAILS"


def test_route_customer_followup_out_of_scope():
    """Verify out-of-scope query terminates session gracefully."""
    class MockContext:
        def __init__(self):
            self.state = {}

    ctx = MockContext()
    res = route_customer_followup("ช่วยแนะนำร้านอาหารอร่อยๆ แถวสยามหน่อยครับ", current_agent="flight_booking_agent", tool_context=ctx)
    assert res.action == FollowupAction.TERMINATE_OUT_OF_SCOPE
    assert res.target_agent is None
    assert "รองรับเฉพาะบริการสำรองที่นั่งตั๋วเครื่องบินและรับเรื่องร้องเรียนเท่านั้น" in res.farewell_or_transition_message
    assert ctx.state["session_stage"] == "CALL_TERMINATED"
    assert ctx.state["termination_reason"] == "OUT_OF_SCOPE_INTENT"
    assert ctx.state["is_call_active"] is False


def test_route_customer_followup_clarification():
    """Verify vague queries trigger clarification prompt."""
    res = route_customer_followup("มีบริการอะไรบ้างครับ", current_agent="complaint_agent")
    assert res.action == FollowupAction.REQUEST_CLARIFICATION
    assert res.target_agent is None
    assert "ทางเรามีบริการค้นหาและสำรองที่นั่งเที่ยวบิน" in res.farewell_or_transition_message



