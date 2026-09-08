"""
Unit Tests for Step 1: Data Contracts, Schemas & Mock Datastores.
Strictly verifies deterministic happy paths, boundary conditions, and Thai conversions.
"""

from datetime import date
import pytest
from pydantic import ValidationError

from app.models import (
    CustomerProfile,
    AuthResult,
    CabinClass,
    FlightOption,
    FlightBookingConfirmation,
    ComplaintRecord,
    ComplaintCategory,
    ComplaintSeverity,
    CallTerminationReason,
    CallTerminationResult,
)
from app.mock_data import (
    CUSTOMER_DB,
    MOCK_CUSTOMERS_LIST,
    convert_be_to_ce,
    normalize_thai_date,
    normalize_name,
    find_customer_by_credentials,
    get_customer_by_id,
    save_booking,
    save_complaint,
    BOOKING_LEDGER,
    COMPLAINT_STORE,
)


def test_mock_customers_count_and_uniqueness():
    """Verify that exactly 20 mock customer records exist with unique IDs and valid fields."""
    assert len(MOCK_CUSTOMERS_LIST) == 20
    assert len(CUSTOMER_DB) == 20
    
    ids = [c.customer_id for c in MOCK_CUSTOMERS_LIST]
    assert len(set(ids)) == 20  # All IDs are unique

    for c in MOCK_CUSTOMERS_LIST:
        assert c.customer_id.startswith("CUST-")
        assert len(c.name_th) > 0
        assert len(c.name_en) > 0
        assert isinstance(c.birthdate, date)
        assert len(c.phone_number) >= 9
        assert "@" in c.email
        assert c.loyalty_tier in ["Standard", "Silver", "Gold", "Platinum"]


def test_thai_be_to_ce_year_conversion():
    """Verify Buddhist Era (พ.ศ.) converts precisely to Christian Era (ค.ศ.)."""
    assert convert_be_to_ce(2533) == 1990
    assert convert_be_to_ce(2569) == 2026
    assert convert_be_to_ce(2500) == 1957
    assert convert_be_to_ce(1990) == 1990  # Already CE


def test_normalize_thai_date_formats():
    """Verify parsing of various Thai date expressions into standard date objects."""
    # ISO formats
    assert normalize_thai_date("1990-01-15") == date(1990, 1, 15)
    assert normalize_thai_date("2533-01-15") == date(1990, 1, 15)
    
    # Slash/Dash formats
    assert normalize_thai_date("15/01/2533") == date(1990, 1, 15)
    assert normalize_thai_date("20/05/1985") == date(1985, 5, 20)
    assert normalize_thai_date("15-01-1990") == date(1990, 1, 15)

    # Textual Thai formats
    assert normalize_thai_date("15 มกราคม 2533") == date(1990, 1, 15)
    assert normalize_thai_date("15 มกราคม พ.ศ. 2533") == date(1990, 1, 15)
    assert normalize_thai_date("20 พฤษภาคม 2528") == date(1985, 5, 20)
    assert normalize_thai_date("8 พ.ย. 2535") == date(1992, 11, 8)
    assert normalize_thai_date("14 กุมภาพันธ์ 2539") == date(1996, 2, 14)

    # Invalid dates
    assert normalize_thai_date("invalid date string") is None
    assert normalize_thai_date("") is None


def test_normalize_name_and_honorifics():
    """Verify title/honorific removal and whitespace normalization."""
    assert normalize_name("  สมชาย  ใจดี  ") == "สมชาย ใจดี"
    assert normalize_name("นายสมชาย ใจดี") == "สมชาย ใจดี"
    assert normalize_name("คุณ สมชาย ใจดี") == "สมชาย ใจดี"
    assert normalize_name("นางสาววรรณภา สุขสมบูรณ์") == "วรรณภา สุขสมบูรณ์"
    assert normalize_name("Mr. Somchai Jaidee") == "somchai jaidee"


def test_customer_authentication_lookup():
    """Test matching customer credentials against mock DB."""
    # Exact Thai match with B.E. text date
    cust1 = find_customer_by_credentials("สมชาย ใจดี", "15 มกราคม 2533")
    assert cust1 is not None
    assert cust1.customer_id == "CUST-001"
    assert cust1.loyalty_tier == "Gold"

    # Match with honorific and ISO B.E. date
    cust2 = find_customer_by_credentials("คุณวรรณภา สุขสมบูรณ์", "2528-05-20")
    assert cust2 is not None
    assert cust2.customer_id == "CUST-002"
    assert cust2.loyalty_tier == "Platinum"

    # Match with English Romanization
    cust3 = find_customer_by_credentials("Somchai Jaidee", "1990-01-15")
    assert cust3 is not None
    assert cust3.customer_id == "CUST-001"

    # Mismatched birthdate -> should fail
    cust_wrong_dob = find_customer_by_credentials("สมชาย ใจดี", "1995-01-15")
    assert cust_wrong_dob is None

    # Unknown name -> should fail
    cust_unknown = find_customer_by_credentials("ไม่มี ในระบบ", "1990-01-15")
    assert cust_unknown is None


def test_schema_validations_and_boundaries():
    """Verify model constraints and validation errors."""
    # Empty customer name should fail
    with pytest.raises(ValidationError):
        CustomerProfile(
            customer_id="CUST-999",
            name_th="",
            name_en="Test",
            birthdate=date(2000, 1, 1),
            phone_number="081-111-2222",
            email="test@example.com"
        )

    # Negative flight price should fail
    with pytest.raises(ValidationError):
        FlightOption(
            flight_number="TG102",
            airline="Thai Airways",
            departure_city="BKK",
            arrival_city="CNX",
            departure_time="08:00",
            arrival_time="09:15",
            departure_date="2026-09-20",
            price_thb=-500.0
        )

    # Invalid PNR length should fail
    with pytest.raises(ValidationError):
        FlightBookingConfirmation(
            booking_reference="INVALID_LONG_PNR",
            customer_id="CUST-001",
            flight_number="TG102",
            passenger_name="สมชาย ใจดี",
            total_price_thb=2450.0
        )


def test_call_termination_schema():
    """Verify CallTerminationReason and CallTerminationResult models."""
    res = CallTerminationResult(
        reason=CallTerminationReason.AUTH_FAILURE_EXCEEDED,
        farewell_message="ขออภัยเป็นอย่างยิ่งครับ ระบบขอยุติการสนทนา"
    )
    assert res.status == "CALL_TERMINATED"
    assert res.reason == CallTerminationReason.AUTH_FAILURE_EXCEEDED
    assert "ขอยุติ" in res.farewell_message


def test_persistence_stores():
    """Test saving booking confirmations and complaints."""
    booking = FlightBookingConfirmation(
        booking_reference="TH8819",
        customer_id="CUST-001",
        flight_number="TG102",
        passenger_name="สมชาย ใจดี",
        total_price_thb=2450.0
    )
    save_booking(booking)
    assert "TH8819" in BOOKING_LEDGER
    assert BOOKING_LEDGER["TH8819"].passenger_name == "สมชาย ใจดี"

    complaint = ComplaintRecord(
        ticket_id="TKT-20260907-0001",
        customer_id="CUST-001",
        customer_name="สมชาย ใจดี",
        category=ComplaintCategory.FLIGHT_DELAY,
        severity=ComplaintSeverity.HIGH,
        incident_datetime="2026-09-06 14:00",
        situation_overview="เที่ยวบินล่าช้ากว่า 3 ชั่วโมง",
        customer_request="ขอรับค่าชดเชยตามระเบียบ"
    )
    save_complaint(complaint)
    assert "TKT-20260907-0001" in COMPLAINT_STORE
    assert COMPLAINT_STORE["TKT-20260907-0001"].severity == ComplaintSeverity.HIGH
