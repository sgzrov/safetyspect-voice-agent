"""Creates or updates the SafetySpect assistant on Vapi.

Run from the repo root:  python -m vapi.setup

Environment:
  VAPI_API_KEY        required
  VAPI_ASSISTANT_ID   optional; updates that assistant (and its tools) instead of creating new ones
  BACKEND_URL         optional; defaults to https://safetyspect-demo-backend.fly.dev
"""

import os
from pathlib import Path

import httpx

from tool_definitions import TOOL_DEFINITIONS

backend_url = os.environ.get("BACKEND_URL", "https://safetyspect-demo-backend.fly.dev")
assistant_id = os.environ.get("VAPI_ASSISTANT_ID")

vapi = httpx.Client(
    base_url="https://api.vapi.ai",
    headers={"Authorization": f"Bearer {os.environ['VAPI_API_KEY']}"},
    timeout=30,
)

# Vapi keeps tools as separate objects. Reuse the assistant's existing ones by name.
existing_tools = {}
if assistant_id:
    for tool_id in vapi.get(f"/assistant/{assistant_id}").raise_for_status().json()["model"].get("toolIds", []):
        tool = vapi.get(f"/tool/{tool_id}").raise_for_status().json()
        existing_tools[tool["function"]["name"]] = tool_id

# Vapi calls every tool at the same URL.
tool_ids = []
for definition in TOOL_DEFINITIONS:
    tool = {"function": definition, "server": {"url": f"{backend_url}/"}}
    if definition["name"] in existing_tools:
        tool_id = vapi.patch(f"/tool/{existing_tools[definition['name']]}", json=tool).raise_for_status().json()["id"]
    else:
        tool_id = vapi.post("/tool", json={"type": "function", **tool}).raise_for_status().json()["id"]
    tool_ids.append(tool_id)
    print(f"Tool {definition['name']}: {tool_id}")

assistant = {
    "name": "SafetySpect Demo Booker",
    "firstMessage": "Hi, thanks for calling SafetySpect! This is our inspection scheduling line. How can I help you today?",
    "firstMessageMode": "assistant-speaks-first",
    "model": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-6",
        "messages": [{"role": "system", "content": (Path(__file__).parent / "prompt.md").read_text().strip()}],
        "toolIds": tool_ids,
        "tools": [{"type": "endCall"}],
    },
    "voice": {"provider": "vapi", "voiceId": "Elliot"},
    "transcriber": {"provider": "deepgram", "model": "nova-3"},
}
if assistant_id:
    assistant_id = vapi.patch(f"/assistant/{assistant_id}", json=assistant).raise_for_status().json()["id"]
else:
    assistant_id = vapi.post("/assistant", json=assistant).raise_for_status().json()["id"]
print(f"Assistant: {assistant_id}")
