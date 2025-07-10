#!/usr/bin/env python3
"""
PowerAutomation Core 集成测试脚本
验证整合后的组件是否正常工作
"""

import sys
import importlib
import traceback
from pathlib import Path

def test_imports():
    """测试关键模块的导入"""
    print("🧪 开始导入测试...")
    
    modules_to_test = [
        # 核心模块
        'core.config',
        'core.event_bus',
        'core.task_manager',
        'core.parallel_executor',
        
        # 智能体系统
        'core.components.agents_mcp.agent_coordinator',
        
        # MCP组件
        'core.components.routing_mcp.smart_router',
        
        # 集成组件
        # 'core.tools.smart_engine',  # 已移除空目录
        
        # 新增组件
        'core.components.memoryos_mcp.memory_engine',
        'core.components.trae_agent_mcp.trae_agent_engine',
        'core.components.routing_mcp.intelligent_task_router',
    ]
    
    success_count = 0
    total_count = len(modules_to_test)
    
    for module in modules_to_test:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {module}: {e}")
        except Exception as e:
            print(f"⚠️ {module}: {e}")
    
    print(f"\n📊 导入测试结果:")
    print(f"   成功: {success_count}/{total_count}")
    print(f"   成功率: {success_count/total_count*100:.1f}%")
    
    return success_count == total_count

def test_directory_structure():
    """测试目录结构完整性"""
    print("\n🏗️ 测试目录结构...")
    
    required_dirs = [
        'core/agents/specialized',
        'core/agents/communication', 
        'core/agents/coordination',
        'core/mcp_coordinator/legacy',
        'core/routing/smart_router',
        'core/workflow',
        'core/integrations/claude_sdk',
        'core/command',
        'core/tools/smart_engine',
        'core/powerautomation_legacy',
        'core/components/memoryos_mcp',
        'core/components/trae_agent_mcp',
    ]
    
    success_count = 0
    total_count = len(required_dirs)
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path}")
            success_count += 1
        else:
            print(f"❌ {dir_path}")
    
    print(f"\n📊 目录结构测试结果:")
    print(f"   存在: {success_count}/{total_count}")
    print(f"   完整率: {success_count/total_count*100:.1f}%")
    
    return success_count == total_count

def test_key_files():
    """测试关键文件存在性"""
    print("\n📄 测试关键文件...")
    
    key_files = [
        'core/powerautomation_main.py',
        'core/components/memoryos_mcp/memory_engine.py',
        'core/components/trae_agent_mcp/trae_agent_engine.py',
    ]
    
    success_count = 0
    total_count = len(key_files)
    
    for file_path in key_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
            success_count += 1
        else:
            print(f"❌ {file_path}")
    
    print(f"\n📊 关键文件测试结果:")
    print(f"   存在: {success_count}/{total_count}")
    print(f"   完整率: {success_count/total_count*100:.1f}%")
    
    return success_count == total_count

def test_agent_components():
    """测试智能体组件"""
    print("\n🤖 测试智能体组件...")
    
    agent_dirs = [
        'core/agents/specialized/architect_agent',
        'core/agents/specialized/deploy_agent',
        'core/agents/specialized/developer_agent',
        'core/agents/specialized/monitor_agent',
        'core/agents/specialized/security_agent',
        'core/agents/specialized/test_agent',
    ]
    
    success_count = 0
    total_count = len(agent_dirs)
    
    for agent_dir in agent_dirs:
        if Path(agent_dir).exists():
            agent_file = Path(agent_dir) / f"{Path(agent_dir).name}.py"
            if agent_file.exists():
                print(f"✅ {agent_dir}")
                success_count += 1
            else:
                print(f"⚠️ {agent_dir} (目录存在但缺少主文件)")
        else:
            print(f"❌ {agent_dir}")
    
    print(f"\n📊 智能体组件测试结果:")
    print(f"   完整: {success_count}/{total_count}")
    print(f"   完整率: {success_count/total_count*100:.1f}%")
    
    return success_count == total_count

def main():
    """主测试函数"""
    print("🚀 PowerAutomation Core 集成测试开始\n")
    
    # 运行所有测试
    tests = [
        ("目录结构测试", test_directory_structure),
        ("关键文件测试", test_key_files),
        ("智能体组件测试", test_agent_components),
        ("导入测试", test_imports),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 执行失败: {e}")
            results.append((test_name, False))
    
    # 总结结果
    print("\n" + "="*50)
    print("📊 集成测试总结")
    print("="*50)
    
    passed_tests = 0
    total_tests = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} {test_name}")
        if result:
            passed_tests += 1
    
    print(f"\n🎯 总体结果: {passed_tests}/{total_tests} 测试通过")
    print(f"📈 成功率: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！核心架构整合成功！")
        return True
    else:
        print(f"\n⚠️ 还有 {total_tests - passed_tests} 个测试需要修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

