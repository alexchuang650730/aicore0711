"""
PowerAutomation v4.6.1 回歸測試套件
智能回歸測試管理系統

核心功能：
- 自動化回歸測試執行
- 版本間功能對比
- 智能測試用例選擇
- 回歸風險評估
- 測試影響分析
- 自動化測試維護
"""

import asyncio
import logging
import json
import git
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import ast
import difflib

logger = logging.getLogger(__name__)


class RegressionRisk(Enum):
    """回歸風險等級"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ChangeType(Enum):
    """變更類型"""
    FEATURE_ADD = "feature_add"
    FEATURE_MODIFY = "feature_modify"
    FEATURE_REMOVE = "feature_remove"
    BUG_FIX = "bug_fix"
    REFACTOR = "refactor"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DEPENDENCY = "dependency"


class TestSelectionStrategy(Enum):
    """測試選擇策略"""
    ALL_TESTS = "all_tests"
    IMPACT_BASED = "impact_based"
    RISK_BASED = "risk_based"
    CHANGE_BASED = "change_based"
    SMART_SELECTION = "smart_selection"


@dataclass
class CodeChange:
    """代碼變更"""
    file_path: str
    change_type: ChangeType
    lines_added: int
    lines_removed: int
    complexity_delta: int
    affected_functions: List[str]
    affected_classes: List[str]
    risk_level: RegressionRisk
    description: str


@dataclass
class TestImpactAnalysis:
    """測試影響分析"""
    test_case_id: str
    impact_score: float
    affected_by_changes: List[str]
    risk_assessment: RegressionRisk
    execution_priority: int
    reasons: List[str]


@dataclass
class RegressionTestSuite:
    """回歸測試套件"""
    id: str
    name: str
    base_version: str
    target_version: str
    changes: List[CodeChange]
    selected_tests: List[str]
    selection_strategy: TestSelectionStrategy
    impact_analysis: List[TestImpactAnalysis]
    created_at: str


class CodeAnalyzer:
    """代碼分析器"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.repo = git.Repo(repo_path)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def analyze_changes_between_versions(self, base_version: str, target_version: str) -> List[CodeChange]:
        """分析版本間的代碼變更"""
        try:
            # 獲取兩個版本間的差異
            base_commit = self.repo.commit(base_version)
            target_commit = self.repo.commit(target_version)
            
            changes = []
            
            # 遍歷所有變更的文件
            for item in target_commit.diff(base_commit):
                if item.a_path and item.a_path.endswith('.py'):
                    change = self._analyze_file_change(item)
                    if change:
                        changes.append(change)
            
            return changes
            
        except Exception as e:
            self.logger.error(f"版本變更分析失敗: {e}")
            return []
    
    def _analyze_file_change(self, diff_item) -> Optional[CodeChange]:
        """分析單個文件的變更"""
        try:
            file_path = diff_item.a_path or diff_item.b_path
            
            # 計算變更行數
            lines_added = 0
            lines_removed = 0
            
            if diff_item.diff:
                diff_text = diff_item.diff.decode('utf-8')
                for line in diff_text.split('\n'):
                    if line.startswith('+') and not line.startswith('+++'):
                        lines_added += 1
                    elif line.startswith('-') and not line.startswith('---'):
                        lines_removed += 1
            
            # 分析變更類型
            change_type = self._determine_change_type(diff_item, file_path)
            
            # 分析受影響的函數和類
            affected_functions, affected_classes = self._analyze_affected_code_elements(diff_item)
            
            # 評估風險等級
            risk_level = self._assess_regression_risk(
                file_path, change_type, lines_added, lines_removed, 
                affected_functions, affected_classes
            )
            
            # 計算複雜度變化
            complexity_delta = self._calculate_complexity_delta(diff_item)
            
            return CodeChange(
                file_path=file_path,
                change_type=change_type,
                lines_added=lines_added,
                lines_removed=lines_removed,
                complexity_delta=complexity_delta,
                affected_functions=affected_functions,
                affected_classes=affected_classes,
                risk_level=risk_level,
                description=f"變更文件 {file_path}: +{lines_added}/-{lines_removed} 行"
            )
            
        except Exception as e:
            self.logger.error(f"文件變更分析失敗: {e}")
            return None
    
    def _determine_change_type(self, diff_item, file_path: str) -> ChangeType:
        """確定變更類型"""
        # 簡化的變更類型判斷邏輯
        if diff_item.new_file:
            return ChangeType.FEATURE_ADD
        elif diff_item.deleted_file:
            return ChangeType.FEATURE_REMOVE
        elif "test" in file_path.lower():
            return ChangeType.BUG_FIX
        elif "security" in file_path.lower():
            return ChangeType.SECURITY
        else:
            return ChangeType.FEATURE_MODIFY
    
    def _analyze_affected_code_elements(self, diff_item) -> Tuple[List[str], List[str]]:
        """分析受影響的代碼元素"""
        affected_functions = []
        affected_classes = []
        
        try:
            if diff_item.b_blob and diff_item.b_blob.data_stream:
                content = diff_item.b_blob.data_stream.read().decode('utf-8')
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        affected_functions.append(node.name)
                    elif isinstance(node, ast.ClassDef):
                        affected_classes.append(node.name)
                        
        except Exception as e:
            self.logger.warning(f"代碼元素分析失敗: {e}")
        
        return affected_functions, affected_classes
    
    def _assess_regression_risk(self, file_path: str, change_type: ChangeType, 
                              lines_added: int, lines_removed: int,
                              affected_functions: List[str], affected_classes: List[str]) -> RegressionRisk:
        """評估回歸風險"""
        risk_score = 0
        
        # 基於變更類型的風險
        type_risk = {
            ChangeType.FEATURE_ADD: 2,
            ChangeType.FEATURE_MODIFY: 3,
            ChangeType.FEATURE_REMOVE: 4,
            ChangeType.BUG_FIX: 1,
            ChangeType.REFACTOR: 3,
            ChangeType.PERFORMANCE: 2,
            ChangeType.SECURITY: 4,
            ChangeType.DEPENDENCY: 3
        }
        risk_score += type_risk.get(change_type, 2)
        
        # 基於變更規模的風險
        change_scale = lines_added + lines_removed
        if change_scale > 100:
            risk_score += 3
        elif change_scale > 50:
            risk_score += 2
        elif change_scale > 10:
            risk_score += 1
        
        # 基於核心文件的風險
        if any(keyword in file_path.lower() for keyword in ['core', 'main', 'manager', 'engine']):
            risk_score += 2
        
        # 基於受影響代碼元素的風險
        if len(affected_functions) > 5 or len(affected_classes) > 3:
            risk_score += 2
        
        # 轉換為風險等級
        if risk_score >= 8:
            return RegressionRisk.CRITICAL
        elif risk_score >= 6:
            return RegressionRisk.HIGH
        elif risk_score >= 4:
            return RegressionRisk.MEDIUM
        else:
            return RegressionRisk.LOW
    
    def _calculate_complexity_delta(self, diff_item) -> int:
        """計算複雜度變化"""
        # 簡化的複雜度計算
        complexity_delta = 0
        
        try:
            if diff_item.diff:
                diff_text = diff_item.diff.decode('utf-8')
                
                # 計算增加的控制結構
                control_keywords = ['if', 'for', 'while', 'try', 'except', 'with']
                for line in diff_text.split('\n'):
                    if line.startswith('+'):
                        for keyword in control_keywords:
                            if keyword in line:
                                complexity_delta += 1
                    elif line.startswith('-'):
                        for keyword in control_keywords:
                            if keyword in line:
                                complexity_delta -= 1
                                
        except Exception as e:
            self.logger.warning(f"複雜度分析失敗: {e}")
        
        return complexity_delta


class TestImpactAnalyzer:
    """測試影響分析器"""
    
    def __init__(self, test_registry: Dict[str, Any]):
        self.test_registry = test_registry
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def analyze_test_impact(self, changes: List[CodeChange], 
                          available_tests: List[str]) -> List[TestImpactAnalysis]:
        """分析測試影響"""
        impact_analyses = []
        
        for test_id in available_tests:
            analysis = self._analyze_single_test_impact(test_id, changes)
            impact_analyses.append(analysis)
        
        # 按影響分數排序
        impact_analyses.sort(key=lambda x: x.impact_score, reverse=True)
        
        return impact_analyses
    
    def _analyze_single_test_impact(self, test_id: str, changes: List[CodeChange]) -> TestImpactAnalysis:
        """分析單個測試的影響"""
        test_info = self.test_registry.get(test_id, {})
        
        impact_score = 0.0
        affected_by_changes = []
        reasons = []
        
        # 分析測試與變更的關聯
        for change in changes:
            # 基於文件路徑的關聯
            if self._is_test_related_to_file(test_info, change.file_path):
                impact_score += self._calculate_file_impact_score(change)
                affected_by_changes.append(change.file_path)
                reasons.append(f"測試覆蓋變更文件: {change.file_path}")
            
            # 基於功能關聯
            if self._is_test_related_to_functions(test_info, change.affected_functions):
                impact_score += self._calculate_function_impact_score(change)
                affected_by_changes.extend(change.affected_functions)
                reasons.append(f"測試覆蓋變更函數: {', '.join(change.affected_functions)}")
            
            # 基於類關聯
            if self._is_test_related_to_classes(test_info, change.affected_classes):
                impact_score += self._calculate_class_impact_score(change)
                affected_by_changes.extend(change.affected_classes)
                reasons.append(f"測試覆蓋變更類: {', '.join(change.affected_classes)}")
        
        # 確定風險評估
        risk_assessment = self._determine_test_risk(impact_score, changes)
        
        # 確定執行優先級
        execution_priority = self._calculate_execution_priority(impact_score, risk_assessment, test_info)
        
        return TestImpactAnalysis(
            test_case_id=test_id,
            impact_score=min(impact_score, 10.0),  # 限制最大分數
            affected_by_changes=list(set(affected_by_changes)),
            risk_assessment=risk_assessment,
            execution_priority=execution_priority,
            reasons=reasons
        )
    
    def _is_test_related_to_file(self, test_info: Dict[str, Any], file_path: str) -> bool:
        """判斷測試是否與文件相關"""
        test_file = test_info.get('test_file', '')
        test_target = test_info.get('target_module', '')
        
        # 直接文件關聯
        if file_path in test_file or file_path in test_target:
            return True
        
        # 模糊匹配
        file_name = Path(file_path).stem
        if file_name in test_file or file_name in test_target:
            return True
        
        return False
    
    def _is_test_related_to_functions(self, test_info: Dict[str, Any], functions: List[str]) -> bool:
        """判斷測試是否與函數相關"""
        test_methods = test_info.get('test_methods', [])
        test_description = test_info.get('description', '').lower()
        
        for func in functions:
            if any(func.lower() in method.lower() for method in test_methods):
                return True
            if func.lower() in test_description:
                return True
        
        return False
    
    def _is_test_related_to_classes(self, test_info: Dict[str, Any], classes: List[str]) -> bool:
        """判斷測試是否與類相關"""
        test_class = test_info.get('test_class', '')
        test_description = test_info.get('description', '').lower()
        
        for cls in classes:
            if cls.lower() in test_class.lower():
                return True
            if cls.lower() in test_description:
                return True
        
        return False
    
    def _calculate_file_impact_score(self, change: CodeChange) -> float:
        """計算文件影響分數"""
        base_score = 3.0
        
        # 基於風險等級調整
        risk_multiplier = {
            RegressionRisk.LOW: 1.0,
            RegressionRisk.MEDIUM: 1.5,
            RegressionRisk.HIGH: 2.0,
            RegressionRisk.CRITICAL: 3.0
        }
        
        return base_score * risk_multiplier.get(change.risk_level, 1.0)
    
    def _calculate_function_impact_score(self, change: CodeChange) -> float:
        """計算函數影響分數"""
        return len(change.affected_functions) * 0.5
    
    def _calculate_class_impact_score(self, change: CodeChange) -> float:
        """計算類影響分數"""
        return len(change.affected_classes) * 1.0
    
    def _determine_test_risk(self, impact_score: float, changes: List[CodeChange]) -> RegressionRisk:
        """確定測試風險"""
        if impact_score >= 8.0:
            return RegressionRisk.CRITICAL
        elif impact_score >= 5.0:
            return RegressionRisk.HIGH
        elif impact_score >= 2.0:
            return RegressionRisk.MEDIUM
        else:
            return RegressionRisk.LOW
    
    def _calculate_execution_priority(self, impact_score: float, risk: RegressionRisk, 
                                    test_info: Dict[str, Any]) -> int:
        """計算執行優先級"""
        priority = int(impact_score * 10)
        
        # 基於風險等級調整
        if risk == RegressionRisk.CRITICAL:
            priority += 50
        elif risk == RegressionRisk.HIGH:
            priority += 30
        elif risk == RegressionRisk.MEDIUM:
            priority += 15
        
        # 基於測試類型調整
        test_type = test_info.get('type', '')
        if test_type in ['smoke', 'critical']:
            priority += 20
        elif test_type in ['integration', 'e2e']:
            priority += 10
        
        return min(priority, 100)


class SmartTestSelector:
    """智能測試選擇器"""
    
    def __init__(self, analyzer: TestImpactAnalyzer):
        self.analyzer = analyzer
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def select_tests(self, impact_analyses: List[TestImpactAnalysis], 
                    strategy: TestSelectionStrategy,
                    max_tests: Optional[int] = None) -> List[str]:
        """選擇測試用例"""
        if strategy == TestSelectionStrategy.ALL_TESTS:
            return self._select_all_tests(impact_analyses, max_tests)
        elif strategy == TestSelectionStrategy.IMPACT_BASED:
            return self._select_impact_based_tests(impact_analyses, max_tests)
        elif strategy == TestSelectionStrategy.RISK_BASED:
            return self._select_risk_based_tests(impact_analyses, max_tests)
        elif strategy == TestSelectionStrategy.CHANGE_BASED:
            return self._select_change_based_tests(impact_analyses, max_tests)
        elif strategy == TestSelectionStrategy.SMART_SELECTION:
            return self._select_smart_tests(impact_analyses, max_tests)
        else:
            return self._select_all_tests(impact_analyses, max_tests)
    
    def _select_all_tests(self, analyses: List[TestImpactAnalysis], max_tests: Optional[int]) -> List[str]:
        """選擇所有測試"""
        tests = [a.test_case_id for a in analyses]
        return tests[:max_tests] if max_tests else tests
    
    def _select_impact_based_tests(self, analyses: List[TestImpactAnalysis], max_tests: Optional[int]) -> List[str]:
        """基於影響分數選擇測試"""
        # 按影響分數排序
        sorted_analyses = sorted(analyses, key=lambda x: x.impact_score, reverse=True)
        
        # 選擇高影響分數的測試
        selected = [a.test_case_id for a in sorted_analyses if a.impact_score > 0]
        
        return selected[:max_tests] if max_tests else selected
    
    def _select_risk_based_tests(self, analyses: List[TestImpactAnalysis], max_tests: Optional[int]) -> List[str]:
        """基於風險等級選擇測試"""
        # 優先選擇高風險測試
        risk_order = [RegressionRisk.CRITICAL, RegressionRisk.HIGH, RegressionRisk.MEDIUM, RegressionRisk.LOW]
        
        selected = []
        for risk_level in risk_order:
            risk_tests = [a.test_case_id for a in analyses if a.risk_assessment == risk_level]
            selected.extend(risk_tests)
            
            if max_tests and len(selected) >= max_tests:
                break
        
        return selected[:max_tests] if max_tests else selected
    
    def _select_change_based_tests(self, analyses: List[TestImpactAnalysis], max_tests: Optional[int]) -> List[str]:
        """基於變更關聯選擇測試"""
        # 選擇與變更相關的測試
        selected = [a.test_case_id for a in analyses if a.affected_by_changes]
        
        return selected[:max_tests] if max_tests else selected
    
    def _select_smart_tests(self, analyses: List[TestImpactAnalysis], max_tests: Optional[int]) -> List[str]:
        """智能選擇測試"""
        # 綜合考慮影響分數、風險等級和執行優先級
        scored_tests = []
        
        for analysis in analyses:
            smart_score = (
                analysis.impact_score * 0.4 +
                self._risk_to_score(analysis.risk_assessment) * 0.3 +
                analysis.execution_priority * 0.01 * 0.3
            )
            scored_tests.append((analysis.test_case_id, smart_score))
        
        # 按智能分數排序
        scored_tests.sort(key=lambda x: x[1], reverse=True)
        
        selected = [test_id for test_id, score in scored_tests if score > 1.0]
        
        return selected[:max_tests] if max_tests else selected
    
    def _risk_to_score(self, risk: RegressionRisk) -> float:
        """將風險等級轉換為分數"""
        risk_scores = {
            RegressionRisk.CRITICAL: 10.0,
            RegressionRisk.HIGH: 7.0,
            RegressionRisk.MEDIUM: 4.0,
            RegressionRisk.LOW: 1.0
        }
        return risk_scores.get(risk, 1.0)


class RegressionTestManager:
    """回歸測試管理器"""
    
    def __init__(self, repo_path: str, test_registry: Dict[str, Any]):
        self.repo_path = repo_path
        self.test_registry = test_registry
        self.code_analyzer = CodeAnalyzer(repo_path)
        self.impact_analyzer = TestImpactAnalyzer(test_registry)
        self.test_selector = SmartTestSelector(self.impact_analyzer)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def create_regression_test_suite(self, base_version: str, target_version: str,
                                         selection_strategy: TestSelectionStrategy = TestSelectionStrategy.SMART_SELECTION,
                                         max_tests: Optional[int] = None) -> RegressionTestSuite:
        """創建回歸測試套件"""
        self.logger.info(f"創建回歸測試套件: {base_version} -> {target_version}")
        
        # 分析代碼變更
        changes = self.code_analyzer.analyze_changes_between_versions(base_version, target_version)
        self.logger.info(f"檢測到 {len(changes)} 個代碼變更")
        
        # 獲取可用測試
        available_tests = list(self.test_registry.keys())
        
        # 分析測試影響
        impact_analyses = self.impact_analyzer.analyze_test_impact(changes, available_tests)
        self.logger.info(f"完成 {len(impact_analyses)} 個測試的影響分析")
        
        # 選擇測試用例
        selected_tests = self.test_selector.select_tests(impact_analyses, selection_strategy, max_tests)
        self.logger.info(f"選擇了 {len(selected_tests)} 個測試用例")
        
        # 創建回歸測試套件
        suite = RegressionTestSuite(
            id=f"regression_{base_version}_{target_version}_{int(datetime.now().timestamp())}",
            name=f"回歸測試: {base_version} -> {target_version}",
            base_version=base_version,
            target_version=target_version,
            changes=changes,
            selected_tests=selected_tests,
            selection_strategy=selection_strategy,
            impact_analysis=impact_analyses,
            created_at=datetime.now().isoformat()
        )
        
        # 保存測試套件
        await self._save_regression_test_suite(suite)
        
        return suite
    
    async def _save_regression_test_suite(self, suite: RegressionTestSuite):
        """保存回歸測試套件"""
        suite_dir = Path("regression_test_suites")
        suite_dir.mkdir(exist_ok=True)
        
        suite_file = suite_dir / f"{suite.id}.json"
        
        with open(suite_file, "w", encoding="utf-8") as f:
            json.dump(asdict(suite), f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"回歸測試套件已保存: {suite_file}")
    
    async def generate_regression_report(self, suite: RegressionTestSuite, 
                                       test_results: List[Any]) -> Dict[str, Any]:
        """生成回歸測試報告"""
        report = {
            "suite_info": {
                "id": suite.id,
                "name": suite.name,
                "base_version": suite.base_version,
                "target_version": suite.target_version,
                "selection_strategy": suite.selection_strategy.value,
                "created_at": suite.created_at
            },
            "changes_analysis": {
                "total_changes": len(suite.changes),
                "change_types": self._analyze_change_types(suite.changes),
                "risk_distribution": self._analyze_risk_distribution(suite.changes),
                "affected_files": len(set(c.file_path for c in suite.changes))
            },
            "test_selection": {
                "total_available_tests": len(self.test_registry),
                "selected_tests": len(suite.selected_tests),
                "selection_coverage": len(suite.selected_tests) / len(self.test_registry) * 100,
                "high_impact_tests": len([a for a in suite.impact_analysis if a.impact_score >= 5.0])
            },
            "test_results": self._analyze_test_results(test_results),
            "regression_assessment": self._assess_regression_risk(suite, test_results),
            "recommendations": self._generate_recommendations(suite, test_results)
        }
        
        # 保存報告
        report_dir = Path("regression_reports")
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"regression_report_{suite.id}_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"回歸測試報告已生成: {report_file}")
        
        return report
    
    def _analyze_change_types(self, changes: List[CodeChange]) -> Dict[str, int]:
        """分析變更類型分布"""
        type_counts = {}
        for change in changes:
            type_key = change.change_type.value
            type_counts[type_key] = type_counts.get(type_key, 0) + 1
        return type_counts
    
    def _analyze_risk_distribution(self, changes: List[CodeChange]) -> Dict[str, int]:
        """分析風險分布"""
        risk_counts = {}
        for change in changes:
            risk_key = change.risk_level.value
            risk_counts[risk_key] = risk_counts.get(risk_key, 0) + 1
        return risk_counts
    
    def _analyze_test_results(self, test_results: List[Any]) -> Dict[str, Any]:
        """分析測試結果"""
        if not test_results:
            return {}
        
        total_tests = len(test_results)
        passed_tests = len([r for r in test_results if getattr(r, 'status', '') == 'passed'])
        failed_tests = len([r for r in test_results if getattr(r, 'status', '') == 'failed'])
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "failure_rate": (failed_tests / total_tests * 100) if total_tests > 0 else 0
        }
    
    def _assess_regression_risk(self, suite: RegressionTestSuite, test_results: List[Any]) -> Dict[str, Any]:
        """評估回歸風險"""
        # 基於測試結果和變更分析評估回歸風險
        high_risk_changes = len([c for c in suite.changes if c.risk_level in [RegressionRisk.HIGH, RegressionRisk.CRITICAL]])
        total_changes = len(suite.changes)
        
        failed_tests = len([r for r in test_results if getattr(r, 'status', '') == 'failed'])
        total_tests = len(test_results)
        
        risk_score = 0
        
        # 基於失敗測試的風險
        if total_tests > 0:
            failure_rate = failed_tests / total_tests
            if failure_rate > 0.1:  # 10%以上失敗率
                risk_score += 3
            elif failure_rate > 0.05:  # 5%以上失敗率
                risk_score += 2
            elif failure_rate > 0:
                risk_score += 1
        
        # 基於高風險變更的風險
        if total_changes > 0:
            high_risk_ratio = high_risk_changes / total_changes
            if high_risk_ratio > 0.3:
                risk_score += 3
            elif high_risk_ratio > 0.1:
                risk_score += 2
            elif high_risk_ratio > 0:
                risk_score += 1
        
        # 確定總體風險等級
        if risk_score >= 5:
            overall_risk = RegressionRisk.CRITICAL
        elif risk_score >= 3:
            overall_risk = RegressionRisk.HIGH
        elif risk_score >= 1:
            overall_risk = RegressionRisk.MEDIUM
        else:
            overall_risk = RegressionRisk.LOW
        
        return {
            "overall_risk": overall_risk.value,
            "risk_score": risk_score,
            "high_risk_changes": high_risk_changes,
            "failed_tests": failed_tests,
            "risk_factors": self._identify_risk_factors(suite, test_results)
        }
    
    def _identify_risk_factors(self, suite: RegressionTestSuite, test_results: List[Any]) -> List[str]:
        """識別風險因素"""
        risk_factors = []
        
        # 檢查關鍵文件變更
        critical_files = [c for c in suite.changes if c.risk_level == RegressionRisk.CRITICAL]
        if critical_files:
            risk_factors.append(f"關鍵文件變更: {len(critical_files)} 個文件")
        
        # 檢查大規模變更
        large_changes = [c for c in suite.changes if c.lines_added + c.lines_removed > 100]
        if large_changes:
            risk_factors.append(f"大規模代碼變更: {len(large_changes)} 個文件")
        
        # 檢查測試失敗
        failed_tests = [r for r in test_results if getattr(r, 'status', '') == 'failed']
        if failed_tests:
            risk_factors.append(f"測試失敗: {len(failed_tests)} 個測試")
        
        return risk_factors
    
    def _generate_recommendations(self, suite: RegressionTestSuite, test_results: List[Any]) -> List[str]:
        """生成建議"""
        recommendations = []
        
        # 基於測試結果的建議
        failed_tests = [r for r in test_results if getattr(r, 'status', '') == 'failed']
        if failed_tests:
            recommendations.append(f"立即修復 {len(failed_tests)} 個失敗的測試")
        
        # 基於變更風險的建議
        high_risk_changes = [c for c in suite.changes if c.risk_level in [RegressionRisk.HIGH, RegressionRisk.CRITICAL]]
        if high_risk_changes:
            recommendations.append(f"重點關注 {len(high_risk_changes)} 個高風險變更")
        
        # 基於測試覆蓋的建議
        if len(suite.selected_tests) < len(self.test_registry) * 0.5:
            recommendations.append("考慮擴大測試覆蓋範圍，當前測試覆蓋率較低")
        
        return recommendations


# 單例實例
def create_regression_test_manager(repo_path: str, test_registry: Dict[str, Any]) -> RegressionTestManager:
    """創建回歸測試管理器實例"""
    return RegressionTestManager(repo_path, test_registry)