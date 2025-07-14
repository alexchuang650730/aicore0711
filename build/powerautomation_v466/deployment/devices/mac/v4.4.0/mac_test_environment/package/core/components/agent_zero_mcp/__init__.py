"""
Agent Zero 集成模块

有机智能体框架集成到PowerAutomation + ClaudEditor
- 自学习能力: 从经验中持续学习和改进
- 有机适应: 根据环境变化自动调整行为
- 智能进化: 通过反馈循环不断优化性能
- 自主决策: 基于学习的知识进行独立决策

适应率: 85%
学习模式: 有机学习
"""

import asyncio
import json
import logging
import time
import random
import math
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import threading
from pathlib import Path


class LearningMode(Enum):
    """学习模式"""
    SUPERVISED = "supervised"
    UNSUPERVISED = "unsupervised"
    REINFORCEMENT = "reinforcement"
    ORGANIC = "organic"  # 有机学习模式


class AdaptationStrategy(Enum):
    """适应策略"""
    CONSERVATIVE = "conservative"  # 保守适应
    MODERATE = "moderate"  # 适度适应
    AGGRESSIVE = "aggressive"  # 激进适应
    ORGANIC = "organic"  # 有机适应


@dataclass
class Experience:
    """经验数据"""
    id: str
    action: str
    context: Dict[str, Any]
    outcome: str
    success: bool
    reward: float
    timestamp: float
    learning_value: float = 0.0
    
    def __post_init__(self):
        if self.learning_value == 0.0:
            # 基于成功率和奖励计算学习价值
            self.learning_value = (0.7 if self.success else 0.3) * abs(self.reward)


@dataclass
class KnowledgeNode:
    """知识节点"""
    id: str
    concept: str
    confidence: float
    connections: List[str]
    usage_count: int = 0
    last_updated: float = 0.0
    decay_rate: float = 0.01
    
    def __post_init__(self):
        if self.last_updated == 0.0:
            self.last_updated = time.time()


@dataclass
class DecisionContext:
    """决策上下文"""
    situation: str
    available_actions: List[str]
    constraints: Dict[str, Any]
    goals: List[str]
    urgency: float = 0.5  # 0.0 - 1.0
    complexity: float = 0.5  # 0.0 - 1.0


class OrganicLearningEngine:
    """有机学习引擎"""
    
    def __init__(self):
        self.logger = logging.getLogger("AgentZero.Learning")
        
        # 学习参数
        self.learning_rate = 0.1
        self.adaptation_rate = 0.85
        self.exploration_rate = 0.2
        self.decay_factor = 0.95
        
        # 经验存储
        self.experiences: List[Experience] = []
        self.max_experiences = 10000
        
        # 知识图谱
        self.knowledge_graph: Dict[str, KnowledgeNode] = {}
        
        # 学习统计
        self.learning_stats = {
            'total_experiences': 0,
            'successful_adaptations': 0,
            'failed_adaptations': 0,
            'knowledge_nodes': 0,
            'learning_efficiency': 0.0
        }
    
    async def learn_from_experience(self, experience: Experience) -> bool:
        """从经验中学习"""
        try:
            # 存储经验
            self.experiences.append(experience)
            if len(self.experiences) > self.max_experiences:
                self.experiences.pop(0)  # 移除最旧的经验
            
            # 更新知识图谱
            await self._update_knowledge_graph(experience)
            
            # 调整学习参数
            await self._adjust_learning_parameters(experience)
            
            # 更新统计
            self.learning_stats['total_experiences'] += 1
            if experience.success:
                self.learning_stats['successful_adaptations'] += 1
            else:
                self.learning_stats['failed_adaptations'] += 1
            
            # 计算学习效率
            total_adaptations = (
                self.learning_stats['successful_adaptations'] + 
                self.learning_stats['failed_adaptations']
            )
            if total_adaptations > 0:
                self.learning_stats['learning_efficiency'] = (
                    self.learning_stats['successful_adaptations'] / total_adaptations
                )
            
            self.logger.info(f"学习经验: {experience.action}, 成功: {experience.success}")
            return True
            
        except Exception as e:
            self.logger.error(f"学习失败: {e}")
            return False
    
    async def _update_knowledge_graph(self, experience: Experience):
        """更新知识图谱"""
        
        # 提取概念
        concepts = self._extract_concepts(experience)
        
        for concept in concepts:
            node_id = f"concept_{hash(concept) % 10000}"
            
            if node_id in self.knowledge_graph:
                # 更新现有节点
                node = self.knowledge_graph[node_id]
                node.usage_count += 1
                node.last_updated = time.time()
                
                # 基于经验调整置信度
                if experience.success:
                    node.confidence = min(1.0, node.confidence + 0.1)
                else:
                    node.confidence = max(0.0, node.confidence - 0.05)
            else:
                # 创建新节点
                node = KnowledgeNode(
                    id=node_id,
                    concept=concept,
                    confidence=0.7 if experience.success else 0.3,
                    connections=[],
                    usage_count=1
                )
                self.knowledge_graph[node_id] = node
                self.learning_stats['knowledge_nodes'] += 1
        
        # 建立连接
        await self._establish_connections(concepts, experience)
    
    def _extract_concepts(self, experience: Experience) -> List[str]:
        """从经验中提取概念"""
        concepts = []
        
        # 从动作中提取
        concepts.append(experience.action)
        
        # 从上下文中提取
        for key, value in experience.context.items():
            if isinstance(value, str) and len(value) > 2:
                concepts.append(f"{key}:{value}")
        
        # 从结果中提取
        concepts.append(experience.outcome)
        
        return concepts[:5]  # 限制概念数量
    
    async def _establish_connections(self, concepts: List[str], experience: Experience):
        """建立概念连接"""
        
        # 为相关概念建立连接
        for i, concept1 in enumerate(concepts):
            for concept2 in concepts[i+1:]:
                node1_id = f"concept_{hash(concept1) % 10000}"
                node2_id = f"concept_{hash(concept2) % 10000}"
                
                if node1_id in self.knowledge_graph and node2_id in self.knowledge_graph:
                    node1 = self.knowledge_graph[node1_id]
                    node2 = self.knowledge_graph[node2_id]
                    
                    # 建立双向连接
                    if node2_id not in node1.connections:
                        node1.connections.append(node2_id)
                    if node1_id not in node2.connections:
                        node2.connections.append(node1_id)
    
    async def _adjust_learning_parameters(self, experience: Experience):
        """调整学习参数"""
        
        # 基于经验调整学习率
        if experience.success:
            self.learning_rate = min(0.5, self.learning_rate * 1.01)
        else:
            self.learning_rate = max(0.01, self.learning_rate * 0.99)
        
        # 调整探索率
        if len(self.experiences) > 100:
            success_rate = sum(1 for exp in self.experiences[-100:] if exp.success) / 100
            if success_rate > 0.8:
                self.exploration_rate = max(0.05, self.exploration_rate * 0.95)
            elif success_rate < 0.5:
                self.exploration_rate = min(0.5, self.exploration_rate * 1.05)
    
    async def predict_outcome(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """预测行动结果"""
        
        # 查找相似经验
        similar_experiences = self._find_similar_experiences(action, context)
        
        if not similar_experiences:
            return {
                'predicted_success': 0.5,
                'confidence': 0.1,
                'reasoning': '缺乏相关经验'
            }
        
        # 计算预测
        success_count = sum(1 for exp in similar_experiences if exp.success)
        total_count = len(similar_experiences)
        predicted_success = success_count / total_count
        
        # 计算置信度
        confidence = min(1.0, total_count / 10.0)
        
        # 生成推理
        reasoning = f"基于{total_count}个相似经验，成功率{predicted_success:.2f}"
        
        return {
            'predicted_success': predicted_success,
            'confidence': confidence,
            'reasoning': reasoning,
            'similar_experiences_count': total_count
        }
    
    def _find_similar_experiences(self, action: str, context: Dict[str, Any]) -> List[Experience]:
        """查找相似经验"""
        similar = []
        
        for exp in self.experiences:
            similarity = self._calculate_similarity(action, context, exp)
            if similarity > 0.5:  # 相似度阈值
                similar.append(exp)
        
        # 按相似度排序，返回最相似的10个
        similar.sort(key=lambda x: self._calculate_similarity(action, context, x), reverse=True)
        return similar[:10]
    
    def _calculate_similarity(self, action: str, context: Dict[str, Any], experience: Experience) -> float:
        """计算相似度"""
        similarity = 0.0
        
        # 动作相似度
        if action == experience.action:
            similarity += 0.5
        elif action.lower() in experience.action.lower() or experience.action.lower() in action.lower():
            similarity += 0.3
        
        # 上下文相似度
        context_similarity = 0.0
        common_keys = set(context.keys()) & set(experience.context.keys())
        if common_keys:
            for key in common_keys:
                if context[key] == experience.context[key]:
                    context_similarity += 1.0 / len(common_keys)
        
        similarity += context_similarity * 0.5
        
        return min(1.0, similarity)


class AdaptiveDecisionEngine:
    """自适应决策引擎"""
    
    def __init__(self, learning_engine: OrganicLearningEngine):
        self.learning_engine = learning_engine
        self.logger = logging.getLogger("AgentZero.Decision")
        
        # 决策策略
        self.strategy = AdaptationStrategy.ORGANIC
        self.risk_tolerance = 0.5
        self.innovation_factor = 0.3
        
        # 决策历史
        self.decision_history: List[Dict[str, Any]] = []
    
    async def make_decision(self, context: DecisionContext) -> Dict[str, Any]:
        """做出决策"""
        
        decision_id = f"decision_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # 评估每个可用行动
        action_evaluations = []
        for action in context.available_actions:
            evaluation = await self._evaluate_action(action, context)
            action_evaluations.append({
                'action': action,
                'score': evaluation['score'],
                'confidence': evaluation['confidence'],
                'reasoning': evaluation['reasoning']
            })
        
        # 选择最佳行动
        best_action = max(action_evaluations, key=lambda x: x['score'])
        
        # 应用探索策略
        if random.random() < self.learning_engine.exploration_rate:
            # 探索性决策
            exploration_action = random.choice(action_evaluations)
            selected_action = exploration_action
            decision_type = "exploration"
        else:
            # 利用性决策
            selected_action = best_action
            decision_type = "exploitation"
        
        # 记录决策
        decision_record = {
            'id': decision_id,
            'context': asdict(context),
            'selected_action': selected_action['action'],
            'decision_type': decision_type,
            'all_evaluations': action_evaluations,
            'timestamp': time.time()
        }
        
        self.decision_history.append(decision_record)
        
        self.logger.info(f"决策: {selected_action['action']} (类型: {decision_type})")
        
        return {
            'decision_id': decision_id,
            'selected_action': selected_action['action'],
            'confidence': selected_action['confidence'],
            'reasoning': selected_action['reasoning'],
            'decision_type': decision_type,
            'alternatives': [eval for eval in action_evaluations if eval['action'] != selected_action['action']]
        }
    
    async def _evaluate_action(self, action: str, context: DecisionContext) -> Dict[str, Any]:
        """评估行动"""
        
        # 获取学习引擎的预测
        prediction = await self.learning_engine.predict_outcome(
            action, 
            {
                'situation': context.situation,
                'urgency': context.urgency,
                'complexity': context.complexity
            }
        )
        
        # 计算基础分数
        base_score = prediction['predicted_success']
        
        # 应用上下文调整
        urgency_adjustment = context.urgency * 0.2  # 紧急情况下偏向已知有效的行动
        complexity_adjustment = (1 - context.complexity) * 0.1  # 复杂情况下更保守
        
        # 应用风险调整
        risk_adjustment = (1 - self.risk_tolerance) * (1 - prediction['confidence']) * 0.3
        
        # 应用创新因子
        innovation_bonus = 0.0
        if prediction['similar_experiences_count'] < 3:  # 新颖的行动
            innovation_bonus = self.innovation_factor * 0.2
        
        # 计算最终分数
        final_score = base_score + urgency_adjustment + complexity_adjustment - risk_adjustment + innovation_bonus
        final_score = max(0.0, min(1.0, final_score))
        
        return {
            'score': final_score,
            'confidence': prediction['confidence'],
            'reasoning': f"{prediction['reasoning']}; 调整后分数: {final_score:.2f}"
        }
    
    async def learn_from_outcome(self, decision_id: str, outcome: str, success: bool, reward: float):
        """从决策结果中学习"""
        
        # 查找决策记录
        decision_record = None
        for record in self.decision_history:
            if record['id'] == decision_id:
                decision_record = record
                break
        
        if not decision_record:
            self.logger.warning(f"未找到决策记录: {decision_id}")
            return
        
        # 创建经验
        experience = Experience(
            id=f"exp_{decision_id}",
            action=decision_record['selected_action'],
            context=decision_record['context'],
            outcome=outcome,
            success=success,
            reward=reward,
            timestamp=time.time()
        )
        
        # 让学习引擎学习
        await self.learning_engine.learn_from_experience(experience)
        
        # 调整决策参数
        await self._adjust_decision_parameters(success, reward)
    
    async def _adjust_decision_parameters(self, success: bool, reward: float):
        """调整决策参数"""
        
        if success:
            # 成功时稍微降低风险容忍度，增加创新因子
            self.risk_tolerance = max(0.1, self.risk_tolerance * 0.99)
            self.innovation_factor = min(0.5, self.innovation_factor * 1.01)
        else:
            # 失败时增加风险容忍度，降低创新因子
            self.risk_tolerance = min(0.9, self.risk_tolerance * 1.01)
            self.innovation_factor = max(0.1, self.innovation_factor * 0.99)


class AgentZeroIntegration:
    """Agent Zero 集成主类"""
    
    def __init__(self):
        self.logger = logging.getLogger("AgentZero")
        
        # 核心组件
        self.learning_engine = OrganicLearningEngine()
        self.decision_engine = AdaptiveDecisionEngine(self.learning_engine)
        
        # 智能体状态
        self.agent_state = {
            'active': False,
            'learning_mode': LearningMode.ORGANIC,
            'adaptation_strategy': AdaptationStrategy.ORGANIC,
            'performance_level': 0.5,
            'experience_count': 0,
            'knowledge_nodes': 0
        }
        
        # 性能统计
        self.performance_stats = {
            'decisions_made': 0,
            'successful_decisions': 0,
            'learning_cycles': 0,
            'adaptation_rate': 0.85,
            'start_time': time.time()
        }
        
        self.logger.info("Agent Zero集成初始化完成")
    
    async def activate_agent(self) -> bool:
        """激活智能体"""
        try:
            self.agent_state['active'] = True
            self.logger.info("Agent Zero已激活")
            return True
        except Exception as e:
            self.logger.error(f"激活失败: {e}")
            return False
    
    async def deactivate_agent(self) -> bool:
        """停用智能体"""
        try:
            self.agent_state['active'] = False
            self.logger.info("Agent Zero已停用")
            return True
        except Exception as e:
            self.logger.error(f"停用失败: {e}")
            return False
    
    async def process_task(
        self,
        task_description: str,
        available_actions: List[str],
        context: Dict[str, Any] = None,
        constraints: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """处理任务"""
        
        if not self.agent_state['active']:
            return {'error': 'Agent Zero未激活'}
        
        # 创建决策上下文
        decision_context = DecisionContext(
            situation=task_description,
            available_actions=available_actions,
            constraints=constraints or {},
            goals=[task_description],
            urgency=context.get('urgency', 0.5) if context else 0.5,
            complexity=context.get('complexity', 0.5) if context else 0.5
        )
        
        # 做出决策
        decision = await self.decision_engine.make_decision(decision_context)
        
        # 更新统计
        self.performance_stats['decisions_made'] += 1
        
        return {
            'task_id': f"task_{int(time.time())}",
            'recommended_action': decision['selected_action'],
            'confidence': decision['confidence'],
            'reasoning': decision['reasoning'],
            'decision_type': decision['decision_type'],
            'alternatives': decision['alternatives'],
            'agent_state': self.agent_state.copy()
        }
    
    async def learn_from_feedback(
        self,
        task_id: str,
        action_taken: str,
        outcome: str,
        success: bool,
        user_feedback: str = None
    ) -> bool:
        """从反馈中学习"""
        
        # 计算奖励
        reward = 1.0 if success else -0.5
        if user_feedback:
            # 基于用户反馈调整奖励
            if 'excellent' in user_feedback.lower() or '优秀' in user_feedback:
                reward += 0.5
            elif 'poor' in user_feedback.lower() or '差' in user_feedback:
                reward -= 0.5
        
        # 创建学习经验
        experience = Experience(
            id=f"feedback_{task_id}",
            action=action_taken,
            context={'task_id': task_id, 'user_feedback': user_feedback or ''},
            outcome=outcome,
            success=success,
            reward=reward,
            timestamp=time.time()
        )
        
        # 学习
        learned = await self.learning_engine.learn_from_experience(experience)
        
        if learned:
            # 更新统计
            self.performance_stats['learning_cycles'] += 1
            if success:
                self.performance_stats['successful_decisions'] += 1
            
            # 更新智能体状态
            self.agent_state['experience_count'] = len(self.learning_engine.experiences)
            self.agent_state['knowledge_nodes'] = len(self.learning_engine.knowledge_graph)
            
            # 计算性能水平
            if self.performance_stats['decisions_made'] > 0:
                success_rate = (
                    self.performance_stats['successful_decisions'] / 
                    self.performance_stats['decisions_made']
                )
                self.agent_state['performance_level'] = success_rate
        
        return learned
    
    async def get_agent_insights(self) -> Dict[str, Any]:
        """获取智能体洞察"""
        
        # 分析学习模式
        recent_experiences = self.learning_engine.experiences[-50:] if len(self.learning_engine.experiences) >= 50 else self.learning_engine.experiences
        
        if recent_experiences:
            success_rate = sum(1 for exp in recent_experiences if exp.success) / len(recent_experiences)
            avg_reward = sum(exp.reward for exp in recent_experiences) / len(recent_experiences)
        else:
            success_rate = 0.0
            avg_reward = 0.0
        
        # 分析知识图谱
        top_concepts = sorted(
            self.learning_engine.knowledge_graph.values(),
            key=lambda x: x.usage_count,
            reverse=True
        )[:5]
        
        uptime = time.time() - self.performance_stats['start_time']
        
        return {
            'agent_status': self.agent_state,
            'performance_metrics': {
                **self.performance_stats,
                'uptime_hours': uptime / 3600,
                'recent_success_rate': success_rate,
                'average_reward': avg_reward,
                'learning_efficiency': self.learning_engine.learning_stats['learning_efficiency']
            },
            'knowledge_insights': {
                'total_concepts': len(self.learning_engine.knowledge_graph),
                'top_concepts': [
                    {
                        'concept': node.concept,
                        'confidence': node.confidence,
                        'usage_count': node.usage_count,
                        'connections': len(node.connections)
                    }
                    for node in top_concepts
                ],
                'knowledge_growth_rate': len(self.learning_engine.knowledge_graph) / max(uptime / 3600, 1)
            },
            'learning_parameters': {
                'learning_rate': self.learning_engine.learning_rate,
                'exploration_rate': self.learning_engine.exploration_rate,
                'adaptation_rate': self.learning_engine.adaptation_rate
            }
        }
    
    async def optimize_performance(self) -> Dict[str, Any]:
        """优化性能"""
        
        # 清理过期知识
        current_time = time.time()
        removed_nodes = 0
        
        for node_id, node in list(self.learning_engine.knowledge_graph.items()):
            # 计算知识衰减
            time_since_update = current_time - node.last_updated
            decay = math.exp(-node.decay_rate * time_since_update)
            node.confidence *= decay
            
            # 移除低置信度的节点
            if node.confidence < 0.1 and node.usage_count < 3:
                del self.learning_engine.knowledge_graph[node_id]
                removed_nodes += 1
        
        # 优化经验存储
        if len(self.learning_engine.experiences) > self.learning_engine.max_experiences * 0.8:
            # 保留高价值经验
            self.learning_engine.experiences.sort(key=lambda x: x.learning_value, reverse=True)
            self.learning_engine.experiences = self.learning_engine.experiences[:int(self.learning_engine.max_experiences * 0.6)]
        
        return {
            'optimization_time': current_time,
            'removed_knowledge_nodes': removed_nodes,
            'remaining_experiences': len(self.learning_engine.experiences),
            'remaining_knowledge_nodes': len(self.learning_engine.knowledge_graph)
        }


# 全局Agent Zero实例
agent_zero = None

def get_agent_zero() -> AgentZeroIntegration:
    """获取Agent Zero实例"""
    global agent_zero
    if agent_zero is None:
        agent_zero = AgentZeroIntegration()
    return agent_zero


if __name__ == "__main__":
    # 测试Agent Zero集成
    async def test_agent_zero():
        agent = get_agent_zero()
        
        # 激活智能体
        await agent.activate_agent()
        
        # 处理任务
        result = await agent.process_task(
            task_description="优化代码性能",
            available_actions=["重构代码", "添加缓存", "优化算法", "并行处理"],
            context={'urgency': 0.7, 'complexity': 0.8}
        )
        print(f"任务处理结果: {result['recommended_action']}")
        
        # 模拟反馈学习
        await agent.learn_from_feedback(
            task_id=result.get('task_id', 'test'),
            action_taken=result['recommended_action'],
            outcome="性能提升30%",
            success=True,
            user_feedback="效果很好"
        )
        
        # 获取洞察
        insights = await agent.get_agent_insights()
        print(f"智能体洞察: 性能水平 {insights['agent_status']['performance_level']:.2f}")
    
    # 运行测试
    asyncio.run(test_agent_zero())

