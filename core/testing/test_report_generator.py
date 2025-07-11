#!/usr/bin/env python3
"""
PowerAutomation Test Report Generator
測試報告生成器

功能：
- 生成詳細的測試執行報告
- 創建可視化測試儀表板
- 生成測試覆蓋率分析
- 提供測試趨勢分析
- 支持多種報告格式輸出

Author: PowerAutomation Team
Version: 1.0.0
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import base64
import io

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from jinja2 import Template, Environment, FileSystemLoader
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo


class TestReportGenerator:
    """測試報告生成器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = self._setup_logging()
        self.output_dir = Path(self.config.get('output_dir', 'reports'))
        self.output_dir.mkdir(exist_ok=True)
        
        # 設置中文字體支持
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 設置樣式
        sns.set_style("whitegrid")
        plt.style.use('seaborn-v0_8')
    
    def _setup_logging(self) -> logging.Logger:
        """設置日志系統"""
        logger = logging.getLogger('test_report_generator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def generate_comprehensive_report(self, test_results: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> str:
        """生成綜合測試報告"""
        self.logger.info("開始生成綜合測試報告")
        
        # 分析測試結果
        analysis = self._analyze_test_results(test_results)
        
        # 生成可視化圖表
        charts = self._generate_charts(analysis)
        
        # 創建HTML報告
        html_report = self._create_html_report(analysis, charts, metadata)
        
        # 保存報告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.output_dir / f'comprehensive_report_{timestamp}.html'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        # 生成PDF版本
        pdf_path = self._generate_pdf_report(html_report, timestamp)
        
        # 生成JSON數據
        json_path = self._save_json_data(analysis, timestamp)
        
        self.logger.info(f"綜合報告已生成: {report_path}")
        
        return str(report_path)
    
    def _analyze_test_results(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析測試結果"""
        analysis = {
            'summary': {
                'total_suites': len(test_results),
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'skipped_tests': 0,
                'error_tests': 0,
                'success_rate': 0.0,
                'total_duration': 0.0,
                'average_duration': 0.0
            },
            'suite_details': [],
            'test_case_details': [],
            'failure_analysis': {
                'common_failures': {},
                'failure_patterns': [],
                'error_categories': {}
            },
            'performance_metrics': {
                'fastest_tests': [],
                'slowest_tests': [],
                'duration_distribution': [],
                'performance_trends': []
            },
            'coverage_analysis': {
                'feature_coverage': {},
                'test_type_distribution': {},
                'environment_coverage': {}
            },
            'quality_metrics': {
                'flaky_tests': [],
                'reliability_score': 0.0,
                'maintainability_score': 0.0
            }
        }
        
        all_test_cases = []
        total_duration = 0.0
        
        # 處理每個測試套件
        for suite_result in test_results:
            suite_analysis = self._analyze_suite(suite_result)
            analysis['suite_details'].append(suite_analysis)
            
            # 累計統計
            analysis['summary']['total_tests'] += suite_analysis['total_tests']
            analysis['summary']['passed_tests'] += suite_analysis['passed_tests']
            analysis['summary']['failed_tests'] += suite_analysis['failed_tests']
            analysis['summary']['skipped_tests'] += suite_analysis['skipped_tests']
            analysis['summary']['error_tests'] += suite_analysis['error_tests']
            
            total_duration += suite_analysis['duration']
            
            # 收集所有測試用例
            if 'test_cases' in suite_result:
                all_test_cases.extend(suite_result['test_cases'])
        
        # 計算總體指標
        analysis['summary']['total_duration'] = total_duration
        if analysis['summary']['total_tests'] > 0:
            analysis['summary']['success_rate'] = (
                analysis['summary']['passed_tests'] / analysis['summary']['total_tests'] * 100
            )
            analysis['summary']['average_duration'] = (
                total_duration / analysis['summary']['total_tests']
            )
        
        # 分析測試用例
        analysis['test_case_details'] = self._analyze_test_cases(all_test_cases)
        
        # 失敗分析
        analysis['failure_analysis'] = self._analyze_failures(all_test_cases)
        
        # 性能分析
        analysis['performance_metrics'] = self._analyze_performance(all_test_cases)
        
        # 覆蓋率分析
        analysis['coverage_analysis'] = self._analyze_coverage(all_test_cases)
        
        return analysis
    
    def _analyze_suite(self, suite_result: Dict[str, Any]) -> Dict[str, Any]:
        """分析單個測試套件"""
        start_time = None
        end_time = None
        
        if suite_result.get('start_time'):
            start_time = datetime.fromisoformat(suite_result['start_time'])
        if suite_result.get('end_time'):
            end_time = datetime.fromisoformat(suite_result['end_time'])
        
        duration = 0.0
        if start_time and end_time:
            duration = (end_time - start_time).total_seconds()
        
        return {
            'id': suite_result.get('id', 'unknown'),
            'name': suite_result.get('name', 'Unknown Suite'),
            'status': suite_result.get('status', 'unknown'),
            'environment': suite_result.get('environment', 'unknown'),
            'total_tests': len(suite_result.get('test_cases', [])),
            'passed_tests': suite_result.get('passed_count', 0),
            'failed_tests': suite_result.get('failed_count', 0),
            'skipped_tests': suite_result.get('skipped_count', 0),
            'error_tests': 0,  # 可以從測試用例中計算
            'duration': duration,
            'start_time': start_time,
            'end_time': end_time
        }
    
    def _analyze_test_cases(self, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析測試用例"""
        analyzed_cases = []
        
        for test_case in test_cases:
            start_time = None
            end_time = None
            duration = 0.0
            
            if test_case.get('start_time'):
                start_time = datetime.fromisoformat(test_case['start_time'])
            if test_case.get('end_time'):
                end_time = datetime.fromisoformat(test_case['end_time'])
            
            if start_time and end_time:
                duration = (end_time - start_time).total_seconds()
            
            analyzed_case = {
                'id': test_case.get('id', 'unknown'),
                'name': test_case.get('name', 'Unknown Test'),
                'description': test_case.get('description', ''),
                'status': test_case.get('status', 'unknown'),
                'test_type': test_case.get('test_type', 'unknown'),
                'environment': test_case.get('environment', 'unknown'),
                'tags': test_case.get('tags', []),
                'priority': test_case.get('priority', 0),
                'duration': duration,
                'error_message': test_case.get('error_message'),
                'screenshots': test_case.get('screenshots', []),
                'dependencies': test_case.get('dependencies', [])
            }
            
            analyzed_cases.append(analyzed_case)
        
        return analyzed_cases
    
    def _analyze_failures(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析失敗模式"""
        failure_analysis = {
            'common_failures': {},
            'failure_patterns': [],
            'error_categories': {}
        }
        
        failed_cases = [tc for tc in test_cases if tc.get('status') == 'failed']
        
        # 統計常見失敗原因
        for test_case in failed_cases:
            error_msg = test_case.get('error_message', 'Unknown error')
            
            # 簡化錯誤信息以便分類
            simplified_error = self._simplify_error_message(error_msg)
            
            if simplified_error not in failure_analysis['common_failures']:
                failure_analysis['common_failures'][simplified_error] = 0
            failure_analysis['common_failures'][simplified_error] += 1
        
        # 識別失敗模式
        failure_patterns = []
        if len(failed_cases) > 1:
            # 分析失敗的測試是否有共同特徵
            common_tags = self._find_common_tags(failed_cases)
            if common_tags:
                failure_patterns.append({
                    'type': 'common_tags',
                    'pattern': f"帶有標籤 {', '.join(common_tags)} 的測試更容易失敗",
                    'affected_tests': len([tc for tc in failed_cases if any(tag in tc.get('tags', []) for tag in common_tags)])
                })
        
        failure_analysis['failure_patterns'] = failure_patterns
        
        return failure_analysis
    
    def _simplify_error_message(self, error_msg: str) -> str:
        """簡化錯誤信息以便分類"""
        if not error_msg:
            return "Unknown error"
        
        # 常見錯誤模式
        patterns = {
            'timeout': ['timeout', 'timed out', 'time out'],
            'element_not_found': ['element not found', 'no such element', 'unable to locate'],
            'network_error': ['network', 'connection', 'http', 'api'],
            'assertion_error': ['assertion', 'assert', 'expected', 'actual'],
            'permission_error': ['permission', 'access denied', 'forbidden'],
            'server_error': ['server error', '500', 'internal server error']
        }
        
        error_lower = error_msg.lower()
        
        for category, keywords in patterns.items():
            if any(keyword in error_lower for keyword in keywords):
                return category.replace('_', ' ').title()
        
        return "Other error"
    
    def _find_common_tags(self, test_cases: List[Dict[str, Any]]) -> List[str]:
        """找出失敗測試的共同標籤"""
        if not test_cases:
            return []
        
        # 統計所有標籤出現頻率
        tag_counts = {}
        total_cases = len(test_cases)
        
        for test_case in test_cases:
            for tag in test_case.get('tags', []):
                if tag not in tag_counts:
                    tag_counts[tag] = 0
                tag_counts[tag] += 1
        
        # 返回出現頻率超過50%的標籤
        common_tags = [tag for tag, count in tag_counts.items() if count / total_cases > 0.5]
        
        return common_tags
    
    def _analyze_performance(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析性能指標"""
        # 計算每個測試用例的執行時間
        durations = []
        for test_case in test_cases:
            start_time = test_case.get('start_time')
            end_time = test_case.get('end_time')
            
            if start_time and end_time:
                start_dt = datetime.fromisoformat(start_time)
                end_dt = datetime.fromisoformat(end_time)
                duration = (end_dt - start_dt).total_seconds()
                
                durations.append({
                    'test_id': test_case.get('id', 'unknown'),
                    'test_name': test_case.get('name', 'Unknown'),
                    'duration': duration,
                    'test_type': test_case.get('test_type', 'unknown')
                })
        
        # 排序找出最快和最慢的測試
        durations_sorted = sorted(durations, key=lambda x: x['duration'])
        
        return {
            'fastest_tests': durations_sorted[:5],
            'slowest_tests': durations_sorted[-5:],
            'duration_distribution': durations,
            'average_duration': sum(d['duration'] for d in durations) / len(durations) if durations else 0,
            'total_execution_time': sum(d['duration'] for d in durations)
        }
    
    def _analyze_coverage(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析測試覆蓋率"""
        # 按功能分類統計
        feature_coverage = {}
        test_type_distribution = {}
        environment_coverage = {}
        
        for test_case in test_cases:
            # 測試類型分布
            test_type = test_case.get('test_type', 'unknown')
            if test_type not in test_type_distribution:
                test_type_distribution[test_type] = 0
            test_type_distribution[test_type] += 1
            
            # 環境覆蓋
            environment = test_case.get('environment', 'unknown')
            if environment not in environment_coverage:
                environment_coverage[environment] = 0
            environment_coverage[environment] += 1
            
            # 功能覆蓋（基於標籤）
            for tag in test_case.get('tags', []):
                if tag not in feature_coverage:
                    feature_coverage[tag] = {'total': 0, 'passed': 0}
                feature_coverage[tag]['total'] += 1
                if test_case.get('status') == 'passed':
                    feature_coverage[tag]['passed'] += 1
        
        return {
            'feature_coverage': feature_coverage,
            'test_type_distribution': test_type_distribution,
            'environment_coverage': environment_coverage
        }
    
    def _generate_charts(self, analysis: Dict[str, Any]) -> Dict[str, str]:
        """生成可視化圖表"""
        charts = {}
        
        # 1. 測試結果總覽餅圖
        charts['test_overview'] = self._create_test_overview_chart(analysis['summary'])
        
        # 2. 測試套件性能對比
        charts['suite_performance'] = self._create_suite_performance_chart(analysis['suite_details'])
        
        # 3. 失敗原因分析
        charts['failure_analysis'] = self._create_failure_analysis_chart(analysis['failure_analysis'])
        
        # 4. 測試執行時間分布
        charts['duration_distribution'] = self._create_duration_distribution_chart(analysis['performance_metrics'])
        
        # 5. 測試覆蓋率分析
        charts['coverage_analysis'] = self._create_coverage_chart(analysis['coverage_analysis'])
        
        # 6. 測試趨勢圖（如果有歷史數據）
        charts['trend_analysis'] = self._create_trend_chart()
        
        return charts
    
    def _create_test_overview_chart(self, summary: Dict[str, Any]) -> str:
        """創建測試結果總覽圖"""
        fig = go.Figure(data=[go.Pie(
            labels=['通過', '失敗', '跳過', '錯誤'],
            values=[
                summary['passed_tests'],
                summary['failed_tests'],
                summary['skipped_tests'],
                summary['error_tests']
            ],
            hole=0.3,
            marker_colors=['#2ecc71', '#e74c3c', '#f39c12', '#9b59b6']
        )])
        
        fig.update_layout(
            title="測試結果總覽",
            font=dict(family="SimHei, sans-serif", size=14),
            showlegend=True
        )
        
        return pyo.plot(fig, output_type='div', include_plotlyjs=False)
    
    def _create_suite_performance_chart(self, suite_details: List[Dict[str, Any]]) -> str:
        """創建測試套件性能對比圖"""
        suite_names = [suite['name'] for suite in suite_details]
        durations = [suite['duration'] for suite in suite_details]
        success_rates = [
            (suite['passed_tests'] / suite['total_tests'] * 100) if suite['total_tests'] > 0 else 0
            for suite in suite_details
        ]
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('執行時間', '成功率'),
            specs=[[{"secondary_y": False}],
                   [{"secondary_y": False}]]
        )
        
        # 執行時間條形圖
        fig.add_trace(
            go.Bar(name='執行時間(秒)', x=suite_names, y=durations, marker_color='#3498db'),
            row=1, col=1
        )
        
        # 成功率條形圖
        fig.add_trace(
            go.Bar(name='成功率(%)', x=suite_names, y=success_rates, marker_color='#2ecc71'),
            row=2, col=1
        )
        
        fig.update_layout(
            title="測試套件性能對比",
            font=dict(family="SimHei, sans-serif", size=14),
            showlegend=False
        )
        
        return pyo.plot(fig, output_type='div', include_plotlyjs=False)
    
    def _create_failure_analysis_chart(self, failure_analysis: Dict[str, Any]) -> str:
        """創建失敗原因分析圖"""
        common_failures = failure_analysis['common_failures']
        
        if not common_failures:
            return "<div>暫無失敗數據</div>"
        
        categories = list(common_failures.keys())
        counts = list(common_failures.values())
        
        fig = go.Figure(data=[
            go.Bar(
                x=counts,
                y=categories,
                orientation='h',
                marker_color='#e74c3c'
            )
        ])
        
        fig.update_layout(
            title="失敗原因分析",
            xaxis_title="失敗次數",
            yaxis_title="失敗類型",
            font=dict(family="SimHei, sans-serif", size=14)
        )
        
        return pyo.plot(fig, output_type='div', include_plotlyjs=False)
    
    def _create_duration_distribution_chart(self, performance_metrics: Dict[str, Any]) -> str:
        """創建測試執行時間分布圖"""
        durations = [item['duration'] for item in performance_metrics['duration_distribution']]
        
        if not durations:
            return "<div>暫無性能數據</div>"
        
        fig = go.Figure(data=[go.Histogram(
            x=durations,
            nbinsx=20,
            marker_color='#3498db',
            opacity=0.7
        )])
        
        fig.update_layout(
            title="測試執行時間分布",
            xaxis_title="執行時間 (秒)",
            yaxis_title="測試數量",
            font=dict(family="SimHei, sans-serif", size=14)
        )
        
        return pyo.plot(fig, output_type='div', include_plotlyjs=False)
    
    def _create_coverage_chart(self, coverage_analysis: Dict[str, Any]) -> str:
        """創建測試覆蓋率圖"""
        test_type_dist = coverage_analysis['test_type_distribution']
        
        if not test_type_dist:
            return "<div>暫無覆蓋率數據</div>"
        
        fig = go.Figure(data=[go.Pie(
            labels=list(test_type_dist.keys()),
            values=list(test_type_dist.values()),
            hole=0.3
        )])
        
        fig.update_layout(
            title="測試類型分布",
            font=dict(family="SimHei, sans-serif", size=14)
        )
        
        return pyo.plot(fig, output_type='div', include_plotlyjs=False)
    
    def _create_trend_chart(self) -> str:
        """創建測試趨勢圖"""
        # 示例趨勢數據（實際應用中應從歷史數據中讀取）
        dates = [datetime.now() - timedelta(days=i) for i in range(7, 0, -1)]
        success_rates = [95, 92, 96, 98, 94, 97, 95]
        
        fig = go.Figure(data=[
            go.Scatter(
                x=dates,
                y=success_rates,
                mode='lines+markers',
                name='成功率',
                line=dict(color='#2ecc71', width=3),
                marker=dict(size=8)
            )
        ])
        
        fig.update_layout(
            title="測試成功率趨勢 (最近7天)",
            xaxis_title="日期",
            yaxis_title="成功率 (%)",
            font=dict(family="SimHei, sans-serif", size=14),
            yaxis=dict(range=[80, 100])
        )
        
        return pyo.plot(fig, output_type='div', include_plotlyjs=False)
    
    def _create_html_report(self, analysis: Dict[str, Any], charts: Dict[str, str], metadata: Dict[str, Any] = None) -> str:
        """創建HTML報告"""
        metadata = metadata or {}
        
        template_str = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PowerAutomation 測試報告</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        
        .header .subtitle {
            margin-top: 10px;
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .content {
            padding: 30px;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .summary-card {
            background: #f8f9fa;
            border-left: 4px solid;
            padding: 20px;
            border-radius: 4px;
        }
        
        .summary-card.success { border-left-color: #28a745; }
        .summary-card.danger { border-left-color: #dc3545; }
        .summary-card.warning { border-left-color: #ffc107; }
        .summary-card.info { border-left-color: #17a2b8; }
        
        .summary-card h3 {
            margin: 0 0 10px 0;
            font-size: 2em;
            font-weight: bold;
        }
        
        .summary-card p {
            margin: 0;
            color: #666;
        }
        
        .section {
            margin-bottom: 40px;
        }
        
        .section h2 {
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
            margin-bottom: 20px;
            color: #495057;
        }
        
        .chart-container {
            margin: 20px 0;
            background: white;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .test-list {
            border: 1px solid #e9ecef;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .test-item {
            padding: 15px;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .test-item:last-child {
            border-bottom: none;
        }
        
        .test-item.passed { background-color: #d4edda; }
        .test-item.failed { background-color: #f8d7da; }
        .test-item.skipped { background-color: #fff3cd; }
        
        .status-badge {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .status-badge.passed { background: #28a745; color: white; }
        .status-badge.failed { background: #dc3545; color: white; }
        .status-badge.skipped { background: #ffc107; color: black; }
        
        .metadata {
            background: #e9ecef;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        
        .metadata h3 {
            margin-top: 0;
        }
        
        .metadata-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }
        
        .footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e9ecef;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background-color: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
            transition: width 0.3s ease;
        }
        
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                border-radius: 0;
            }
            
            .content {
                padding: 20px;
            }
            
            .summary-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 PowerAutomation</h1>
            <div class="subtitle">測試執行報告</div>
            <div style="margin-top: 15px; font-size: 1em;">
                生成時間: {{ generation_time }}
            </div>
        </div>
        
        <div class="content">
            <!-- 執行元數據 -->
            {% if metadata %}
            <div class="metadata">
                <h3>📋 執行信息</h3>
                <div class="metadata-grid">
                    {% for key, value in metadata.items() %}
                    <div><strong>{{ key }}:</strong> {{ value }}</div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
            
            <!-- 總覽統計 -->
            <div class="section">
                <h2>📊 執行總覽</h2>
                <div class="summary-grid">
                    <div class="summary-card success">
                        <h3>{{ summary.passed_tests }}</h3>
                        <p>通過測試</p>
                    </div>
                    <div class="summary-card danger">
                        <h3>{{ summary.failed_tests }}</h3>
                        <p>失敗測試</p>
                    </div>
                    <div class="summary-card warning">
                        <h3>{{ summary.skipped_tests }}</h3>
                        <p>跳過測試</p>
                    </div>
                    <div class="summary-card info">
                        <h3>{{ "%.1f"|format(summary.success_rate) }}%</h3>
                        <p>成功率</p>
                    </div>
                </div>
                
                <div style="margin: 20px 0;">
                    <h4>整體成功率</h4>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {{ summary.success_rate }}%;"></div>
                    </div>
                    <small>{{ summary.passed_tests }}/{{ summary.total_tests }} 測試通過</small>
                </div>
            </div>
            
            <!-- 可視化圖表 -->
            <div class="section">
                <h2>📈 可視化分析</h2>
                
                <div class="chart-container">
                    {{ charts.test_overview | safe }}
                </div>
                
                <div class="chart-container">
                    {{ charts.suite_performance | safe }}
                </div>
                
                <div class="chart-container">
                    {{ charts.failure_analysis | safe }}
                </div>
                
                <div class="chart-container">
                    {{ charts.duration_distribution | safe }}
                </div>
                
                <div class="chart-container">
                    {{ charts.coverage_analysis | safe }}
                </div>
                
                <div class="chart-container">
                    {{ charts.trend_analysis | safe }}
                </div>
            </div>
            
            <!-- 測試套件詳情 -->
            <div class="section">
                <h2>📋 測試套件詳情</h2>
                {% for suite in suite_details %}
                <div style="margin-bottom: 30px; border: 1px solid #e9ecef; border-radius: 4px; overflow: hidden;">
                    <div style="background: #f8f9fa; padding: 15px; border-bottom: 1px solid #e9ecef;">
                        <h3 style="margin: 0;">{{ suite.name }}</h3>
                        <div style="margin-top: 5px; color: #666;">
                            環境: {{ suite.environment }} | 
                            執行時間: {{ "%.2f"|format(suite.duration) }}秒 |
                            成功率: {{ "%.1f"|format((suite.passed_tests / suite.total_tests * 100) if suite.total_tests > 0 else 0) }}%
                        </div>
                    </div>
                    <div style="padding: 15px;">
                        <div class="summary-grid">
                            <div><strong>總測試數:</strong> {{ suite.total_tests }}</div>
                            <div><strong>通過:</strong> <span style="color: #28a745;">{{ suite.passed_tests }}</span></div>
                            <div><strong>失敗:</strong> <span style="color: #dc3545;">{{ suite.failed_tests }}</span></div>
                            <div><strong>跳過:</strong> <span style="color: #ffc107;">{{ suite.skipped_tests }}</span></div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
            
            <!-- 失敗分析 -->
            {% if failure_analysis.common_failures %}
            <div class="section">
                <h2>🔍 失敗分析</h2>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 4px;">
                    <h4>常見失敗原因</h4>
                    {% for error_type, count in failure_analysis.common_failures.items() %}
                    <div style="margin: 10px 0; padding: 10px; background: white; border-radius: 4px; border-left: 3px solid #dc3545;">
                        <strong>{{ error_type }}</strong>: {{ count }} 次
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
            
            <!-- 性能分析 -->
            <div class="section">
                <h2>⚡ 性能分析</h2>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <h4>執行最快的測試</h4>
                        <div class="test-list">
                            {% for test in performance_metrics.fastest_tests %}
                            <div class="test-item">
                                <span>{{ test.test_name }}</span>
                                <span class="status-badge passed">{{ "%.2f"|format(test.duration) }}s</span>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    <div>
                        <h4>執行最慢的測試</h4>
                        <div class="test-list">
                            {% for test in performance_metrics.slowest_tests %}
                            <div class="test-item">
                                <span>{{ test.test_name }}</span>
                                <span class="status-badge warning">{{ "%.2f"|format(test.duration) }}s</span>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 測試覆蓋率 -->
            <div class="section">
                <h2>📊 測試覆蓋率</h2>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                    <div>
                        <h4>功能覆蓋率</h4>
                        {% for feature, data in coverage_analysis.feature_coverage.items() %}
                        <div style="margin: 10px 0;">
                            <div style="display: flex; justify-content: space-between;">
                                <span>{{ feature }}</span>
                                <span>{{ data.passed }}/{{ data.total }}</span>
                            </div>
                            <div class="progress-bar" style="height: 8px;">
                                <div class="progress-fill" style="width: {{ (data.passed / data.total * 100) if data.total > 0 else 0 }}%;"></div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    <div>
                        <h4>環境覆蓋</h4>
                        {% for env, count in coverage_analysis.environment_coverage.items() %}
                        <div style="margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                            <strong>{{ env }}</strong>: {{ count }} 個測試
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>🤖 PowerAutomation 測試報告系統 - 自動生成於 {{ generation_time }}</p>
            <p>報告版本: v1.0.0 | 系統: PowerAutomation v4.6.0</p>
            <p>測試技術: Test MCP + Stagewise MCP + AG-UI MCP + Selenium + pytest</p>
        </div>
    </div>
</body>
</html>
        """
        
        template = Template(template_str)
        
        return template.render(
            generation_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            summary=analysis['summary'],
            suite_details=analysis['suite_details'],
            failure_analysis=analysis['failure_analysis'],
            performance_metrics=analysis['performance_metrics'],
            coverage_analysis=analysis['coverage_analysis'],
            charts=charts,
            metadata=metadata
        )
    
    def _generate_pdf_report(self, html_content: str, timestamp: str) -> str:
        """生成PDF報告"""
        try:
            import pdfkit
            
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None
            }
            
            pdf_path = self.output_dir / f'test_report_{timestamp}.pdf'
            pdfkit.from_string(html_content, str(pdf_path), options=options)
            
            self.logger.info(f"PDF報告已生成: {pdf_path}")
            return str(pdf_path)
            
        except ImportError:
            self.logger.warning("pdfkit未安裝，跳過PDF報告生成")
            return ""
        except Exception as e:
            self.logger.error(f"PDF報告生成失敗: {e}")
            return ""
    
    def _save_json_data(self, analysis: Dict[str, Any], timestamp: str) -> str:
        """保存JSON數據"""
        json_path = self.output_dir / f'test_data_{timestamp}.json'
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2, default=str)
        
        self.logger.info(f"JSON數據已保存: {json_path}")
        return str(json_path)
    
    def generate_daily_summary(self, test_results: List[Dict[str, Any]]) -> str:
        """生成每日測試摘要"""
        analysis = self._analyze_test_results(test_results)
        
        summary_text = f"""
# PowerAutomation 每日測試摘要 - {datetime.now().strftime('%Y-%m-%d')}

## 📊 執行概況
- **總測試數**: {analysis['summary']['total_tests']}
- **通過率**: {analysis['summary']['success_rate']:.1f}%
- **執行時間**: {analysis['summary']['total_duration']:.1f}秒

## 🎯 關鍵指標
- ✅ **通過**: {analysis['summary']['passed_tests']}
- ❌ **失敗**: {analysis['summary']['failed_tests']}
- ⏭️ **跳過**: {analysis['summary']['skipped_tests']}

## 📈 性能表現
- **平均執行時間**: {analysis['summary']['average_duration']:.2f}秒
- **最快測試**: {analysis['performance_metrics']['fastest_tests'][0]['duration']:.2f}秒
- **最慢測試**: {analysis['performance_metrics']['slowest_tests'][-1]['duration']:.2f}秒

## 🔍 需要關注的問題
"""
        
        if analysis['failure_analysis']['common_failures']:
            summary_text += "\n### 常見失敗原因:\n"
            for error_type, count in analysis['failure_analysis']['common_failures'].items():
                summary_text += f"- {error_type}: {count} 次\n"
        else:
            summary_text += "\n✅ 無明顯失敗模式\n"
        
        # 保存摘要
        timestamp = datetime.now().strftime('%Y%m%d')
        summary_path = self.output_dir / f'daily_summary_{timestamp}.md'
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_text)
        
        return str(summary_path)


def main():
    """主函數示例"""
    # 示例測試結果數據
    sample_test_results = [
        {
            "id": "powerautomation_e2e_suite",
            "name": "PowerAutomation 端到端測試套件",
            "status": "passed",
            "environment": "docker",
            "start_time": "2025-07-11T10:00:00",
            "end_time": "2025-07-11T10:15:00",
            "passed_count": 8,
            "failed_count": 2,
            "skipped_count": 1,
            "test_cases": [
                {
                    "id": "pa_login_test",
                    "name": "用戶登錄測試",
                    "status": "passed",
                    "test_type": "e2e",
                    "environment": "docker",
                    "tags": ["auth", "critical"],
                    "start_time": "2025-07-11T10:00:00",
                    "end_time": "2025-07-11T10:01:30",
                },
                {
                    "id": "pa_project_creation_test",
                    "name": "項目創建測試",
                    "status": "failed",
                    "test_type": "e2e",
                    "environment": "docker",
                    "tags": ["project", "core"],
                    "start_time": "2025-07-11T10:02:00",
                    "end_time": "2025-07-11T10:04:00",
                    "error_message": "Element not found: id=create-project-btn"
                }
            ]
        }
    ]
    
    # 創建報告生成器
    generator = TestReportGenerator()
    
    # 生成綜合報告
    report_path = generator.generate_comprehensive_report(
        sample_test_results,
        metadata={
            "版本": "v4.6.0",
            "分支": "main",
            "提交": "abc123ef",
            "執行者": "GitHub Actions",
            "環境": "Docker"
        }
    )
    
    print(f"測試報告已生成: {report_path}")
    
    # 生成每日摘要
    summary_path = generator.generate_daily_summary(sample_test_results)
    print(f"每日摘要已生成: {summary_path}")


if __name__ == "__main__":
    main()