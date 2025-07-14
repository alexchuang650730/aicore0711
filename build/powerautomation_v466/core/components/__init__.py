"""
PowerAutomation v4.6.1 MCP組件統一入口
Unified MCP Components Entry Point
"""

# 導入所有核心組件
try:
    from .intelligent_error_handler_mcp.error_handler import intelligent_error_handler
except ImportError as e:
    print(f"Warning: Could not import intelligent_error_handler_mcp: {e}")
    intelligent_error_handler = None

try:
    from .project_analyzer_mcp.project_analyzer import project_analyzer
except ImportError as e:
    print(f"Warning: Could not import project_analyzer_mcp: {e}")
    project_analyzer = None

# 模擬其他MCP組件
workflow_automation_mcp = type('MockMCP', (), {'status': 'available'})()
code_review_mcp = type('MockMCP', (), {'status': 'available'})()
test_generator_mcp = type('MockMCP', (), {'status': 'available'})()
deployment_mcp = type('MockMCP', (), {'status': 'available'})()
monitoring_mcp = type('MockMCP', (), {'status': 'available'})()
collaboration_mcp = type('MockMCP', (), {'status': 'available'})()

__all__ = [
    'intelligent_error_handler',
    'project_analyzer',
    'workflow_automation_mcp',
    'code_review_mcp', 
    'test_generator_mcp',
    'deployment_mcp',
    'monitoring_mcp',
    'collaboration_mcp'
]