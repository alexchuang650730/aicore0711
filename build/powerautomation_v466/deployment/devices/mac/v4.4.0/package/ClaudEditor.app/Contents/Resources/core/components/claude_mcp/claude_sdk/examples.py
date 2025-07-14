#!/usr/bin/env python3
"""
ClaudeSDKMCP 快速启动示例
演示基本功能使用方法
"""

import asyncio
import json
import os
from claude_sdk_mcp_v2 import ClaudeSDKMCP

async def demo_basic_usage():
    """演示基本使用方法"""
    print("🚀 ClaudeSDKMCP v2.0.0 快速启动演示")
    print("=" * 50)
    
    # 初始化 ClaudeSDKMCP
    print("📝 初始化 ClaudeSDKMCP...")
    claude_sdk = ClaudeSDKMCP()
    await claude_sdk.initialize()
    
    try:
        # 示例1: 代码分析
        print("\n📊 示例1: 代码分析")
        print("-" * 30)
        
        code_analysis_result = await claude_sdk.process_request(
            "请分析这段Python代码的性能问题和改进建议",
            {
                "code": """
def find_duplicates(data):
    duplicates = []
    for i in range(len(data)):
        for j in range(i + 1, len(data)):
            if data[i] == data[j] and data[i] not in duplicates:
                duplicates.append(data[i])
    return duplicates
""",
                "language": "python",
                "file_name": "example.py"
            }
        )
        
        print(f"✅ 分析成功: {code_analysis_result.success}")
        print(f"🧠 使用专家: {code_analysis_result.expert_used}")
        print(f"⚙️ 执行操作: {', '.join(code_analysis_result.operations_executed)}")
        print(f"⏱️ 处理时间: {code_analysis_result.processing_time:.2f}s")
        print(f"📋 分析报告:\n{code_analysis_result.result_content[:500]}...")
        
        # 示例2: 架构设计咨询
        print("\n🏗️ 示例2: 架构设计咨询")
        print("-" * 30)
        
        architecture_result = await claude_sdk.process_request(
            "我正在设计一个电商系统，需要支持高并发和微服务架构，请给出设计建议",
            {
                "system_type": "e-commerce",
                "requirements": ["high_concurrency", "microservices", "scalability"],
                "expected_users": 100000
            }
        )
        
        print(f"✅ 咨询成功: {architecture_result.success}")
        print(f"🧠 使用专家: {architecture_result.expert_used}")
        print(f"⚙️ 执行操作: {', '.join(architecture_result.operations_executed)}")
        print(f"📋 设计建议:\n{architecture_result.result_content[:500]}...")
        
        # 示例3: API设计审查
        print("\n🔌 示例3: API设计审查")
        print("-" * 30)
        
        api_result = await claude_sdk.process_request(
            "请审查这个REST API设计是否符合最佳实践",
            {
                "api_spec": {
                    "endpoints": [
                        "GET /users",
                        "POST /users",
                        "GET /users/{id}",
                        "PUT /users/{id}",
                        "DELETE /users/{id}"
                    ],
                    "authentication": "JWT",
                    "response_format": "JSON"
                },
                "api_type": "REST"
            }
        )
        
        print(f"✅ 审查成功: {api_result.success}")
        print(f"🧠 使用专家: {api_result.expert_used}")
        print(f"⚙️ 执行操作: {', '.join(api_result.operations_executed)}")
        print(f"📋 审查结果:\n{api_result.result_content[:500]}...")
        
        # 示例4: 安全分析
        print("\n🔒 示例4: 安全分析")
        print("-" * 30)
        
        security_result = await claude_sdk.process_request(
            "请分析这个登录系统的安全性",
            {
                "code": """
def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    result = db.execute(query)
    return result.fetchone() is not None
""",
                "language": "python",
                "security_focus": ["sql_injection", "password_security"]
            }
        )
        
        print(f"✅ 分析成功: {security_result.success}")
        print(f"🧠 使用专家: {security_result.expert_used}")
        print(f"⚙️ 执行操作: {', '.join(security_result.operations_executed)}")
        print(f"📋 安全报告:\n{security_result.result_content[:500]}...")
        
        # 示例5: 数据库优化
        print("\n🗄️ 示例5: 数据库优化")
        print("-" * 30)
        
        db_result = await claude_sdk.process_request(
            "请优化这个SQL查询的性能",
            {
                "sql": """
SELECT u.name, p.title, c.name as category
FROM users u
JOIN posts p ON u.id = p.user_id
JOIN categories c ON p.category_id = c.id
WHERE u.created_at > '2023-01-01'
ORDER BY p.created_at DESC
""",
                "database": "postgresql",
                "table_sizes": {"users": 1000000, "posts": 5000000, "categories": 100}
            }
        )
        
        print(f"✅ 优化成功: {db_result.success}")
        print(f"🧠 使用专家: {db_result.expert_used}")
        print(f"⚙️ 执行操作: {', '.join(db_result.operations_executed)}")
        print(f"📋 优化建议:\n{db_result.result_content[:500]}...")
        
        # 获取系统统计
        print("\n📊 系统统计信息")
        print("-" * 30)
        
        stats = claude_sdk.get_stats()
        print(f"📈 总请求数: {stats['system_stats']['total_requests']}")
        print(f"✅ 成功请求数: {stats['system_stats']['successful_requests']}")
        print(f"⏱️ 平均处理时间: {stats['system_stats']['average_processing_time']:.2f}s")
        print(f"🧠 专家数量: {stats['expert_count']}")
        print(f"⚙️ 操作数量: {stats['operation_count']}")
        
        # 专家使用情况
        print("\n👥 专家使用情况:")
        for expert, count in stats['system_stats']['expert_usage'].items():
            print(f"  - {expert}: {count}次")
        
        # 操作使用情况
        print("\n⚙️ 操作使用情况:")
        for operation, count in list(stats['system_stats']['operation_usage'].items())[:5]:
            print(f"  - {operation}: {count}次")
        
    finally:
        await claude_sdk.close()
        print("\n🔚 演示完成")


async def demo_expert_system():
    """演示专家系统功能"""
    print("\n👥 专家系统演示")
    print("=" * 50)
    
    claude_sdk = ClaudeSDKMCP()
    await claude_sdk.initialize()
    
    try:
        # 获取所有专家
        experts = claude_sdk.get_all_experts()
        print(f"📋 系统中共有 {len(experts)} 位专家:")
        
        for expert in experts:
            print(f"\n🧠 {expert.name}")
            print(f"   领域: {expert.domain}")
            print(f"   专长: {', '.join(expert.specialties)}")
            print(f"   成功率: {expert.success_rate:.1%}")
            print(f"   处理请求: {expert.total_requests}次")
            if expert.last_used:
                print(f"   最后使用: {expert.last_used.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 获取专家推荐
        print(f"\n🎯 场景专家推荐:")
        scenarios = ["code_analysis", "architecture_design", "performance_optimization", 
                    "api_design", "security_analysis", "database_design"]
        
        for scenario in scenarios:
            recommended_experts = await claude_sdk.get_expert_recommendation(scenario)
            if recommended_experts:
                expert = recommended_experts[0]
                print(f"  - {scenario}: {expert.name}")
    
    finally:
        await claude_sdk.close()


async def demo_operations():
    """演示操作系统功能"""
    print("\n⚙️ 操作系统演示")
    print("=" * 50)
    
    claude_sdk = ClaudeSDKMCP()
    await claude_sdk.initialize()
    
    try:
        # 获取所有操作
        operations = claude_sdk.get_all_operations()
        print(f"📋 系统中共有 {len(operations)} 个操作处理器:")
        
        # 按类别分组显示
        categories = {}
        for op in operations:
            if op.category not in categories:
                categories[op.category] = []
            categories[op.category].append(op)
        
        for category, ops in categories.items():
            print(f"\n📂 {category.upper()} ({len(ops)}个操作):")
            for op in ops:
                print(f"  - {op.name}: {op.description}")
                if op.execution_count > 0:
                    success_rate = op.success_count / op.execution_count
                    print(f"    执行次数: {op.execution_count}, 成功率: {success_rate:.1%}")
    
    finally:
        await claude_sdk.close()


async def demo_interactive_mode():
    """演示交互模式"""
    print("\n💬 交互模式演示")
    print("=" * 50)
    print("输入 'quit' 退出交互模式")
    
    claude_sdk = ClaudeSDKMCP()
    await claude_sdk.initialize()
    
    try:
        while True:
            user_input = input("\n🤔 请输入您的问题: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                break
            
            if not user_input:
                continue
            
            print("🔄 正在分析...")
            
            result = await claude_sdk.process_request(user_input)
            
            print(f"\n✅ 分析完成!")
            print(f"🧠 专家: {result.expert_used}")
            print(f"⚙️ 操作: {', '.join(result.operations_executed)}")
            print(f"⏱️ 耗时: {result.processing_time:.2f}s")
            print(f"\n📋 分析结果:")
            print("-" * 40)
            print(result.result_content)
            print("-" * 40)
    
    finally:
        await claude_sdk.close()
        print("\n👋 再见!")


async def demo_performance_test():
    """演示性能测试"""
    print("\n⚡ 性能测试演示")
    print("=" * 50)
    
    claude_sdk = ClaudeSDKMCP()
    await claude_sdk.initialize()
    
    try:
        import time
        
        # 并发测试
        print("🚀 并发处理测试...")
        
        test_requests = [
            ("分析这段代码的复杂度", {"code": "def test(): pass", "language": "python"}),
            ("设计一个用户管理系统", {"system_type": "user_management"}),
            ("优化数据库查询性能", {"sql": "SELECT * FROM users", "database": "mysql"}),
            ("审查API安全性", {"api_type": "REST"}),
            ("分析系统架构", {"architecture": "microservices"})
        ]
        
        start_time = time.time()
        
        # 并发执行
        tasks = [
            claude_sdk.process_request(request, context) 
            for request, context in test_requests
        ]
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"📊 并发测试结果:")
        print(f"  - 总请求数: {len(test_requests)}")
        print(f"  - 总耗时: {total_time:.2f}s")
        print(f"  - 平均耗时: {total_time/len(test_requests):.2f}s/请求")
        print(f"  - 吞吐量: {len(test_requests)/total_time:.2f}请求/s")
        
        success_count = sum(1 for result in results if result.success)
        print(f"  - 成功率: {success_count/len(results):.1%}")
        
        # 显示每个请求的结果
        for i, (result, (request, _)) in enumerate(zip(results, test_requests)):
            status = "✅" if result.success else "❌"
            print(f"  {status} 请求{i+1}: {request[:30]}... ({result.processing_time:.2f}s)")
    
    finally:
        await claude_sdk.close()


def main():
    """主函数"""
    print("🎉 ClaudeSDKMCP v2.0.0 示例程序")
    print("=" * 60)
    
    demos = {
        "1": ("基本功能演示", demo_basic_usage),
        "2": ("专家系统演示", demo_expert_system),
        "3": ("操作系统演示", demo_operations),
        "4": ("交互模式演示", demo_interactive_mode),
        "5": ("性能测试演示", demo_performance_test),
        "0": ("运行所有演示", None)
    }
    
    print("\n请选择演示模式:")
    for key, (name, _) in demos.items():
        print(f"  {key}. {name}")
    
    choice = input("\n请输入选择 (0-5): ").strip()
    
    if choice == "0":
        # 运行所有演示
        async def run_all():
            for key, (name, demo_func) in demos.items():
                if demo_func:
                    print(f"\n{'='*60}")
                    print(f"🎬 开始 {name}")
                    print(f"{'='*60}")
                    await demo_func()
                    print(f"\n✅ {name} 完成")
        
        asyncio.run(run_all())
    
    elif choice in demos and demos[choice][1]:
        asyncio.run(demos[choice][1]())
    
    else:
        print("❌ 无效选择")


if __name__ == "__main__":
    main()

