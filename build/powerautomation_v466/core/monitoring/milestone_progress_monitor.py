#!/usr/bin/env python3
"""
PowerAutomation Milestone Progress Monitoring System
自動化里程碑進度監控系統

功能：
- 自動追蹤項目里程碑進度
- 生成進度報告和預警
- 集成GitHub API監控代碼變更
- 支持多項目並行監控
- 自動風險評估和建議

Author: PowerAutomation Team
Version: 1.0.0
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import aiohttp
import git
from github import Github
import yaml


class MilestoneStatus(Enum):
    """里程碑狀態枚舉"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress" 
    DELAYED = "delayed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RiskLevel(Enum):
    """風險等級枚舉"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TaskProgress:
    """任務進度數據類"""
    id: str
    name: str
    description: str
    status: MilestoneStatus
    progress: float  # 0-100%
    estimated_hours: int
    actual_hours: int
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    assignee: Optional[str]
    dependencies: List[str]
    blockers: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            **asdict(self),
            'status': self.status.value,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None
        }


@dataclass
class MilestoneProgress:
    """里程碑進度數據類"""
    milestone_id: str
    name: str
    version: str
    quarter: str
    status: MilestoneStatus
    overall_progress: float
    tasks: List[TaskProgress]
    start_date: datetime
    target_date: datetime
    completion_date: Optional[datetime]
    risk_level: RiskLevel
    risk_factors: List[str]
    blockers: List[str]
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'milestone_id': self.milestone_id,
            'name': self.name,
            'version': self.version,
            'quarter': self.quarter,
            'status': self.status.value,
            'overall_progress': self.overall_progress,
            'tasks': [task.to_dict() for task in self.tasks],
            'start_date': self.start_date.isoformat(),
            'target_date': self.target_date.isoformat(),
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'risk_level': self.risk_level.value,
            'risk_factors': self.risk_factors,
            'blockers': self.blockers,
            'last_updated': self.last_updated.isoformat()
        }


class GitHubIntegration:
    """GitHub集成類"""
    
    def __init__(self, token: str, repo_name: str):
        self.github = Github(token)
        self.repo = self.github.get_repo(repo_name)
        self.logger = logging.getLogger(__name__)
    
    async def get_commit_activity(self, since_date: datetime) -> Dict[str, Any]:
        """獲取提交活動統計"""
        commits = self.repo.get_commits(since=since_date)
        
        activity_data = {
            'total_commits': commits.totalCount,
            'contributors': set(),
            'files_changed': 0,
            'lines_added': 0,
            'lines_deleted': 0,
            'daily_activity': {}
        }
        
        for commit in commits:
            activity_data['contributors'].add(commit.author.login if commit.author else 'unknown')
            commit_date = commit.commit.author.date.strftime('%Y-%m-%d')
            
            if commit_date not in activity_data['daily_activity']:
                activity_data['daily_activity'][commit_date] = 0
            activity_data['daily_activity'][commit_date] += 1
            
            # 統計文件變更
            if commit.stats:
                activity_data['files_changed'] += len(commit.files)
                activity_data['lines_added'] += commit.stats.additions
                activity_data['lines_deleted'] += commit.stats.deletions
        
        activity_data['contributors'] = list(activity_data['contributors'])
        return activity_data
    
    async def get_pull_request_status(self) -> Dict[str, Any]:
        """獲取PR狀態統計"""
        open_prs = self.repo.get_pulls(state='open')
        closed_prs = self.repo.get_pulls(state='closed')
        
        return {
            'open_count': open_prs.totalCount,
            'closed_count': closed_prs.totalCount,
            'recent_prs': [
                {
                    'title': pr.title,
                    'state': pr.state,
                    'created_at': pr.created_at.isoformat(),
                    'author': pr.user.login
                }
                for pr in list(open_prs)[:5]
            ]
        }
    
    async def get_issue_metrics(self) -> Dict[str, Any]:
        """獲取Issues指標"""
        open_issues = self.repo.get_issues(state='open')
        closed_issues = self.repo.get_issues(state='closed')
        
        return {
            'open_count': open_issues.totalCount,
            'closed_count': closed_issues.totalCount,
            'labels': [issue.labels for issue in list(open_issues)[:10]]
        }


class MilestoneProgressMonitor:
    """里程碑進度監控主類"""
    
    def __init__(self, config_path: str = "monitoring_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.logger = self._setup_logging()
        self.github_integration = None
        
        if self.config.get('github', {}).get('token'):
            self.github_integration = GitHubIntegration(
                self.config['github']['token'],
                self.config['github']['repo']
            )
    
    def _load_config(self) -> Dict[str, Any]:
        """加載配置文件"""
        if not self.config_path.exists():
            # 創建默認配置
            default_config = {
                'monitoring': {
                    'check_interval_hours': 6,
                    'report_interval_hours': 24,
                    'risk_threshold_days': 7
                },
                'github': {
                    'token': os.getenv('GITHUB_TOKEN', ''),
                    'repo': 'alexchuang650730/aicore0711'
                },
                'notifications': {
                    'slack_webhook': os.getenv('SLACK_WEBHOOK', ''),
                    'email_recipients': []
                },
                'milestones': {
                    'data_file': 'milestones_data.json',
                    'backup_dir': 'backups'
                }
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
            
            return default_config
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _setup_logging(self) -> logging.Logger:
        """設置日志系統"""
        logger = logging.getLogger('milestone_monitor')
        logger.setLevel(logging.INFO)
        
        # 文件處理器
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(
            log_dir / f'milestone_monitor_{datetime.now().strftime("%Y%m%d")}.log',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # 控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def load_milestones_data(self) -> List[MilestoneProgress]:
        """加載里程碑數據"""
        data_file = Path(self.config['milestones']['data_file'])
        
        if not data_file.exists():
            # 創建初始里程碑數據
            initial_milestones = self._create_initial_milestones()
            self.save_milestones_data(initial_milestones)
            return initial_milestones
        
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            milestones = []
            for milestone_data in data:
                # 解析任務
                tasks = []
                for task_data in milestone_data.get('tasks', []):
                    task = TaskProgress(
                        id=task_data['id'],
                        name=task_data['name'],
                        description=task_data['description'],
                        status=MilestoneStatus(task_data['status']),
                        progress=task_data['progress'],
                        estimated_hours=task_data['estimated_hours'],
                        actual_hours=task_data['actual_hours'],
                        start_date=datetime.fromisoformat(task_data['start_date']) if task_data['start_date'] else None,
                        end_date=datetime.fromisoformat(task_data['end_date']) if task_data['end_date'] else None,
                        assignee=task_data['assignee'],
                        dependencies=task_data['dependencies'],
                        blockers=task_data['blockers']
                    )
                    tasks.append(task)
                
                # 解析里程碑
                milestone = MilestoneProgress(
                    milestone_id=milestone_data['milestone_id'],
                    name=milestone_data['name'],
                    version=milestone_data['version'],
                    quarter=milestone_data['quarter'],
                    status=MilestoneStatus(milestone_data['status']),
                    overall_progress=milestone_data['overall_progress'],
                    tasks=tasks,
                    start_date=datetime.fromisoformat(milestone_data['start_date']),
                    target_date=datetime.fromisoformat(milestone_data['target_date']),
                    completion_date=datetime.fromisoformat(milestone_data['completion_date']) if milestone_data['completion_date'] else None,
                    risk_level=RiskLevel(milestone_data['risk_level']),
                    risk_factors=milestone_data['risk_factors'],
                    blockers=milestone_data['blockers'],
                    last_updated=datetime.fromisoformat(milestone_data['last_updated'])
                )
                milestones.append(milestone)
            
            return milestones
            
        except Exception as e:
            self.logger.error(f"加載里程碑數據失敗: {e}")
            return self._create_initial_milestones()
    
    def save_milestones_data(self, milestones: List[MilestoneProgress]):
        """保存里程碑數據"""
        data_file = Path(self.config['milestones']['data_file'])
        backup_dir = Path(self.config['milestones']['backup_dir'])
        backup_dir.mkdir(exist_ok=True)
        
        # 創建備份
        if data_file.exists():
            backup_file = backup_dir / f"milestones_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            data_file.rename(backup_file)
        
        # 保存新數據
        data = [milestone.to_dict() for milestone in milestones]
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"里程碑數據已保存到 {data_file}")
    
    def _create_initial_milestones(self) -> List[MilestoneProgress]:
        """創建初始里程碑數據"""
        now = datetime.now()
        
        # Q3 2025 里程碑 - 企業化轉型
        q3_tasks = [
            TaskProgress(
                id="q3_task_1",
                name="需求分析工作流 (8090)",
                description="實現個人版/團隊版/企業版需求分析功能",
                status=MilestoneStatus.IN_PROGRESS,
                progress=25.0,
                estimated_hours=160,
                actual_hours=40,
                start_date=now,
                end_date=None,
                assignee="development_team",
                dependencies=[],
                blockers=[]
            ),
            TaskProgress(
                id="q3_task_2", 
                name="架構設計工作流 (8091)",
                description="智能引擎架構設計分層實施",
                status=MilestoneStatus.NOT_STARTED,
                progress=0.0,
                estimated_hours=160,
                actual_hours=0,
                start_date=None,
                end_date=None,
                assignee="architecture_team",
                dependencies=["q3_task_1"],
                blockers=[]
            ),
            TaskProgress(
                id="q3_task_3",
                name="編碼實現工作流 (8092)",
                description="KiloCode引擎三版本差異化開發",
                status=MilestoneStatus.NOT_STARTED,
                progress=0.0,
                estimated_hours=240,
                actual_hours=0,
                start_date=None,
                end_date=None,
                assignee="development_team",
                dependencies=["q3_task_2"],
                blockers=[]
            ),
            TaskProgress(
                id="q3_task_4",
                name="測試驗證工作流 (8093)",
                description="模板測試生成引擎實施",
                status=MilestoneStatus.NOT_STARTED,
                progress=0.0,
                estimated_hours=160,
                actual_hours=0,
                start_date=None,
                end_date=None,
                assignee="qa_team",
                dependencies=["q3_task_3"],
                blockers=[]
            ),
            TaskProgress(
                id="q3_task_5",
                name="部署發布工作流 (8094)",
                description="Release Manager + 插件系統開發",
                status=MilestoneStatus.NOT_STARTED,
                progress=0.0,
                estimated_hours=160,
                actual_hours=0,
                start_date=None,
                end_date=None,
                assignee="devops_team",
                dependencies=["q3_task_4"],
                blockers=[]
            ),
            TaskProgress(
                id="q3_task_6",
                name="監控運維工作流 (8095)",
                description="AdminBoard運維管理系統",
                status=MilestoneStatus.NOT_STARTED,
                progress=0.0,
                estimated_hours=80,
                actual_hours=0,
                start_date=None,
                end_date=None,
                assignee="ops_team",
                dependencies=["q3_task_5"],
                blockers=[]
            ),
            TaskProgress(
                id="q3_task_7",
                name="全平台一鍵部署系統",
                description="Windows/Mac/Linux/Community/Web/VSCode跨平台部署",
                status=MilestoneStatus.NOT_STARTED,
                progress=0.0,
                estimated_hours=240,
                actual_hours=0,
                start_date=None,
                end_date=None,
                assignee="platform_team",
                dependencies=["q3_task_5"],
                blockers=[]
            )
        ]
        
        q3_milestone = MilestoneProgress(
            milestone_id="milestone_4_8_0",
            name="企業自動化平台",
            version="4.6.0",
            quarter="Q3 2025",
            status=MilestoneStatus.IN_PROGRESS,
            overall_progress=5.0,
            tasks=q3_tasks,
            start_date=datetime(2025, 7, 1),
            target_date=datetime(2025, 9, 30),
            completion_date=None,
            risk_level=RiskLevel.MEDIUM,
            risk_factors=["複雜度高", "跨團隊協作", "技術棧多樣"],
            blockers=[],
            last_updated=now
        )
        
        return [q3_milestone]
    
    async def analyze_progress(self, milestones: List[MilestoneProgress]) -> Dict[str, Any]:
        """分析進度並生成報告"""
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'milestones_summary': {},
            'risk_assessment': {},
            'recommendations': [],
            'github_activity': {},
            'alerts': []
        }
        
        # 分析每個里程碑
        total_progress = 0
        high_risk_count = 0
        delayed_count = 0
        
        for milestone in milestones:
            milestone_analysis = self._analyze_milestone(milestone)
            analysis['milestones_summary'][milestone.milestone_id] = milestone_analysis
            
            total_progress += milestone.overall_progress
            
            if milestone.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                high_risk_count += 1
            
            if milestone.status == MilestoneStatus.DELAYED:
                delayed_count += 1
        
        # 總體狀態評估
        avg_progress = total_progress / len(milestones) if milestones else 0
        
        if high_risk_count > 0 or delayed_count > 0:
            analysis['overall_status'] = 'at_risk'
        elif avg_progress < 30:
            analysis['overall_status'] = 'behind_schedule'
        
        # GitHub活動分析
        if self.github_integration:
            try:
                week_ago = datetime.now() - timedelta(days=7)
                analysis['github_activity'] = await self.github_integration.get_commit_activity(week_ago)
            except Exception as e:
                self.logger.warning(f"GitHub活動分析失敗: {e}")
        
        # 風險評估
        analysis['risk_assessment'] = self._assess_risks(milestones)
        
        # 生成建議
        analysis['recommendations'] = self._generate_recommendations(milestones, analysis)
        
        return analysis
    
    def _analyze_milestone(self, milestone: MilestoneProgress) -> Dict[str, Any]:
        """分析單個里程碑"""
        days_remaining = (milestone.target_date - datetime.now()).days
        
        completed_tasks = sum(1 for task in milestone.tasks if task.status == MilestoneStatus.COMPLETED)
        in_progress_tasks = sum(1 for task in milestone.tasks if task.status == MilestoneStatus.IN_PROGRESS)
        blocked_tasks = sum(1 for task in milestone.tasks if task.blockers)
        
        return {
            'name': milestone.name,
            'version': milestone.version,
            'status': milestone.status.value,
            'progress': milestone.overall_progress,
            'days_remaining': days_remaining,
            'risk_level': milestone.risk_level.value,
            'tasks_summary': {
                'total': len(milestone.tasks),
                'completed': completed_tasks,
                'in_progress': in_progress_tasks,
                'blocked': blocked_tasks
            },
            'estimated_completion': self._estimate_completion_date(milestone),
            'velocity': self._calculate_velocity(milestone)
        }
    
    def _estimate_completion_date(self, milestone: MilestoneProgress) -> str:
        """估算完成日期"""
        if milestone.overall_progress == 0:
            return "無法估算"
        
        days_elapsed = (datetime.now() - milestone.start_date).days
        if days_elapsed <= 0:
            return "無法估算"
        
        velocity = milestone.overall_progress / days_elapsed  # 每日進度百分比
        if velocity <= 0:
            return "進度停滯"
        
        remaining_progress = 100 - milestone.overall_progress
        estimated_days = remaining_progress / velocity
        estimated_date = datetime.now() + timedelta(days=estimated_days)
        
        return estimated_date.strftime('%Y-%m-%d')
    
    def _calculate_velocity(self, milestone: MilestoneProgress) -> float:
        """計算開發速度"""
        days_elapsed = (datetime.now() - milestone.start_date).days
        if days_elapsed <= 0:
            return 0.0
        
        return milestone.overall_progress / days_elapsed
    
    def _assess_risks(self, milestones: List[MilestoneProgress]) -> Dict[str, Any]:
        """評估風險"""
        risks = {
            'high_risk_milestones': [],
            'common_blockers': {},
            'resource_conflicts': [],
            'timeline_risks': []
        }
        
        for milestone in milestones:
            if milestone.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                risks['high_risk_milestones'].append({
                    'id': milestone.milestone_id,
                    'name': milestone.name,
                    'risk_level': milestone.risk_level.value,
                    'factors': milestone.risk_factors
                })
            
            # 統計常見阻礙
            for blocker in milestone.blockers:
                if blocker not in risks['common_blockers']:
                    risks['common_blockers'][blocker] = 0
                risks['common_blockers'][blocker] += 1
            
            # 檢查時間線風險
            days_remaining = (milestone.target_date - datetime.now()).days
            if days_remaining < 30 and milestone.overall_progress < 70:
                risks['timeline_risks'].append({
                    'milestone': milestone.name,
                    'days_remaining': days_remaining,
                    'progress': milestone.overall_progress
                })
        
        return risks
    
    def _generate_recommendations(self, milestones: List[MilestoneProgress], analysis: Dict[str, Any]) -> List[str]:
        """生成改進建議"""
        recommendations = []
        
        # 基於風險評估的建議
        if analysis['risk_assessment']['high_risk_milestones']:
            recommendations.append("立即關注高風險里程碑，制定風險緩解計劃")
        
        if analysis['risk_assessment']['timeline_risks']:
            recommendations.append("調整資源分配，加快關鍵里程碑進度")
        
        # 基於GitHub活動的建議
        github_activity = analysis.get('github_activity', {})
        if github_activity.get('total_commits', 0) < 10:
            recommendations.append("過去一週代碼提交較少，建議增加開發活動")
        
        # 基於進度的建議
        avg_progress = sum(m.overall_progress for m in milestones) / len(milestones) if milestones else 0
        if avg_progress < 25:
            recommendations.append("整體進度偏慢，建議重新評估時間線和資源配置")
        
        return recommendations
    
    async def generate_report(self, analysis: Dict[str, Any]) -> str:
        """生成進度報告"""
        report_lines = [
            "# PowerAutomation 里程碑進度報告",
            f"**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 📊 總體狀態",
            f"**狀態**: {analysis['overall_status']}",
            "",
            "## 🎯 里程碑進度",
            ""
        ]
        
        for milestone_id, milestone_data in analysis['milestones_summary'].items():
            report_lines.extend([
                f"### {milestone_data['name']} ({milestone_data['version']})",
                f"- **進度**: {milestone_data['progress']:.1f}%",
                f"- **狀態**: {milestone_data['status']}",
                f"- **風險等級**: {milestone_data['risk_level']}",
                f"- **剩余天數**: {milestone_data['days_remaining']}天",
                f"- **任務狀態**: {milestone_data['tasks_summary']['completed']}/{milestone_data['tasks_summary']['total']} 已完成",
                f"- **預計完成**: {milestone_data['estimated_completion']}",
                ""
            ])
        
        # GitHub活動
        if analysis.get('github_activity'):
            github = analysis['github_activity']
            report_lines.extend([
                "## 📈 開發活動 (過去7天)",
                f"- **提交數量**: {github.get('total_commits', 0)}",
                f"- **參與人員**: {len(github.get('contributors', []))}",
                f"- **文件變更**: {github.get('files_changed', 0)}",
                f"- **代碼行數**: +{github.get('lines_added', 0)} -{github.get('lines_deleted', 0)}",
                ""
            ])
        
        # 風險評估
        risks = analysis['risk_assessment']
        if risks['high_risk_milestones'] or risks['timeline_risks']:
            report_lines.extend([
                "## ⚠️ 風險預警",
                ""
            ])
            
            for risk_milestone in risks['high_risk_milestones']:
                report_lines.append(f"- **{risk_milestone['name']}**: {risk_milestone['risk_level']} 風險")
            
            for timeline_risk in risks['timeline_risks']:
                report_lines.append(f"- **{timeline_risk['milestone']}**: 僅剩 {timeline_risk['days_remaining']} 天，進度 {timeline_risk['progress']:.1f}%")
            
            report_lines.append("")
        
        # 建議
        if analysis['recommendations']:
            report_lines.extend([
                "## 💡 改進建議",
                ""
            ])
            for i, rec in enumerate(analysis['recommendations'], 1):
                report_lines.append(f"{i}. {rec}")
            report_lines.append("")
        
        return "\n".join(report_lines)
    
    async def send_notifications(self, analysis: Dict[str, Any], report: str):
        """發送通知"""
        # Slack通知
        slack_webhook = self.config.get('notifications', {}).get('slack_webhook')
        if slack_webhook and analysis['overall_status'] != 'healthy':
            await self._send_slack_notification(slack_webhook, analysis, report)
        
        # 郵件通知 (TODO: 實現郵件發送)
        email_recipients = self.config.get('notifications', {}).get('email_recipients', [])
        if email_recipients:
            self.logger.info(f"郵件通知功能待實現，收件人: {email_recipients}")
    
    async def _send_slack_notification(self, webhook_url: str, analysis: Dict[str, Any], report: str):
        """發送Slack通知"""
        try:
            payload = {
                "text": f"PowerAutomation 里程碑狀態: {analysis['overall_status']}",
                "attachments": [
                    {
                        "color": "warning" if analysis['overall_status'] == 'at_risk' else "good",
                        "fields": [
                            {
                                "title": "里程碑數量",
                                "value": str(len(analysis['milestones_summary'])),
                                "short": True
                            },
                            {
                                "title": "建議數量", 
                                "value": str(len(analysis['recommendations'])),
                                "short": True
                            }
                        ],
                        "text": "詳細報告請查看監控日誌"
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        self.logger.info("Slack通知發送成功")
                    else:
                        self.logger.error(f"Slack通知發送失敗: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"發送Slack通知時出錯: {e}")
    
    async def update_milestone_progress(self, milestone_id: str, task_id: str, new_progress: float):
        """更新任務進度"""
        milestones = self.load_milestones_data()
        
        for milestone in milestones:
            if milestone.milestone_id == milestone_id:
                for task in milestone.tasks:
                    if task.id == task_id:
                        task.progress = new_progress
                        task.actual_hours += 1  # 示例：增加工時記錄
                        
                        # 更新任務狀態
                        if new_progress >= 100:
                            task.status = MilestoneStatus.COMPLETED
                            task.end_date = datetime.now()
                        elif new_progress > 0:
                            task.status = MilestoneStatus.IN_PROGRESS
                            if not task.start_date:
                                task.start_date = datetime.now()
                
                # 重新計算里程碑整體進度
                total_progress = sum(task.progress for task in milestone.tasks)
                milestone.overall_progress = total_progress / len(milestone.tasks) if milestone.tasks else 0
                
                # 更新里程碑狀態
                if milestone.overall_progress >= 100:
                    milestone.status = MilestoneStatus.COMPLETED
                    milestone.completion_date = datetime.now()
                elif milestone.overall_progress > 0:
                    milestone.status = MilestoneStatus.IN_PROGRESS
                
                milestone.last_updated = datetime.now()
                break
        
        self.save_milestones_data(milestones)
        self.logger.info(f"更新任務 {task_id} 進度至 {new_progress}%")
    
    async def run_monitoring_cycle(self):
        """運行監控循環"""
        self.logger.info("開始里程碑進度監控循環")
        
        while True:
            try:
                # 加載最新數據
                milestones = self.load_milestones_data()
                
                # 分析進度
                analysis = await self.analyze_progress(milestones)
                
                # 生成報告
                report = await self.generate_report(analysis)
                
                # 保存報告
                report_dir = Path('reports')
                report_dir.mkdir(exist_ok=True)
                
                report_file = report_dir / f"milestone_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(report)
                
                self.logger.info(f"進度報告已生成: {report_file}")
                
                # 發送通知
                if analysis['overall_status'] != 'healthy':
                    await self.send_notifications(analysis, report)
                
                # 等待下次檢查
                check_interval = self.config['monitoring']['check_interval_hours'] * 3600
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"監控循環出錯: {e}")
                await asyncio.sleep(300)  # 5分鐘後重試


async def main():
    """主函數"""
    monitor = MilestoneProgressMonitor()
    
    # 示例：更新任務進度
    await monitor.update_milestone_progress("milestone_4_8_0", "q3_task_1", 35.0)
    
    # 運行監控
    await monitor.run_monitoring_cycle()


if __name__ == "__main__":
    asyncio.run(main())