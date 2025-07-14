#!/usr/bin/env python3
"""
ClaudEditor + Kimi K2 演示版本 - 不依賴外部API權限
展示完整的UI和功能，使用模擬的AI回應
"""

import asyncio
import logging
import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime

# 設置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    messages: List[ChatMessage] = []
    message: Optional[str] = None  # 兼容不同格式
    model: str = "kimi_k2"
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9

class ChatResponse(BaseModel):
    response: str
    model: str
    timestamp: str

# 模擬AI回應生成器
class MockAIClient:
    def __init__(self):
        self.kimi_responses = [
            "你好！我是Kimi K2，月之暗面開發的大型語言模型。我擅長中文理解和生成，具有1萬億參數的MoE架構。",
            "作為Kimi K2，我可以幫助你進行代碼分析、文本創作、邏輯推理等任務。我的中文能力特別強，能理解複雜的語境。",
            "我基於Transformer架構和混合專家模型(MoE)設計，擁有強大的多任務處理能力。有什麼具體問題我可以幫助你解決呢？",
            "Kimi K2支持長達128K的上下文窗口，能處理長篇文档和複雜對話。我也支持多輪對話和上下文理解。",
            "作為月之暗面的旗艦模型，我在代碼生成、數學推理、創意寫作等方面都有不錯的表現。請告訴我你需要什麼幫助！"
        ]
        
        self.claude_responses = [
            "我是Claude，Anthropic開發的AI助手。我可以協助你進行各種任務，包括寫作、分析、編程等。",
            "作為Claude，我注重準確性和有用性。我會盡力提供清晰、有條理的回答來幫助你。",
            "我擅長邏輯推理、創意寫作和技術問題解答。有什麼我可以為你做的嗎？",
            "Claude致力於提供安全、有幫助的AI協助。我會根據上下文給出最合適的回應。",
            "我可以幫助你處理複雜的分析任務、代碼調試、文档撰寫等工作。請告訴我你的需求！"
        ]
        
        self.response_count = {"kimi_k2": 0, "claude": 0}
    
    async def generate_response(self, message: str, model: str, **kwargs) -> str:
        """生成模擬AI回應"""
        await asyncio.sleep(0.5)  # 模擬API延遲
        
        if model == "kimi_k2":
            responses = self.kimi_responses
            prefix = "🌙 "
        else:
            responses = self.claude_responses  
            prefix = "🔵 "
        
        # 根據輸入生成相關回應
        if "你好" in message or "hello" in message.lower():
            base_response = responses[0]
        elif "代碼" in message or "code" in message.lower():
            base_response = f"我來幫你分析代碼問題。{responses[1]}"
        elif "功能" in message or "feature" in message.lower():
            base_response = f"關於功能問題：{responses[2]}"
        elif "測試" in message or "test" in message.lower():
            base_response = f"測試相關問題我很樂意協助。{responses[3]}"
        else:
            # 循環使用不同回應
            count = self.response_count[model]
            base_response = responses[count % len(responses)]
            self.response_count[model] += 1
        
        # 添加針對性回應
        response = f"{prefix}{base_response}\n\n對於你的問題「{message}」，我會根據我的訓練為你提供最佳的幫助。"
        
        return response

# 初始化模擬客戶端
mock_client = MockAIClient()

@app.get("/", response_class=HTMLResponse)
async def home():
    """主頁面 - 增強版ClaudEditor界面"""
    html_content = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ClaudEditor v4.2 + Kimi K2 Demo</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f7fa; }
        
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; padding: 15px 20px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header-content { max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; }
        .logo { font-size: 24px; font-weight: bold; display: flex; align-items: center; gap: 10px; }
        .status-badge { background: rgba(255,255,255,0.2); padding: 5px 12px; border-radius: 20px; font-size: 12px; }
        
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .main-content { display: grid; grid-template-columns: 250px 1fr; gap: 20px; }
        
        .sidebar { background: white; border-radius: 8px; padding: 20px; height: fit-content; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .nav-section h3 { color: #333; margin-bottom: 15px; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; }
        .nav-item { 
            padding: 10px 15px; margin-bottom: 5px; border-radius: 6px; cursor: pointer; 
            display: flex; align-items: center; gap: 10px; transition: all 0.2s;
        }
        .nav-item:hover { background: #f0f2f5; }
        .nav-item.active { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        
        .chat-panel { background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden; }
        .panel-header { 
            background: #f8f9fa; padding: 20px; border-bottom: 1px solid #e9ecef;
            display: flex; justify-content: space-between; align-items: center;
        }
        .panel-title { font-size: 18px; font-weight: 600; color: #333; }
        
        .model-controls { display: flex; gap: 15px; align-items: center; }
        .model-select { 
            padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; 
            background: white; font-size: 14px; min-width: 200px;
        }
        .params-btn { 
            padding: 8px 12px; background: #6c757d; color: white; border: none; 
            border-radius: 6px; cursor: pointer; font-size: 12px;
        }
        .params-btn:hover { background: #5a6268; }
        
        .params-panel { 
            background: #f8f9fa; padding: 15px 20px; border-bottom: 1px solid #e9ecef;
            display: none; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;
        }
        .param-group label { display: block; margin-bottom: 5px; font-size: 12px; color: #666; }
        .param-group input { width: 100%; padding: 5px; border: 1px solid #ddd; border-radius: 4px; }
        
        .messages { 
            height: 450px; overflow-y: auto; padding: 20px; 
            background: linear-gradient(to bottom, #fafbfc, #ffffff);
        }
        .message { 
            margin-bottom: 20px; padding: 15px; border-radius: 12px; 
            max-width: 80%; position: relative; animation: fadeIn 0.3s ease-out;
        }
        .message.user { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; margin-left: auto; 
        }
        .message.assistant { 
            background: #f8f9fa; border: 1px solid #e9ecef; 
            margin-right: auto;
        }
        .message-header { 
            display: flex; justify-content: space-between; align-items: center; 
            margin-bottom: 8px; font-size: 12px;
        }
        .model-tag { 
            background: rgba(0,0,0,0.1); padding: 2px 8px; border-radius: 10px; 
            font-weight: 500;
        }
        .timestamp { opacity: 0.7; }
        
        .input-container { 
            padding: 20px; background: #f8f9fa; border-top: 1px solid #e9ecef;
            display: flex; gap: 10px; align-items: flex-end;
        }
        .message-input { 
            flex: 1; padding: 12px 15px; border: 1px solid #ddd; border-radius: 25px; 
            resize: none; font-family: inherit; min-height: 44px; max-height: 120px;
        }
        .send-btn { 
            padding: 12px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; border: none; border-radius: 25px; cursor: pointer; font-weight: 500;
        }
        .send-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); }
        .send-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        
        .loading { 
            display: none; padding: 10px 20px; color: #666; font-style: italic;
            background: #fff3cd; border-radius: 6px; margin: 10px 20px;
        }
        
        .comparison-panel {
            background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 20px; display: none;
        }
        .model-checkboxes {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 10px; margin: 15px 0;
        }
        .model-checkbox {
            display: flex; align-items: center; gap: 8px; padding: 10px; 
            border: 1px solid #ddd; border-radius: 6px; cursor: pointer;
        }
        .model-checkbox:hover { background: #f8f9fa; }
        .comparison-input { 
            width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 6px; 
            margin: 15px 0; resize: vertical; height: 80px;
        }
        .compare-btn {
            padding: 10px 20px; background: #28a745; color: white; border: none; 
            border-radius: 6px; cursor: pointer; font-weight: 500;
        }
        .comparison-results { margin-top: 20px; }
        .comparison-result { 
            background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; 
            margin-bottom: 15px; overflow: hidden;
        }
        .result-header { 
            background: #e9ecef; padding: 10px 15px; font-weight: 500; 
            display: flex; justify-content: space-between; align-items: center;
        }
        .result-content { padding: 15px; }
        
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        
        .notification {
            position: fixed; top: 20px; right: 20px; background: #667eea; color: white;
            padding: 12px 20px; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            display: none; z-index: 1000; animation: slideIn 0.3s ease-out;
        }
        @keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }
        
        @media (max-width: 768px) {
            .main-content { grid-template-columns: 1fr; }
            .sidebar { order: 2; }
            .model-controls { flex-direction: column; align-items: stretch; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <div class="logo">
                🧠 ClaudEditor v4.2 + 🌙 Kimi K2
            </div>
            <div class="status-badge" id="status-badge">
                ✅ 已就緒
            </div>
        </div>
    </div>
    
    <div class="container">
        <div class="main-content">
            <div class="sidebar">
                <div class="nav-section">
                    <h3>核心功能</h3>
                    <div class="nav-item active" data-panel="chat">
                        <span>🤖</span> AI助手
                    </div>
                    <div class="nav-item" data-panel="comparison">
                        <span>⚖️</span> 模型對比
                    </div>
                </div>
            </div>
            
            <div class="content-area">
                <!-- AI聊天面板 -->
                <div class="chat-panel" id="chat-panel">
                    <div class="panel-header">
                        <div class="panel-title">AI助手</div>
                        <div class="model-controls">
                            <select class="model-select" id="model-select">
                                <option value="kimi_k2">🌙 Kimi K2 (月之暗面)</option>
                                <option value="claude">🔵 Claude (Anthropic)</option>
                            </select>
                            <button class="params-btn" onclick="toggleParams()">⚙️ 參數</button>
                        </div>
                    </div>
                    
                    <div class="params-panel" id="params-panel">
                        <div class="param-group">
                            <label>Temperature: <span id="temp-value">0.7</span></label>
                            <input type="range" id="temperature" min="0" max="1" step="0.1" value="0.7" oninput="updateValue('temp-value', this.value)">
                        </div>
                        <div class="param-group">
                            <label>Top P: <span id="topp-value">0.9</span></label>
                            <input type="range" id="top-p" min="0" max="1" step="0.1" value="0.9" oninput="updateValue('topp-value', this.value)">
                        </div>
                        <div class="param-group">
                            <label>Max Tokens</label>
                            <input type="number" id="max-tokens" min="50" max="2000" value="1000">
                        </div>
                    </div>
                    
                    <div class="messages" id="messages">
                        <div class="message assistant">
                            <div class="message-header">
                                <span class="model-tag">🌙 Kimi K2</span>
                                <span class="timestamp">現在</span>
                            </div>
                            <div>你好！歡迎使用ClaudEditor v4.2！我是集成的Kimi K2模型，月之暗面開發的大型語言模型。我可以幫助你進行代碼分析、文本創作、邏輯推理等任務。試試切換不同的AI模型，或使用模型對比功能！</div>
                        </div>
                    </div>
                    
                    <div class="loading" id="loading">
                        🌙 AI正在思考中...
                    </div>
                    
                    <div class="input-container">
                        <textarea class="message-input" id="message-input" placeholder="輸入你的消息..." rows="1" onkeypress="handleKeyPress(event)"></textarea>
                        <button class="send-btn" onclick="sendMessage()" id="send-btn">發送</button>
                    </div>
                </div>
                
                <!-- 模型對比面板 -->
                <div class="comparison-panel" id="comparison-panel">
                    <h2>🔬 AI模型對比</h2>
                    <p>同時詢問多個AI模型，比較它們的回應差異：</p>
                    
                    <div class="model-checkboxes">
                        <label class="model-checkbox">
                            <input type="checkbox" value="kimi_k2" checked>
                            🌙 Kimi K2 (月之暗面)
                        </label>
                        <label class="model-checkbox">
                            <input type="checkbox" value="claude" checked>
                            🔵 Claude (Anthropic)
                        </label>
                    </div>
                    
                    <textarea class="comparison-input" id="comparison-input" placeholder="輸入要對比的問題..."></textarea>
                    <button class="compare-btn" onclick="compareModels()">🚀 詢問所有選中的模型</button>
                    
                    <div class="comparison-results" id="comparison-results"></div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="notification" id="notification">
        <span id="notification-text"></span>
    </div>

    <script>
        let isLoading = false;
        let currentPanel = 'chat';
        
        // 初始化
        document.addEventListener('DOMContentLoaded', function() {
            checkServerStatus();
            setupNavigation();
            autoResizeTextarea();
        });
        
        // 設置導航
        function setupNavigation() {
            document.querySelectorAll('.nav-item').forEach(item => {
                item.addEventListener('click', function() {
                    const panel = this.dataset.panel;
                    switchPanel(panel);
                });
            });
        }
        
        // 切換面板
        function switchPanel(panel) {
            // 更新導航狀態
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
            });
            document.querySelector(`[data-panel="${panel}"]`).classList.add('active');
            
            // 顯示對應面板
            document.getElementById('chat-panel').style.display = panel === 'chat' ? 'block' : 'none';
            document.getElementById('comparison-panel').style.display = panel === 'comparison' ? 'block' : 'none';
            
            currentPanel = panel;
        }
        
        // 檢查服務器狀態
        async function checkServerStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                document.getElementById('status-badge').textContent = '✅ ' + data.status;
            } catch (error) {
                document.getElementById('status-badge').textContent = '❌ 離線';
            }
        }
        
        // 切換參數面板
        function toggleParams() {
            const panel = document.getElementById('params-panel');
            panel.style.display = panel.style.display === 'grid' ? 'none' : 'grid';
        }
        
        // 更新參數值顯示
        function updateValue(elementId, value) {
            document.getElementById(elementId).textContent = value;
        }
        
        // 自動調整文本框高度
        function autoResizeTextarea() {
            const textarea = document.getElementById('message-input');
            textarea.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = (this.scrollHeight) + 'px';
            });
        }
        
        // 發送消息
        async function sendMessage() {
            if (isLoading) return;
            
            const input = document.getElementById('message-input');
            const message = input.value.trim();
            if (!message) return;
            
            const model = document.getElementById('model-select').value;
            const temperature = parseFloat(document.getElementById('temperature').value);
            const topP = parseFloat(document.getElementById('top-p').value);
            const maxTokens = parseInt(document.getElementById('max-tokens').value);
            
            // 添加用戶消息
            addMessage('user', '👤 您', message);
            input.value = '';
            input.style.height = 'auto';
            
            // 顯示載入狀態
            setLoading(true);
            
            try {
                const response = await fetch('/api/ai/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: message,
                        model: model,
                        max_tokens: maxTokens,
                        temperature: temperature,
                        top_p: topP
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    const modelIcon = model === 'kimi_k2' ? '🌙 Kimi K2' : '🔵 Claude';
                    addMessage('assistant', modelIcon, data.response);
                    showNotification(`${modelIcon} 回應完成`);
                } else {
                    addMessage('assistant', '❌ 錯誤', `API調用失敗: ${data.detail || '未知錯誤'}`);
                }
                
            } catch (error) {
                addMessage('assistant', '❌ 錯誤', `網絡錯誤: ${error.message}`);
            }
            
            setLoading(false);
        }
        
        // 模型對比
        async function compareModels() {
            const input = document.getElementById('comparison-input');
            const question = input.value.trim();
            if (!question) return;
            
            const checkboxes = document.querySelectorAll('.model-checkbox input:checked');
            const selectedModels = Array.from(checkboxes).map(cb => cb.value);
            
            if (selectedModels.length === 0) {
                showNotification('請至少選擇一個模型');
                return;
            }
            
            const resultsDiv = document.getElementById('comparison-results');
            resultsDiv.innerHTML = '<p>🔄 正在獲取各模型回應...</p>';
            
            const results = [];
            
            for (const model of selectedModels) {
                try {
                    const response = await fetch('/api/ai/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            message: question,
                            model: model,
                            max_tokens: 800,
                            temperature: 0.7
                        })
                    });
                    
                    const data = await response.json();
                    results.push({
                        model: model,
                        name: model === 'kimi_k2' ? '🌙 Kimi K2' : '🔵 Claude',
                        response: response.ok ? data.response : `錯誤: ${data.detail}`,
                        success: response.ok
                    });
                    
                } catch (error) {
                    results.push({
                        model: model,
                        name: model === 'kimi_k2' ? '🌙 Kimi K2' : '🔵 Claude',
                        response: `網絡錯誤: ${error.message}`,
                        success: false
                    });
                }
            }
            
            // 顯示對比結果
            displayComparisonResults(question, results);
        }
        
        // 顯示對比結果
        function displayComparisonResults(question, results) {
            const resultsDiv = document.getElementById('comparison-results');
            
            let html = `
                <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <strong>🤔 對比問題:</strong> ${question}
                </div>
            `;
            
            results.forEach((result, index) => {
                const statusIcon = result.success ? '✅' : '❌';
                html += `
                    <div class="comparison-result">
                        <div class="result-header">
                            <span>${result.name}</span>
                            <span>${statusIcon}</span>
                        </div>
                        <div class="result-content">
                            ${result.response}
                        </div>
                    </div>
                `;
            });
            
            resultsDiv.innerHTML = html;
            showNotification('對比完成！');
        }
        
        // 添加消息到聊天窗口
        function addMessage(type, role, content) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            
            const now = new Date().toLocaleTimeString('zh-CN', { hour12: false });
            messageDiv.innerHTML = `
                <div class="message-header">
                    <span class="model-tag">${role}</span>
                    <span class="timestamp">${now}</span>
                </div>
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
            
            loadingDiv.style.display = loading ? 'block' : 'none';
            sendBtn.disabled = loading;
            sendBtn.textContent = loading ? '發送中...' : '發送';
        }
        
        // 顯示通知
        function showNotification(message) {
            const notification = document.getElementById('notification');
            const notificationText = document.getElementById('notification-text');
            
            notificationText.textContent = message;
            notification.style.display = 'block';
            
            setTimeout(() => {
                notification.style.display = 'none';
            }, 3000);
        }
        
        // 處理Enter鍵
        function handleKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }
        
        // 模型切換事件
        document.getElementById('model-select').addEventListener('change', function() {
            const model = this.value;
            const modelName = model === 'kimi_k2' ? 'Kimi K2' : 'Claude';
            showNotification(`已切換到 ${modelName} 模型`);
        });
    </script>
</body>
</html>
    '''
    return html_content

@app.get("/api/status")
async def get_status():
    """獲取系統狀態"""
    return {
        "status": "運行中",
        "message": "ClaudEditor + Kimi K2 Demo服務正常運行",
        "kimi_k2_available": True,
        "timestamp": datetime.now().isoformat()
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
                "description": "1T參數MoE架構，擅長中文和複雜推理",
                "context_window": 128000,
                "max_tokens": 4096
            },
            {
                "id": "claude",
                "name": "🔵 Claude (Anthropic)",
                "provider": "anthropic", 
                "description": "Constitutional AI，注重安全和有用性",
                "context_window": 100000,
                "max_tokens": 4096
            }
        ]
    }

@app.post("/api/ai/chat")
async def ai_chat(request: ChatRequest):
    """AI聊天API"""
    try:
        # 處理消息
        if request.message:
            message = request.message
        elif request.messages:
            message = request.messages[-1].content
        else:
            raise HTTPException(status_code=400, detail="未提供消息內容")
        
        # 生成AI回應
        response = await mock_client.generate_response(
            message=message,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p
        )
        
        return ChatResponse(
            response=response,
            model=request.model,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"聊天API錯誤: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info("🚀 啟動ClaudEditor + Kimi K2 演示服務器")
    logger.info("🌐 訪問地址: http://localhost:8001")
    logger.info("🌙 Kimi K2演示版已就緒，包含完整UI和功能")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )