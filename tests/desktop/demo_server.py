#!/usr/bin/env python3
"""
ClaudEditor + Kimi K2 快速測試服務器
用於演示和測試Kimi K2整合功能
"""

import asyncio
import logging
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# 設置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置
HF_TOKEN = os.getenv("HF_TOKEN", "<your_token_here>")

app = FastAPI(title="ClaudEditor + Kimi K2 Demo", version="1.0.0")

# CORS設置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 請求/響應模型
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: str = "kimi_k2"
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9

class ChatResponse(BaseModel):
    response: str
    model: str
    timestamp: str

# Kimi K2客戶端
class KimiK2Client:
    def __init__(self):
        self.hf_token = HF_TOKEN
        
    async def send_message(self, message: str, **kwargs) -> str:
        try:
            from huggingface_hub import InferenceClient
            
            client = InferenceClient(
                provider="novita",
                api_key=self.hf_token,
            )
            
            completion = client.chat.completions.create(
                model="moonshotai/Kimi-K2-Instruct",
                messages=[{"role": "user", "content": message}],
                max_tokens=kwargs.get("max_tokens", 1000),
                temperature=kwargs.get("temperature", 0.7)
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Kimi K2 API調用失敗: {e}")
            return f"抱歉，Kimi K2模型暫時不可用。錯誤: {str(e)}"

# 初始化客戶端
kimi_client = KimiK2Client()

@app.get("/", response_class=HTMLResponse)
async def home():
    """主頁面"""
    html_content = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ClaudEditor + Kimi K2 Demo</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .title { color: #333; display: flex; align-items: center; gap: 10px; }
        .status { padding: 10px 15px; background: #e3f2fd; border-radius: 4px; margin-top: 10px; }
        .chat-container { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .model-selector { margin-bottom: 20px; }
        .model-selector select { padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
        .messages { height: 400px; overflow-y: auto; border: 1px solid #eee; border-radius: 4px; padding: 15px; margin-bottom: 15px; background: #fafafa; }
        .message { margin-bottom: 15px; padding: 10px; border-radius: 8px; }
        .message.user { background: #e3f2fd; margin-left: 50px; }
        .message.assistant { background: #f3e5f5; margin-right: 50px; }
        .message .role { font-weight: bold; margin-bottom: 5px; }
        .message.user .role { color: #1976d2; }
        .message.assistant .role { color: #7b1fa2; }
        .input-container { display: flex; gap: 10px; }
        .input-container input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        .input-container button { padding: 10px 20px; background: #1976d2; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .input-container button:hover { background: #1565c0; }
        .input-container button:disabled { background: #ccc; cursor: not-allowed; }
        .loading { display: none; color: #666; font-style: italic; }
        .error { color: #d32f2f; background: #ffebee; padding: 10px; border-radius: 4px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">
                🧠 ClaudEditor + 🌙 Kimi K2 Demo
            </h1>
            <div class="status" id="status">
                <strong>狀態:</strong> <span id="status-text">正在檢查...</span>
            </div>
        </div>
        
        <div class="chat-container">
            <div class="model-selector">
                <label for="model-select"><strong>選擇AI模型:</strong></label>
                <select id="model-select">
                    <option value="kimi_k2">🌙 Kimi K2 (月之暗面)</option>
                    <option value="claude">🔵 Claude (模擬)</option>
                </select>
            </div>
            
            <div class="messages" id="messages">
                <div class="message assistant">
                    <div class="role">🌙 Kimi K2</div>
                    <div>你好！我是Kimi K2，月之暗面開發的AI助手。我擅長中文對話和複雜推理。有什麼我可以幫助你的嗎？</div>
                </div>
            </div>
            
            <div class="loading" id="loading">🌙 Kimi K2 正在思考中...</div>
            
            <div class="input-container">
                <input type="text" id="message-input" placeholder="輸入你的消息..." onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()" id="send-btn">發送</button>
            </div>
        </div>
    </div>

    <script>
        let isLoading = false;
        
        // 檢查服務狀態
        async function checkStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                document.getElementById('status-text').textContent = `✅ ${data.status} - Kimi K2已就緒`;
            } catch (error) {
                document.getElementById('status-text').textContent = '❌ 服務器連接失敗';
            }
        }
        
        // 發送消息
        async function sendMessage() {
            if (isLoading) return;
            
            const input = document.getElementById('message-input');
            const message = input.value.trim();
            if (!message) return;
            
            const model = document.getElementById('model-select').value;
            
            // 添加用戶消息
            addMessage('user', '👤 用戶', message);
            input.value = '';
            
            // 顯示載入狀態
            setLoading(true);
            
            try {
                const response = await fetch('/api/ai/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        messages: [{ role: 'user', content: message }],
                        model: model,
                        max_tokens: 1000,
                        temperature: 0.7
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    const modelIcon = model === 'kimi_k2' ? '🌙 Kimi K2' : '🔵 Claude';
                    addMessage('assistant', modelIcon, data.response);
                } else {
                    addMessage('assistant', '❌ 錯誤', `API調用失敗: ${data.detail || '未知錯誤'}`);
                }
                
            } catch (error) {
                addMessage('assistant', '❌ 錯誤', `網絡錯誤: ${error.message}`);
            }
            
            setLoading(false);
        }
        
        // 添加消息到聊天窗口
        function addMessage(type, role, content) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            messageDiv.innerHTML = `
                <div class="role">${role}</div>
                <div>${content}</div>
            `;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        // 設置載入狀態
        function setLoading(loading) {
            isLoading = loading;
            const loadingDiv = document.getElementById('loading');
            const sendBtn = document.getElementById('send-btn');
            
            if (loading) {
                loadingDiv.style.display = 'block';
                sendBtn.disabled = true;
                sendBtn.textContent = '發送中...';
            } else {
                loadingDiv.style.display = 'none';
                sendBtn.disabled = false;
                sendBtn.textContent = '發送';
            }
        }
        
        // 處理Enter鍵
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        // 初始化
        checkStatus();
    </script>
</body>
</html>
    '''
    return html_content

@app.get("/api/status")
async def get_status():
    """獲取系統狀態"""
    return {
        "status": "running",
        "message": "ClaudEditor + Kimi K2 Demo服務正常運行",
        "kimi_k2_available": True
    }

@app.get("/api/models")
async def get_models():
    """獲取可用模型列表"""
    return {
        "models": [
            {
                "id": "kimi_k2",
                "name": "🌙 Kimi K2 (月之暗面)",
                "provider": "novita",
                "description": "1T參數MoE架構，擅長中文和複雜推理"
            },
            {
                "id": "claude",
                "name": "🔵 Claude (模擬)",
                "provider": "anthropic",
                "description": "模擬回應，用於演示對比"
            }
        ]
    }

@app.post("/api/ai/chat")
async def ai_chat(request: ChatRequest):
    """AI聊天API"""
    try:
        message = request.messages[-1].content if request.messages else ""
        
        if request.model == "kimi_k2":
            # 調用真實的Kimi K2 API
            response = await kimi_client.send_message(
                message,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p
            )
        elif request.model == "claude":
            # 模擬Claude回應
            response = f"[模擬Claude回應] 感謝你的問題：「{message}」。這是一個演示回應，展示多模型支持功能。"
        else:
            raise HTTPException(status_code=400, detail="不支持的模型")
        
        return ChatResponse(
            response=response,
            model=request.model,
            timestamp="now"
        )
        
    except Exception as e:
        logger.error(f"聊天API錯誤: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info("🚀 啟動ClaudEditor + Kimi K2 Demo服務器")
    logger.info("🌐 訪問地址: http://localhost:8000")
    logger.info("🌙 Kimi K2已整合，可進行測試")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )