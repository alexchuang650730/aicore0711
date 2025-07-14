"""
Result Transformer - Format Conversion Between Trae Agent and PowerAutomation

This module provides comprehensive result transformation capabilities,
converting between Trae Agent output format and PowerAutomation result format.
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
from enum import Enum


class ResultType(Enum):
    """Types of results that can be transformed"""
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    DEBUGGING = "debugging"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ARCHITECTURE = "architecture"
    PERFORMANCE = "performance"
    SECURITY = "security"


@dataclass
class TransformationRule:
    """Rule for transforming specific result types"""
    source_field: str
    target_field: str
    transformation_function: str
    required: bool = True
    default_value: Any = None


@dataclass
class QualityMetrics:
    """Quality metrics for transformed results"""
    completeness_score: float
    accuracy_score: float
    relevance_score: float
    format_compliance: float
    overall_quality: float


class ResultTransformer:
    """
    Result Transformer
    
    Transforms results between Trae Agent format and PowerAutomation format,
    ensuring data integrity, quality validation, and format compliance.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Result Transformer
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Transformation configuration
        self.enable_quality_validation = self.config.get('enable_quality_validation', True)
        self.enable_format_validation = self.config.get('enable_format_validation', True)
        self.enable_content_enhancement = self.config.get('enable_content_enhancement', True)
        
        # Transformation rules
        self.transformation_rules = self._initialize_transformation_rules()
        
        # Quality thresholds
        self.quality_thresholds = {
            'completeness_min': 0.7,
            'accuracy_min': 0.8,
            'relevance_min': 0.7,
            'format_compliance_min': 0.9,
            'overall_quality_min': 0.75
        }
        
        # Performance tracking
        self.transformation_stats = {
            'total_transformations': 0,
            'successful_transformations': 0,
            'failed_transformations': 0,
            'average_transformation_time': 0.0,
            'quality_scores': []
        }
        
        self.logger.info("ResultTransformer initialized")
    
    async def transform_to_pa_format(self, trae_result: Dict[str, Any], original_task: Any) -> Dict[str, Any]:
        """
        Transform Trae Agent result to PowerAutomation format
        
        Args:
            trae_result: Result from Trae Agent
            original_task: Original PowerAutomation task
            
        Returns:
            Dict: Result in PowerAutomation format
        """
        start_time = time.time()
        
        try:
            self.logger.info("Transforming Trae Agent result to PowerAutomation format")
            
            # Validate input
            if not await self._validate_trae_result(trae_result):
                raise ValueError("Invalid Trae Agent result format")
            
            # Determine result type
            result_type = await self._determine_result_type(trae_result, original_task)
            
            # Apply transformation rules
            transformed_result = await self._apply_transformation_rules(
                trae_result, original_task, result_type
            )
            
            # Enhance content if enabled
            if self.enable_content_enhancement:
                transformed_result = await self._enhance_content(
                    transformed_result, result_type, original_task
                )
            
            # Validate quality if enabled
            if self.enable_quality_validation:
                quality_metrics = await self._validate_quality(
                    transformed_result, trae_result, original_task
                )
                transformed_result['quality_metrics'] = quality_metrics
            
            # Validate format if enabled
            if self.enable_format_validation:
                format_valid = await self._validate_pa_format(transformed_result)
                if not format_valid:
                    self.logger.warning("Transformed result does not meet format requirements")
            
            # Update statistics
            transformation_time = time.time() - start_time
            await self._update_transformation_stats(transformation_time, True, transformed_result)
            
            self.logger.info(f"Result transformation completed in {transformation_time:.2f}s")
            return transformed_result
            
        except Exception as e:
            transformation_time = time.time() - start_time
            await self._update_transformation_stats(transformation_time, False, None)
            
            self.logger.error(f"Result transformation failed: {str(e)}")
            
            # Return fallback result
            return await self._create_fallback_result(trae_result, original_task, str(e))
    
    async def transform_to_trae_format(self, pa_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform PowerAutomation result to Trae Agent format (for feedback/learning)
        
        Args:
            pa_result: PowerAutomation result
            
        Returns:
            Dict: Result in Trae Agent format
        """
        try:
            self.logger.info("Transforming PowerAutomation result to Trae Agent format")
            
            # Basic transformation (reverse of main transformation)
            trae_result = {
                'success': pa_result.get('success', True),
                'output': pa_result.get('content', ''),
                'files_modified': pa_result.get('files_modified', []),
                'tools_used': pa_result.get('tools_used', []),
                'model_used': pa_result.get('model_used', 'unknown'),
                'execution_time': pa_result.get('execution_time', 0.0),
                'trajectory': pa_result.get('trajectory', []),
                'metadata': pa_result.get('metadata', {})
            }
            
            return trae_result
            
        except Exception as e:
            self.logger.error(f"Reverse transformation failed: {str(e)}")
            return {}
    
    async def _validate_trae_result(self, trae_result: Dict[str, Any]) -> bool:
        """
        Validate Trae Agent result format
        
        Args:
            trae_result: Trae Agent result to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ['success', 'output', 'execution_time']
        
        # Check required fields
        for field in required_fields:
            if field not in trae_result:
                self.logger.error(f"Missing required field in Trae result: {field}")
                return False
        
        # Validate field types
        if not isinstance(trae_result['success'], bool):
            self.logger.error("'success' field must be boolean")
            return False
        
        if not isinstance(trae_result['output'], str):
            self.logger.error("'output' field must be string")
            return False
        
        if not isinstance(trae_result['execution_time'], (int, float)):
            self.logger.error("'execution_time' field must be numeric")
            return False
        
        return True
    
    async def _determine_result_type(self, trae_result: Dict[str, Any], original_task: Any) -> ResultType:
        """
        Determine the type of result based on content and task
        
        Args:
            trae_result: Trae Agent result
            original_task: Original task
            
        Returns:
            ResultType: Determined result type
        """
        # Check task description for type hints
        task_description = getattr(original_task, 'description', '').lower()
        
        # Type detection based on keywords
        type_keywords = {
            ResultType.CODE_ANALYSIS: ['analyze', 'analysis', 'examine', 'inspect', 'review'],
            ResultType.CODE_GENERATION: ['generate', 'create', 'write', 'implement', 'build'],
            ResultType.DEBUGGING: ['debug', 'bug', 'error', 'fix', 'issue', 'problem'],
            ResultType.REFACTORING: ['refactor', 'improve', 'optimize', 'restructure', 'clean'],
            ResultType.DOCUMENTATION: ['document', 'documentation', 'comment', 'explain', 'describe'],
            ResultType.TESTING: ['test', 'testing', 'unit test', 'integration test', 'coverage'],
            ResultType.ARCHITECTURE: ['design', 'architecture', 'structure', 'pattern', 'framework'],
            ResultType.PERFORMANCE: ['performance', 'optimize', 'speed', 'efficiency', 'benchmark'],
            ResultType.SECURITY: ['security', 'vulnerability', 'secure', 'safety', 'protection']
        }
        
        # Score each type
        type_scores = {}
        for result_type, keywords in type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in task_description)
            if score > 0:
                type_scores[result_type] = score
        
        # Check result content for additional hints
        result_output = trae_result.get('output', '').lower()
        
        # Additional scoring based on result content
        if 'class ' in result_output or 'function ' in result_output or 'def ' in result_output:
            type_scores[ResultType.CODE_GENERATION] = type_scores.get(ResultType.CODE_GENERATION, 0) + 2
        
        if 'error' in result_output or 'exception' in result_output or 'traceback' in result_output:
            type_scores[ResultType.DEBUGGING] = type_scores.get(ResultType.DEBUGGING, 0) + 2
        
        if 'test' in result_output or 'assert' in result_output:
            type_scores[ResultType.TESTING] = type_scores.get(ResultType.TESTING, 0) + 2
        
        # Return highest scoring type, default to CODE_ANALYSIS
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        else:
            return ResultType.CODE_ANALYSIS
    
    async def _apply_transformation_rules(
        self, 
        trae_result: Dict[str, Any], 
        original_task: Any, 
        result_type: ResultType
    ) -> Dict[str, Any]:
        """
        Apply transformation rules to convert Trae result to PowerAutomation format
        
        Args:
            trae_result: Trae Agent result
            original_task: Original task
            result_type: Determined result type
            
        Returns:
            Dict: Transformed result
        """
        # Base PowerAutomation result structure
        pa_result = {
            'task_id': getattr(original_task, 'id', 'unknown'),
            'success': trae_result.get('success', False),
            'result_type': result_type.value,
            'content': '',
            'summary': '',
            'details': {},
            'files_modified': trae_result.get('files_modified', []),
            'tools_used': trae_result.get('tools_used', []),
            'model_used': trae_result.get('model_used', 'unknown'),
            'execution_time': trae_result.get('execution_time', 0.0),
            'metadata': {
                'original_trae_result': trae_result,
                'transformation_timestamp': time.time(),
                'result_type': result_type.value
            }
        }
        
        # Apply type-specific transformations
        if result_type == ResultType.CODE_ANALYSIS:
            pa_result.update(await self._transform_code_analysis(trae_result, original_task))
        elif result_type == ResultType.CODE_GENERATION:
            pa_result.update(await self._transform_code_generation(trae_result, original_task))
        elif result_type == ResultType.DEBUGGING:
            pa_result.update(await self._transform_debugging(trae_result, original_task))
        elif result_type == ResultType.REFACTORING:
            pa_result.update(await self._transform_refactoring(trae_result, original_task))
        elif result_type == ResultType.DOCUMENTATION:
            pa_result.update(await self._transform_documentation(trae_result, original_task))
        elif result_type == ResultType.TESTING:
            pa_result.update(await self._transform_testing(trae_result, original_task))
        elif result_type == ResultType.ARCHITECTURE:
            pa_result.update(await self._transform_architecture(trae_result, original_task))
        elif result_type == ResultType.PERFORMANCE:
            pa_result.update(await self._transform_performance(trae_result, original_task))
        elif result_type == ResultType.SECURITY:
            pa_result.update(await self._transform_security(trae_result, original_task))
        else:
            # Default transformation
            pa_result.update(await self._transform_default(trae_result, original_task))
        
        return pa_result
    
    async def _transform_code_analysis(self, trae_result: Dict[str, Any], original_task: Any) -> Dict[str, Any]:
        """Transform code analysis result"""
        output = trae_result.get('output', '')
        
        return {
            'content': output,
            'summary': await self._extract_summary(output, 'code analysis'),
            'details': {
                'analysis_type': 'code_analysis',
                'findings': await self._extract_findings(output),
                'recommendations': await self._extract_recommendations(output),
                'code_quality_score': await self._extract_quality_score(output),
                'complexity_metrics': await self._extract_complexity_metrics(output)
            }
        }
    
    async def _transform_code_generation(self, trae_result: Dict[str, Any], original_task: Any) -> Dict[str, Any]:
        """Transform code generation result"""
        output = trae_result.get('output', '')
        
        return {
            'content': output,
            'summary': await self._extract_summary(output, 'code generation'),
            'details': {
                'generation_type': 'code_generation',
                'generated_files': trae_result.get('files_modified', []),
                'code_blocks': await self._extract_code_blocks(output),
                'language': await self._detect_programming_language(output),
                'estimated_lines': await self._count_code_lines(output)
            }
        }
    
    async def _transform_debugging(self, trae_result: Dict[str, Any], original_task: Any) -> Dict[str, Any]:
        """Transform debugging result"""
        output = trae_result.get('output', '')
        
        return {
            'content': output,
            'summary': await self._extract_summary(output, 'debugging'),
            'details': {
                'debug_type': 'debugging',
                'issues_found': await self._extract_issues(output),
                'fixes_applied': await self._extract_fixes(output),
                'root_cause': await self._extract_root_cause(output),
                'testing_suggestions': await self._extract_testing_suggestions(output)
            }
        }
    
    async def _transform_refactoring(self, trae_result: Dict[str, Any], original_task: Any) -> Dict[str, Any]:
        """Transform refactoring result"""
        output = trae_result.get('output', '')
        
        return {
            'content': output,
            'summary': await self._extract_summary(output, 'refactoring'),
            'details': {
                'refactoring_type': 'refactoring',
                'changes_made': await self._extract_changes(output),
                'improvements': await self._extract_improvements(output),
                'before_after_comparison': await self._extract_comparison(output),
                'impact_assessment': await self._extract_impact(output)
            }
        }
    
    async def _transform_documentation(self, trae_result: Dict[str, Any], original_task: Any) -> Dict[str, Any]:
        """Transform documentation result"""
        output = trae_result.get('output', '')
        
        return {
            'content': output,
            'summary': await self._extract_summary(output, 'documentation'),
            'details': {
                'documentation_type': 'documentation',
                'sections_created': await self._extract_sections(output),
                'coverage_areas': await self._extract_coverage(output),
                'format': await self._detect_documentation_format(output),
                'completeness_score': await self._assess_documentation_completeness(output)
            }
        }
    
    async def _transform_testing(self, trae_result: Dict[str, Any], original_task: Any) -> Dict[str, Any]:
        """Transform testing result"""
        output = trae_result.get('output', '')
        
        return {
            'content': output,
            'summary': await self._extract_summary(output, 'testing'),
            'details': {
                'testing_type': 'testing',
                'test_cases_created': await self._extract_test_cases(output),
                'coverage_metrics': await self._extract_coverage_metrics(output),
                'test_framework': await self._detect_test_framework(output),
                'assertions_count': await self._count_assertions(output)
            }
        }
    
    async def _transform_architecture(self, trae_result: Dict[str, Any], original_task: Any) -> Dict[str, Any]:
        """Transform architecture result"""
        output = trae_result.get('output', '')
        
        return {
            'content': output,
            'summary': await self._extract_summary(output, 'architecture'),
            'details': {
                'architecture_type': 'architecture',
                'design_patterns': await self._extract_patterns(output),
                'components': await self._extract_components(output),
                'relationships': await self._extract_relationships(output),
                'scalability_considerations': await self._extract_scalability(output)
            }
        }
    
    async def _transform_performance(self, trae_result: Dict[str, Any], original_task: Any) -> Dict[str, Any]:
        """Transform performance result"""
        output = trae_result.get('output', '')
        
        return {
            'content': output,
            'summary': await self._extract_summary(output, 'performance'),
            'details': {
                'performance_type': 'performance',
                'metrics': await self._extract_performance_metrics(output),
                'bottlenecks': await self._extract_bottlenecks(output),
                'optimizations': await self._extract_optimizations(output),
                'benchmark_results': await self._extract_benchmarks(output)
            }
        }
    
    async def _transform_security(self, trae_result: Dict[str, Any], original_task: Any) -> Dict[str, Any]:
        """Transform security result"""
        output = trae_result.get('output', '')
        
        return {
            'content': output,
            'summary': await self._extract_summary(output, 'security'),
            'details': {
                'security_type': 'security',
                'vulnerabilities': await self._extract_vulnerabilities(output),
                'risk_assessment': await self._extract_risk_assessment(output),
                'mitigation_strategies': await self._extract_mitigations(output),
                'compliance_status': await self._extract_compliance(output)
            }
        }
    
    async def _transform_default(self, trae_result: Dict[str, Any], original_task: Any) -> Dict[str, Any]:
        """Default transformation for unknown result types"""
        output = trae_result.get('output', '')
        
        return {
            'content': output,
            'summary': await self._extract_summary(output, 'general'),
            'details': {
                'result_type': 'general',
                'key_points': await self._extract_key_points(output),
                'conclusions': await self._extract_conclusions(output)
            }
        }
    
    # Helper methods for content extraction
    async def _extract_summary(self, content: str, result_type: str) -> str:
        """Extract summary from content"""
        # Simple implementation - take first paragraph or first 200 characters
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and len(line) > 20:
                return line[:200] + ('...' if len(line) > 200 else '')
        
        return content[:200] + ('...' if len(content) > 200 else '')
    
    async def _extract_findings(self, content: str) -> List[str]:
        """Extract findings from content"""
        findings = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['found', 'identified', 'discovered', 'issue', 'problem']):
                findings.append(line)
        
        return findings[:10]  # Limit to 10 findings
    
    async def _extract_recommendations(self, content: str) -> List[str]:
        """Extract recommendations from content"""
        recommendations = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'consider', 'improve']):
                recommendations.append(line)
        
        return recommendations[:10]  # Limit to 10 recommendations
    
    async def _extract_quality_score(self, content: str) -> Optional[float]:
        """Extract quality score from content"""
        # Look for numeric scores in the content
        import re
        
        score_patterns = [
            r'quality.*?(\d+(?:\.\d+)?)',
            r'score.*?(\d+(?:\.\d+)?)',
            r'rating.*?(\d+(?:\.\d+)?)'
        ]
        
        for pattern in score_patterns:
            matches = re.findall(pattern, content.lower())
            if matches:
                try:
                    score = float(matches[0])
                    if 0 <= score <= 100:
                        return score / 100  # Normalize to 0-1
                    elif 0 <= score <= 10:
                        return score / 10   # Normalize to 0-1
                    elif 0 <= score <= 1:
                        return score
                except ValueError:
                    continue
        
        return None
    
    async def _extract_complexity_metrics(self, content: str) -> Dict[str, Any]:
        """Extract complexity metrics from content"""
        metrics = {}
        
        # Look for common complexity metrics
        import re
        
        metric_patterns = {
            'cyclomatic_complexity': r'cyclomatic.*?(\d+)',
            'cognitive_complexity': r'cognitive.*?(\d+)',
            'lines_of_code': r'lines.*?(\d+)',
            'functions': r'functions.*?(\d+)',
            'classes': r'classes.*?(\d+)'
        }
        
        for metric_name, pattern in metric_patterns.items():
            matches = re.findall(pattern, content.lower())
            if matches:
                try:
                    metrics[metric_name] = int(matches[0])
                except ValueError:
                    continue
        
        return metrics
    
    async def _extract_code_blocks(self, content: str) -> List[str]:
        """Extract code blocks from content"""
        import re
        
        # Look for code blocks marked with ```
        code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', content, re.DOTALL)
        
        # Also look for indented code blocks
        lines = content.split('\n')
        current_block = []
        code_blocks_indented = []
        
        for line in lines:
            if line.startswith('    ') or line.startswith('\t'):
                current_block.append(line)
            else:
                if current_block:
                    code_blocks_indented.append('\n'.join(current_block))
                    current_block = []
        
        if current_block:
            code_blocks_indented.append('\n'.join(current_block))
        
        return code_blocks + code_blocks_indented
    
    async def _detect_programming_language(self, content: str) -> str:
        """Detect programming language from content"""
        language_indicators = {
            'python': ['def ', 'import ', 'class ', 'if __name__', 'print('],
            'javascript': ['function ', 'const ', 'let ', 'var ', '=>', 'console.log'],
            'java': ['public class', 'private ', 'public ', 'System.out'],
            'cpp': ['#include', 'std::', 'cout', 'cin', 'int main'],
            'c': ['#include', 'printf', 'scanf', 'int main'],
            'go': ['package ', 'func ', 'import ', 'fmt.'],
            'rust': ['fn ', 'let ', 'mut ', 'println!'],
            'typescript': ['interface ', 'type ', 'const ', ': string', ': number']
        }
        
        content_lower = content.lower()
        
        for language, indicators in language_indicators.items():
            score = sum(1 for indicator in indicators if indicator in content_lower)
            if score >= 2:
                return language
        
        return 'unknown'
    
    async def _count_code_lines(self, content: str) -> int:
        """Count lines of code in content"""
        code_blocks = await self._extract_code_blocks(content)
        total_lines = 0
        
        for block in code_blocks:
            lines = [line.strip() for line in block.split('\n') if line.strip()]
            total_lines += len(lines)
        
        return total_lines
    
    # Additional helper methods would be implemented similarly...
    async def _extract_issues(self, content: str) -> List[str]:
        """Extract issues from debugging content"""
        return await self._extract_findings(content)  # Reuse findings extraction
    
    async def _extract_fixes(self, content: str) -> List[str]:
        """Extract fixes from debugging content"""
        fixes = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['fix', 'fixed', 'solution', 'resolved', 'corrected']):
                fixes.append(line)
        
        return fixes[:10]
    
    async def _extract_root_cause(self, content: str) -> str:
        """Extract root cause from debugging content"""
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['root cause', 'cause', 'reason', 'because']):
                return line
        
        return "Root cause not explicitly identified"
    
    async def _extract_testing_suggestions(self, content: str) -> List[str]:
        """Extract testing suggestions"""
        return await self._extract_recommendations(content)  # Reuse recommendations extraction
    
    # More helper methods would be implemented for other transformation types...
    
    async def _enhance_content(self, result: Dict[str, Any], result_type: ResultType, original_task: Any) -> Dict[str, Any]:
        """Enhance content with additional information"""
        if not self.enable_content_enhancement:
            return result
        
        # Add enhancement metadata
        result['metadata']['content_enhanced'] = True
        result['metadata']['enhancement_timestamp'] = time.time()
        
        # Add task context to summary if not present
        if 'task_context' not in result['summary']:
            task_description = getattr(original_task, 'description', '')
            if task_description:
                result['summary'] = f"Task: {task_description[:100]}... | {result['summary']}"
        
        return result
    
    async def _validate_quality(
        self, 
        transformed_result: Dict[str, Any], 
        trae_result: Dict[str, Any], 
        original_task: Any
    ) -> QualityMetrics:
        """Validate quality of transformed result"""
        
        # Calculate completeness score
        completeness_score = await self._calculate_completeness_score(transformed_result, trae_result)
        
        # Calculate accuracy score
        accuracy_score = await self._calculate_accuracy_score(transformed_result, trae_result)
        
        # Calculate relevance score
        relevance_score = await self._calculate_relevance_score(transformed_result, original_task)
        
        # Calculate format compliance
        format_compliance = await self._calculate_format_compliance(transformed_result)
        
        # Calculate overall quality
        overall_quality = (completeness_score + accuracy_score + relevance_score + format_compliance) / 4
        
        return QualityMetrics(
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            relevance_score=relevance_score,
            format_compliance=format_compliance,
            overall_quality=overall_quality
        )
    
    async def _calculate_completeness_score(self, transformed_result: Dict[str, Any], trae_result: Dict[str, Any]) -> float:
        """Calculate completeness score"""
        required_fields = ['content', 'summary', 'details']
        present_fields = sum(1 for field in required_fields if field in transformed_result and transformed_result[field])
        
        return present_fields / len(required_fields)
    
    async def _calculate_accuracy_score(self, transformed_result: Dict[str, Any], trae_result: Dict[str, Any]) -> float:
        """Calculate accuracy score"""
        # Simple accuracy check - ensure content is preserved
        original_content = trae_result.get('output', '')
        transformed_content = transformed_result.get('content', '')
        
        if not original_content:
            return 1.0
        
        # Check if key information is preserved
        original_words = set(original_content.lower().split())
        transformed_words = set(transformed_content.lower().split())
        
        if not original_words:
            return 1.0
        
        preserved_ratio = len(original_words.intersection(transformed_words)) / len(original_words)
        return min(1.0, preserved_ratio + 0.2)  # Add bonus for transformation
    
    async def _calculate_relevance_score(self, transformed_result: Dict[str, Any], original_task: Any) -> float:
        """Calculate relevance score"""
        task_description = getattr(original_task, 'description', '').lower()
        result_content = transformed_result.get('content', '').lower()
        
        if not task_description or not result_content:
            return 0.5  # Neutral score
        
        task_words = set(task_description.split())
        result_words = set(result_content.split())
        
        if not task_words:
            return 0.5
        
        relevance_ratio = len(task_words.intersection(result_words)) / len(task_words)
        return min(1.0, relevance_ratio * 2)  # Scale up relevance
    
    async def _calculate_format_compliance(self, transformed_result: Dict[str, Any]) -> float:
        """Calculate format compliance score"""
        required_structure = {
            'task_id': str,
            'success': bool,
            'result_type': str,
            'content': str,
            'summary': str,
            'details': dict,
            'execution_time': (int, float),
            'metadata': dict
        }
        
        compliance_score = 0
        total_checks = len(required_structure)
        
        for field, expected_type in required_structure.items():
            if field in transformed_result:
                if isinstance(transformed_result[field], expected_type):
                    compliance_score += 1
                else:
                    compliance_score += 0.5  # Partial credit for presence
        
        return compliance_score / total_checks
    
    async def _validate_pa_format(self, result: Dict[str, Any]) -> bool:
        """Validate PowerAutomation format compliance"""
        required_fields = ['task_id', 'success', 'content', 'summary']
        
        for field in required_fields:
            if field not in result:
                self.logger.warning(f"Missing required field: {field}")
                return False
        
        return True
    
    async def _create_fallback_result(self, trae_result: Dict[str, Any], original_task: Any, error_message: str) -> Dict[str, Any]:
        """Create fallback result when transformation fails"""
        return {
            'task_id': getattr(original_task, 'id', 'unknown'),
            'success': False,
            'result_type': 'transformation_error',
            'content': trae_result.get('output', ''),
            'summary': f"Transformation failed: {error_message}",
            'details': {
                'error': error_message,
                'original_trae_result': trae_result,
                'fallback_used': True
            },
            'files_modified': trae_result.get('files_modified', []),
            'tools_used': trae_result.get('tools_used', []),
            'model_used': trae_result.get('model_used', 'unknown'),
            'execution_time': trae_result.get('execution_time', 0.0),
            'metadata': {
                'transformation_error': error_message,
                'fallback_timestamp': time.time()
            }
        }
    
    async def _update_transformation_stats(self, transformation_time: float, success: bool, result: Optional[Dict[str, Any]]):
        """Update transformation statistics"""
        self.transformation_stats['total_transformations'] += 1
        
        if success:
            self.transformation_stats['successful_transformations'] += 1
            
            # Update quality scores if available
            if result and 'quality_metrics' in result:
                quality_metrics = result['quality_metrics']
                if hasattr(quality_metrics, 'overall_quality'):
                    self.transformation_stats['quality_scores'].append(quality_metrics.overall_quality)
        else:
            self.transformation_stats['failed_transformations'] += 1
        
        # Update average transformation time
        total = self.transformation_stats['total_transformations']
        current_avg = self.transformation_stats['average_transformation_time']
        self.transformation_stats['average_transformation_time'] = (
            (current_avg * (total - 1) + transformation_time) / total
        )
    
    def _initialize_transformation_rules(self) -> Dict[str, List[TransformationRule]]:
        """Initialize transformation rules for different result types"""
        return {
            'default': [
                TransformationRule('output', 'content', 'direct_copy', True),
                TransformationRule('success', 'success', 'direct_copy', True),
                TransformationRule('execution_time', 'execution_time', 'direct_copy', True),
                TransformationRule('files_modified', 'files_modified', 'direct_copy', False, []),
                TransformationRule('tools_used', 'tools_used', 'direct_copy', False, []),
                TransformationRule('model_used', 'model_used', 'direct_copy', False, 'unknown')
            ]
        }
    
    async def get_transformation_stats(self) -> Dict[str, Any]:
        """Get transformation statistics"""
        stats = self.transformation_stats.copy()
        
        # Calculate additional metrics
        if stats['quality_scores']:
            stats['average_quality_score'] = sum(stats['quality_scores']) / len(stats['quality_scores'])
            stats['min_quality_score'] = min(stats['quality_scores'])
            stats['max_quality_score'] = max(stats['quality_scores'])
        else:
            stats['average_quality_score'] = 0.0
            stats['min_quality_score'] = 0.0
            stats['max_quality_score'] = 0.0
        
        # Calculate success rate
        if stats['total_transformations'] > 0:
            stats['success_rate'] = stats['successful_transformations'] / stats['total_transformations']
        else:
            stats['success_rate'] = 0.0
        
        return stats

