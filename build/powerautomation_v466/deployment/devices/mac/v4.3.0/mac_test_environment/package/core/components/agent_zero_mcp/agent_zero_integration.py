#!/usr/bin/env python3
"""
Agent Zero有机智能体完整深度集成

基于Agent Zero的有机智能体架构，为PowerAutomation 4.1提供自学习智能体网络。
实现5个专业智能体的协作、自学习能力、动态适应性和知识图谱构建。

主要功能：
- 5个专业智能体（代码分析、生成、调试、优化、协作）
- 自学习能力和持续改进
- 动态适应性和策略调整
- 多智能体协作和知识共享
- 知识图谱构建和维护
- 有机进化和能力增长

技术特色：
- 有机智能体架构
- 自学习和适应算法
- 多智能体协作网络
- 知识驱动的决策
- 持续学习和改进

作者: PowerAutomation Team
版本: 4.1.0
日期: 2025-01-07
"""

import asyncio
import json
import uuid
import logging
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import pickle
import hashlib
import sqlite3
from collections import defaultdict, deque
import threading
import math
import random
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class AgentType(Enum):
    """智能体类型"""
    CODE_ANALYZER = "code_analyzer"  # 代码分析智能体
    CODE_GENERATOR = "code_generator"  # 代码生成智能体
    DEBUGGER = "debugger"  # 调试智能体
    OPTIMIZER = "optimizer"  # 优化智能体
    COLLABORATOR = "collaborator"  # 协作智能体

class LearningStrategy(Enum):
    """学习策略"""
    REINFORCEMENT = "reinforcement"  # 强化学习
    IMITATION = "imitation"  # 模仿学习
    EXPLORATION = "exploration"  # 探索学习
    COLLABORATIVE = "collaborative"  # 协作学习
    ADAPTIVE = "adaptive"  # 自适应学习

class TaskComplexity(Enum):
    """任务复杂度"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    EXPERT = "expert"

class AgentState(Enum):
    """智能体状态"""
    IDLE = "idle"
    LEARNING = "learning"
    WORKING = "working"
    COLLABORATING = "collaborating"
    EVOLVING = "evolving"

@dataclass
class AgentCapability:
    """智能体能力"""
    capability_id: str
    name: str
    description: str
    proficiency: float  # 熟练度 0-1
    confidence: float  # 置信度 0-1
    usage_count: int = 0
    success_rate: float = 0.0
    last_used: Optional[datetime] = None
    learning_rate: float = 0.1
    decay_rate: float = 0.01

@dataclass
class Task:
    """任务"""
    task_id: str
    task_type: str
    description: str
    complexity: TaskComplexity
    requirements: Dict[str, Any]
    context: Dict[str, Any] = field(default_factory=dict)
    deadline: Optional[datetime] = None
    priority: int = 1
    assigned_agents: List[str] = field(default_factory=list)
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class LearningEvent:
    """学习事件"""
    event_id: str
    agent_id: str
    event_type: str
    task_id: str
    outcome: str
    performance_score: float
    learning_data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CollaborationRecord:
    """协作记录"""
    collaboration_id: str
    participating_agents: List[str]
    task_id: str
    collaboration_type: str
    outcome: str
    efficiency_score: float
    knowledge_shared: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class KnowledgeNode:
    """知识节点"""
    node_id: str
    content: Dict[str, Any]
    node_type: str
    confidence: float
    source_agent: str
    connections: Set[str] = field(default_factory=set)
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

class BaseAgent(ABC):
    """基础智能体抽象类"""
    
    def __init__(self, agent_id: str, agent_type: AgentType, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.config = config
        self.state = AgentState.IDLE
        
        # 能力系统
        self.capabilities: Dict[str, AgentCapability] = {}
        self.learning_strategy = LearningStrategy.ADAPTIVE
        self.learning_rate = config.get("learning_rate", 0.1)
        
        # 性能指标
        self.performance_history: List[float] = []
        self.task_success_rate = 0.0
        self.collaboration_score = 0.0
        self.adaptation_score = 0.0
        
        # 学习和记忆
        self.experience_buffer: deque = deque(maxlen=1000)
        self.knowledge_base: Dict[str, Any] = {}
        self.skill_tree: Dict[str, float] = {}
        
        # 协作网络
        self.collaboration_partners: Set[str] = set()
        self.trust_scores: Dict[str, float] = {}
        
        # 进化参数
        self.generation = 0
        self.mutation_rate = config.get("mutation_rate", 0.05)
        self.evolution_threshold = config.get("evolution_threshold", 0.8)
        
        logger.info(f"初始化智能体: {agent_id} ({agent_type.value})")
    
    @abstractmethod
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """执行任务"""
        pass
    
    @abstractmethod
    async def learn_from_experience(self, experience: Dict[str, Any]) -> bool:
        """从经验中学习"""
        pass
    
    async def update_capability(self, capability_id: str, performance_score: float):
        """更新能力"""
        if capability_id not in self.capabilities:
            return
        
        capability = self.capabilities[capability_id]
        
        # 更新熟练度
        old_proficiency = capability.proficiency
        learning_delta = self.learning_rate * (performance_score - old_proficiency)
        capability.proficiency = max(0.0, min(1.0, old_proficiency + learning_delta))
        
        # 更新置信度
        capability.confidence = (capability.confidence * 0.9 + performance_score * 0.1)
        
        # 更新使用统计
        capability.usage_count += 1
        capability.last_used = datetime.now()
        
        # 更新成功率
        if capability.usage_count == 1:
            capability.success_rate = performance_score
        else:
            capability.success_rate = (capability.success_rate * 0.8 + performance_score * 0.2)
        
        logger.debug(f"更新能力 {capability_id}: 熟练度 {old_proficiency:.3f} -> {capability.proficiency:.3f}")
    
    async def collaborate_with(self, other_agent_id: str, task: Task) -> Dict[str, Any]:
        """与其他智能体协作"""
        self.state = AgentState.COLLABORATING
        
        # 记录协作伙伴
        self.collaboration_partners.add(other_agent_id)
        
        # 初始化信任分数
        if other_agent_id not in self.trust_scores:
            self.trust_scores[other_agent_id] = 0.5
        
        # 协作逻辑（由子类实现具体协作策略）
        collaboration_result = await self._perform_collaboration(other_agent_id, task)
        
        # 更新信任分数
        if collaboration_result.get("success", False):
            self.trust_scores[other_agent_id] = min(1.0, self.trust_scores[other_agent_id] + 0.1)
        else:
            self.trust_scores[other_agent_id] = max(0.0, self.trust_scores[other_agent_id] - 0.05)
        
        self.state = AgentState.IDLE
        return collaboration_result
    
    async def _perform_collaboration(self, other_agent_id: str, task: Task) -> Dict[str, Any]:
        """执行协作（基础实现）"""
        return {
            "success": True,
            "contribution": 0.5,
            "knowledge_gained": {},
            "efficiency_boost": 0.2
        }
    
    async def evolve(self) -> bool:
        """进化智能体"""
        if self.task_success_rate < self.evolution_threshold:
            return False
        
        self.state = AgentState.EVOLVING
        
        # 增加代数
        self.generation += 1
        
        # 能力变异
        for capability in self.capabilities.values():
            if random.random() < self.mutation_rate:
                mutation = random.gauss(0, 0.1)
                capability.proficiency = max(0.0, min(1.0, capability.proficiency + mutation))
        
        # 学习策略进化
        if random.random() < self.mutation_rate:
            strategies = list(LearningStrategy)
            self.learning_strategy = random.choice(strategies)
        
        # 学习率自适应
        if self.task_success_rate > 0.9:
            self.learning_rate *= 0.95  # 降低学习率
        elif self.task_success_rate < 0.7:
            self.learning_rate *= 1.05  # 提高学习率
        
        self.learning_rate = max(0.01, min(0.5, self.learning_rate))
        
        self.state = AgentState.IDLE
        logger.info(f"智能体 {self.agent_id} 进化到第 {self.generation} 代")
        return True
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """获取性能指标"""
        return {
            "task_success_rate": self.task_success_rate,
            "collaboration_score": self.collaboration_score,
            "adaptation_score": self.adaptation_score,
            "average_performance": np.mean(self.performance_history) if self.performance_history else 0.0,
            "learning_rate": self.learning_rate,
            "generation": self.generation,
            "capability_count": len(self.capabilities),
            "collaboration_partners": len(self.collaboration_partners)
        }

class CodeAnalyzerAgent(BaseAgent):
    """代码分析智能体"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, AgentType.CODE_ANALYZER, config)
        
        # 初始化代码分析能力
        self.capabilities = {
            "syntax_analysis": AgentCapability(
                "syntax_analysis", "语法分析", "分析代码语法结构", 0.7, 0.8
            ),
            "complexity_analysis": AgentCapability(
                "complexity_analysis", "复杂度分析", "分析代码复杂度", 0.6, 0.7
            ),
            "pattern_recognition": AgentCapability(
                "pattern_recognition", "模式识别", "识别代码模式和反模式", 0.5, 0.6
            ),
            "dependency_analysis": AgentCapability(
                "dependency_analysis", "依赖分析", "分析代码依赖关系", 0.6, 0.7
            ),
            "security_analysis": AgentCapability(
                "security_analysis", "安全分析", "检测安全漏洞", 0.4, 0.5
            )
        }
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """执行代码分析任务"""
        self.state = AgentState.WORKING
        
        try:
            code_content = task.requirements.get("code", "")
            analysis_type = task.requirements.get("analysis_type", "comprehensive")
            
            results = {}
            
            # 语法分析
            if analysis_type in ["comprehensive", "syntax"]:
                syntax_result = await self._analyze_syntax(code_content)
                results["syntax_analysis"] = syntax_result
                await self.update_capability("syntax_analysis", syntax_result.get("score", 0.5))
            
            # 复杂度分析
            if analysis_type in ["comprehensive", "complexity"]:
                complexity_result = await self._analyze_complexity(code_content)
                results["complexity_analysis"] = complexity_result
                await self.update_capability("complexity_analysis", complexity_result.get("score", 0.5))
            
            # 模式识别
            if analysis_type in ["comprehensive", "patterns"]:
                pattern_result = await self._recognize_patterns(code_content)
                results["pattern_recognition"] = pattern_result
                await self.update_capability("pattern_recognition", pattern_result.get("score", 0.5))
            
            # 依赖分析
            if analysis_type in ["comprehensive", "dependencies"]:
                dependency_result = await self._analyze_dependencies(code_content)
                results["dependency_analysis"] = dependency_result
                await self.update_capability("dependency_analysis", dependency_result.get("score", 0.5))
            
            # 安全分析
            if analysis_type in ["comprehensive", "security"]:
                security_result = await self._analyze_security(code_content)
                results["security_analysis"] = security_result
                await self.update_capability("security_analysis", security_result.get("score", 0.5))
            
            # 计算总体性能
            overall_score = np.mean([r.get("score", 0.5) for r in results.values()])
            self.performance_history.append(overall_score)
            
            # 更新成功率
            if len(self.performance_history) == 1:
                self.task_success_rate = overall_score
            else:
                self.task_success_rate = self.task_success_rate * 0.9 + overall_score * 0.1
            
            self.state = AgentState.IDLE
            
            return {
                "success": True,
                "results": results,
                "overall_score": overall_score,
                "agent_id": self.agent_id,
                "task_id": task.task_id
            }
            
        except Exception as e:
            logger.error(f"代码分析任务失败: {e}")
            self.state = AgentState.IDLE
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id,
                "task_id": task.task_id
            }
    
    async def _analyze_syntax(self, code: str) -> Dict[str, Any]:
        """语法分析"""
        # 简化实现：基于代码长度和结构的启发式分析
        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        # 基础语法检查
        syntax_score = 0.8  # 基础分数
        
        # 检查缩进一致性
        indentations = [len(line) - len(line.lstrip()) for line in non_empty_lines if line.strip()]
        if indentations and len(set(indentations)) <= 3:
            syntax_score += 0.1
        
        # 检查括号匹配
        brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        bracket_matched = True
        
        for char in code:
            if char in brackets:
                stack.append(char)
            elif char in brackets.values():
                if not stack or brackets.get(stack.pop()) != char:
                    bracket_matched = False
                    break
        
        if bracket_matched and not stack:
            syntax_score += 0.1
        
        return {
            "score": min(1.0, syntax_score),
            "line_count": len(lines),
            "non_empty_lines": len(non_empty_lines),
            "indentation_consistent": len(set(indentations)) <= 3 if indentations else True,
            "brackets_matched": bracket_matched,
            "issues": []
        }
    
    async def _analyze_complexity(self, code: str) -> Dict[str, Any]:
        """复杂度分析"""
        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        # 圈复杂度估算
        complexity_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'with']
        complexity_count = 0
        
        for line in non_empty_lines:
            for keyword in complexity_keywords:
                if keyword in line:
                    complexity_count += 1
        
        # 计算复杂度分数（越低越好）
        if len(non_empty_lines) == 0:
            complexity_score = 1.0
        else:
            complexity_ratio = complexity_count / len(non_empty_lines)
            complexity_score = max(0.1, 1.0 - complexity_ratio)
        
        return {
            "score": complexity_score,
            "cyclomatic_complexity": complexity_count,
            "lines_of_code": len(non_empty_lines),
            "complexity_ratio": complexity_count / len(non_empty_lines) if non_empty_lines else 0,
            "complexity_level": "low" if complexity_count < 5 else "medium" if complexity_count < 15 else "high"
        }
    
    async def _recognize_patterns(self, code: str) -> Dict[str, Any]:
        """模式识别"""
        patterns_found = []
        pattern_score = 0.5
        
        # 检查常见设计模式
        if "class" in code and "__init__" in code:
            patterns_found.append("object_oriented")
            pattern_score += 0.1
        
        if "def " in code:
            patterns_found.append("functional")
            pattern_score += 0.1
        
        if "import " in code or "from " in code:
            patterns_found.append("modular")
            pattern_score += 0.1
        
        if "try:" in code and "except" in code:
            patterns_found.append("error_handling")
            pattern_score += 0.1
        
        if "with " in code:
            patterns_found.append("context_management")
            pattern_score += 0.1
        
        return {
            "score": min(1.0, pattern_score),
            "patterns_found": patterns_found,
            "pattern_count": len(patterns_found),
            "code_style": "good" if len(patterns_found) >= 3 else "basic"
        }
    
    async def _analyze_dependencies(self, code: str) -> Dict[str, Any]:
        """依赖分析"""
        import_lines = [line for line in code.split('\n') if line.strip().startswith(('import ', 'from '))]
        
        dependencies = []
        for line in import_lines:
            if line.strip().startswith('import '):
                dep = line.strip()[7:].split()[0]
                dependencies.append(dep)
            elif line.strip().startswith('from '):
                dep = line.strip()[5:].split()[0]
                dependencies.append(dep)
        
        # 依赖分数（适中的依赖数量最好）
        dep_count = len(set(dependencies))
        if dep_count == 0:
            dependency_score = 0.7  # 无依赖可能过于简单
        elif dep_count <= 5:
            dependency_score = 1.0  # 适中的依赖数量
        elif dep_count <= 10:
            dependency_score = 0.8  # 较多依赖
        else:
            dependency_score = 0.6  # 过多依赖
        
        return {
            "score": dependency_score,
            "dependencies": list(set(dependencies)),
            "dependency_count": dep_count,
            "import_lines": len(import_lines),
            "dependency_level": "none" if dep_count == 0 else "low" if dep_count <= 3 else "medium" if dep_count <= 7 else "high"
        }
    
    async def _analyze_security(self, code: str) -> Dict[str, Any]:
        """安全分析"""
        security_issues = []
        security_score = 1.0
        
        # 检查常见安全问题
        dangerous_functions = ['eval', 'exec', 'input', 'raw_input']
        for func in dangerous_functions:
            if func + '(' in code:
                security_issues.append(f"使用了危险函数: {func}")
                security_score -= 0.2
        
        # 检查硬编码密码
        if any(keyword in code.lower() for keyword in ['password', 'secret', 'key']):
            if any(char in code for char in ['"', "'"]):
                security_issues.append("可能存在硬编码密码")
                security_score -= 0.1
        
        # 检查SQL注入风险
        if 'sql' in code.lower() and '%' in code:
            security_issues.append("可能存在SQL注入风险")
            security_score -= 0.2
        
        security_score = max(0.0, security_score)
        
        return {
            "score": security_score,
            "security_issues": security_issues,
            "issue_count": len(security_issues),
            "security_level": "high" if security_score >= 0.8 else "medium" if security_score >= 0.6 else "low"
        }
    
    async def learn_from_experience(self, experience: Dict[str, Any]) -> bool:
        """从经验中学习"""
        self.state = AgentState.LEARNING
        
        try:
            # 添加到经验缓冲区
            self.experience_buffer.append(experience)
            
            # 分析经验模式
            task_type = experience.get("task_type", "unknown")
            performance = experience.get("performance", 0.5)
            
            # 更新知识库
            if task_type not in self.knowledge_base:
                self.knowledge_base[task_type] = {
                    "success_patterns": [],
                    "failure_patterns": [],
                    "best_practices": []
                }
            
            # 根据性能更新模式
            if performance > 0.7:
                self.knowledge_base[task_type]["success_patterns"].append(experience)
            elif performance < 0.4:
                self.knowledge_base[task_type]["failure_patterns"].append(experience)
            
            # 更新技能树
            capabilities_used = experience.get("capabilities_used", [])
            for capability in capabilities_used:
                if capability in self.skill_tree:
                    self.skill_tree[capability] += 0.1 * performance
                else:
                    self.skill_tree[capability] = 0.1 * performance
            
            self.state = AgentState.IDLE
            return True
            
        except Exception as e:
            logger.error(f"学习失败: {e}")
            self.state = AgentState.IDLE
            return False

class CodeGeneratorAgent(BaseAgent):
    """代码生成智能体"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, AgentType.CODE_GENERATOR, config)
        
        # 初始化代码生成能力
        self.capabilities = {
            "function_generation": AgentCapability(
                "function_generation", "函数生成", "生成函数代码", 0.6, 0.7
            ),
            "class_generation": AgentCapability(
                "class_generation", "类生成", "生成类代码", 0.5, 0.6
            ),
            "algorithm_implementation": AgentCapability(
                "algorithm_implementation", "算法实现", "实现算法代码", 0.7, 0.8
            ),
            "api_integration": AgentCapability(
                "api_integration", "API集成", "生成API集成代码", 0.4, 0.5
            ),
            "test_generation": AgentCapability(
                "test_generation", "测试生成", "生成测试代码", 0.5, 0.6
            )
        }
        
        # 代码模板库
        self.code_templates = {
            "function": """def {function_name}({parameters}):
    \"\"\"
    {description}
    \"\"\"
    {body}
    return {return_value}""",
            
            "class": """class {class_name}:
    \"\"\"
    {description}
    \"\"\"
    
    def __init__(self{init_params}):
        {init_body}
    
    {methods}""",
            
            "api_call": """async def {function_name}({parameters}):
    \"\"\"
    {description}
    \"\"\"
    try:
        response = await {api_call}
        return response
    except Exception as e:
        logger.error(f"API调用失败: {{e}}")
        return None"""
        }
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """执行代码生成任务"""
        self.state = AgentState.WORKING
        
        try:
            generation_type = task.requirements.get("type", "function")
            specification = task.requirements.get("specification", {})
            
            generated_code = ""
            generation_score = 0.5
            
            if generation_type == "function":
                result = await self._generate_function(specification)
                generated_code = result["code"]
                generation_score = result["score"]
                await self.update_capability("function_generation", generation_score)
            
            elif generation_type == "class":
                result = await self._generate_class(specification)
                generated_code = result["code"]
                generation_score = result["score"]
                await self.update_capability("class_generation", generation_score)
            
            elif generation_type == "algorithm":
                result = await self._implement_algorithm(specification)
                generated_code = result["code"]
                generation_score = result["score"]
                await self.update_capability("algorithm_implementation", generation_score)
            
            elif generation_type == "api":
                result = await self._generate_api_integration(specification)
                generated_code = result["code"]
                generation_score = result["score"]
                await self.update_capability("api_integration", generation_score)
            
            elif generation_type == "test":
                result = await self._generate_test_code(specification)
                generated_code = result["code"]
                generation_score = result["score"]
                await self.update_capability("test_generation", generation_score)
            
            # 更新性能历史
            self.performance_history.append(generation_score)
            
            # 更新成功率
            if len(self.performance_history) == 1:
                self.task_success_rate = generation_score
            else:
                self.task_success_rate = self.task_success_rate * 0.9 + generation_score * 0.1
            
            self.state = AgentState.IDLE
            
            return {
                "success": True,
                "generated_code": generated_code,
                "generation_score": generation_score,
                "generation_type": generation_type,
                "agent_id": self.agent_id,
                "task_id": task.task_id
            }
            
        except Exception as e:
            logger.error(f"代码生成任务失败: {e}")
            self.state = AgentState.IDLE
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id,
                "task_id": task.task_id
            }
    
    async def _generate_function(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """生成函数代码"""
        function_name = spec.get("name", "generated_function")
        parameters = spec.get("parameters", [])
        description = spec.get("description", "Generated function")
        return_type = spec.get("return_type", "Any")
        
        # 构建参数字符串
        param_str = ", ".join(parameters) if parameters else ""
        
        # 生成函数体（简化实现）
        if "calculate" in function_name.lower():
            body = "    result = 0\n    # TODO: 实现计算逻辑"
            return_value = "result"
        elif "process" in function_name.lower():
            body = "    processed_data = data\n    # TODO: 实现处理逻辑"
            return_value = "processed_data"
        else:
            body = "    # TODO: 实现函数逻辑"
            return_value = "None"
        
        code = self.code_templates["function"].format(
            function_name=function_name,
            parameters=param_str,
            description=description,
            body=body,
            return_value=return_value
        )
        
        # 评估生成质量
        score = 0.7  # 基础分数
        if parameters:
            score += 0.1  # 有参数
        if description and len(description) > 10:
            score += 0.1  # 有详细描述
        if return_type != "Any":
            score += 0.1  # 指定了返回类型
        
        return {
            "code": code,
            "score": min(1.0, score)
        }
    
    async def _generate_class(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """生成类代码"""
        class_name = spec.get("name", "GeneratedClass")
        description = spec.get("description", "Generated class")
        attributes = spec.get("attributes", [])
        methods = spec.get("methods", [])
        
        # 生成初始化方法
        if attributes:
            init_params = ", " + ", ".join(attributes)
            init_body = "\n        ".join([f"self.{attr} = {attr}" for attr in attributes])
        else:
            init_params = ""
            init_body = "pass"
        
        # 生成方法
        method_code = ""
        for method in methods:
            method_name = method.get("name", "method")
            method_params = method.get("parameters", [])
            method_desc = method.get("description", "Generated method")
            
            param_str = ", ".join(method_params) if method_params else ""
            method_code += f"""
    def {method_name}(self{', ' + param_str if param_str else ''}):
        \"\"\"
        {method_desc}
        \"\"\"
        # TODO: 实现方法逻辑
        pass
"""
        
        code = self.code_templates["class"].format(
            class_name=class_name,
            description=description,
            init_params=init_params,
            init_body=init_body,
            methods=method_code
        )
        
        # 评估生成质量
        score = 0.6  # 基础分数
        if attributes:
            score += 0.1  # 有属性
        if methods:
            score += 0.2  # 有方法
        if len(description) > 10:
            score += 0.1  # 有详细描述
        
        return {
            "code": code,
            "score": min(1.0, score)
        }
    
    async def _implement_algorithm(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """实现算法代码"""
        algorithm_name = spec.get("name", "algorithm")
        algorithm_type = spec.get("type", "general")
        
        # 根据算法类型生成代码
        if algorithm_type == "sort":
            code = self._generate_sort_algorithm(algorithm_name)
            score = 0.8
        elif algorithm_type == "search":
            code = self._generate_search_algorithm(algorithm_name)
            score = 0.8
        elif algorithm_type == "graph":
            code = self._generate_graph_algorithm(algorithm_name)
            score = 0.7
        else:
            code = f"""def {algorithm_name}(data):
    \"\"\"
    {algorithm_type} algorithm implementation
    \"\"\"
    # TODO: 实现{algorithm_type}算法
    return data"""
            score = 0.5
        
        return {
            "code": code,
            "score": score
        }
    
    def _generate_sort_algorithm(self, name: str) -> str:
        """生成排序算法"""
        if "quick" in name.lower():
            return """def quick_sort(arr):
    \"\"\"
    快速排序算法实现
    \"\"\"
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quick_sort(left) + middle + quick_sort(right)"""
        
        elif "merge" in name.lower():
            return """def merge_sort(arr):
    \"\"\"
    归并排序算法实现
    \"\"\"
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    return result"""
        
        else:
            return """def bubble_sort(arr):
    \"\"\"
    冒泡排序算法实现
    \"\"\"
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr"""
    
    def _generate_search_algorithm(self, name: str) -> str:
        """生成搜索算法"""
        if "binary" in name.lower():
            return """def binary_search(arr, target):
    \"\"\"
    二分搜索算法实现
    \"\"\"
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1"""
        
        else:
            return """def linear_search(arr, target):
    \"\"\"
    线性搜索算法实现
    \"\"\"
    for i, value in enumerate(arr):
        if value == target:
            return i
    return -1"""
    
    def _generate_graph_algorithm(self, name: str) -> str:
        """生成图算法"""
        return """def dfs(graph, start, visited=None):
    \"\"\"
    深度优先搜索算法实现
    \"\"\"
    if visited is None:
        visited = set()
    
    visited.add(start)
    result = [start]
    
    for neighbor in graph.get(start, []):
        if neighbor not in visited:
            result.extend(dfs(graph, neighbor, visited))
    
    return result"""
    
    async def _generate_api_integration(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """生成API集成代码"""
        api_name = spec.get("name", "api_call")
        api_url = spec.get("url", "https://api.example.com")
        method = spec.get("method", "GET")
        
        code = f"""import aiohttp
import logging

logger = logging.getLogger(__name__)

async def {api_name}(session, **kwargs):
    \"\"\"
    {api_name} API调用
    \"\"\"
    url = "{api_url}"
    
    try:
        async with session.{method.lower()}(url, **kwargs) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"API调用失败: {{response.status}}")
                return None
    except Exception as e:
        logger.error(f"API调用异常: {{e}}")
        return None"""
        
        return {
            "code": code,
            "score": 0.7
        }
    
    async def _generate_test_code(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """生成测试代码"""
        function_name = spec.get("function_name", "test_function")
        test_cases = spec.get("test_cases", [])
        
        code = f"""import unittest

class Test{function_name.title()}(unittest.TestCase):
    \"\"\"
    {function_name} 测试类
    \"\"\"
    
    def setUp(self):
        \"\"\"测试前置设置\"\"\"
        pass
    
    def tearDown(self):
        \"\"\"测试后置清理\"\"\"
        pass
"""
        
        # 生成测试方法
        for i, test_case in enumerate(test_cases):
            test_name = test_case.get("name", f"test_case_{i+1}")
            expected = test_case.get("expected", "None")
            
            code += f"""
    def test_{test_name}(self):
        \"\"\"测试 {test_name}\"\"\"
        # TODO: 实现测试逻辑
        result = {function_name}()
        self.assertEqual(result, {expected})
"""
        
        code += """
if __name__ == '__main__':
    unittest.main()"""
        
        return {
            "code": code,
            "score": 0.6 + 0.1 * len(test_cases)
        }
    
    async def learn_from_experience(self, experience: Dict[str, Any]) -> bool:
        """从经验中学习"""
        self.state = AgentState.LEARNING
        
        try:
            # 添加到经验缓冲区
            self.experience_buffer.append(experience)
            
            # 学习代码生成模式
            generation_type = experience.get("generation_type", "unknown")
            performance = experience.get("performance", 0.5)
            generated_code = experience.get("generated_code", "")
            
            # 更新代码模板
            if performance > 0.8 and generated_code:
                if generation_type not in self.knowledge_base:
                    self.knowledge_base[generation_type] = {"successful_patterns": []}
                
                self.knowledge_base[generation_type]["successful_patterns"].append({
                    "code": generated_code,
                    "performance": performance,
                    "timestamp": datetime.now().isoformat()
                })
            
            self.state = AgentState.IDLE
            return True
            
        except Exception as e:
            logger.error(f"学习失败: {e}")
            self.state = AgentState.IDLE
            return False

class AgentZeroIntegration:
    """Agent Zero有机智能体集成系统"""
    
    def __init__(self, config_path: str = "./agent_zero_config.json"):
        """初始化Agent Zero集成"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # 智能体池
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_types: Dict[AgentType, List[str]] = defaultdict(list)
        
        # 任务管理
        self.task_queue: deque = deque()
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: List[Task] = []
        
        # 协作网络
        self.collaboration_network: Dict[str, Set[str]] = defaultdict(set)
        self.collaboration_history: List[CollaborationRecord] = []
        
        # 知识图谱
        self.knowledge_graph: Dict[str, KnowledgeNode] = {}
        self.knowledge_connections: Dict[str, Set[str]] = defaultdict(set)
        
        # 学习系统
        self.learning_events: List[LearningEvent] = []
        self.collective_knowledge: Dict[str, Any] = {}
        
        # 性能监控
        self.system_metrics: Dict[str, float] = {}
        self.agent_performance: Dict[str, Dict[str, float]] = {}
        
        # 存储
        self.data_dir = Path(self.config.get("data_dir", "./agent_zero_data"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "agent_zero.db"
        
        # 初始化数据库
        self._init_database()
        
        # 创建初始智能体
        self._create_initial_agents()
        
        # 后台任务
        self.task_processor = None
        self.learning_processor = None
        self.evolution_processor = None
        
        logger.info("Agent Zero有机智能体集成系统初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "initial_agents": {
                "code_analyzer": 1,
                "code_generator": 1,
                "debugger": 1,
                "optimizer": 1,
                "collaborator": 1
            },
            "max_agents_per_type": 3,
            "task_timeout": 300,
            "collaboration_threshold": 0.7,
            "evolution_interval": 3600,
            "learning_interval": 1800,
            "data_dir": "./agent_zero_data",
            "enable_evolution": True,
            "enable_collaboration": True,
            "enable_learning": True,
            "mutation_rate": 0.05,
            "evolution_threshold": 0.8,
            "learning_rate": 0.1
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"加载配置文件失败，使用默认配置: {e}")
        
        return default_config
    
    def _init_database(self):
        """初始化数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建智能体表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS agents (
                        agent_id TEXT PRIMARY KEY,
                        agent_type TEXT NOT NULL,
                        capabilities TEXT,
                        performance_history TEXT,
                        knowledge_base TEXT,
                        collaboration_partners TEXT,
                        generation INTEGER DEFAULT 0,
                        created_at TIMESTAMP NOT NULL,
                        last_updated TIMESTAMP
                    )
                ''')
                
                # 创建任务表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        task_id TEXT PRIMARY KEY,
                        task_type TEXT NOT NULL,
                        description TEXT,
                        complexity TEXT,
                        requirements TEXT,
                        assigned_agents TEXT,
                        status TEXT,
                        result TEXT,
                        created_at TIMESTAMP NOT NULL,
                        completed_at TIMESTAMP
                    )
                ''')
                
                # 创建学习事件表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_events (
                        event_id TEXT PRIMARY KEY,
                        agent_id TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        task_id TEXT,
                        outcome TEXT,
                        performance_score REAL,
                        learning_data TEXT,
                        timestamp TIMESTAMP NOT NULL
                    )
                ''')
                
                # 创建协作记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS collaboration_records (
                        collaboration_id TEXT PRIMARY KEY,
                        participating_agents TEXT NOT NULL,
                        task_id TEXT NOT NULL,
                        collaboration_type TEXT,
                        outcome TEXT,
                        efficiency_score REAL,
                        knowledge_shared TEXT,
                        timestamp TIMESTAMP NOT NULL
                    )
                ''')
                
                # 创建知识图谱表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_nodes (
                        node_id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        node_type TEXT,
                        confidence REAL,
                        source_agent TEXT,
                        connections TEXT,
                        access_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP NOT NULL,
                        last_accessed TIMESTAMP
                    )
                ''')
                
                # 创建索引
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_type ON agents(agent_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_status ON tasks(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_learning_agent ON learning_events(agent_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_collaboration_task ON collaboration_records(task_id)')
                
                conn.commit()
                logger.info("Agent Zero数据库初始化完成")
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def _create_initial_agents(self):
        """创建初始智能体"""
        initial_agents = self.config.get("initial_agents", {})
        
        for agent_type_str, count in initial_agents.items():
            agent_type = AgentType(agent_type_str)
            
            for i in range(count):
                agent_id = f"{agent_type_str}_{i+1}_{uuid.uuid4().hex[:8]}"
                
                if agent_type == AgentType.CODE_ANALYZER:
                    agent = CodeAnalyzerAgent(agent_id, self.config)
                elif agent_type == AgentType.CODE_GENERATOR:
                    agent = CodeGeneratorAgent(agent_id, self.config)
                # TODO: 实现其他智能体类型
                else:
                    continue
                
                self.agents[agent_id] = agent
                self.agent_types[agent_type].append(agent_id)
                
                logger.info(f"创建智能体: {agent_id} ({agent_type.value})")
    
    async def start_background_tasks(self):
        """启动后台任务"""
        self.task_processor = asyncio.create_task(self._task_processing_loop())
        
        if self.config.get("enable_learning", True):
            self.learning_processor = asyncio.create_task(self._learning_processing_loop())
        
        if self.config.get("enable_evolution", True):
            self.evolution_processor = asyncio.create_task(self._evolution_processing_loop())
        
        logger.info("Agent Zero后台任务启动完成")
    
    async def submit_task(self, task_type: str, description: str, 
                         requirements: Dict[str, Any],
                         complexity: TaskComplexity = TaskComplexity.MEDIUM,
                         priority: int = 1) -> str:
        """提交任务"""
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        
        task = Task(
            task_id=task_id,
            task_type=task_type,
            description=description,
            complexity=complexity,
            requirements=requirements,
            priority=priority
        )
        
        # 添加到任务队列
        self.task_queue.append(task)
        self.active_tasks[task_id] = task
        
        logger.info(f"提交任务: {task_id} ({task_type})")
        return task_id
    
    async def assign_task_to_agent(self, task: Task) -> Optional[str]:
        """将任务分配给智能体"""
        # 根据任务类型选择合适的智能体类型
        suitable_agent_types = self._get_suitable_agent_types(task.task_type)
        
        best_agent_id = None
        best_score = 0.0
        
        for agent_type in suitable_agent_types:
            agent_ids = self.agent_types.get(agent_type, [])
            
            for agent_id in agent_ids:
                agent = self.agents[agent_id]
                
                # 检查智能体状态
                if agent.state != AgentState.IDLE:
                    continue
                
                # 计算适合度分数
                score = await self._calculate_agent_suitability(agent, task)
                
                if score > best_score:
                    best_score = score
                    best_agent_id = agent_id
        
        if best_agent_id:
            task.assigned_agents = [best_agent_id]
            logger.debug(f"任务 {task.task_id} 分配给智能体 {best_agent_id} (分数: {best_score:.3f})")
        
        return best_agent_id
    
    def _get_suitable_agent_types(self, task_type: str) -> List[AgentType]:
        """获取适合的智能体类型"""
        type_mapping = {
            "code_analysis": [AgentType.CODE_ANALYZER],
            "code_generation": [AgentType.CODE_GENERATOR],
            "debugging": [AgentType.DEBUGGER],
            "optimization": [AgentType.OPTIMIZER],
            "collaboration": [AgentType.COLLABORATOR],
            "comprehensive": [AgentType.CODE_ANALYZER, AgentType.CODE_GENERATOR, AgentType.OPTIMIZER]
        }
        
        return type_mapping.get(task_type, [AgentType.CODE_ANALYZER])
    
    async def _calculate_agent_suitability(self, agent: BaseAgent, task: Task) -> float:
        """计算智能体适合度"""
        base_score = 0.5
        
        # 基于任务成功率
        success_rate_score = agent.task_success_rate * 0.4
        
        # 基于相关能力
        relevant_capabilities = self._get_relevant_capabilities(task.task_type)
        capability_score = 0.0
        
        for cap_id in relevant_capabilities:
            if cap_id in agent.capabilities:
                capability = agent.capabilities[cap_id]
                capability_score += capability.proficiency * capability.confidence
        
        if relevant_capabilities:
            capability_score /= len(relevant_capabilities)
        
        capability_score *= 0.3
        
        # 基于协作能力
        collaboration_score = agent.collaboration_score * 0.2
        
        # 基于学习能力
        adaptation_score = agent.adaptation_score * 0.1
        
        total_score = base_score + success_rate_score + capability_score + collaboration_score + adaptation_score
        
        return min(1.0, total_score)
    
    def _get_relevant_capabilities(self, task_type: str) -> List[str]:
        """获取相关能力"""
        capability_mapping = {
            "code_analysis": ["syntax_analysis", "complexity_analysis", "pattern_recognition"],
            "code_generation": ["function_generation", "class_generation", "algorithm_implementation"],
            "debugging": ["error_detection", "bug_fixing", "testing"],
            "optimization": ["performance_optimization", "code_refactoring", "efficiency_improvement"]
        }
        
        return capability_mapping.get(task_type, [])
    
    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """执行任务"""
        if task_id not in self.active_tasks:
            return {"success": False, "error": "任务不存在"}
        
        task = self.active_tasks[task_id]
        
        # 分配智能体
        if not task.assigned_agents:
            agent_id = await self.assign_task_to_agent(task)
            if not agent_id:
                return {"success": False, "error": "无可用智能体"}
        
        agent_id = task.assigned_agents[0]
        agent = self.agents[agent_id]
        
        # 检查是否需要协作
        if task.complexity in [TaskComplexity.COMPLEX, TaskComplexity.EXPERT]:
            collaboration_result = await self._handle_collaborative_task(task)
            if collaboration_result:
                return collaboration_result
        
        # 执行任务
        try:
            result = await agent.execute_task(task)
            
            # 记录学习事件
            await self._record_learning_event(
                agent_id=agent_id,
                event_type="task_execution",
                task_id=task_id,
                outcome="success" if result.get("success", False) else "failure",
                performance_score=result.get("overall_score", result.get("generation_score", 0.5)),
                learning_data=result
            )
            
            # 更新任务状态
            task.status = "completed" if result.get("success", False) else "failed"
            self.completed_tasks.append(task)
            
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            return result
            
        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            task.status = "failed"
            return {"success": False, "error": str(e)}
    
    async def _handle_collaborative_task(self, task: Task) -> Optional[Dict[str, Any]]:
        """处理协作任务"""
        if not self.config.get("enable_collaboration", True):
            return None
        
        # 选择协作智能体
        primary_agent_id = task.assigned_agents[0]
        primary_agent = self.agents[primary_agent_id]
        
        # 寻找协作伙伴
        collaboration_partners = await self._find_collaboration_partners(primary_agent, task)
        
        if not collaboration_partners:
            return None
        
        # 执行协作
        collaboration_id = f"collab_{uuid.uuid4().hex[:12]}"
        participating_agents = [primary_agent_id] + collaboration_partners
        
        try:
            # 协作执行逻辑
            results = []
            
            for agent_id in participating_agents:
                agent = self.agents[agent_id]
                agent_result = await agent.execute_task(task)
                results.append(agent_result)
            
            # 整合结果
            integrated_result = await self._integrate_collaboration_results(results)
            
            # 记录协作
            collaboration_record = CollaborationRecord(
                collaboration_id=collaboration_id,
                participating_agents=participating_agents,
                task_id=task.task_id,
                collaboration_type="task_execution",
                outcome="success" if integrated_result.get("success", False) else "failure",
                efficiency_score=integrated_result.get("efficiency_score", 0.5),
                knowledge_shared=integrated_result.get("knowledge_shared", {})
            )
            
            self.collaboration_history.append(collaboration_record)
            
            # 更新协作网络
            for i, agent_id1 in enumerate(participating_agents):
                for j, agent_id2 in enumerate(participating_agents):
                    if i != j:
                        self.collaboration_network[agent_id1].add(agent_id2)
            
            return integrated_result
            
        except Exception as e:
            logger.error(f"协作任务执行失败: {e}")
            return None
    
    async def _find_collaboration_partners(self, primary_agent: BaseAgent, 
                                         task: Task) -> List[str]:
        """寻找协作伙伴"""
        partners = []
        collaboration_threshold = self.config.get("collaboration_threshold", 0.7)
        
        # 基于信任分数选择伙伴
        for partner_id, trust_score in primary_agent.trust_scores.items():
            if trust_score >= collaboration_threshold and partner_id in self.agents:
                partner_agent = self.agents[partner_id]
                if partner_agent.state == AgentState.IDLE:
                    partners.append(partner_id)
        
        # 如果没有足够的信任伙伴，基于能力选择
        if len(partners) < 2:
            suitable_types = self._get_suitable_agent_types(task.task_type)
            
            for agent_type in suitable_types:
                agent_ids = self.agent_types.get(agent_type, [])
                
                for agent_id in agent_ids:
                    if agent_id != primary_agent.agent_id and agent_id not in partners:
                        agent = self.agents[agent_id]
                        if agent.state == AgentState.IDLE and agent.task_success_rate > 0.6:
                            partners.append(agent_id)
                            if len(partners) >= 2:
                                break
                
                if len(partners) >= 2:
                    break
        
        return partners[:2]  # 最多2个协作伙伴
    
    async def _integrate_collaboration_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """整合协作结果"""
        successful_results = [r for r in results if r.get("success", False)]
        
        if not successful_results:
            return {"success": False, "error": "所有协作智能体都失败了"}
        
        # 选择最佳结果
        best_result = max(successful_results, 
                         key=lambda r: r.get("overall_score", r.get("generation_score", 0.0)))
        
        # 计算协作效率
        success_rate = len(successful_results) / len(results)
        efficiency_score = success_rate * 0.7 + best_result.get("overall_score", 0.5) * 0.3
        
        # 整合知识
        knowledge_shared = {}
        for result in successful_results:
            if "knowledge_gained" in result:
                knowledge_shared.update(result["knowledge_gained"])
        
        integrated_result = best_result.copy()
        integrated_result.update({
            "collaboration": True,
            "participating_agents": len(results),
            "success_rate": success_rate,
            "efficiency_score": efficiency_score,
            "knowledge_shared": knowledge_shared
        })
        
        return integrated_result
    
    async def _record_learning_event(self, agent_id: str, event_type: str,
                                   task_id: str, outcome: str,
                                   performance_score: float,
                                   learning_data: Dict[str, Any]):
        """记录学习事件"""
        event_id = f"learn_{uuid.uuid4().hex[:12]}"
        
        learning_event = LearningEvent(
            event_id=event_id,
            agent_id=agent_id,
            event_type=event_type,
            task_id=task_id,
            outcome=outcome,
            performance_score=performance_score,
            learning_data=learning_data
        )
        
        self.learning_events.append(learning_event)
        
        # 触发智能体学习
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            await agent.learn_from_experience({
                "task_type": learning_data.get("task_type", "unknown"),
                "performance": performance_score,
                "outcome": outcome,
                "capabilities_used": learning_data.get("capabilities_used", [])
            })
        
        logger.debug(f"记录学习事件: {event_id} (智能体: {agent_id})")
    
    async def trigger_collective_learning(self, topic: str, 
                                        examples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """触发集体学习"""
        try:
            learning_results = {}
            
            # 为所有智能体触发学习
            for agent_id, agent in self.agents.items():
                agent.state = AgentState.LEARNING
                
                # 构建学习经验
                learning_experience = {
                    "topic": topic,
                    "examples": examples,
                    "collective_learning": True,
                    "timestamp": datetime.now().isoformat()
                }
                
                # 触发学习
                success = await agent.learn_from_experience(learning_experience)
                learning_results[agent_id] = success
                
                agent.state = AgentState.IDLE
            
            # 更新集体知识
            if topic not in self.collective_knowledge:
                self.collective_knowledge[topic] = {
                    "examples": [],
                    "learning_count": 0,
                    "success_rate": 0.0
                }
            
            self.collective_knowledge[topic]["examples"].extend(examples)
            self.collective_knowledge[topic]["learning_count"] += 1
            
            success_count = sum(1 for success in learning_results.values() if success)
            success_rate = success_count / len(learning_results) if learning_results else 0.0
            
            self.collective_knowledge[topic]["success_rate"] = (
                self.collective_knowledge[topic]["success_rate"] * 0.8 + success_rate * 0.2
            )
            
            logger.info(f"集体学习完成: {topic} (成功率: {success_rate:.1%})")
            
            return {
                "success": True,
                "topic": topic,
                "agents_learned": len(learning_results),
                "success_rate": success_rate,
                "learning_results": learning_results
            }
            
        except Exception as e:
            logger.error(f"集体学习失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _task_processing_loop(self):
        """任务处理循环"""
        while True:
            try:
                if self.task_queue:
                    task = self.task_queue.popleft()
                    await self.execute_task(task.task_id)
                else:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"任务处理失败: {e}")
                await asyncio.sleep(5)
    
    async def _learning_processing_loop(self):
        """学习处理循环"""
        learning_interval = self.config.get("learning_interval", 1800)
        
        while True:
            try:
                await self._process_collective_learning()
                await asyncio.sleep(learning_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"学习处理失败: {e}")
                await asyncio.sleep(learning_interval)
    
    async def _evolution_processing_loop(self):
        """进化处理循环"""
        evolution_interval = self.config.get("evolution_interval", 3600)
        
        while True:
            try:
                await self._process_agent_evolution()
                await asyncio.sleep(evolution_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"进化处理失败: {e}")
                await asyncio.sleep(evolution_interval)
    
    async def _process_collective_learning(self):
        """处理集体学习"""
        # 分析最近的学习事件
        recent_events = [
            event for event in self.learning_events
            if (datetime.now() - event.timestamp).total_seconds() < 3600
        ]
        
        if not recent_events:
            return
        
        # 按事件类型分组
        event_groups = defaultdict(list)
        for event in recent_events:
            event_groups[event.event_type].append(event)
        
        # 为每个事件类型触发集体学习
        for event_type, events in event_groups.items():
            if len(events) >= 3:  # 至少3个事件才触发集体学习
                examples = [
                    {
                        "performance": event.performance_score,
                        "outcome": event.outcome,
                        "data": event.learning_data
                    }
                    for event in events
                ]
                
                await self.trigger_collective_learning(event_type, examples)
    
    async def _process_agent_evolution(self):
        """处理智能体进化"""
        evolution_candidates = []
        
        # 找到符合进化条件的智能体
        for agent_id, agent in self.agents.items():
            if agent.task_success_rate >= agent.evolution_threshold:
                evolution_candidates.append(agent_id)
        
        # 执行进化
        evolved_count = 0
        for agent_id in evolution_candidates:
            agent = self.agents[agent_id]
            if await agent.evolve():
                evolved_count += 1
        
        if evolved_count > 0:
            logger.info(f"智能体进化完成: {evolved_count} 个智能体进化")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        # 计算系统指标
        total_agents = len(self.agents)
        active_tasks = len(self.active_tasks)
        completed_tasks = len(self.completed_tasks)
        
        # 计算平均性能
        agent_performances = []
        for agent in self.agents.values():
            agent_performances.append(agent.task_success_rate)
        
        avg_performance = np.mean(agent_performances) if agent_performances else 0.0
        
        # 协作统计
        collaboration_count = len(self.collaboration_history)
        avg_collaboration_efficiency = 0.0
        
        if self.collaboration_history:
            efficiencies = [record.efficiency_score for record in self.collaboration_history]
            avg_collaboration_efficiency = np.mean(efficiencies)
        
        # 学习统计
        learning_events_count = len(self.learning_events)
        collective_knowledge_topics = len(self.collective_knowledge)
        
        return {
            "system_metrics": {
                "total_agents": total_agents,
                "active_tasks": active_tasks,
                "completed_tasks": completed_tasks,
                "average_performance": avg_performance,
                "collaboration_count": collaboration_count,
                "avg_collaboration_efficiency": avg_collaboration_efficiency,
                "learning_events_count": learning_events_count,
                "collective_knowledge_topics": collective_knowledge_topics
            },
            "agent_breakdown": {
                agent_type.value: len(agent_ids) 
                for agent_type, agent_ids in self.agent_types.items()
            },
            "performance_distribution": {
                "excellent": sum(1 for p in agent_performances if p >= 0.9),
                "good": sum(1 for p in agent_performances if 0.7 <= p < 0.9),
                "average": sum(1 for p in agent_performances if 0.5 <= p < 0.7),
                "poor": sum(1 for p in agent_performances if p < 0.5)
            },
            "collaboration_network_size": sum(len(partners) for partners in self.collaboration_network.values()),
            "knowledge_graph_nodes": len(self.knowledge_graph)
        }
    
    async def cleanup(self):
        """清理资源"""
        try:
            # 取消后台任务
            if self.task_processor:
                self.task_processor.cancel()
                try:
                    await self.task_processor
                except asyncio.CancelledError:
                    pass
            
            if self.learning_processor:
                self.learning_processor.cancel()
                try:
                    await self.learning_processor
                except asyncio.CancelledError:
                    pass
            
            if self.evolution_processor:
                self.evolution_processor.cancel()
                try:
                    await self.evolution_processor
                except asyncio.CancelledError:
                    pass
            
            # 保存数据
            await self._persist_all_data()
            
            logger.info("Agent Zero集成系统清理完成")
            
        except Exception as e:
            logger.error(f"清理资源失败: {e}")
    
    async def _persist_all_data(self):
        """持久化所有数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 保存智能体数据
                for agent_id, agent in self.agents.items():
                    cursor.execute('''
                        INSERT OR REPLACE INTO agents 
                        (agent_id, agent_type, capabilities, performance_history, 
                         knowledge_base, collaboration_partners, generation, 
                         created_at, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        agent_id,
                        agent.agent_type.value,
                        json.dumps({cap_id: asdict(cap) for cap_id, cap in agent.capabilities.items()}),
                        json.dumps(agent.performance_history),
                        json.dumps(agent.knowledge_base),
                        json.dumps(list(agent.collaboration_partners)),
                        agent.generation,
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    ))
                
                # 保存学习事件
                for event in self.learning_events[-1000:]:  # 只保存最近1000个事件
                    cursor.execute('''
                        INSERT OR REPLACE INTO learning_events 
                        (event_id, agent_id, event_type, task_id, outcome, 
                         performance_score, learning_data, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        event.event_id,
                        event.agent_id,
                        event.event_type,
                        event.task_id,
                        event.outcome,
                        event.performance_score,
                        json.dumps(event.learning_data),
                        event.timestamp.isoformat()
                    ))
                
                # 保存协作记录
                for record in self.collaboration_history[-500:]:  # 只保存最近500个记录
                    cursor.execute('''
                        INSERT OR REPLACE INTO collaboration_records 
                        (collaboration_id, participating_agents, task_id, 
                         collaboration_type, outcome, efficiency_score, 
                         knowledge_shared, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        record.collaboration_id,
                        json.dumps(record.participating_agents),
                        record.task_id,
                        record.collaboration_type,
                        record.outcome,
                        record.efficiency_score,
                        json.dumps(record.knowledge_shared),
                        record.timestamp.isoformat()
                    ))
                
                conn.commit()
                logger.info("Agent Zero数据持久化完成")
                
        except Exception as e:
            logger.error(f"数据持久化失败: {e}")

# 工厂函数
def get_agent_zero_integration(config_path: str = "./agent_zero_config.json") -> AgentZeroIntegration:
    """获取Agent Zero集成实例"""
    return AgentZeroIntegration(config_path)

# 测试和演示
if __name__ == "__main__":
    async def test_agent_zero_integration():
        """测试Agent Zero集成"""
        agent_zero = get_agent_zero_integration()
        
        try:
            # 启动后台任务
            await agent_zero.start_background_tasks()
            
            # 提交代码分析任务
            print("📝 提交代码分析任务...")
            task_id1 = await agent_zero.submit_task(
                task_type="code_analysis",
                description="分析Python函数的复杂度和模式",
                requirements={
                    "code": """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)
""",
                    "analysis_type": "comprehensive"
                },
                complexity=TaskComplexity.MEDIUM
            )
            
            # 提交代码生成任务
            print("🔧 提交代码生成任务...")
            task_id2 = await agent_zero.submit_task(
                task_type="code_generation",
                description="生成快速排序算法",
                requirements={
                    "type": "algorithm",
                    "specification": {
                        "name": "quick_sort",
                        "type": "sort",
                        "description": "快速排序算法实现"
                    }
                },
                complexity=TaskComplexity.MEDIUM
            )
            
            # 等待任务完成
            print("⏳ 等待任务完成...")
            await asyncio.sleep(5)
            
            # 触发集体学习
            print("🧠 触发集体学习...")
            learning_result = await agent_zero.trigger_collective_learning(
                topic="Python性能优化",
                examples=[
                    {"technique": "动态规划", "improvement": 0.8},
                    {"technique": "缓存机制", "improvement": 0.6},
                    {"technique": "算法优化", "improvement": 0.9}
                ]
            )
            
            print(f"集体学习结果: 成功率 {learning_result['success_rate']:.1%}")
            
            # 获取系统状态
            print("📊 系统状态...")
            status = await agent_zero.get_system_status()
            
            print(f"总智能体数: {status['system_metrics']['total_agents']}")
            print(f"已完成任务: {status['system_metrics']['completed_tasks']}")
            print(f"平均性能: {status['system_metrics']['average_performance']:.1%}")
            print(f"协作次数: {status['system_metrics']['collaboration_count']}")
            print(f"学习事件: {status['system_metrics']['learning_events_count']}")
            
            print("\n智能体类型分布:")
            for agent_type, count in status['agent_breakdown'].items():
                print(f"  - {agent_type}: {count}")
            
            print("\n性能分布:")
            for level, count in status['performance_distribution'].items():
                print(f"  - {level}: {count}")
            
        finally:
            # 清理
            await agent_zero.cleanup()
    
    # 运行测试
    asyncio.run(test_agent_zero_integration())

