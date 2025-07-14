"""
多模型协调器

智能协调Claude和Gemini API，实现最优的模型选择和负载均衡
根据任务类型、成本要求、性能需求自动选择最适合的AI模型
"""

import asyncio
import json
import logging
import time
import random
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

from .claude_api_client import ClaudeAPIClient, get_claude_client
from .gemini_api_client import GeminiAPIClient, get_gemini_client


class TaskType(Enum):
    """任务类型枚举"""
    CODE_GENERATION = "code_generation"
    CODE_EXPLANATION = "code_explanation"
    CODE_DEBUG = "code_debug"
    CODE_OPTIMIZATION = "code_optimization"
    CODE_REFACTORING = "code_refactoring"
    CODE_REVIEW = "code_review"
    TEST_GENERATION = "test_generation"
    ARCHITECTURE_DESIGN = "architecture_design"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    INNOVATION_SOLUTION = "innovation_solution"


class ModelStrategy(Enum):
    """模型选择策略"""
    QUALITY_FIRST = "quality_first"      # 质量优先
    COST_EFFICIENT = "cost_efficient"    # 成本优先
    SPEED_FIRST = "speed_first"          # 速度优先
    BALANCED = "balanced"                # 平衡策略
    INNOVATION_FOCUS = "innovation_focus" # 创新优先
    AUTO_SELECT = "auto_select"          # 自动选择


@dataclass
class TaskRequest:
    """任务请求"""
    task_type: TaskType
    prompt: str
    language: str = "python"
    strategy: ModelStrategy = ModelStrategy.AUTO_SELECT
    context: str = None
    constraints: Dict[str, Any] = None
    priority: int = 1  # 1-5, 5最高
    max_cost: float = None
    max_time: float = None
    
    def __post_init__(self):
        if self.constraints is None:
            self.constraints = {}


@dataclass
class ModelResponse:
    """模型响应"""
    content: str
    model_used: str
    task_type: TaskType
    execution_time: float
    estimated_cost: float
    quality_score: float
    innovation_score: float
    success: bool
    error: str = None
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class MultiModelCoordinator:
    """多模型协调器"""
    
    def __init__(self, claude_api_key: str, gemini_api_key: str):
        self.claude_client = get_claude_client(claude_api_key)
        self.gemini_client = get_gemini_client(gemini_api_key)
        self.logger = logging.getLogger("MultiModelCoordinator")
        
        # 模型特性配置
        self.model_capabilities = {
            'claude': {
                'quality_score': 0.95,
                'innovation_score': 0.85,
                'speed_score': 0.75,
                'cost_efficiency': 0.70,
                'reasoning_strength': 0.95,
                'code_quality': 0.90,
                'explanation_ability': 0.95
            },
            'gemini': {
                'quality_score': 0.85,
                'innovation_score': 0.88,
                'speed_score': 0.92,
                'cost_efficiency': 0.95,
                'performance_optimization': 0.90,
                'rapid_prototyping': 0.95,
                'scalability_design': 0.88
            }
        }
        
        # 任务类型到模型的映射权重
        self.task_model_weights = {
            TaskType.CODE_GENERATION: {'claude': 0.6, 'gemini': 0.4},
            TaskType.CODE_EXPLANATION: {'claude': 0.8, 'gemini': 0.2},
            TaskType.CODE_DEBUG: {'claude': 0.7, 'gemini': 0.3},
            TaskType.CODE_OPTIMIZATION: {'claude': 0.3, 'gemini': 0.7},
            TaskType.CODE_REFACTORING: {'claude': 0.6, 'gemini': 0.4},
            TaskType.CODE_REVIEW: {'claude': 0.8, 'gemini': 0.2},
            TaskType.TEST_GENERATION: {'claude': 0.5, 'gemini': 0.5},
            TaskType.ARCHITECTURE_DESIGN: {'claude': 0.4, 'gemini': 0.6},
            TaskType.PERFORMANCE_ANALYSIS: {'claude': 0.2, 'gemini': 0.8},
            TaskType.INNOVATION_SOLUTION: {'claude': 0.4, 'gemini': 0.6}
        }
        
        # 协调器统计
        self.coordinator_stats = {
            'total_requests': 0,
            'claude_requests': 0,
            'gemini_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_cost_saved': 0.0,
            'average_response_time': 0.0,
            'model_selection_accuracy': 0.0
        }
        
        # 请求历史和性能数据
        self.request_history: List[Dict[str, Any]] = []
        self.model_performance: Dict[str, List[float]] = {
            'claude': [],
            'gemini': []
        }
        self.max_history = 200
        
        self.logger.info("多模型协调器初始化完成")
    
    async def process_request(self, request: TaskRequest) -> ModelResponse:
        """处理任务请求"""
        
        start_time = time.time()
        self.coordinator_stats['total_requests'] += 1
        
        try:
            # 1. 选择最适合的模型
            selected_model = await self._select_optimal_model(request)
            
            # 2. 执行任务
            response = await self._execute_task(request, selected_model)
            
            # 3. 更新统计和性能数据
            execution_time = time.time() - start_time
            await self._update_performance_data(selected_model, response, execution_time)
            
            self.coordinator_stats['successful_requests'] += 1
            self.logger.info(f"任务完成: {request.task_type.value} 使用 {selected_model} 模型")
            
            return response
            
        except Exception as e:
            self.coordinator_stats['failed_requests'] += 1
            execution_time = time.time() - start_time
            
            error_response = ModelResponse(
                content="",
                model_used="none",
                task_type=request.task_type,
                execution_time=execution_time,
                estimated_cost=0.0,
                quality_score=0.0,
                innovation_score=0.0,
                success=False,
                error=str(e)
            )
            
            self.logger.error(f"任务执行失败: {e}")
            return error_response
    
    async def _select_optimal_model(self, request: TaskRequest) -> str:
        """选择最优模型"""
        
        if request.strategy == ModelStrategy.AUTO_SELECT:
            return await self._auto_select_model(request)
        elif request.strategy == ModelStrategy.QUALITY_FIRST:
            return "claude"  # Claude在质量方面更强
        elif request.strategy == ModelStrategy.COST_EFFICIENT:
            return "gemini"  # Gemini更具成本效益
        elif request.strategy == ModelStrategy.SPEED_FIRST:
            return "gemini"  # Gemini速度更快
        elif request.strategy == ModelStrategy.INNOVATION_FOCUS:
            return "gemini"  # Gemini创新分数更高
        elif request.strategy == ModelStrategy.BALANCED:
            return await self._balanced_selection(request)
        else:
            return await self._auto_select_model(request)
    
    async def _auto_select_model(self, request: TaskRequest) -> str:
        """自动选择模型"""
        
        # 获取任务类型权重
        task_weights = self.task_model_weights.get(request.task_type, {'claude': 0.5, 'gemini': 0.5})
        
        # 计算综合评分
        claude_score = 0.0
        gemini_score = 0.0
        
        # 基础任务适配性
        claude_score += task_weights['claude'] * 0.4
        gemini_score += task_weights['gemini'] * 0.4
        
        # 成本考虑
        if request.max_cost:
            if request.max_cost < 0.5:  # 低成本需求
                gemini_score += 0.3
            else:
                claude_score += 0.1
        else:
            gemini_score += 0.2  # 默认偏向成本效益
        
        # 时间考虑
        if request.max_time:
            if request.max_time < 30:  # 快速响应需求
                gemini_score += 0.2
            else:
                claude_score += 0.1
        else:
            gemini_score += 0.1  # 默认偏向速度
        
        # 优先级考虑
        if request.priority >= 4:  # 高优先级任务
            claude_score += 0.2
        else:
            gemini_score += 0.1
        
        # 历史性能考虑
        claude_recent_performance = await self._get_recent_performance('claude')
        gemini_recent_performance = await self._get_recent_performance('gemini')
        
        claude_score += claude_recent_performance * 0.1
        gemini_score += gemini_recent_performance * 0.1
        
        # 负载均衡考虑
        claude_load = self.coordinator_stats['claude_requests'] / max(self.coordinator_stats['total_requests'], 1)
        gemini_load = self.coordinator_stats['gemini_requests'] / max(self.coordinator_stats['total_requests'], 1)
        
        if claude_load > 0.7:  # Claude负载过高
            gemini_score += 0.1
        elif gemini_load > 0.7:  # Gemini负载过高
            claude_score += 0.1
        
        # 选择评分更高的模型
        selected_model = "claude" if claude_score > gemini_score else "gemini"
        
        self.logger.info(f"自动选择模型: {selected_model} (Claude: {claude_score:.2f}, Gemini: {gemini_score:.2f})")
        return selected_model
    
    async def _balanced_selection(self, request: TaskRequest) -> str:
        """平衡选择策略"""
        
        # 简单的轮询策略，但考虑任务类型
        task_weights = self.task_model_weights.get(request.task_type, {'claude': 0.5, 'gemini': 0.5})
        
        # 基于权重的随机选择
        if random.random() < task_weights['claude']:
            return "claude"
        else:
            return "gemini"
    
    async def _execute_task(self, request: TaskRequest, model: str) -> ModelResponse:
        """执行具体任务"""
        
        start_time = time.time()
        
        try:
            if model == "claude":
                response = await self._execute_claude_task(request)
                self.coordinator_stats['claude_requests'] += 1
            else:
                response = await self._execute_gemini_task(request)
                self.coordinator_stats['gemini_requests'] += 1
            
            execution_time = time.time() - start_time
            
            # 估算成本（简化模型）
            estimated_cost = self._estimate_cost(model, len(response.content))
            
            # 评估质量和创新分数
            quality_score = self._evaluate_quality(response.content, request.task_type)
            innovation_score = self._evaluate_innovation(response.content, request.task_type)
            
            return ModelResponse(
                content=response.content,
                model_used=model,
                task_type=request.task_type,
                execution_time=execution_time,
                estimated_cost=estimated_cost,
                quality_score=quality_score,
                innovation_score=innovation_score,
                success=True
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ModelResponse(
                content="",
                model_used=model,
                task_type=request.task_type,
                execution_time=execution_time,
                estimated_cost=0.0,
                quality_score=0.0,
                innovation_score=0.0,
                success=False,
                error=str(e)
            )
    
    async def _execute_claude_task(self, request: TaskRequest):
        """执行Claude任务"""
        
        if request.task_type == TaskType.CODE_GENERATION:
            return await self.claude_client.generate_code(
                request.prompt, request.language, request.context
            )
        elif request.task_type == TaskType.CODE_EXPLANATION:
            return await self.claude_client.explain_code(
                request.prompt, request.language
            )
        elif request.task_type == TaskType.CODE_DEBUG:
            return await self.claude_client.debug_code(
                request.prompt, request.context, request.language
            )
        elif request.task_type == TaskType.CODE_OPTIMIZATION:
            return await self.claude_client.optimize_code(
                request.prompt, "performance", request.language
            )
        elif request.task_type == TaskType.CODE_REFACTORING:
            return await self.claude_client.refactor_code(
                request.prompt, "improve structure", request.language
            )
        elif request.task_type == TaskType.CODE_REVIEW:
            return await self.claude_client.code_review(
                request.prompt, "comprehensive", request.language
            )
        elif request.task_type == TaskType.TEST_GENERATION:
            return await self.claude_client.generate_tests(
                request.prompt, "pytest", request.language
            )
        else:
            # 默认使用代码生成
            return await self.claude_client.generate_code(
                request.prompt, request.language, request.context
            )
    
    async def _execute_gemini_task(self, request: TaskRequest):
        """执行Gemini任务"""
        
        if request.task_type == TaskType.CODE_GENERATION:
            return await self.gemini_client.generate_efficient_code(
                request.prompt, request.language, "performance", request.context
            )
        elif request.task_type == TaskType.CODE_OPTIMIZATION:
            return await self.gemini_client.optimize_for_performance(
                request.prompt, request.language, "speed"
            )
        elif request.task_type == TaskType.ARCHITECTURE_DESIGN:
            return await self.gemini_client.scalable_architecture(
                request.prompt, request.constraints or {}, request.language
            )
        elif request.task_type == TaskType.PERFORMANCE_ANALYSIS:
            return await self.gemini_client.optimize_for_performance(
                request.prompt, request.language, "throughput"
            )
        elif request.task_type == TaskType.INNOVATION_SOLUTION:
            return await self.gemini_client.innovative_approach(
                request.prompt, "general", request.language
            )
        else:
            # 默认使用高效代码生成
            return await self.gemini_client.generate_efficient_code(
                request.prompt, request.language, "performance", request.context
            )
    
    def _estimate_cost(self, model: str, content_length: int) -> float:
        """估算成本"""
        
        # 简化的成本模型（基于内容长度）
        base_cost_per_1k_chars = {
            'claude': 0.015,  # Claude相对较贵
            'gemini': 0.010   # Gemini更便宜
        }
        
        cost_per_char = base_cost_per_1k_chars[model] / 1000
        return content_length * cost_per_char
    
    def _evaluate_quality(self, content: str, task_type: TaskType) -> float:
        """评估质量分数"""
        
        # 简化的质量评估（基于内容特征）
        quality_indicators = {
            'code_blocks': content.count('```'),
            'explanations': content.count('解释') + content.count('说明'),
            'examples': content.count('示例') + content.count('例子'),
            'best_practices': content.count('最佳实践') + content.count('建议'),
            'length': len(content)
        }
        
        # 基础质量分数
        base_score = 0.6
        
        # 根据指标调整分数
        if quality_indicators['code_blocks'] > 0:
            base_score += 0.1
        if quality_indicators['explanations'] > 0:
            base_score += 0.1
        if quality_indicators['examples'] > 0:
            base_score += 0.1
        if quality_indicators['best_practices'] > 0:
            base_score += 0.1
        if quality_indicators['length'] > 500:
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    def _evaluate_innovation(self, content: str, task_type: TaskType) -> float:
        """评估创新分数"""
        
        # 简化的创新评估
        innovation_keywords = [
            '创新', '新颖', '独特', '突破', '优化', '改进',
            'innovative', 'novel', 'unique', 'breakthrough'
        ]
        
        innovation_count = sum(content.lower().count(keyword.lower()) for keyword in innovation_keywords)
        
        # 基础创新分数
        base_score = 0.5
        
        # 根据创新关键词调整
        base_score += min(innovation_count * 0.1, 0.4)
        
        # 根据任务类型调整
        if task_type in [TaskType.INNOVATION_SOLUTION, TaskType.ARCHITECTURE_DESIGN]:
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    async def _get_recent_performance(self, model: str) -> float:
        """获取最近性能表现"""
        
        recent_performances = self.model_performance[model][-10:]  # 最近10次
        
        if not recent_performances:
            return 0.5  # 默认中等性能
        
        return sum(recent_performances) / len(recent_performances)
    
    async def _update_performance_data(self, model: str, response: ModelResponse, execution_time: float):
        """更新性能数据"""
        
        if response.success:
            # 计算综合性能分数
            performance_score = (
                response.quality_score * 0.4 +
                response.innovation_score * 0.3 +
                (1.0 / max(execution_time, 0.1)) * 0.2 +  # 速度分数
                (1.0 / max(response.estimated_cost, 0.01)) * 0.1  # 成本效率分数
            )
            
            self.model_performance[model].append(min(performance_score, 1.0))
            
            # 保持性能历史在合理范围内
            if len(self.model_performance[model]) > 50:
                self.model_performance[model].pop(0)
        
        # 记录请求历史
        self._record_request_history(response, execution_time)
    
    def _record_request_history(self, response: ModelResponse, execution_time: float):
        """记录请求历史"""
        
        record = {
            'timestamp': time.time(),
            'model_used': response.model_used,
            'task_type': response.task_type.value,
            'success': response.success,
            'execution_time': execution_time,
            'quality_score': response.quality_score,
            'innovation_score': response.innovation_score,
            'estimated_cost': response.estimated_cost
        }
        
        self.request_history.append(record)
        
        # 保持历史记录在限制范围内
        if len(self.request_history) > self.max_history:
            self.request_history.pop(0)
    
    async def get_coordinator_statistics(self) -> Dict[str, Any]:
        """获取协调器统计信息"""
        
        # 计算成功率
        total_requests = self.coordinator_stats['total_requests']
        success_rate = (
            self.coordinator_stats['successful_requests'] / total_requests
            if total_requests > 0 else 0.0
        )
        
        # 计算模型使用分布
        claude_usage = (
            self.coordinator_stats['claude_requests'] / total_requests
            if total_requests > 0 else 0.0
        )
        gemini_usage = (
            self.coordinator_stats['gemini_requests'] / total_requests
            if total_requests > 0 else 0.0
        )
        
        # 分析最近性能
        recent_requests = self.request_history[-20:] if len(self.request_history) >= 20 else self.request_history
        
        avg_quality = (
            sum(req['quality_score'] for req in recent_requests if req['success']) / 
            len([req for req in recent_requests if req['success']])
            if recent_requests else 0.0
        )
        
        avg_innovation = (
            sum(req['innovation_score'] for req in recent_requests if req['success']) / 
            len([req for req in recent_requests if req['success']])
            if recent_requests else 0.0
        )
        
        return {
            'coordinator_statistics': {
                **self.coordinator_stats,
                'success_rate': success_rate,
                'claude_usage_rate': claude_usage,
                'gemini_usage_rate': gemini_usage
            },
            'model_performance': {
                'claude_recent_performance': await self._get_recent_performance('claude'),
                'gemini_recent_performance': await self._get_recent_performance('gemini')
            },
            'quality_metrics': {
                'average_quality_score': avg_quality,
                'average_innovation_score': avg_innovation,
                'total_requests_processed': len(self.request_history)
            },
            'model_capabilities': self.model_capabilities
        }
    
    async def test_all_models(self) -> Dict[str, bool]:
        """测试所有模型连接"""
        
        results = {}
        
        try:
            results['claude'] = await self.claude_client.test_connection()
        except Exception as e:
            results['claude'] = False
            self.logger.error(f"Claude连接测试失败: {e}")
        
        try:
            results['gemini'] = await self.gemini_client.test_connection()
        except Exception as e:
            results['gemini'] = False
            self.logger.error(f"Gemini连接测试失败: {e}")
        
        return results


# 全局多模型协调器实例
multi_model_coordinator = None

def get_multi_model_coordinator(claude_api_key: str = None, gemini_api_key: str = None) -> MultiModelCoordinator:
    """获取多模型协调器实例"""
    global multi_model_coordinator
    if multi_model_coordinator is None and claude_api_key and gemini_api_key:
        multi_model_coordinator = MultiModelCoordinator(claude_api_key, gemini_api_key)
    return multi_model_coordinator


if __name__ == "__main__":
    # 测试多模型协调器
    async def test_coordinator():
        claude_key = "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"
        gemini_key = "AIzaSyC_EsNirr14s8ypd3KafqWazSi_RW0NiqA"
        
        coordinator = get_multi_model_coordinator(claude_key, gemini_key)
        
        # 测试连接
        connection_results = await coordinator.test_all_models()
        print(f"连接测试结果: {connection_results}")
        
        if all(connection_results.values()):
            # 测试不同类型的任务
            test_requests = [
                TaskRequest(
                    task_type=TaskType.CODE_GENERATION,
                    prompt="创建一个快速排序算法",
                    language="python",
                    strategy=ModelStrategy.AUTO_SELECT
                ),
                TaskRequest(
                    task_type=TaskType.CODE_OPTIMIZATION,
                    prompt="def bubble_sort(arr): ...",  # 简化示例
                    language="python",
                    strategy=ModelStrategy.COST_EFFICIENT
                ),
                TaskRequest(
                    task_type=TaskType.INNOVATION_SOLUTION,
                    prompt="设计一个新颖的缓存系统",
                    language="python",
                    strategy=ModelStrategy.INNOVATION_FOCUS
                )
            ]
            
            for request in test_requests:
                response = await coordinator.process_request(request)
                print(f"\n任务: {request.task_type.value}")
                print(f"使用模型: {response.model_used}")
                print(f"成功: {response.success}")
                print(f"质量分数: {response.quality_score:.2f}")
                print(f"创新分数: {response.innovation_score:.2f}")
                print(f"执行时间: {response.execution_time:.2f}s")
                print(f"预估成本: ${response.estimated_cost:.4f}")
            
            # 获取统计信息
            stats = await coordinator.get_coordinator_statistics()
            print(f"\n协调器统计: {stats}")
    
    # 运行测试
    asyncio.run(test_coordinator())

