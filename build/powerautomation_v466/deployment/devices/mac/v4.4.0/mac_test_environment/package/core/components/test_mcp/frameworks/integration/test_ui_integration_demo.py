#!/usr/bin/env python3
"""
UI测试集成演示脚本

演示如何使用Stagewise框架运行test/目录下的UI测试用例
"""

import asyncio
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from test.ui_test_registry import get_ui_test_registry
from core.components.stagewise_mcp.ui_test_integration import StagewiseUITestRunner

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demo_ui_test_integration():
    """演示UI测试集成功能"""
    print("🚀 UI测试集成演示开始")
    print("=" * 60)
    
    try:
        # 1. 创建UI测试运行器
        print("\n📋 步骤1: 初始化UI测试运行器")
        runner = StagewiseUITestRunner()
        
        # 2. 初始化并发现测试
        print("\n🔍 步骤2: 发现和注册UI测试")
        if await runner.initialize():
            print("✅ UI测试运行器初始化成功")
        else:
            print("❌ UI测试运行器初始化失败")
            return
        
        # 3. 获取测试摘要
        print("\n📊 步骤3: 获取测试摘要")
        summary = runner.get_test_summary()
        print(f"  总测试用例: {summary.get('total_tests', 0)}")
        print(f"  总测试套件: {summary.get('total_suites', 0)}")
        print(f"  优先级分布: {summary.get('priority_distribution', {})}")
        print(f"  分类分布: {summary.get('category_distribution', {})}")
        print(f"  组件分布: {summary.get('component_distribution', {})}")
        
        # 4. 列出可用的测试套件
        print("\n📋 步骤4: 可用的测试套件")
        test_suites = summary.get('test_suites', {})
        for suite_id, suite_info in test_suites.items():
            print(f"  - {suite_id}: {suite_info['name']} ({suite_info['test_count']} 个测试)")
        
        # 5. 运行一个基础UI操作测试用例
        print("\n🧪 步骤5: 运行单个UI测试用例")
        try:
            result = await runner.ui_integration.run_ui_test_case("ui_test_001")
            print(f"  测试结果: {result.status.value}")
            print(f"  执行时间: {result.duration:.2f}秒")
            if result.output:
                print(f"  输出: {result.output}")
        except Exception as e:
            print(f"  ❌ 运行测试用例失败: {str(e)}")
        
        # 6. 运行基础UI操作测试套件
        print("\n📦 步骤6: 运行UI测试套件")
        try:
            session = await runner.ui_integration.run_ui_test_suite("basic_ui_operations")
            print(f"  测试套件结果: {session.passed_tests}/{session.total_tests} 通过")
            print(f"  总执行时间: {session.duration:.2f}秒")
            print(f"  成功率: {session.success_rate:.1%}")
        except Exception as e:
            print(f"  ❌ 运行测试套件失败: {str(e)}")
        
        # 7. 生成测试报告
        print("\n📄 步骤7: 生成测试报告")
        if runner.framework.current_session:
            report = runner.generate_test_report(runner.framework.current_session)
            print("  测试报告已生成")
            print(f"  报告长度: {len(report)} 字符")
        else:
            print("  没有可用的测试会话数据")
        
        print("\n✅ UI测试集成演示完成")
        
    except Exception as e:
        logger.error(f"演示过程中发生错误: {str(e)}")
        print(f"\n❌ 演示失败: {str(e)}")


async def demo_ui_test_registry():
    """演示UI测试注册器功能"""
    print("\n🔧 UI测试注册器演示")
    print("-" * 40)
    
    try:
        # 获取UI测试注册器
        registry = get_ui_test_registry()
        
        # 发现和注册测试
        result = registry.discover_and_register_tests()
        print(f"✅ 注册了 {result['total_tests']} 个测试用例")
        print(f"📁 测试模块: {', '.join(result['modules'])}")
        print(f"📋 测试套件: {', '.join(result['suites'])}")
        
        # 获取已注册的测试
        tests = registry.get_registered_tests()
        suites = registry.get_test_suites()
        
        print(f"\n📊 统计信息:")
        print(f"  注册的测试用例: {len(tests)}")
        print(f"  注册的测试套件: {len(suites)}")
        
        # 按优先级分组显示测试用例
        p0_tests = [t for t in tests.values() if t.priority.value == "P0"]
        p1_tests = [t for t in tests.values() if t.priority.value == "P1"]
        
        print(f"\n🔥 P0优先级测试 ({len(p0_tests)} 个):")
        for test in p0_tests:
            print(f"  - {test.test_id}: {test.name}")
        
        print(f"\n⚡ P1优先级测试 ({len(p1_tests)} 个):")
        for test in p1_tests:
            print(f"  - {test.test_id}: {test.name}")
        
    except Exception as e:
        logger.error(f"UI测试注册器演示失败: {str(e)}")
        print(f"❌ 注册器演示失败: {str(e)}")


async def main():
    """主函数"""
    print("🎯 PowerAutomation 4.0 UI测试集成演示")
    print("=" * 80)
    
    # 演示UI测试注册器
    await demo_ui_test_registry()
    
    # 演示UI测试集成
    await demo_ui_test_integration()
    
    print("\n🎉 所有演示完成！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

