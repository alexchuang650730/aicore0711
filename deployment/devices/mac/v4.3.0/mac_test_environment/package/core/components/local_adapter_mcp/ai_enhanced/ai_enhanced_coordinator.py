"""
AI Enhanced Coordinator - AI增强协调器
统一管理和协调所有AI增强功能，提供统一的AI服务接口

功能：
- 统一管理所有AI组件
- 智能任务路由和调度
- AI功能协调和优化
- 统一的AI服务接口
- 性能监控和报告
- 自适应学习和优化
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

from .intelligent_task_optimizer import IntelligentTaskOptimizer, TaskOptimizationRequest
from .local_ai_model_integration import LocalAIModelIntegration, OCRConfig
from .predictive_resource_allocator import PredictiveResourceAllocator, ResourceUsage, AllocationStrategy
from .smart_performance_tuner import SmartPerformanceTuner, PerformanceData, TuningStrategy

class AIServiceType(Enum):
    """AI服务类型"""
    TASK_OPTIMIZATION = "task_optimization"
    OCR_PROCESSING = "ocr_processing"
    RESOURCE_PREDICTION = "resource_prediction"
    PERFORMANCE_TUNING = "performance_tuning"

class AIRequestPriority(Enum):
    """AI请求优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class AIRequest:
    """AI请求"""
    request_id: str
    service_type: AIServiceType
    priority: AIRequestPriority
    data: Dict[str, Any]
    timestamp: datetime
    timeout: int = 300  # 默认5分钟超时

@dataclass
class AIResponse:
    """AI响应"""
    request_id: str
    service_type: AIServiceType
    success: bool
    result: Any
    processing_time: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

class AIEnhancedCoordinator:
    """AI增强协调器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # AI组件初始化
        self.task_optimizer = IntelligentTaskOptimizer()
        self.ocr_model = LocalAIModelIntegration()
        self.resource_allocator = PredictiveResourceAllocator(AllocationStrategy.BALANCED)
        self.performance_tuner = SmartPerformanceTuner(TuningStrategy.BALANCED)
        
        # 请求队列和处理状态
        self.request_queue: asyncio.Queue = asyncio.Queue()
        self.active_requests: Dict[str, AIRequest] = {}
        self.request_history: List[AIResponse] = []
        
        # 性能统计
        self.service_stats = {
            service_type: {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "average_processing_time": 0.0,
                "last_request_time": None
            }
            for service_type in AIServiceType
        }
        
        # 配置参数
        self.max_concurrent_requests = 10
        self.request_timeout = 300  # 5分钟
        self.cleanup_interval = 3600  # 1小时清理一次历史记录
        
        # 启动后台任务
        self._background_tasks = []
        
        self.logger.info("AI增强协调器初始化完成")
    
    async def initialize(self) -> bool:
        """
        初始化AI增强协调器
        
        Returns:
            bool: 是否成功初始化
        """
        try:
            # 初始化OCR模型
            ocr_success = await self.ocr_model.initialize_model()
            if not ocr_success:
                self.logger.warning("OCR模型初始化失败，OCR功能将不可用")
            
            # 启动后台任务
            self._background_tasks = [
                asyncio.create_task(self._process_requests()),
                asyncio.create_task(self._cleanup_task()),
                asyncio.create_task(self._monitoring_task())
            ]
            
            self.logger.info("AI增强协调器初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"AI增强协调器初始化失败: {e}")
            return False
    
    async def submit_ai_request(self, request: AIRequest) -> str:
        """
        提交AI请求
        
        Args:
            request: AI请求
            
        Returns:
            str: 请求ID
        """
        try:
            # 添加到队列
            await self.request_queue.put(request)
            self.active_requests[request.request_id] = request
            
            self.logger.info(f"提交AI请求: {request.request_id} - {request.service_type.value}")
            
            return request.request_id
            
        except Exception as e:
            self.logger.error(f"提交AI请求失败: {e}")
            raise
    
    async def get_ai_response(self, request_id: str, timeout: int = None) -> Optional[AIResponse]:
        """
        获取AI响应
        
        Args:
            request_id: 请求ID
            timeout: 超时时间（秒）
            
        Returns:
            Optional[AIResponse]: AI响应，如果超时或失败返回None
        """
        try:
            timeout = timeout or self.request_timeout
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # 检查是否有响应
                for response in self.request_history:
                    if response.request_id == request_id:
                        return response
                
                # 检查请求是否还在处理中
                if request_id not in self.active_requests:
                    break
                
                await asyncio.sleep(0.1)  # 100ms检查间隔
            
            # 超时处理
            if request_id in self.active_requests:
                del self.active_requests[request_id]
                self.logger.warning(f"AI请求超时: {request_id}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"获取AI响应失败: {e}")
            return None
    
    async def process_task_optimization(self, request_data: Dict[str, Any]) -> Any:
        """处理任务优化请求"""
        try:
            # 构建优化请求
            optimization_request = TaskOptimizationRequest(
                task_type=request_data.get("task_type", "unknown"),
                platform=request_data.get("platform", "unknown"),
                estimated_duration=request_data.get("estimated_duration", 60),
                resource_requirements=request_data.get("resource_requirements", {}),
                priority=request_data.get("priority", 1),
                context=request_data.get("context", {})
            )
            
            # 执行优化
            optimization_result = await self.task_optimizer.optimize_task_execution(optimization_request)
            
            return {
                "optimized_strategy": optimization_result.optimized_strategy,
                "expected_improvement": optimization_result.expected_improvement,
                "resource_allocation": optimization_result.resource_allocation,
                "execution_order": optimization_result.execution_order,
                "confidence": optimization_result.confidence
            }
            
        except Exception as e:
            self.logger.error(f"任务优化处理失败: {e}")
            raise
    
    async def process_ocr_request(self, request_data: Dict[str, Any]) -> Any:
        """处理OCR请求"""
        try:
            file_path = request_data.get("file_path")
            output_path = request_data.get("output_path")
            
            if not file_path:
                raise ValueError("缺少file_path参数")
            
            # 处理OCR
            if file_path.lower().endswith('.pdf'):
                result = await self.ocr_model.process_pdf(file_path, output_path)
            else:
                result = await self.ocr_model.process_image(file_path, output_path)
            
            return {
                "success": result.success,
                "output_path": result.output_path,
                "processing_time": result.processing_time,
                "page_count": getattr(result, 'page_count', 1),
                "error_message": result.error_message
            }
            
        except Exception as e:
            self.logger.error(f"OCR处理失败: {e}")
            raise
    
    async def process_resource_prediction(self, request_data: Dict[str, Any]) -> Any:
        """处理资源预测请求"""
        try:
            platform = request_data.get("platform", "unknown")
            resource_type = request_data.get("resource_type", "cpu")
            time_horizon = request_data.get("time_horizon", 60)
            
            # 转换资源类型
            from .predictive_resource_allocator import ResourceType
            resource_type_enum = ResourceType(resource_type)
            
            # 执行预测
            prediction = await self.resource_allocator.predict_resource_demand(
                platform, resource_type_enum, time_horizon
            )
            
            return {
                "predicted_usage": prediction.predicted_usage,
                "confidence": prediction.confidence,
                "time_horizon": prediction.time_horizon,
                "factors": prediction.factors
            }
            
        except Exception as e:
            self.logger.error(f"资源预测处理失败: {e}")
            raise
    
    async def process_performance_tuning(self, request_data: Dict[str, Any]) -> Any:
        """处理性能调优请求"""
        try:
            platform = request_data.get("platform")
            task_type = request_data.get("task_type")
            
            # 分析性能瓶颈
            bottlenecks = await self.performance_tuner.analyze_performance_bottlenecks(platform, task_type)
            
            # 生成调优建议
            recommendations = await self.performance_tuner.generate_tuning_recommendations(platform, task_type)
            
            return {
                "bottlenecks": bottlenecks,
                "recommendations": [asdict(rec) for rec in recommendations],
                "current_config": self.performance_tuner.get_current_config()
            }
            
        except Exception as e:
            self.logger.error(f"性能调优处理失败: {e}")
            raise
    
    async def _process_requests(self):
        """后台请求处理任务"""
        while True:
            try:
                # 获取请求（带超时）
                try:
                    request = await asyncio.wait_for(self.request_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # 检查并发限制
                if len(self.active_requests) > self.max_concurrent_requests:
                    # 重新放回队列
                    await self.request_queue.put(request)
                    await asyncio.sleep(0.1)
                    continue
                
                # 处理请求
                asyncio.create_task(self._handle_single_request(request))
                
            except Exception as e:
                self.logger.error(f"请求处理循环错误: {e}")
                await asyncio.sleep(1)
    
    async def _handle_single_request(self, request: AIRequest):
        """处理单个请求"""
        start_time = time.time()
        response = None
        
        try:
            # 根据服务类型分发请求
            if request.service_type == AIServiceType.TASK_OPTIMIZATION:
                result = await self.process_task_optimization(request.data)
            elif request.service_type == AIServiceType.OCR_PROCESSING:
                result = await self.process_ocr_request(request.data)
            elif request.service_type == AIServiceType.RESOURCE_PREDICTION:
                result = await self.process_resource_prediction(request.data)
            elif request.service_type == AIServiceType.PERFORMANCE_TUNING:
                result = await self.process_performance_tuning(request.data)
            else:
                raise ValueError(f"不支持的服务类型: {request.service_type}")
            
            # 创建成功响应
            response = AIResponse(
                request_id=request.request_id,
                service_type=request.service_type,
                success=True,
                result=result,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            # 创建失败响应
            response = AIResponse(
                request_id=request.request_id,
                service_type=request.service_type,
                success=False,
                result=None,
                processing_time=time.time() - start_time,
                error_message=str(e)
            )
            
            self.logger.error(f"处理AI请求失败: {request.request_id} - {e}")
        
        finally:
            # 清理和记录
            if request.request_id in self.active_requests:
                del self.active_requests[request.request_id]
            
            if response:
                self.request_history.append(response)
                self._update_service_stats(response)
    
    def _update_service_stats(self, response: AIResponse):
        """更新服务统计"""
        try:
            stats = self.service_stats[response.service_type]
            
            stats["total_requests"] += 1
            stats["last_request_time"] = datetime.now()
            
            if response.success:
                stats["successful_requests"] += 1
            else:
                stats["failed_requests"] += 1
            
            # 更新平均处理时间
            total_successful = stats["successful_requests"]
            if total_successful > 0:
                current_avg = stats["average_processing_time"]
                new_avg = ((current_avg * (total_successful - 1)) + response.processing_time) / total_successful
                stats["average_processing_time"] = new_avg
            
        except Exception as e:
            self.logger.error(f"更新服务统计失败: {e}")
    
    async def _cleanup_task(self):
        """清理任务"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                # 清理过期的请求历史
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.request_history = [
                    response for response in self.request_history
                    if response.request_id and len(self.request_history) < 1000
                ]
                
                # 清理超时的活跃请求
                current_time = time.time()
                expired_requests = []
                
                for request_id, request in self.active_requests.items():
                    if current_time - request.timestamp.timestamp() > request.timeout:
                        expired_requests.append(request_id)
                
                for request_id in expired_requests:
                    del self.active_requests[request_id]
                    self.logger.warning(f"清理超时请求: {request_id}")
                
                self.logger.debug(f"清理完成，活跃请求: {len(self.active_requests)}, "
                                f"历史记录: {len(self.request_history)}")
                
            except Exception as e:
                self.logger.error(f"清理任务错误: {e}")
    
    async def _monitoring_task(self):
        """监控任务"""
        while True:
            try:
                await asyncio.sleep(300)  # 5分钟监控间隔
                
                # 记录系统状态
                stats = self.get_statistics()
                self.logger.info(f"AI协调器状态 - 活跃请求: {len(self.active_requests)}, "
                               f"队列大小: {self.request_queue.qsize()}, "
                               f"总处理请求: {sum(s['total_requests'] for s in self.service_stats.values())}")
                
                # 检查组件健康状态
                await self._check_component_health()
                
            except Exception as e:
                self.logger.error(f"监控任务错误: {e}")
    
    async def _check_component_health(self):
        """检查组件健康状态"""
        try:
            # 检查OCR模型状态
            ocr_status = self.ocr_model.get_status()
            if not ocr_status.get("model_loaded", False):
                self.logger.warning("OCR模型未加载")
            
            # 检查其他组件状态
            components = [
                ("任务优化器", self.task_optimizer),
                ("资源分配器", self.resource_allocator),
                ("性能调优器", self.performance_tuner)
            ]
            
            for name, component in components:
                if hasattr(component, 'get_status'):
                    status = component.get_status()
                    if status.get("status") != "active":
                        self.logger.warning(f"{name}状态异常: {status}")
            
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
    
    async def shutdown(self):
        """关闭协调器"""
        try:
            # 取消后台任务
            for task in self._background_tasks:
                task.cancel()
            
            # 等待任务完成
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
            
            self.logger.info("AI增强协调器已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭协调器失败: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            # 计算总体统计
            total_requests = sum(stats["total_requests"] for stats in self.service_stats.values())
            total_successful = sum(stats["successful_requests"] for stats in self.service_stats.values())
            total_failed = sum(stats["failed_requests"] for stats in self.service_stats.values())
            
            success_rate = (total_successful / total_requests * 100) if total_requests > 0 else 0
            
            # 计算平均处理时间
            processing_times = []
            for response in self.request_history[-100:]:  # 最近100个请求
                if response.success:
                    processing_times.append(response.processing_time)
            
            avg_processing_time = statistics.mean(processing_times) if processing_times else 0
            
            return {
                "total_requests": total_requests,
                "successful_requests": total_successful,
                "failed_requests": total_failed,
                "success_rate": success_rate,
                "average_processing_time": avg_processing_time,
                "active_requests": len(self.active_requests),
                "queue_size": self.request_queue.qsize(),
                "service_statistics": self.service_stats,
                "component_status": {
                    "task_optimizer": self.task_optimizer.get_status(),
                    "ocr_model": self.ocr_model.get_status(),
                    "resource_allocator": self.resource_allocator.get_status(),
                    "performance_tuner": self.performance_tuner.get_status()
                }
            }
            
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {"error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态信息"""
        return {
            "status": "active",
            "supported_services": [service.value for service in AIServiceType],
            "max_concurrent_requests": self.max_concurrent_requests,
            "request_timeout": self.request_timeout,
            "components_initialized": True,
            "statistics": self.get_statistics()
        }

# 便捷函数
async def create_ai_request(service_type: AIServiceType, data: Dict[str, Any],
                          priority: AIRequestPriority = AIRequestPriority.NORMAL,
                          timeout: int = 300) -> AIRequest:
    """创建AI请求"""
    import uuid
    
    return AIRequest(
        request_id=str(uuid.uuid4()),
        service_type=service_type,
        priority=priority,
        data=data,
        timestamp=datetime.now(),
        timeout=timeout
    )

