"""
PowerAutomation 4.0 代码生成器

基于元素分析结果生成高质量的自动化代码，支持多种框架和语言。
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from jinja2 import Environment, BaseLoader, Template


class ActionType(Enum):
    """操作类型"""
    CLICK = "click"
    INPUT = "input"
    SELECT = "select"
    HOVER = "hover"
    WAIT = "wait"
    EXTRACT = "extract"
    SCROLL = "scroll"
    DRAG_DROP = "drag_drop"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    CLEAR = "clear"
    SUBMIT = "submit"
    UPLOAD = "upload"
    DOWNLOAD = "download"


class CodeFramework(Enum):
    """代码框架"""
    SELENIUM = "selenium"
    PLAYWRIGHT = "playwright"
    PUPPETEER = "puppeteer"
    CYPRESS = "cypress"
    REQUESTS = "requests"


class CodeLanguage(Enum):
    """编程语言"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"


@dataclass
class CodeTemplate:
    """代码模板"""
    name: str
    framework: CodeFramework
    language: CodeLanguage
    action_type: ActionType
    template: str
    imports: List[str]
    setup_code: List[str]
    cleanup_code: List[str]
    variables: Dict[str, Any]


@dataclass
class GeneratedCodeResult:
    """生成的代码结果"""
    code: str
    language: str
    framework: str
    action_type: str
    confidence: float
    imports: List[str]
    setup_required: bool
    cleanup_required: bool
    variables_used: List[str]
    optimization_suggestions: List[str]


class CodeGenerator:
    """代码生成器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 模板引擎
        self.jinja_env = Environment(loader=BaseLoader())
        
        # 代码模板存储
        self.templates: Dict[str, CodeTemplate] = {}
        
        # 代码优化规则
        self.optimization_rules = []
        
        # 生成统计
        self.stats = {
            "total_generated": 0,
            "by_framework": {},
            "by_language": {},
            "by_action": {},
            "avg_confidence": 0.0
        }
        
        # 运行状态
        self.is_running = False
    
    async def start(self):
        """启动代码生成器"""
        if self.is_running:
            return
        
        self.logger.info("启动代码生成器...")
        
        # 初始化代码模板
        await self._initialize_templates()
        
        # 初始化优化规则
        await self._initialize_optimization_rules()
        
        self.is_running = True
        self.logger.info("代码生成器启动完成")
    
    async def stop(self):
        """停止代码生成器"""
        if not self.is_running:
            return
        
        self.logger.info("停止代码生成器...")
        
        # 清理资源
        self.templates.clear()
        self.optimization_rules.clear()
        
        self.is_running = False
        self.logger.info("代码生成器已停止")
    
    async def generate_code(
        self,
        element_selection: Any,  # ElementSelection对象
        action_type: str,
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """生成代码"""
        if not self.is_running:
            raise RuntimeError("代码生成器未启动")
        
        options = options or {}
        framework = options.get("framework", "selenium")
        language = options.get("language", "python")
        
        try:
            # 获取对应的模板
            template_key = f"{framework}_{language}_{action_type}"
            template = self.templates.get(template_key)
            
            if not template:
                # 尝试获取默认模板
                template = await self._get_default_template(framework, language, action_type)
            
            if not template:
                raise ValueError(f"未找到模板: {template_key}")
            
            # 准备模板变量
            template_vars = await self._prepare_template_variables(
                element_selection, action_type, options
            )
            
            # 渲染代码
            jinja_template = self.jinja_env.from_string(template.template)
            generated_code = jinja_template.render(**template_vars)
            
            # 代码优化
            optimized_code = await self._optimize_code(generated_code, template, options)
            
            # 计算置信度
            confidence = await self._calculate_code_confidence(
                element_selection, template, template_vars
            )
            
            # 生成优化建议
            suggestions = await self._generate_optimization_suggestions(
                optimized_code, template, options
            )
            
            # 更新统计
            self._update_statistics(framework, language, action_type, confidence)
            
            result = GeneratedCodeResult(
                code=optimized_code,
                language=language,
                framework=framework,
                action_type=action_type,
                confidence=confidence,
                imports=template.imports.copy(),
                setup_required=bool(template.setup_code),
                cleanup_required=bool(template.cleanup_code),
                variables_used=list(template_vars.keys()),
                optimization_suggestions=suggestions
            )
            
            self.logger.info(f"代码生成完成: {action_type}, 置信度: {confidence:.2f}")
            return asdict(result)
            
        except Exception as e:
            self.logger.error(f"代码生成失败: {e}")
            raise
    
    async def get_suggestions(
        self,
        element_selection: Any,
        context: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """获取代码建议"""
        context = context or {}
        suggestions = []
        
        # 基于元素类型推荐操作
        element_type = getattr(element_selection, 'element_type', 'unknown')
        
        if element_type == "button":
            suggestions.extend([
                {
                    "action": "click",
                    "description": "点击按钮",
                    "confidence": 0.9,
                    "frameworks": ["selenium", "playwright", "puppeteer"]
                },
                {
                    "action": "hover",
                    "description": "悬停在按钮上",
                    "confidence": 0.7,
                    "frameworks": ["selenium", "playwright", "puppeteer"]
                }
            ])
        elif element_type == "input":
            suggestions.extend([
                {
                    "action": "input",
                    "description": "输入文本",
                    "confidence": 0.9,
                    "frameworks": ["selenium", "playwright", "puppeteer"]
                },
                {
                    "action": "clear",
                    "description": "清空输入框",
                    "confidence": 0.8,
                    "frameworks": ["selenium", "playwright", "puppeteer"]
                }
            ])
        elif element_type == "select":
            suggestions.extend([
                {
                    "action": "select",
                    "description": "选择选项",
                    "confidence": 0.9,
                    "frameworks": ["selenium", "playwright", "puppeteer"]
                }
            ])
        elif element_type == "link":
            suggestions.extend([
                {
                    "action": "click",
                    "description": "点击链接",
                    "confidence": 0.9,
                    "frameworks": ["selenium", "playwright", "puppeteer"]
                }
            ])
        
        # 通用操作建议
        suggestions.extend([
            {
                "action": "extract",
                "description": "提取元素文本",
                "confidence": 0.8,
                "frameworks": ["selenium", "playwright", "puppeteer", "requests"]
            },
            {
                "action": "wait",
                "description": "等待元素出现",
                "confidence": 0.7,
                "frameworks": ["selenium", "playwright", "puppeteer"]
            }
        ])
        
        return suggestions
    
    async def optimize_code(
        self,
        code: str,
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """优化代码"""
        options = options or {}
        
        optimized_code = code
        applied_optimizations = []
        
        # 应用优化规则
        for rule in self.optimization_rules:
            if rule["enabled"]:
                try:
                    result = await self._apply_optimization_rule(optimized_code, rule)
                    if result["modified"]:
                        optimized_code = result["code"]
                        applied_optimizations.append(rule["name"])
                except Exception as e:
                    self.logger.warning(f"优化规则应用失败 {rule['name']}: {e}")
        
        return {
            "original_code": code,
            "optimized_code": optimized_code,
            "applied_optimizations": applied_optimizations,
            "improvement_score": await self._calculate_improvement_score(code, optimized_code)
        }
    
    async def export_code(
        self,
        generated_code_list: List[Dict[str, Any]],
        format: str = "python",
        include_comments: bool = True
    ) -> str:
        """导出代码"""
        if not generated_code_list:
            return ""
        
        # 按框架和语言分组
        grouped_code = {}
        for code_data in generated_code_list:
            key = f"{code_data.get('language', 'python')}_{code_data.get('framework', 'selenium')}"
            if key not in grouped_code:
                grouped_code[key] = []
            grouped_code[key].append(code_data)
        
        # 生成完整代码
        exported_parts = []
        
        for group_key, code_list in grouped_code.items():
            language, framework = group_key.split('_')
            
            # 添加文件头注释
            if include_comments:
                exported_parts.append(f"# PowerAutomation 4.0 生成的代码")
                exported_parts.append(f"# 框架: {framework}")
                exported_parts.append(f"# 语言: {language}")
                exported_parts.append(f"# 生成时间: {datetime.now().isoformat()}")
                exported_parts.append("")
            
            # 添加导入语句
            all_imports = set()
            for code_data in code_list:
                imports = code_data.get('imports', [])
                all_imports.update(imports)
            
            if all_imports:
                for import_stmt in sorted(all_imports):
                    exported_parts.append(import_stmt)
                exported_parts.append("")
            
            # 添加设置代码
            setup_code = await self._generate_setup_code(framework, language)
            if setup_code:
                if include_comments:
                    exported_parts.append("# 初始化设置")
                exported_parts.extend(setup_code)
                exported_parts.append("")
            
            # 添加主要代码
            if include_comments:
                exported_parts.append("# 主要操作代码")
            
            for i, code_data in enumerate(code_list):
                if include_comments:
                    action_type = code_data.get('code_type', 'unknown')
                    exported_parts.append(f"# 操作 {i+1}: {action_type}")
                
                code = code_data.get('generated_code', '')
                # 确保代码缩进正确
                code_lines = code.split('\n')
                for line in code_lines:
                    if line.strip():
                        exported_parts.append(line)
                
                exported_parts.append("")
            
            # 添加清理代码
            cleanup_code = await self._generate_cleanup_code(framework, language)
            if cleanup_code:
                if include_comments:
                    exported_parts.append("# 清理资源")
                exported_parts.extend(cleanup_code)
                exported_parts.append("")
        
        return '\n'.join(exported_parts)
    
    async def _initialize_templates(self):
        """初始化代码模板"""
        # Selenium Python 模板
        self.templates["selenium_python_click"] = CodeTemplate(
            name="selenium_python_click",
            framework=CodeFramework.SELENIUM,
            language=CodeLanguage.PYTHON,
            action_type=ActionType.CLICK,
            template="""# 点击元素: {{ element_description }}
element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "{{ selector }}")))
element.click()""",
            imports=[
                "from selenium import webdriver",
                "from selenium.webdriver.common.by import By",
                "from selenium.webdriver.support.ui import WebDriverWait",
                "from selenium.webdriver.support import expected_conditions as EC"
            ],
            setup_code=[
                "driver = webdriver.Chrome()",
                "wait = WebDriverWait(driver, 10)"
            ],
            cleanup_code=["driver.quit()"],
            variables={}
        )
        
        self.templates["selenium_python_input"] = CodeTemplate(
            name="selenium_python_input",
            framework=CodeFramework.SELENIUM,
            language=CodeLanguage.PYTHON,
            action_type=ActionType.INPUT,
            template="""# 输入文本到元素: {{ element_description }}
element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "{{ selector }}")))
element.clear()
element.send_keys("{{ input_text }}")""",
            imports=[
                "from selenium import webdriver",
                "from selenium.webdriver.common.by import By",
                "from selenium.webdriver.support.ui import WebDriverWait",
                "from selenium.webdriver.support import expected_conditions as EC"
            ],
            setup_code=[
                "driver = webdriver.Chrome()",
                "wait = WebDriverWait(driver, 10)"
            ],
            cleanup_code=["driver.quit()"],
            variables={}
        )
        
        # Playwright Python 模板
        self.templates["playwright_python_click"] = CodeTemplate(
            name="playwright_python_click",
            framework=CodeFramework.PLAYWRIGHT,
            language=CodeLanguage.PYTHON,
            action_type=ActionType.CLICK,
            template="""# 点击元素: {{ element_description }}
await page.click("{{ selector }}")""",
            imports=[
                "from playwright.async_api import async_playwright"
            ],
            setup_code=[
                "async with async_playwright() as p:",
                "    browser = await p.chromium.launch()",
                "    page = await browser.new_page()"
            ],
            cleanup_code=["    await browser.close()"],
            variables={}
        )
        
        # JavaScript Puppeteer 模板
        self.templates["puppeteer_javascript_click"] = CodeTemplate(
            name="puppeteer_javascript_click",
            framework=CodeFramework.PUPPETEER,
            language=CodeLanguage.JAVASCRIPT,
            action_type=ActionType.CLICK,
            template="""// 点击元素: {{ element_description }}
await page.click('{{ selector }}');""",
            imports=["const puppeteer = require('puppeteer');"],
            setup_code=[
                "const browser = await puppeteer.launch();",
                "const page = await browser.newPage();"
            ],
            cleanup_code=["await browser.close();"],
            variables={}
        )
        
        # 添加更多模板...
        await self._load_additional_templates()
    
    async def _load_additional_templates(self):
        """加载额外的模板"""
        # 这里可以从配置文件或数据库加载更多模板
        additional_templates = {
            # Selenium 更多操作
            "selenium_python_hover": {
                "template": """# 悬停在元素上: {{ element_description }}
element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "{{ selector }}")))
ActionChains(driver).move_to_element(element).perform()""",
                "imports": ["from selenium.webdriver.common.action_chains import ActionChains"]
            },
            
            "selenium_python_wait": {
                "template": """# 等待元素: {{ element_description }}
element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "{{ selector }}")))""",
                "imports": []
            },
            
            "selenium_python_extract": {
                "template": """# 提取元素文本: {{ element_description }}
element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "{{ selector }}")))
text = element.text
print(f"提取的文本: {text}")""",
                "imports": []
            },
            
            # Playwright 更多操作
            "playwright_python_input": {
                "template": """# 输入文本到元素: {{ element_description }}
await page.fill("{{ selector }}", "{{ input_text }}")""",
                "imports": []
            },
            
            "playwright_python_extract": {
                "template": """# 提取元素文本: {{ element_description }}
text = await page.text_content("{{ selector }}")
print(f"提取的文本: {text}")""",
                "imports": []
            }
        }
        
        # 转换为CodeTemplate对象
        for template_key, template_data in additional_templates.items():
            parts = template_key.split('_')
            framework = parts[0]
            language = parts[1]
            action = parts[2]
            
            self.templates[template_key] = CodeTemplate(
                name=template_key,
                framework=CodeFramework(framework),
                language=CodeLanguage(language),
                action_type=ActionType(action),
                template=template_data["template"],
                imports=template_data.get("imports", []),
                setup_code=[],
                cleanup_code=[],
                variables={}
            )
    
    async def _initialize_optimization_rules(self):
        """初始化优化规则"""
        self.optimization_rules = [
            {
                "name": "remove_redundant_waits",
                "description": "移除冗余的等待语句",
                "enabled": True,
                "pattern": r"wait\.until.*\n\s*wait\.until",
                "replacement": lambda m: m.group(0).split('\n')[0]  # 保留第一个wait
            },
            {
                "name": "combine_similar_selectors",
                "description": "合并相似的选择器",
                "enabled": True,
                "pattern": r'By\.CSS_SELECTOR,\s*"([^"]+)"\)\s*\n.*By\.CSS_SELECTOR,\s*"\1"',
                "replacement": lambda m: m.group(0).split('\n')[0]  # 保留第一个
            },
            {
                "name": "add_error_handling",
                "description": "添加错误处理",
                "enabled": True,
                "pattern": r"(element\.click\(\)|page\.click\()",
                "replacement": r"try:\n    \1\nexcept Exception as e:\n    print(f'点击失败: {e}')"
            }
        ]
    
    async def _get_default_template(
        self,
        framework: str,
        language: str,
        action_type: str
    ) -> Optional[CodeTemplate]:
        """获取默认模板"""
        # 尝试获取通用模板
        generic_key = f"{framework}_{language}_generic"
        if generic_key in self.templates:
            template = self.templates[generic_key]
            # 复制并修改模板
            return CodeTemplate(
                name=f"{framework}_{language}_{action_type}",
                framework=template.framework,
                language=template.language,
                action_type=ActionType(action_type),
                template=f"# {action_type} 操作\n# 选择器: {{{{ selector }}}}\n# 请手动实现具体逻辑",
                imports=template.imports,
                setup_code=template.setup_code,
                cleanup_code=template.cleanup_code,
                variables=template.variables
            )
        
        return None
    
    async def _prepare_template_variables(
        self,
        element_selection: Any,
        action_type: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """准备模板变量"""
        variables = {
            "selector": getattr(element_selection, 'selector', ''),
            "element_description": f"{getattr(element_selection, 'tag_name', 'element')} 元素",
            "action_type": action_type,
            "timestamp": datetime.now().isoformat()
        }
        
        # 添加特定操作的变量
        if action_type == "input":
            variables["input_text"] = options.get("text", "示例文本")
        elif action_type == "select":
            variables["option_value"] = options.get("value", "")
            variables["option_text"] = options.get("text", "")
        elif action_type == "wait":
            variables["timeout"] = options.get("timeout", 10)
        
        # 添加元素特定信息
        if hasattr(element_selection, 'text_content'):
            variables["element_text"] = element_selection.text_content
        
        if hasattr(element_selection, 'attributes'):
            variables["element_attributes"] = element_selection.attributes
        
        return variables
    
    async def _optimize_code(
        self,
        code: str,
        template: CodeTemplate,
        options: Dict[str, Any]
    ) -> str:
        """优化代码"""
        optimized_code = code
        
        # 应用基础优化
        optimized_code = self._apply_basic_optimizations(optimized_code)
        
        # 应用框架特定优化
        if template.framework == CodeFramework.SELENIUM:
            optimized_code = self._optimize_selenium_code(optimized_code)
        elif template.framework == CodeFramework.PLAYWRIGHT:
            optimized_code = self._optimize_playwright_code(optimized_code)
        
        return optimized_code
    
    def _apply_basic_optimizations(self, code: str) -> str:
        """应用基础优化"""
        # 移除多余的空行
        code = re.sub(r'\n\s*\n\s*\n', '\n\n', code)
        
        # 标准化缩进
        lines = code.split('\n')
        optimized_lines = []
        for line in lines:
            if line.strip():
                # 确保正确的缩进
                optimized_lines.append(line.rstrip())
            else:
                optimized_lines.append('')
        
        return '\n'.join(optimized_lines)
    
    def _optimize_selenium_code(self, code: str) -> str:
        """优化Selenium代码"""
        # 添加显式等待
        if "element.click()" in code and "wait.until" not in code:
            code = code.replace(
                "element.click()",
                "wait.until(EC.element_to_be_clickable(element)).click()"
            )
        
        return code
    
    def _optimize_playwright_code(self, code: str) -> str:
        """优化Playwright代码"""
        # 添加等待选项
        if "page.click(" in code and "timeout" not in code:
            code = code.replace(
                'page.click("',
                'page.click("'
            )
        
        return code
    
    async def _calculate_code_confidence(
        self,
        element_selection: Any,
        template: CodeTemplate,
        template_vars: Dict[str, Any]
    ) -> float:
        """计算代码置信度"""
        base_confidence = 0.7
        
        # 基于选择器质量
        selector_confidence = getattr(element_selection, 'confidence', 0.5)
        base_confidence += selector_confidence * 0.2
        
        # 基于模板匹配度
        if template.action_type.value in template_vars.get("action_type", ""):
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    async def _generate_optimization_suggestions(
        self,
        code: str,
        template: CodeTemplate,
        options: Dict[str, Any]
    ) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        # 检查错误处理
        if "try:" not in code and "except:" not in code:
            suggestions.append("建议添加错误处理机制")
        
        # 检查等待机制
        if template.framework == CodeFramework.SELENIUM:
            if "wait.until" not in code:
                suggestions.append("建议添加显式等待")
        
        # 检查选择器稳定性
        if '"#' not in code and '".':  # 没有ID选择器，使用类选择器
            suggestions.append("考虑使用更稳定的选择器（如ID）")
        
        return suggestions
    
    async def _apply_optimization_rule(
        self,
        code: str,
        rule: Dict[str, Any]
    ) -> Dict[str, Any]:
        """应用优化规则"""
        pattern = rule["pattern"]
        replacement = rule["replacement"]
        
        if isinstance(replacement, str):
            new_code = re.sub(pattern, replacement, code)
        else:
            # 函数替换
            new_code = re.sub(pattern, replacement, code)
        
        return {
            "code": new_code,
            "modified": new_code != code
        }
    
    async def _calculate_improvement_score(
        self,
        original_code: str,
        optimized_code: str
    ) -> float:
        """计算改进分数"""
        # 简单的改进评估
        original_lines = len(original_code.split('\n'))
        optimized_lines = len(optimized_code.split('\n'))
        
        # 基于代码行数变化
        if optimized_lines < original_lines:
            return 0.1  # 代码更简洁
        elif optimized_lines > original_lines:
            return 0.05  # 可能添加了错误处理等
        
        return 0.0
    
    async def _generate_setup_code(
        self,
        framework: str,
        language: str
    ) -> List[str]:
        """生成设置代码"""
        if framework == "selenium" and language == "python":
            return [
                "# 初始化WebDriver",
                "from selenium import webdriver",
                "from selenium.webdriver.support.ui import WebDriverWait",
                "from selenium.webdriver.support import expected_conditions as EC",
                "",
                "driver = webdriver.Chrome()",
                "wait = WebDriverWait(driver, 10)"
            ]
        elif framework == "playwright" and language == "python":
            return [
                "# 初始化Playwright",
                "from playwright.async_api import async_playwright",
                "",
                "async with async_playwright() as p:",
                "    browser = await p.chromium.launch()",
                "    page = await browser.new_page()"
            ]
        
        return []
    
    async def _generate_cleanup_code(
        self,
        framework: str,
        language: str
    ) -> List[str]:
        """生成清理代码"""
        if framework == "selenium" and language == "python":
            return [
                "# 清理资源",
                "driver.quit()"
            ]
        elif framework == "playwright" and language == "python":
            return [
                "    # 清理资源",
                "    await browser.close()"
            ]
        
        return []
    
    def _update_statistics(
        self,
        framework: str,
        language: str,
        action_type: str,
        confidence: float
    ):
        """更新统计信息"""
        self.stats["total_generated"] += 1
        
        # 按框架统计
        if framework not in self.stats["by_framework"]:
            self.stats["by_framework"][framework] = 0
        self.stats["by_framework"][framework] += 1
        
        # 按语言统计
        if language not in self.stats["by_language"]:
            self.stats["by_language"][language] = 0
        self.stats["by_language"][language] += 1
        
        # 按操作统计
        if action_type not in self.stats["by_action"]:
            self.stats["by_action"][action_type] = 0
        self.stats["by_action"][action_type] += 1
        
        # 更新平均置信度
        total = self.stats["total_generated"]
        current_avg = self.stats["avg_confidence"]
        self.stats["avg_confidence"] = (
            (current_avg * (total - 1) + confidence) / total
        )
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "component": "code_generator",
            "status": "healthy" if self.is_running else "unhealthy",
            "templates_loaded": len(self.templates),
            "optimization_rules": len(self.optimization_rules),
            "statistics": await self.get_statistics()
        }

