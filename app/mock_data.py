"""
Mock Datastores & Normalization Utilities for Gemini Live Bot.
Pre-seeds 20 Thai customer profiles and provides Thai calendar/name normalizers.
Strictly conforms to SPEC-20260907-GEMINI-LIVE-ADK-THAI-VOICE-AGENT.
"""

import re
from datetime import date, datetime
from typing import Dict, List, Optional
from app.models import CustomerProfile, FlightBookingConfirmation, ComplaintRecord


THAI_MONTHS = {
    "มกราคม": 1, "ม.ค.": 1, "ม.ค": 1, "january": 1, "jan": 1,
    "กุมภาพันธ์": 2, "ก.พ.": 2, "ก.พ": 2, "february": 2, "feb": 2,
    "มีนาคม": 3, "มี.ค.": 3, "มี.ค": 3, "march": 3, "mar": 3,
    "เมษายน": 4, "เม.ย.": 4, "เม.ย": 4, "april": 4, "apr": 4,
    "พฤษภาคม": 5, "พ.ค.": 5, "พ.ค": 5, "may": 5,
    "มิถุนายน": 6, "มิ.ย.": 6, "มิ.ย": 6, "june": 6, "jun": 6,
    "กรกฎาคม": 7, "ก.ค.": 7, "ก.ค": 7, "july": 7, "jul": 7,
    "สิงหาคม": 8, "ส.ค.": 8, "ส.ค": 8, "august": 8, "aug": 8,
    "กันยายน": 9, "ก.ย.": 9, "ก.ย": 9, "september": 9, "sep": 9, "sept": 9,
    "ตุลาคม": 10, "ต.ค.": 10, "ต.ค": 10, "october": 10, "oct": 10,
    "พฤศจิกายน": 11, "พ.ย.": 11, "พ.ย": 11, "november": 11, "nov": 11,
    "ธันวาคม": 12, "ธ.ค.": 12, "ธ.ค": 12, "december": 12, "dec": 12,
}


def convert_be_to_ce(year: int) -> int:
    """
    Converts a Buddhist Era (B.E. / พ.ศ.) year to Christian Era (C.E. / ค.ศ.).
    Invariant 1: Exact subtraction of 543 when year is in B.E. range (>= 2400).
    """
    if year >= 2400:
        return year - 543
    return year


def normalize_thai_date(date_input: str) -> Optional[date]:
    """
    Parses diverse Thai date formats into a standard date object:
    - ISO format: '1990-01-15' or '2533-01-15'
    - Slash / Dash format: '15/01/2533', '15-01-1990'
    - Textual Thai format: '15 มกราคม 2533', '15 ม.ค. 1990', '15 มกราคม พ.ศ. 2533'
    """
    if not date_input:
        return None

    if isinstance(date_input, date):
        return date_input
    
    text = str(date_input).strip()
    text = re.sub(r'(พ\.ศ\.|ค\.ศ\.|พศ|คศ)', '', text).strip()
    
    # Check ISO format YYYY-MM-DD
    iso_match = re.match(r'^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$', text)
    if iso_match:
        y, m, d = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
        y = convert_be_to_ce(y)
        try:
            return date(y, m, d)
        except ValueError:
            return None

    # Check Day-Month-Year numeric: DD/MM/YYYY or DD-MM-YYYY
    dmy_match = re.match(r'^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$', text)
    if dmy_match:
        d, m, y = int(dmy_match.group(1)), int(dmy_match.group(2)), int(dmy_match.group(3))
        y = convert_be_to_ce(y)
        try:
            return date(y, m, d)
        except ValueError:
            return None

    # Check Textual Thai: '15 มกราคม 2533' or '15 ม.ค. 1990'
    words = text.split()
    day = None
    month = None
    year = None

    for w in words:
        clean_w = w.strip().lower()
        if clean_w.isdigit():
            val = int(clean_w)
            if val > 1900:  # Year
                year = convert_be_to_ce(val)
            elif day is None and 1 <= val <= 31:
                day = val
            elif year is None and val > 31:
                year = convert_be_to_ce(val)
        elif clean_w in THAI_MONTHS:
            month = THAI_MONTHS[clean_w]

    if day and month and year:
        try:
            return date(year, month, day)
        except ValueError:
            return None

    return None


def normalize_name(name_str: str) -> str:
    """Normalizes Thai and English names by stripping titles and extra whitespace."""
    if not name_str:
        return ""
    # Strip common Thai honorifics for robust matching (longest prefixes first)
    cleaned = re.sub(r'^(นางสาว|นาง|นาย|คุณ|mr\.|ms\.|mrs\.)\s*', '', name_str.strip(), flags=re.IGNORECASE)
    # Collapse multiple whitespaces into a single space
    return re.sub(r'\s+', ' ', cleaned).strip().lower()


# 20 Pre-Seeded Realistic Thai Customer Profiles
MOCK_CUSTOMERS_LIST: List[CustomerProfile] = [
    CustomerProfile(
        customer_id="CUST-001",
        name_th="สมชาย ใจดี",
        name_en="Somchai Jaidee",
        birthdate=date(1990, 1, 15),
        phone_number="081-234-5678",
        email="somchai.j@example.com",
        loyalty_tier="Gold"
    ),
    CustomerProfile(
        customer_id="CUST-002",
        name_th="วรรณภา สุขสมบูรณ์",
        name_en="Wannapa Suksomboon",
        birthdate=date(1985, 5, 20),
        phone_number="082-345-6789",
        email="wannapa.s@example.com",
        loyalty_tier="Platinum"
    ),
    CustomerProfile(
        customer_id="CUST-003",
        name_th="กิตติศักดิ์ รัตนดิลก",
        name_en="Kittisak Rattanadilok",
        birthdate=date(1992, 11, 8),
        phone_number="089-456-7890",
        email="kittisak.r@example.com",
        loyalty_tier="Silver"
    ),
    CustomerProfile(
        customer_id="CUST-004",
        name_th="ชลธิชา พงษ์ไพโรจน์",
        name_en="Chonthicha Pongpairoj",
        birthdate=date(1998, 3, 25),
        phone_number="086-567-8901",
        email="chonthicha.p@example.com",
        loyalty_tier="Standard"
    ),
    CustomerProfile(
        customer_id="CUST-005",
        name_th="ธีรภัทร อนันตชัย",
        name_en="Theerapat Anantachai",
        birthdate=date(1979, 7, 12),
        phone_number="084-678-9012",
        email="theerapat.a@example.com",
        loyalty_tier="Platinum"
    ),
    CustomerProfile(
        customer_id="CUST-006",
        name_th="พิมพิกา อัครเดช",
        name_en="Pimpika Akkaradech",
        birthdate=date(1995, 9, 30),
        phone_number="083-789-0123",
        email="pimpika.a@example.com",
        loyalty_tier="Gold"
    ),
    CustomerProfile(
        customer_id="CUST-007",
        name_th="ณัฐพล ศิริวัฒนา",
        name_en="Nattapol Siriwatthana",
        birthdate=date(1988, 12, 5),
        phone_number="085-890-1234",
        email="nattapol.s@example.com",
        loyalty_tier="Standard"
    ),
    CustomerProfile(
        customer_id="CUST-008",
        name_th="อรวรรณ ธนบดี",
        name_en="Orawan Thanabodee",
        birthdate=date(1993, 4, 18),
        phone_number="087-901-2345",
        email="orawan.t@example.com",
        loyalty_tier="Silver"
    ),
    CustomerProfile(
        customer_id="CUST-009",
        name_th="ธนากร เจริญผล",
        name_en="Thanakorn Charoenphon",
        birthdate=date(1982, 8, 22),
        phone_number="081-012-3456",
        email="thanakorn.c@example.com",
        loyalty_tier="Gold"
    ),
    CustomerProfile(
        customer_id="CUST-010",
        name_th="รัชดาพร วงศ์สว่าง",
        name_en="Ratchadaporn Wongsawang",
        birthdate=date(1996, 2, 14),
        phone_number="088-123-4567",
        email="ratchadaporn.w@example.com",
        loyalty_tier="Standard"
    ),
    CustomerProfile(
        customer_id="CUST-011",
        name_th="สุรชัย ประเสริฐยิ่ง",
        name_en="Surachai Prasertying",
        birthdate=date(1975, 10, 3),
        phone_number="082-234-5678",
        email="surachai.p@example.com",
        loyalty_tier="Platinum"
    ),
    CustomerProfile(
        customer_id="CUST-012",
        name_th="วิลาวัลย์ เลิศปัญญา",
        name_en="Wilawan Lertpanya",
        birthdate=date(1991, 6, 28),
        phone_number="089-345-6789",
        email="wilawan.l@example.com",
        loyalty_tier="Silver"
    ),
    CustomerProfile(
        customer_id="CUST-013",
        name_th="นพรัตน์ แสนสุข",
        name_en="Nopparat Saensuk",
        birthdate=date(1987, 1, 9),
        phone_number="086-456-7890",
        email="nopparat.s@example.com",
        loyalty_tier="Standard"
    ),
    CustomerProfile(
        customer_id="CUST-014",
        name_th="สุภาภรณ์ ชัยชนะ",
        name_en="Supaporn Chaichana",
        birthdate=date(1994, 7, 19),
        phone_number="084-567-8901",
        email="supaporn.c@example.com",
        loyalty_tier="Gold"
    ),
    CustomerProfile(
        customer_id="CUST-015",
        name_th="อนุชา ศรีสุวรรณ",
        name_en="Anucha Srisuwan",
        birthdate=date(1980, 3, 11),
        phone_number="083-678-9012",
        email="anucha.s@example.com",
        loyalty_tier="Silver"
    ),
    CustomerProfile(
        customer_id="CUST-016",
        name_th="เบญจมาศ มณีโชติ",
        name_en="Benjamas Maneechot",
        birthdate=date(1999, 12, 25),
        phone_number="085-789-0123",
        email="benjamas.m@example.com",
        loyalty_tier="Standard"
    ),
    CustomerProfile(
        customer_id="CUST-017",
        name_th="ปริญญา เกียรติสกุล",
        name_en="Parinya Kiatsakul",
        birthdate=date(1984, 9, 17),
        phone_number="087-890-1234",
        email="parinya.k@example.com",
        loyalty_tier="Platinum"
    ),
    CustomerProfile(
        customer_id="CUST-018",
        name_th="กมลชนก ธรรมปรีชา",
        name_en="Kamolchanok Thampreecha",
        birthdate=date(1997, 5, 4),
        phone_number="081-901-2345",
        email="kamolchanok.t@example.com",
        loyalty_tier="Standard"
    ),
    CustomerProfile(
        customer_id="CUST-019",
        name_th="ชัชวาล เลิศรัตนชัย",
        name_en="Chatchawal Lertrattanachai",
        birthdate=date(1986, 11, 29),
        phone_number="088-012-3456",
        email="chatchawal.l@example.com",
        loyalty_tier="Gold"
    ),
    CustomerProfile(
        customer_id="CUST-020",
        name_th="มัลลิกา เจริญสุข",
        name_en="Mallika Charoensuk",
        birthdate=date(1993, 8, 7),
        phone_number="082-123-4567",
        email="mallika.c@example.com",
        loyalty_tier="Silver"
    )
]

# In-Memory Datastores
CUSTOMER_DB: Dict[str, CustomerProfile] = {c.customer_id: c for c in MOCK_CUSTOMERS_LIST}
BOOKING_LEDGER: Dict[str, FlightBookingConfirmation] = {}
COMPLAINT_STORE: Dict[str, ComplaintRecord] = {}


def find_customer_by_credentials(name_input: str, birthdate_input: str) -> Optional[CustomerProfile]:
    """
    Matches customer against mock database by Thai name (or Romanized) and parsed birthdate.
    """
    if not name_input or not birthdate_input:
        return None

    parsed_birthdate = normalize_thai_date(birthdate_input)
    if not parsed_birthdate:
        return None

    normalized_input_name = normalize_name(name_input)

    for customer in CUSTOMER_DB.values():
        if customer.birthdate == parsed_birthdate:
            norm_th = normalize_name(customer.name_th)
            norm_en = normalize_name(customer.name_en)
            if normalized_input_name == norm_th or normalized_input_name == norm_en:
                return customer
            # Also allow partial first name + last name matching
            if (norm_th in normalized_input_name or normalized_input_name in norm_th) or \
               (norm_en in normalized_input_name or normalized_input_name in norm_en):
                return customer

    return None


def get_customer_by_id(customer_id: str) -> Optional[CustomerProfile]:
    """Retrieve customer by unique customer ID."""
    return CUSTOMER_DB.get(customer_id)


def save_booking(booking: FlightBookingConfirmation) -> None:
    """Persists a confirmed flight reservation to ledger."""
    BOOKING_LEDGER[booking.booking_reference] = booking


def save_complaint(complaint: ComplaintRecord) -> None:
    """Persists a complaint ticket to store."""
    COMPLAINT_STORE[complaint.ticket_id] = complaint
