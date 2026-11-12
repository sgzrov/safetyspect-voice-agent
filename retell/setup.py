"""Creates or updates the SafetySpect agent on Retell.

Run from the repo root:  python -m retell.setup

Environment:
  RETELL_API_KEY    required
  RETELL_AGENT_ID   optional; updates that agent and its LLM instead of creating new ones
  BACKEND_URL       optional; defaults to https://safetyspect-demo-backend.fly.dev
"""

import os
from pathlib import Path

import httpx

from tool_definitions import TOOL_DEFINITIONS

backend_url = os.environ.get("BACKEND_URL", "https://safetyspect-demo-backend.fly.dev")
agent_id = os.environ.get("RETELL_AGENT_ID")

retell = httpx.Client(
    base_url="https://api.retellai.com",
    headers={"Authorization": f"Bearer {os.environ['RETELL_API_KEY']}"},
    timeout=30,
)

# Retell calls each tool at its own URL.
tools = []
for definition in TOOL_DEFINITIONS:
    tools.append({
        "type": "custom",
        "url": f"{backend_url}/retell/{definition['name']}",
        "method": "POST",
        "speak_during_execution": True,
        "speak_after_execution": True,
        **definition,
    })
tools.append({
    "type": "end_call",
    "name": "end_call",
    "description": "End the call once the caller says they're done.",
})

# An existing agent already points at its LLM, so update that one.
llm_id = None
if agent_id:
    llm_id = retell.get(f"/get-agent/{agent_id}").raise_for_status().json()["response_engine"]["llm_id"]

# The LLM: what the agent knows and which tools it can call.
llm = {
    "model": "claude-4.5-haiku",
    "model_temperature": 0,
    "general_prompt": (Path(__file__).parent / "prompt.md").read_text(),
    "begin_message": "Hi, thanks for calling SafetySpect! This is our inspection scheduling line. How can I help you today?",
    "general_tools": tools,
}
if llm_id:
    llm_id = retell.patch(f"/update-retell-llm/{llm_id}", json=llm).raise_for_status().json()["llm_id"]
else:
    llm_id = retell.post("/create-retell-llm", json=llm).raise_for_status().json()["llm_id"]
print(f"LLM: {llm_id}")

# The agent: the voice and call settings around that LLM.
agent = {
    "agent_name": "SafetySpect Demo Booker",
    "response_engine": {"type": "retell-llm", "llm_id": llm_id},
    "voice_id": "11labs-Adrian",
    "language": "en-US",
    "interruption_sensitivity": 0.8,
    "enable_backchannel": True,
    "backchannel_frequency": 0.8,
    "ambient_sound": "call-center",
    "ambient_sound_volume": 0.3,
    "max_call_duration_ms": 5 * 60 * 1000,
    "end_call_after_silence_ms": 20 * 1000,
    "boosted_keywords": ["SafetySpect", "OSHA"],
    "normalize_for_speech": True,
}
if agent_id:
    agent_id = retell.patch(f"/update-agent/{agent_id}", json=agent).raise_for_status().json()["agent_id"]
else:
    agent_id = retell.post("/create-agent", json=agent).raise_for_status().json()["agent_id"]
print(f"Agent: {agent_id}")
