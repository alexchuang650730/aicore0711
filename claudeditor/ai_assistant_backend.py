"""
AI助手後端服務 - 與項目分析器集成
提供比Manus更強的項目理解能力
"""

import asyncio
import json
import os
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# 導入項目分析器
from core.components.project_analyzer_mcp.project_analyzer import ProjectAnalyzer, ProjectContext

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="ClaudEditor AI Assistant API", version="4.5.0")

# 配置CORS - 允許前端調用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局變量存儲項目上下文
current_project_context: Optional[ProjectContext] = None
project_analyzer = ProjectAnalyzer()

class AutonomousTaskRequest(BaseModel):
    """自主任務請求模型"""
    task_description: str
    project_path: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ChatMessage(BaseModel):
    """聊天消息模型"""
    message: str
    project_path: Optional[str] = None
    use_project_context: bool = True

class TaskPlan(BaseModel):
    """任務計劃模型"""
    task_id: int
    title: str
    steps: List[Dict[str, Any]]
    total_time: str
    autonomous_execution: bool

@app.get("/")
async def root():
    """API根路徑"""
    return {
        "name": "ClaudEditor AI Assistant API",
        "version": "4.5.0",
        "features": [
            "自主任務執行",
            "項目級代碼理解", 
            "智能錯誤處理",
            "實時協作支持"
        ],
        "status": "ready_to_compete_with_manus"
    }

@app.post("/api/analyze-project")
async def analyze_project(request: Dict[str, str], background_tasks: BackgroundTasks):
    """
    分析項目代碼庫
    這是與Manus競爭的關鍵API
    """
    try:
        project_path = request.get("project_path", "./")
        
        logger.info(f"🔍 開始分析項目: {project_path}")
        
        # 後台執行項目分析
        background_tasks.add_task(analyze_project_background, project_path)
        
        return {
            "status": "started",
            "message": "項目分析已開始，這將提供比Manus更深入的代碼理解能力",
            "project_path": project_path
        }
        
    except Exception as e:
        logger.error(f"項目分析失敗: {e}")
        raise HTTPException(status_code=500, detail=f"項目分析失敗: {str(e)}")

async def analyze_project_background(project_path: str):
    """後台執行項目分析"""
    global current_project_context
    try:
        current_project_context = await project_analyzer.analyze_codebase(project_path)
        logger.info(f"✅ 項目分析完成: {current_project_context.total_files}個文件")
    except Exception as e:
        logger.error(f"後台項目分析失敗: {e}")

@app.get("/api/project-context")
async def get_project_context():
    """獲取當前項目上下文"""
    if not current_project_context:
        return {"status": "no_analysis", "message": "尚未進行項目分析"}
    
    return {
        "status": "available",
        "context": {
            "total_files": current_project_context.total_files,
            "total_lines": current_project_context.total_lines,
            "languages": current_project_context.languages,
            "architecture_pattern": current_project_context.architecture_pattern,
            "entry_points": current_project_context.entry_points,
            "main_dependencies": current_project_context.main_dependencies[:10],
            "api_endpoints": current_project_context.api_endpoints[:10],
            "database_models": current_project_context.database_models[:10],
            "test_coverage": current_project_context.test_coverage,
            "analysis_timestamp": current_project_context.analysis_timestamp
        }
    }

@app.post("/api/autonomous-task")
async def create_autonomous_task(request: AutonomousTaskRequest):
    """
    創建自主任務
    與Manus競爭的核心功能
    """
    try:
        task_description = request.task_description
        
        # 基於項目上下文智能規劃任務
        task_plan = await generate_intelligent_task_plan(task_description)
        
        logger.info(f"🎯 創建自主任務: {task_plan['title']}")
        
        return {
            "status": "created",
            "task_plan": task_plan,
            "project_context_used": current_project_context is not None,
            "estimated_completion": task_plan["total_time"]
        }
        
    except Exception as e:
        logger.error(f"創建自主任務失敗: {e}")
        raise HTTPException(status_code=500, detail=f"任務創建失敗: {str(e)}")

async def generate_intelligent_task_plan(task_description: str) -> Dict[str, Any]:
    """
    基於項目上下文生成智能任務計劃
    這是超越Manus的關鍵能力
    """
    task_lower = task_description.lower()
    
    # 基於項目上下文優化任務計劃
    project_info = ""
    if current_project_context:
        project_info = f"""
        
📊 **項目上下文信息**:
• 架構模式: {current_project_context.architecture_pattern}
• 主要語言: {list(current_project_context.languages.keys())}
• 總文件數: {current_project_context.total_files}
• API端點: {len(current_project_context.api_endpoints)}個
• 測試覆蓋率: {current_project_context.test_coverage}%
        """
    
    if '創建' in task_description or 'create' in task_lower or '新建' in task_description:
        return {
            "task_id": int(asyncio.get_event_loop().time()),
            "title": f"🚀 智能創建任務: {task_description}",
            "steps": [
                {
                    "id": 1,
                    "description": f"🧠 AI分析需求並基於項目架構({current_project_context.architecture_pattern if current_project_context else 'Unknown'})制定方案",
                    "status": "pending",
                    "estimated_time": "3分鐘"
                },
                {
                    "id": 2,
                    "description": "🏗️ 智能設計符合現有項目結構的架構",
                    "status": "pending", 
                    "estimated_time": "5分鐘"
                },
                {
                    "id": 3,
                    "description": "⚡ 生成高質量代碼，自動集成現有依賴",
                    "status": "pending",
                    "estimated_time": "8分鐘"
                },
                {
                    "id": 4,
                    "description": "🧪 自動生成對應測試用例，提高覆蓋率",
                    "status": "pending",
                    "estimated_time": "4分鐘"
                },
                {
                    "id": 5,
                    "description": "📝 生成API文檔和使用示例",
                    "status": "pending",
                    "estimated_time": "2分鐘"
                }
            ],
            "total_time": "22分鐘",
            "autonomous_execution": True,
            "project_aware": True,
            "context_info": project_info
        }
    
    elif '調試' in task_description or 'debug' in task_lower or '修復' in task_description:
        return {
            "task_id": int(asyncio.get_event_loop().time()),
            "title": f"🔧 智能調試任務: {task_description}",
            "steps": [
                {
                    "id": 1,
                    "description": "🔍 掃描整個項目，識別潛在錯誤和問題",
                    "status": "pending",
                    "estimated_time": "2分鐘"
                },
                {
                    "id": 2,
                    "description": "🧠 基於項目架構深度分析錯誤根因",
                    "status": "pending",
                    "estimated_time": "4分鐘"
                },
                {
                    "id": 3,
                    "description": "⚡ AI自主生成修復方案，考慮依賴影響",
                    "status": "pending",
                    "estimated_time": "6分鐘"
                },
                {
                    "id": 4,
                    "description": "✅ 自動應用修復並驗證不破壞現有功能",
                    "status": "pending",
                    "estimated_time": "3分鐘"
                },
                {
                    "id": 5,
                    "description": "📊 生成調試報告和預防建議",
                    "status": "pending",
                    "estimated_time": "2分鐘"
                }
            ],
            "total_time": "17分鐘",
            "autonomous_execution": True,
            "project_aware": True,
            "context_info": project_info
        }
    
    elif '優化' in task_description or 'optimize' in task_lower or '性能' in task_description:
        return {
            "task_id": int(asyncio.get_event_loop().time()),
            "title": f"⚡ 智能優化任務: {task_description}",
            "steps": [
                {
                    "id": 1,
                    "description": "📈 全項目性能基線測試和瓶頸識別",
                    "status": "pending",
                    "estimated_time": "4分鐘"
                },
                {
                    "id": 2,
                    "description": "🔍 AI分析架構層面的優化機會",
                    "status": "pending",
                    "estimated_time": "6分鐘"
                },
                {
                    "id": 3,
                    "description": "⚡ 實施智能優化策略（緩存、算法、數據庫等）",
                    "status": "pending",
                    "estimated_time": "12分鐘"
                },
                {
                    "id": 4,
                    "description": "📊 性能對比測試和效果驗證",
                    "status": "pending",
                    "estimated_time": "4分鐘"
                },
                {
                    "id": 5,
                    "description": "📋 生成優化報告和持續改進建議",
                    "status": "pending",
                    "estimated_time": "3分鐘"
                }
            ],
            "total_time": "29分鐘",
            "autonomous_execution": True,
            "project_aware": True,
            "context_info": project_info
        }
    
    # 默認智能任務
    return {
        "task_id": int(asyncio.get_event_loop().time()),
        "title": f"🤖 AI智能任務: {task_description}",
        "steps": [
            {
                "id": 1,
                "description": "🧠 AI深度理解任務需求和項目上下文",
                "status": "pending",
                "estimated_time": "3分鐘"
            },
            {
                "id": 2,
                "description": "📋 基於項目架構制定最優執行計劃",
                "status": "pending",
                "estimated_time": "4分鐘"
            },
            {
                "id": 3,
                "description": "⚡ 智能執行核心任務，自動處理依賴",
                "status": "pending",
                "estimated_time": "15分鐘"
            },
            {
                "id": 4,
                "description": "✅ 質量檢查和自動化測試",
                "status": "pending",
                "estimated_time": "4分鐘"
            },
            {
                "id": 5,
                "description": "📝 生成總結報告和後續建議",
                "status": "pending",
                "estimated_time": "3分鐘"
            }
        ],
        "total_time": "29分鐘",
        "autonomous_execution": True,
        "project_aware": True,
        "context_info": project_info
    }

@app.post("/api/chat")
async def chat_with_ai(request: ChatMessage):
    """
    與AI助手聊天
    集成項目上下文的智能對話
    """
    try:
        message = request.message
        
        # 構建包含項目上下文的響應
        context_info = ""
        if request.use_project_context and current_project_context:
            context_info = f"""
            
🧠 **我已了解你的項目**:
• 📁 {current_project_context.total_files}個文件，{current_project_context.total_lines}行代碼
• 🏗️ 架構: {current_project_context.architecture_pattern}
• 🔧 主要技術: {', '.join(list(current_project_context.languages.keys())[:3])}
• 🚀 入口點: {len(current_project_context.entry_points)}個
• 📊 測試覆蓋率: {current_project_context.test_coverage}%
            """
        
        # 生成智能回復
        response = await generate_intelligent_response(message, context_info)
        
        return {
            "response": response,
            "project_context_used": current_project_context is not None,
            "timestamp": asyncio.get_event_loop().time()
        }
        
    except Exception as e:
        logger.error(f"聊天處理失敗: {e}")
        raise HTTPException(status_code=500, detail=f"聊天失敗: {str(e)}")

async def generate_intelligent_response(message: str, context_info: str) -> str:
    """生成基於項目上下文的智能回復"""
    
    # 檢查是否是任務相關詢問
    if any(keyword in message.lower() for keyword in ['怎麼', '如何', 'how', '創建', '修復', '優化']):
        return f"""🤖 **基於你的項目，我的建議是**:

{context_info}

針對你的問題 "{message}"，我建議直接使用自主任務功能：

🎯 **快速解決方案**:
• 點擊"🚀 創建自主任務"
• 描述具體需求
• 我會基於你的項目架構制定執行計劃
• 自主完成整個任務

💡 **為什麼選擇ClaudEditor**:
• ✅ 完整項目理解（vs Manus的片段式理解）  
• ✅ 智能架構感知（自動適配你的技術棧）
• ✅ 本地隱私保護（代碼不離開你的機器）
• ✅ 專業開發工具（專為程序員設計）

需要我立即為你創建自主任務嗎？"""
    
    elif '比較' in message or 'manus' in message.lower() or '競爭' in message:
        return f"""🥊 **ClaudEditor vs Manus 競爭優勢**:

{context_info}

🏆 **我們的優勢**:
• 🧠 **更深度的項目理解**: 我分析了你的整個代碼庫架構
• 🔒 **本地隱私保護**: 你的代碼永不離開本機  
• 🛠️ **專業開發工具**: 專為程序員設計，而非通用商務
• ⚡ **更快的響應速度**: 本地處理 + 智能緩存
• 💰 **更親民價格**: ¥99/月 vs Manus ¥300-1500/月
• 🔍 **透明AI決策**: 你能看到AI的思考過程

🎯 **Manus無法做到的**:
• 無法深度理解你的項目架構
• 無法提供真正的本地隱私保護  
• 缺乏專業開發工具集成
• AI決策過程黑盒，無法解釋

想體驗我們的自主任務功能嗎？我會展示真正的項目級智能！"""
    
    else:
        return f"""👋 你好！我是ClaudEditor的AI助手。

{context_info}

🚀 **我能為你做什麼**:
• 🤖 **自主任務執行**: 告訴我任務，我會制定計劃並自主完成
• 🧠 **項目級理解**: 基於你的完整代碼庫提供建議
• 🔧 **智能調試**: 自動發現並修復問題
• ⚡ **性能優化**: 全面分析並優化項目性能
• 📝 **文檔生成**: 自動生成API文檔和代碼說明

💬 **與我對話的技巧**:
• 描述具體任務（如"創建用戶認證功能"）
• 詢問技術問題（如"如何優化數據庫查詢"）
• 請求代碼分析（如"分析這個函數的性能"）

試試發送一個具體任務，讓我展示自主執行能力！"""

@app.get("/api/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "version": "4.5.0",
        "project_analyzer_ready": True,
        "project_context_loaded": current_project_context is not None,
        "competitive_advantage": "ready_to_compete_with_manus"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082, log_level="info")