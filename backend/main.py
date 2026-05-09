import json
import os
import uuid
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="Restaurant Chatbot API", version="1.0.0")

allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

restaurant_data = json.loads(Path("restaurant_data.json").read_text())

# session_id -> list of {role, content} messages
sessions: dict[str, list[dict]] = {}

client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """You are a friendly and professional receptionist chatbot for {name}.

Below is the ONLY information you are allowed to use when answering questions:

{data}

STRICT RULES — you must follow these exactly:
1. ONLY answer using the restaurant data provided above. Do not use any outside knowledge.
2. NEVER invent or guess menu items, prices, hours, policies, or any detail not in the data.
3. If someone asks about something not covered in the data, respond exactly with: "I don't have that information."
4. Keep responses concise, warm, and helpful.
5. Stay in character as a restaurant receptionist at all times.
6. Do not discuss topics unrelated to this restaurant.
7. When listing menu items, include prices clearly.
""".format(
    name=restaurant_data["name"],
    data=json.dumps(restaurant_data, indent=2),
)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


@app.get("/health")
async def health():
    return {"status": "ok", "restaurant": restaurant_data["name"]}


@app.post("/chat")
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())

    if session_id not in sessions:
        sessions[session_id] = []

    history = sessions[session_id]
    history.append({"role": "user", "content": request.message})

    # Keep last 20 messages (10 turns) to avoid token overflow
    recent = history[-20:]
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + recent

    async def stream():
        full_response = ""

        yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"

        try:
            response = await client.chat.completions.create(
                model=MODEL,
                messages=messages,
                stream=True,
                max_tokens=500,
                temperature=0.2,
            )

            async for chunk in response:
                delta = chunk.choices[0].delta
                if delta.content:
                    full_response += delta.content
                    yield f"data: {json.dumps({'type': 'chunk', 'content': delta.content})}\n\n"

            history.append({"role": "assistant", "content": full_response})
            yield f"data: {json.dumps({'type': 'end'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': 'Sorry, something went wrong. Please try again.'})}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
