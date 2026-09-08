"""
Quick WebSocket Live Test Script for Gemini Live Bot.
Demonstrates connecting to ws://localhost:8080/ws/live and sending test prompts.
"""

import asyncio
import json
import websockets

SERVER_URI = "ws://localhost:8080/ws/live"

TEST_PROMPTS = [
    "สวัสดีครับ ผมสมชาย ใจดี เกิด 15 มกราคม 2533 อยากจองตั๋วเครื่องบินไปเชียงใหม่ครับ",
    "ขอเที่ยวบินแรกช่วงเช้าเลยครับ",
    "ยืนยันการจองครับ",
    "ไม่มีเรื่องอื่นแล้วครับ ขอบคุณมากครับ"
]


async def run_test():
    print(f"Connecting to {SERVER_URI}...")
    try:
        async with websockets.connect(SERVER_URI) as ws:
            print("Connected! Waiting for session initialization...\n")

            # Receiver task
            async def receive_loop():
                try:
                    async for message in ws:
                        if isinstance(message, str):
                            data = json.loads(message)
                            msg_type = data.get("type")
                            if msg_type == "SESSION_INIT":
                                print(f"[EVENT] Session Initialized with Agent: {data.get('active_agent')}")
                            elif msg_type == "TOOL_CALL":
                                print(f"[TOOL]  {data.get('tool_name')}({data.get('args')})")
                            elif msg_type == "AUTH_SUCCESS":
                                print(f"[AUTH]  Verified {data.get('customer_name')} ({data.get('customer_id')})")
                            elif msg_type == "AGENT_TRANSFER":
                                print(f"[XFER]  Transferred to {data.get('target_agent')}")
                            elif msg_type == "CALL_TERMINATED":
                                print(f"[STOP]  Call Terminated: {data.get('reason')}")
                                print(f"        Farewell: {data.get('farewell_message')}")
                                break
                            elif msg_type == "TEXT_MESSAGE":
                                print(f"[AGENT] {data.get('text')}")
                        else:
                            # 24kHz PCM binary audio chunk received
                            pass
                except asyncio.CancelledError:
                    pass

            recv_task = asyncio.create_task(receive_loop())

            # Send prompt sequence
            for prompt in TEST_PROMPTS:
                await asyncio.sleep(2)
                print(f"\n[USER]  {prompt}")
                await ws.send(json.dumps({"type": "TEXT_MESSAGE", "text": prompt}))
                await asyncio.sleep(4)

            await asyncio.sleep(3)
            recv_task.cancel()
            await asyncio.gather(recv_task, return_exceptions=True)

    except ConnectionRefusedError:
        print(f"Error: Could not connect to {SERVER_URI}. Is the server running? (run: uvicorn app.server:app --port 8080)")
    except Exception as e:
        print(f"Connection error: {e}")


if __name__ == "__main__":
    asyncio.run(run_test())
