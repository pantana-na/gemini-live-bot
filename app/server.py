"""
FastAPI Orchestration Web Server for Gemini Live Bot.
Provides /healthz liveness probe (Rule 6) and WebSocket audio endpoint for ADK Live Runner.
Strictly conforms to SPEC-20260907-GEMINI-LIVE-ADK-THAI-VOICE-AGENT.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
import os
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import asyncio
from google import genai
from google.genai import types

from app.agent import (
    root_agent,
    LIVE_MODEL,
    VOICE_ORCHESTRATOR,
    TEMPERATURE,
    ROOT_ORCHESTRATOR_INSTRUCTION,
    FLIGHT_BOOKING_INSTRUCTION,
    COMPLAINT_INSTRUCTION
)
from app.tools.auth_tools import authenticate_customer, check_customer_status
from app.tools.flight_tools import search_real_flights, confirm_flight_booking
from app.tools.complaint_tools import record_customer_complaint
from app.tools.call_control_tools import terminate_call
from app.tools.coordination_tools import route_customer_followup
from app.models import CallTerminationReason, CallTerminationResult

# Configure structured logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("gemini-live-bot")

app = FastAPI(
    title="Gemini Live Bot Platform",
    description="Multimodal Voice-First Thai Airline Customer Engagement Platform with Google ADK",
    version="1.0.0"
)

# CORS configuration for ADK web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """
    Root endpoint: returns service metadata and points to ADK Web UI (/dev-ui/).
    """
    return {
        "service": "gemini-live-bot",
        "status": "online",
        "interface": "adk-web",
        "adk_ui_url": "/dev-ui/",
        "target_model": LIVE_MODEL,
        "language": "th",
        "orchestrator": root_agent.name,
        "sub_agents": [s.name for s in root_agent.sub_agents],
        "endpoints": {
            "health": "/health",
            "healthz": "/healthz",
            "ready": "/readyz",
            "websocket_live": "/ws/live"
        }
    }


@app.get("/health")
async def health():
    """ADK standard health check endpoint."""
    return {"status": "ok"}


@app.get("/api/info")
async def api_info():
    """Service status and landing metadata."""
    return {
        "service": "gemini-live-bot",
        "status": "online",
        "target_model": LIVE_MODEL,
        "language": "th",
        "orchestrator": root_agent.name,
        "sub_agents": [s.name for s in root_agent.sub_agents],
        "endpoints": {
            "health": "/healthz",
            "ready": "/readyz",
            "websocket_live": "/ws/live"
        }
    }


@app.get("/healthz")
async def health_probe():
    """
    Rule 6: Cloud Run Liveness Probe Endpoint.
    Strictly returns 200 OK to indicate healthy operational status.
    Invariant 10: Invariant to query parameters or headers.
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "gemini-live-bot",
            "model": LIVE_MODEL,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@app.get("/readyz")
async def readiness_probe():
    """Cloud Run Readiness Probe."""
    return JSONResponse(
        status_code=200,
        content={"status": "ready", "service": "gemini-live-bot"}
    )


@app.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    """
    WebSocket Bidirectional Streaming Endpoint for Live Audio & JSON Control.
    Connects client audio stream directly to Google Gemini Live API.
    Streams 16kHz audio upstream, receives 24kHz PCM audio downstream, and invokes domain tools.
    """
    await websocket.accept()
    logger.info("Client connected to /ws/live")

    # Ensure Vertex AI disabled for direct API key usage
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
    api_key = os.getenv("GEMINI_API_KEY")

    client = genai.Client(api_key=api_key)

    # Combined multi-agent instruction prompt
    system_instruction_text = f"""
{ROOT_ORCHESTRATOR_INSTRUCTION}

{FLIGHT_BOOKING_INSTRUCTION}

{COMPLAINT_INSTRUCTION}
"""

    live_config = types.LiveConnectConfig(
        response_modalities=[types.Modality.AUDIO],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE_ORCHESTRATOR)
            )
        ),
        system_instruction=types.Content(parts=[types.Part.from_text(text=system_instruction_text)]),
        tools=[authenticate_customer, check_customer_status, search_real_flights, confirm_flight_booking, record_customer_complaint, route_customer_followup, terminate_call],
        temperature=TEMPERATURE
    )

    # Tool execution mapping
    tool_map = {
        "authenticate_customer": authenticate_customer,
        "check_customer_status": check_customer_status,
        "search_real_flights": search_real_flights,
        "confirm_flight_booking": confirm_flight_booking,
        "record_customer_complaint": record_customer_complaint,
        "route_customer_followup": route_customer_followup,
        "terminate_call": terminate_call,
    }

    try:
        # Connect to Gemini Live Multimodal Session
        async with client.aio.live.connect(model=LIVE_MODEL, config=live_config) as session:
            logger.info("Connected to Gemini Live session (%s)", LIVE_MODEL)

            await websocket.send_text(json.dumps({
                "type": "SESSION_INIT",
                "active_agent": root_agent.name,
                "status": "READY"
            }))

            # Downstream receive task: stream model responses back to browser
            async def receive_from_gemini():
                try:
                    async for response in session.receive():
                        # Handle tool calls
                        if response.tool_call:
                            function_responses = []
                            for fc in response.tool_call.function_calls:
                                fn_name = fc.name
                                fn_args = fc.args or {}
                                logger.info("Gemini Live Tool Call: %s(%s)", fn_name, fn_args)

                                # Notify client of tool execution
                                await websocket.send_text(json.dumps({
                                    "type": "TOOL_CALL",
                                    "tool_name": fn_name,
                                    "args": fn_args
                                }))

                                tool_fn = tool_map.get(fn_name)
                                if tool_fn:
                                    try:
                                        res = tool_fn(**fn_args)
                                        # If Pydantic model, convert to dict
                                        res_data = res.model_dump() if hasattr(res, "model_dump") else res
                                    except Exception as err:
                                        res_data = {"error": str(err)}
                                else:
                                    res_data = {"error": f"Unknown tool: {fn_name}"}

                                # Extra notifications for key domain actions
                                if fn_name == "authenticate_customer" and isinstance(res_data, dict):
                                    if res_data.get("is_authenticated"):
                                        await websocket.send_text(json.dumps({
                                            "type": "AUTH_SUCCESS",
                                            "customer_id": res_data.get("customer_id"),
                                            "customer_name": res_data.get("customer_name")
                                        }))
                                elif fn_name == "terminate_call" and isinstance(res_data, dict):
                                    await websocket.send_text(json.dumps({
                                        "type": "CALL_TERMINATED",
                                        "reason": res_data.get("reason"),
                                        "farewell_message": res_data.get("farewell_message")
                                    }))
                                elif fn_name == "route_customer_followup" and isinstance(res_data, dict):
                                    action = res_data.get("action")
                                    if action in ["TERMINATE_SESSION_COMPLETED", "TERMINATE_OUT_OF_SCOPE"]:
                                        await websocket.send_text(json.dumps({
                                            "type": "CALL_TERMINATED",
                                            "reason": action,
                                            "farewell_message": res_data.get("farewell_or_transition_message")
                                        }))
                                    elif "TRANSFER" in str(action):
                                        await websocket.send_text(json.dumps({
                                            "type": "AGENT_TRANSFER",
                                            "target_agent": res_data.get("target_agent"),
                                            "message": res_data.get("farewell_or_transition_message")
                                        }))

                                function_responses.append(types.FunctionResponse(
                                    name=fc.name,
                                    id=fc.id,
                                    response={"output": res_data}
                                ))

                            # Send tool execution result back to Gemini Live
                            await session.send_tool_response(function_responses=function_responses)

                        # Handle server audio and text content
                        sc = response.server_content
                        if sc and sc.model_turn:
                            for part in sc.model_turn.parts:
                                if part.text:
                                    await websocket.send_text(json.dumps({
                                        "type": "TEXT_MESSAGE",
                                        "text": part.text
                                    }))
                                if part.inline_data and part.inline_data.data:
                                    # Stream 24kHz binary PCM chunk directly to browser
                                    await websocket.send_bytes(part.inline_data.data)

                except asyncio.CancelledError:
                    pass
                except Exception as err:
                    logger.error("Error in receive_from_gemini: %s", err, exc_info=True)

            gemini_recv_task = asyncio.create_task(receive_from_gemini())

            # Upstream loop: read audio bytes or text messages from browser and forward to Gemini
            try:
                while True:
                    message = await websocket.receive()
                    if message.get("type") == "websocket.disconnect":
                        break

                    if "bytes" in message and message["bytes"]:
                        audio_chunk = message["bytes"]
                        # Forward 16kHz PCM audio chunk to Gemini Live
                        await session.send_realtime_input(
                            audio=types.Blob(data=audio_chunk, mime_type="audio/pcm;rate=16000")
                        )

                    elif "text" in message and message["text"]:
                        try:
                            payload = json.loads(message["text"])
                        except json.JSONDecodeError:
                            payload = {"type": "TEXT_MESSAGE", "text": message["text"]}

                        msg_type = payload.get("type", "")

                        if msg_type == "PING":
                            await websocket.send_text(json.dumps({"type": "PONG"}))

                        elif msg_type == "TEXT_MESSAGE":
                            user_text = payload.get("text", "")
                            if user_text:
                                await session.send_client_content(
                                    turns=[types.Content(parts=[types.Part.from_text(text=user_text)])],
                                    turn_complete=True
                                )

                        elif msg_type == "TERMINATE_CALL":
                            reason_val = payload.get("reason", "SESSION_COMPLETED")
                            term_res = terminate_call(reason_val)
                            await websocket.send_text(json.dumps({
                                "type": "CALL_TERMINATED",
                                "reason": term_res.reason.value,
                                "farewell_message": term_res.farewell_message
                            }))
                            await websocket.close(code=1000)
                            break

            finally:
                gemini_recv_task.cancel()
                await asyncio.gather(gemini_recv_task, return_exceptions=True)

    except WebSocketDisconnect:
        logger.info("Client disconnected from /ws/live")
    except Exception as e:
        logger.error("Error in websocket session: %s", str(e), exc_info=True)
        try:
            await websocket.close(code=1011)
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.server:app", host="0.0.0.0", port=8080, reload=True)
