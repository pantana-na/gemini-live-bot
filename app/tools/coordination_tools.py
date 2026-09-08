"""
Coordination & Handoff Routing Tools for Gemini Live Bot.
Strictly conforms to SPEC-20260908-FOLLOWUP-INTENT-ROUTING-TOOL.
"""

from typing import Optional, Any
from app.models import FollowupAction, FollowupRouteResult, CallTerminationReason
from app.tools.call_control_tools import STANDARD_FAREWELLS
from app.intent_lexicon import (
    COMPLETION_KEYWORDS,
    COMPLAINT_KEYWORDS,
    FLIGHT_KEYWORDS,
    CLARIFICATION_KEYWORDS,
    detect_customer_intent,
)


def route_customer_followup(
    customer_response: str,
    current_agent: Optional[str] = None,
    tool_context: Optional[Any] = None,
) -> FollowupRouteResult:
    """
    Evaluates customer post-task response and executes deterministic transfer or termination.
    
    Args:
        customer_response: The verbatim user statement when asked if they need anything else.
        current_agent: Optional name of the active agent calling this tool ('flight_booking_agent' or 'complaint_agent').
        tool_context: Optional ADK ToolContext automatically injected by framework.
        
    Returns:
        FollowupRouteResult specifying routing action, target agent, and response message.
    """
    text = (customer_response or "").strip().lower()

    # Fallback to discover current_agent from tool_context if not explicitly passed
    resolved_agent = current_agent
    if not resolved_agent and tool_context:
        if hasattr(tool_context, "agent") and hasattr(tool_context.agent, "name"):
            resolved_agent = tool_context.agent.name
        elif hasattr(tool_context, "agent_name"):
            resolved_agent = tool_context.agent_name

    # 1. Check Completion / Termination intent first
    if any(k in text for k in COMPLETION_KEYWORDS):
        farewell = STANDARD_FAREWELLS[CallTerminationReason.SESSION_COMPLETED]
        if tool_context and hasattr(tool_context, "state"):
            tool_context.state["session_stage"] = "CALL_TERMINATED"
            tool_context.state["termination_reason"] = "SESSION_COMPLETED"
            tool_context.state["is_call_active"] = False

        return FollowupRouteResult(
            action=FollowupAction.TERMINATE_SESSION_COMPLETED,
            target_agent=None,
            farewell_or_transition_message=farewell,
            explanation="Customer indicated they do not require further assistance. Session terminated politely."
        )

    # 2. Check Complaint & Flight Booking intents using centralized classifier
    detected_intent = detect_customer_intent(text)

    if detected_intent == "complaint":
        if resolved_agent == "complaint_agent":
            if tool_context and hasattr(tool_context, "state"):
                tool_context.state["session_stage"] = "COLLECTING_COMPLAINT_DETAILS"
            return FollowupRouteResult(
                action=FollowupAction.CONTINUE_CURRENT_AGENT,
                target_agent=None,
                farewell_or_transition_message="สามารถแจ้งรายละเอียดข้อร้องเรียนเพิ่มเติมได้เลยครับ เจ้าหน้าที่กำลังรับฟังอยู่ครับ",
                explanation="Customer wants to lodge another complaint while already in complaint_agent."
            )
        else:
            if tool_context:
                if hasattr(tool_context, "state"):
                    tool_context.state["session_stage"] = "TRANSFERRING_TO_COMPLAINT"
                if hasattr(tool_context, "actions") and hasattr(tool_context.actions, "transfer_to_agent"):
                    tool_context.actions.transfer_to_agent = "complaint_agent"
            return FollowupRouteResult(
                action=FollowupAction.TRANSFER_TO_COMPLAINT,
                target_agent="complaint_agent",
                farewell_or_transition_message="รับทราบครับ เดี๋ยวผมประสานงานส่งต่อสายไปยังเจ้าหน้าที่ฝ่ายรับเรื่องร้องเรียนให้ทันทีเลยนะครับ สักครู่นะครับ",
                explanation="Customer requested grievance/complaint assistance. Programmatic handoff to complaint_agent initiated."
            )

    elif detected_intent == "flight":
        if resolved_agent == "flight_booking_agent":
            if tool_context and hasattr(tool_context, "state"):
                tool_context.state["session_stage"] = "COLLECTING_FLIGHT_SEARCH"
            return FollowupRouteResult(
                action=FollowupAction.CONTINUE_CURRENT_AGENT,
                target_agent=None,
                farewell_or_transition_message="ยินดีให้บริการสำรองที่นั่งเพิ่มเติมครับ คุณลูกค้าต้องการเดินทางจากที่ไหน ไปที่ไหน และในวันใดครับ",
                explanation="Customer wants another flight booking while already in flight_booking_agent."
            )
        else:
            if tool_context:
                if hasattr(tool_context, "state"):
                    tool_context.state["session_stage"] = "TRANSFERRING_TO_FLIGHT"
                if hasattr(tool_context, "actions") and hasattr(tool_context.actions, "transfer_to_agent"):
                    tool_context.actions.transfer_to_agent = "flight_booking_agent"
            return FollowupRouteResult(
                action=FollowupAction.TRANSFER_TO_FLIGHT,
                target_agent="flight_booking_agent",
                farewell_or_transition_message="ยินดีครับ เดี๋ยวผมโอนสายไปยังเจ้าหน้าที่ฝ่ายสำรองที่นั่งตั๋วเครื่องบินให้ทันทีเลยนะครับ รอสักครู่นะครับ",
                explanation="Customer requested flight booking. Programmatic handoff to flight_booking_agent initiated."
            )

    # 4. Clarification Request / Ambiguity
    if not text or len(text) <= 4 or any(k in text for k in CLARIFICATION_KEYWORDS):
        return FollowupRouteResult(
            action=FollowupAction.REQUEST_CLARIFICATION,
            target_agent=None,
            farewell_or_transition_message="ทางเรามีบริการค้นหาและสำรองที่นั่งเที่ยวบิน รวมถึงรับเรื่องร้องเรียนและข้อเสนอแนะบริการครับ ไม่ทราบว่าคุณลูกค้าต้องการให้ดูแลด้านใดเพิ่มเติมไหมครับ",
            explanation="Customer query is ambiguous or requesting capabilities. Clarification prompted."
        )

    # 5. Out of Scope / Unrecognized request
    farewell = STANDARD_FAREWELLS[CallTerminationReason.OUT_OF_SCOPE_INTENT]
    if tool_context and hasattr(tool_context, "state"):
        tool_context.state["session_stage"] = "CALL_TERMINATED"
        tool_context.state["termination_reason"] = "OUT_OF_SCOPE_INTENT"
        tool_context.state["is_call_active"] = False

    return FollowupRouteResult(
        action=FollowupAction.TERMINATE_OUT_OF_SCOPE,
        target_agent=None,
        farewell_or_transition_message=farewell,
        explanation="Customer requested an out-of-scope service outside flight booking and complaints. Session terminated."
    )
