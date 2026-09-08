"""
Canonical Customer Intent Lexicons & Matchers.
Ensures 100% consistency across Root Orchestrator (authenticate_customer)
and Sub-Agents (route_customer_followup).
"""

from typing import Optional

# Universal Customer Completion / Termination expressions
COMPLETION_KEYWORDS = [
    "ไม่มี", "พอแล้ว", "พอ", "เสร็จแล้ว", "เสร็จสิ้น", "เสร็จ", "แค่นี้", "ขอบคุณ", "วางสาย", 
    "บ๊ายบาย", "บาย", "ไม่เป็นไร", "ไม่ต้องการ", "ไม่มีแล้ว", 
    "เรียบร้อยแล้ว", "เรียบร้อย", "thank", "bye", "no", "nothing", "done"
]

# Customer Grievance & Complaint expressions
COMPLAINT_KEYWORDS = [
    "complaint", "complain", "ร้องเรียน", "คอมเพลน", "แจ้งปัญหา", "มีปัญหา", "ปัญหา",
    "กระเป๋าหาย", "กระเป๋าพัง", "สัมภาระ", "หาย", "เสียหาย", "ชำรุด",
    "ล่าช้า", "ดีเลย์", "delay", "บริการแย่", "พนักงานไม่สุภาพ", "ไม่ประทับใจ",
    "เคลม", "claim", "ขอเงินคืน", "refund"
]

# Customer Flight Search & Booking expressions
FLIGHT_KEYWORDS = [
    "flight", "booking", "book", "จองตั๋ว", "จองเที่ยวบิน", "จอง",
    "เช็คเที่ยวบิน", "ค้นหาเที่ยวบิน", "ตารางบิน", "ราคาตั๋ว", "สำรองที่นั่ง", "ซื้อตั๋ว",
    "ไฟลท์", "เครื่องบิน", "เดินทาง", "หาตั๋ว", "อยากไป",
    "ไปเชียงใหม่", "ไปภูเก็ต", "ไปโตเกียว"
]

# Ambiguity / Clarification expressions
CLARIFICATION_KEYWORDS = [
    "ทำอะไรได้บ้าง", "มีบริการอะไร", "ช่วยอะไรได้บ้าง", "มีอะไรบ้าง", 
    "งง", "ยังไงนะ", "อะไรนะ", "help"
]


def detect_customer_intent(text: Optional[str]) -> Optional[str]:
    """
    Evaluates customer statement and classifies intent into 'complaint', 'flight', or None.
    Grievance/complaint has precedence over flight keywords to prevent false-positives
    when airline terms (e.g. 'ปัญหาบนเที่ยวบิน') are mentioned.
    
    Args:
        text: Raw user statement or recognized speech transcript.
        
    Returns:
        'complaint' | 'flight' | None
    """
    if not text:
        return None
    
    norm = text.strip().lower()

    # 1. Complaint evaluation first
    if any(k in norm for k in COMPLAINT_KEYWORDS):
        return "complaint"

    # 2. Flight booking evaluation
    if any(k in norm for k in FLIGHT_KEYWORDS) or ("บิน" in norm and "ปัญหา" not in norm and "ร้องเรียน" not in norm):
        return "flight"

    return None
