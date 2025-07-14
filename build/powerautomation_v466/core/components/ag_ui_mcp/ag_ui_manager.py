"""
AG-UI MCP - 智能UI組件生成器
PowerAutomation v4.6.1 自動生成UI組件管理平台

基於aicore0707的AG-UI MCP實現，提供：
- 智能UI組件生成
- 測試界面自動創建
- 交互式儀表板
- 實時UI適配
"""

import asyncio
import logging
import time
import uuid
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class ComponentType(Enum):
    """組件類型枚舉"""
    DASHBOARD = "dashboard"
    PANEL = "panel"
    FORM = "form"
    TABLE = "table"
    CHART = "chart"
    BUTTON = "button"
    INPUT = "input"
    MODAL = "modal"
    MENU = "menu"
    NOTIFICATION = "notification"


class ThemeType(Enum):
    """主題類型枚舉"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"
    CLAUDEDITOR_DARK = "claudeditor_dark"
    CLAUDEDITOR_LIGHT = "claudeditor_light"
    TESTING_FOCUSED = "testing_focused"


class LayoutType(Enum):
    """布局類型枚舉"""
    GRID = "grid"
    FLEX = "flex"
    ABSOLUTE = "absolute"
    TABBED = "tabbed"
    THREE_COLUMN = "three_column"


@dataclass
class ComponentSpec:
    """組件規格"""
    type: ComponentType
    id: str
    title: str
    description: str
    properties: Dict[str, Any]
    styles: Dict[str, Any]
    events: List[str]
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class UIInterface:
    """UI界面"""
    id: str
    name: str
    description: str
    components: List[ComponentSpec]
    layout: LayoutType
    theme: ThemeType
    global_styles: Dict[str, Any]
    scripts: List[str]
    created_at: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ComponentGenerator:
    """組件生成器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.component_templates = self._load_component_templates()
    
    def _load_component_templates(self) -> Dict[str, Dict[str, Any]]:
        """載入組件模板"""
        return {
            "test_dashboard": {
                "html": """
                <div class="test-dashboard" id="{id}">
                    <header class="dashboard-header">
                        <h1>{title}</h1>
                        <div class="dashboard-controls">
                            <button class="btn-primary" onclick="startTest()">開始測試</button>
                            <button class="btn-secondary" onclick="stopTest()">停止測試</button>
                        </div>
                    </header>
                    <main class="dashboard-content">
                        <div class="stats-panel">
                            <div class="stat-card">
                                <span class="stat-value" id="total-tests">0</span>
                                <span class="stat-label">總測試數</span>
                            </div>
                            <div class="stat-card">
                                <span class="stat-value" id="passed-tests">0</span>
                                <span class="stat-label">通過</span>
                            </div>
                            <div class="stat-card">
                                <span class="stat-value" id="failed-tests">0</span>
                                <span class="stat-label">失敗</span>
                            </div>
                        </div>
                        <div class="test-results-area">
                            <div id="test-progress-bar" class="progress-bar">
                                <div class="progress-fill" style="width: 0%"></div>
                            </div>
                            <div id="test-logs" class="test-logs"></div>
                        </div>
                    </main>
                </div>
                """,
                "css": """
                .test-dashboard {
                    width: 100%;
                    height: 100vh;
                    background: {background_color};
                    color: {text_color};
                    font-family: 'Segoe UI', sans-serif;
                }
                .dashboard-header {
                    padding: 20px;
                    border-bottom: 1px solid {border_color};
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .dashboard-controls button {
                    margin-left: 10px;
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
                .btn-primary {
                    background: #007bff;
                    color: white;
                }
                .btn-secondary {
                    background: #6c757d;
                    color: white;
                }
                .stats-panel {
                    display: flex;
                    gap: 20px;
                    padding: 20px;
                }
                .stat-card {
                    flex: 1;
                    padding: 20px;
                    background: {card_background};
                    border-radius: 8px;
                    text-align: center;
                }
                .stat-value {
                    display: block;
                    font-size: 2em;
                    font-weight: bold;
                    color: {primary_color};
                }
                .stat-label {
                    color: {secondary_color};
                }
                .progress-bar {
                    height: 8px;
                    background: {progress_background};
                    border-radius: 4px;
                    overflow: hidden;
                    margin: 20px;
                }
                .progress-fill {
                    height: 100%;
                    background: {progress_color};
                    transition: width 0.3s ease;
                }
                .test-logs {
                    height: 300px;
                    overflow-y: auto;
                    padding: 20px;
                    background: {logs_background};
                    border-radius: 4px;
                    margin: 20px;
                    font-family: monospace;
                }
                """,
                "js": """
                function startTest() {
                    console.log('Starting test...');
                    document.getElementById('test-progress-bar').querySelector('.progress-fill').style.width = '0%';
                    // 與PowerAutomation API通信
                    fetch('/test/start', {method: 'POST'})
                        .then(response => response.json())
                        .then(data => console.log('Test started:', data));
                }
                
                function stopTest() {
                    console.log('Stopping test...');
                    fetch('/test/stop', {method: 'POST'})
                        .then(response => response.json())
                        .then(data => console.log('Test stopped:', data));
                }
                
                function updateTestStats(stats) {
                    document.getElementById('total-tests').textContent = stats.total;
                    document.getElementById('passed-tests').textContent = stats.passed;
                    document.getElementById('failed-tests').textContent = stats.failed;
                    
                    const progress = stats.total > 0 ? (stats.passed + stats.failed) / stats.total * 100 : 0;
                    document.getElementById('test-progress-bar').querySelector('.progress-fill').style.width = progress + '%';
                }
                
                function addTestLog(message) {
                    const logs = document.getElementById('test-logs');
                    const timestamp = new Date().toLocaleTimeString();
                    logs.innerHTML += `<div>[${timestamp}] ${message}</div>`;
                    logs.scrollTop = logs.scrollHeight;
                }
                """
            },
            "panel": {
                "html": """
                <div class="panel" id="{id}">
                    <div class="panel-header">
                        <h3>{title}</h3>
                    </div>
                    <div class="panel-content">
                        <p>Panel content area</p>
                    </div>
                </div>
                """,
                "css": """
                .panel {{
                    background: {background_color};
                    border: 1px solid {border_color};
                    border-radius: 8px;
                    padding: 16px;
                    margin: 8px;
                }}
                .panel-header h3 {{
                    margin: 0;
                    color: {primary_color};
                }}
                .panel-content {{
                    margin-top: 12px;
                    color: {text_color};
                }}
                """
            },
            "test_execution_panel": {
                "html": """
                <div class="test-execution-panel" id="{id}">
                    <div class="panel-header">
                        <h3>{title}</h3>
                    </div>
                    <div class="panel-content">
                        <div class="test-suite-selector">
                            <label>選擇測試套件:</label>
                            <select id="test-suite-select">
                                <option value="">請選擇...</option>
                            </select>
                        </div>
                        <div class="test-options">
                            <label>
                                <input type="checkbox" id="parallel-execution"> 並行執行
                            </label>
                            <label>
                                <input type="checkbox" id="headless-mode"> 無頭模式
                            </label>
                        </div>
                        <div class="execution-controls">
                            <button id="start-test-btn" class="btn btn-primary">開始測試</button>
                            <button id="pause-test-btn" class="btn btn-secondary" disabled>暫停</button>
                            <button id="stop-test-btn" class="btn btn-danger" disabled>停止</button>
                        </div>
                        <div class="current-test-info">
                            <div class="info-item">
                                <span class="label">當前測試:</span>
                                <span id="current-test-name">-</span>
                            </div>
                            <div class="info-item">
                                <span class="label">執行時間:</span>
                                <span id="execution-time">00:00</span>
                            </div>
                        </div>
                    </div>
                </div>
                """
            },
            "test_results_viewer": {
                "html": """
                <div class="test-results-viewer" id="{id}">
                    <div class="viewer-header">
                        <h3>{title}</h3>
                        <div class="viewer-controls">
                            <button class="btn-icon" onclick="refreshResults()">🔄</button>
                            <button class="btn-icon" onclick="exportResults()">📥</button>
                            <button class="btn-icon" onclick="clearResults()">🗑️</button>
                        </div>
                    </div>
                    <div class="viewer-content">
                        <div class="results-summary">
                            <div class="summary-stats">
                                <span class="stat passed">通過: <strong id="summary-passed">0</strong></span>
                                <span class="stat failed">失敗: <strong id="summary-failed">0</strong></span>
                                <span class="stat skipped">跳過: <strong id="summary-skipped">0</strong></span>
                            </div>
                        </div>
                        <div class="results-table-container">
                            <table class="results-table">
                                <thead>
                                    <tr>
                                        <th>狀態</th>
                                        <th>測試名稱</th>
                                        <th>執行時間</th>
                                        <th>錯誤信息</th>
                                        <th>操作</th>
                                    </tr>
                                </thead>
                                <tbody id="results-table-body">
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                """
            }
        }
    
    async def generate_component(self, spec: ComponentSpec, theme: ThemeType) -> Dict[str, str]:
        """生成組件代碼"""
        component_type = spec.type.value
        
        if component_type not in self.component_templates:
            raise ValueError(f"不支持的組件類型: {component_type}")
        
        template = self.component_templates[component_type]
        theme_colors = self._get_theme_colors(theme)
        
        # 格式化HTML
        html = template["html"].format(
            id=spec.id,
            title=spec.title,
            **spec.properties
        )
        
        # 格式化CSS
        css = ""
        if "css" in template:
            css = template["css"].format(**theme_colors)
        
        # 添加自定義樣式
        if spec.styles:
            css += "\n" + self._generate_custom_css(spec.id, spec.styles)
        
        # JavaScript
        js = template.get("js", "")
        
        return {
            "html": html,
            "css": css,
            "js": js
        }
    
    def _get_theme_colors(self, theme: ThemeType) -> Dict[str, str]:
        """獲取主題顏色"""
        themes = {
            ThemeType.LIGHT: {
                "background_color": "#ffffff",
                "text_color": "#333333",
                "border_color": "#e1e1e1",
                "card_background": "#f8f9fa",
                "primary_color": "#007bff",
                "secondary_color": "#6c757d",
                "progress_background": "#e9ecef",
                "progress_color": "#28a745",
                "logs_background": "#f8f9fa"
            },
            ThemeType.DARK: {
                "background_color": "#1a1a1a",
                "text_color": "#ffffff",
                "border_color": "#333333",
                "card_background": "#2d2d2d",
                "primary_color": "#0d6efd",
                "secondary_color": "#6c757d",
                "progress_background": "#343a40",
                "progress_color": "#28a745",
                "logs_background": "#212529"
            },
            ThemeType.CLAUDEDITOR_DARK: {
                "background_color": "#0d1117",
                "text_color": "#f0f6fc",
                "border_color": "#21262d",
                "card_background": "#161b22",
                "primary_color": "#58a6ff",
                "secondary_color": "#8b949e",
                "progress_background": "#21262d",
                "progress_color": "#2ea043",
                "logs_background": "#0d1117"
            },
            ThemeType.TESTING_FOCUSED: {
                "background_color": "#fafafa",
                "text_color": "#2d3748",
                "border_color": "#e2e8f0",
                "card_background": "#ffffff",
                "primary_color": "#3182ce",
                "secondary_color": "#718096",
                "progress_background": "#edf2f7",
                "progress_color": "#38a169",
                "logs_background": "#f7fafc"
            }
        }
        
        return themes.get(theme, themes[ThemeType.LIGHT])
    
    def _generate_custom_css(self, component_id: str, styles: Dict[str, Any]) -> str:
        """生成自定義CSS"""
        css_lines = [f"#{component_id} {{"]
        
        for property_name, value in styles.items():
            css_property = property_name.replace("_", "-")
            css_lines.append(f"    {css_property}: {value};")
        
        css_lines.append("}")
        
        return "\n".join(css_lines)


class UIInterfaceBuilder:
    """UI界面構建器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.component_generator = ComponentGenerator()
    
    async def build_interface(self, interface: UIInterface) -> Dict[str, str]:
        """構建界面"""
        self.logger.info(f"構建界面: {interface.name}")
        
        # 生成各組件
        all_html = []
        all_css = []
        all_js = []
        
        for component_spec in interface.components:
            component_code = await self.component_generator.generate_component(
                component_spec, interface.theme
            )
            
            all_html.append(component_code["html"])
            all_css.append(component_code["css"])
            all_js.append(component_code["js"])
        
        # 組合完整的HTML文檔
        full_html = self._create_full_html_document(
            interface, all_html, all_css, all_js
        )
        
        return {
            "html": full_html,
            "css": "\n".join(all_css),
            "js": "\n".join(all_js)
        }
    
    def _create_full_html_document(self, interface: UIInterface, html_parts: List[str], 
                                   css_parts: List[str], js_parts: List[str]) -> str:
        """創建完整的HTML文檔"""
        layout_class = self._get_layout_class(interface.layout)
        
        return f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{interface.name}</title>
    <style>
        {chr(10).join(css_parts)}
        
        /* 全局樣式 */
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
        }}
        
        .{layout_class} {{
            {self._get_layout_css(interface.layout)}
        }}
        
        /* 自定義全局樣式 */
        {self._generate_global_styles(interface.global_styles)}
    </style>
</head>
<body>
    <div class="{layout_class}" id="main-container">
        {chr(10).join(html_parts)}
    </div>
    
    <script>
        {chr(10).join(js_parts)}
        
        // 界面初始化
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('AG-UI界面已載入: {interface.name}');
            initializeInterface();
        }});
        
        function initializeInterface() {{
            // 界面初始化邏輯
            setupEventListeners();
            loadInitialData();
        }}
        
        function setupEventListeners() {{
            // 設置事件監聽器
        }}
        
        function loadInitialData() {{
            // 載入初始數據
        }}
    </script>
</body>
</html>
        """
    
    def _get_layout_class(self, layout: LayoutType) -> str:
        """獲取布局類名"""
        return f"layout-{layout.value.replace('_', '-')}"
    
    def _get_layout_css(self, layout: LayoutType) -> str:
        """獲取布局CSS"""
        layouts = {
            LayoutType.GRID: """
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                padding: 20px;
            """,
            LayoutType.FLEX: """
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                padding: 20px;
            """,
            LayoutType.THREE_COLUMN: """
                display: grid;
                grid-template-columns: 250px 1fr 300px;
                gap: 20px;
                height: 100vh;
            """,
            LayoutType.TABBED: """
                display: flex;
                flex-direction: column;
                height: 100vh;
            """
        }
        
        return layouts.get(layout, layouts[LayoutType.GRID])
    
    def _generate_global_styles(self, global_styles: Dict[str, Any]) -> str:
        """生成全局樣式"""
        if not global_styles:
            return ""
        
        css_lines = []
        for selector, styles in global_styles.items():
            css_lines.append(f"{selector} {{")
            for prop, value in styles.items():
                css_lines.append(f"    {prop.replace('_', '-')}: {value};")
            css_lines.append("}")
        
        return "\n".join(css_lines)


class AGUIMCPManager:
    """AG-UI MCP管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.component_generator = ComponentGenerator()
        self.interface_builder = UIInterfaceBuilder()
        self.generated_interfaces = {}
        self.component_registry = {}
    
    async def initialize(self):
        """初始化AG-UI MCP"""
        self.logger.info("🎨 初始化AG-UI MCP - 智能UI組件生成器")
        
        # 註冊默認組件類型
        await self._register_default_components()
        
        self.logger.info("✅ AG-UI MCP初始化完成")
    
    async def _register_default_components(self):
        """註冊默認組件類型"""
        default_components = [
            ComponentType.DASHBOARD,
            ComponentType.PANEL,
            ComponentType.TABLE,
            ComponentType.CHART,
            ComponentType.FORM
        ]
        
        for component_type in default_components:
            self.component_registry[component_type.value] = {
                "type": component_type,
                "description": f"{component_type.value} component",
                "properties": ["title", "id", "theme"],
                "events": ["click", "change", "submit"]
            }
    
    async def generate_testing_interface(self, interface_spec: Dict[str, Any]) -> Dict[str, Any]:
        """生成測試界面"""
        interface_id = str(uuid.uuid4())
        
        # 解析界面規格
        dashboard_spec = interface_spec.get("dashboard", {})
        monitor_spec = interface_spec.get("monitor", {})
        viewer_spec = interface_spec.get("viewer", {})
        
        # 創建組件規格
        components = []
        
        # 測試儀表板組件
        if dashboard_spec:
            dashboard_component = ComponentSpec(
                type=ComponentType.DASHBOARD,
                id="test-dashboard",
                title="測試執行儀表板",
                description="主要的測試控制和監控界面",
                properties={
                    "features": dashboard_spec.get("features", []),
                    "theme": dashboard_spec.get("theme", "dark")
                },
                styles={},
                events=["start_test", "stop_test", "pause_test"]
            )
            components.append(dashboard_component)
        
        # 測試監控組件
        if monitor_spec:
            monitor_component = ComponentSpec(
                type=ComponentType.PANEL,
                id="test-monitor",
                title="實時監控面板",
                description="實時顯示測試執行狀態",
                properties={
                    "real_time": monitor_spec.get("real_time", True),
                    "features": monitor_spec.get("features", [])
                },
                styles={},
                events=["update_status", "alert"]
            )
            components.append(monitor_component)
        
        # 結果查看器組件
        if viewer_spec:
            viewer_component = ComponentSpec(
                type=ComponentType.TABLE,
                id="results-viewer",
                title="測試結果查看器",
                description="顯示詳細的測試結果",
                properties={
                    "view_modes": viewer_spec.get("view_modes", ["summary"]),
                    "features": viewer_spec.get("features", [])
                },
                styles={},
                events=["view_details", "export", "filter"]
            )
            components.append(viewer_component)
        
        # 創建界面
        theme = ThemeType(interface_spec.get("theme", "dark"))
        layout = LayoutType(interface_spec.get("layout_type", "grid"))
        
        interface = UIInterface(
            id=interface_id,
            name="PowerAutomation測試界面",
            description="AI生成的測試執行和監控界面",
            components=components,
            layout=layout,
            theme=theme,
            global_styles={
                ".test-interface": {
                    "font-family": "'Segoe UI', sans-serif",
                    "background": "var(--bg-color)",
                    "color": "var(--text-color)"
                }
            },
            scripts=[],
            created_at=datetime.now().isoformat()
        )
        
        # 構建界面
        interface_code = await self.interface_builder.build_interface(interface)
        
        # 保存生成的界面
        self.generated_interfaces[interface_id] = {
            "interface": interface,
            "code": interface_code,
            "created_at": datetime.now().isoformat()
        }
        
        self.logger.info(f"生成測試界面: {interface_id}")
        
        return {
            "success": True,
            "interface_id": interface_id,
            "interface_name": interface.name,
            "components_count": len(components),
            "code": interface_code
        }
    
    async def generate_complete_testing_interface(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """生成完整的測試界面"""
        try:
            # 更詳細的界面生成邏輯
            interface_result = await self.generate_testing_interface(spec)
            
            if interface_result["success"]:
                # 添加額外的測試功能組件
                interface_id = interface_result["interface_id"]
                
                # 保存界面文件
                await self._save_interface_files(interface_id, interface_result["code"])
                
                return {
                    "success": True,
                    "interface_id": interface_id,
                    "url": f"/interface/{interface_id}",
                    "features": [
                        "real_time_monitoring",
                        "test_execution_control",
                        "results_visualization",
                        "export_capabilities"
                    ]
                }
            else:
                return {"success": False, "error": "界面生成失敗"}
                
        except Exception as e:
            self.logger.error(f"生成完整測試界面失敗: {e}")
            return {"success": False, "error": str(e)}
    
    async def _save_interface_files(self, interface_id: str, code: Dict[str, str]):
        """保存界面文件"""
        interface_dir = Path(f"generated_interfaces/{interface_id}")
        interface_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存HTML文件
        with open(interface_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(code["html"])
        
        # 保存CSS文件
        with open(interface_dir / "styles.css", "w", encoding="utf-8") as f:
            f.write(code["css"])
        
        # 保存JS文件
        with open(interface_dir / "scripts.js", "w", encoding="utf-8") as f:
            f.write(code["js"])
    
    async def generate_custom_component(self, component_spec: Dict[str, Any]) -> Dict[str, Any]:
        """生成自定義組件"""
        component_id = str(uuid.uuid4())
        
        # 創建組件規格
        spec = ComponentSpec(
            type=ComponentType(component_spec["type"]),
            id=component_id,
            title=component_spec.get("title", "自定義組件"),
            description=component_spec.get("description", ""),
            properties=component_spec.get("properties", {}),
            styles=component_spec.get("styles", {}),
            events=component_spec.get("events", [])
        )
        
        # 生成組件代碼
        theme = ThemeType(component_spec.get("theme", "light"))
        component_code = await self.component_generator.generate_component(spec, theme)
        
        return {
            "component_id": component_id,
            "component_type": spec.type.value,
            "code": component_code
        }
    
    async def list_available_components(self) -> List[Dict[str, Any]]:
        """列出可用的組件類型"""
        return [
            {
                "type": comp_type,
                "info": comp_info
            }
            for comp_type, comp_info in self.component_registry.items()
        ]
    
    async def get_interface_preview(self, interface_id: str) -> Optional[Dict[str, Any]]:
        """獲取界面預覽"""
        if interface_id not in self.generated_interfaces:
            return None
        
        interface_data = self.generated_interfaces[interface_id]
        interface = interface_data["interface"]
        
        return {
            "id": interface.id,
            "name": interface.name,
            "description": interface.description,
            "components_count": len(interface.components),
            "theme": interface.theme.value,
            "layout": interface.layout.value,
            "created_at": interface.created_at,
            "preview_url": f"/interface/{interface_id}/preview"
        }
    
    def get_status(self) -> Dict[str, Any]:
        """獲取AG-UI MCP狀態"""
        return {
            "component": "AG-UI MCP",
            "version": "4.6.1",
            "status": "running",
            "generated_interfaces": len(self.generated_interfaces),
            "registered_components": len(self.component_registry),
            "supported_themes": [theme.value for theme in ThemeType],
            "supported_layouts": [layout.value for layout in LayoutType],
            "capabilities": [
                "component_generation",
                "interface_building",
                "theme_adaptation",
                "real_time_updates",
                "export_functionality"
            ]
        }


# 單例實例
ag_ui_mcp = AGUIMCPManager()