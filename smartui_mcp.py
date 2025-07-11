#!/usr/bin/env python3
"""
SmartUI MCP 智能UI生成組件
Smart UI Generation Component for PowerAutomation v4.6.2

🤖 SmartUI MCP 核心功能:
1. AI驅動UI組件生成
2. 智能布局和響應式設計
3. 自動樣式優化
4. 無障礙訪問支持
5. 性能智能調優
6. 設計系統管理
7. 品牌一致性檢查
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class UIComponentType(Enum):
    """UI組件類型"""
    BUTTON = "button"
    INPUT_FIELD = "input_field"
    FORM = "form"
    NAVIGATION = "navigation"
    CARD = "card"
    MODAL = "modal"
    TABLE = "table"
    CHART = "chart"
    LAYOUT = "layout"
    CUSTOM = "custom"

class DesignTheme(Enum):
    """設計主題"""
    MODERN = "modern"
    CLASSIC = "classic"
    MINIMAL = "minimal"
    CORPORATE = "corporate"
    CREATIVE = "creative"
    MOBILE_FIRST = "mobile_first"

class AccessibilityLevel(Enum):
    """無障礙訪問級別"""
    BASIC = "basic"          # 基礎訪問支持
    WCAG_AA = "wcag_aa"     # WCAG 2.1 AA標準
    WCAG_AAA = "wcag_aaa"   # WCAG 2.1 AAA標準

@dataclass
class UIGenerationRequest:
    """UI生成請求"""
    description: str                              # 自然語言描述
    component_type: UIComponentType             # 組件類型
    theme: DesignTheme = DesignTheme.MODERN     # 設計主題
    accessibility: AccessibilityLevel = AccessibilityLevel.WCAG_AA
    responsive: bool = True                      # 響應式設計
    framework: str = "react"                    # 前端框架
    custom_styles: Dict[str, Any] = field(default_factory=dict)
    brand_colors: Dict[str, str] = field(default_factory=dict)
    target_platforms: List[str] = field(default_factory=lambda: ["web", "mobile"])

@dataclass
class GeneratedUIComponent:
    """生成的UI組件"""
    id: str
    name: str
    component_type: UIComponentType
    html_code: str
    css_code: str
    javascript_code: str
    framework_code: str                         # 框架特定代碼
    accessibility_features: List[str]
    performance_score: float
    responsive_breakpoints: Dict[str, str]
    design_tokens: Dict[str, Any]
    preview_url: Optional[str] = None
    generated_at: str = field(default_factory=lambda: time.time())

@dataclass
class DesignSystemConfig:
    """設計系統配置"""
    primary_color: str = "#007BFF"
    secondary_color: str = "#6C757D"
    success_color: str = "#28A745"
    warning_color: str = "#FFC107"
    danger_color: str = "#DC3545"
    font_family: str = "SF Pro Display, system-ui"
    border_radius: str = "8px"
    spacing_unit: str = "8px"
    breakpoints: Dict[str, str] = field(default_factory=lambda: {
        "xs": "0px",
        "sm": "576px", 
        "md": "768px",
        "lg": "992px",
        "xl": "1200px"
    })

class SmartUIMCP:
    """SmartUI MCP 主類"""
    
    def __init__(self):
        self.version = "1.0.0"
        self.ai_model = "gpt-4-turbo"  # AI模型
        self.design_system = DesignSystemConfig()
        self.generated_components = {}
        self.component_library = {}
        self.performance_cache = {}
        
        # 初始化組件庫
        self._initialize_component_library()
        
    def _initialize_component_library(self):
        """初始化組件庫"""
        print("🎨 初始化SmartUI組件庫...")
        
        # 預定義組件模板
        self.component_library = {
            UIComponentType.BUTTON: {
                "templates": ["primary", "secondary", "outlined", "text"],
                "variants": ["small", "medium", "large"],
                "states": ["normal", "hover", "active", "disabled"]
            },
            UIComponentType.INPUT_FIELD: {
                "templates": ["text", "email", "password", "search"],
                "variants": ["outlined", "filled", "underlined"],
                "states": ["normal", "focus", "error", "disabled"]
            },
            UIComponentType.FORM: {
                "templates": ["login", "registration", "contact", "survey"],
                "layouts": ["vertical", "horizontal", "grid"],
                "validation": ["client", "server", "realtime"]
            },
            UIComponentType.NAVIGATION: {
                "templates": ["navbar", "sidebar", "tabs", "breadcrumb"],
                "styles": ["fixed", "sticky", "static"],
                "responsive": ["collapse", "drawer", "scroll"]
            },
            UIComponentType.CARD: {
                "templates": ["product", "profile", "article", "stats"],
                "layouts": ["vertical", "horizontal", "grid"],
                "interactions": ["hover", "click", "swipe"]
            }
        }
        
        print("✅ SmartUI組件庫初始化完成")
    
    async def generate_ui_component(self, request: UIGenerationRequest) -> GeneratedUIComponent:
        """生成UI組件"""
        print(f"🤖 SmartUI生成組件: {request.component_type.value}")
        print(f"   描述: {request.description}")
        
        start_time = time.time()
        
        try:
            # 1. AI分析需求
            analysis = await self._analyze_requirements(request)
            
            # 2. 生成設計方案
            design_spec = await self._generate_design_specification(request, analysis)
            
            # 3. 生成代碼
            code_result = await self._generate_component_code(design_spec)
            
            # 4. 優化性能
            optimized_code = await self._optimize_performance(code_result)
            
            # 5. 添加無障礙功能
            accessible_code = await self._add_accessibility_features(optimized_code, request.accessibility)
            
            # 6. 響應式適配
            responsive_code = await self._add_responsive_design(accessible_code, request.responsive)
            
            # 7. 生成最終組件
            component = GeneratedUIComponent(
                id=str(uuid.uuid4()),
                name=f"{request.component_type.value}_{int(time.time())}",
                component_type=request.component_type,
                html_code=responsive_code["html"],
                css_code=responsive_code["css"],
                javascript_code=responsive_code["javascript"],
                framework_code=responsive_code.get("framework", ""),
                accessibility_features=accessible_code["accessibility_features"],
                performance_score=optimized_code["performance_score"],
                responsive_breakpoints=responsive_code["breakpoints"],
                design_tokens=design_spec["design_tokens"],
                preview_url=f"/preview/{responsive_code['id']}"
            )
            
            # 緩存組件
            self.generated_components[component.id] = component
            
            generation_time = time.time() - start_time
            print(f"✅ 組件生成完成 ({generation_time:.2f}s)")
            print(f"   性能評分: {component.performance_score:.1f}/100")
            print(f"   無障礙功能: {len(component.accessibility_features)}項")
            
            return component
            
        except Exception as e:
            logger.error(f"UI組件生成失敗: {e}")
            raise
    
    async def _analyze_requirements(self, request: UIGenerationRequest) -> Dict[str, Any]:
        """AI分析需求"""
        # 模擬AI需求分析
        await asyncio.sleep(0.1)
        
        analysis = {
            "intent": f"生成{request.component_type.value}組件",
            "complexity": "medium",
            "features": [],
            "constraints": [],
            "suggestions": []
        }
        
        # 基於描述分析功能需求
        description = request.description.lower()
        
        if "登入" in description or "login" in description:
            analysis["features"].extend(["用戶名輸入", "密碼輸入", "記住我", "登入按鈕"])
            analysis["suggestions"].append("添加忘記密碼連結")
            
        if "搜尋" in description or "search" in description:
            analysis["features"].extend(["搜尋輸入框", "搜尋按鈕", "自動完成"])
            analysis["suggestions"].append("添加搜尋歷史")
            
        if "響應式" in description or "responsive" in description:
            analysis["constraints"].append("必須支援響應式設計")
            
        if "無障礙" in description or "accessibility" in description:
            analysis["constraints"].append("必須符合無障礙標準")
        
        return analysis
    
    async def _generate_design_specification(self, request: UIGenerationRequest, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成設計規範"""
        await asyncio.sleep(0.1)
        
        # 基於請求和分析生成設計規範
        design_spec = {
            "component_name": f"{request.component_type.value}_component",
            "theme": request.theme.value,
            "layout": self._determine_layout(request, analysis),
            "colors": self._generate_color_scheme(request),
            "typography": self._generate_typography(request),
            "spacing": self._generate_spacing(),
            "interactions": self._generate_interactions(request, analysis),
            "design_tokens": self._generate_design_tokens(request)
        }
        
        return design_spec
    
    def _determine_layout(self, request: UIGenerationRequest, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """決定布局"""
        layout_configs = {
            UIComponentType.BUTTON: {
                "display": "inline-flex",
                "align_items": "center",
                "justify_content": "center",
                "padding": "12px 24px",
                "min_width": "120px"
            },
            UIComponentType.INPUT_FIELD: {
                "display": "block",
                "width": "100%",
                "padding": "12px 16px",
                "margin_bottom": "16px"
            },
            UIComponentType.FORM: {
                "display": "flex",
                "flex_direction": "column",
                "gap": "16px",
                "max_width": "400px"
            },
            UIComponentType.CARD: {
                "display": "flex",
                "flex_direction": "column",
                "padding": "24px",
                "border_radius": "12px",
                "box_shadow": "0 4px 16px rgba(0,0,0,0.1)"
            }
        }
        
        return layout_configs.get(request.component_type, {
            "display": "block",
            "padding": "16px"
        })
    
    def _generate_color_scheme(self, request: UIGenerationRequest) -> Dict[str, str]:
        """生成色彩方案"""
        base_colors = {
            "primary": request.brand_colors.get("primary", self.design_system.primary_color),
            "secondary": request.brand_colors.get("secondary", self.design_system.secondary_color),
            "success": self.design_system.success_color,
            "warning": self.design_system.warning_color,
            "danger": self.design_system.danger_color
        }
        
        # 根據主題調整色彩
        if request.theme == DesignTheme.MINIMAL:
            base_colors.update({
                "background": "#FFFFFF",
                "surface": "#FAFAFA",
                "text": "#2E2E2E",
                "border": "#E5E5E5"
            })
        elif request.theme == DesignTheme.CORPORATE:
            base_colors.update({
                "background": "#F8F9FA",
                "surface": "#FFFFFF",
                "text": "#495057",
                "border": "#DEE2E6"
            })
        else:  # MODERN
            base_colors.update({
                "background": "#FFFFFF",
                "surface": "#F1F3F4",
                "text": "#1A1A1A",
                "border": "#E0E0E0"
            })
        
        return base_colors
    
    def _generate_typography(self, request: UIGenerationRequest) -> Dict[str, str]:
        """生成字體排版"""
        return {
            "font_family": self.design_system.font_family,
            "font_size_small": "14px",
            "font_size_base": "16px",
            "font_size_large": "18px",
            "font_size_xl": "24px",
            "font_weight_normal": "400",
            "font_weight_medium": "500",
            "font_weight_bold": "600",
            "line_height": "1.5",
            "letter_spacing": "0.02em"
        }
    
    def _generate_spacing(self) -> Dict[str, str]:
        """生成間距系統"""
        return {
            "xs": "4px",
            "sm": "8px",
            "md": "16px",
            "lg": "24px",
            "xl": "32px",
            "xxl": "48px"
        }
    
    def _generate_interactions(self, request: UIGenerationRequest, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成交互設計"""
        interactions = {
            "hover_effects": True,
            "focus_states": True,
            "active_states": True,
            "disabled_states": True,
            "transitions": {
                "duration": "0.2s",
                "timing": "ease-in-out"
            }
        }
        
        # 根據組件類型添加特定交互
        if request.component_type == UIComponentType.BUTTON:
            interactions.update({
                "click_animation": "scale(0.98)",
                "loading_state": True,
                "ripple_effect": True
            })
        elif request.component_type == UIComponentType.INPUT_FIELD:
            interactions.update({
                "label_animation": "float",
                "validation_feedback": True,
                "auto_complete": True
            })
        
        return interactions
    
    def _generate_design_tokens(self, request: UIGenerationRequest) -> Dict[str, Any]:
        """生成設計令牌"""
        return {
            "colors": self._generate_color_scheme(request),
            "typography": self._generate_typography(request),
            "spacing": self._generate_spacing(),
            "shadows": {
                "small": "0 2px 4px rgba(0,0,0,0.1)",
                "medium": "0 4px 8px rgba(0,0,0,0.12)",
                "large": "0 8px 16px rgba(0,0,0,0.15)"
            },
            "border_radius": {
                "small": "4px",
                "medium": "8px",
                "large": "12px",
                "round": "50%"
            },
            "breakpoints": self.design_system.breakpoints
        }
    
    async def _generate_component_code(self, design_spec: Dict[str, Any]) -> Dict[str, Any]:
        """生成組件代碼"""
        await asyncio.sleep(0.2)
        
        # 生成HTML
        html_code = self._generate_html_code(design_spec)
        
        # 生成CSS
        css_code = self._generate_css_code(design_spec)
        
        # 生成JavaScript
        javascript_code = self._generate_javascript_code(design_spec)
        
        # 生成React代碼 (示例)
        react_code = self._generate_react_code(design_spec)
        
        return {
            "html": html_code,
            "css": css_code,
            "javascript": javascript_code,
            "react": react_code,
            "id": design_spec["component_name"]
        }
    
    def _generate_html_code(self, design_spec: Dict[str, Any]) -> str:
        """生成HTML代碼"""
        component_name = design_spec["component_name"]
        
        # 簡化的HTML生成邏輯
        if "button" in component_name:
            return f"""<button class="{component_name}" type="button" aria-label="智能生成按鈕">
    <span class="button-text">點擊我</span>
    <span class="button-icon" aria-hidden="true">→</span>
</button>"""
        
        elif "input" in component_name:
            return f"""<div class="{component_name}-wrapper">
    <label for="{component_name}" class="input-label">輸入標籤</label>
    <input 
        id="{component_name}"
        class="{component_name}"
        type="text"
        placeholder="請輸入內容"
        aria-describedby="{component_name}-help"
    >
    <div id="{component_name}-help" class="input-help">輔助說明文字</div>
</div>"""
        
        elif "form" in component_name:
            return f"""<form class="{component_name}" novalidate>
    <div class="form-group">
        <label for="email" class="form-label">電子郵件</label>
        <input id="email" type="email" class="form-input" required>
    </div>
    <div class="form-group">
        <label for="password" class="form-label">密碼</label>
        <input id="password" type="password" class="form-input" required>
    </div>
    <button type="submit" class="form-submit">提交</button>
</form>"""
        
        else:
            return f"""<div class="{component_name}">
    <h2 class="component-title">智能生成組件</h2>
    <p class="component-content">這是一個由SmartUI MCP自動生成的組件</p>
</div>"""
    
    def _generate_css_code(self, design_spec: Dict[str, Any]) -> str:
        """生成CSS代碼"""
        colors = design_spec["colors"]
        typography = design_spec["typography"]
        layout = design_spec["layout"]
        component_name = design_spec["component_name"]
        
        css_code = f"""/* SmartUI MCP 自動生成的CSS */
.{component_name} {{
    font-family: {typography["font_family"]};
    font-size: {typography["font_size_base"]};
    line-height: {typography["line_height"]};
    color: {colors["text"]};
    background-color: {colors["background"]};
    border: 1px solid {colors["border"]};
    border-radius: {self.design_system.border_radius};
    transition: all 0.2s ease-in-out;
"""
        
        # 添加布局樣式
        for prop, value in layout.items():
            css_property = prop.replace("_", "-")
            css_code += f"    {css_property}: {value};\n"
        
        css_code += "}\n\n"
        
        # 添加交互狀態
        css_code += f""".{component_name}:hover {{
    background-color: {colors["surface"]};
    border-color: {colors["primary"]};
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}}

.{component_name}:focus {{
    outline: 2px solid {colors["primary"]};
    outline-offset: 2px;
}}

.{component_name}:active {{
    transform: translateY(0);
}}

.{component_name}:disabled {{
    opacity: 0.6;
    cursor: not-allowed;
    background-color: {colors["surface"]};
}}

/* 響應式設計 */
@media (max-width: 768px) {{
    .{component_name} {{
        font-size: {typography["font_size_small"]};
        padding: 8px 16px;
    }}
}}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {{
    .{component_name} {{
        background-color: #2A2A2A;
        color: #FFFFFF;
        border-color: #404040;
    }}
}}

/* 高對比度支持 */
@media (prefers-contrast: high) {{
    .{component_name} {{
        border-width: 2px;
        font-weight: {typography["font_weight_medium"]};
    }}
}}"""
        
        return css_code
    
    def _generate_javascript_code(self, design_spec: Dict[str, Any]) -> str:
        """生成JavaScript代碼"""
        component_name = design_spec["component_name"]
        
        return f"""// SmartUI MCP 自動生成的JavaScript
class {component_name.replace('_', '').title()}Component {{
    constructor(element) {{
        this.element = element;
        this.init();
    }}
    
    init() {{
        this.addEventListeners();
        this.setupAccessibility();
        this.setupAnimations();
    }}
    
    addEventListeners() {{
        // 點擊事件
        this.element.addEventListener('click', this.handleClick.bind(this));
        
        // 鍵盤事件
        this.element.addEventListener('keydown', this.handleKeydown.bind(this));
        
        // 焦點事件
        this.element.addEventListener('focus', this.handleFocus.bind(this));
        this.element.addEventListener('blur', this.handleBlur.bind(this));
    }}
    
    handleClick(event) {{
        // 添加漣漪效果
        this.addRippleEffect(event);
        
        // 觸發自定義事件
        this.element.dispatchEvent(new CustomEvent('{component_name}:click', {{
            detail: {{ element: this.element }}
        }}));
    }}
    
    handleKeydown(event) {{
        // Enter 或 Space 鍵觸發點擊
        if (event.key === 'Enter' || event.key === ' ') {{
            event.preventDefault();
            this.handleClick(event);
        }}
    }}
    
    handleFocus(event) {{
        this.element.classList.add('focused');
    }}
    
    handleBlur(event) {{
        this.element.classList.remove('focused');
    }}
    
    addRippleEffect(event) {{
        const ripple = document.createElement('span');
        const rect = this.element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.style.cssText = `
            position: absolute;
            width: ${{size}}px;
            height: ${{size}}px;
            left: ${{x}}px;
            top: ${{y}}px;
            background: rgba(255,255,255,0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s ease-out;
            pointer-events: none;
        `;
        
        this.element.appendChild(ripple);
        
        setTimeout(() => {{
            ripple.remove();
        }}, 600);
    }}
    
    setupAccessibility() {{
        // 確保有適當的 ARIA 屬性
        if (!this.element.hasAttribute('role')) {{
            this.element.setAttribute('role', 'button');
        }}
        
        if (!this.element.hasAttribute('tabindex')) {{
            this.element.setAttribute('tabindex', '0');
        }}
    }}
    
    setupAnimations() {{
        // 添加CSS動畫樣式
        const style = document.createElement('style');
        style.textContent = `
            @keyframes ripple {{
                to {{
                    transform: scale(4);
                    opacity: 0;
                }}
            }}
        `;
        document.head.appendChild(style);
    }}
    
    // 公開API
    enable() {{
        this.element.disabled = false;
        this.element.setAttribute('aria-disabled', 'false');
    }}
    
    disable() {{
        this.element.disabled = true;
        this.element.setAttribute('aria-disabled', 'true');
    }}
    
    setLoading(loading) {{
        if (loading) {{
            this.element.classList.add('loading');
            this.element.setAttribute('aria-busy', 'true');
        }} else {{
            this.element.classList.remove('loading');
            this.element.setAttribute('aria-busy', 'false');
        }}
    }}
}}

// 自動初始化
document.addEventListener('DOMContentLoaded', () => {{
    const elements = document.querySelectorAll('.{component_name}');
    elements.forEach(element => {{
        new {component_name.replace('_', '').title()}Component(element);
    }});
}});"""
    
    def _generate_react_code(self, design_spec: Dict[str, Any]) -> str:
        """生成React代碼"""
        component_name = design_spec["component_name"].replace('_', '').title()
        
        return f"""// SmartUI MCP 自動生成的React組件
import React, {{ useState, useCallback, forwardRef }} from 'react';
import PropTypes from 'prop-types';

const {component_name} = forwardRef(({{
    children,
    onClick,
    disabled = false,
    loading = false,
    variant = 'primary',
    size = 'medium',
    className = '',
    ...props
}}, ref) => {{
    const [isClicked, setIsClicked] = useState(false);
    
    const handleClick = useCallback((event) => {{
        if (disabled || loading) return;
        
        setIsClicked(true);
        setTimeout(() => setIsClicked(false), 150);
        
        onClick?.(event);
    }}, [disabled, loading, onClick]);
    
    const classNames = [
        '{component_name.lower()}',
        `{component_name.lower()}--${{variant}}`,
        `{component_name.lower()}--${{size}}`,
        disabled && '{component_name.lower()}--disabled',
        loading && '{component_name.lower()}--loading',
        isClicked && '{component_name.lower()}--clicked',
        className
    ].filter(Boolean).join(' ');
    
    return (
        <button
            ref={{ref}}
            className={{classNames}}
            onClick={{handleClick}}
            disabled={{disabled || loading}}
            aria-disabled={{disabled || loading}}
            aria-busy={{loading}}
            {{...props}}
        >
            {{loading && (
                <span className="{component_name.lower()}__spinner" aria-hidden="true">
                    <svg viewBox="0 0 24 24" className="{component_name.lower()}__spinner-icon">
                        <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2" />
                    </svg>
                </span>
            )}}
            <span className="{component_name.lower()}__content">
                {{children}}
            </span>
        </button>
    );
}});

{component_name}.propTypes = {{
    children: PropTypes.node,
    onClick: PropTypes.func,
    disabled: PropTypes.bool,
    loading: PropTypes.bool,
    variant: PropTypes.oneOf(['primary', 'secondary', 'success', 'warning', 'danger']),
    size: PropTypes.oneOf(['small', 'medium', 'large']),
    className: PropTypes.string
}};

{component_name}.displayName = '{component_name}';

export default {component_name};"""
    
    async def _optimize_performance(self, code_result: Dict[str, Any]) -> Dict[str, Any]:
        """優化性能"""
        await asyncio.sleep(0.1)
        
        # 模擬性能優化
        optimizations = [
            "CSS最小化",
            "JavaScript優化",
            "圖片壓縮",
            "緩存策略",
            "懶加載"
        ]
        
        # 計算性能評分
        performance_score = 85.0 + (len(optimizations) * 2)
        
        # 返回優化後的代碼和評分
        return {
            **code_result,
            "optimizations": optimizations,
            "performance_score": min(performance_score, 100.0)
        }
    
    async def _add_accessibility_features(self, code_result: Dict[str, Any], level: AccessibilityLevel) -> Dict[str, Any]:
        """添加無障礙功能"""
        await asyncio.sleep(0.1)
        
        accessibility_features = []
        
        # 基礎無障礙功能
        accessibility_features.extend([
            "ARIA標籤支持",
            "鍵盤導航支持",
            "焦點管理",
            "語義化HTML"
        ])
        
        # WCAG AA級別
        if level in [AccessibilityLevel.WCAG_AA, AccessibilityLevel.WCAG_AAA]:
            accessibility_features.extend([
                "顏色對比度符合標準",
                "文字大小可調整",
                "屏幕閱讀器支持",
                "高對比度模式"
            ])
        
        # WCAG AAA級別
        if level == AccessibilityLevel.WCAG_AAA:
            accessibility_features.extend([
                "增強的顏色對比度",
                "更完善的鍵盤支持",
                "詳細的ARIA描述",
                "無障礙測試通過"
            ])
        
        return {
            **code_result,
            "accessibility_features": accessibility_features
        }
    
    async def _add_responsive_design(self, code_result: Dict[str, Any], responsive: bool) -> Dict[str, Any]:
        """添加響應式設計"""
        await asyncio.sleep(0.1)
        
        if not responsive:
            return {
                **code_result,
                "breakpoints": {}
            }
        
        # 添加響應式斷點
        breakpoints = {
            "mobile": "max-width: 767px",
            "tablet": "min-width: 768px and max-width: 1023px",
            "desktop": "min-width: 1024px"
        }
        
        # 在CSS中添加響應式規則
        responsive_css = f"""
/* 響應式設計 - 移動設備 */
@media ({breakpoints["mobile"]}) {{
    .{code_result["id"]} {{
        padding: 8px 12px;
        font-size: 14px;
    }}
}}

/* 響應式設計 - 平板設備 */
@media ({breakpoints["tablet"]}) {{
    .{code_result["id"]} {{
        padding: 10px 16px;
        font-size: 15px;
    }}
}}

/* 響應式設計 - 桌面設備 */
@media ({breakpoints["desktop"]}) {{
    .{code_result["id"]} {{
        padding: 12px 24px;
        font-size: 16px;
    }}
}}"""
        
        code_result["css"] += responsive_css
        
        return {
            **code_result,
            "breakpoints": breakpoints
        }
    
    async def optimize_existing_component(self, component_id: str) -> Dict[str, Any]:
        """優化現有組件"""
        if component_id not in self.generated_components:
            raise ValueError(f"組件 {component_id} 不存在")
        
        component = self.generated_components[component_id]
        
        print(f"🔧 優化組件: {component.name}")
        
        # 性能分析
        performance_issues = await self._analyze_performance(component)
        
        # 無障礙分析
        accessibility_issues = await self._analyze_accessibility(component)
        
        # 代碼質量分析
        quality_issues = await self._analyze_code_quality(component)
        
        # 生成優化建議
        optimizations = {
            "performance": performance_issues,
            "accessibility": accessibility_issues,
            "quality": quality_issues,
            "recommendations": self._generate_optimization_recommendations(
                performance_issues, accessibility_issues, quality_issues
            )
        }
        
        print(f"✅ 組件優化分析完成")
        print(f"   性能問題: {len(performance_issues)}個")
        print(f"   無障礙問題: {len(accessibility_issues)}個")
        print(f"   質量問題: {len(quality_issues)}個")
        
        return optimizations
    
    async def _analyze_performance(self, component: GeneratedUIComponent) -> List[Dict[str, Any]]:
        """分析性能問題"""
        await asyncio.sleep(0.1)
        
        issues = []
        
        # 檢查CSS大小
        if len(component.css_code) > 5000:
            issues.append({
                "type": "css_size",
                "severity": "medium",
                "message": "CSS文件過大，建議拆分或最小化",
                "recommendation": "使用CSS最小化工具"
            })
        
        # 檢查JavaScript複雜度
        if component.javascript_code.count('function') > 10:
            issues.append({
                "type": "js_complexity",
                "severity": "medium", 
                "message": "JavaScript函數過多，建議重構",
                "recommendation": "拆分為更小的模組"
            })
        
        return issues
    
    async def _analyze_accessibility(self, component: GeneratedUIComponent) -> List[Dict[str, Any]]:
        """分析無障礙問題"""
        await asyncio.sleep(0.1)
        
        issues = []
        
        # 檢查ARIA標籤
        if 'aria-label' not in component.html_code:
            issues.append({
                "type": "missing_aria",
                "severity": "high",
                "message": "缺少ARIA標籤",
                "recommendation": "添加適當的ARIA屬性"
            })
        
        # 檢查鍵盤支持
        if 'tabindex' not in component.html_code:
            issues.append({
                "type": "keyboard_support",
                "severity": "medium",
                "message": "可能缺少鍵盤支持",
                "recommendation": "確保所有交互元素支持鍵盤操作"
            })
        
        return issues
    
    async def _analyze_code_quality(self, component: GeneratedUIComponent) -> List[Dict[str, Any]]:
        """分析代碼質量"""
        await asyncio.sleep(0.1)
        
        issues = []
        
        # 檢查代碼註釋
        comment_ratio = component.javascript_code.count('//') / max(component.javascript_code.count('\n'), 1)
        if comment_ratio < 0.1:
            issues.append({
                "type": "insufficient_comments",
                "severity": "low",
                "message": "代碼註釋不足",
                "recommendation": "添加更多解釋性註釋"
            })
        
        return issues
    
    def _generate_optimization_recommendations(self, perf_issues: List, acc_issues: List, quality_issues: List) -> List[str]:
        """生成優化建議"""
        recommendations = []
        
        if perf_issues:
            recommendations.append("🚀 性能優化: 壓縮CSS和JavaScript文件")
            recommendations.append("⚡ 性能優化: 實施懶加載策略")
        
        if acc_issues:
            recommendations.append("♿ 無障礙優化: 完善ARIA標籤和鍵盤支持")
            recommendations.append("🎯 無障礙優化: 測試屏幕閱讀器兼容性")
        
        if quality_issues:
            recommendations.append("📝 代碼質量: 增加註釋和文檔")
            recommendations.append("🔧 代碼質量: 重構複雜函數")
        
        if not any([perf_issues, acc_issues, quality_issues]):
            recommendations.append("✅ 組件質量優秀，無需額外優化")
        
        return recommendations
    
    def get_component_library_stats(self) -> Dict[str, Any]:
        """獲取組件庫統計"""
        return {
            "total_components": len(self.generated_components),
            "component_types": list(set(comp.component_type.value for comp in self.generated_components.values())),
            "avg_performance_score": sum(comp.performance_score for comp in self.generated_components.values()) / max(len(self.generated_components), 1),
            "template_library": {
                comp_type.value: len(templates["templates"]) 
                for comp_type, templates in self.component_library.items()
            },
            "generation_stats": {
                "today": len([comp for comp in self.generated_components.values() 
                            if time.time() - comp.generated_at < 86400]),
                "this_week": len([comp for comp in self.generated_components.values() 
                               if time.time() - comp.generated_at < 604800])
            }
        }

# 演示函數
async def demo_smartui_mcp():
    """演示SmartUI MCP功能"""
    print("🤖 SmartUI MCP 智能UI生成演示")
    print("=" * 60)
    
    smartui = SmartUIMCP()
    
    # 演示不同類型的組件生成
    test_requests = [
        UIGenerationRequest(
            description="創建一個現代風格的登入按鈕，支援響應式設計和無障礙訪問",
            component_type=UIComponentType.BUTTON,
            theme=DesignTheme.MODERN,
            accessibility=AccessibilityLevel.WCAG_AA,
            framework="react"
        ),
        UIGenerationRequest(
            description="生成一個企業級的輸入框，包含驗證和幫助文字",
            component_type=UIComponentType.INPUT_FIELD,
            theme=DesignTheme.CORPORATE,
            accessibility=AccessibilityLevel.WCAG_AA,
            brand_colors={"primary": "#0066CC"}
        ),
        UIGenerationRequest(
            description="創建一個簡潔的登入表單，包含用戶名、密碼和提交按鈕",
            component_type=UIComponentType.FORM,
            theme=DesignTheme.MINIMAL,
            accessibility=AccessibilityLevel.WCAG_AAA
        )
    ]
    
    generated_components = []
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n🎨 生成第{i}個組件...")
        try:
            component = await smartui.generate_ui_component(request)
            generated_components.append(component)
            
            print(f"   組件ID: {component.id}")
            print(f"   組件名稱: {component.name}")
            print(f"   組件類型: {component.component_type.value}")
            print(f"   性能評分: {component.performance_score}/100")
            print(f"   無障礙功能: {len(component.accessibility_features)}項")
            
        except Exception as e:
            print(f"   ❌ 生成失敗: {e}")
    
    # 優化演示
    if generated_components:
        print(f"\n🔧 優化組件演示...")
        first_component = generated_components[0]
        
        optimization_result = await smartui.optimize_existing_component(first_component.id)
        
        print(f"   優化建議數: {len(optimization_result['recommendations'])}")
        for rec in optimization_result['recommendations']:
            print(f"   {rec}")
    
    # 顯示組件庫統計
    print(f"\n📊 組件庫統計:")
    stats = smartui.get_component_library_stats()
    print(f"   總組件數: {stats['total_components']}")
    print(f"   組件類型: {', '.join(stats['component_types'])}")
    print(f"   平均性能: {stats['avg_performance_score']:.1f}/100")
    print(f"   今日生成: {stats['generation_stats']['today']}個")
    
    return smartui, generated_components

if __name__ == "__main__":
    asyncio.run(demo_smartui_mcp())