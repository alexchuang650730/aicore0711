#!/usr/bin/env python3
"""
导入路径更新脚本
自动更新所有Python文件中的PowerAutomation导入路径
"""

import os
import re
from pathlib import Path

def update_imports_in_file(file_path):
    """更新单个文件中的导入路径"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 更新导入路径映射
        import_mappings = {
            r'from PowerAutomation\.agent_squad': 'from core.components.agents_mcp',
            r'import PowerAutomation\.agent_squad': 'import core.components.agents_mcp',
            r'from PowerAutomation\.mcp_coordinator': 'from core.mcp_coordinator.legacy',
            r'import PowerAutomation\.mcp_coordinator': 'import core.mcp_coordinator.legacy',
            r'from PowerAutomation\.smart_router_mcp': 'from core.components.routing_mcp.smart_router',
            r'import PowerAutomation\.smart_router_mcp': 'import core.components.routing_mcp.smart_router',
            r'from PowerAutomation\.workflow_mcp': 'from core.workflow',
            r'import PowerAutomation\.workflow_mcp': 'import core.workflow',
            r'from PowerAutomation\.claude_sdk': 'from core.components.claude_integration_mcp.claude_sdk',
            r'import PowerAutomation\.claude_sdk': 'import core.integrations.claude_sdk',
            r'from PowerAutomation\.command_master': 'from core.components.command_mcp.command_master',
            r'import PowerAutomation\.command_master': 'import core.command',
            # r'from PowerAutomation\.simple_smart_tool_engine': 'from core.tools.smart_engine',  # 已移除
            # r'import PowerAutomation\.simple_smart_tool_engine': 'import core.tools.smart_engine',  # 已移除
            r'import PowerAutomation\.core': 'import core.powerautomation_legacy',
            r'from PowerAutomation': 'from core',
            r'import PowerAutomation': 'import core',
        }
        
        # 应用所有映射
        for old_pattern, new_path in import_mappings.items():
            content = re.sub(old_pattern, new_path, content)
        
        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 更新: {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ 错误处理 {file_path}: {e}")
        return False

def main():
    """主函数"""
    print("🔄 开始更新导入路径...")
    
    updated_files = 0
    total_files = 0
    
    # 遍历core目录下的所有Python文件
    for py_file in Path('core').rglob('*.py'):
        total_files += 1
        if update_imports_in_file(py_file):
            updated_files += 1
    
    print(f"\n📊 更新完成:")
    print(f"   总文件数: {total_files}")
    print(f"   更新文件数: {updated_files}")
    print(f"   成功率: {updated_files/total_files*100:.1f}%")

if __name__ == "__main__":
    main()
