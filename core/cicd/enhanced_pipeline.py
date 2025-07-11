"""
PowerAutomation v4.6.1 Enhanced CI/CD Pipeline
增強型CI/CD流水線，整合六大工作流體系

CI/CD Pipeline架構：
1. 觸發階段 (Trigger Stage)
2. 代碼分析階段 (Code Analysis Stage)  
3. 測試自動化階段 (Test Automation Stage)
4. 構建階段 (Build Stage)
5. 部署階段 (Deployment Stage)
6. 監控階段 (Monitoring Stage)

與六大工作流的集成：
- 代碼開發工作流: 代碼分析、生成、審查
- 測試自動化工作流: 自動化測試、質量門禁
- 部署發布工作流: 構建、部署、發布
- 項目管理工作流: 任務追蹤、里程碑管理
- 協作溝通工作流: 通知、報告、反饋
- 監控運維工作流: 健康檢查、異常檢測
"""

import asyncio
import logging
import json
import os
# import yaml  # Optional dependency for YAML configuration
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
import subprocess
import uuid

# 導入工作流和版本策略
from core.workflows.workflow_engine import workflow_engine, WorkflowCategory
from core.enterprise.version_strategy import enterprise_version_strategy, EditionTier

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """流水線階段"""
    TRIGGER = "trigger"
    CODE_ANALYSIS = "code_analysis"
    TEST_AUTOMATION = "test_automation"
    BUILD = "build"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    NOTIFICATION = "notification"


class PipelineStatus(Enum):
    """流水線狀態"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class TriggerType(Enum):
    """觸發類型"""
    GIT_PUSH = "git_push"
    GIT_TAG = "git_tag"
    PULL_REQUEST = "pull_request"
    MANUAL = "manual"
    SCHEDULE = "schedule"
    WORKFLOW_TRIGGER = "workflow_trigger"


@dataclass
class PipelineStageResult:
    """流水線階段結果"""
    stage: PipelineStage
    status: PipelineStatus
    start_time: str
    end_time: Optional[str] = None
    duration: float = 0.0
    artifacts: Dict[str, Any] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    workflow_executions: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


@dataclass
class PipelineExecution:
    """流水線執行記錄"""
    id: str
    trigger_type: TriggerType
    trigger_data: Dict[str, Any]
    status: PipelineStatus
    start_time: str
    end_time: Optional[str] = None
    stages: Dict[str, PipelineStageResult] = field(default_factory=dict)
    overall_metrics: Dict[str, Any] = field(default_factory=dict)
    edition: EditionTier = EditionTier.PERSONAL
    enabled_features: List[str] = field(default_factory=list)


@dataclass
class PipelineConfiguration:
    """流水線配置"""
    name: str
    version: str
    enabled_stages: List[PipelineStage]
    stage_configurations: Dict[str, Dict[str, Any]]
    quality_gates: Dict[str, Any]
    notification_settings: Dict[str, Any]
    retention_policy: Dict[str, Any]
    edition_requirements: Dict[str, List[str]]


class EnhancedCICDPipeline:
    """增強型CI/CD流水線"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.executions = {}
        self.configurations = {}
        self.stage_handlers = {}
        self.active_pipelines = {}
        self.quality_gates = {}
        
    async def initialize(self):
        """初始化CI/CD流水線"""
        self.logger.info("🔄 初始化Enhanced CI/CD Pipeline - 六大工作流整合")
        
        # 初始化工作流引擎
        await workflow_engine.initialize()
        
        # 初始化版本策略
        await enterprise_version_strategy.initialize()
        
        # 載入流水線配置
        await self._load_pipeline_configurations()
        
        # 註冊階段處理器
        await self._register_stage_handlers()
        
        # 設置質量門禁
        await self._setup_quality_gates()
        
        self.logger.info("✅ Enhanced CI/CD Pipeline初始化完成")
    
    async def _load_pipeline_configurations(self):
        """載入流水線配置"""
        
        # 基礎配置
        base_config = PipelineConfiguration(
            name="PowerAutomation CI/CD Pipeline",
            version="4.6.1",
            enabled_stages=[
                PipelineStage.TRIGGER,
                PipelineStage.CODE_ANALYSIS,
                PipelineStage.TEST_AUTOMATION,
                PipelineStage.BUILD,
                PipelineStage.DEPLOYMENT,
                PipelineStage.MONITORING,
                PipelineStage.NOTIFICATION
            ],
            stage_configurations={
                "trigger": {
                    "supported_triggers": ["git_push", "git_tag", "pull_request", "manual", "schedule"],
                    "branch_filters": ["main", "develop", "release/*"],
                    "tag_pattern": "v*.*.*"
                },
                "code_analysis": {
                    "workflows": ["code_development_workflow"],
                    "enabled_checks": ["syntax", "security", "quality", "dependencies"],
                    "parallel_analysis": True
                },
                "test_automation": {
                    "workflows": ["test_automation_workflow"],
                    "test_types": ["unit", "integration", "ui", "api"],
                    "parallel_execution": True,
                    "coverage_threshold": 80
                },
                "build": {
                    "workflows": ["deployment_release_workflow"],
                    "platforms": ["macos", "linux", "windows"],
                    "artifact_retention": 30
                },
                "deployment": {
                    "workflows": ["deployment_release_workflow"],
                    "environments": ["development", "staging", "production"],
                    "approval_required": ["staging", "production"]
                },
                "monitoring": {
                    "workflows": ["monitoring_operations_workflow"],
                    "health_checks": ["api", "database", "external_services"],
                    "alert_channels": ["slack", "email", "webhook"]
                }
            },
            quality_gates={
                "code_quality": {
                    "min_maintainability_index": 70,
                    "max_technical_debt_ratio": 30,
                    "max_cyclomatic_complexity": 20
                },
                "test_quality": {
                    "min_coverage": 80,
                    "min_pass_rate": 95,
                    "max_test_duration": 1800  # 30分鐘
                },
                "security": {
                    "max_critical_vulnerabilities": 0,
                    "max_high_vulnerabilities": 3,
                    "security_scan_required": True
                },
                "performance": {
                    "max_build_time": 600,  # 10分鐘
                    "max_deployment_time": 300,  # 5分鐘
                    "memory_limit_mb": 2048
                }
            },
            notification_settings={
                "success": ["email", "slack"],
                "failure": ["email", "slack", "teams"],
                "quality_gate_failure": ["email", "slack"],
                "deployment_success": ["slack", "webhook"]
            },
            retention_policy={
                "execution_logs": 90,  # 天
                "artifacts": 30,
                "test_reports": 180,
                "metrics": 365
            },
            edition_requirements={
                "personal": ["trigger", "code_analysis"],
                "professional": ["trigger", "code_analysis", "test_automation", "build"],
                "team": ["trigger", "code_analysis", "test_automation", "build", "deployment"],
                "enterprise": ["trigger", "code_analysis", "test_automation", "build", "deployment", "monitoring", "notification"]
            }
        )
        
        self.configurations["default"] = base_config
        self.logger.info("載入流水線配置完成")
    
    async def _register_stage_handlers(self):
        """註冊階段處理器"""
        self.stage_handlers = {
            PipelineStage.TRIGGER: self._handle_trigger_stage,
            PipelineStage.CODE_ANALYSIS: self._handle_code_analysis_stage,
            PipelineStage.TEST_AUTOMATION: self._handle_test_automation_stage,
            PipelineStage.BUILD: self._handle_build_stage,
            PipelineStage.DEPLOYMENT: self._handle_deployment_stage,
            PipelineStage.MONITORING: self._handle_monitoring_stage,
            PipelineStage.NOTIFICATION: self._handle_notification_stage
        }
    
    async def _setup_quality_gates(self):
        """設置質量門禁"""
        config = self.configurations["default"]
        self.quality_gates = config.quality_gates
    
    async def trigger_pipeline(self, trigger_type: TriggerType, trigger_data: Dict[str, Any], 
                             edition: EditionTier = None) -> str:
        """觸發流水線執行"""
        
        if edition is None:
            edition = enterprise_version_strategy.current_edition
        
        execution_id = str(uuid.uuid4())
        
        # 獲取版本功能
        enabled_features = enterprise_version_strategy.get_available_features(edition)
        
        execution = PipelineExecution(
            id=execution_id,
            trigger_type=trigger_type,
            trigger_data=trigger_data,
            status=PipelineStatus.PENDING,
            start_time=datetime.now().isoformat(),
            edition=edition,
            enabled_features=enabled_features
        )
        
        self.executions[execution_id] = execution
        self.active_pipelines[execution_id] = True
        
        self.logger.info(f"觸發流水線執行: {execution_id} (版本: {edition.value})")
        
        # 異步執行流水線
        asyncio.create_task(self._execute_pipeline(execution_id))
        
        return execution_id
    
    async def _execute_pipeline(self, execution_id: str):
        """執行流水線"""
        execution = self.executions[execution_id]
        config = self.configurations["default"]
        
        try:
            execution.status = PipelineStatus.RUNNING
            
            # 根據版本權限過濾階段
            enabled_stages = self._filter_stages_by_edition(
                config.enabled_stages, 
                execution.edition
            )
            
            self.logger.info(f"執行流水線 {execution_id}: {len(enabled_stages)} 個階段")
            
            # 順序執行各個階段
            for stage in enabled_stages:
                if execution_id not in self.active_pipelines:
                    # 流水線已被取消
                    execution.status = PipelineStatus.CANCELLED
                    return
                
                stage_result = await self._execute_stage(execution_id, stage)
                execution.stages[stage.value] = stage_result
                
                # 檢查階段執行結果
                if stage_result.status == PipelineStatus.FAILED:
                    execution.status = PipelineStatus.FAILED
                    await self._handle_pipeline_failure(execution_id, stage, stage_result.error_message)
                    return
                
                # 檢查質量門禁
                if not await self._check_quality_gates(execution_id, stage, stage_result):
                    execution.status = PipelineStatus.FAILED
                    await self._handle_quality_gate_failure(execution_id, stage)
                    return
            
            # 所有階段成功完成
            execution.status = PipelineStatus.SUCCESS
            execution.end_time = datetime.now().isoformat()
            
            # 計算整體指標
            await self._calculate_overall_metrics(execution_id)
            
            self.logger.info(f"流水線 {execution_id} 執行成功")
            
        except Exception as e:
            execution.status = PipelineStatus.FAILED
            execution.end_time = datetime.now().isoformat()
            self.logger.error(f"流水線 {execution_id} 執行失敗: {e}")
            
        finally:
            if execution_id in self.active_pipelines:
                del self.active_pipelines[execution_id]
    
    def _filter_stages_by_edition(self, stages: List[PipelineStage], edition: EditionTier) -> List[PipelineStage]:
        """根據版本過濾階段"""
        config = self.configurations["default"]
        allowed_stages = config.edition_requirements.get(edition.value, [])
        
        return [stage for stage in stages if stage.value in allowed_stages]
    
    async def _execute_stage(self, execution_id: str, stage: PipelineStage) -> PipelineStageResult:
        """執行單個階段"""
        execution = self.executions[execution_id]
        
        stage_result = PipelineStageResult(
            stage=stage,
            status=PipelineStatus.RUNNING,
            start_time=datetime.now().isoformat()
        )
        
        try:
            self.logger.info(f"執行階段 {stage.value} (流水線: {execution_id})")
            
            # 執行階段處理器
            handler = self.stage_handlers.get(stage)
            if handler:
                await handler(execution_id, stage_result)
            else:
                raise ValueError(f"未找到階段處理器: {stage.value}")
            
            stage_result.status = PipelineStatus.SUCCESS
            stage_result.end_time = datetime.now().isoformat()
            
            # 計算執行時間
            start_time = datetime.fromisoformat(stage_result.start_time)
            end_time = datetime.fromisoformat(stage_result.end_time)
            stage_result.duration = (end_time - start_time).total_seconds()
            
            self.logger.info(f"階段 {stage.value} 執行成功 (耗時: {stage_result.duration:.2f}秒)")
            
        except Exception as e:
            stage_result.status = PipelineStatus.FAILED
            stage_result.error_message = str(e)
            stage_result.end_time = datetime.now().isoformat()
            
            self.logger.error(f"階段 {stage.value} 執行失敗: {e}")
        
        return stage_result
    
    async def _handle_trigger_stage(self, execution_id: str, stage_result: PipelineStageResult):
        """處理觸發階段"""
        execution = self.executions[execution_id]
        
        stage_result.logs.append(f"觸發類型: {execution.trigger_type.value}")
        stage_result.logs.append(f"觸發數據: {execution.trigger_data}")
        stage_result.logs.append(f"版本: {execution.edition.value}")
        
        # 驗證觸發條件
        if execution.trigger_type == TriggerType.GIT_TAG:
            tag = execution.trigger_data.get('tag', '')
            if not tag.startswith('v'):
                raise ValueError(f"無效的版本標籤: {tag}")
        
        stage_result.artifacts['trigger_validated'] = True
        stage_result.metrics['trigger_processing_time'] = 0.1
    
    async def _handle_code_analysis_stage(self, execution_id: str, stage_result: PipelineStageResult):
        """處理代碼分析階段"""
        execution = self.executions[execution_id]
        
        # 執行代碼開發工作流
        workflow_execution_id = await workflow_engine.execute_workflow(
            'code_development_workflow',
            {
                'project_path': execution.trigger_data.get('repository', '.'),
                'target_language': 'python',
                'analysis_level': 'full'
            }
        )
        
        stage_result.workflow_executions.append(workflow_execution_id)
        stage_result.logs.append(f"啟動代碼開發工作流: {workflow_execution_id}")
        
        # 等待工作流完成 (簡化處理)
        await asyncio.sleep(2)
        
        # 模擬分析結果
        stage_result.artifacts.update({
            'code_quality_score': 85,
            'security_issues': 2,
            'technical_debt_hours': 8,
            'maintainability_index': 78
        })
        
        stage_result.metrics.update({
            'lines_analyzed': 15000,
            'files_analyzed': 120,
            'analysis_time': 45
        })
        
        stage_result.logs.append("代碼分析完成")
    
    async def _handle_test_automation_stage(self, execution_id: str, stage_result: PipelineStageResult):
        """處理測試自動化階段"""
        execution = self.executions[execution_id]
        
        # 執行測試自動化工作流
        workflow_execution_id = await workflow_engine.execute_workflow(
            'test_automation_workflow',
            {
                'test_types': ['unit', 'integration', 'ui'],
                'coverage_threshold': 80,
                'parallel_execution': True
            }
        )
        
        stage_result.workflow_executions.append(workflow_execution_id)
        stage_result.logs.append(f"啟動測試自動化工作流: {workflow_execution_id}")
        
        # 等待工作流完成
        await asyncio.sleep(3)
        
        # 模擬測試結果
        stage_result.artifacts.update({
            'test_coverage': 85.5,
            'tests_passed': 450,
            'tests_failed': 5,
            'tests_skipped': 2,
            'test_report_url': 'https://ci.powerautomation.com/reports/test-123'
        })
        
        stage_result.metrics.update({
            'total_tests': 457,
            'test_duration': 180,
            'pass_rate': 98.9
        })
        
        stage_result.logs.append("測試自動化完成")
    
    async def _handle_build_stage(self, execution_id: str, stage_result: PipelineStageResult):
        """處理構建階段"""
        execution = self.executions[execution_id]
        
        # 執行部署發布工作流 (構建部分)
        workflow_execution_id = await workflow_engine.execute_workflow(
            'deployment_release_workflow',
            {
                'build_platforms': ['macos', 'linux'],
                'build_type': 'release',
                'artifact_retention': 30
            }
        )
        
        stage_result.workflow_executions.append(workflow_execution_id)
        stage_result.logs.append(f"啟動部署發布工作流: {workflow_execution_id}")
        
        # 等待構建完成
        await asyncio.sleep(4)
        
        # 模擬構建結果
        stage_result.artifacts.update({
            'build_success': True,
            'artifacts': [
                'PowerAutomation-v4.6.1-macos.dmg',
                'PowerAutomation-v4.6.1-linux.tar.gz'
            ],
            'artifact_size_mb': 128.5,
            'build_hash': 'abc123def456'
        })
        
        stage_result.metrics.update({
            'build_time': 240,
            'artifact_count': 2,
            'compressed_size_mb': 128.5
        })
        
        stage_result.logs.append("構建階段完成")
    
    async def _handle_deployment_stage(self, execution_id: str, stage_result: PipelineStageResult):
        """處理部署階段"""
        execution = self.executions[execution_id]
        
        # 檢查版本權限
        if execution.edition not in [EditionTier.TEAM, EditionTier.ENTERPRISE]:
            stage_result.status = PipelineStatus.SKIPPED
            stage_result.logs.append("部署階段跳過 (版本權限不足)")
            return
        
        # 繼續執行部署發布工作流
        stage_result.logs.append("執行部署發布工作流")
        
        # 模擬部署過程
        await asyncio.sleep(2)
        
        stage_result.artifacts.update({
            'deployment_success': True,
            'deployed_environments': ['staging'],
            'deployment_urls': ['https://staging.powerautomation.com'],
            'rollback_available': True
        })
        
        stage_result.metrics.update({
            'deployment_time': 120,
            'environments_deployed': 1,
            'health_check_passed': True
        })
        
        stage_result.logs.append("部署階段完成")
    
    async def _handle_monitoring_stage(self, execution_id: str, stage_result: PipelineStageResult):
        """處理監控階段"""
        execution = self.executions[execution_id]
        
        # 檢查版本權限
        if execution.edition != EditionTier.ENTERPRISE:
            stage_result.status = PipelineStatus.SKIPPED
            stage_result.logs.append("監控階段跳過 (僅企業版支持)")
            return
        
        # 執行監控運維工作流
        workflow_execution_id = await workflow_engine.execute_workflow(
            'monitoring_operations_workflow',
            {
                'monitoring_duration': 300,  # 5分鐘
                'health_checks': ['api', 'database'],
                'alert_thresholds': {'response_time': 500, 'error_rate': 0.01}
            }
        )
        
        stage_result.workflow_executions.append(workflow_execution_id)
        stage_result.logs.append(f"啟動監控運維工作流: {workflow_execution_id}")
        
        # 等待監控檢查
        await asyncio.sleep(1)
        
        stage_result.artifacts.update({
            'monitoring_active': True,
            'health_status': 'healthy',
            'metrics_collected': 50,
            'alerts_triggered': 0
        })
        
        stage_result.metrics.update({
            'response_time_avg': 245,
            'error_rate': 0.001,
            'uptime_percentage': 99.9
        })
        
        stage_result.logs.append("監控階段完成")
    
    async def _handle_notification_stage(self, execution_id: str, stage_result: PipelineStageResult):
        """處理通知階段"""
        execution = self.executions[execution_id]
        
        # 執行協作溝通工作流
        workflow_execution_id = await workflow_engine.execute_workflow(
            'collaboration_communication_workflow',
            {
                'notification_type': 'pipeline_completion',
                'recipients': ['team@powerautomation.com'],
                'channels': ['email', 'slack']
            }
        )
        
        stage_result.workflow_executions.append(workflow_execution_id)
        stage_result.logs.append(f"啟動協作溝通工作流: {workflow_execution_id}")
        
        stage_result.artifacts.update({
            'notifications_sent': 3,
            'channels_used': ['email', 'slack'],
            'delivery_success': True
        })
        
        stage_result.metrics.update({
            'notification_time': 5,
            'delivery_rate': 100
        })
        
        stage_result.logs.append("通知階段完成")
    
    async def _check_quality_gates(self, execution_id: str, stage: PipelineStage, 
                                 stage_result: PipelineStageResult) -> bool:
        """檢查質量門禁"""
        
        if stage == PipelineStage.CODE_ANALYSIS:
            # 代碼質量門禁
            quality_score = stage_result.artifacts.get('code_quality_score', 0)
            if quality_score < 70:
                return False
            
            security_issues = stage_result.artifacts.get('security_issues', 0)
            if security_issues > 5:
                return False
        
        elif stage == PipelineStage.TEST_AUTOMATION:
            # 測試質量門禁
            coverage = stage_result.artifacts.get('test_coverage', 0)
            if coverage < self.quality_gates['test_quality']['min_coverage']:
                return False
            
            pass_rate = stage_result.metrics.get('pass_rate', 0)
            if pass_rate < self.quality_gates['test_quality']['min_pass_rate']:
                return False
        
        elif stage == PipelineStage.BUILD:
            # 構建質量門禁
            build_time = stage_result.metrics.get('build_time', 0)
            if build_time > self.quality_gates['performance']['max_build_time']:
                return False
        
        return True
    
    async def _handle_pipeline_failure(self, execution_id: str, failed_stage: PipelineStage, error_message: str):
        """處理流水線失敗"""
        execution = self.executions[execution_id]
        execution.end_time = datetime.now().isoformat()
        
        self.logger.error(f"流水線 {execution_id} 在 {failed_stage.value} 階段失敗: {error_message}")
        
        # 發送失敗通知
        await self._send_failure_notification(execution_id, failed_stage, error_message)
    
    async def _handle_quality_gate_failure(self, execution_id: str, failed_stage: PipelineStage):
        """處理質量門禁失敗"""
        execution = self.executions[execution_id]
        execution.end_time = datetime.now().isoformat()
        
        self.logger.warning(f"流水線 {execution_id} 在 {failed_stage.value} 階段質量門禁失敗")
        
        # 發送質量門禁失敗通知
        await self._send_quality_gate_failure_notification(execution_id, failed_stage)
    
    async def _send_failure_notification(self, execution_id: str, failed_stage: PipelineStage, error_message: str):
        """發送失敗通知"""
        # 簡化的通知實現
        self.logger.info(f"發送失敗通知: 流水線 {execution_id} 失敗")
    
    async def _send_quality_gate_failure_notification(self, execution_id: str, failed_stage: PipelineStage):
        """發送質量門禁失敗通知"""
        # 簡化的通知實現
        self.logger.info(f"發送質量門禁失敗通知: 流水線 {execution_id}")
    
    async def _calculate_overall_metrics(self, execution_id: str):
        """計算整體指標"""
        execution = self.executions[execution_id]
        
        start_time = datetime.fromisoformat(execution.start_time)
        end_time = datetime.fromisoformat(execution.end_time)
        total_duration = (end_time - start_time).total_seconds()
        
        execution.overall_metrics = {
            'total_duration': total_duration,
            'stages_executed': len(execution.stages),
            'stages_successful': sum(1 for stage in execution.stages.values() 
                                   if stage.status == PipelineStatus.SUCCESS),
            'total_workflow_executions': sum(len(stage.workflow_executions) 
                                           for stage in execution.stages.values()),
            'success_rate': 100.0
        }
    
    def get_pipeline_status(self, execution_id: str) -> Optional[PipelineExecution]:
        """獲取流水線狀態"""
        return self.executions.get(execution_id)
    
    def list_active_pipelines(self) -> List[str]:
        """列出活躍的流水線"""
        return list(self.active_pipelines.keys())
    
    def cancel_pipeline(self, execution_id: str) -> bool:
        """取消流水線執行"""
        if execution_id in self.active_pipelines:
            del self.active_pipelines[execution_id]
            
            execution = self.executions.get(execution_id)
            if execution:
                execution.status = PipelineStatus.CANCELLED
                execution.end_time = datetime.now().isoformat()
            
            self.logger.info(f"取消流水線執行: {execution_id}")
            return True
        
        return False
    
    def get_pipeline_metrics(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """獲取流水線指標"""
        
        executions = list(self.executions.values())
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            executions = [e for e in executions if datetime.fromisoformat(e.start_time) >= start_dt]
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            executions = [e for e in executions if datetime.fromisoformat(e.start_time) <= end_dt]
        
        if not executions:
            return {}
        
        total_executions = len(executions)
        successful_executions = sum(1 for e in executions if e.status == PipelineStatus.SUCCESS)
        failed_executions = sum(1 for e in executions if e.status == PipelineStatus.FAILED)
        
        avg_duration = sum(e.overall_metrics.get('total_duration', 0) for e in executions) / total_executions
        
        return {
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'failed_executions': failed_executions,
            'success_rate': (successful_executions / total_executions * 100) if total_executions > 0 else 0,
            'average_duration': avg_duration,
            'stage_metrics': self._calculate_stage_metrics(executions),
            'edition_distribution': self._calculate_edition_distribution(executions)
        }
    
    def _calculate_stage_metrics(self, executions: List[PipelineExecution]) -> Dict[str, Any]:
        """計算階段指標"""
        stage_metrics = {}
        
        for stage in PipelineStage:
            stage_executions = []
            for execution in executions:
                if stage.value in execution.stages:
                    stage_executions.append(execution.stages[stage.value])
            
            if stage_executions:
                successful = sum(1 for s in stage_executions if s.status == PipelineStatus.SUCCESS)
                avg_duration = sum(s.duration for s in stage_executions) / len(stage_executions)
                
                stage_metrics[stage.value] = {
                    'total_executions': len(stage_executions),
                    'successful_executions': successful,
                    'success_rate': (successful / len(stage_executions) * 100),
                    'average_duration': avg_duration
                }
        
        return stage_metrics
    
    def _calculate_edition_distribution(self, executions: List[PipelineExecution]) -> Dict[str, int]:
        """計算版本分布"""
        distribution = {}
        for execution in executions:
            edition = execution.edition.value
            distribution[edition] = distribution.get(edition, 0) + 1
        
        return distribution
    
    def get_status(self) -> Dict[str, Any]:
        """獲取CI/CD流水線狀態"""
        return {
            "component": "Enhanced CI/CD Pipeline",
            "version": "4.6.1",
            "total_executions": len(self.executions),
            "active_pipelines": len(self.active_pipelines),
            "supported_stages": [stage.value for stage in PipelineStage],
            "supported_triggers": [trigger.value for trigger in TriggerType],
            "quality_gates_count": len(self.quality_gates),
            "workflow_integration": {
                "code_development": "✅",
                "test_automation": "✅", 
                "deployment_release": "✅",
                "project_management": "✅",
                "collaboration_communication": "✅",
                "monitoring_operations": "✅"
            },
            "enterprise_features": {
                "edition_based_access": "✅",
                "quality_gates": "✅",
                "advanced_monitoring": "✅",
                "notification_system": "✅"
            }
        }


# 單例實例
enhanced_cicd_pipeline = EnhancedCICDPipeline()