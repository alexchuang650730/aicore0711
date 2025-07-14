"""
Metrics Collector - 指标收集器
为ClaudEditor提供自定义指标收集和聚合功能

功能：
- 多源指标收集
- 实时指标聚合
- 自定义指标定义
- 指标存储和查询
- 数据导出和备份
"""

import asyncio
import logging
import json
import sqlite3
import threading
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import statistics
import numpy as np
from pathlib import Path

class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"          # 计数器（只增不减）
    GAUGE = "gauge"             # 仪表（可增可减）
    HISTOGRAM = "histogram"      # 直方图
    SUMMARY = "summary"         # 摘要
    TIMER = "timer"             # 计时器

class AggregationType(Enum):
    """聚合类型"""
    SUM = "sum"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    PERCENTILE = "percentile"
    RATE = "rate"

@dataclass
class MetricDefinition:
    """指标定义"""
    name: str
    metric_type: MetricType
    description: str
    unit: str
    labels: List[str]
    aggregation_types: List[AggregationType]
    retention_days: int
    collection_interval: int  # 秒
    enabled: bool

@dataclass
class MetricValue:
    """指标值"""
    metric_name: str
    value: Union[float, int]
    labels: Dict[str, str]
    timestamp: datetime
    source: str

@dataclass
class AggregatedMetric:
    """聚合指标"""
    metric_name: str
    aggregation_type: AggregationType
    value: float
    labels: Dict[str, str]
    time_window: timedelta
    start_time: datetime
    end_time: datetime
    sample_count: int

class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, storage_path: str = "/tmp/metrics.db"):
        self.logger = logging.getLogger(__name__)
        
        # 存储配置
        self.storage_path = storage_path
        self.db_connection = None
        self.db_lock = threading.Lock()
        
        # 指标定义
        self.metric_definitions: Dict[str, MetricDefinition] = {}
        
        # 内存缓存
        self.metric_cache: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.aggregation_cache: Dict[str, Dict] = defaultdict(dict)
        
        # 收集器状态
        self.is_collecting = False
        self.collection_tasks = []
        
        # 自定义收集器
        self.custom_collectors: Dict[str, Callable] = {}
        
        # 聚合配置
        self.aggregation_windows = [
            timedelta(minutes=1),
            timedelta(minutes=5),
            timedelta(minutes=15),
            timedelta(hours=1),
            timedelta(hours=6),
            timedelta(days=1)
        ]
        
        # 初始化存储
        self._init_storage()
        
        # 创建默认指标定义
        self._create_default_metrics()
        
        self.logger.info("指标收集器初始化完成")
    
    def _init_storage(self):
        """初始化存储"""
        try:
            # 确保目录存在
            Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 连接数据库
            self.db_connection = sqlite3.connect(
                self.storage_path, 
                check_same_thread=False,
                timeout=30.0
            )
            
            # 创建表
            self._create_tables()
            
            self.logger.info(f"指标存储初始化完成: {self.storage_path}")
            
        except Exception as e:
            self.logger.error(f"初始化存储失败: {e}")
            raise
    
    def _create_tables(self):
        """创建数据库表"""
        try:
            cursor = self.db_connection.cursor()
            
            # 指标值表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metric_values (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    labels TEXT,
                    timestamp DATETIME NOT NULL,
                    source TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 聚合指标表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aggregated_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    aggregation_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    labels TEXT,
                    time_window_seconds INTEGER NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME NOT NULL,
                    sample_count INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_metric_values_name_time 
                ON metric_values(metric_name, timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_aggregated_metrics_name_type_time 
                ON aggregated_metrics(metric_name, aggregation_type, start_time)
            """)
            
            self.db_connection.commit()
            
        except Exception as e:
            self.logger.error(f"创建数据库表失败: {e}")
            raise
    
    def _create_default_metrics(self):
        """创建默认指标定义"""
        default_metrics = [
            MetricDefinition(
                name="system_cpu_percent",
                metric_type=MetricType.GAUGE,
                description="系统CPU使用率",
                unit="percent",
                labels=["platform"],
                aggregation_types=[AggregationType.AVERAGE, AggregationType.MAX],
                retention_days=30,
                collection_interval=5,
                enabled=True
            ),
            MetricDefinition(
                name="system_memory_percent",
                metric_type=MetricType.GAUGE,
                description="系统内存使用率",
                unit="percent",
                labels=["platform"],
                aggregation_types=[AggregationType.AVERAGE, AggregationType.MAX],
                retention_days=30,
                collection_interval=5,
                enabled=True
            ),
            MetricDefinition(
                name="task_execution_time",
                metric_type=MetricType.TIMER,
                description="任务执行时间",
                unit="seconds",
                labels=["task_type", "platform", "status"],
                aggregation_types=[AggregationType.AVERAGE, AggregationType.PERCENTILE],
                retention_days=7,
                collection_interval=0,  # 事件驱动
                enabled=True
            ),
            MetricDefinition(
                name="ai_component_requests",
                metric_type=MetricType.COUNTER,
                description="AI组件请求数",
                unit="count",
                labels=["component", "status"],
                aggregation_types=[AggregationType.SUM, AggregationType.RATE],
                retention_days=14,
                collection_interval=0,  # 事件驱动
                enabled=True
            ),
            MetricDefinition(
                name="ai_component_response_time",
                metric_type=MetricType.HISTOGRAM,
                description="AI组件响应时间",
                unit="seconds",
                labels=["component"],
                aggregation_types=[AggregationType.AVERAGE, AggregationType.PERCENTILE],
                retention_days=7,
                collection_interval=0,  # 事件驱动
                enabled=True
            )
        ]
        
        for metric in default_metrics:
            self.metric_definitions[metric.name] = metric
    
    async def start_collection(self) -> bool:
        """启动指标收集"""
        try:
            if self.is_collecting:
                self.logger.warning("指标收集已在运行中")
                return True
            
            self.is_collecting = True
            
            # 启动收集任务
            self.collection_tasks = [
                asyncio.create_task(self._periodic_collection_loop()),
                asyncio.create_task(self._aggregation_loop()),
                asyncio.create_task(self._cleanup_loop())
            ]
            
            self.logger.info("指标收集启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"启动指标收集失败: {e}")
            self.is_collecting = False
            return False
    
    async def stop_collection(self):
        """停止指标收集"""
        try:
            self.is_collecting = False
            
            # 取消收集任务
            for task in self.collection_tasks:
                task.cancel()
            
            # 等待任务完成
            await asyncio.gather(*self.collection_tasks, return_exceptions=True)
            
            # 关闭数据库连接
            if self.db_connection:
                self.db_connection.close()
            
            self.logger.info("指标收集已停止")
            
        except Exception as e:
            self.logger.error(f"停止指标收集失败: {e}")
    
    async def _periodic_collection_loop(self):
        """周期性收集循环"""
        while self.is_collecting:
            try:
                # 收集周期性指标
                for metric_name, definition in self.metric_definitions.items():
                    if not definition.enabled or definition.collection_interval == 0:
                        continue
                    
                    # 检查是否到了收集时间
                    if await self._should_collect_metric(metric_name, definition):
                        await self._collect_periodic_metric(metric_name, definition)
                
                await asyncio.sleep(1)  # 1秒检查一次
                
            except Exception as e:
                self.logger.error(f"周期性收集循环错误: {e}")
                await asyncio.sleep(5)
    
    async def _should_collect_metric(self, metric_name: str, definition: MetricDefinition) -> bool:
        """检查是否应该收集指标"""
        try:
            # 获取最后收集时间
            last_collection = self.aggregation_cache.get(metric_name, {}).get('last_collection')
            
            if not last_collection:
                return True
            
            # 检查间隔
            elapsed = (datetime.now() - last_collection).total_seconds()
            return elapsed >= definition.collection_interval
            
        except Exception as e:
            self.logger.error(f"检查收集时间失败: {e}")
            return False
    
    async def _collect_periodic_metric(self, metric_name: str, definition: MetricDefinition):
        """收集周期性指标"""
        try:
            # 根据指标名称调用相应的收集器
            if metric_name.startswith("system_"):
                await self._collect_system_metrics(metric_name, definition)
            elif metric_name in self.custom_collectors:
                await self._collect_custom_metric(metric_name, definition)
            
            # 更新最后收集时间
            self.aggregation_cache[metric_name]['last_collection'] = datetime.now()
            
        except Exception as e:
            self.logger.error(f"收集指标 {metric_name} 失败: {e}")
    
    async def _collect_system_metrics(self, metric_name: str, definition: MetricDefinition):
        """收集系统指标"""
        try:
            import psutil
            import platform
            
            platform_name = platform.system().lower()
            
            if metric_name == "system_cpu_percent":
                value = psutil.cpu_percent(interval=1)
                await self.record_metric(
                    metric_name, value, {"platform": platform_name}, "system_collector"
                )
            
            elif metric_name == "system_memory_percent":
                memory = psutil.virtual_memory()
                await self.record_metric(
                    metric_name, memory.percent, {"platform": platform_name}, "system_collector"
                )
            
        except Exception as e:
            self.logger.error(f"收集系统指标失败: {e}")
    
    async def _collect_custom_metric(self, metric_name: str, definition: MetricDefinition):
        """收集自定义指标"""
        try:
            collector = self.custom_collectors[metric_name]
            
            if asyncio.iscoroutinefunction(collector):
                result = await collector()
            else:
                result = collector()
            
            if isinstance(result, (int, float)):
                await self.record_metric(metric_name, result, {}, "custom_collector")
            elif isinstance(result, dict):
                value = result.get('value')
                labels = result.get('labels', {})
                source = result.get('source', 'custom_collector')
                if value is not None:
                    await self.record_metric(metric_name, value, labels, source)
            
        except Exception as e:
            self.logger.error(f"收集自定义指标 {metric_name} 失败: {e}")
    
    async def record_metric(self, 
                          metric_name: str, 
                          value: Union[float, int], 
                          labels: Dict[str, str] = None, 
                          source: str = "manual") -> bool:
        """
        记录指标值
        
        Args:
            metric_name: 指标名称
            value: 指标值
            labels: 标签
            source: 数据源
            
        Returns:
            bool: 是否成功记录
        """
        try:
            labels = labels or {}
            timestamp = datetime.now()
            
            # 创建指标值对象
            metric_value = MetricValue(
                metric_name=metric_name,
                value=float(value),
                labels=labels,
                timestamp=timestamp,
                source=source
            )
            
            # 添加到内存缓存
            self.metric_cache[metric_name].append(metric_value)
            
            # 存储到数据库
            await self._store_metric_value(metric_value)
            
            self.logger.debug(f"记录指标: {metric_name} = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"记录指标失败: {e}")
            return False
    
    async def _store_metric_value(self, metric_value: MetricValue):
        """存储指标值到数据库"""
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    INSERT INTO metric_values 
                    (metric_name, value, labels, timestamp, source)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    metric_value.metric_name,
                    metric_value.value,
                    json.dumps(metric_value.labels),
                    metric_value.timestamp.isoformat(),
                    metric_value.source
                ))
                self.db_connection.commit()
                
        except Exception as e:
            self.logger.error(f"存储指标值失败: {e}")
    
    async def _aggregation_loop(self):
        """聚合循环"""
        while self.is_collecting:
            try:
                # 对每个时间窗口进行聚合
                for window in self.aggregation_windows:
                    await self._aggregate_metrics_for_window(window)
                
                await asyncio.sleep(60)  # 每分钟聚合一次
                
            except Exception as e:
                self.logger.error(f"聚合循环错误: {e}")
                await asyncio.sleep(60)
    
    async def _aggregate_metrics_for_window(self, window: timedelta):
        """为指定时间窗口聚合指标"""
        try:
            end_time = datetime.now()
            start_time = end_time - window
            
            for metric_name, definition in self.metric_definitions.items():
                if not definition.enabled:
                    continue
                
                # 获取时间窗口内的数据
                values = await self._get_metric_values(metric_name, start_time, end_time)
                
                if not values:
                    continue
                
                # 执行聚合
                for agg_type in definition.aggregation_types:
                    aggregated = await self._aggregate_values(values, agg_type, window, start_time, end_time)
                    if aggregated:
                        await self._store_aggregated_metric(aggregated)
            
        except Exception as e:
            self.logger.error(f"聚合指标失败: {e}")
    
    async def _get_metric_values(self, 
                               metric_name: str, 
                               start_time: datetime, 
                               end_time: datetime) -> List[MetricValue]:
        """获取指定时间范围的指标值"""
        try:
            values = []
            
            # 首先从内存缓存获取
            cached_values = self.metric_cache.get(metric_name, [])
            for value in cached_values:
                if start_time <= value.timestamp <= end_time:
                    values.append(value)
            
            # 如果缓存数据不足，从数据库获取
            if len(values) < 10:  # 阈值可调
                db_values = await self._get_metric_values_from_db(metric_name, start_time, end_time)
                values.extend(db_values)
            
            return values
            
        except Exception as e:
            self.logger.error(f"获取指标值失败: {e}")
            return []
    
    async def _get_metric_values_from_db(self, 
                                       metric_name: str, 
                                       start_time: datetime, 
                                       end_time: datetime) -> List[MetricValue]:
        """从数据库获取指标值"""
        try:
            values = []
            
            with self.db_lock:
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    SELECT metric_name, value, labels, timestamp, source
                    FROM metric_values
                    WHERE metric_name = ? AND timestamp BETWEEN ? AND ?
                    ORDER BY timestamp
                """, (metric_name, start_time.isoformat(), end_time.isoformat()))
                
                for row in cursor.fetchall():
                    values.append(MetricValue(
                        metric_name=row[0],
                        value=row[1],
                        labels=json.loads(row[2]) if row[2] else {},
                        timestamp=datetime.fromisoformat(row[3]),
                        source=row[4]
                    ))
            
            return values
            
        except Exception as e:
            self.logger.error(f"从数据库获取指标值失败: {e}")
            return []
    
    async def _aggregate_values(self, 
                              values: List[MetricValue], 
                              agg_type: AggregationType,
                              window: timedelta,
                              start_time: datetime,
                              end_time: datetime) -> Optional[AggregatedMetric]:
        """聚合指标值"""
        try:
            if not values:
                return None
            
            numeric_values = [v.value for v in values]
            
            # 计算聚合值
            if agg_type == AggregationType.SUM:
                agg_value = sum(numeric_values)
            elif agg_type == AggregationType.AVERAGE:
                agg_value = statistics.mean(numeric_values)
            elif agg_type == AggregationType.MIN:
                agg_value = min(numeric_values)
            elif agg_type == AggregationType.MAX:
                agg_value = max(numeric_values)
            elif agg_type == AggregationType.COUNT:
                agg_value = len(numeric_values)
            elif agg_type == AggregationType.PERCENTILE:
                agg_value = np.percentile(numeric_values, 95)  # 95th percentile
            elif agg_type == AggregationType.RATE:
                # 计算速率（每秒）
                time_span = window.total_seconds()
                agg_value = len(numeric_values) / time_span if time_span > 0 else 0
            else:
                return None
            
            # 合并标签（简化处理，取第一个值的标签）
            labels = values[0].labels if values else {}
            
            return AggregatedMetric(
                metric_name=values[0].metric_name,
                aggregation_type=agg_type,
                value=agg_value,
                labels=labels,
                time_window=window,
                start_time=start_time,
                end_time=end_time,
                sample_count=len(values)
            )
            
        except Exception as e:
            self.logger.error(f"聚合值失败: {e}")
            return None
    
    async def _store_aggregated_metric(self, aggregated: AggregatedMetric):
        """存储聚合指标"""
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    INSERT INTO aggregated_metrics 
                    (metric_name, aggregation_type, value, labels, time_window_seconds, 
                     start_time, end_time, sample_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    aggregated.metric_name,
                    aggregated.aggregation_type.value,
                    aggregated.value,
                    json.dumps(aggregated.labels),
                    int(aggregated.time_window.total_seconds()),
                    aggregated.start_time.isoformat(),
                    aggregated.end_time.isoformat(),
                    aggregated.sample_count
                ))
                self.db_connection.commit()
                
        except Exception as e:
            self.logger.error(f"存储聚合指标失败: {e}")
    
    async def _cleanup_loop(self):
        """清理循环"""
        while self.is_collecting:
            try:
                await asyncio.sleep(3600)  # 每小时清理一次
                
                # 清理过期数据
                await self._cleanup_expired_data()
                
            except Exception as e:
                self.logger.error(f"清理循环错误: {e}")
    
    async def _cleanup_expired_data(self):
        """清理过期数据"""
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                
                # 清理过期的原始指标值
                for metric_name, definition in self.metric_definitions.items():
                    cutoff_date = datetime.now() - timedelta(days=definition.retention_days)
                    
                    cursor.execute("""
                        DELETE FROM metric_values 
                        WHERE metric_name = ? AND timestamp < ?
                    """, (metric_name, cutoff_date.isoformat()))
                
                # 清理过期的聚合指标（保留更长时间）
                cutoff_date = datetime.now() - timedelta(days=90)
                cursor.execute("""
                    DELETE FROM aggregated_metrics 
                    WHERE start_time < ?
                """, (cutoff_date.isoformat(),))
                
                self.db_connection.commit()
                
                self.logger.info("清理过期数据完成")
                
        except Exception as e:
            self.logger.error(f"清理过期数据失败: {e}")
    
    def register_custom_collector(self, metric_name: str, collector: Callable):
        """
        注册自定义收集器
        
        Args:
            metric_name: 指标名称
            collector: 收集器函数
        """
        self.custom_collectors[metric_name] = collector
        self.logger.info(f"注册自定义收集器: {metric_name}")
    
    def add_metric_definition(self, definition: MetricDefinition) -> bool:
        """
        添加指标定义
        
        Args:
            definition: 指标定义
            
        Returns:
            bool: 是否成功添加
        """
        try:
            self.metric_definitions[definition.name] = definition
            self.logger.info(f"添加指标定义: {definition.name}")
            return True
        except Exception as e:
            self.logger.error(f"添加指标定义失败: {e}")
            return False
    
    async def get_metric_data(self, 
                            metric_name: str, 
                            start_time: datetime, 
                            end_time: datetime,
                            aggregation_type: Optional[AggregationType] = None) -> List[Dict[str, Any]]:
        """
        获取指标数据
        
        Args:
            metric_name: 指标名称
            start_time: 开始时间
            end_time: 结束时间
            aggregation_type: 聚合类型（可选）
            
        Returns:
            List[Dict[str, Any]]: 指标数据
        """
        try:
            if aggregation_type:
                return await self._get_aggregated_data(metric_name, start_time, end_time, aggregation_type)
            else:
                return await self._get_raw_data(metric_name, start_time, end_time)
                
        except Exception as e:
            self.logger.error(f"获取指标数据失败: {e}")
            return []
    
    async def _get_raw_data(self, metric_name: str, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """获取原始数据"""
        try:
            values = await self._get_metric_values(metric_name, start_time, end_time)
            return [asdict(value) for value in values]
            
        except Exception as e:
            self.logger.error(f"获取原始数据失败: {e}")
            return []
    
    async def _get_aggregated_data(self, 
                                 metric_name: str, 
                                 start_time: datetime, 
                                 end_time: datetime,
                                 aggregation_type: AggregationType) -> List[Dict[str, Any]]:
        """获取聚合数据"""
        try:
            data = []
            
            with self.db_lock:
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    SELECT metric_name, aggregation_type, value, labels, 
                           time_window_seconds, start_time, end_time, sample_count
                    FROM aggregated_metrics
                    WHERE metric_name = ? AND aggregation_type = ? 
                          AND start_time >= ? AND end_time <= ?
                    ORDER BY start_time
                """, (
                    metric_name, 
                    aggregation_type.value, 
                    start_time.isoformat(), 
                    end_time.isoformat()
                ))
                
                for row in cursor.fetchall():
                    data.append({
                        "metric_name": row[0],
                        "aggregation_type": row[1],
                        "value": row[2],
                        "labels": json.loads(row[3]) if row[3] else {},
                        "time_window_seconds": row[4],
                        "start_time": row[5],
                        "end_time": row[6],
                        "sample_count": row[7]
                    })
            
            return data
            
        except Exception as e:
            self.logger.error(f"获取聚合数据失败: {e}")
            return []
    
    def get_metric_definitions(self) -> Dict[str, Dict[str, Any]]:
        """获取所有指标定义"""
        return {name: asdict(definition) for name, definition in self.metric_definitions.items()}
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取收集器统计信息"""
        try:
            total_metrics = 0
            enabled_metrics = 0
            
            for definition in self.metric_definitions.values():
                total_metrics += 1
                if definition.enabled:
                    enabled_metrics += 1
            
            # 获取数据库统计
            with self.db_lock:
                cursor = self.db_connection.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM metric_values")
                total_values = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM aggregated_metrics")
                total_aggregated = cursor.fetchone()[0]
            
            return {
                "is_collecting": self.is_collecting,
                "total_metric_definitions": total_metrics,
                "enabled_metric_definitions": enabled_metrics,
                "custom_collectors": len(self.custom_collectors),
                "total_metric_values": total_values,
                "total_aggregated_metrics": total_aggregated,
                "cache_size": sum(len(cache) for cache in self.metric_cache.values()),
                "aggregation_windows": len(self.aggregation_windows),
                "storage_path": self.storage_path
            }
            
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {"error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """获取收集器状态"""
        return {
            "status": "active" if self.is_collecting else "inactive",
            "collection_enabled": self.is_collecting,
            "storage_initialized": self.db_connection is not None,
            "statistics": self.get_statistics()
        }

