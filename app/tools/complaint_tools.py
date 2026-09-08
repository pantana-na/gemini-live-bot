"""
Complaint Logging & Grievance Care Tools.
Strictly conforms to SPEC-20260907-GEMINI-LIVE-ADK-THAI-VOICE-AGENT.
"""

import random
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.models import ComplaintRecord, ComplaintCategory, ComplaintSeverity
from app.mock_data import save_complaint, COMPLAINT_STORE


CATEGORY_MAP = {
    "delay": ComplaintCategory.FLIGHT_DELAY,
    "ล่าช้า": ComplaintCategory.FLIGHT_DELAY,
    "ดีเลย์": ComplaintCategory.FLIGHT_DELAY,
    "baggage": ComplaintCategory.LOST_BAGGAGE,
    "กระเป๋า": ComplaintCategory.LOST_BAGGAGE,
    "สัมภาระ": ComplaintCategory.LOST_BAGGAGE,
    "inflight": ComplaintCategory.INFLIGHT_SERVICE,
    "บริการบนเครื่อง": ComplaintCategory.INFLIGHT_SERVICE,
    "อาหาร": ComplaintCategory.INFLIGHT_SERVICE,
    "ticket": ComplaintCategory.TICKETING_REFUND,
    "ตั๋ว": ComplaintCategory.TICKETING_REFUND,
    "คืนเงิน": ComplaintCategory.TICKETING_REFUND,
    "ground": ComplaintCategory.GROUND_STAFF,
    "ภาคพื้น": ComplaintCategory.GROUND_STAFF,
    "เคาน์เตอร์": ComplaintCategory.GROUND_STAFF,
}


def parse_category(category_str: str) -> ComplaintCategory:
    """Matches text or keyword to ComplaintCategory enum."""
    clean = category_str.strip().lower()
    for kw, cat in CATEGORY_MAP.items():
        if kw in clean:
            return cat
    try:
        return ComplaintCategory(category_str)
    except ValueError:
        return ComplaintCategory.OTHER


def parse_severity(severity_str: str) -> ComplaintSeverity:
    """Matches text or keyword to ComplaintSeverity enum."""
    clean = severity_str.strip().upper()
    try:
        return ComplaintSeverity(clean)
    except ValueError:
        return ComplaintSeverity.MEDIUM


def generate_ticket_id() -> str:
    """Generates unique ticket code formatted as TKT-YYYYMMDD-XXXX."""
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    rand_suffix = f"{random.randint(1000, 9999)}"
    return f"TKT-{date_part}-{rand_suffix}"


def get_sla_timeframe(severity: ComplaintSeverity) -> str:
    """Returns resolution SLA notice in Thai based on severity."""
    if severity == ComplaintSeverity.CRITICAL:
        return "ภายใน 6 - 12 ชั่วโมง (กรณีเร่งด่วนที่สุด)"
    elif severity == ComplaintSeverity.HIGH:
        return "ภายใน 24 ชั่วโมง"
    return "ภายใน 24 - 48 ชั่วโมงทำการ"


def record_customer_complaint(
    category: str,
    situation_overview: str,
    incident_datetime: str,
    customer_request: str,
    severity: str = "MEDIUM",
    customer_id: Optional[str] = None,
    customer_name: Optional[str] = None,
    tool_context: Optional[Any] = None,
) -> ComplaintRecord:
    """
    Records a customer grievance into the airline customer care system.
    
    Args:
        category: Grievance classification (e.g. 'ความล่าช้าของเที่ยวบิน', 'กระเป๋าหาย').
        situation_overview: Summary of what occurred.
        incident_datetime: Date and time when the incident took place.
        customer_request: Desired resolution requested by the passenger.
        severity: Priority level ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'). Default 'MEDIUM'.
        customer_id: Optional authenticated customer ID (falls back to tool_context.state).
        customer_name: Optional passenger name (falls back to tool_context.state).
        tool_context: Optional ADK ToolContext injected automatically by the framework.
        
    Returns:
        ComplaintRecord with unique ticket ID and status.
    """
    # Deterministic identity fallback from session state
    resolved_customer_id = customer_id
    if (not resolved_customer_id or not str(resolved_customer_id).strip()) and tool_context and hasattr(tool_context, "state"):
        resolved_customer_id = tool_context.state.get("customer_id")

    resolved_customer_name = customer_name
    if (not resolved_customer_name or not str(resolved_customer_name).strip()) and tool_context and hasattr(tool_context, "state"):
        resolved_customer_name = tool_context.state.get("customer_name")

    cat_enum = parse_category(category)
    sev_enum = parse_severity(severity)
    ticket_id = generate_ticket_id()
    sla_timeframe = get_sla_timeframe(sev_enum)

    record = ComplaintRecord(
        ticket_id=ticket_id,
        customer_id=str(resolved_customer_id).strip() if resolved_customer_id else None,
        customer_name=str(resolved_customer_name).strip() if resolved_customer_name else None,
        category=cat_enum,
        severity=sev_enum,
        incident_datetime=incident_datetime.strip(),
        situation_overview=situation_overview.strip(),
        customer_request=customer_request.strip(),
        status="OPEN",
        sla_timeframe=sla_timeframe
    )

    save_complaint(record)

    if tool_context and hasattr(tool_context, "state"):
        tool_context.state["session_stage"] = "COMPLAINT_RECORDED"
        tool_context.state["last_ticket_id"] = ticket_id

    return record


def query_complaint_status(ticket_id: str) -> Dict[str, Any]:
    """Retrieves complaint investigation status by ticket ID."""
    clean_id = ticket_id.strip().upper()
    complaint = COMPLAINT_STORE.get(clean_id)
    if not complaint:
        return {"status": "NOT_FOUND", "message": f"ไม่พบหมายเลขคำร้อง {clean_id}"}

    return {
        "status": "FOUND",
        "ticket_id": complaint.ticket_id,
        "category": complaint.category.value,
        "severity": complaint.severity.value,
        "resolution_status": complaint.status,
        "sla": get_sla_timeframe(complaint.severity),
        "incident_datetime": complaint.incident_datetime,
        "customer_request": complaint.customer_request
    }
