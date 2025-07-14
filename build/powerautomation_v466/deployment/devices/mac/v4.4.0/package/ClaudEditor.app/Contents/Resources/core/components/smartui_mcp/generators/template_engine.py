#!/usr/bin/env python3
"""
模板引擎

负责模板解析、变量替换、条件渲染等功能
"""

import re
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TemplateNodeType(Enum):
    """模板节点类型"""
    TEXT = "text"
    VARIABLE = "variable"
    CONDITION = "condition"
    LOOP = "loop"
    PARTIAL = "partial"

@dataclass
class TemplateNode:
    """模板节点"""
    type: TemplateNodeType
    content: str
    children: List['TemplateNode'] = None
    condition: Optional[str] = None
    variable: Optional[str] = None

class TemplateEngine:
    """模板引擎"""
    
    def __init__(self):
        # 变量模式: {{variable}}
        self.variable_pattern = re.compile(r'\{\{([^}]+)\}\}')
        
        # 条件模式: {{#if condition}} ... {{/if}}
        self.condition_pattern = re.compile(r'\{\{#if\s+([^}]+)\}\}(.*?)\{\{/if\}\}', re.DOTALL)
        
        # 循环模式: {{#each items}} ... {{/each}}
        self.loop_pattern = re.compile(r'\{\{#each\s+([^}]+)\}\}(.*?)\{\{/each\}\}', re.DOTALL)
        
        # 部分模板模式: {{> partial_name}}
        self.partial_pattern = re.compile(r'\{\{>\s*([^}]+)\}\}')
        
        # 辅助函数
        self.helpers = {
            'eq': self._helper_eq,
            'ne': self._helper_ne,
            'gt': self._helper_gt,
            'lt': self._helper_lt,
            'and': self._helper_and,
            'or': self._helper_or,
            'not': self._helper_not,
            'if': self._helper_if,
            'unless': self._helper_unless
        }
        
        # 部分模板缓存
        self.partials: Dict[str, str] = {}
    
    def register_partial(self, name: str, template: str) -> None:
        """注册部分模板"""
        self.partials[name] = template
    
    def register_helper(self, name: str, func) -> None:
        """注册辅助函数"""
        self.helpers[name] = func
    
    def render(self, template: Union[str, Dict[str, Any]], context: Dict[str, Any]) -> str:
        """渲染模板"""
        if isinstance(template, dict):
            return self._render_object_template(template, context)
        else:
            return self._render_string_template(template, context)
    
    def _render_string_template(self, template: str, context: Dict[str, Any]) -> str:
        """渲染字符串模板"""
        # 处理部分模板
        template = self._process_partials(template, context)
        
        # 处理条件语句
        template = self._process_conditions(template, context)
        
        # 处理循环
        template = self._process_loops(template, context)
        
        # 处理变量替换
        template = self._process_variables(template, context)
        
        return template
    
    def _render_object_template(self, template: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """渲染对象模板"""
        result = {}
        
        for key, value in template.items():
            if isinstance(value, str):
                result[key] = self._render_string_template(value, context)
            elif isinstance(value, dict):
                result[key] = self._render_object_template(value, context)
            elif isinstance(value, list):
                result[key] = [
                    self._render_object_template(item, context) if isinstance(item, dict)
                    else self._render_string_template(item, context) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        
        return result
    
    def _process_partials(self, template: str, context: Dict[str, Any]) -> str:
        """处理部分模板"""
        def replace_partial(match):
            partial_name = match.group(1).strip()
            if partial_name in self.partials:
                return self._render_string_template(self.partials[partial_name], context)
            else:
                logger.warning(f"Partial '{partial_name}' not found")
                return ""
        
        return self.partial_pattern.sub(replace_partial, template)
    
    def _process_conditions(self, template: str, context: Dict[str, Any]) -> str:
        """处理条件语句"""
        def replace_condition(match):
            condition = match.group(1).strip()
            content = match.group(2)
            
            if self._evaluate_condition(condition, context):
                return self._render_string_template(content, context)
            else:
                return ""
        
        return self.condition_pattern.sub(replace_condition, template)
    
    def _process_loops(self, template: str, context: Dict[str, Any]) -> str:
        """处理循环"""
        def replace_loop(match):
            items_expr = match.group(1).strip()
            content = match.group(2)
            
            items = self._get_value(items_expr, context)
            if not isinstance(items, list):
                return ""
            
            result = []
            for i, item in enumerate(items):
                loop_context = context.copy()
                loop_context['this'] = item
                loop_context['@index'] = i
                loop_context['@first'] = i == 0
                loop_context['@last'] = i == len(items) - 1
                
                result.append(self._render_string_template(content, loop_context))
            
            return ''.join(result)
        
        return self.loop_pattern.sub(replace_loop, template)
    
    def _process_variables(self, template: str, context: Dict[str, Any]) -> str:
        """处理变量替换"""
        def replace_variable(match):
            expression = match.group(1).strip()
            
            # 检查是否是辅助函数调用
            if self._is_helper_call(expression):
                return str(self._evaluate_helper(expression, context))
            else:
                value = self._get_value(expression, context)
                return str(value) if value is not None else ""
        
        return self.variable_pattern.sub(replace_variable, template)
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """评估条件表达式"""
        # 简单的条件评估实现
        condition = condition.strip()
        
        # 处理辅助函数
        if self._is_helper_call(condition):
            return bool(self._evaluate_helper(condition, context))
        
        # 处理简单变量
        value = self._get_value(condition, context)
        return self._is_truthy(value)
    
    def _is_helper_call(self, expression: str) -> bool:
        """检查是否是辅助函数调用"""
        parts = expression.split()
        return len(parts) > 1 and parts[0] in self.helpers
    
    def _evaluate_helper(self, expression: str, context: Dict[str, Any]) -> Any:
        """评估辅助函数"""
        parts = expression.split()
        helper_name = parts[0]
        args = parts[1:]
        
        if helper_name not in self.helpers:
            logger.warning(f"Helper '{helper_name}' not found")
            return None
        
        # 解析参数
        parsed_args = []
        for arg in args:
            if arg.startswith('"') and arg.endswith('"'):
                # 字符串字面量
                parsed_args.append(arg[1:-1])
            elif arg.startswith("'") and arg.endswith("'"):
                # 字符串字面量
                parsed_args.append(arg[1:-1])
            elif arg.isdigit():
                # 数字字面量
                parsed_args.append(int(arg))
            elif arg.replace('.', '').isdigit():
                # 浮点数字面量
                parsed_args.append(float(arg))
            elif arg in ['true', 'false']:
                # 布尔字面量
                parsed_args.append(arg == 'true')
            else:
                # 变量
                parsed_args.append(self._get_value(arg, context))
        
        return self.helpers[helper_name](*parsed_args)
    
    def _get_value(self, path: str, context: Dict[str, Any]) -> Any:
        """获取变量值"""
        if not path:
            return None
        
        # 处理点号分隔的路径
        parts = path.split('.')
        value = context
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        
        return value
    
    def _is_truthy(self, value: Any) -> bool:
        """判断值是否为真"""
        if value is None or value is False:
            return False
        if isinstance(value, (str, list, dict)) and len(value) == 0:
            return False
        if isinstance(value, (int, float)) and value == 0:
            return False
        return True
    
    # 辅助函数实现
    def _helper_eq(self, a: Any, b: Any) -> bool:
        """相等比较"""
        return a == b
    
    def _helper_ne(self, a: Any, b: Any) -> bool:
        """不等比较"""
        return a != b
    
    def _helper_gt(self, a: Any, b: Any) -> bool:
        """大于比较"""
        try:
            return a > b
        except TypeError:
            return False
    
    def _helper_lt(self, a: Any, b: Any) -> bool:
        """小于比较"""
        try:
            return a < b
        except TypeError:
            return False
    
    def _helper_and(self, *args) -> bool:
        """逻辑与"""
        return all(self._is_truthy(arg) for arg in args)
    
    def _helper_or(self, *args) -> bool:
        """逻辑或"""
        return any(self._is_truthy(arg) for arg in args)
    
    def _helper_not(self, value: Any) -> bool:
        """逻辑非"""
        return not self._is_truthy(value)
    
    def _helper_if(self, condition: Any, true_value: Any, false_value: Any = "") -> Any:
        """条件选择"""
        return true_value if self._is_truthy(condition) else false_value
    
    def _helper_unless(self, condition: Any, true_value: Any, false_value: Any = "") -> Any:
        """反向条件选择"""
        return false_value if self._is_truthy(condition) else true_value

