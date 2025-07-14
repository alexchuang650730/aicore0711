"""
PowerAutomation 4.0 AG-UI组件生成器

基于智能体需求和用户上下文，动态生成符合AG-UI协议的UI组件。
"""

import asyncio
import uuid
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from .ag_ui_protocol_adapter import AGUIComponent, AGUIComponentType


class GenerationStrategy(Enum):
    """生成策略"""
    TEMPLATE_BASED = "template_based"
    AI_GENERATED = "ai_generated"
    RULE_BASED = "rule_based"
    HYBRID = "hybrid"


class ComponentComplexity(Enum):
    """组件复杂度"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    ADVANCED = "advanced"


@dataclass
class GenerationContext:
    """生成上下文"""
    user_id: str
    session_id: str
    agent_id: str
    requirements: Dict[str, Any]
    constraints: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    existing_components: List[AGUIComponent] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentTemplate:
    """组件模板"""
    template_id: str
    name: str
    component_type: str
    complexity: ComponentComplexity
    template_data: Dict[str, Any]
    variables: List[str] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationRule:
    """生成规则"""
    rule_id: str
    name: str
    condition: str
    action: str
    priority: int = 0
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class AGUIComponentGenerator:
    """AG-UI组件生成器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 组件模板库
        self.component_templates: Dict[str, ComponentTemplate] = {}
        
        # 生成规则
        self.generation_rules: Dict[str, GenerationRule] = {}
        
        # AI生成器配置
        self.ai_config = self.config.get("ai_generator", {})
        
        # 缓存
        self.generation_cache: Dict[str, AGUIComponent] = {}
        self.cache_ttl = self.config.get("cache_ttl", 300)  # 5分钟
        
        # 统计信息
        self.stats = {
            "total_generated": 0,
            "generation_by_strategy": {},
            "generation_by_type": {},
            "cache_hits": 0,
            "cache_misses": 0,
            "generation_errors": 0,
            "avg_generation_time": 0.0
        }
        
        # 运行状态
        self.is_running = False
    
    async def start(self):
        """启动组件生成器"""
        if self.is_running:
            return
        
        self.logger.info("启动AG-UI组件生成器...")
        
        # 加载默认模板
        await self._load_default_templates()
        
        # 加载默认规则
        await self._load_default_rules()
        
        self.is_running = True
        self.logger.info("AG-UI组件生成器启动完成")
    
    async def stop(self):
        """停止组件生成器"""
        if not self.is_running:
            return
        
        self.logger.info("停止AG-UI组件生成器...")
        
        # 清理缓存
        self.generation_cache.clear()
        
        self.is_running = False
        self.logger.info("AG-UI组件生成器已停止")
    
    async def generate_component(
        self,
        context: GenerationContext,
        strategy: str = "hybrid"
    ) -> Optional[AGUIComponent]:
        """生成组件"""
        start_time = datetime.now()
        
        try:
            # 检查缓存
            cache_key = self._generate_cache_key(context)
            cached_component = await self._get_from_cache(cache_key)
            if cached_component:
                self.stats["cache_hits"] += 1
                return cached_component
            
            self.stats["cache_misses"] += 1
            
            # 根据策略生成组件
            component = None
            if strategy == GenerationStrategy.TEMPLATE_BASED.value:
                component = await self._generate_from_template(context)
            elif strategy == GenerationStrategy.AI_GENERATED.value:
                component = await self._generate_with_ai(context)
            elif strategy == GenerationStrategy.RULE_BASED.value:
                component = await self._generate_with_rules(context)
            elif strategy == GenerationStrategy.HYBRID.value:
                component = await self._generate_hybrid(context)
            else:
                raise ValueError(f"不支持的生成策略: {strategy}")
            
            if component:
                # 应用后处理
                component = await self._post_process_component(component, context)
                
                # 缓存结果
                await self._cache_component(cache_key, component)
                
                # 更新统计
                self.stats["total_generated"] += 1
                if strategy not in self.stats["generation_by_strategy"]:
                    self.stats["generation_by_strategy"][strategy] = 0
                self.stats["generation_by_strategy"][strategy] += 1
                
                if component.type not in self.stats["generation_by_type"]:
                    self.stats["generation_by_type"][component.type] = 0
                self.stats["generation_by_type"][component.type] += 1
                
                # 更新平均生成时间
                generation_time = (datetime.now() - start_time).total_seconds()
                current_avg = self.stats["avg_generation_time"]
                total_generated = self.stats["total_generated"]
                self.stats["avg_generation_time"] = (
                    (current_avg * (total_generated - 1) + generation_time) / total_generated
                )
                
                self.logger.info(f"生成组件成功: {component.id}, 策略: {strategy}")
                return component
            
            return None
            
        except Exception as e:
            self.stats["generation_errors"] += 1
            self.logger.error(f"组件生成失败: {e}")
            return None
    
    async def generate_form(
        self,
        context: GenerationContext,
        fields: List[Dict[str, Any]]
    ) -> Optional[AGUIComponent]:
        """生成表单组件"""
        try:
            form_id = str(uuid.uuid4())
            form_component = AGUIComponent(
                id=form_id,
                type="form",
                properties={
                    "title": context.requirements.get("title", "表单"),
                    "method": context.requirements.get("method", "POST"),
                    "action": context.requirements.get("action", ""),
                    "validation": context.requirements.get("validation", True)
                },
                children=[],
                events={
                    "submit": f"handle_form_submit_{form_id}",
                    "reset": f"handle_form_reset_{form_id}"
                },
                metadata={
                    "generated_at": datetime.now().isoformat(),
                    "generator": "form_generator",
                    "context_id": context.session_id
                }
            )
            
            # 生成字段组件
            for field_config in fields:
                field_component = await self._generate_form_field(field_config, context)
                if field_component:
                    form_component.children.append(field_component)
            
            # 添加提交按钮
            submit_button = AGUIComponent(
                id=str(uuid.uuid4()),
                type="button",
                properties={
                    "text": context.requirements.get("submit_text", "提交"),
                    "variant": "primary",
                    "type": "submit"
                },
                events={"click": f"submit_form_{form_id}"}
            )
            form_component.children.append(submit_button)
            
            return form_component
            
        except Exception as e:
            self.logger.error(f"表单生成失败: {e}")
            return None
    
    async def generate_layout(
        self,
        context: GenerationContext,
        layout_type: str = "grid"
    ) -> Optional[AGUIComponent]:
        """生成布局组件"""
        try:
            layout_id = str(uuid.uuid4())
            
            if layout_type == "grid":
                return await self._generate_grid_layout(context, layout_id)
            elif layout_type == "flex":
                return await self._generate_flex_layout(context, layout_id)
            elif layout_type == "stack":
                return await self._generate_stack_layout(context, layout_id)
            else:
                raise ValueError(f"不支持的布局类型: {layout_type}")
                
        except Exception as e:
            self.logger.error(f"布局生成失败: {e}")
            return None
    
    async def generate_data_visualization(
        self,
        context: GenerationContext,
        data: Dict[str, Any],
        chart_type: str = "auto"
    ) -> Optional[AGUIComponent]:
        """生成数据可视化组件"""
        try:
            # 自动选择图表类型
            if chart_type == "auto":
                chart_type = await self._auto_select_chart_type(data)
            
            chart_id = str(uuid.uuid4())
            chart_component = AGUIComponent(
                id=chart_id,
                type="chart",
                properties={
                    "chart_type": chart_type,
                    "data": data,
                    "title": context.requirements.get("title", "数据图表"),
                    "responsive": True,
                    "interactive": context.requirements.get("interactive", True)
                },
                events={
                    "data_point_click": f"handle_chart_click_{chart_id}",
                    "zoom": f"handle_chart_zoom_{chart_id}"
                },
                metadata={
                    "generated_at": datetime.now().isoformat(),
                    "generator": "chart_generator",
                    "data_source": context.requirements.get("data_source", "unknown")
                }
            )
            
            return chart_component
            
        except Exception as e:
            self.logger.error(f"数据可视化生成失败: {e}")
            return None
    
    async def register_template(self, template: ComponentTemplate) -> bool:
        """注册组件模板"""
        try:
            self.component_templates[template.template_id] = template
            self.logger.info(f"注册组件模板: {template.template_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"注册模板失败: {e}")
            return False
    
    async def register_generation_rule(self, rule: GenerationRule) -> bool:
        """注册生成规则"""
        try:
            self.generation_rules[rule.rule_id] = rule
            self.logger.info(f"注册生成规则: {rule.rule_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"注册规则失败: {e}")
            return False
    
    async def _generate_from_template(
        self,
        context: GenerationContext
    ) -> Optional[AGUIComponent]:
        """基于模板生成组件"""
        # 查找匹配的模板
        template = await self._find_matching_template(context)
        if not template:
            return None
        
        # 应用模板
        component_data = template.template_data.copy()
        
        # 替换变量
        for variable in template.variables:
            value = context.requirements.get(variable)
            if value is not None:
                component_data = await self._replace_template_variable(
                    component_data, variable, value
                )
        
        # 创建组件
        return AGUIComponent(
            id=str(uuid.uuid4()),
            type=component_data.get("type", "div"),
            properties=component_data.get("properties", {}),
            children=[],
            events=component_data.get("events", {}),
            styles=component_data.get("styles", {}),
            metadata={
                "generated_at": datetime.now().isoformat(),
                "generator": "template_based",
                "template_id": template.template_id
            }
        )
    
    async def _generate_with_ai(
        self,
        context: GenerationContext
    ) -> Optional[AGUIComponent]:
        """使用AI生成组件"""
        # 这里应该调用AI服务生成组件
        # 简化实现，返回基础组件
        
        component_type = context.requirements.get("type", "div")
        
        return AGUIComponent(
            id=str(uuid.uuid4()),
            type=component_type,
            properties={
                "ai_generated": True,
                "prompt": context.requirements.get("prompt", ""),
                "confidence": 0.8
            },
            children=[],
            events={},
            metadata={
                "generated_at": datetime.now().isoformat(),
                "generator": "ai_generated",
                "model": self.ai_config.get("model", "gpt-4")
            }
        )
    
    async def _generate_with_rules(
        self,
        context: GenerationContext
    ) -> Optional[AGUIComponent]:
        """基于规则生成组件"""
        # 应用生成规则
        applicable_rules = await self._find_applicable_rules(context)
        
        if not applicable_rules:
            return None
        
        # 按优先级排序
        applicable_rules.sort(key=lambda r: r.priority, reverse=True)
        
        # 应用第一个匹配的规则
        rule = applicable_rules[0]
        
        # 执行规则动作
        component_config = await self._execute_generation_rule(rule, context)
        
        if component_config:
            return AGUIComponent(
                id=str(uuid.uuid4()),
                type=component_config.get("type", "div"),
                properties=component_config.get("properties", {}),
                children=[],
                events=component_config.get("events", {}),
                metadata={
                    "generated_at": datetime.now().isoformat(),
                    "generator": "rule_based",
                    "rule_id": rule.rule_id
                }
            )
        
        return None
    
    async def _generate_hybrid(
        self,
        context: GenerationContext
    ) -> Optional[AGUIComponent]:
        """混合策略生成组件"""
        # 尝试模板生成
        component = await self._generate_from_template(context)
        if component:
            return component
        
        # 尝试规则生成
        component = await self._generate_with_rules(context)
        if component:
            return component
        
        # 最后尝试AI生成
        return await self._generate_with_ai(context)
    
    async def _generate_form_field(
        self,
        field_config: Dict[str, Any],
        context: GenerationContext
    ) -> Optional[AGUIComponent]:
        """生成表单字段"""
        field_type = field_config.get("type", "input")
        field_id = str(uuid.uuid4())
        
        if field_type == "input":
            return AGUIComponent(
                id=field_id,
                type="input",
                properties={
                    "name": field_config.get("name", ""),
                    "label": field_config.get("label", ""),
                    "type": field_config.get("input_type", "text"),
                    "placeholder": field_config.get("placeholder", ""),
                    "required": field_config.get("required", False),
                    "validation": field_config.get("validation", {})
                },
                events={
                    "change": f"handle_field_change_{field_id}",
                    "blur": f"handle_field_blur_{field_id}"
                }
            )
        elif field_type == "select":
            return AGUIComponent(
                id=field_id,
                type="select",
                properties={
                    "name": field_config.get("name", ""),
                    "label": field_config.get("label", ""),
                    "options": field_config.get("options", []),
                    "multiple": field_config.get("multiple", False),
                    "required": field_config.get("required", False)
                },
                events={"change": f"handle_select_change_{field_id}"}
            )
        elif field_type == "textarea":
            return AGUIComponent(
                id=field_id,
                type="textarea",
                properties={
                    "name": field_config.get("name", ""),
                    "label": field_config.get("label", ""),
                    "placeholder": field_config.get("placeholder", ""),
                    "rows": field_config.get("rows", 4),
                    "required": field_config.get("required", False)
                },
                events={"change": f"handle_textarea_change_{field_id}"}
            )
        
        return None
    
    async def _generate_grid_layout(
        self,
        context: GenerationContext,
        layout_id: str
    ) -> AGUIComponent:
        """生成网格布局"""
        return AGUIComponent(
            id=layout_id,
            type="layout",
            properties={
                "layout_type": "grid",
                "columns": context.requirements.get("columns", 12),
                "gap": context.requirements.get("gap", "16px"),
                "responsive": True
            },
            children=[],
            styles={
                "display": "grid",
                "grid-template-columns": f"repeat({context.requirements.get('columns', 12)}, 1fr)",
                "gap": context.requirements.get("gap", "16px")
            },
            metadata={
                "generated_at": datetime.now().isoformat(),
                "generator": "layout_generator",
                "layout_type": "grid"
            }
        )
    
    async def _generate_flex_layout(
        self,
        context: GenerationContext,
        layout_id: str
    ) -> AGUIComponent:
        """生成弹性布局"""
        return AGUIComponent(
            id=layout_id,
            type="layout",
            properties={
                "layout_type": "flex",
                "direction": context.requirements.get("direction", "row"),
                "justify": context.requirements.get("justify", "flex-start"),
                "align": context.requirements.get("align", "stretch"),
                "wrap": context.requirements.get("wrap", "nowrap")
            },
            children=[],
            styles={
                "display": "flex",
                "flex-direction": context.requirements.get("direction", "row"),
                "justify-content": context.requirements.get("justify", "flex-start"),
                "align-items": context.requirements.get("align", "stretch"),
                "flex-wrap": context.requirements.get("wrap", "nowrap")
            },
            metadata={
                "generated_at": datetime.now().isoformat(),
                "generator": "layout_generator",
                "layout_type": "flex"
            }
        )
    
    async def _generate_stack_layout(
        self,
        context: GenerationContext,
        layout_id: str
    ) -> AGUIComponent:
        """生成堆叠布局"""
        return AGUIComponent(
            id=layout_id,
            type="layout",
            properties={
                "layout_type": "stack",
                "spacing": context.requirements.get("spacing", "16px"),
                "direction": context.requirements.get("direction", "vertical")
            },
            children=[],
            styles={
                "display": "flex",
                "flex-direction": "column" if context.requirements.get("direction", "vertical") == "vertical" else "row",
                "gap": context.requirements.get("spacing", "16px")
            },
            metadata={
                "generated_at": datetime.now().isoformat(),
                "generator": "layout_generator",
                "layout_type": "stack"
            }
        )
    
    async def _auto_select_chart_type(self, data: Dict[str, Any]) -> str:
        """自动选择图表类型"""
        # 简化的图表类型选择逻辑
        if "categories" in data and "values" in data:
            if len(data["categories"]) <= 10:
                return "bar"
            else:
                return "line"
        elif "x" in data and "y" in data:
            return "scatter"
        elif "labels" in data and "values" in data:
            return "pie"
        else:
            return "bar"
    
    async def _find_matching_template(
        self,
        context: GenerationContext
    ) -> Optional[ComponentTemplate]:
        """查找匹配的模板"""
        required_type = context.requirements.get("type")
        if not required_type:
            return None
        
        # 查找类型匹配的模板
        matching_templates = [
            template for template in self.component_templates.values()
            if template.component_type == required_type
        ]
        
        if not matching_templates:
            return None
        
        # 返回第一个匹配的模板（可以增加更复杂的匹配逻辑）
        return matching_templates[0]
    
    async def _find_applicable_rules(
        self,
        context: GenerationContext
    ) -> List[GenerationRule]:
        """查找适用的规则"""
        applicable_rules = []
        
        for rule in self.generation_rules.values():
            if not rule.enabled:
                continue
            
            # 简化的条件评估
            if await self._evaluate_rule_condition(rule, context):
                applicable_rules.append(rule)
        
        return applicable_rules
    
    async def _evaluate_rule_condition(
        self,
        rule: GenerationRule,
        context: GenerationContext
    ) -> bool:
        """评估规则条件"""
        # 简化实现
        condition = rule.condition
        
        if "type" in condition:
            required_type = context.requirements.get("type")
            return required_type and required_type in condition
        
        return True
    
    async def _execute_generation_rule(
        self,
        rule: GenerationRule,
        context: GenerationContext
    ) -> Optional[Dict[str, Any]]:
        """执行生成规则"""
        # 简化实现
        action = rule.action
        
        if action == "create_button":
            return {
                "type": "button",
                "properties": {
                    "text": context.requirements.get("text", "按钮"),
                    "variant": context.requirements.get("variant", "primary")
                },
                "events": {"click": "handle_button_click"}
            }
        elif action == "create_input":
            return {
                "type": "input",
                "properties": {
                    "placeholder": context.requirements.get("placeholder", ""),
                    "type": context.requirements.get("input_type", "text")
                },
                "events": {"change": "handle_input_change"}
            }
        
        return None
    
    async def _replace_template_variable(
        self,
        template_data: Dict[str, Any],
        variable: str,
        value: Any
    ) -> Dict[str, Any]:
        """替换模板变量"""
        # 递归替换模板中的变量
        if isinstance(template_data, dict):
            result = {}
            for key, val in template_data.items():
                if isinstance(val, str) and f"{{{variable}}}" in val:
                    result[key] = val.replace(f"{{{variable}}}", str(value))
                else:
                    result[key] = await self._replace_template_variable(val, variable, value)
            return result
        elif isinstance(template_data, list):
            return [
                await self._replace_template_variable(item, variable, value)
                for item in template_data
            ]
        else:
            return template_data
    
    async def _post_process_component(
        self,
        component: AGUIComponent,
        context: GenerationContext
    ) -> AGUIComponent:
        """后处理组件"""
        # 添加通用属性
        component.metadata.update({
            "session_id": context.session_id,
            "user_id": context.user_id,
            "agent_id": context.agent_id
        })
        
        # 应用约束
        constraints = context.constraints
        if "max_width" in constraints:
            component.styles["max-width"] = constraints["max_width"]
        if "theme" in constraints:
            component.properties["theme"] = constraints["theme"]
        
        return component
    
    def _generate_cache_key(self, context: GenerationContext) -> str:
        """生成缓存键"""
        key_data = {
            "requirements": context.requirements,
            "constraints": context.constraints,
            "preferences": context.preferences
        }
        return f"component_{hash(json.dumps(key_data, sort_keys=True))}"
    
    async def _get_from_cache(self, cache_key: str) -> Optional[AGUIComponent]:
        """从缓存获取组件"""
        return self.generation_cache.get(cache_key)
    
    async def _cache_component(self, cache_key: str, component: AGUIComponent):
        """缓存组件"""
        self.generation_cache[cache_key] = component
        
        # 简化的TTL实现（实际应该使用更复杂的缓存机制）
        asyncio.create_task(self._expire_cache_entry(cache_key))
    
    async def _expire_cache_entry(self, cache_key: str):
        """过期缓存条目"""
        await asyncio.sleep(self.cache_ttl)
        self.generation_cache.pop(cache_key, None)
    
    async def _load_default_templates(self):
        """加载默认模板"""
        default_templates = [
            ComponentTemplate(
                template_id="button_template",
                name="按钮模板",
                component_type="button",
                complexity=ComponentComplexity.SIMPLE,
                template_data={
                    "type": "button",
                    "properties": {
                        "text": "{text}",
                        "variant": "{variant}",
                        "disabled": False
                    },
                    "events": {"click": "handle_button_click"}
                },
                variables=["text", "variant"]
            ),
            ComponentTemplate(
                template_id="input_template",
                name="输入框模板",
                component_type="input",
                complexity=ComponentComplexity.SIMPLE,
                template_data={
                    "type": "input",
                    "properties": {
                        "placeholder": "{placeholder}",
                        "type": "{input_type}",
                        "required": False
                    },
                    "events": {"change": "handle_input_change"}
                },
                variables=["placeholder", "input_type"]
            )
        ]
        
        for template in default_templates:
            await self.register_template(template)
    
    async def _load_default_rules(self):
        """加载默认规则"""
        default_rules = [
            GenerationRule(
                rule_id="button_rule",
                name="按钮生成规则",
                condition="type:button",
                action="create_button",
                priority=1
            ),
            GenerationRule(
                rule_id="input_rule",
                name="输入框生成规则",
                condition="type:input",
                action="create_input",
                priority=1
            )
        ]
        
        for rule in default_rules:
            await self.register_generation_rule(rule)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "is_running": self.is_running,
            "templates_count": len(self.component_templates),
            "rules_count": len(self.generation_rules),
            "cache_size": len(self.generation_cache),
            "statistics": self.stats.copy()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "component": "ag_ui_component_generator",
            "status": "healthy" if self.is_running else "unhealthy",
            "statistics": await self.get_statistics()
        }

