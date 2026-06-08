import os
import replicate
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = FastAPI()

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

@app.post("/edit-photo")
@limiter.limit("3/minute")
async def edit_photo(request: Request, prompt: str = Form(...), image: UploadFile = File(...)):
    try:
        output = replicate.run(
            "timbrooks/instruct-pix2pix:30c1d0b916a6f8efce20493f5d61ee27491ab2a60437c13c588468b9810ec23f",
            input={"image": image.file, "prompt": prompt}
        )
        return {"url": output[0]}
    except Exception as e:
        return {"error": str(e)}

html_code = """
<!DOCTYPE html>
<html>
<head><title>MarcoAI</title></head>
<body style="font-family:sans-serif;background:#111;color:#eee;padding:20px;">
<h1>MarcoAI_PLATFORM</h1>
<div id="tabs">
  <button onclick="showTab('chat')">Chat</button>
  <button onclick="showTab('photo')">Photo Edit</button>
</div>

<div id="chat-tab">
  <div id="chat" style="height:50vh;overflow-y:scroll;border:1px solid #444;padding:15px;background:#1a1a1a;border-radius:10px;margin:15px 0;"></div>
  <input id="msg" style="width:75%;padding:12px;background:#222;color:white;border:1px solid #444;border-radius:8px;" placeholder="Ask MarcoAI anything...">
  <button onclick="send()" style="width:22%;padding:12px;background:#0a84ff;color:white;border:none;border-radius:8px;">Send</button>
</div>

<div id="photo-tab" style="display:none;">
  <input type="file" id="img" accept="image/*" style="margin:15px 0;">
  <input id="editprompt" style="width:75%;padding:12px;background:#222;color:white;border:1px solid #444;border-radius:8px;" placeholder="Edit instruction: make it anime, add sunglasses...">
  <button onclick="editPhoto()" style="width:22%;padding:12px;background:#00ff88;color:black;border:none;border-radius:8px;">Edit Photo</button>
  <div id="result" style="margin-top:15px;"></div>
</div>

<script>
function showTab(tab) {
  document.getElementById('chat-tab').style.display = tab==='chat' ? 'block' : 'none';
  document.getElementById('photo-tab').style.display = tab==='photo' ? 'block' : 'none';
}
async function send() {
  const input = document.getElementById('msg');
  const chat = document.getElementById('chat');
  const msg = input.value.trim();
  if (!msg) return;
  chat.innerHTML += `<div style="text-align:right;margin:10px 0;"><b style="color:#0a84ff">You:</b> ${msg}</div>`;
  input.value = '';
  const res = await fetch('/chat', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})});
  const data = await res.json();
  chat.innerHTML += `<div style="margin:10px 0;"><b style="color:#00ff88">MarcoAI:</b> ${data.reply}</div>`;
  chat.scrollTop = chat.scrollHeight;
}
async function editPhoto() {
  const fileInput = document.getElementById('img');
  const prompt = document.getElementById('editprompt').value;
  const result = document.getElementById('result');
  if (!fileInput.files[0] || !prompt) {alert('Upload image + add prompt'); return;}
  result.innerHTML = 'Editing... takes 10-20 seconds';
  const formData = new FormData();
  formData.append('image', fileInput.files[0]);
  formData.append('prompt', prompt);
  const res = await fetch('/edit-photo', {method:'POST', body:formData});
  const data = await res.json();
  if(data.url) {result.innerHTML = `<img src="${data.url}" style="max-width:100%;border-radius:10px;">`;}
  else {result.innerHTML = `Error: ${data.error}`;}
}
document.getElementById('msg').addEventListener('keypress', e => { if(e.key==='Enter') send(); });
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def home():
    return html_code




