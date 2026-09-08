"""
Call Control & Termination Tools for Gemini Live Bot.
Strictly conforms to SPEC-20260907-GEMINI-LIVE-ADK-THAI-VOICE-AGENT.
"""

from typing import Optional, Union, Any
from app.models import CallTerminationReason, CallTerminationResult


STANDARD_FAREWELLS = {
    CallTerminationReason.AUTH_FAILURE_EXCEEDED: (
        "ขออภัยเป็นอย่างยิ่งครับ ระบบไม่สามารถยืนยันข้อมูลตัวตนของคุณลูกค้าได้ครบ 3 ครั้ง "
        "เพื่อความปลอดภัยของข้อมูลบัญชี ทางระบบจำเป็นต้องขออนุญาตยุติการสนทนานี้ "
        "กรุณาติดต่อศูนย์บริการลูกค้าโดยตรง หรือลองใหม่อีกครั้งในภายหลัง ขอบพระคุณครับ"
    ),
    CallTerminationReason.OUT_OF_SCOPE_INTENT: (
        "ทางสายการบินต้องกราบขออภัยด้วยครับ ระบบผู้ช่วยอัตโนมัตินี้รองรับเฉพาะบริการสำรองที่นั่งตั๋วเครื่องบิน"
        "และรับเรื่องร้องเรียนเท่านั้น ไม่สามารถให้บริการในส่วนนี้ได้ ทางเราขอขอบพระคุณที่ติดต่อเข้ามา "
        "และขออนุญาตยุติการสนทนา สวัสดีครับ"
    ),
    CallTerminationReason.SESSION_COMPLETED: (
        "ขอบพระคุณที่เลือกใช้บริการสายการบินของเรา ขอให้มีความสุขและเดินทางโดยสวัสดิภาพ สวัสดีครับ"
    ),
    CallTerminationReason.CUSTOMER_DISCONNECT: (
        "สายสนทนาสิ้นสุดลงแล้ว ขอบพระคุณครับ"
    )
}


def terminate_call(
    reason: Union[CallTerminationReason, str],
    farewell_message: Optional[str] = None,
    tool_context: Optional[Any] = None,
) -> CallTerminationResult:
    """
    Politely terminates the current voice session and WebSocket connection.
    
    Args:
        reason: The rationale for call termination:
            - 'AUTH_FAILURE_EXCEEDED': Customer failed authentication 3 times.
            - 'OUT_OF_SCOPE_INTENT': Customer requested service outside flight booking or complaints.
            - 'SESSION_COMPLETED': Customer confirmed all tasks completed ('ไม่มีเรื่องอื่นแล้ว').
            - 'CUSTOMER_DISCONNECT': Customer disconnected.
        farewell_message: Optional custom courteous Thai closing message.
        tool_context: Optional ADK ToolContext injected automatically by the framework.
        
    Returns:
        CallTerminationResult instructing the server to close the WebSocket audio channel.
    """
    if isinstance(reason, str):
        try:
            reason_enum = CallTerminationReason(reason.strip().upper())
        except ValueError:
            reason_enum = CallTerminationReason.OUT_OF_SCOPE_INTENT
    else:
        reason_enum = reason

    spoken_message = farewell_message or STANDARD_FAREWELLS.get(
        reason_enum,
        STANDARD_FAREWELLS[CallTerminationReason.SESSION_COMPLETED]
    )

    if tool_context and hasattr(tool_context, "state"):
        tool_context.state["session_stage"] = "CALL_TERMINATED"
        tool_context.state["termination_reason"] = reason_enum.value
        tool_context.state["is_call_active"] = False

    return CallTerminationResult(
        status="CALL_TERMINATED",
        reason=reason_enum,
        farewell_message=spoken_message
    )

