import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

app = FastAPI()

# Rate limiter: 10 messages per minute per person
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
@limiter.limit("10/minute")
async def chat(request: Request, chat_req: ChatRequest):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are MarcoAI, a helpful assistant built by Zaid."},
                {"role": "user", "content": chat_req.message}
            ]
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        return {"reply": f"API Error: {str(e)}"}

html_code = """
<!DOCTYPE html>
<html>
<head><title>MarcoAI</title></head>
<body style="font-family:sans-serif;background:#111;color:#eee;padding:20px;">
<h1>MarcoAI_PLATFORM</h1>
<div id="chat" style="height:60vh;overflow-y:scroll;border:1px solid #444;padding:15px;background:#1a1a1a;border-radius:10px;margin-bottom:15px;"></div>
<input id="msg" style="width:75%;padding:12px;background:#222;color:white;border:1px solid #444;border-radius:8px;" placeholder="Ask MarcoAI anything...">
<button onclick="send()" style="width:22%;padding:12px;background:#0a84ff;color:white;border:none;border-radius:8px;">Send</button>
<script>
async function send() {
  const input = document.getElementById('msg');
  const chat = document.getElementById('chat');
  const msg = input.value.trim();
  if (!msg) return;
  chat.innerHTML += `<div style="text-align:right;margin:10px 0;"><b style="color:#0a84ff">You:</b> ${msg}</div>`;
  input.value = '';
  chat.scrollTop = chat.scrollHeight;
  try {
    const res = await fetch('/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({message: msg}) });
    const data = await res.json();
    chat.innerHTML += `<div style="margin:10px 0;"><b style="color:#00ff88">MarcoAI:</b> ${data.reply}</div>`;
  } catch(err) {
    chat.innerHTML += `<div style="color:red;margin:10px 0;">Error: Too many requests. Wait 1 minute.</div>`;
  }
  chat.scrollTop = chat.scrollHeight;
}
document.getElementById('msg').addEventListener('keypress', e => { if(e.key==='Enter') send(); });
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def home():
    return html_code

70 lines hidden
