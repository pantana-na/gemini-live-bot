"""
Authentication & Customer Lookup Tools for Root Orchestrator.
Strictly conforms to SPEC-20260907-GEMINI-LIVE-ADK-THAI-VOICE-AGENT.
"""

from typing import Dict, Any, Optional
from app.models import AuthResult
from app.mock_data import find_customer_by_credentials, get_customer_by_id
from app.intent_lexicon import detect_customer_intent


def authenticate_customer(
    name: str,
    birthdate: str,
    customer_intent: Optional[str] = None,
    tool_context: Optional[Any] = None,
) -> AuthResult:
    """
    Verifies customer identity against the airline customer database.
    
    Args:
        name: Full name in Thai (e.g. 'สมชาย ใจดี') or English ('Somchai Jaidee').
        birthdate: Date of birth in Thai format (e.g. '15 มกราคม 2533') or ISO ('1990-01-15').
        customer_intent: Optional customer intent mentioned earlier ('complaint' / 'ร้องเรียน' or 'flight' / 'จองตั๋ว').
        tool_context: Internal ADK ToolContext injected automatically by the framework.
        
    Returns:
        AuthResult indicating verification status, customer_id, and greeting message.
    """
    customer = find_customer_by_credentials(name_input=name, birthdate_input=birthdate)
    
    if customer:
        if tool_context and hasattr(tool_context, "state"):
            tool_context.state["auth_fail_count"] = 0
            tool_context.state["is_authenticated"] = True
            tool_context.state["customer_id"] = customer.customer_id
            tool_context.state["customer_name"] = customer.name_th
            tool_context.state["loyalty_tier"] = customer.loyalty_tier
            tool_context.state["session_stage"] = "AUTHENTICATED"
            tool_context.state["is_call_active"] = True

        # If user explicitly requested complaint or flight earlier, trigger immediate transfer via ADK action
        if customer_intent and tool_context:
            detected_intent = detect_customer_intent(customer_intent)
            if detected_intent == "complaint":
                if hasattr(tool_context, "actions"):
                    tool_context.actions.transfer_to_agent = "complaint_agent"
                if hasattr(tool_context, "state"):
                    tool_context.state["session_stage"] = "TRANSFERRING_TO_COMPLAINT"
            elif detected_intent == "flight":
                if hasattr(tool_context, "actions"):
                    tool_context.actions.transfer_to_agent = "flight_booking_agent"
                if hasattr(tool_context, "state"):
                    tool_context.state["session_stage"] = "TRANSFERRING_TO_FLIGHT"

        return AuthResult(
            is_authenticated=True,
            customer_id=customer.customer_id,
            customer_name=customer.name_th,
            loyalty_tier=customer.loyalty_tier,
            message=f"ยืนยันตัวตนสำเร็จ สวัสดีครับ คุณ{customer.name_th} สมาชิกสถานะ {customer.loyalty_tier}"
        )
    
    # Deterministic Failed Auth Counter (Guardrail 1A)
    fail_count = 1
    if tool_context and hasattr(tool_context, "state"):
        fail_count = tool_context.state.get("auth_fail_count", 0) + 1
        tool_context.state["auth_fail_count"] = fail_count
        if fail_count >= 3:
            tool_context.state["session_stage"] = "CALL_TERMINATED"
            tool_context.state["termination_reason"] = "AUTH_FAILURE_EXCEEDED"
            tool_context.state["is_call_active"] = False
            return AuthResult(
                is_authenticated=False,
                customer_id=None,
                customer_name=None,
                loyalty_tier=None,
                message="ขออภัยเป็นอย่างยิ่งครับ ระบบไม่สามารถยืนยันข้อมูลตัวตนของคุณลูกค้าได้ครบ 3 ครั้ง เพื่อความปลอดภัยของข้อมูลบัญชี ทางระบบจำเป็นต้องขออนุญาตยุติการสนทนานี้ กรุณาติดต่อศูนย์บริการลูกค้าโดยตรง หรือลองใหม่อีกครั้งในภายหลัง ขอบพระคุณครับ"
            )

    return AuthResult(
        is_authenticated=False,
        customer_id=None,
        customer_name=None,
        loyalty_tier=None,
        message="ไม่พบข้อมูลผู้โดยสารที่ตรงกับชื่อและวันเดือนปีเกิดที่ระบุ กรุณาลองใหม่อีกครั้งครับ"
    )


def check_customer_status(customer_id: str) -> Dict[str, Any]:
    """
    Retrieves customer account profile by ID.
    
    Args:
        customer_id: The unique customer identifier (e.g. 'CUST-001').
    """
    customer = get_customer_by_id(customer_id)
    if not customer:
        return {"status": "NOT_FOUND", "message": f"ไม่พบบัญชีลูกค้าสำหรับรหัส {customer_id}"}
    
    return {
        "status": "FOUND",
        "customer_id": customer.customer_id,
        "name_th": customer.name_th,
        "name_en": customer.name_en,
        "loyalty_tier": customer.loyalty_tier,
        "email": customer.email,
        "phone_number": customer.phone_number
    }
