"""SafetySpect backend: the tools behind the Retell and Vapi voice agents."""

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

import db
from seed import seed
from tools import run_tool


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await db.connect()
    await seed()
    yield
    await db.pool.close()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    await db.pool.fetchval("SELECT 1")
    return {"status": "ok", "database": "postgresql"}


# Retell calls one URL per tool and sends {"args": {...}}.
@app.post("/retell/{tool_name}")
async def retell_tool(tool_name: str, request: Request) -> dict:
    body = await request.json()
    return await run_tool(tool_name, body.get("args", {}))


# Vapi calls one URL for every tool and sends a "tool-calls" message, expecting one result per call.
@app.post("/")
async def vapi_tools(request: Request) -> dict:
    message = (await request.json()).get("message") or {}
    if message.get("type") != "tool-calls":
        return {"results": []}

    results = []
    for call in message.get("toolCallList", []):
        function = call.get("function") or {}
        args = function.get("arguments") or {}
        if isinstance(args, str):
            args = json.loads(args)
        result = await run_tool(function.get("name"), args)
        results.append({"toolCallId": call.get("id"), "result": json.dumps(result)})
    return {"results": results}
