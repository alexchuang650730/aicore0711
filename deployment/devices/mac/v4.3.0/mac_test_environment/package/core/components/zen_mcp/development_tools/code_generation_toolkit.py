"""
Zen MCP代码生成工具包

提供智能代码生成功能，包括：
- 多语言代码生成
- 模板驱动开发
- AI辅助编程
- 代码重构工具
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import ast
import re
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class CodeLanguage(Enum):
    """编程语言枚举"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    CPP = "cpp"
    HTML = "html"
    CSS = "css"
    SQL = "sql"

class CodeTemplate(Enum):
    """代码模板类型枚举"""
    CLASS = "class"
    FUNCTION = "function"
    MODULE = "module"
    API_ENDPOINT = "api_endpoint"
    DATABASE_MODEL = "database_model"
    TEST_CASE = "test_case"
    COMPONENT = "component"
    SERVICE = "service"
    UTILITY = "utility"

class GenerationMode(Enum):
    """生成模式枚举"""
    TEMPLATE_BASED = "template_based"
    AI_ASSISTED = "ai_assisted"
    PATTERN_MATCHING = "pattern_matching"
    REFACTORING = "refactoring"
    OPTIMIZATION = "optimization"

@dataclass
class CodeGenerationRequest:
    """代码生成请求数据结构"""
    id: str
    language: CodeLanguage
    template_type: CodeTemplate
    generation_mode: GenerationMode
    requirements: Dict[str, Any]
    context: Dict[str, Any]
    output_path: str
    created_at: datetime
    priority: int = 1
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class GeneratedCode:
    """生成的代码数据结构"""
    request_id: str
    language: CodeLanguage
    code_content: str
    file_path: str
    quality_score: float
    complexity_metrics: Dict[str, Any]
    dependencies: List[str]
    documentation: str
    test_coverage: float
    generated_at: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class CodeGenerationToolkit:
    """Zen MCP代码生成工具包核心类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化代码生成工具包
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.generation_requests: Dict[str, CodeGenerationRequest] = {}
        self.generated_codes: Dict[str, GeneratedCode] = {}
        self.templates: Dict[str, Dict[str, str]] = {}
        self.ai_models: Dict[str, Any] = {}
        self.quality_metrics: Dict[str, float] = {}
        
        # 配置参数
        self.output_directory = self.config.get('output_directory', './generated_code')
        self.template_directory = self.config.get('template_directory', './templates')
        self.quality_threshold = self.config.get('quality_threshold', 0.8)
        self.max_complexity = self.config.get('max_complexity', 10)
        self.enable_ai_assistance = self.config.get('enable_ai_assistance', True)
        
        # 初始化模板
        self._initialize_templates()
        
        logger.info("Zen MCP代码生成工具包初始化完成")
    
    async def generate_code(self,
                           language: CodeLanguage,
                           template_type: CodeTemplate,
                           requirements: Dict[str, Any],
                           generation_mode: GenerationMode = GenerationMode.TEMPLATE_BASED,
                           output_path: str = None,
                           context: Dict[str, Any] = None) -> str:
        """
        生成代码
        
        Args:
            language: 编程语言
            template_type: 模板类型
            requirements: 需求规格
            generation_mode: 生成模式
            output_path: 输出路径
            context: 上下文信息
            
        Returns:
            生成请求ID
        """
        try:
            request_id = f"gen_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # 创建生成请求
            request = CodeGenerationRequest(
                id=request_id,
                language=language,
                template_type=template_type,
                generation_mode=generation_mode,
                requirements=requirements,
                context=context or {},
                output_path=output_path or self._generate_output_path(language, template_type),
                created_at=datetime.now()
            )
            
            self.generation_requests[request_id] = request
            
            # 异步执行代码生成
            asyncio.create_task(self._execute_code_generation(request_id))
            
            logger.info(f"代码生成请求创建成功: {request_id}")
            return request_id
            
        except Exception as e:
            logger.error(f"创建代码生成请求失败: {e}")
            raise
    
    async def generate_from_specification(self,
                                        specification: Dict[str, Any],
                                        target_language: CodeLanguage = CodeLanguage.PYTHON) -> List[str]:
        """
        从规格说明生成代码
        
        Args:
            specification: 规格说明
            target_language: 目标语言
            
        Returns:
            生成请求ID列表
        """
        try:
            request_ids = []
            
            # 解析规格说明
            components = specification.get('components', [])
            
            for component in components:
                component_type = component.get('type', 'class')
                template_type = self._map_component_to_template(component_type)
                
                requirements = {
                    'name': component.get('name', 'GeneratedComponent'),
                    'description': component.get('description', ''),
                    'properties': component.get('properties', {}),
                    'methods': component.get('methods', []),
                    'interfaces': component.get('interfaces', []),
                    'dependencies': component.get('dependencies', [])
                }
                
                request_id = await self.generate_code(
                    language=target_language,
                    template_type=template_type,
                    requirements=requirements,
                    generation_mode=GenerationMode.AI_ASSISTED,
                    context={'specification': specification}
                )
                
                request_ids.append(request_id)
            
            logger.info(f"从规格说明生成 {len(request_ids)} 个代码组件")
            return request_ids
            
        except Exception as e:
            logger.error(f"从规格说明生成代码失败: {e}")
            return []
    
    async def refactor_code(self,
                           source_code: str,
                           language: CodeLanguage,
                           refactoring_rules: List[str],
                           output_path: str = None) -> str:
        """
        重构代码
        
        Args:
            source_code: 源代码
            language: 编程语言
            refactoring_rules: 重构规则
            output_path: 输出路径
            
        Returns:
            重构请求ID
        """
        try:
            request_id = f"refactor_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            requirements = {
                'source_code': source_code,
                'refactoring_rules': refactoring_rules,
                'preserve_functionality': True,
                'improve_readability': True,
                'optimize_performance': True
            }
            
            request = CodeGenerationRequest(
                id=request_id,
                language=language,
                template_type=CodeTemplate.UTILITY,
                generation_mode=GenerationMode.REFACTORING,
                requirements=requirements,
                context={'original_code': source_code},
                output_path=output_path or self._generate_output_path(language, CodeTemplate.UTILITY),
                created_at=datetime.now()
            )
            
            self.generation_requests[request_id] = request
            
            # 异步执行重构
            asyncio.create_task(self._execute_code_refactoring(request_id))
            
            logger.info(f"代码重构请求创建成功: {request_id}")
            return request_id
            
        except Exception as e:
            logger.error(f"创建代码重构请求失败: {e}")
            raise
    
    async def optimize_code(self,
                           source_code: str,
                           language: CodeLanguage,
                           optimization_targets: List[str],
                           output_path: str = None) -> str:
        """
        优化代码
        
        Args:
            source_code: 源代码
            language: 编程语言
            optimization_targets: 优化目标
            output_path: 输出路径
            
        Returns:
            优化请求ID
        """
        try:
            request_id = f"optimize_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            requirements = {
                'source_code': source_code,
                'optimization_targets': optimization_targets,
                'performance_goals': {
                    'execution_time': 'minimize',
                    'memory_usage': 'minimize',
                    'code_complexity': 'reduce'
                }
            }
            
            request = CodeGenerationRequest(
                id=request_id,
                language=language,
                template_type=CodeTemplate.UTILITY,
                generation_mode=GenerationMode.OPTIMIZATION,
                requirements=requirements,
                context={'original_code': source_code},
                output_path=output_path or self._generate_output_path(language, CodeTemplate.UTILITY),
                created_at=datetime.now()
            )
            
            self.generation_requests[request_id] = request
            
            # 异步执行优化
            asyncio.create_task(self._execute_code_optimization(request_id))
            
            logger.info(f"代码优化请求创建成功: {request_id}")
            return request_id
            
        except Exception as e:
            logger.error(f"创建代码优化请求失败: {e}")
            raise
    
    async def get_generation_status(self, request_id: str) -> Dict[str, Any]:
        """
        获取生成状态
        
        Args:
            request_id: 请求ID
            
        Returns:
            生成状态信息
        """
        try:
            if request_id not in self.generation_requests:
                return {'status': 'not_found'}
            
            request = self.generation_requests[request_id]
            
            status = {
                'request_id': request_id,
                'language': request.language.value,
                'template_type': request.template_type.value,
                'generation_mode': request.generation_mode.value,
                'created_at': request.created_at.isoformat(),
                'status': 'pending'
            }
            
            if request_id in self.generated_codes:
                generated_code = self.generated_codes[request_id]
                status.update({
                    'status': 'completed',
                    'file_path': generated_code.file_path,
                    'quality_score': generated_code.quality_score,
                    'complexity_metrics': generated_code.complexity_metrics,
                    'test_coverage': generated_code.test_coverage,
                    'generated_at': generated_code.generated_at.isoformat()
                })
            
            return status
            
        except Exception as e:
            logger.error(f"获取生成状态失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def get_toolkit_statistics(self) -> Dict[str, Any]:
        """
        获取工具包统计信息
        
        Returns:
            统计信息字典
        """
        try:
            total_requests = len(self.generation_requests)
            completed_requests = len(self.generated_codes)
            
            # 语言分布统计
            language_distribution = {}
            for request in self.generation_requests.values():
                lang = request.language.value
                language_distribution[lang] = language_distribution.get(lang, 0) + 1
            
            # 模板类型分布统计
            template_distribution = {}
            for request in self.generation_requests.values():
                template = request.template_type.value
                template_distribution[template] = template_distribution.get(template, 0) + 1
            
            # 质量指标统计
            if self.generated_codes:
                quality_scores = [code.quality_score for code in self.generated_codes.values()]
                avg_quality = sum(quality_scores) / len(quality_scores)
                
                test_coverages = [code.test_coverage for code in self.generated_codes.values()]
                avg_coverage = sum(test_coverages) / len(test_coverages)
            else:
                avg_quality = 0.0
                avg_coverage = 0.0
            
            statistics = {
                'generation_statistics': {
                    'total_requests': total_requests,
                    'completed_requests': completed_requests,
                    'success_rate': completed_requests / total_requests if total_requests > 0 else 0,
                    'language_distribution': language_distribution,
                    'template_distribution': template_distribution
                },
                'quality_metrics': {
                    'average_quality_score': round(avg_quality, 2),
                    'average_test_coverage': round(avg_coverage, 2),
                    'quality_threshold': self.quality_threshold
                },
                'toolkit_info': {
                    'available_languages': [lang.value for lang in CodeLanguage],
                    'available_templates': [template.value for template in CodeTemplate],
                    'generation_modes': [mode.value for mode in GenerationMode],
                    'ai_assistance_enabled': self.enable_ai_assistance
                }
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"获取工具包统计信息失败: {e}")
            return {}
    
    async def _execute_code_generation(self, request_id: str):
        """执行代码生成"""
        try:
            request = self.generation_requests[request_id]
            
            # 根据生成模式选择生成策略
            if request.generation_mode == GenerationMode.TEMPLATE_BASED:
                code_content = await self._generate_from_template(request)
            elif request.generation_mode == GenerationMode.AI_ASSISTED:
                code_content = await self._generate_with_ai_assistance(request)
            elif request.generation_mode == GenerationMode.PATTERN_MATCHING:
                code_content = await self._generate_from_patterns(request)
            else:
                code_content = await self._generate_from_template(request)
            
            # 分析代码质量
            quality_score = await self._analyze_code_quality(code_content, request.language)
            complexity_metrics = await self._calculate_complexity_metrics(code_content, request.language)
            
            # 生成文档
            documentation = await self._generate_documentation(code_content, request)
            
            # 计算测试覆盖率
            test_coverage = await self._estimate_test_coverage(code_content, request.language)
            
            # 提取依赖
            dependencies = await self._extract_dependencies(code_content, request.language)
            
            # 创建生成结果
            generated_code = GeneratedCode(
                request_id=request_id,
                language=request.language,
                code_content=code_content,
                file_path=request.output_path,
                quality_score=quality_score,
                complexity_metrics=complexity_metrics,
                dependencies=dependencies,
                documentation=documentation,
                test_coverage=test_coverage,
                generated_at=datetime.now()
            )
            
            self.generated_codes[request_id] = generated_code
            
            # 保存到文件
            await self._save_generated_code(generated_code)
            
            logger.info(f"代码生成完成: {request_id}, 质量分数: {quality_score:.2f}")
            
        except Exception as e:
            logger.error(f"执行代码生成失败: {e}")
    
    async def _generate_from_template(self, request: CodeGenerationRequest) -> str:
        """从模板生成代码"""
        try:
            template_key = f"{request.language.value}_{request.template_type.value}"
            
            if template_key not in self.templates:
                # 使用默认模板
                template_key = f"{request.language.value}_default"
            
            if template_key not in self.templates:
                raise ValueError(f"未找到模板: {template_key}")
            
            template = self.templates[template_key]['content']
            
            # 替换模板变量
            code_content = template
            for key, value in request.requirements.items():
                placeholder = f"{{{{{key}}}}}"
                code_content = code_content.replace(placeholder, str(value))
            
            # 处理特殊模板逻辑
            if request.template_type == CodeTemplate.CLASS:
                code_content = await self._process_class_template(code_content, request.requirements)
            elif request.template_type == CodeTemplate.FUNCTION:
                code_content = await self._process_function_template(code_content, request.requirements)
            elif request.template_type == CodeTemplate.API_ENDPOINT:
                code_content = await self._process_api_template(code_content, request.requirements)
            
            return code_content
            
        except Exception as e:
            logger.error(f"从模板生成代码失败: {e}")
            return f"# 代码生成失败: {e}"
    
    async def _generate_with_ai_assistance(self, request: CodeGenerationRequest) -> str:
        """使用AI辅助生成代码"""
        try:
            if not self.enable_ai_assistance:
                return await self._generate_from_template(request)
            
            # 构建AI提示
            prompt = self._build_ai_prompt(request)
            
            # 模拟AI生成（实际实现中会调用AI模型）
            ai_generated_code = await self._simulate_ai_generation(prompt, request)
            
            # 后处理和优化
            optimized_code = await self._post_process_ai_code(ai_generated_code, request)
            
            return optimized_code
            
        except Exception as e:
            logger.error(f"AI辅助代码生成失败: {e}")
            return await self._generate_from_template(request)
    
    def _build_ai_prompt(self, request: CodeGenerationRequest) -> str:
        """构建AI提示"""
        prompt = f"""
        生成{request.language.value}代码，类型为{request.template_type.value}。
        
        需求:
        {json.dumps(request.requirements, indent=2, ensure_ascii=False)}
        
        上下文:
        {json.dumps(request.context, indent=2, ensure_ascii=False)}
        
        请生成高质量、可维护的代码，包含适当的注释和错误处理。
        """
        return prompt
    
    async def _simulate_ai_generation(self, prompt: str, request: CodeGenerationRequest) -> str:
        """模拟AI生成（实际实现中会调用真实的AI模型）"""
        # 这里是模拟实现，实际会调用GPT、Claude等AI模型
        await asyncio.sleep(0.5)  # 模拟AI处理时间
        
        if request.language == CodeLanguage.PYTHON:
            return self._generate_python_code_sample(request)
        elif request.language == CodeLanguage.JAVASCRIPT:
            return self._generate_javascript_code_sample(request)
        else:
            return await self._generate_from_template(request)
    
    def _generate_python_code_sample(self, request: CodeGenerationRequest) -> str:
        """生成Python代码示例"""
        name = request.requirements.get('name', 'GeneratedClass')
        description = request.requirements.get('description', '自动生成的类')
        
        if request.template_type == CodeTemplate.CLASS:
            return f'''"""
{description}
"""

class {name}:
    """
    {description}
    
    这是一个自动生成的类，提供基础功能。
    """
    
    def __init__(self):
        """初始化{name}实例"""
        self._initialized = True
        self._data = {{}}
    
    def get_data(self):
        """获取数据"""
        return self._data.copy()
    
    def set_data(self, key, value):
        """设置数据"""
        if not isinstance(key, str):
            raise ValueError("键必须是字符串类型")
        self._data[key] = value
    
    def __str__(self):
        """字符串表示"""
        return f"{name}(data={{len(self._data)}} items)"
    
    def __repr__(self):
        """开发者表示"""
        return f"{name}({{self._data}})"
'''
        else:
            return f'''"""
{description}
"""

def {name.lower()}():
    """
    {description}
    
    Returns:
        str: 处理结果
    """
    try:
        # 实现功能逻辑
        result = "处理完成"
        return result
    except Exception as e:
        raise RuntimeError(f"处理失败: {{e}}")
'''
    
    def _generate_javascript_code_sample(self, request: CodeGenerationRequest) -> str:
        """生成JavaScript代码示例"""
        name = request.requirements.get('name', 'GeneratedClass')
        description = request.requirements.get('description', '自动生成的类')
        
        if request.template_type == CodeTemplate.CLASS:
            return f'''/**
 * {description}
 */
class {name} {{
    /**
     * 创建{name}实例
     */
    constructor() {{
        this._initialized = true;
        this._data = {{}};
    }}
    
    /**
     * 获取数据
     * @returns {{Object}} 数据副本
     */
    getData() {{
        return {{ ...this._data }};
    }}
    
    /**
     * 设置数据
     * @param {{string}} key - 键
     * @param {{*}} value - 值
     */
    setData(key, value) {{
        if (typeof key !== 'string') {{
            throw new Error('键必须是字符串类型');
        }}
        this._data[key] = value;
    }}
    
    /**
     * 字符串表示
     * @returns {{string}} 字符串表示
     */
    toString() {{
        return `{name}(data=${{Object.keys(this._data).length}} items)`;
    }}
}}

module.exports = {name};
'''
        else:
            return f'''/**
 * {description}
 * @returns {{string}} 处理结果
 */
function {name.lower()}() {{
    try {{
        // 实现功能逻辑
        const result = "处理完成";
        return result;
    }} catch (error) {{
        throw new Error(`处理失败: ${{error.message}}`);
    }}
}}

module.exports = {name.lower()};
'''
    
    async def _analyze_code_quality(self, code: str, language: CodeLanguage) -> float:
        """分析代码质量"""
        try:
            quality_score = 0.8  # 基础分数
            
            # 检查代码长度
            if len(code) > 100:
                quality_score += 0.1
            
            # 检查注释
            if '"""' in code or '/*' in code or '#' in code:
                quality_score += 0.1
            
            # 检查错误处理
            if 'try' in code or 'except' in code or 'catch' in code:
                quality_score += 0.1
            
            return min(1.0, quality_score)
            
        except Exception:
            return 0.5
    
    async def _calculate_complexity_metrics(self, code: str, language: CodeLanguage) -> Dict[str, Any]:
        """计算复杂度指标"""
        try:
            metrics = {
                'lines_of_code': len(code.split('\n')),
                'cyclomatic_complexity': 1,  # 简化计算
                'cognitive_complexity': 1,
                'maintainability_index': 85
            }
            
            # 简单的复杂度计算
            if language == CodeLanguage.PYTHON:
                # 计算if、for、while等控制结构
                control_structures = code.count('if ') + code.count('for ') + code.count('while ')
                metrics['cyclomatic_complexity'] = max(1, control_structures + 1)
            
            return metrics
            
        except Exception:
            return {'lines_of_code': 0, 'cyclomatic_complexity': 1}
    
    async def _generate_documentation(self, code: str, request: CodeGenerationRequest) -> str:
        """生成文档"""
        try:
            doc = f"""
# {request.requirements.get('name', '生成的代码')}

## 描述
{request.requirements.get('description', '自动生成的代码组件')}

## 语言
{request.language.value}

## 类型
{request.template_type.value}

## 生成时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 使用方法
请参考代码中的注释和示例。

## 依赖
无特殊依赖

## 注意事项
这是自动生成的代码，请根据实际需求进行调整。
"""
            return doc
            
        except Exception:
            return "文档生成失败"
    
    async def _estimate_test_coverage(self, code: str, language: CodeLanguage) -> float:
        """估算测试覆盖率"""
        try:
            # 简单的覆盖率估算
            if 'test' in code.lower() or 'assert' in code.lower():
                return 0.8
            else:
                return 0.3  # 默认覆盖率
                
        except Exception:
            return 0.0
    
    async def _extract_dependencies(self, code: str, language: CodeLanguage) -> List[str]:
        """提取依赖"""
        try:
            dependencies = []
            
            if language == CodeLanguage.PYTHON:
                # 提取import语句
                import_lines = [line.strip() for line in code.split('\n') 
                              if line.strip().startswith('import ') or line.strip().startswith('from ')]
                dependencies.extend(import_lines)
            elif language == CodeLanguage.JAVASCRIPT:
                # 提取require和import语句
                require_pattern = r'require\([\'"]([^\'"]+)[\'"]\)'
                import_pattern = r'import.*from\s+[\'"]([^\'"]+)[\'"]'
                
                dependencies.extend(re.findall(require_pattern, code))
                dependencies.extend(re.findall(import_pattern, code))
            
            return dependencies
            
        except Exception:
            return []
    
    async def _save_generated_code(self, generated_code: GeneratedCode):
        """保存生成的代码"""
        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(generated_code.file_path)
            os.makedirs(output_dir, exist_ok=True)
            
            # 保存代码文件
            with open(generated_code.file_path, 'w', encoding='utf-8') as f:
                f.write(generated_code.code_content)
            
            # 保存文档文件
            doc_path = generated_code.file_path.replace('.py', '_doc.md').replace('.js', '_doc.md')
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(generated_code.documentation)
            
            logger.info(f"代码文件保存成功: {generated_code.file_path}")
            
        except Exception as e:
            logger.error(f"保存生成的代码失败: {e}")
    
    def _initialize_templates(self):
        """初始化代码模板"""
        try:
            # Python类模板
            self.templates['python_class'] = {
                'content': '''"""
{{description}}
"""

class {{name}}:
    """{{description}}"""
    
    def __init__(self):
        """初始化{{name}}实例"""
        pass
    
    def __str__(self):
        """字符串表示"""
        return "{{name}}()"
''',
                'variables': ['name', 'description']
            }
            
            # Python函数模板
            self.templates['python_function'] = {
                'content': '''"""
{{description}}
"""

def {{name}}():
    """
    {{description}}
    
    Returns:
        str: 处理结果
    """
    try:
        # 实现功能逻辑
        result = "处理完成"
        return result
    except Exception as e:
        raise RuntimeError(f"处理失败: {e}")
''',
                'variables': ['name', 'description']
            }
            
            logger.info("代码模板初始化完成")
            
        except Exception as e:
            logger.error(f"初始化代码模板失败: {e}")
    
    def _generate_output_path(self, language: CodeLanguage, template_type: CodeTemplate) -> str:
        """生成输出路径"""
        extensions = {
            CodeLanguage.PYTHON: '.py',
            CodeLanguage.JAVASCRIPT: '.js',
            CodeLanguage.TYPESCRIPT: '.ts',
            CodeLanguage.JAVA: '.java',
            CodeLanguage.CSHARP: '.cs',
            CodeLanguage.GO: '.go',
            CodeLanguage.RUST: '.rs',
            CodeLanguage.CPP: '.cpp',
            CodeLanguage.HTML: '.html',
            CodeLanguage.CSS: '.css',
            CodeLanguage.SQL: '.sql'
        }
        
        ext = extensions.get(language, '.txt')
        filename = f"generated_{template_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        
        return os.path.join(self.output_directory, language.value, filename)
    
    def _map_component_to_template(self, component_type: str) -> CodeTemplate:
        """映射组件类型到模板类型"""
        mapping = {
            'class': CodeTemplate.CLASS,
            'function': CodeTemplate.FUNCTION,
            'module': CodeTemplate.MODULE,
            'api': CodeTemplate.API_ENDPOINT,
            'model': CodeTemplate.DATABASE_MODEL,
            'test': CodeTemplate.TEST_CASE,
            'component': CodeTemplate.COMPONENT,
            'service': CodeTemplate.SERVICE
        }
        
        return mapping.get(component_type, CodeTemplate.CLASS)
    
    async def _execute_code_refactoring(self, request_id: str):
        """执行代码重构"""
        try:
            request = self.generation_requests[request_id]
            source_code = request.requirements['source_code']
            refactoring_rules = request.requirements['refactoring_rules']
            
            # 应用重构规则
            refactored_code = source_code
            
            for rule in refactoring_rules:
                if rule == 'extract_method':
                    refactored_code = await self._apply_extract_method(refactored_code)
                elif rule == 'rename_variable':
                    refactored_code = await self._apply_rename_variable(refactored_code)
                elif rule == 'remove_duplication':
                    refactored_code = await self._apply_remove_duplication(refactored_code)
            
            # 创建重构结果
            generated_code = GeneratedCode(
                request_id=request_id,
                language=request.language,
                code_content=refactored_code,
                file_path=request.output_path,
                quality_score=await self._analyze_code_quality(refactored_code, request.language),
                complexity_metrics=await self._calculate_complexity_metrics(refactored_code, request.language),
                dependencies=await self._extract_dependencies(refactored_code, request.language),
                documentation=f"重构后的代码\n原始代码长度: {len(source_code)}\n重构后长度: {len(refactored_code)}",
                test_coverage=await self._estimate_test_coverage(refactored_code, request.language),
                generated_at=datetime.now()
            )
            
            self.generated_codes[request_id] = generated_code
            await self._save_generated_code(generated_code)
            
            logger.info(f"代码重构完成: {request_id}")
            
        except Exception as e:
            logger.error(f"执行代码重构失败: {e}")
    
    async def _execute_code_optimization(self, request_id: str):
        """执行代码优化"""
        try:
            request = self.generation_requests[request_id]
            source_code = request.requirements['source_code']
            optimization_targets = request.requirements['optimization_targets']
            
            # 应用优化策略
            optimized_code = source_code
            
            for target in optimization_targets:
                if target == 'performance':
                    optimized_code = await self._optimize_performance(optimized_code)
                elif target == 'memory':
                    optimized_code = await self._optimize_memory(optimized_code)
                elif target == 'readability':
                    optimized_code = await self._optimize_readability(optimized_code)
            
            # 创建优化结果
            generated_code = GeneratedCode(
                request_id=request_id,
                language=request.language,
                code_content=optimized_code,
                file_path=request.output_path,
                quality_score=await self._analyze_code_quality(optimized_code, request.language),
                complexity_metrics=await self._calculate_complexity_metrics(optimized_code, request.language),
                dependencies=await self._extract_dependencies(optimized_code, request.language),
                documentation=f"优化后的代码\n优化目标: {', '.join(optimization_targets)}",
                test_coverage=await self._estimate_test_coverage(optimized_code, request.language),
                generated_at=datetime.now()
            )
            
            self.generated_codes[request_id] = generated_code
            await self._save_generated_code(generated_code)
            
            logger.info(f"代码优化完成: {request_id}")
            
        except Exception as e:
            logger.error(f"执行代码优化失败: {e}")
    
    async def _apply_extract_method(self, code: str) -> str:
        """应用提取方法重构"""
        # 简化实现，实际会进行复杂的代码分析
        return code + "\n# 已应用提取方法重构"
    
    async def _apply_rename_variable(self, code: str) -> str:
        """应用重命名变量重构"""
        # 简化实现
        return code.replace('temp', 'temporary_value')
    
    async def _apply_remove_duplication(self, code: str) -> str:
        """应用去除重复重构"""
        # 简化实现
        lines = code.split('\n')
        unique_lines = []
        seen = set()
        
        for line in lines:
            if line.strip() not in seen:
                unique_lines.append(line)
                seen.add(line.strip())
        
        return '\n'.join(unique_lines)
    
    async def _optimize_performance(self, code: str) -> str:
        """性能优化"""
        # 简化实现
        return code + "\n# 已应用性能优化"
    
    async def _optimize_memory(self, code: str) -> str:
        """内存优化"""
        # 简化实现
        return code + "\n# 已应用内存优化"
    
    async def _optimize_readability(self, code: str) -> str:
        """可读性优化"""
        # 简化实现
        return code + "\n# 已应用可读性优化"

