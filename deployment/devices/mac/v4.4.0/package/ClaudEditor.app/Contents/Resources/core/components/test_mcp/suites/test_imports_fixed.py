#!/usr/bin/env python3
"""
修正的导入测试脚本
使用相对路径和sys.path配置
"""

import sys
import os
import importlib
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

def test_core_imports():
    """测试核心模块导入"""
    print("🧪 测试核心模块导入...")
    
    core_modules = [
        'core.config',
        'core.event_bus', 
        'core.task_manager',
        'core.parallel_executor',
        'core.exceptions',
        'core.logging_config',
    ]
    
    success_count = 0
    for module in core_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
            success_count += 1
        except Exception as e:
            print(f"❌ {module}: {e}")
    
    return success_count, len(core_modules)

def test_agent_imports():
    """测试智能体模块导入"""
    print("\n🤖 测试智能体模块导入...")
    
    agent_modules = [
        'core.components.agents_mcp.agent_coordinator',
    ]
    
    success_count = 0
    for module in agent_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
            success_count += 1
        except Exception as e:
            print(f"❌ {module}: {e}")
    
    return success_count, len(agent_modules)

def test_mcp_imports():
    """测试MCP组件导入"""
    print("\n🔗 测试MCP组件导入...")
    
    mcp_modules = [
        'core.components.memoryos_mcp.memory_engine',
        'core.components.trae_agent_mcp.trae_agent_engine',
        'core.components.routing_mcp.intelligent_task_router',
        'core.components.mcp_coordinator_mcp.integration_layer',
    ]
    
    success_count = 0
    for module in mcp_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
            success_count += 1
        except Exception as e:
            print(f"❌ {module}: {e}")
    
    return success_count, len(mcp_modules)

def test_integration_imports():
    """测试集成组件导入"""
    print("\n🔧 测试集成组件导入...")
    
    integration_modules = []
    
    # 检查claude_sdk是否有可导入的模块
    claude_sdk_path = Path('core/integrations/claude_sdk')
    if claude_sdk_path.exists():
        for py_file in claude_sdk_path.glob('*.py'):
            if py_file.name != '__init__.py':
                module_name = f'core.integrations.claude_sdk.{py_file.stem}'
                integration_modules.append(module_name)
    
    # 检查command模块
    command_path = Path('core/command')
    if command_path.exists():
        for py_file in command_path.glob('*.py'):
            if py_file.name != '__init__.py':
                module_name = f'core.command.{py_file.stem}'
                integration_modules.append(module_name)
    
    success_count = 0
    for module in integration_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
            success_count += 1
        except Exception as e:
            print(f"❌ {module}: {e}")
    
    return success_count, len(integration_modules)

def test_file_structure():
    """测试文件结构完整性"""
    print("\n📁 测试文件结构完整性...")
    
    required_paths = [
        'core/__init__.py',
        'core/powerautomation_main.py',
        'core/agents/agent_coordinator.py',
        'core/components/memoryos_mcp/__init__.py',
        'core/components/trae_agent_mcp/__init__.py',
        'core/routing/intelligent_task_router.py',
    ]
    
    success_count = 0
    for path in required_paths:
        if Path(path).exists():
            print(f"✅ {path}")
            success_count += 1
        else:
            print(f"❌ {path}")
    
    return success_count, len(required_paths)

def main():
    """主测试函数"""
    print("🚀 PowerAutomation Core 修正导入测试\n")
    print(f"📍 当前工作目录: {os.getcwd()}")
    print(f"🐍 Python路径: {sys.path[:3]}...\n")
    
    # 运行所有测试
    tests = [
        ("文件结构测试", test_file_structure),
        ("核心模块导入", test_core_imports),
        ("智能体模块导入", test_agent_imports),
        ("MCP组件导入", test_mcp_imports),
        ("集成组件导入", test_integration_imports),
    ]
    
    total_success = 0
    total_modules = 0
    
    for test_name, test_func in tests:
        try:
            success, total = test_func()
            total_success += success
            total_modules += total
            print(f"   {test_name}: {success}/{total} 成功")
        except Exception as e:
            print(f"❌ {test_name} 执行失败: {e}")
    
    # 总结
    print("\n" + "="*50)
    print("📊 导入测试总结")
    print("="*50)
    print(f"🎯 总体成功率: {total_success}/{total_modules} ({total_success/total_modules*100:.1f}%)")
    
    if total_success >= total_modules * 0.8:  # 80%成功率认为通过
        print("🎉 导入测试基本通过！")
        return True
    else:
        print("⚠️ 导入测试需要进一步修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

