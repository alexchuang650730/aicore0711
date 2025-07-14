"""
AI助手API路由

提供多模型AI编程助手的API端点
"""

from flask import Blueprint, request, jsonify
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from core.components.ai_ecosystem_integration.claudeditor.multi_model_coordinator import MultiModelCoordinator
from core.components.ai_ecosystem_integration.claudeditor.claude_api_client import ClaudeAPIClient
from core.components.ai_ecosystem_integration.claudeditor.gemini_api_client import GeminiAPIClient

ai_assistant_bp = Blueprint('ai_assistant', __name__, url_prefix='/api/ai-assistant')

# 初始化多模型协调器
coordinator = None

def init_coordinator():
    """初始化多模型协调器"""
    global coordinator
    if coordinator is None:
        # API密钥配置
        claude_api_key = "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"
        gemini_api_key = "AIzaSyC_EsNirr14s8ypd3KafqWazSi_RW0NiqA"
        
        # 创建API客户端
        claude_client = ClaudeAPIClient(claude_api_key)
        gemini_client = GeminiAPIClient(gemini_api_key)
        
        # 创建协调器
        coordinator = MultiModelCoordinator(claude_client, gemini_client)
    
    return coordinator

@ai_assistant_bp.route('/process', methods=['POST'])
def process_request():
    """处理AI助手请求"""
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400
        
        # 验证必需字段
        required_fields = ['task_type', 'prompt']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'缺少必需字段: {field}'}), 400
        
        # 初始化协调器
        coord = init_coordinator()
        
        # 准备请求参数
        task_type = data.get('task_type')
        prompt = data.get('prompt')
        language = data.get('language', 'python')
        strategy = data.get('strategy', 'auto_select')
        context = data.get('context')
        priority = data.get('priority', 3)
        constraints = data.get('constraints', {})
        
        # 异步处理请求
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                coord.process_request(
                    task_type=task_type,
                    prompt=prompt,
                    language=language,
                    strategy=strategy,
                    context=context,
                    priority=priority,
                    constraints=constraints
                )
            )
            
            return jsonify(result)
            
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({
            'error': f'处理请求时发生错误: {str(e)}',
            'success': False
        }), 500

@ai_assistant_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """获取API统计信息"""
    try:
        coord = init_coordinator()
        
        # 获取协调器统计信息
        coordinator_stats = coord.get_statistics()
        
        # 获取模型性能数据
        model_performance = {
            'claude': coord.claude_client.get_statistics() if hasattr(coord.claude_client, 'get_statistics') else {},
            'gemini': coord.gemini_client.get_statistics() if hasattr(coord.gemini_client, 'get_statistics') else {}
        }
        
        return jsonify({
            'coordinator_statistics': coordinator_stats,
            'model_performance': model_performance,
            'success': True
        })
        
    except Exception as e:
        return jsonify({
            'error': f'获取统计信息时发生错误: {str(e)}',
            'success': False
        }), 500

@ai_assistant_bp.route('/models', methods=['GET'])
def get_available_models():
    """获取可用的AI模型信息"""
    try:
        models = {
            'claude': {
                'name': 'Claude 3.5 Sonnet',
                'description': '推理型 - 逻辑严密，代码质量高',
                'capabilities': ['code_generation', 'explanation', 'review', 'refactoring'],
                'max_tokens': 200000,
                'cost_level': 'medium',
                'speed_level': 'medium',
                'quality_level': 'high',
                'strengths': ['代码解释', '代码审查', '逻辑推理']
            },
            'gemini': {
                'name': 'Gemini 1.5 Pro',
                'description': '性能型 - 高性价比，88%创新分数',
                'capabilities': ['performance_optimization', 'rapid_prototyping', 'innovation'],
                'max_tokens': 128000,
                'cost_level': 'low',
                'speed_level': 'high',
                'quality_level': 'medium',
                'strengths': ['性能优化', '快速原型', '创新解决方案']
            }
        }
        
        return jsonify({
            'models': models,
            'success': True
        })
        
    except Exception as e:
        return jsonify({
            'error': f'获取模型信息时发生错误: {str(e)}',
            'success': False
        }), 500

@ai_assistant_bp.route('/task-types', methods=['GET'])
def get_task_types():
    """获取支持的任务类型"""
    try:
        task_types = {
            'code_generation': {
                'name': '代码生成',
                'description': '根据需求生成代码',
                'recommended_model': 'auto'
            },
            'code_explanation': {
                'name': '代码解释',
                'description': '解释代码功能和实现原理',
                'recommended_model': 'claude'
            },
            'code_debug': {
                'name': '代码调试',
                'description': '分析和修复代码问题',
                'recommended_model': 'claude'
            },
            'code_optimization': {
                'name': '性能优化',
                'description': '优化代码性能和效率',
                'recommended_model': 'gemini'
            },
            'code_refactoring': {
                'name': '代码重构',
                'description': '改进代码结构和可读性',
                'recommended_model': 'claude'
            },
            'code_review': {
                'name': '代码审查',
                'description': '全面的代码质量评估',
                'recommended_model': 'claude'
            },
            'test_generation': {
                'name': '测试生成',
                'description': '生成单元测试和测试用例',
                'recommended_model': 'auto'
            },
            'architecture_design': {
                'name': '架构设计',
                'description': '设计系统架构和模块结构',
                'recommended_model': 'gemini'
            },
            'performance_analysis': {
                'name': '性能分析',
                'description': '分析性能瓶颈和优化建议',
                'recommended_model': 'gemini'
            },
            'innovation_solution': {
                'name': '创新方案',
                'description': '提供创新的解决方案',
                'recommended_model': 'gemini'
            }
        }
        
        return jsonify({
            'task_types': task_types,
            'success': True
        })
        
    except Exception as e:
        return jsonify({
            'error': f'获取任务类型时发生错误: {str(e)}',
            'success': False
        }), 500

@ai_assistant_bp.route('/strategies', methods=['GET'])
def get_selection_strategies():
    """获取可用的选择策略"""
    try:
        strategies = {
            'auto_select': {
                'name': '智能选择',
                'description': '自动选择最适合的模型'
            },
            'quality_first': {
                'name': '质量优先',
                'description': '优先选择高质量输出'
            },
            'cost_efficient': {
                'name': '成本优先',
                'description': '优先选择成本效益'
            },
            'speed_first': {
                'name': '速度优先',
                'description': '优先选择快速响应'
            },
            'innovation_focus': {
                'name': '创新优先',
                'description': '优先选择创新方案'
            },
            'balanced': {
                'name': '平衡策略',
                'description': '平衡质量、成本和速度'
            }
        }
        
        return jsonify({
            'strategies': strategies,
            'success': True
        })
        
    except Exception as e:
        return jsonify({
            'error': f'获取选择策略时发生错误: {str(e)}',
            'success': False
        }), 500

@ai_assistant_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    try:
        coord = init_coordinator()
        
        # 检查模型可用性
        claude_available = hasattr(coord, 'claude_client') and coord.claude_client is not None
        gemini_available = hasattr(coord, 'gemini_client') and coord.gemini_client is not None
        
        return jsonify({
            'status': 'healthy',
            'models': {
                'claude': 'available' if claude_available else 'unavailable',
                'gemini': 'available' if gemini_available else 'unavailable'
            },
            'coordinator': 'initialized' if coord else 'not_initialized',
            'success': True
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'success': False
        }), 500

