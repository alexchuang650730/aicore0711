#!/usr/bin/env python3
"""
PowerAutomation 4.0 AG-UI Auto Generator

AG-UI组件自动生成器
将测试节点转换为可复用的AG-UI组件
"""

import asyncio
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import re

from .test_node_generator import TestNode, TestFlow, TestNodeType, TestAssertion
from .action_recognition_engine import ActionType, ElementType
from ..ag_ui_mcp.ag_ui_component_generator import AGUIComponentGenerator

logger = logging.getLogger(__name__)


class AGUIComponentType(Enum):
    """AG-UI组件类型"""
    BUTTON = "button"
    INPUT = "input"
    FORM = "form"
    DIALOG = "dialog"
    LIST = "list"
    CARD = "card"
    NAVIGATION = "navigation"
    WORKFLOW = "workflow"
    TEST_SUITE = "test_suite"


@dataclass
class AGUIComponent:
    """AG-UI组件"""
    component_id: str
    name: str
    component_type: AGUIComponentType
    description: str
    
    # 组件属性
    props: Dict[str, Any] = field(default_factory=dict)
    events: Dict[str, str] = field(default_factory=dict)
    styles: Dict[str, Any] = field(default_factory=dict)
    
    # 测试相关
    test_actions: List[str] = field(default_factory=list)  # 关联的测试动作
    assertions: List[TestAssertion] = field(default_factory=list)
    
    # 代码生成
    react_code: Optional[str] = None
    vue_code: Optional[str] = None
    html_code: Optional[str] = None
    css_code: Optional[str] = None
    
    # 元数据
    created_time: datetime = field(default_factory=datetime.now)
    source_nodes: List[str] = field(default_factory=list)  # 源测试节点ID
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AGUITestSuite:
    """AG-UI测试套件"""
    suite_id: str
    name: str
    description: str
    components: List[AGUIComponent] = field(default_factory=list)
    test_flow: Optional[TestFlow] = None
    
    # 套件级别的代码
    test_runner_code: Optional[str] = None
    integration_code: Optional[str] = None
    
    created_time: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AGUIAutoGenerator:
    """AG-UI自动生成器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.ag_ui_generator = AGUIComponentGenerator()
        
        # 生成配置
        self.generate_react = self.config.get('generate_react', True)
        self.generate_vue = self.config.get('generate_vue', False)
        self.generate_html = self.config.get('generate_html', True)
        self.component_prefix = self.config.get('component_prefix', 'Test')
        
        # 组件模板
        self._init_templates()
        
        logger.info("AG-UI自动生成器初始化完成")
    
    def _init_templates(self):
        """初始化组件模板"""
        self.templates = {
            'react_button': '''
import React from 'react';
import {{ Button }} from '@/components/ui/button';

interface {component_name}Props {{
  onClick?: () => void;
  disabled?: boolean;
  children?: React.ReactNode;
  testId?: string;
}}

export const {component_name}: React.FC<{component_name}Props> = ({{
  onClick,
  disabled = false,
  children = "{button_text}",
  testId = "{test_id}"
}}) => {{
  return (
    <Button
      onClick={{onClick}}
      disabled={{disabled}}
      data-testid={{testId}}
      className="{css_classes}"
    >
      {{children}}
    </Button>
  );
}};
''',
            
            'react_input': '''
import React, {{ useState }} from 'react';
import {{ Input }} from '@/components/ui/input';

interface {component_name}Props {{
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  testId?: string;
}}

export const {component_name}: React.FC<{component_name}Props> = ({{
  value: controlledValue,
  onChange,
  placeholder = "{placeholder_text}",
  disabled = false,
  testId = "{test_id}"
}}) => {{
  const [internalValue, setInternalValue] = useState(controlledValue || "");
  const value = controlledValue !== undefined ? controlledValue : internalValue;
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {{
    const newValue = e.target.value;
    if (controlledValue === undefined) {{
      setInternalValue(newValue);
    }}
    onChange?.(newValue);
  }};
  
  return (
    <Input
      value={{value}}
      onChange={{handleChange}}
      placeholder={{placeholder}}
      disabled={{disabled}}
      data-testid={{testId}}
      className="{css_classes}"
    />
  );
}};
''',
            
            'react_form': '''
import React, {{ useState }} from 'react';
import {{ Form, FormField, FormItem, FormLabel, FormControl }} from '@/components/ui/form';
import {{ Button }} from '@/components/ui/button';

interface {component_name}Props {{
  onSubmit?: (data: any) => void;
  initialData?: any;
  testId?: string;
}}

export const {component_name}: React.FC<{component_name}Props> = ({{
  onSubmit,
  initialData = {{}},
  testId = "{test_id}"
}}) => {{
  const [formData, setFormData] = useState(initialData);
  
  const handleSubmit = (e: React.FormEvent) => {{
    e.preventDefault();
    onSubmit?.(formData);
  }};
  
  return (
    <Form onSubmit={{handleSubmit}} data-testid={{testId}}>
      {form_fields}
      <Button type="submit" className="mt-4">
        提交
      </Button>
    </Form>
  );
}};
''',
            
            'test_runner': '''
import {{ render, screen, fireEvent, waitFor }} from '@testing-library/react';
import {{ {component_name} }} from './{component_name}';

describe('{component_name}', () => {{
  {test_cases}
}});
'''
        }
    
    async def generate_components_from_test_flow(self, test_flow: TestFlow) -> AGUITestSuite:
        """从测试流程生成AG-UI组件"""
        try:
            suite_id = str(uuid.uuid4())
            suite_name = f"{test_flow.name}_Components"
            
            # 分析测试节点，识别可复用的组件模式
            component_patterns = self._analyze_component_patterns(test_flow.nodes)
            
            # 生成AG-UI组件
            components = []
            for pattern in component_patterns:
                component = await self._generate_component_from_pattern(pattern, test_flow.nodes)
                if component:
                    components.append(component)
            
            # 生成测试套件级别的代码
            test_runner_code = self._generate_test_runner_code(components, test_flow)
            integration_code = self._generate_integration_code(components, test_flow)
            
            test_suite = AGUITestSuite(
                suite_id=suite_id,
                name=suite_name,
                description=f"从测试流程 '{test_flow.name}' 自动生成的AG-UI组件套件",
                components=components,
                test_flow=test_flow,
                test_runner_code=test_runner_code,
                integration_code=integration_code,
                metadata={
                    'source_flow_id': test_flow.flow_id,
                    'generated_components_count': len(components),
                    'generation_time': datetime.now().isoformat()
                }
            )
            
            logger.info(f"生成AG-UI测试套件: {suite_name}, 包含 {len(components)} 个组件")
            return test_suite
            
        except Exception as e:
            logger.error(f"AG-UI组件生成失败: {e}")
            raise
    
    def _analyze_component_patterns(self, nodes: List[TestNode]) -> List[Dict[str, Any]]:
        """分析组件模式"""
        patterns = []
        
        try:
            # 按功能分组节点
            action_groups = self._group_nodes_by_function(nodes)
            
            for group_name, group_nodes in action_groups.items():
                pattern = self._identify_component_pattern(group_name, group_nodes)
                if pattern:
                    patterns.append(pattern)
            
            logger.debug(f"识别到 {len(patterns)} 个组件模式")
            return patterns
            
        except Exception as e:
            logger.error(f"组件模式分析失败: {e}")
            return []
    
    def _group_nodes_by_function(self, nodes: List[TestNode]) -> Dict[str, List[TestNode]]:
        """按功能分组节点"""
        groups = {}
        
        try:
            for node in nodes:
                if node.node_type == TestNodeType.ACTION:
                    # 基于动作类型和目标元素分组
                    group_key = self._determine_group_key(node)
                    if group_key not in groups:
                        groups[group_key] = []
                    groups[group_key].append(node)
            
            return groups
            
        except Exception as e:
            logger.error(f"节点分组失败: {e}")
            return {}
    
    def _determine_group_key(self, node: TestNode) -> str:
        """确定节点的分组键"""
        try:
            # 基于节点特征生成分组键
            if node.action_type == ActionType.CLICK:
                if "button" in node.name.lower() or "btn" in node.name.lower():
                    return "button_interactions"
                elif "link" in node.name.lower():
                    return "navigation_links"
                else:
                    return "click_actions"
            
            elif node.action_type == ActionType.TYPE:
                if "input" in node.name.lower() or "输入" in node.name:
                    return "form_inputs"
                else:
                    return "text_inputs"
            
            elif node.action_type == ActionType.SCROLL:
                return "scroll_actions"
            
            else:
                return "other_actions"
                
        except Exception as e:
            logger.error(f"分组键确定失败: {e}")
            return "unknown_actions"
    
    def _identify_component_pattern(self, group_name: str, nodes: List[TestNode]) -> Optional[Dict[str, Any]]:
        """识别组件模式"""
        try:
            if not nodes:
                return None
            
            pattern = {
                'pattern_id': str(uuid.uuid4()),
                'group_name': group_name,
                'nodes': nodes,
                'component_type': self._map_group_to_component_type(group_name),
                'properties': self._extract_component_properties(nodes),
                'events': self._extract_component_events(nodes),
                'styles': self._extract_component_styles(nodes)
            }
            
            return pattern
            
        except Exception as e:
            logger.error(f"组件模式识别失败: {e}")
            return None
    
    def _map_group_to_component_type(self, group_name: str) -> AGUIComponentType:
        """映射分组到组件类型"""
        mapping = {
            'button_interactions': AGUIComponentType.BUTTON,
            'form_inputs': AGUIComponentType.INPUT,
            'navigation_links': AGUIComponentType.NAVIGATION,
            'click_actions': AGUIComponentType.BUTTON,
            'text_inputs': AGUIComponentType.INPUT,
            'scroll_actions': AGUIComponentType.LIST
        }
        
        return mapping.get(group_name, AGUIComponentType.BUTTON)
    
    def _extract_component_properties(self, nodes: List[TestNode]) -> Dict[str, Any]:
        """提取组件属性"""
        props = {}
        
        try:
            for node in nodes:
                if node.action_type == ActionType.TYPE and node.input_text:
                    props['defaultValue'] = node.input_text
                    props['placeholder'] = f"请输入{node.name}"
                
                elif node.action_type == ActionType.CLICK:
                    props['onClick'] = True
                    if "button" in node.name.lower():
                        props['variant'] = 'primary'
                
                if node.selector:
                    props['selector'] = node.selector
                
                if node.coordinates:
                    props['position'] = node.coordinates
            
            return props
            
        except Exception as e:
            logger.error(f"组件属性提取失败: {e}")
            return {}
    
    def _extract_component_events(self, nodes: List[TestNode]) -> Dict[str, str]:
        """提取组件事件"""
        events = {}
        
        try:
            for node in nodes:
                if node.action_type == ActionType.CLICK:
                    events['onClick'] = f"handle{self._pascal_case(node.name)}Click"
                
                elif node.action_type == ActionType.TYPE:
                    events['onChange'] = f"handle{self._pascal_case(node.name)}Change"
                
                elif node.action_type == ActionType.SCROLL:
                    events['onScroll'] = f"handle{self._pascal_case(node.name)}Scroll"
            
            return events
            
        except Exception as e:
            logger.error(f"组件事件提取失败: {e}")
            return {}
    
    def _extract_component_styles(self, nodes: List[TestNode]) -> Dict[str, Any]:
        """提取组件样式"""
        styles = {}
        
        try:
            # 基于节点信息推断样式
            for node in nodes:
                if node.coordinates:
                    x, y = node.coordinates
                    styles['position'] = 'absolute'
                    styles['left'] = f"{x}px"
                    styles['top'] = f"{y}px"
                
                if "button" in node.name.lower():
                    styles['padding'] = '8px 16px'
                    styles['borderRadius'] = '4px'
                    styles['cursor'] = 'pointer'
                
                elif "input" in node.name.lower():
                    styles['padding'] = '8px 12px'
                    styles['border'] = '1px solid #ccc'
                    styles['borderRadius'] = '4px'
            
            return styles
            
        except Exception as e:
            logger.error(f"组件样式提取失败: {e}")
            return {}
    
    async def _generate_component_from_pattern(self, pattern: Dict[str, Any], all_nodes: List[TestNode]) -> Optional[AGUIComponent]:
        """从模式生成组件"""
        try:
            component_id = str(uuid.uuid4())
            component_name = self._generate_component_name(pattern)
            component_type = pattern['component_type']
            
            # 生成组件代码
            react_code = None
            vue_code = None
            html_code = None
            css_code = None
            
            if self.generate_react:
                react_code = self._generate_react_code(component_name, component_type, pattern)
            
            if self.generate_vue:
                vue_code = self._generate_vue_code(component_name, component_type, pattern)
            
            if self.generate_html:
                html_code = self._generate_html_code(component_name, component_type, pattern)
                css_code = self._generate_css_code(component_name, component_type, pattern)
            
            # 提取测试断言
            assertions = []
            for node in pattern['nodes']:
                assertions.extend(node.assertions)
            
            component = AGUIComponent(
                component_id=component_id,
                name=component_name,
                component_type=component_type,
                description=f"从 {pattern['group_name']} 模式自动生成的组件",
                props=pattern['properties'],
                events=pattern['events'],
                styles=pattern['styles'],
                test_actions=[node.node_id for node in pattern['nodes']],
                assertions=assertions,
                react_code=react_code,
                vue_code=vue_code,
                html_code=html_code,
                css_code=css_code,
                source_nodes=[node.node_id for node in pattern['nodes']],
                metadata={
                    'pattern_id': pattern['pattern_id'],
                    'group_name': pattern['group_name'],
                    'node_count': len(pattern['nodes'])
                }
            )
            
            return component
            
        except Exception as e:
            logger.error(f"组件生成失败: {e}")
            return None
    
    def _generate_component_name(self, pattern: Dict[str, Any]) -> str:
        """生成组件名称"""
        try:
            base_name = pattern['group_name'].replace('_', ' ').title().replace(' ', '')
            component_name = f"{self.component_prefix}{base_name}Component"
            return component_name
            
        except Exception as e:
            logger.error(f"组件名称生成失败: {e}")
            return f"{self.component_prefix}Component"
    
    def _generate_react_code(self, component_name: str, component_type: AGUIComponentType, pattern: Dict[str, Any]) -> str:
        """生成React代码"""
        try:
            if component_type == AGUIComponentType.BUTTON:
                return self._generate_react_button_code(component_name, pattern)
            elif component_type == AGUIComponentType.INPUT:
                return self._generate_react_input_code(component_name, pattern)
            elif component_type == AGUIComponentType.FORM:
                return self._generate_react_form_code(component_name, pattern)
            else:
                return self._generate_react_generic_code(component_name, pattern)
                
        except Exception as e:
            logger.error(f"React代码生成失败: {e}")
            return f"// React component: {component_name}\n// Generation failed: {str(e)}"
    
    def _generate_react_button_code(self, component_name: str, pattern: Dict[str, Any]) -> str:
        """生成React按钮代码"""
        try:
            # 从节点中提取按钮文本
            button_text = "Click Me"
            for node in pattern['nodes']:
                if node.name and "'" in node.name:
                    # 提取引号中的文本
                    match = re.search(r"'([^']*)'", node.name)
                    if match:
                        button_text = match.group(1)
                        break
            
            return self.templates['react_button'].format(
                component_name=component_name,
                button_text=button_text,
                test_id=component_name.lower(),
                css_classes="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            )
            
        except Exception as e:
            logger.error(f"React按钮代码生成失败: {e}")
            return f"// React button component: {component_name}\n// Generation failed"
    
    def _generate_react_input_code(self, component_name: str, pattern: Dict[str, Any]) -> str:
        """生成React输入框代码"""
        try:
            # 从节点中提取占位符文本
            placeholder_text = "请输入内容"
            for node in pattern['nodes']:
                if node.input_text:
                    placeholder_text = f"请输入{node.input_text}"
                    break
                elif "输入" in node.name:
                    placeholder_text = node.name.replace("在", "").replace("中输入文本", "")
            
            return self.templates['react_input'].format(
                component_name=component_name,
                placeholder_text=placeholder_text,
                test_id=component_name.lower(),
                css_classes="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
            )
            
        except Exception as e:
            logger.error(f"React输入框代码生成失败: {e}")
            return f"// React input component: {component_name}\n// Generation failed"
    
    def _generate_react_form_code(self, component_name: str, pattern: Dict[str, Any]) -> str:
        """生成React表单代码"""
        try:
            # 生成表单字段
            form_fields = []
            for node in pattern['nodes']:
                if node.action_type == ActionType.TYPE:
                    field_name = self._camel_case(node.name)
                    form_fields.append(f'''
      <FormField name="{field_name}">
        <FormItem>
          <FormLabel>{node.name}</FormLabel>
          <FormControl>
            <Input
              value={{formData.{field_name} || ""}}
              onChange={{(e) => setFormData({{...formData, {field_name}: e.target.value}})}}
              placeholder="{node.input_text or '请输入'}"
            />
          </FormControl>
        </FormItem>
      </FormField>''')
            
            form_fields_code = '\n'.join(form_fields)
            
            return self.templates['react_form'].format(
                component_name=component_name,
                test_id=component_name.lower(),
                form_fields=form_fields_code
            )
            
        except Exception as e:
            logger.error(f"React表单代码生成失败: {e}")
            return f"// React form component: {component_name}\n// Generation failed"
    
    def _generate_react_generic_code(self, component_name: str, pattern: Dict[str, Any]) -> str:
        """生成通用React代码"""
        return f'''
import React from 'react';

interface {component_name}Props {{
  testId?: string;
}}

export const {component_name}: React.FC<{component_name}Props> = ({{
  testId = "{component_name.lower()}"
}}) => {{
  return (
    <div data-testid={{testId}} className="component-{component_name.lower()}">
      {/* Generated from pattern: {pattern['group_name']} */}
      <p>Component: {component_name}</p>
    </div>
  );
}};
'''
    
    def _generate_vue_code(self, component_name: str, component_type: AGUIComponentType, pattern: Dict[str, Any]) -> str:
        """生成Vue代码"""
        # Vue代码生成实现
        return f"<!-- Vue component: {component_name} -->\n<!-- TODO: Implement Vue code generation -->"
    
    def _generate_html_code(self, component_name: str, component_type: AGUIComponentType, pattern: Dict[str, Any]) -> str:
        """生成HTML代码"""
        # HTML代码生成实现
        return f"<!-- HTML component: {component_name} -->\n<!-- TODO: Implement HTML code generation -->"
    
    def _generate_css_code(self, component_name: str, component_type: AGUIComponentType, pattern: Dict[str, Any]) -> str:
        """生成CSS代码"""
        # CSS代码生成实现
        return f"/* CSS for component: {component_name} */\n/* TODO: Implement CSS code generation */"
    
    def _generate_test_runner_code(self, components: List[AGUIComponent], test_flow: TestFlow) -> str:
        """生成测试运行器代码"""
        try:
            test_cases = []
            
            for component in components:
                test_case = f'''
  it('should render and interact with {component.name}', async () => {{
    render(<{component.name} />);
    
    // Test component rendering
    const component = screen.getByTestId('{component.name.lower()}');
    expect(component).toBeInTheDocument();
    
    // Test interactions
    {self._generate_interaction_tests(component)}
  }});'''
                test_cases.append(test_case)
            
            test_cases_code = '\n'.join(test_cases)
            component_imports = ', '.join([comp.name for comp in components])
            
            return self.templates['test_runner'].format(
                component_name=component_imports,
                test_cases=test_cases_code
            )
            
        except Exception as e:
            logger.error(f"测试运行器代码生成失败: {e}")
            return "// Test runner generation failed"
    
    def _generate_interaction_tests(self, component: AGUIComponent) -> str:
        """生成交互测试代码"""
        tests = []
        
        if 'onClick' in component.events:
            tests.append('''
    // Test click interaction
    fireEvent.click(component);
    // Add assertions here''')
        
        if 'onChange' in component.events:
            tests.append('''
    // Test input change
    fireEvent.change(component, { target: { value: 'test input' } });
    // Add assertions here''')
        
        return '\n'.join(tests)
    
    def _generate_integration_code(self, components: List[AGUIComponent], test_flow: TestFlow) -> str:
        """生成集成代码"""
        try:
            component_imports = '\n'.join([
                f"import {{ {comp.name} }} from './{comp.name}';"
                for comp in components
            ])
            
            component_usage = '\n'.join([
                f"      <{comp.name} />"
                for comp in components
            ])
            
            return f'''
{component_imports}

export const TestFlowIntegration = () => {{
  return (
    <div className="test-flow-integration">
      <h2>{test_flow.name}</h2>
      <div className="components">
{component_usage}
      </div>
    </div>
  );
}};
'''
            
        except Exception as e:
            logger.error(f"集成代码生成失败: {e}")
            return "// Integration code generation failed"
    
    def _pascal_case(self, text: str) -> str:
        """转换为PascalCase"""
        return ''.join(word.capitalize() for word in re.findall(r'\w+', text))
    
    def _camel_case(self, text: str) -> str:
        """转换为camelCase"""
        words = re.findall(r'\w+', text)
        if not words:
            return text
        return words[0].lower() + ''.join(word.capitalize() for word in words[1:])
    
    def export_test_suite_to_files(self, test_suite: AGUITestSuite, output_dir: str):
        """导出测试套件到文件"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 导出组件文件
            for component in test_suite.components:
                if component.react_code:
                    react_file = output_path / f"{component.name}.tsx"
                    with open(react_file, 'w', encoding='utf-8') as f:
                        f.write(component.react_code)
                
                if component.vue_code:
                    vue_file = output_path / f"{component.name}.vue"
                    with open(vue_file, 'w', encoding='utf-8') as f:
                        f.write(component.vue_code)
                
                if component.html_code:
                    html_file = output_path / f"{component.name}.html"
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(component.html_code)
                
                if component.css_code:
                    css_file = output_path / f"{component.name}.css"
                    with open(css_file, 'w', encoding='utf-8') as f:
                        f.write(component.css_code)
            
            # 导出测试运行器
            if test_suite.test_runner_code:
                test_file = output_path / "TestRunner.test.tsx"
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(test_suite.test_runner_code)
            
            # 导出集成代码
            if test_suite.integration_code:
                integration_file = output_path / "Integration.tsx"
                with open(integration_file, 'w', encoding='utf-8') as f:
                    f.write(test_suite.integration_code)
            
            # 导出套件元数据
            metadata_file = output_path / "suite_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(test_suite), f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"测试套件已导出到: {output_path}")
            
        except Exception as e:
            logger.error(f"测试套件导出失败: {e}")


# 使用示例
async def demo_ag_ui_generation():
    """AG-UI生成演示"""
    from .action_recognition_engine import ActionRecognitionEngine
    from .test_node_generator import TestNodeGenerator
    
    # 创建引擎
    action_engine = ActionRecognitionEngine()
    node_generator = TestNodeGenerator()
    ag_ui_generator = AGUIAutoGenerator()
    
    # 模拟用户动作
    print("模拟用户动作...")
    actions = [
        action_engine.simulate_click_action((100, 100)),
        action_engine.simulate_type_action("test@example.com", (200, 150)),
        action_engine.simulate_click_action((300, 200)),
    ]
    
    # 生成测试流程
    print("生成测试流程...")
    test_flow = await node_generator.generate_test_flow_from_actions(actions, "登录测试流程")
    
    # 生成AG-UI组件
    print("生成AG-UI组件...")
    test_suite = await ag_ui_generator.generate_components_from_test_flow(test_flow)
    
    # 导出组件文件
    ag_ui_generator.export_test_suite_to_files(test_suite, "generated_components")
    
    print(f"生成了 {len(test_suite.components)} 个AG-UI组件")
    for component in test_suite.components:
        print(f"  - {component.name} ({component.component_type.value})")


if __name__ == "__main__":
    asyncio.run(demo_ag_ui_generation())

