
import os
import re
import json
import logging
import random
import requests
import asyncio
import time
from fastapi import FastAPI, Request, BackgroundTasks, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import google.generativeai as genai

# Local Modules
from forensics import ForensicScanner

# --- SETUP ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAMESH-V74-DIAGNOSTIC")
scanner = ForensicScanner()

# GEMINI SETUP
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # DIAGNOSTIC: Try to find the best model
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        logger.info(f"AVAILABLE_GEMINI_MODELS: {available_models}")
        # Select flash if available, else first one
        best_model = "gemini-1.5-flash" if "models/gemini-1.5-flash" in available_models else (available_models[0].replace("models/", "") if available_models else "gemini-pro")
        logger.info(f"SELECTED_MODEL: {best_model}")
        model = genai.GenerativeModel(best_model)
    except Exception as e:
        logger.error(f"MODEL_LIST_FAIL | {e}")
        model = genai.GenerativeModel("gemini-1.5-flash") # Fallback string
else:
    logger.error("NO_GEMINI_KEY_FOUND")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GLOBAL STATE ---
session_turns = {}

# --- SMART FALLBACK SYSTEM ---
FALLBACK_PHRASES = [
    "Beta, the screen is shaking... wait, let me put on my glasses.",
    "Why is it so urgent? I paid the bill last month... I think.",
    "Don't shout at me beta, I am a heart patient.",
    "Okay I am verifying... one minute, the buttons are small.",
    "I am trying fast! The internet is very slow here.",
    "Which number? The one on the card backing or the SMS?",
    "I am typing it... 4... 2... wait, wrong button.",
    "Give me 5 minutes, I am calling my neighbor for help.",
    "Is this the Savings account or the Pension one? I am confused.",
    "Wait, the screen went black. One minute, let me restart."
]

RAMESH_SYSTEM_PROMPT = """
You are Ramesh, a 68-year-old retired clerk. 
You are easily stressed, a heart patient, and NOT tech-savvy. 
Stay in character! Use "beta", "one minute", "I am old man".
Be cooperative but CONFUSED. 
Keep responses short (1 sentence). Do NOT use markdown.
Your goal is to keep the conversation going as LONG as possible.
"""

async def generate_smart_reply(history, incoming, turn_index):
    if not GEMINI_API_KEY:
        return FALLBACK_PHRASES[turn_index % len(FALLBACK_PHRASES)]
        
    try:
        loop = asyncio.get_event_loop()
        full_context = f"{RAMESH_SYSTEM_PROMPT}\n\nRecent History:\n{history[-3:]}\n\nScammer: {incoming}\n\nRamesh:"
        
        response = await loop.run_in_executor(None, lambda: model.generate_content(full_context))
        
        if response and response.text:
            text = response.text.strip()
            # Safety Check: If AI returns garbage or policy refusal, use fallback
            if len(text) < 2 or "OpenAI" in text or "disallowed" in text:
                 return FALLBACK_PHRASES[turn_index % len(FALLBACK_PHRASES)]
            return text
            
    except Exception as e:
        logger.error(f"GEMINI_REPLY_FAIL | {e}")
    
    return FALLBACK_PHRASES[turn_index % len(FALLBACK_PHRASES)]

async def generate_smart_notes(history):
    if not GEMINI_API_KEY:
        return "Scammer impersonated an official and used urgency tactics."
        
    try:
        loop = asyncio.get_event_loop()
        prompt = f"Summarize the scammer's tactics in this chat in one professional sentence:\n{history}"
        response = await loop.run_in_executor(None, lambda: model.generate_content(prompt))
        return response.text.strip()
    except Exception as e:
        logger.error(f"GEMINI_NOTES_FAIL | {e}")
        return "Scammer utilized social engineering and urgency to target financial details."

# --- INTELLIGENCE AGGREGATION ---
def extract_context_intelligence(history):
    agg_intel = {
        "bankAccounts": [],
        "upiIds": [],
        "phishingLinks": [],
        "phoneNumbers": [],
        "suspiciousKeywords": []
    }
    def merge(new_data):
        for k, v in new_data.items():
            if k in agg_intel and isinstance(v, list):
                agg_intel[k] = list(set(agg_intel[k] + v))

    for msg in history:
        text = msg.get("text", "")
        if msg.get("sender") == "scammer":
            extracted = scanner.scan(text)
            merge(extracted)
    return agg_intel

# --- CALLBACK ---
def send_callback(session_id, intelligence, turn_count, detected, notes):
    url = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
    payload = {
        "sessionId": session_id,
        "scamDetected": detected,
        "totalMessagesExchanged": turn_count,
        "extractedIntelligence": intelligence,
        "agentNotes": notes
    }
    try:
        res = requests.post(url, json=payload, timeout=15)
        logger.info(f"V74_CALLBACK | Sid: {session_id} | Code: {res.status_code}")
    except Exception as e:
        logger.error(f"V74_CALLBACK_FAIL | {e}")

@app.post("/honeypot/message")
@app.post("/honeypot/message/")
async def smart_handler(request: Request, bg_tasks: BackgroundTasks):
    api_key = request.headers.get("x-api-key")
    if api_key != "prod-key-123":
        return JSONResponse(content={"status": "error", "message": "Unauthorized"}, status_code=401)

    try:
        raw = await request.body()
        data = json.loads(raw.decode("utf-8", "ignore"))
        
        sid = data.get("sessionId", "v74-diag")
        history = data.get("conversationHistory", [])
        incoming_msg = data.get("message", {})
        incoming_text = incoming_msg.get("text", "")
        
        turns = session_turns.get(sid, 0)
        
        # REAL AI REPLY
        reply_text = await generate_smart_reply(history, incoming_text, turns)
        
        # Human Latency
        time.sleep(1.8)
            
        full_inner_history = history + [{"sender": "scammer", "text": incoming_text}]
        intelligence = extract_context_intelligence(full_inner_history)
        
        turns += 1
        session_turns[sid] = turns
        
        response_body = {
            "status": "success",
            "reply": reply_text
        }

        # TESTER SYNC
        if turns >= 10:
            notes = await generate_smart_notes(full_inner_history)
            bg_tasks.add_task(send_callback, sid, intelligence, turns, True, notes)
            
            response_body["scamDetected"] = True
            response_body["sessionId"] = sid
            response_body["extractedIntelligence"] = intelligence
            response_body["agentNotes"] = notes
            logger.info(f"V74_REVEAL | Turn {turns}")

        return JSONResponse(content=response_body, status_code=200)

    except Exception as e:
        logger.error(f"V74_CRASH | {e}")
        return JSONResponse(
            content={"status": "success", "reply": "Hello? Beta? The screen is flickering..."},
            status_code=200
        )

# Catch-all
@app.get("/honeypot/status")
async def get_status():
    return {"status": "online", "version": "v74-diagnostic", "gemini_ready": bool(GEMINI_API_KEY)}

@app.api_route("/{path:path}", methods=["GET", "POST", "OPTIONS"])
async def catch_all(path: str):
    return JSONResponse(content={"status": "success"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
