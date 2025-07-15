#!/usr/bin/env python3
"""
PowerAutomation Core 數據收集和反饋系統
v4.6.9.4 - 全面的數據收集、分析和反饋機制
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import sqlite3
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict, deque
import threading
import queue

logger = logging.getLogger(__name__)

class DataType(Enum):
    """數據類型"""
    USER_INTERACTION = "user_interaction"
    SYSTEM_PERFORMANCE = "system_performance"
    ERROR_EVENT = "error_event"
    LEARNING_PROGRESS = "learning_progress"
    CONTEXT_USAGE = "context_usage"
    CLAUDE_INTERACTION = "claude_interaction"
    COMPONENT_METRICS = "component_metrics"
    WORKFLOW_EXECUTION = "workflow_execution"
    OPTIMIZATION_RESULT = "optimization_result"
    FEEDBACK_RESPONSE = "feedback_response"

class DataPriority(Enum):
    """數據優先級"""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

@dataclass
class DataPoint:
    """數據點"""
    id: str
    data_type: DataType
    priority: DataPriority
    timestamp: float
    source: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    processed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return asdict(self)

@dataclass
class FeedbackLoop:
    """反饋循環"""
    id: str
    name: str
    input_data_types: List[DataType]
    output_actions: List[str]
    processing_function: Callable
    enabled: bool = True
    last_execution: float = 0.0
    execution_count: int = 0
    success_rate: float = 0.0

@dataclass
class CollectionRule:
    """收集規則"""
    id: str
    name: str
    data_type: DataType
    conditions: Dict[str, Any]
    sampling_rate: float = 1.0
    enabled: bool = True
    created_at: float = 0.0

class DataCollectionSystem:
    """數據收集系統"""
    
    def __init__(self, db_path: str = "data_collection.db"):
        self.db_path = Path(db_path)
        self.connection = None
        
        # 數據收集
        self.data_queue = queue.Queue(maxsize=10000)
        self.collection_rules: Dict[str, CollectionRule] = {}
        self.data_processors: Dict[DataType, List[Callable]] = defaultdict(list)
        
        # 反饋循環
        self.feedback_loops: Dict[str, FeedbackLoop] = {}
        self.feedback_results = deque(maxlen=1000)
        
        # 實時監控
        self.real_time_metrics = defaultdict(deque)
        self.metric_thresholds = {}
        self.alert_callbacks = []
        
        # 統計信息
        self.collection_stats = {
            "total_data_points": 0,
            "data_by_type": defaultdict(int),
            "data_by_priority": defaultdict(int),
            "processing_errors": 0,
            "feedback_executions": 0,
            "alerts_triggered": 0
        }
        
        # 任務管理
        self.collection_tasks = []
        self.processing_tasks = []
        self.feedback_tasks = []
        self.is_running = False
        
    async def initialize(self):
        """初始化數據收集系統"""
        logger.info("📊 初始化數據收集系統...")
        
        try:
            # 創建數據庫
            await self._create_database()
            
            # 載入收集規則
            await self._load_collection_rules()
            
            # 設置默認反饋循環
            await self._setup_default_feedback_loops()
            
            # 啟動收集任務
            await self._start_collection_tasks()
            
            self.is_running = True
            logger.info("✅ 數據收集系統初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 數據收集系統初始化失敗: {e}")
            raise
    
    async def _create_database(self):
        """創建數據庫"""
        self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
        
        create_sql = """
        CREATE TABLE IF NOT EXISTS data_points (
            id TEXT PRIMARY KEY,
            data_type TEXT NOT NULL,
            priority TEXT NOT NULL,
            timestamp REAL NOT NULL,
            source TEXT NOT NULL,
            data TEXT NOT NULL,
            metadata TEXT,
            processed BOOLEAN DEFAULT 0,
            created_at REAL DEFAULT (strftime('%s', 'now'))
        );
        
        CREATE TABLE IF NOT EXISTS feedback_results (
            id TEXT PRIMARY KEY,
            feedback_loop_id TEXT NOT NULL,
            input_data TEXT NOT NULL,
            output_actions TEXT NOT NULL,
            execution_time REAL NOT NULL,
            success BOOLEAN NOT NULL,
            timestamp REAL NOT NULL,
            error_message TEXT
        );
        
        CREATE TABLE IF NOT EXISTS collection_rules (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            data_type TEXT NOT NULL,
            conditions TEXT NOT NULL,
            sampling_rate REAL DEFAULT 1.0,
            enabled BOOLEAN DEFAULT 1,
            created_at REAL DEFAULT (strftime('%s', 'now'))
        );
        
        CREATE INDEX IF NOT EXISTS idx_data_type ON data_points(data_type);
        CREATE INDEX IF NOT EXISTS idx_timestamp ON data_points(timestamp);
        CREATE INDEX IF NOT EXISTS idx_priority ON data_points(priority);
        CREATE INDEX IF NOT EXISTS idx_processed ON data_points(processed);
        """
        
        self.connection.executescript(create_sql)
        self.connection.commit()
    
    async def _load_collection_rules(self):
        """載入收集規則"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM collection_rules WHERE enabled = 1")
            
            for row in cursor.fetchall():
                rule = CollectionRule(
                    id=row[0],
                    name=row[1],
                    data_type=DataType(row[2]),
                    conditions=json.loads(row[3]),
                    sampling_rate=row[4],
                    enabled=bool(row[5]),
                    created_at=row[6]
                )
                self.collection_rules[rule.id] = rule
            
            # 如果沒有規則，創建默認規則
            if not self.collection_rules:
                await self._create_default_rules()
            
            logger.info(f"📋 載入 {len(self.collection_rules)} 個收集規則")
            
        except Exception as e:
            logger.error(f"❌ 載入收集規則失敗: {e}")
            await self._create_default_rules()
    
    async def _create_default_rules(self):
        """創建默認收集規則"""
        default_rules = [
            CollectionRule(
                id="user_interaction_high",
                name="用戶交互高優先級",
                data_type=DataType.USER_INTERACTION,
                conditions={"min_response_time": 0, "max_response_time": 10000},
                sampling_rate=1.0,
                enabled=True,
                created_at=time.time()
            ),
            CollectionRule(
                id="claude_interaction_all",
                name="Claude 交互全記錄",
                data_type=DataType.CLAUDE_INTERACTION,
                conditions={"min_satisfaction": 0.0},
                sampling_rate=1.0,
                enabled=True,
                created_at=time.time()
            ),
            CollectionRule(
                id="error_critical",
                name="關鍵錯誤事件",
                data_type=DataType.ERROR_EVENT,
                conditions={"severity": ["critical", "high"]},
                sampling_rate=1.0,
                enabled=True,
                created_at=time.time()
            ),
            CollectionRule(
                id="performance_monitoring",
                name="性能監控",
                data_type=DataType.SYSTEM_PERFORMANCE,
                conditions={"cpu_threshold": 80, "memory_threshold": 80},
                sampling_rate=0.1,
                enabled=True,
                created_at=time.time()
            ),
            CollectionRule(
                id="learning_progress",
                name="學習進度跟蹤",
                data_type=DataType.LEARNING_PROGRESS,
                conditions={"success_rate_threshold": 0.7},
                sampling_rate=1.0,
                enabled=True,
                created_at=time.time()
            )
        ]
        
        cursor = self.connection.cursor()
        
        for rule in default_rules:
            cursor.execute("""
                INSERT OR REPLACE INTO collection_rules
                (id, name, data_type, conditions, sampling_rate, enabled, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                rule.id,
                rule.name,
                rule.data_type.value,
                json.dumps(rule.conditions),
                rule.sampling_rate,
                rule.enabled,
                rule.created_at
            ))
            
            self.collection_rules[rule.id] = rule
        
        self.connection.commit()
        logger.info(f"✅ 創建 {len(default_rules)} 個默認收集規則")
    
    async def _setup_default_feedback_loops(self):
        """設置默認反饋循環"""
        # 性能優化反饋循環
        self.feedback_loops["performance_optimization"] = FeedbackLoop(
            id="performance_optimization",
            name="性能優化反饋",
            input_data_types=[DataType.SYSTEM_PERFORMANCE, DataType.COMPONENT_METRICS],
            output_actions=["optimize_memory", "adjust_thresholds", "scale_resources"],
            processing_function=self._process_performance_feedback,
            enabled=True
        )
        
        # 學習改進反饋循環
        self.feedback_loops["learning_improvement"] = FeedbackLoop(
            id="learning_improvement",
            name="學習改進反饋",
            input_data_types=[DataType.LEARNING_PROGRESS, DataType.CLAUDE_INTERACTION],
            output_actions=["adjust_learning_rate", "update_models", "optimize_context"],
            processing_function=self._process_learning_feedback,
            enabled=True
        )
        
        # 錯誤預防反饋循環
        self.feedback_loops["error_prevention"] = FeedbackLoop(
            id="error_prevention",
            name="錯誤預防反饋",
            input_data_types=[DataType.ERROR_EVENT, DataType.COMPONENT_METRICS],
            output_actions=["update_error_patterns", "adjust_monitoring", "preventive_fixes"],
            processing_function=self._process_error_feedback,
            enabled=True
        )
        
        # 用戶體驗優化反饋循環
        self.feedback_loops["user_experience"] = FeedbackLoop(
            id="user_experience",
            name="用戶體驗優化",
            input_data_types=[DataType.USER_INTERACTION, DataType.FEEDBACK_RESPONSE],
            output_actions=["personalize_interface", "adjust_responses", "improve_workflow"],
            processing_function=self._process_user_feedback,
            enabled=True
        )
        
        logger.info(f"🔄 設置 {len(self.feedback_loops)} 個反饋循環")
    
    async def _start_collection_tasks(self):
        """啟動收集任務"""
        # 數據處理任務
        processing_task = asyncio.create_task(self._process_data_queue())
        self.processing_tasks.append(processing_task)
        
        # 反饋循環任務
        feedback_task = asyncio.create_task(self._execute_feedback_loops())
        self.feedback_tasks.append(feedback_task)
        
        # 實時監控任務
        monitoring_task = asyncio.create_task(self._monitor_real_time_metrics())
        self.collection_tasks.append(monitoring_task)
        
        # 數據清理任務
        cleanup_task = asyncio.create_task(self._cleanup_old_data())
        self.collection_tasks.append(cleanup_task)
        
        logger.info("🚀 數據收集任務啟動完成")
    
    async def collect_data(self, 
                         data_type: DataType,
                         source: str,
                         data: Dict[str, Any],
                         priority: DataPriority = DataPriority.NORMAL,
                         metadata: Dict[str, Any] = None):
        """收集數據"""
        try:
            # 檢查收集規則
            if not self._should_collect_data(data_type, data):
                return
            
            # 創建數據點
            data_point = DataPoint(
                id=str(uuid.uuid4()),
                data_type=data_type,
                priority=priority,
                timestamp=time.time(),
                source=source,
                data=data,
                metadata=metadata or {},
                processed=False
            )
            
            # 添加到隊列
            if not self.data_queue.full():
                self.data_queue.put(data_point)
                
                # 更新統計
                self.collection_stats["total_data_points"] += 1
                self.collection_stats["data_by_type"][data_type.value] += 1
                self.collection_stats["data_by_priority"][priority.value] += 1
                
                # 更新實時指標
                self._update_real_time_metrics(data_type, data)
                
                logger.debug(f"📊 收集數據: {data_type.value} from {source}")
            else:
                logger.warning("⚠️ 數據隊列已滿，丟棄數據點")
                
        except Exception as e:
            logger.error(f"❌ 收集數據失敗: {e}")
    
    def _should_collect_data(self, data_type: DataType, data: Dict[str, Any]) -> bool:
        """檢查是否應該收集數據"""
        for rule in self.collection_rules.values():
            if rule.data_type == data_type and rule.enabled:
                # 檢查採樣率
                if np.random.random() > rule.sampling_rate:
                    return False
                
                # 檢查條件
                if self._check_rule_conditions(rule, data):
                    return True
        
        return False
    
    def _check_rule_conditions(self, rule: CollectionRule, data: Dict[str, Any]) -> bool:
        """檢查規則條件"""
        try:
            conditions = rule.conditions
            
            # 檢查響應時間條件
            if "min_response_time" in conditions:
                response_time = data.get("response_time", 0)
                if response_time < conditions["min_response_time"]:
                    return False
            
            if "max_response_time" in conditions:
                response_time = data.get("response_time", float('inf'))
                if response_time > conditions["max_response_time"]:
                    return False
            
            # 檢查滿意度條件
            if "min_satisfaction" in conditions:
                satisfaction = data.get("user_satisfaction", 0)
                if satisfaction < conditions["min_satisfaction"]:
                    return False
            
            # 檢查嚴重程度條件
            if "severity" in conditions:
                severity = data.get("severity", "")
                if severity not in conditions["severity"]:
                    return False
            
            # 檢查閾值條件
            if "cpu_threshold" in conditions:
                cpu_usage = data.get("cpu_usage", 0)
                if cpu_usage < conditions["cpu_threshold"]:
                    return False
            
            if "memory_threshold" in conditions:
                memory_usage = data.get("memory_usage", 0)
                if memory_usage < conditions["memory_threshold"]:
                    return False
            
            # 檢查成功率條件
            if "success_rate_threshold" in conditions:
                success_rate = data.get("success_rate", 0)
                if success_rate < conditions["success_rate_threshold"]:
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"檢查規則條件失敗: {e}")
            return True  # 默認收集
    
    def _update_real_time_metrics(self, data_type: DataType, data: Dict[str, Any]):
        """更新實時指標"""
        try:
            # 更新通用指標
            self.real_time_metrics["data_rate"].append(time.time())
            
            # 更新特定類型指標
            if data_type == DataType.SYSTEM_PERFORMANCE:
                if "cpu_usage" in data:
                    self.real_time_metrics["cpu_usage"].append(data["cpu_usage"])
                if "memory_usage" in data:
                    self.real_time_metrics["memory_usage"].append(data["memory_usage"])
            
            elif data_type == DataType.CLAUDE_INTERACTION:
                if "response_time" in data:
                    self.real_time_metrics["response_time"].append(data["response_time"])
                if "user_satisfaction" in data:
                    self.real_time_metrics["user_satisfaction"].append(data["user_satisfaction"])
            
            elif data_type == DataType.ERROR_EVENT:
                self.real_time_metrics["error_rate"].append(time.time())
            
            elif data_type == DataType.LEARNING_PROGRESS:
                if "success_rate" in data:
                    self.real_time_metrics["learning_success_rate"].append(data["success_rate"])
            
            # 保持指標隊列大小
            for metric_name, metric_queue in self.real_time_metrics.items():
                if len(metric_queue) > 100:
                    # 移除最舊的數據
                    for _ in range(len(metric_queue) - 100):
                        metric_queue.popleft()
            
        except Exception as e:
            logger.error(f"❌ 更新實時指標失敗: {e}")
    
    async def _process_data_queue(self):
        """處理數據隊列"""
        while self.is_running:
            try:
                # 批量處理數據
                batch = []
                batch_size = 50
                
                for _ in range(batch_size):
                    try:
                        data_point = self.data_queue.get(timeout=1.0)
                        batch.append(data_point)
                    except queue.Empty:
                        break
                
                if batch:
                    await self._process_data_batch(batch)
                
                # 短暫休息
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ 處理數據隊列失敗: {e}")
                await asyncio.sleep(1)
    
    async def _process_data_batch(self, batch: List[DataPoint]):
        """處理數據批次"""
        try:
            # 保存到數據庫
            cursor = self.connection.cursor()
            
            for data_point in batch:
                cursor.execute("""
                    INSERT INTO data_points
                    (id, data_type, priority, timestamp, source, data, metadata, processed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data_point.id,
                    data_point.data_type.value,
                    data_point.priority.value,
                    data_point.timestamp,
                    data_point.source,
                    json.dumps(data_point.data),
                    json.dumps(data_point.metadata),
                    data_point.processed
                ))
            
            self.connection.commit()
            
            # 調用數據處理器
            await self._call_data_processors(batch)
            
            logger.debug(f"📊 處理數據批次: {len(batch)} 個數據點")
            
        except Exception as e:
            logger.error(f"❌ 處理數據批次失敗: {e}")
            self.collection_stats["processing_errors"] += 1
    
    async def _call_data_processors(self, batch: List[DataPoint]):
        """調用數據處理器"""
        try:
            # 按數據類型分組
            grouped_data = defaultdict(list)
            for data_point in batch:
                grouped_data[data_point.data_type].append(data_point)
            
            # 調用對應的處理器
            for data_type, data_points in grouped_data.items():
                if data_type in self.data_processors:
                    for processor in self.data_processors[data_type]:
                        try:
                            await processor(data_points)
                        except Exception as e:
                            logger.error(f"❌ 數據處理器失敗 ({data_type.value}): {e}")
            
        except Exception as e:
            logger.error(f"❌ 調用數據處理器失敗: {e}")
    
    async def _execute_feedback_loops(self):
        """執行反饋循環"""
        while self.is_running:
            try:
                for loop_id, feedback_loop in self.feedback_loops.items():
                    if feedback_loop.enabled:
                        # 檢查是否到了執行時間
                        current_time = time.time()
                        if current_time - feedback_loop.last_execution >= 60:  # 1分鐘間隔
                            await self._execute_single_feedback_loop(feedback_loop)
                
                # 等待下一次檢查
                await asyncio.sleep(30)  # 30秒檢查一次
                
            except Exception as e:
                logger.error(f"❌ 執行反饋循環失敗: {e}")
                await asyncio.sleep(60)
    
    async def _execute_single_feedback_loop(self, feedback_loop: FeedbackLoop):
        """執行單個反饋循環"""
        try:
            start_time = time.time()
            
            # 收集輸入數據
            input_data = await self._collect_feedback_input_data(feedback_loop)
            
            if not input_data:
                return
            
            # 執行處理函數
            output_actions = await feedback_loop.processing_function(input_data)
            
            # 記錄結果
            execution_time = time.time() - start_time
            success = bool(output_actions)
            
            # 更新反饋循環統計
            feedback_loop.last_execution = time.time()
            feedback_loop.execution_count += 1
            
            # 更新成功率
            if success:
                feedback_loop.success_rate = (
                    feedback_loop.success_rate * 0.9 + 0.1
                )
            else:
                feedback_loop.success_rate = (
                    feedback_loop.success_rate * 0.9
                )
            
            # 保存結果
            await self._save_feedback_result(
                feedback_loop.id,
                input_data,
                output_actions,
                execution_time,
                success
            )
            
            self.collection_stats["feedback_executions"] += 1
            
            logger.debug(f"🔄 執行反饋循環: {feedback_loop.name}")
            
        except Exception as e:
            logger.error(f"❌ 執行反饋循環失敗 ({feedback_loop.name}): {e}")
            
            # 保存失敗結果
            await self._save_feedback_result(
                feedback_loop.id,
                {},
                [],
                time.time() - start_time,
                False,
                str(e)
            )
    
    async def _collect_feedback_input_data(self, feedback_loop: FeedbackLoop) -> Dict[str, Any]:
        """收集反饋輸入數據"""
        try:
            input_data = {}
            
            # 從數據庫查詢相關數據
            cursor = self.connection.cursor()
            
            for data_type in feedback_loop.input_data_types:
                cursor.execute("""
                    SELECT data FROM data_points
                    WHERE data_type = ? AND timestamp > ?
                    ORDER BY timestamp DESC
                    LIMIT 50
                """, (data_type.value, time.time() - 3600))  # 最近1小時
                
                rows = cursor.fetchall()
                data_points = []
                
                for row in rows:
                    try:
                        data_points.append(json.loads(row[0]))
                    except json.JSONDecodeError:
                        continue
                
                input_data[data_type.value] = data_points
            
            return input_data
            
        except Exception as e:
            logger.error(f"❌ 收集反饋輸入數據失敗: {e}")
            return {}
    
    async def _save_feedback_result(self,
                                  feedback_loop_id: str,
                                  input_data: Dict[str, Any],
                                  output_actions: List[str],
                                  execution_time: float,
                                  success: bool,
                                  error_message: str = None):
        """保存反饋結果"""
        try:
            result_id = str(uuid.uuid4())
            
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO feedback_results
                (id, feedback_loop_id, input_data, output_actions, execution_time, success, timestamp, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result_id,
                feedback_loop_id,
                json.dumps(input_data),
                json.dumps(output_actions),
                execution_time,
                success,
                time.time(),
                error_message
            ))
            
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"❌ 保存反饋結果失敗: {e}")
    
    async def _monitor_real_time_metrics(self):
        """監控實時指標"""
        while self.is_running:
            try:
                # 檢查閾值
                await self._check_metric_thresholds()
                
                # 等待下一次檢查
                await asyncio.sleep(30)  # 30秒檢查一次
                
            except Exception as e:
                logger.error(f"❌ 監控實時指標失敗: {e}")
                await asyncio.sleep(60)
    
    async def _check_metric_thresholds(self):
        """檢查指標閾值"""
        try:
            current_time = time.time()
            
            # 檢查各種指標
            metrics_to_check = {
                "cpu_usage": {"threshold": 90, "duration": 300},
                "memory_usage": {"threshold": 85, "duration": 300},
                "error_rate": {"threshold": 10, "duration": 300},  # 每5分鐘10個錯誤
                "response_time": {"threshold": 5000, "duration": 300}
            }
            
            for metric_name, config in metrics_to_check.items():
                if metric_name in self.real_time_metrics:
                    await self._check_single_metric_threshold(
                        metric_name,
                        config["threshold"],
                        config["duration"],
                        current_time
                    )
            
        except Exception as e:
            logger.error(f"❌ 檢查指標閾值失敗: {e}")
    
    async def _check_single_metric_threshold(self,
                                           metric_name: str,
                                           threshold: float,
                                           duration: float,
                                           current_time: float):
        """檢查單個指標閾值"""
        try:
            metric_queue = self.real_time_metrics[metric_name]
            
            if not metric_queue:
                return
            
            # 過濾指定時間內的數據
            if metric_name == "error_rate":
                # 錯誤率計算
                recent_errors = [
                    timestamp for timestamp in metric_queue
                    if current_time - timestamp <= duration
                ]
                current_value = len(recent_errors)
            else:
                # 其他指標的平均值
                recent_values = [
                    value for value in metric_queue
                    if isinstance(value, (int, float))
                ]
                current_value = np.mean(recent_values) if recent_values else 0
            
            # 檢查是否超過閾值
            if current_value > threshold:
                await self._trigger_alert(metric_name, current_value, threshold)
            
        except Exception as e:
            logger.error(f"❌ 檢查單個指標閾值失敗 ({metric_name}): {e}")
    
    async def _trigger_alert(self, metric_name: str, current_value: float, threshold: float):
        """觸發警報"""
        try:
            alert_data = {
                "metric_name": metric_name,
                "current_value": current_value,
                "threshold": threshold,
                "timestamp": time.time(),
                "severity": "high" if current_value > threshold * 1.5 else "medium"
            }
            
            # 調用警報回調
            for callback in self.alert_callbacks:
                try:
                    await callback(alert_data)
                except Exception as e:
                    logger.error(f"❌ 警報回調失敗: {e}")
            
            # 收集警報數據
            await self.collect_data(
                data_type=DataType.SYSTEM_PERFORMANCE,
                source="alert_system",
                data=alert_data,
                priority=DataPriority.HIGH
            )
            
            self.collection_stats["alerts_triggered"] += 1
            
            logger.warning(f"🚨 觸發警報: {metric_name} = {current_value:.2f} (閾值: {threshold})")
            
        except Exception as e:
            logger.error(f"❌ 觸發警報失敗: {e}")
    
    async def _cleanup_old_data(self):
        """清理舊數據"""
        while self.is_running:
            try:
                # 清理30天前的數據
                cutoff_time = time.time() - (30 * 24 * 3600)
                
                cursor = self.connection.cursor()
                
                # 清理數據點
                cursor.execute("""
                    DELETE FROM data_points
                    WHERE timestamp < ?
                """, (cutoff_time,))
                
                # 清理反饋結果
                cursor.execute("""
                    DELETE FROM feedback_results
                    WHERE timestamp < ?
                """, (cutoff_time,))
                
                self.connection.commit()
                
                logger.info("🧹 清理舊數據完成")
                
                # 等待下一次清理（每天清理一次）
                await asyncio.sleep(86400)
                
            except Exception as e:
                logger.error(f"❌ 清理舊數據失敗: {e}")
                await asyncio.sleep(3600)  # 錯誤時1小時後重試
    
    # 反饋循環處理函數
    async def _process_performance_feedback(self, input_data: Dict[str, Any]) -> List[str]:
        """處理性能反饋"""
        actions = []
        
        # 分析系統性能數據
        performance_data = input_data.get("system_performance", [])
        
        if performance_data:
            # 計算平均 CPU 和內存使用率
            cpu_usage = [d.get("cpu_usage", 0) for d in performance_data if "cpu_usage" in d]
            memory_usage = [d.get("memory_usage", 0) for d in performance_data if "memory_usage" in d]
            
            if cpu_usage:
                avg_cpu = np.mean(cpu_usage)
                if avg_cpu > 80:
                    actions.append("optimize_cpu_usage")
            
            if memory_usage:
                avg_memory = np.mean(memory_usage)
                if avg_memory > 80:
                    actions.append("optimize_memory_usage")
        
        return actions
    
    async def _process_learning_feedback(self, input_data: Dict[str, Any]) -> List[str]:
        """處理學習反饋"""
        actions = []
        
        # 分析學習進度數據
        learning_data = input_data.get("learning_progress", [])
        claude_data = input_data.get("claude_interaction", [])
        
        if learning_data:
            success_rates = [d.get("success_rate", 0) for d in learning_data if "success_rate" in d]
            if success_rates:
                avg_success_rate = np.mean(success_rates)
                if avg_success_rate < 0.7:
                    actions.append("adjust_learning_parameters")
        
        if claude_data:
            satisfactions = [d.get("user_satisfaction", 0) for d in claude_data if "user_satisfaction" in d]
            if satisfactions:
                avg_satisfaction = np.mean(satisfactions)
                if avg_satisfaction < 0.6:
                    actions.append("improve_response_quality")
        
        return actions
    
    async def _process_error_feedback(self, input_data: Dict[str, Any]) -> List[str]:
        """處理錯誤反饋"""
        actions = []
        
        # 分析錯誤事件數據
        error_data = input_data.get("error_event", [])
        
        if error_data:
            # 統計錯誤類型
            error_types = defaultdict(int)
            for error in error_data:
                error_type = error.get("error_type", "unknown")
                error_types[error_type] += 1
            
            # 如果某種錯誤頻繁出現，採取行動
            for error_type, count in error_types.items():
                if count > 5:  # 超過5次
                    actions.append(f"prevent_{error_type}_errors")
        
        return actions
    
    async def _process_user_feedback(self, input_data: Dict[str, Any]) -> List[str]:
        """處理用戶反饋"""
        actions = []
        
        # 分析用戶交互數據
        user_data = input_data.get("user_interaction", [])
        feedback_data = input_data.get("feedback_response", [])
        
        if user_data:
            response_times = [d.get("response_time", 0) for d in user_data if "response_time" in d]
            if response_times:
                avg_response_time = np.mean(response_times)
                if avg_response_time > 3000:  # 超過3秒
                    actions.append("optimize_response_time")
        
        if feedback_data:
            ratings = [d.get("rating", 0) for d in feedback_data if "rating" in d]
            if ratings:
                avg_rating = np.mean(ratings)
                if avg_rating < 0.7:
                    actions.append("improve_user_experience")
        
        return actions
    
    # 公共 API 方法
    def add_data_processor(self, data_type: DataType, processor: Callable):
        """添加數據處理器"""
        self.data_processors[data_type].append(processor)
        logger.info(f"➕ 添加數據處理器: {data_type.value}")
    
    def add_alert_callback(self, callback: Callable):
        """添加警報回調"""
        self.alert_callbacks.append(callback)
        logger.info("🚨 添加警報回調")
    
    def remove_alert_callback(self, callback: Callable):
        """移除警報回調"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
            logger.info("🗑️ 移除警報回調")
    
    async def get_collection_statistics(self) -> Dict[str, Any]:
        """獲取收集統計"""
        try:
            # 計算實時指標統計
            real_time_stats = {}
            for metric_name, metric_queue in self.real_time_metrics.items():
                if metric_queue:
                    if metric_name in ["error_rate", "data_rate"]:
                        # 計算頻率
                        recent_count = len([
                            timestamp for timestamp in metric_queue
                            if time.time() - timestamp <= 300  # 最近5分鐘
                        ])
                        real_time_stats[metric_name] = recent_count
                    else:
                        # 計算平均值
                        values = [v for v in metric_queue if isinstance(v, (int, float))]
                        real_time_stats[metric_name] = np.mean(values) if values else 0
            
            # 獲取數據庫統計
            cursor = self.connection.cursor()
            
            # 數據點統計
            cursor.execute("SELECT COUNT(*) FROM data_points")
            total_data_points = cursor.fetchone()[0]
            
            # 反饋結果統計
            cursor.execute("SELECT COUNT(*) FROM feedback_results")
            total_feedback_results = cursor.fetchone()[0]
            
            # 反饋循環統計
            feedback_loop_stats = {}
            for loop_id, loop in self.feedback_loops.items():
                feedback_loop_stats[loop_id] = {
                    "name": loop.name,
                    "enabled": loop.enabled,
                    "execution_count": loop.execution_count,
                    "success_rate": loop.success_rate,
                    "last_execution": loop.last_execution
                }
            
            return {
                "collection_stats": self.collection_stats,
                "real_time_metrics": real_time_stats,
                "database_stats": {
                    "total_data_points": total_data_points,
                    "total_feedback_results": total_feedback_results
                },
                "feedback_loops": feedback_loop_stats,
                "collection_rules": len(self.collection_rules),
                "is_running": self.is_running
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取收集統計失敗: {e}")
            return {}
    
    async def cleanup(self):
        """清理資源"""
        logger.info("🧹 清理數據收集系統...")
        
        # 停止運行
        self.is_running = False
        
        # 取消所有任務
        all_tasks = self.collection_tasks + self.processing_tasks + self.feedback_tasks
        for task in all_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # 處理剩餘的數據隊列
        remaining_data = []
        while not self.data_queue.empty():
            try:
                data_point = self.data_queue.get_nowait()
                remaining_data.append(data_point)
            except queue.Empty:
                break
        
        if remaining_data:
            await self._process_data_batch(remaining_data)
        
        # 關閉數據庫連接
        if self.connection:
            self.connection.close()
        
        logger.info("✅ 數據收集系統清理完成")

# 創建全局數據收集系統實例
data_collection_system = None

async def initialize_data_collection_system():
    """初始化數據收集系統"""
    global data_collection_system
    
    if data_collection_system is None:
        data_collection_system = DataCollectionSystem()
        await data_collection_system.initialize()
    
    return data_collection_system

async def get_data_collection_system():
    """獲取數據收集系統實例"""
    global data_collection_system
    
    if data_collection_system is None:
        data_collection_system = await initialize_data_collection_system()
    
    return data_collection_system

# 測試函數
async def main():
    """測試數據收集系統"""
    print("🧪 測試數據收集系統...")
    
    # 初始化系統
    system = await initialize_data_collection_system()
    
    # 測試數據收集
    await system.collect_data(
        data_type=DataType.CLAUDE_INTERACTION,
        source="test_system",
        data={
            "user_input": "如何使用 Python 進行數據分析？",
            "claude_response": "Python 數據分析可以使用 pandas、numpy 等庫...",
            "response_time": 2500,
            "user_satisfaction": 0.85
        },
        priority=DataPriority.HIGH
    )
    
    # 測試性能數據收集
    await system.collect_data(
        data_type=DataType.SYSTEM_PERFORMANCE,
        source="system_monitor",
        data={
            "cpu_usage": 75.5,
            "memory_usage": 68.2,
            "disk_usage": 45.8
        },
        priority=DataPriority.NORMAL
    )
    
    # 等待處理
    await asyncio.sleep(2)
    
    # 獲取統計
    stats = await system.get_collection_statistics()
    print(f"📊 收集統計: {stats}")
    
    # 清理
    await system.cleanup()
    print("✅ 測試完成")

if __name__ == "__main__":
    asyncio.run(main())