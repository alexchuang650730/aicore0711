#!/usr/bin/env python3
"""
PowerAutomation 4.0 Test Node Generator

测试节点自动生成器
将用户动作转换为可执行的测试节点
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

from .action_recognition_engine import (
    ActionRecognitionEngine, UserAction, ActionType, ElementType, ScreenElement
)

logger = logging.getLogger(__name__)


class TestNodeType(Enum):
    """测试节点类型"""
    ACTION = "action"           # 执行动作
    VERIFICATION = "verification"  # 验证结果
    WAIT = "wait"              # 等待条件
    DATA = "data"              # 数据准备
    CONDITION = "condition"     # 条件判断
    LOOP = "loop"              # 循环执行
    SCREENSHOT = "screenshot"   # 截图验证


class TestNodeStatus(Enum):
    """测试节点状态"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TestAssertion:
    """测试断言"""
    assertion_type: str  # exists, text_equals, text_contains, visible, enabled, etc.
    target: str         # 目标元素或属性
    expected_value: Any # 期望值
    actual_value: Any = None
    passed: bool = False
    error_message: str = ""


@dataclass
class TestNode:
    """测试节点"""
    node_id: str
    name: str
    description: str
    node_type: TestNodeType
    action_type: Optional[ActionType] = None
    
    # 执行参数
    selector: Optional[str] = None
    coordinates: Optional[Tuple[int, int]] = None
    input_text: Optional[str] = None
    key_combination: Optional[str] = None
    wait_timeout: float = 30.0
    
    # 验证参数
    assertions: List[TestAssertion] = field(default_factory=list)
    screenshot_path: Optional[str] = None
    
    # 执行状态
    status: TestNodeStatus = TestNodeStatus.PENDING
    execution_time: float = 0.0
    error_message: Optional[str] = None
    
    # 元数据
    created_time: datetime = field(default_factory=datetime.now)
    source_action_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestFlow:
    """测试流程"""
    flow_id: str
    name: str
    description: str
    nodes: List[TestNode] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)  # node_id -> [dependency_node_ids]
    created_time: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TestNodeGenerator:
    """测试节点生成器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # 生成配置
        self.auto_generate_assertions = self.config.get('auto_generate_assertions', True)
        self.group_similar_actions = self.config.get('group_similar_actions', True)
        self.add_wait_nodes = self.config.get('add_wait_nodes', True)
        self.screenshot_verification = self.config.get('screenshot_verification', True)
        
        # 动作分组阈值
        self.action_group_timeout = self.config.get('action_group_timeout', 2.0)  # 2秒内的动作可能相关
        self.coordinate_threshold = self.config.get('coordinate_threshold', 50)   # 50像素内认为是同一区域
        
        logger.info("测试节点生成器初始化完成")
    
    async def generate_test_flow_from_actions(self, actions: List[UserAction], flow_name: str = None) -> TestFlow:
        """从用户动作生成测试流程"""
        try:
            flow_id = str(uuid.uuid4())
            flow_name = flow_name or f"Generated_Flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 预处理动作
            processed_actions = self._preprocess_actions(actions)
            
            # 生成测试节点
            test_nodes = []
            for action in processed_actions:
                nodes = await self._generate_nodes_from_action(action)
                test_nodes.extend(nodes)
            
            # 添加验证节点
            if self.auto_generate_assertions:
                verification_nodes = await self._generate_verification_nodes(processed_actions)
                test_nodes.extend(verification_nodes)
            
            # 添加等待节点
            if self.add_wait_nodes:
                wait_nodes = await self._generate_wait_nodes(processed_actions)
                test_nodes.extend(wait_nodes)
            
            # 生成依赖关系
            dependencies = self._generate_dependencies(test_nodes)
            
            test_flow = TestFlow(
                flow_id=flow_id,
                name=flow_name,
                description=f"从 {len(actions)} 个用户动作自动生成的测试流程",
                nodes=test_nodes,
                dependencies=dependencies,
                metadata={
                    'source_actions_count': len(actions),
                    'generated_nodes_count': len(test_nodes),
                    'generation_time': datetime.now().isoformat()
                }
            )
            
            logger.info(f"生成测试流程: {flow_name}, 包含 {len(test_nodes)} 个节点")
            return test_flow
            
        except Exception as e:
            logger.error(f"测试流程生成失败: {e}")
            raise
    
    def _preprocess_actions(self, actions: List[UserAction]) -> List[UserAction]:
        """预处理用户动作"""
        try:
            # 过滤无效动作
            valid_actions = [
                action for action in actions
                if action.action_type in [ActionType.CLICK, ActionType.DOUBLE_CLICK, ActionType.RIGHT_CLICK,
                                        ActionType.TYPE, ActionType.SCROLL, ActionType.KEY_PRESS]
            ]
            
            # 按时间排序
            valid_actions.sort(key=lambda x: x.timestamp)
            
            # 合并相似动作
            if self.group_similar_actions:
                valid_actions = self._group_similar_actions(valid_actions)
            
            logger.debug(f"预处理完成: {len(actions)} -> {len(valid_actions)} 个动作")
            return valid_actions
            
        except Exception as e:
            logger.error(f"动作预处理失败: {e}")
            return actions
    
    def _group_similar_actions(self, actions: List[UserAction]) -> List[UserAction]:
        """合并相似的动作"""
        try:
            grouped_actions = []
            i = 0
            
            while i < len(actions):
                current_action = actions[i]
                
                # 检查是否可以与后续动作合并
                if current_action.action_type == ActionType.TYPE:
                    # 合并连续的输入动作
                    combined_text = current_action.input_text or ""
                    j = i + 1
                    
                    while j < len(actions) and actions[j].action_type == ActionType.TYPE:
                        next_action = actions[j]
                        time_diff = (next_action.timestamp - current_action.timestamp).total_seconds()
                        
                        if time_diff <= self.action_group_timeout:
                            combined_text += next_action.input_text or ""
                            j += 1
                        else:
                            break
                    
                    # 创建合并后的动作
                    if j > i + 1:
                        merged_action = UserAction(
                            action_id=f"merged_{current_action.action_id}",
                            action_type=ActionType.TYPE,
                            timestamp=current_action.timestamp,
                            coordinates=current_action.coordinates,
                            target_element=current_action.target_element,
                            input_text=combined_text,
                            metadata={'merged_from': [actions[k].action_id for k in range(i, j)]}
                        )
                        grouped_actions.append(merged_action)
                        i = j
                    else:
                        grouped_actions.append(current_action)
                        i += 1
                else:
                    grouped_actions.append(current_action)
                    i += 1
            
            return grouped_actions
            
        except Exception as e:
            logger.error(f"动作合并失败: {e}")
            return actions
    
    async def _generate_nodes_from_action(self, action: UserAction) -> List[TestNode]:
        """从单个动作生成测试节点"""
        try:
            nodes = []
            
            if action.action_type in [ActionType.CLICK, ActionType.DOUBLE_CLICK, ActionType.RIGHT_CLICK]:
                node = await self._create_click_node(action)
                nodes.append(node)
                
            elif action.action_type == ActionType.TYPE:
                node = await self._create_input_node(action)
                nodes.append(node)
                
            elif action.action_type == ActionType.SCROLL:
                node = await self._create_scroll_node(action)
                nodes.append(node)
                
            elif action.action_type == ActionType.KEY_PRESS:
                node = await self._create_key_press_node(action)
                nodes.append(node)
            
            return nodes
            
        except Exception as e:
            logger.error(f"节点生成失败: {e}")
            return []
    
    async def _create_click_node(self, action: UserAction) -> TestNode:
        """创建点击节点"""
        node_id = str(uuid.uuid4())
        
        # 生成选择器
        selector = self._generate_selector(action.target_element)
        
        # 生成节点名称和描述
        element_desc = "未知元素"
        if action.target_element:
            if action.target_element.text:
                element_desc = f"'{action.target_element.text}'"
            else:
                element_desc = f"{action.target_element.element_type.value}元素"
        
        action_name = "点击"
        if action.action_type == ActionType.DOUBLE_CLICK:
            action_name = "双击"
        elif action.action_type == ActionType.RIGHT_CLICK:
            action_name = "右键点击"
        
        node = TestNode(
            node_id=node_id,
            name=f"{action_name}{element_desc}",
            description=f"{action_name}位于 {action.coordinates} 的{element_desc}",
            node_type=TestNodeType.ACTION,
            action_type=action.action_type,
            selector=selector,
            coordinates=action.coordinates,
            source_action_id=action.action_id,
            metadata={
                'original_action': asdict(action),
                'element_type': action.target_element.element_type.value if action.target_element else None
            }
        )
        
        return node
    
    async def _create_input_node(self, action: UserAction) -> TestNode:
        """创建输入节点"""
        node_id = str(uuid.uuid4())
        
        # 生成选择器
        selector = self._generate_selector(action.target_element)
        
        # 生成节点名称和描述
        element_desc = "输入框"
        if action.target_element and action.target_element.text:
            element_desc = f"'{action.target_element.text}'输入框"
        
        node = TestNode(
            node_id=node_id,
            name=f"在{element_desc}中输入文本",
            description=f"在位于 {action.coordinates} 的{element_desc}中输入: {action.input_text}",
            node_type=TestNodeType.ACTION,
            action_type=ActionType.TYPE,
            selector=selector,
            coordinates=action.coordinates,
            input_text=action.input_text,
            source_action_id=action.action_id,
            metadata={
                'original_action': asdict(action),
                'text_length': len(action.input_text or "")
            }
        )
        
        return node
    
    async def _create_scroll_node(self, action: UserAction) -> TestNode:
        """创建滚动节点"""
        node_id = str(uuid.uuid4())
        
        direction_desc = "向下" if action.scroll_direction == "down" else "向上"
        
        node = TestNode(
            node_id=node_id,
            name=f"{direction_desc}滚动页面",
            description=f"在位置 {action.coordinates} {direction_desc}滚动 {action.scroll_amount} 次",
            node_type=TestNodeType.ACTION,
            action_type=ActionType.SCROLL,
            coordinates=action.coordinates,
            source_action_id=action.action_id,
            metadata={
                'original_action': asdict(action),
                'scroll_direction': action.scroll_direction,
                'scroll_amount': action.scroll_amount
            }
        )
        
        return node
    
    async def _create_key_press_node(self, action: UserAction) -> TestNode:
        """创建按键节点"""
        node_id = str(uuid.uuid4())
        
        node = TestNode(
            node_id=node_id,
            name=f"按下 {action.key_combination}",
            description=f"按下键盘组合键: {action.key_combination}",
            node_type=TestNodeType.ACTION,
            action_type=ActionType.KEY_PRESS,
            key_combination=action.key_combination,
            source_action_id=action.action_id,
            metadata={
                'original_action': asdict(action)
            }
        )
        
        return node
    
    async def _generate_verification_nodes(self, actions: List[UserAction]) -> List[TestNode]:
        """生成验证节点"""
        verification_nodes = []
        
        try:
            # 为每个有目标元素的动作生成验证
            for action in actions:
                if action.target_element and action.action_type in [ActionType.CLICK, ActionType.TYPE]:
                    node = await self._create_verification_node(action)
                    if node:
                        verification_nodes.append(node)
            
            # 添加页面级验证
            if actions:
                page_verification = await self._create_page_verification_node()
                if page_verification:
                    verification_nodes.append(page_verification)
            
        except Exception as e:
            logger.error(f"验证节点生成失败: {e}")
        
        return verification_nodes
    
    async def _create_verification_node(self, action: UserAction) -> Optional[TestNode]:
        """创建验证节点"""
        try:
            node_id = str(uuid.uuid4())
            
            assertions = []
            
            # 根据动作类型生成不同的断言
            if action.action_type == ActionType.CLICK:
                # 验证点击后的状态变化
                assertions.append(TestAssertion(
                    assertion_type="element_exists",
                    target=self._generate_selector(action.target_element),
                    expected_value=True
                ))
                
                if action.target_element and action.target_element.element_type == ElementType.BUTTON:
                    # 如果是按钮，可能会导航到新页面或显示新内容
                    assertions.append(TestAssertion(
                        assertion_type="page_changed",
                        target="page_url_or_title",
                        expected_value="changed"
                    ))
            
            elif action.action_type == ActionType.TYPE:
                # 验证输入的文本
                assertions.append(TestAssertion(
                    assertion_type="text_equals",
                    target=self._generate_selector(action.target_element),
                    expected_value=action.input_text
                ))
            
            if not assertions:
                return None
            
            element_desc = "元素"
            if action.target_element and action.target_element.text:
                element_desc = f"'{action.target_element.text}'"
            
            node = TestNode(
                node_id=node_id,
                name=f"验证{element_desc}状态",
                description=f"验证{element_desc}的状态是否符合预期",
                node_type=TestNodeType.VERIFICATION,
                assertions=assertions,
                source_action_id=action.action_id,
                metadata={
                    'verification_for': action.action_id,
                    'assertion_count': len(assertions)
                }
            )
            
            return node
            
        except Exception as e:
            logger.error(f"验证节点创建失败: {e}")
            return None
    
    async def _create_page_verification_node(self) -> Optional[TestNode]:
        """创建页面级验证节点"""
        try:
            node_id = str(uuid.uuid4())
            
            assertions = [
                TestAssertion(
                    assertion_type="page_loaded",
                    target="document.readyState",
                    expected_value="complete"
                ),
                TestAssertion(
                    assertion_type="no_errors",
                    target="console.errors",
                    expected_value=0
                )
            ]
            
            node = TestNode(
                node_id=node_id,
                name="验证页面状态",
                description="验证页面是否正确加载且无错误",
                node_type=TestNodeType.VERIFICATION,
                assertions=assertions,
                metadata={
                    'verification_type': 'page_level'
                }
            )
            
            return node
            
        except Exception as e:
            logger.error(f"页面验证节点创建失败: {e}")
            return None
    
    async def _generate_wait_nodes(self, actions: List[UserAction]) -> List[TestNode]:
        """生成等待节点"""
        wait_nodes = []
        
        try:
            # 在可能需要等待的动作后添加等待节点
            for i, action in enumerate(actions):
                if action.action_type == ActionType.CLICK and action.target_element:
                    # 如果点击的是按钮或链接，可能需要等待页面加载
                    if action.target_element.element_type in [ElementType.BUTTON, ElementType.LINK]:
                        wait_node = await self._create_wait_node(action)
                        if wait_node:
                            wait_nodes.append(wait_node)
        
        except Exception as e:
            logger.error(f"等待节点生成失败: {e}")
        
        return wait_nodes
    
    async def _create_wait_node(self, action: UserAction) -> Optional[TestNode]:
        """创建等待节点"""
        try:
            node_id = str(uuid.uuid4())
            
            node = TestNode(
                node_id=node_id,
                name="等待页面响应",
                description=f"等待点击{action.target_element.text or '元素'}后的页面响应",
                node_type=TestNodeType.WAIT,
                wait_timeout=5.0,
                source_action_id=action.action_id,
                metadata={
                    'wait_for': 'page_response',
                    'trigger_action': action.action_id
                }
            )
            
            return node
            
        except Exception as e:
            logger.error(f"等待节点创建失败: {e}")
            return None
    
    def _generate_dependencies(self, nodes: List[TestNode]) -> Dict[str, List[str]]:
        """生成节点依赖关系"""
        dependencies = {}
        
        try:
            # 按照时间顺序和逻辑关系建立依赖
            for i, node in enumerate(nodes):
                deps = []
                
                # 每个节点依赖于前一个节点（简单的顺序依赖）
                if i > 0:
                    deps.append(nodes[i-1].node_id)
                
                # 验证节点依赖于对应的动作节点
                if node.node_type == TestNodeType.VERIFICATION and node.source_action_id:
                    for other_node in nodes:
                        if other_node.source_action_id == node.source_action_id and other_node.node_type == TestNodeType.ACTION:
                            if other_node.node_id not in deps:
                                deps.append(other_node.node_id)
                
                # 等待节点依赖于触发动作
                if node.node_type == TestNodeType.WAIT and node.source_action_id:
                    for other_node in nodes:
                        if other_node.source_action_id == node.source_action_id and other_node.node_type == TestNodeType.ACTION:
                            if other_node.node_id not in deps:
                                deps.append(other_node.node_id)
                
                if deps:
                    dependencies[node.node_id] = deps
        
        except Exception as e:
            logger.error(f"依赖关系生成失败: {e}")
        
        return dependencies
    
    def _generate_selector(self, element: Optional[ScreenElement]) -> Optional[str]:
        """生成元素选择器"""
        if not element:
            return None
        
        try:
            # 基于元素信息生成CSS选择器或XPath
            if element.text:
                # 基于文本内容生成选择器
                text = element.text.strip()
                if element.element_type == ElementType.BUTTON:
                    return f"button:contains('{text}')"
                elif element.element_type == ElementType.LINK:
                    return f"a:contains('{text}')"
                elif element.element_type == ElementType.INPUT:
                    return f"input[placeholder*='{text}']"
                else:
                    return f"*:contains('{text}')"
            
            # 基于元素类型生成通用选择器
            if element.element_type == ElementType.BUTTON:
                return "button"
            elif element.element_type == ElementType.INPUT:
                return "input"
            elif element.element_type == ElementType.LINK:
                return "a"
            
            # 基于坐标生成选择器（最后的备选方案）
            x, y, w, h = element.bounds
            return f"element_at_{x}_{y}"
            
        except Exception as e:
            logger.error(f"选择器生成失败: {e}")
            return None
    
    def export_test_flow_to_json(self, test_flow: TestFlow, filepath: str):
        """导出测试流程到JSON文件"""
        try:
            flow_data = {
                'flow_id': test_flow.flow_id,
                'name': test_flow.name,
                'description': test_flow.description,
                'created_time': test_flow.created_time.isoformat(),
                'metadata': test_flow.metadata,
                'nodes': [],
                'dependencies': test_flow.dependencies
            }
            
            for node in test_flow.nodes:
                node_data = {
                    'node_id': node.node_id,
                    'name': node.name,
                    'description': node.description,
                    'node_type': node.node_type.value,
                    'action_type': node.action_type.value if node.action_type else None,
                    'selector': node.selector,
                    'coordinates': node.coordinates,
                    'input_text': node.input_text,
                    'key_combination': node.key_combination,
                    'wait_timeout': node.wait_timeout,
                    'assertions': [asdict(assertion) for assertion in node.assertions],
                    'status': node.status.value,
                    'created_time': node.created_time.isoformat(),
                    'source_action_id': node.source_action_id,
                    'metadata': node.metadata
                }
                flow_data['nodes'].append(node_data)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(flow_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"测试流程已导出到: {filepath}")
            
        except Exception as e:
            logger.error(f"测试流程导出失败: {e}")


# 使用示例
async def demo_test_node_generation():
    """测试节点生成演示"""
    from .action_recognition_engine import ActionRecognitionEngine
    
    # 创建动作识别引擎和节点生成器
    action_engine = ActionRecognitionEngine()
    node_generator = TestNodeGenerator()
    
    # 模拟一些用户动作
    print("模拟用户动作...")
    actions = [
        action_engine.simulate_click_action((100, 100)),
        action_engine.simulate_type_action("test@example.com", (200, 150)),
        action_engine.simulate_click_action((300, 200)),
    ]
    
    # 生成测试流程
    print("生成测试流程...")
    test_flow = await node_generator.generate_test_flow_from_actions(actions, "登录测试流程")
    
    # 导出测试流程
    node_generator.export_test_flow_to_json(test_flow, "demo_test_flow.json")
    
    print(f"生成了包含 {len(test_flow.nodes)} 个节点的测试流程")
    for node in test_flow.nodes:
        print(f"  - {node.name} ({node.node_type.value})")


if __name__ == "__main__":
    asyncio.run(demo_test_node_generation())

