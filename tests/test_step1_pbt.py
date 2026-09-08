"""
Property-Based Tests (PBT) for Step 1: Mathematical & Logical Invariants.
Utilizes Hypothesis to guarantee universal properties across generative input spaces.
"""

from datetime import date
from hypothesis import given, strategies as st
from app.models import (
    CustomerProfile,
    CabinClass,
    FlightOption,
    ComplaintCategory,
    ComplaintSeverity,
    ComplaintRecord,
    CallTerminationReason,
    CallTerminationResult,
)
from app.mock_data import convert_be_to_ce, normalize_name


# --- Strategies ---

st_thai_be_years = st.integers(min_value=2400, max_value=3000)
st_ce_years = st.integers(min_value=1900, max_value=2399)

st_valid_names = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Lo', 'Nd'), whitelist_characters=' '),
    min_size=1,
    max_size=50
).filter(lambda s: bool(s.strip()))

st_customer_profiles = st.builds(
    CustomerProfile,
    customer_id=st.from_regex(r"^CUST-\d{3,6}$"),
    name_th=st_valid_names,
    name_en=st_valid_names,
    birthdate=st.dates(min_value=date(1940, 1, 1), max_value=date(2025, 12, 31)),
    phone_number=st.from_regex(r"^0\d{2}-\d{3}-\d{4}$"),
    email=st.emails(),
    loyalty_tier=st.sampled_from(["Standard", "Silver", "Gold", "Platinum"])
)

st_flight_options = st.builds(
    FlightOption,
    flight_number=st.from_regex(r"^[A-Z]{2}\d{3,4}$"),
    airline=st.sampled_from(["Thai Airways", "Bangkok Airways", "AirAsia", "Nok Air"]),
    departure_city=st.sampled_from(["BKK", "DMK", "CNX", "HKT", "USM"]),
    arrival_city=st.sampled_from(["NRT", "HND", "ICN", "SIN", "LHR"]),
    departure_time=st.from_regex(r"^(0\d|1\d|2[0-3]):[0-5]\d$"),
    arrival_time=st.from_regex(r"^(0\d|1\d|2[0-3]):[0-5]\d$"),
    departure_date=st.dates().map(lambda d: d.isoformat()),
    price_thb=st.floats(min_value=0.0, max_value=200000.0, allow_nan=False, allow_infinity=False),
    cabin_class=st.sampled_from(list(CabinClass)),
    available_seats=st.integers(min_value=1, max_value=300)
)


# --- Property Invariants ---

@given(st_thai_be_years)
def test_invariant_1_be_to_ce_year_monotonicity(year: int):
    """
    Invariant 1 (B.E. Normalization):
    For all Buddhist Era years Y >= 2400, convert_be_to_ce(Y) is strictly Y - 543.
    """
    assert convert_be_to_ce(year) == year - 543


@given(st_ce_years)
def test_invariant_1b_ce_year_invariance(year: int):
    """
    Invariant 1b (C.E. Invariance):
    For all Christian Era years Y < 2400, convert_be_to_ce(Y) is strictly Y.
    """
    assert convert_be_to_ce(year) == year


@given(st_customer_profiles)
def test_invariant_2_customer_schema_lossless_roundtrip(customer: CustomerProfile):
    """
    Invariant 2 (Customer Model Lossless Round-Trip):
    For all valid customer profiles, dump and re-validate is identity:
    CustomerProfile.model_validate(c.model_dump()) == c
    """
    dumped = customer.model_dump()
    validated = CustomerProfile.model_validate(dumped)
    assert validated == customer


@given(st_flight_options)
def test_invariant_3_flight_option_lossless_roundtrip(flight: FlightOption):
    """
    Invariant 3 (Flight Option Schema Lossless Round-Trip):
    For all valid flight options, validate(dump(f)) == f.
    """
    dumped = flight.model_dump()
    validated = FlightOption.model_validate(dumped)
    assert validated == flight


@given(st.text(max_size=100))
def test_invariant_4_name_normalizer_idempotence(text: str):
    """
    Invariant 4 (Normalizer Idempotence):
    For any string S, normalize_name(normalize_name(S)) == normalize_name(S).
    """
    norm1 = normalize_name(text)
    norm2 = normalize_name(norm1)
    assert norm1 == norm2
