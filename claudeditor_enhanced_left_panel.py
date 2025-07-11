#!/usr/bin/env python3
"""
PowerAutomation v4.6.1 ClaudEditor左側面板增強
Enhanced Left Panel for ClaudEditor

🎛️ 左側面板完整功能:
1. 工作流導航和階段進度
2. 快速操作區 (Quick Actions)
3. 模型使用統計 (Model Usage)
4. Token使用和節省統計
5. 代碼倉庫管理 (Repository Manager)
6. 快速Import功能
7. 項目儀表板
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """AI模型類型"""
    CLAUDE_SONNET = "claude-sonnet-4"
    CLAUDE_HAIKU = "claude-haiku-3" 
    CLAUDE_OPUS = "claude-opus-3"
    GPT_4 = "gpt-4-turbo"
    CODELLAMA = "codellama-70b"
    CUSTOM_MODEL = "custom-model"

class QuickActionType(Enum):
    """快速操作類型"""
    GENERATE_CODE = "generate_code"
    RUN_TESTS = "run_tests"
    DEBUG_CODE = "debug_code"
    OPTIMIZE_PERFORMANCE = "optimize_performance"
    CREATE_DOCS = "create_docs"
    REFACTOR_CODE = "refactor_code"
    IMPORT_REPO = "import_repo"
    EXPORT_PROJECT = "export_project"
    DEPLOY_BUILD = "deploy_build"
    ANALYZE_QUALITY = "analyze_quality"

class RepositoryProvider(Enum):
    """代碼倉庫提供商"""
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    AZURE_DEVOPS = "azure_devops"
    LOCAL_GIT = "local_git"
    ZIP_UPLOAD = "zip_upload"

@dataclass
class ModelUsageStats:
    """模型使用統計"""
    model_type: ModelType
    total_requests: int = 0
    total_tokens_used: int = 0
    total_tokens_saved: int = 0
    avg_response_time: float = 0.0
    success_rate: float = 100.0
    cost_estimate: float = 0.0
    last_used: Optional[str] = None

@dataclass
class TokenUsageSummary:
    """Token使用摘要"""
    today_used: int = 0
    today_saved: int = 0
    this_week_used: int = 0
    this_week_saved: int = 0
    this_month_used: int = 0
    this_month_saved: int = 0
    efficiency_score: float = 0.0
    cost_saved_usd: float = 0.0

@dataclass
class RepositoryInfo:
    """倉庫信息"""
    repo_id: str
    name: str
    provider: RepositoryProvider
    url: str
    branch: str
    last_sync: Optional[str] = None
    file_count: int = 0
    languages: List[str] = field(default_factory=list)
    size_mb: float = 0.0
    is_connected: bool = False

@dataclass
class QuickAction:
    """快速操作"""
    action_type: QuickActionType
    display_name: str
    description: str
    icon: str
    shortcut: str
    enabled: bool = True
    category: str = "general"

class ClaudEditorLeftPanel:
    """ClaudEditor左側面板管理器"""
    
    def __init__(self):
        self.model_stats: Dict[ModelType, ModelUsageStats] = {}
        self.token_summary = TokenUsageSummary()
        self.repositories: List[RepositoryInfo] = []
        self.quick_actions = self._initialize_quick_actions()
        self.current_project_stats = {}
        
    def _initialize_quick_actions(self) -> List[QuickAction]:
        """初始化快速操作"""
        return [
            # 代碼相關操作
            QuickAction(
                QuickActionType.GENERATE_CODE,
                "生成代碼",
                "基於需求自動生成代碼",
                "💻",
                "Ctrl+G",
                category="code"
            ),
            QuickAction(
                QuickActionType.REFACTOR_CODE,
                "重構代碼", 
                "智能重構和優化代碼結構",
                "🔧",
                "Ctrl+R",
                category="code"
            ),
            QuickAction(
                QuickActionType.DEBUG_CODE,
                "調試助手",
                "AI輔助代碼調試和錯誤修復",
                "🐛",
                "Ctrl+D",
                category="debug"
            ),
            
            # 測試相關操作
            QuickAction(
                QuickActionType.RUN_TESTS,
                "運行測試",
                "執行自動化測試套件",
                "🧪",
                "Ctrl+T",
                category="test"
            ),
            QuickAction(
                QuickActionType.ANALYZE_QUALITY,
                "質量分析",
                "分析代碼質量和性能指標",
                "📊",
                "Ctrl+Q",
                category="quality"
            ),
            
            # 文檔和優化
            QuickAction(
                QuickActionType.CREATE_DOCS,
                "生成文檔",
                "自動生成API文檔和代碼注釋",
                "📚",
                "Ctrl+Shift+D",
                category="docs"
            ),
            QuickAction(
                QuickActionType.OPTIMIZE_PERFORMANCE,
                "性能優化",
                "分析和優化代碼性能",
                "⚡",
                "Ctrl+O",
                category="optimization"
            ),
            
            # 倉庫管理
            QuickAction(
                QuickActionType.IMPORT_REPO,
                "導入倉庫",
                "快速導入Git倉庫或項目",
                "📥",
                "Ctrl+I",
                category="repo"
            ),
            QuickAction(
                QuickActionType.EXPORT_PROJECT,
                "導出項目",
                "導出項目到Git倉庫或ZIP文件",
                "📤",
                "Ctrl+E",
                category="repo"
            ),
            
            # 部署操作
            QuickAction(
                QuickActionType.DEPLOY_BUILD,
                "部署構建",
                "執行項目構建和部署",
                "🚀",
                "Ctrl+Shift+B",
                category="deploy"
            )
        ]
    
    def render_left_panel(self, current_workflow: str, current_stage: str) -> Dict[str, Any]:
        """渲染完整的左側面板"""
        return {
            "panel_config": {
                "width": "300px",
                "resizable": True,
                "collapsible": True,
                "sections": [
                    "workflow_navigation",
                    "quick_actions", 
                    "model_usage",
                    "token_stats",
                    "repository_manager",
                    "project_dashboard"
                ]
            },
            "sections": {
                "workflow_navigation": self._render_workflow_navigation(current_workflow, current_stage),
                "quick_actions": self._render_quick_actions(),
                "model_usage": self._render_model_usage(),
                "token_stats": self._render_token_stats(),
                "repository_manager": self._render_repository_manager(),
                "project_dashboard": self._render_project_dashboard()
            },
            "styling": self._get_left_panel_styling()
        }
    
    def _render_workflow_navigation(self, current_workflow: str, current_stage: str) -> Dict[str, Any]:
        """渲染工作流導航區域"""
        return {
            "section_id": "workflow_navigation",
            "title": "🔧 工作流導航",
            "collapsible": False,
            "content": {
                "current_workflow": {
                    "name": current_workflow,
                    "display_name": self._get_workflow_display_name(current_workflow),
                    "icon": self._get_workflow_icon(current_workflow)
                },
                "stage_progress": {
                    "current_stage": current_stage,
                    "completed_stages": self._get_completed_stages(),
                    "total_stages": self._get_total_stages(),
                    "progress_percentage": self._calculate_progress_percentage()
                },
                "stage_list": self._get_stage_list_with_status(),
                "workflow_controls": {
                    "buttons": [
                        {"id": "prev_stage", "label": "上一階段", "icon": "⬅️", "enabled": True},
                        {"id": "next_stage", "label": "下一階段", "icon": "➡️", "enabled": True},
                        {"id": "skip_stage", "label": "跳過", "icon": "⏭️", "enabled": False},
                        {"id": "restart_workflow", "label": "重新開始", "icon": "🔄", "enabled": True}
                    ]
                }
            }
        }
    
    def _render_quick_actions(self) -> Dict[str, Any]:
        """渲染快速操作區域"""
        # 按類別組織快速操作
        actions_by_category = {}
        for action in self.quick_actions:
            if action.category not in actions_by_category:
                actions_by_category[action.category] = []
            actions_by_category[action.category].append({
                "id": action.action_type.value,
                "name": action.display_name,
                "description": action.description,
                "icon": action.icon,
                "shortcut": action.shortcut,
                "enabled": action.enabled
            })
        
        return {
            "section_id": "quick_actions",
            "title": "⚡ 快速操作",
            "collapsible": True,
            "collapsed": False,
            "content": {
                "layout": "grid",
                "columns": 2,
                "categories": {
                    "code": {
                        "name": "代碼操作",
                        "actions": actions_by_category.get("code", [])
                    },
                    "test": {
                        "name": "測試調試", 
                        "actions": actions_by_category.get("test", []) + actions_by_category.get("debug", [])
                    },
                    "repo": {
                        "name": "倉庫管理",
                        "actions": actions_by_category.get("repo", [])
                    },
                    "deploy": {
                        "name": "構建部署",
                        "actions": actions_by_category.get("deploy", []) + actions_by_category.get("optimization", [])
                    }
                },
                "search": {
                    "enabled": True,
                    "placeholder": "搜索操作..."
                },
                "favorites": self._get_favorite_actions()
            }
        }
    
    def _render_model_usage(self) -> Dict[str, Any]:
        """渲染模型使用統計"""
        # 更新模型統計數據
        self._update_model_stats()
        
        model_data = []
        for model_type, stats in self.model_stats.items():
            model_data.append({
                "model": model_type.value,
                "display_name": self._get_model_display_name(model_type),
                "icon": self._get_model_icon(model_type),
                "requests": stats.total_requests,
                "tokens_used": stats.total_tokens_used,
                "tokens_saved": stats.total_tokens_saved,
                "success_rate": stats.success_rate,
                "avg_response_time": stats.avg_response_time,
                "cost_estimate": stats.cost_estimate,
                "last_used": stats.last_used,
                "efficiency": self._calculate_model_efficiency(stats)
            })
        
        return {
            "section_id": "model_usage",
            "title": "🤖 模型使用統計",
            "collapsible": True,
            "collapsed": False,
            "content": {
                "current_model": {
                    "name": "Claude Sonnet 4",
                    "icon": "🧠",
                    "status": "active",
                    "quality": "premium"
                },
                "model_list": model_data,
                "summary": {
                    "total_models_used": len(self.model_stats),
                    "most_efficient": self._get_most_efficient_model(),
                    "recommendation": self._get_model_recommendation()
                },
                "controls": {
                    "switch_model": True,
                    "model_settings": True,
                    "usage_details": True
                }
            }
        }
    
    def _render_token_stats(self) -> Dict[str, Any]:
        """渲染Token使用統計"""
        # 更新Token統計
        self._update_token_stats()
        
        return {
            "section_id": "token_stats", 
            "title": "💰 Token統計",
            "collapsible": True,
            "collapsed": False,
            "content": {
                "current_session": {
                    "tokens_used": 1250,
                    "tokens_saved": 3800,
                    "efficiency": 75.2,
                    "cost_saved": 12.50
                },
                "time_periods": {
                    "today": {
                        "used": self.token_summary.today_used,
                        "saved": self.token_summary.today_saved,
                        "efficiency": self._calculate_efficiency(self.token_summary.today_used, self.token_summary.today_saved)
                    },
                    "week": {
                        "used": self.token_summary.this_week_used,
                        "saved": self.token_summary.this_week_saved,
                        "efficiency": self._calculate_efficiency(self.token_summary.this_week_used, self.token_summary.this_week_saved)
                    },
                    "month": {
                        "used": self.token_summary.this_month_used,
                        "saved": self.token_summary.this_month_saved,
                        "efficiency": self._calculate_efficiency(self.token_summary.this_month_used, self.token_summary.this_month_saved)
                    }
                },
                "savings_breakdown": {
                    "code_generation": {"saved": 1200, "percentage": 35},
                    "code_optimization": {"saved": 800, "percentage": 25},
                    "documentation": {"saved": 600, "percentage": 18},
                    "debugging": {"saved": 400, "percentage": 12},
                    "testing": {"saved": 350, "percentage": 10}
                },
                "cost_analysis": {
                    "total_saved_usd": self.token_summary.cost_saved_usd,
                    "monthly_budget": 100.0,
                    "budget_used_percentage": 35.2,
                    "projected_monthly_cost": 45.80
                },
                "visualization": {
                    "chart_type": "donut",
                    "show_trends": True,
                    "time_range_selector": True
                }
            }
        }
    
    def _render_repository_manager(self) -> Dict[str, Any]:
        """渲染倉庫管理區域"""
        return {
            "section_id": "repository_manager",
            "title": "📁 倉庫管理",
            "collapsible": True,
            "collapsed": False,
            "content": {
                "current_repo": self._get_current_repository(),
                "recent_repos": self._get_recent_repositories(),
                "quick_import": {
                    "providers": [
                        {
                            "id": "github",
                            "name": "GitHub",
                            "icon": "🐙",
                            "quick_connect": True,
                            "auth_status": "connected"
                        },
                        {
                            "id": "gitlab", 
                            "name": "GitLab",
                            "icon": "🦊",
                            "quick_connect": True,
                            "auth_status": "not_connected"
                        },
                        {
                            "id": "local",
                            "name": "本地文件",
                            "icon": "📂",
                            "quick_connect": True,
                            "auth_status": "ready"
                        },
                        {
                            "id": "zip",
                            "name": "ZIP上傳",
                            "icon": "📦",
                            "quick_connect": True,
                            "auth_status": "ready"
                        }
                    ],
                    "quick_actions": [
                        {
                            "id": "import_repo",
                            "label": "快速導入",
                            "icon": "📥",
                            "description": "輸入Git URL或選擇文件"
                        },
                        {
                            "id": "clone_template",
                            "label": "模板克隆", 
                            "icon": "📋",
                            "description": "從模板庫快速開始"
                        },
                        {
                            "id": "sync_all",
                            "label": "同步所有",
                            "icon": "🔄",
                            "description": "同步所有連接的倉庫"
                        }
                    ]
                },
                "import_dialog": {
                    "url_input": {
                        "placeholder": "輸入Git倉庫URL...",
                        "validation": True,
                        "auto_detect": True
                    },
                    "options": {
                        "branch_selection": True,
                        "selective_import": True,
                        "auto_analysis": True
                    }
                },
                "repo_templates": [
                    {
                        "name": "React + FastAPI",
                        "description": "全棧Web應用模板",
                        "icon": "⚛️",
                        "tags": ["frontend", "backend", "api"]
                    },
                    {
                        "name": "Python微服務",
                        "description": "微服務架構模板",
                        "icon": "🐍",
                        "tags": ["microservices", "docker", "api"]
                    },
                    {
                        "name": "Vue + Express",
                        "description": "Node.js全棧模板",
                        "icon": "💚",
                        "tags": ["vue", "nodejs", "express"]
                    }
                ]
            }
        }
    
    def _render_project_dashboard(self) -> Dict[str, Any]:
        """渲染項目儀表板"""
        return {
            "section_id": "project_dashboard",
            "title": "📊 項目儀表板",
            "collapsible": True,
            "collapsed": True,
            "content": {
                "project_health": {
                    "overall_score": 87,
                    "code_quality": 92,
                    "test_coverage": 78,
                    "documentation": 85,
                    "security": 90
                },
                "recent_activity": [
                    {
                        "time": "2分鐘前",
                        "action": "生成了API端點代碼",
                        "icon": "💻",
                        "status": "success"
                    },
                    {
                        "time": "5分鐘前", 
                        "action": "運行了測試套件",
                        "icon": "🧪",
                        "status": "success"
                    },
                    {
                        "time": "10分鐘前",
                        "action": "導入了GitHub倉庫",
                        "icon": "📥",
                        "status": "success"
                    }
                ],
                "quick_insights": {
                    "files_modified": 12,
                    "lines_of_code": 2847,
                    "tests_written": 45,
                    "bugs_fixed": 3,
                    "time_saved": "2.5小時"
                },
                "notifications": [
                    {
                        "type": "warning",
                        "message": "測試覆蓋率低於85%",
                        "action": "生成更多測試"
                    },
                    {
                        "type": "info",
                        "message": "發現3個性能優化建議",
                        "action": "查看建議"
                    }
                ]
            }
        }
    
    def _get_left_panel_styling(self) -> Dict[str, Any]:
        """獲取左側面板樣式"""
        return {
            "theme": "professional",
            "colors": {
                "background": "#F8F9FA",
                "surface": "#FFFFFF", 
                "border": "#E9ECEF",
                "text_primary": "#212529",
                "text_secondary": "#6C757D",
                "accent": "#007BFF",
                "success": "#28A745",
                "warning": "#FFC107",
                "danger": "#DC3545"
            },
            "typography": {
                "section_title": {
                    "font_size": "14px",
                    "font_weight": "600",
                    "color": "#495057"
                },
                "content_text": {
                    "font_size": "13px",
                    "font_weight": "400",
                    "color": "#6C757D"
                }
            },
            "spacing": {
                "section_gap": "16px",
                "content_padding": "12px",
                "item_spacing": "8px"
            },
            "animations": {
                "hover_transition": "0.2s ease",
                "collapse_animation": "0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                "loading_animation": True
            },
            "responsive": {
                "min_width": "280px",
                "max_width": "400px",
                "collapse_threshold": "768px"
            }
        }
    
    # 輔助方法
    def _update_model_stats(self):
        """更新模型統計數據"""
        # 模擬實際統計數據
        self.model_stats = {
            ModelType.CLAUDE_SONNET: ModelUsageStats(
                ModelType.CLAUDE_SONNET,
                total_requests=156,
                total_tokens_used=45200,
                total_tokens_saved=12800,
                avg_response_time=1.2,
                success_rate=98.7,
                cost_estimate=22.60,
                last_used=datetime.now().isoformat()
            ),
            ModelType.CLAUDE_HAIKU: ModelUsageStats(
                ModelType.CLAUDE_HAIKU,
                total_requests=89,
                total_tokens_used=28900,
                total_tokens_saved=8600,
                avg_response_time=0.8,
                success_rate=99.1,
                cost_estimate=8.90,
                last_used=(datetime.now() - timedelta(hours=2)).isoformat()
            )
        }
    
    def _update_token_stats(self):
        """更新Token統計數據"""
        self.token_summary = TokenUsageSummary(
            today_used=5200,
            today_saved=15600,
            this_week_used=28400,
            this_week_saved=85200,
            this_month_used=125000,
            this_month_saved=375000,
            efficiency_score=75.0,
            cost_saved_usd=187.50
        )
    
    def _get_current_repository(self) -> Dict[str, Any]:
        """獲取當前倉庫信息"""
        return {
            "name": "powerautomation-v4.6.1",
            "provider": "github",
            "url": "https://github.com/alexchuang650730/aicore0711",
            "branch": "main",
            "last_sync": "2分鐘前",
            "status": "up_to_date",
            "file_count": 147,
            "languages": ["Python", "JavaScript", "Markdown"],
            "size": "2.3 MB"
        }
    
    def _get_recent_repositories(self) -> List[Dict[str, Any]]:
        """獲取最近使用的倉庫"""
        return [
            {
                "name": "aicore0711",
                "provider": "github", 
                "icon": "🐙",
                "last_used": "當前",
                "status": "active"
            },
            {
                "name": "claude-code-assistant",
                "provider": "gitlab",
                "icon": "🦊", 
                "last_used": "昨天",
                "status": "synced"
            },
            {
                "name": "local-project",
                "provider": "local",
                "icon": "📂",
                "last_used": "3天前",
                "status": "local"
            }
        ]
    
    def _get_favorite_actions(self) -> List[str]:
        """獲取收藏的操作"""
        return ["generate_code", "run_tests", "import_repo", "debug_code"]
    
    def _calculate_efficiency(self, used: int, saved: int) -> float:
        """計算效率百分比"""
        total = used + saved
        return (saved / total * 100) if total > 0 else 0.0
    
    def _get_completed_stages(self) -> int:
        """獲取已完成階段數"""
        return 3
    
    def _get_total_stages(self) -> int:
        """獲取總階段數"""
        return 7
    
    def _calculate_progress_percentage(self) -> float:
        """計算進度百分比"""
        completed = self._get_completed_stages()
        total = self._get_total_stages()
        return (completed / total * 100) if total > 0 else 0.0
    
    def _get_stage_list_with_status(self) -> List[Dict[str, Any]]:
        """獲取帶狀態的階段列表"""
        return [
            {"id": "trigger", "name": "觸發器配置", "status": "completed", "icon": "✅"},
            {"id": "analysis", "name": "代碼分析", "status": "completed", "icon": "✅"},
            {"id": "testing", "name": "測試生成", "status": "current", "icon": "🔄"},
            {"id": "build", "name": "構建驗證", "status": "pending", "icon": "⏳"},
            {"id": "deploy", "name": "部署準備", "status": "locked", "icon": "🔒"},
            {"id": "monitor", "name": "監控配置", "status": "locked", "icon": "🔒"},
            {"id": "notify", "name": "通知設置", "status": "locked", "icon": "🔒"}
        ]
    
    def _calculate_model_efficiency(self, stats: ModelUsageStats) -> float:
        """計算模型效率"""
        total = stats.total_tokens_used + stats.total_tokens_saved
        return (stats.total_tokens_saved / total * 100) if total > 0 else 0.0
    
    def _get_most_efficient_model(self) -> str:
        """獲取最高效的模型"""
        return "Claude Haiku 3"
    
    def _get_model_recommendation(self) -> str:
        """獲取模型推薦"""
        return "建議使用Claude Sonnet用於複雜任務，Haiku用於快速響應"
    
    def _get_workflow_display_name(self, workflow: str) -> str:
        """獲取工作流顯示名稱"""
        names = {
            "code_generation": "代碼生成工作流",
            "ui_design": "UI設計工作流",
            "api_development": "API開發工作流"
        }
        return names.get(workflow, workflow)
    
    def _get_workflow_icon(self, workflow: str) -> str:
        """獲取工作流圖標"""
        icons = {
            "code_generation": "💻",
            "ui_design": "🎨", 
            "api_development": "🔌"
        }
        return icons.get(workflow, "⚙️")
    
    def _get_model_display_name(self, model_type: ModelType) -> str:
        """獲取模型顯示名稱"""
        names = {
            ModelType.CLAUDE_SONNET: "Claude Sonnet 4",
            ModelType.CLAUDE_HAIKU: "Claude Haiku 3",
            ModelType.CLAUDE_OPUS: "Claude Opus 3"
        }
        return names.get(model_type, model_type.value)
    
    def _get_model_icon(self, model_type: ModelType) -> str:
        """獲取模型圖標"""
        icons = {
            ModelType.CLAUDE_SONNET: "🧠",
            ModelType.CLAUDE_HAIKU: "⚡",
            ModelType.CLAUDE_OPUS: "🎯"
        }
        return icons.get(model_type, "🤖")

# 演示函數
async def demo_enhanced_left_panel():
    """演示增強的左側面板"""
    print("🎛️ ClaudEditor左側面板完整功能演示")
    print("=" * 60)
    
    left_panel = ClaudEditorLeftPanel()
    
    # 渲染完整左側面板
    panel_ui = left_panel.render_left_panel("code_generation", "code_analysis")
    
    print("📱 左側面板結構:")
    print(f"  寬度: {panel_ui['panel_config']['width']}")
    print(f"  可調整: {panel_ui['panel_config']['resizable']}")
    print(f"  可摺疊: {panel_ui['panel_config']['collapsible']}")
    
    print(f"\n🔧 包含的功能區域 ({len(panel_ui['panel_config']['sections'])}個):")
    for section in panel_ui['panel_config']['sections']:
        section_data = panel_ui['sections'][section]
        print(f"  📋 {section_data['title']}")
    
    # 展示快速操作
    quick_actions = panel_ui['sections']['quick_actions']
    print(f"\n⚡ 快速操作 ({len(quick_actions['content']['categories'])}個類別):")
    for category, data in quick_actions['content']['categories'].items():
        print(f"  🏷️ {data['name']}: {len(data['actions'])}個操作")
        for action in data['actions'][:2]:  # 顯示前2個
            print(f"    {action['icon']} {action['name']} ({action['shortcut']})")
    
    # 展示模型使用統計
    model_usage = panel_ui['sections']['model_usage']
    print(f"\n🤖 模型使用統計:")
    current_model = model_usage['content']['current_model']
    print(f"  當前模型: {current_model['icon']} {current_model['name']} ({current_model['status']})")
    
    model_list = model_usage['content']['model_list']
    print(f"  使用過的模型: {len(model_list)}個")
    for model in model_list:
        print(f"    {model['icon']} {model['display_name']}: {model['requests']}次請求")
    
    # 展示Token統計
    token_stats = panel_ui['sections']['token_stats']
    print(f"\n💰 Token使用統計:")
    current_session = token_stats['content']['current_session']
    print(f"  本次會話: 使用{current_session['tokens_used']}, 節省{current_session['tokens_saved']}")
    print(f"  效率: {current_session['efficiency']:.1f}%")
    print(f"  節省成本: ${current_session['cost_saved']:.2f}")
    
    # 展示倉庫管理
    repo_manager = panel_ui['sections']['repository_manager']
    print(f"\n📁 倉庫管理:")
    current_repo = repo_manager['content']['current_repo']
    print(f"  當前倉庫: {current_repo['name']} ({current_repo['provider']})")
    print(f"  文件數: {current_repo['file_count']}, 大小: {current_repo['size']}")
    
    providers = repo_manager['content']['quick_import']['providers']
    print(f"  支持的導入方式: {len(providers)}種")
    for provider in providers:
        status_icon = "✅" if provider['auth_status'] == "connected" else "⭕"
        print(f"    {status_icon} {provider['icon']} {provider['name']}")

if __name__ == "__main__":
    asyncio.run(demo_enhanced_left_panel())