"""
Claude Code Router MCP - API服務器
提供HTTP API接口的FastAPI服務器
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn

from .router import claude_code_router_mcp
from .models import RouterRequest, RouterResponse, SupportedModel
from .config import RouterConfig
from .utils import RouterUtils

logger = logging.getLogger(__name__)

# 安全認證
security = HTTPBearer(auto_error=False)

# 請求模型
class ChatCompletionRequest(BaseModel):
    model: str = Field(..., description="模型名稱")
    messages: List[Dict[str, Any]] = Field(..., description="對話消息")
    max_tokens: Optional[int] = Field(4096, description="最大token數")
    temperature: Optional[float] = Field(0.7, description="溫度參數")
    top_p: Optional[float] = Field(1.0, description="top_p參數")
    frequency_penalty: Optional[float] = Field(0.0, description="頻率懲罰")
    presence_penalty: Optional[float] = Field(0.0, description="存在懲罰")
    stream: bool = Field(False, description="是否流式輸出")
    tools: Optional[List[Dict[str, Any]]] = Field(None, description="工具定義")
    tool_choice: Optional[str] = Field(None, description="工具選擇")
    user: Optional[str] = Field(None, description="用戶ID")

class ModelSwitchRequest(BaseModel):
    from_model: str = Field(..., description="源模型")
    to_model: str = Field(..., description="目標模型")

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    uptime: float

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    # 啟動時初始化
    await claude_code_router_mcp.initialize()
    
    yield
    
    # 關閉時清理
    await claude_code_router_mcp.cleanup()

# 創建FastAPI應用
app = FastAPI(
    title="Claude Code Router MCP API",
    description="多AI模型智能路由系統API服務",
    version="4.6.9.4",
    lifespan=lifespan
)

# 添加CORS中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 認證依賴
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """驗證API令牌"""
    # 開發模式下跳過認證
    if credentials is None:
        return "dev-token"
    # 這裡可以添加更複雜的認證邏輯
    if credentials.credentials != "your-auth-token":
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return credentials.credentials

# 請求日誌中間件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """記錄請求日誌"""
    start_time = time.time()
    
    # 記錄請求信息
    logger.info(f"📡 {request.method} {request.url.path} - {request.client.host}")
    
    # 處理請求
    response = await call_next(request)
    
    # 記錄響應信息
    process_time = time.time() - start_time
    logger.info(f"✅ {request.method} {request.url.path} - {response.status_code} ({process_time:.2f}s)")
    
    return response

@app.get("/", response_model=Dict[str, Any])
async def root():
    """根路徑"""
    return {
        "service": "Claude Code Router MCP API",
        "version": "4.6.9.4",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "chat": "/v1/chat/completions",
            "models": "/v1/models",
            "health": "/health",
            "stats": "/v1/stats",
            "switch": "/v1/switch"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康檢查"""
    status = claude_code_router_mcp.get_status()
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="4.6.9.4",
        uptime=status.get("uptime", 0)
    )

@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    auth_token: str = Depends(verify_token),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    聊天完成API - 兼容OpenAI格式
    支持多模型智能路由
    """
    try:
        # 驗證請求格式
        validation_result = RouterUtils.validate_request_format(request.dict())
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"請求格式錯誤: {', '.join(validation_result['errors'])}"
            )
        
        # 創建路由請求
        router_request = RouterRequest(
            model=request.model,
            messages=request.messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty,
            stream=request.stream,
            tools=request.tools,
            tool_choice=request.tool_choice,
            user_id=request.user,
            request_id=RouterUtils.generate_request_id()
        )
        
        # 如果是流式請求
        if request.stream:
            return StreamingResponse(
                _stream_response(router_request),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive"
                }
            )
        
        # 普通請求
        response = await claude_code_router_mcp.route_request(router_request)
        
        # 後台任務：更新統計
        background_tasks.add_task(_update_usage_stats, router_request, response)
        
        return JSONResponse(
            content=response.__dict__,
            headers={
                "X-Request-ID": router_request.request_id,
                "X-Model-Used": response.model,
                "X-Provider": response.provider.value if response.provider else "unknown",
                "X-Response-Time": f"{response.response_time:.2f}s",
                "X-Cached": str(response.cached),
                "X-Cost": f"${response.cost:.4f}"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 聊天完成失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def _stream_response(router_request: RouterRequest):
    """流式響應生成器"""
    try:
        # 這裡需要實現流式響應邏輯
        # 暫時返回非流式響應
        response = await claude_code_router_mcp.route_request(router_request)
        
        # 模擬流式輸出
        content = response.choices[0]["message"]["content"]
        words = content.split()
        
        for i, word in enumerate(words):
            chunk = {
                "id": response.id,
                "object": "chat.completion.chunk",
                "created": response.created,
                "model": response.model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": word + " " if i < len(words) - 1 else word},
                    "finish_reason": None if i < len(words) - 1 else "stop"
                }]
            }
            
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.05)  # 模擬延遲
        
        # 結束標記
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        error_chunk = {
            "error": {
                "message": str(e),
                "type": "server_error"
            }
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"

async def _update_usage_stats(request: RouterRequest, response: RouterResponse):
    """更新使用統計"""
    try:
        # 這裡可以添加統計邏輯
        logger.debug(f"📊 使用統計更新: {request.model} -> {response.model}")
    except Exception as e:
        logger.error(f"統計更新失敗: {e}")

@app.get("/v1/models")
async def list_models(auth_token: str = Depends(verify_token)):
    """獲取可用模型列表"""
    try:
        models = await claude_code_router_mcp.get_available_models()
        
        # 轉換為OpenAI格式
        model_list = [
            {
                "id": model["model_id"],
                "object": "model",
                "created": int(time.time()),
                "owned_by": model["provider"],
                "permission": [],
                "root": model["model_id"],
                "parent": None,
                "metadata": {
                    "supports_vision": model["supports_vision"],
                    "supports_function_calling": model["supports_function_calling"],
                    "context_window": model["context_window"],
                    "cost_per_1k_tokens": model["cost_per_1k_tokens"],
                    "priority": model["priority"],
                    "success_rate": model["success_rate"],
                    "avg_response_time": model["avg_response_time"],
                    "health_status": model["health_status"]
                }
            }
            for model in models
        ]
        
        return {
            "object": "list",
            "data": model_list
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取模型列表失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/models/{model_id}")
async def get_model(model_id: str, auth_token: str = Depends(verify_token)):
    """獲取特定模型信息"""
    try:
        models = await claude_code_router_mcp.get_available_models()
        
        for model in models:
            if model["model_id"] == model_id:
                return {
                    "id": model["model_id"],
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": model["provider"],
                    "permission": [],
                    "root": model["model_id"],
                    "parent": None,
                    "metadata": {
                        "supports_vision": model["supports_vision"],
                        "supports_function_calling": model["supports_function_calling"],
                        "context_window": model["context_window"],
                        "cost_per_1k_tokens": model["cost_per_1k_tokens"],
                        "priority": model["priority"],
                        "success_rate": model["success_rate"],
                        "avg_response_time": model["avg_response_time"],
                        "health_status": model["health_status"],
                        "formatted_info": RouterUtils.format_model_info(model)
                    }
                }
        
        raise HTTPException(status_code=404, detail=f"模型未找到: {model_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 獲取模型信息失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/stats")
async def get_stats(auth_token: str = Depends(verify_token)):
    """獲取路由統計信息"""
    try:
        stats = await claude_code_router_mcp.get_stats()
        status = claude_code_router_mcp.get_status()
        
        return {
            "router_stats": stats,
            "system_status": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取統計信息失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/switch")
async def switch_model(
    request: ModelSwitchRequest,
    auth_token: str = Depends(verify_token)
):
    """切換模型"""
    try:
        success = await claude_code_router_mcp.switch_model(
            request.from_model,
            request.to_model
        )
        
        if success:
            return {
                "success": True,
                "message": f"模型切換成功: {request.from_model} -> {request.to_model}",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"模型切換失敗: {request.from_model} -> {request.to_model}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 模型切換失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/providers/compare")
async def compare_providers(auth_token: str = Depends(verify_token)):
    """比較不同的Kimi K2 Provider"""
    try:
        models = await claude_code_router_mcp.get_available_models()
        
        # 篩選Kimi K2模型
        kimi_models = [
            model for model in models 
            if "kimi" in model["model_id"].lower() or "moonshot" in model["model_id"].lower()
        ]
        
        comparison = {
            "moonshot_official": None,
            "infini_ai_cloud": None,
            "recommendation": None
        }
        
        for model in kimi_models:
            if "api.moonshot.cn" in model.get("api_base", ""):
                comparison["moonshot_official"] = {
                    "model_id": model["model_id"],
                    "provider": "官方Moonshot API",
                    "api_base": "https://api.moonshot.cn/v1",
                    "advantages": [
                        "官方支持，穩定性最高",
                        "第一時間獲得新功能",
                        "完整的SLA保障",
                        "官方文檔支持"
                    ],
                    "disadvantages": [
                        "可能成本較高",
                        "可能有地域限制",
                        "速率限制可能較嚴格"
                    ],
                    "stats": {
                        "success_rate": model["success_rate"],
                        "avg_response_time": model["avg_response_time"],
                        "cost_per_1k_tokens": model["cost_per_1k_tokens"]
                    }
                }
            elif "cloud.infini-ai.com" in model.get("api_base", ""):
                comparison["infini_ai_cloud"] = {
                    "model_id": model["model_id"],
                    "provider": "Infini-AI Cloud代理",
                    "api_base": "https://cloud.infini-ai.com/maas/v1",
                    "advantages": [
                        "可能有成本優勢",
                        "可能有更高的速率限制",
                        "可能有CDN優化",
                        "可能有更好的可用性"
                    ],
                    "disadvantages": [
                        "第三方服務，穩定性依賴代理商",
                        "新功能可能有延遲",
                        "技術支持可能不如官方",
                        "存在額外的故障點"
                    ],
                    "stats": {
                        "success_rate": model["success_rate"],
                        "avg_response_time": model["avg_response_time"],
                        "cost_per_1k_tokens": model["cost_per_1k_tokens"]
                    }
                }
        
        # 生成建議
        if comparison["moonshot_official"] and comparison["infini_ai_cloud"]:
            moonshot_stats = comparison["moonshot_official"]["stats"]
            infini_stats = comparison["infini_ai_cloud"]["stats"]
            
            if moonshot_stats["success_rate"] > infini_stats["success_rate"]:
                primary_choice = "moonshot_official"
                reason = "官方API穩定性更高"
            elif infini_stats["cost_per_1k_tokens"] < moonshot_stats["cost_per_1k_tokens"]:
                primary_choice = "infini_ai_cloud"
                reason = "Infini-AI成本更低"
            else:
                primary_choice = "moonshot_official"
                reason = "官方API綜合表現更好"
                
            comparison["recommendation"] = {
                "primary_choice": primary_choice,
                "reason": reason,
                "strategy": "建議使用主選擇作為primary，另一個作為fallback",
                "load_balancing": "可以配置負載均衡，根據實際性能動態調整"
            }
        
        return {
            "comparison": comparison,
            "timestamp": datetime.now().isoformat(),
            "total_kimi_models": len(kimi_models)
        }
        
    except Exception as e:
        logger.error(f"❌ Provider比較失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 錯誤處理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局異常處理"""
    logger.error(f"❌ 全局異常: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "服務器內部錯誤",
                "type": "internal_server_error",
                "timestamp": datetime.now().isoformat()
            }
        }
    )

def start_server(host: str = "0.0.0.0", port: int = 8765, workers: int = 1):
    """啟動API服務器"""
    config = RouterConfig()
    
    uvicorn.run(
        "claude_code_router_mcp.api_server:app",
        host=host,
        port=port,
        workers=workers,
        log_level=config.log_level.lower(),
        reload=config.debug
    )

if __name__ == "__main__":
    start_server()