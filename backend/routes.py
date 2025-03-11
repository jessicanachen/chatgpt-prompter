from fastapi import APIRouter, Request
from backend.gpt import format_prompt_with_gpt, send_prompt_to_gpt

router = APIRouter()

@router.post("/format-prompt/")
async def format_prompt(request: Request):
    data = await request.json()
    raw_prompt = data["raw_prompt"]
    formatted = format_prompt_with_gpt(raw_prompt)
    return {"formatted_prompt": formatted}

@router.post("/send-prompt/")
async def send_prompt(request: Request):
    data = await request.json()
    messages = data["messages"]
    reply = send_prompt_to_gpt(messages)
    return {"reply": reply}
