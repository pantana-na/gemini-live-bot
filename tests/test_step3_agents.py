"""
Unit Tests for Step 3: Google ADK Multi-Agent Orchestration & Prompts.
Verifies agent hierarchy structure, tool bindings, delegation, and loopback directives.
"""

from app.agent import root_agent, flight_booking_agent, complaint_agent
from app.tools.auth_tools import authenticate_customer, check_customer_status
from app.tools.flight_tools import search_real_flights, confirm_flight_booking
from app.tools.complaint_tools import record_customer_complaint, query_complaint_status
from app.tools.call_control_tools import terminate_call


def test_agent_hierarchy_and_registration():
    """Verify root agent has registered 2 specialized sub-agents."""
    assert root_agent.name == "thai_customer_orchestrator"
    assert len(root_agent.sub_agents) == 2
    sub_names = [sub.name for sub in root_agent.sub_agents]
    assert "flight_booking_agent" in sub_names
    assert "complaint_agent" in sub_names


def test_subagents_allow_transfer_to_parent_and_peers_for_coordination():
    """Verify subagents allow transfer back to parent and peers for decentralized concierge coordination."""
    assert flight_booking_agent.disallow_transfer_to_parent is False
    assert complaint_agent.disallow_transfer_to_parent is False
    assert flight_booking_agent.disallow_transfer_to_peers is False
    assert complaint_agent.disallow_transfer_to_peers is False


def test_tool_bindings_across_agents():
    """Verify each agent has access to its domain-specific tools and terminate_call."""
    # Root orchestrator tools
    root_tool_names = [t.__name__ for t in root_agent.tools]
    assert "authenticate_customer" in root_tool_names
    assert "check_customer_status" in root_tool_names
    assert "terminate_call" in root_tool_names

    # Flight booking agent tools (includes terminate_call and route_customer_followup for autonomous concierge loop)
    flight_tool_names = [t.__name__ for t in flight_booking_agent.tools]
    assert "search_real_flights" in flight_tool_names
    assert "confirm_flight_booking" in flight_tool_names
    assert "route_customer_followup" in flight_tool_names
    assert "terminate_call" in flight_tool_names

    # Complaint agent tools (includes terminate_call and route_customer_followup for autonomous concierge loop)
    comp_tool_names = [t.__name__ for t in complaint_agent.tools]
    assert "record_customer_complaint" in comp_tool_names
    assert "query_complaint_status" in comp_tool_names
    assert "route_customer_followup" in comp_tool_names
    assert "terminate_call" in comp_tool_names


def test_orchestrator_guardrail_prompt_directives():
    """Verify root orchestrator instructions enforce dual terminations, concierge loop, and zero-redundancy transfer."""
    instruction = root_agent.instruction
    # Guardrail 1A: 3 failed auth attempts
    assert "3 ครั้ง" in instruction
    assert "AUTH_FAILURE_EXCEEDED" in instruction
    # Guardrail 1B: Out of scope
    assert "OUT_OF_SCOPE_INTENT" in instruction
    # Guardrail 2: Concierge loop prompt
    assert "มีบริการอื่นใดให้ทางเราช่วยดูแลเพิ่มเติมอีกไหม" in instruction
    assert "SESSION_COMPLETED" in instruction
    # Hybrid zero-redundancy transfer directives
    assert "ห้ามถามซ้ำ" in instruction
    assert "transfer_to_agent" in instruction
    assert "customer_intent" in instruction


def test_subagent_decentralized_coordination_directives():
    """Verify sub-agents act as coordinators: asking what else customer needs, peer-routing, and terminating."""
    flight_inst = flight_booking_agent.instruction
    assert "มีบริการอื่นใดให้ก้อยช่วยดูแลเพิ่มเติมอีกไหม" in flight_inst
    assert "route_customer_followup" in flight_inst
    assert "complaint_agent" in flight_inst

    comp_inst = complaint_agent.instruction
    assert "มีบริการอื่นใดให้ไอติมช่วยดูแลเพิ่มเติมอีกไหม" in comp_inst
    assert "route_customer_followup" in comp_inst
    assert "flight_booking_agent" in comp_inst



def test_agent_voice_profiles_and_thai_names():
    """Verify distinct voice profiles, Thai names, and fixed personas configured for each agent."""
    from app.agent import AGENT_PROFILES, TEMPERATURE

    # Orchestrator: Aoede -> ฝน
    root_voice = root_agent.model.speech_config.voice_config.prebuilt_voice_config.voice_name
    assert root_voice == "Aoede"
    assert AGENT_PROFILES["orchestrator"]["thai_name"] == "ฝน"
    assert "ฝน" in root_agent.instruction
    assert "ฝน" in root_agent.description

    # Flight booking: Kore -> ก้อย
    flight_voice = flight_booking_agent.model.speech_config.voice_config.prebuilt_voice_config.voice_name
    assert flight_voice == "Kore"
    assert AGENT_PROFILES["flight"]["thai_name"] == "ก้อย"
    assert "ก้อย" in flight_booking_agent.instruction
    assert "ก้อย" in flight_booking_agent.description

    # Complaint agent: Charon -> ไอติม
    complaint_voice = complaint_agent.model.speech_config.voice_config.prebuilt_voice_config.voice_name
    assert complaint_voice == "Charon"
    assert AGENT_PROFILES["complaint"]["thai_name"] == "ไอติม"
    assert "ไอติม" in complaint_agent.instruction
    assert "ไอติม" in complaint_agent.description

    # Low temperature to avoid hallucination/imagination
    assert TEMPERATURE <= 0.3
    assert root_agent.generate_content_config.temperature == TEMPERATURE
    assert flight_booking_agent.generate_content_config.temperature == TEMPERATURE
    assert complaint_agent.generate_content_config.temperature == TEMPERATURE


def test_agent_name_introduction_directives():
    """Verify all agents are explicitly instructed to introduce their name in the first conversation."""
    for ag in [root_agent, flight_booking_agent, complaint_agent]:
        assert "แนะนำชื่อตนเอง" in ag.instruction


def test_agent_concise_dialogue_and_question_splitting():
    """Verify all agents are instructed to be concise and split multiple questions into 2-3 sets."""
    for ag in [root_agent, flight_booking_agent, complaint_agent]:
        # Concise speech directive
        assert "พูดสั้น" in ag.instruction or "ไม่พูดยืดยาว" in ag.instruction
        # Splitting into 2-3 sets
        assert "2-3" in ag.instruction


def test_complaint_acknowledgment_and_reassurance_directive():
    """Verify complaint agent is instructed to acknowledge, reassure with Ticket ID & SLA, then inquire for other needs."""
    instruction = complaint_agent.instruction
    assert "กล่าวตอบรับและยืนยันกับลูกค้าทันทีหลังบันทึกข้อมูล" in instruction
    assert "Ticket ID" in instruction
    assert "SLA" in instruction
    assert "มีบริการอื่นใดให้ไอติมช่วยดูแลเพิ่มเติมอีกไหม" in instruction
    assert "Concierge Coordination" in instruction


