"""
Pydantic Data Models & Type Contracts for Gemini Live Bot.
Strictly conforms to SPEC-20260907-GEMINI-LIVE-ADK-THAI-VOICE-AGENT.
"""

from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class CustomerProfile(BaseModel):
    """Customer profile record stored in database."""
    customer_id: str = Field(..., description="Unique customer ID (e.g. CUST-001)")
    name_th: str = Field(..., description="Full name in Thai script")
    name_en: str = Field(..., description="Full name transliterated in English")
    birthdate: date = Field(..., description="Date of birth (YYYY-MM-DD)")
    phone_number: str = Field(..., description="Contact telephone number")
    email: str = Field(..., description="Customer email address")
    loyalty_tier: str = Field(default="Standard", description="Loyalty tier: Standard, Silver, Gold, Platinum")

    @field_validator("customer_id")
    @classmethod
    def validate_customer_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("customer_id cannot be empty")
        return v.strip()

    @field_validator("name_th", "name_en")
    @classmethod
    def validate_names(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class AuthResult(BaseModel):
    """Result of customer authentication attempt."""
    is_authenticated: bool = Field(..., description="True if credentials matched successfully")
    customer_id: Optional[str] = Field(None, description="Customer ID if verified")
    customer_name: Optional[str] = Field(None, description="Customer full name")
    loyalty_tier: Optional[str] = Field(None, description="Loyalty tier")
    message: str = Field(..., description="Status message in Thai")


class CabinClass(str, Enum):
    ECONOMY = "Economy"
    PREMIUM_ECONOMY = "Premium Economy"
    BUSINESS = "Business"


class FlightOption(BaseModel):
    """Curated flight option from mock flight search engine."""
    flight_number: str = Field(..., description="Airline flight code (e.g. TG642)")
    airline: str = Field(..., description="Airline carrier name")
    departure_city: str = Field(..., description="Departure city or airport name")
    arrival_city: str = Field(..., description="Arrival city or airport name")
    departure_time: str = Field(..., description="Departure time in format HH:MM")
    arrival_time: str = Field(..., description="Arrival time in format HH:MM")
    departure_date: str = Field(..., description="Date of departure (YYYY-MM-DD)")
    price_thb: float = Field(..., description="Ticket price in Thai Baht (THB)")
    cabin_class: CabinClass = Field(default=CabinClass.ECONOMY)
    available_seats: int = Field(default=9, description="Number of remaining seats")

    @field_validator("price_thb")
    @classmethod
    def validate_price(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Price cannot be negative")
        return v


class FlightSearchParams(BaseModel):
    """Parameters for live flight search."""
    departure_city: str = Field(..., description="Origin city/airport")
    arrival_city: str = Field(..., description="Destination city/airport")
    departure_date: str = Field(..., description="Date of travel (YYYY-MM-DD)")
    return_date: Optional[str] = Field(None, description="Optional return date")


class FlightBookingConfirmation(BaseModel):
    """Confirmed flight reservation ledger entry."""
    booking_reference: str = Field(..., description="6-character PNR reference code (e.g. TH9284)")
    customer_id: str = Field(..., description="Booked customer identifier")
    flight_number: str = Field(..., description="Confirmed flight code")
    passenger_name: str = Field(..., description="Passenger name")
    total_price_thb: float = Field(..., description="Total confirmed price in THB")
    booking_status: str = Field(default="CONFIRMED", description="CONFIRMED | PENDING | CANCELLED")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("booking_reference")
    @classmethod
    def validate_pnr(cls, v: str) -> str:
        if len(v.strip()) != 6:
            raise ValueError("PNR booking reference must be exactly 6 characters")
        return v.strip().upper()


class ComplaintSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ComplaintCategory(str, Enum):
    FLIGHT_DELAY = "ความล่าช้าของเที่ยวบิน"
    LOST_BAGGAGE = "สัมภาระสูญหายหรือเสียหาย"
    INFLIGHT_SERVICE = "การบริการบนเที่ยวบิน"
    TICKETING_REFUND = "ปัญหาการจองตั๋วหรือคืนเงิน"
    GROUND_STAFF = "การบริการของเจ้าหน้าที่ภาคพื้น"
    OTHER = "อื่นๆ"


class ComplaintRecord(BaseModel):
    """Customer grievance complaint record."""
    ticket_id: str = Field(..., description="Unique ticket code (e.g. TKT-20260907-8812)")
    customer_id: Optional[str] = Field(None, description="Associated authenticated customer ID")
    customer_name: Optional[str] = Field(None, description="Customer name")
    category: ComplaintCategory = Field(..., description="Categorized grievance")
    severity: ComplaintSeverity = Field(default=ComplaintSeverity.MEDIUM)
    incident_datetime: str = Field(..., description="When the incident occurred")
    situation_overview: str = Field(..., description="Detailed description of what occurred")
    customer_request: str = Field(..., description="Desired resolution requested by customer")
    status: str = Field(default="OPEN", description="OPEN | IN_INVESTIGATION | RESOLVED")
    sla_timeframe: str = Field(default="ภายใน 24 - 48 ชั่วโมงทำการ", description="SLA resolution commitment")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CallTerminationReason(str, Enum):
    AUTH_FAILURE_EXCEEDED = "AUTH_FAILURE_EXCEEDED"  # Failed authentication 3 consecutive times
    OUT_OF_SCOPE_INTENT = "OUT_OF_SCOPE_INTENT"      # Customer requested unauthorized or out-of-scope task
    SESSION_COMPLETED = "SESSION_COMPLETED"          # Customer finished and confirmed no more assistance needed
    CUSTOMER_DISCONNECT = "CUSTOMER_DISCONNECT"      # User abruptly closed WebSocket / microphone


class CallTerminationResult(BaseModel):
    """Result payload emitted when call termination is executed."""
    status: str = Field(default="CALL_TERMINATED")
    reason: CallTerminationReason
    farewell_message: str = Field(..., description="Courteous Thai closing message spoken before disconnection")


class FollowupAction(str, Enum):
    TRANSFER_TO_FLIGHT = "TRANSFER_TO_FLIGHT"
    TRANSFER_TO_COMPLAINT = "TRANSFER_TO_COMPLAINT"
    CONTINUE_CURRENT_AGENT = "CONTINUE_CURRENT_AGENT"
    TERMINATE_SESSION_COMPLETED = "TERMINATE_SESSION_COMPLETED"
    TERMINATE_OUT_OF_SCOPE = "TERMINATE_OUT_OF_SCOPE"
    REQUEST_CLARIFICATION = "REQUEST_CLARIFICATION"


class FollowupRouteResult(BaseModel):
    """Result payload from route_customer_followup tool."""
    action: FollowupAction
    target_agent: Optional[str] = Field(None, description="Target agent name if transfer is initiated")
    farewell_or_transition_message: str = Field(..., description="Polite response in Thai for the customer")
    explanation: str = Field(..., description="Reason for the routing decision")

