#!/usr/bin/env python3
"""
ClaudeSDKMCP v2.0.0 CLI接口
提供命令行工具用于代码分析和专家咨询
"""

import asyncio
import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List
import time

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from claude_sdk_mcp_v2 import ClaudeSDKMCP


class ClaudeSDKMCPCLI:
    """Claude SDK MCP CLI控制器"""
    
    def __init__(self):
        self.claude_sdk = None
    
    async def initialize(self):
        """初始化CLI"""
        try:
            self.claude_sdk = ClaudeSDKMCP()
            await self.claude_sdk.initialize()
            return True
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            return False
    
    async def cleanup(self):
        """清理资源"""
        if self.claude_sdk:
            await self.claude_sdk.close()
    
    async def analyze_code(self, args):
        """分析代码"""
        print("🔍 开始代码分析...")
        
        context = {}
        
        # 处理代码输入
        if args.file:
            try:
                with open(args.file, 'r', encoding='utf-8') as f:
                    code = f.read()
                context['code'] = code
                context['file_name'] = os.path.basename(args.file)
                
                # 自动检测语言
                if not args.language:
                    ext = Path(args.file).suffix.lower()
                    language_map = {
                        '.py': 'python',
                        '.js': 'javascript',
                        '.ts': 'typescript',
                        '.java': 'java',
                        '.cpp': 'cpp',
                        '.c': 'c',
                        '.go': 'go',
                        '.rs': 'rust',
                        '.php': 'php',
                        '.rb': 'ruby'
                    }
                    args.language = language_map.get(ext, 'unknown')
                
            except FileNotFoundError:
                print(f"❌ 文件不存在: {args.file}")
                return
            except Exception as e:
                print(f"❌ 读取文件失败: {e}")
                return
        
        elif args.code:
            context['code'] = args.code
        
        else:
            print("❌ 请提供代码文件或代码片段")
            return
        
        # 设置语言
        if args.language:
            context['language'] = args.language
        
        # 构建分析请求
        if args.focus:
            request = f"请重点分析代码的{args.focus}方面"
        else:
            request = "请全面分析这段代码，包括语法、语义、性能、安全性等方面"
        
        # 执行分析
        try:
            result = await self.claude_sdk.process_request(request, context)
            
            # 显示结果
            self._display_result(result)
            
            # 保存结果
            if args.output:
                self._save_result(result, args.output)
                print(f"📁 结果已保存到: {args.output}")
        
        except Exception as e:
            print(f"❌ 分析失败: {e}")
    
    async def list_experts(self, args):
        """列出所有专家"""
        print("👥 系统专家列表")
        print("=" * 50)
        
        experts = self.claude_sdk.get_all_experts()
        
        for expert in experts:
            print(f"\n🧠 {expert.name}")
            print(f"   领域: {expert.domain}")
            print(f"   专长: {', '.join(expert.specialties)}")
            print(f"   成功率: {expert.success_rate:.1%}")
            print(f"   处理请求: {expert.total_requests}次")
            if expert.average_response_time > 0:
                print(f"   平均响应时间: {expert.average_response_time:.2f}s")
            if expert.last_used:
                print(f"   最后使用: {expert.last_used.strftime('%Y-%m-%d %H:%M:%S')}")
    
    async def recommend_experts(self, args):
        """推荐专家"""
        print(f"🎯 为场景 '{args.scenario}' 推荐专家")
        print("=" * 50)
        
        try:
            experts = await self.claude_sdk.get_expert_recommendation(
                args.scenario, 
                args.domains.split(',') if args.domains else None
            )
            
            if experts:
                for i, expert in enumerate(experts, 1):
                    print(f"\n{i}. 🧠 {expert.name}")
                    print(f"   领域: {expert.domain}")
                    print(f"   专长: {', '.join(expert.specialties)}")
                    print(f"   成功率: {expert.success_rate:.1%}")
            else:
                print("❌ 未找到合适的专家")
        
        except Exception as e:
            print(f"❌ 推荐失败: {e}")
    
    async def list_operations(self, args):
        """列出操作"""
        print("⚙️ 系统操作列表")
        print("=" * 50)
        
        if args.category:
            operations = self.claude_sdk.get_operations_by_category(args.category)
            print(f"\n📂 {args.category.upper()} 类别操作:")
        else:
            operations = self.claude_sdk.get_all_operations()
            print(f"\n📋 所有操作 (共{len(operations)}个):")
        
        # 按类别分组
        categories = {}
        for op in operations:
            if op.category not in categories:
                categories[op.category] = []
            categories[op.category].append(op)
        
        for category, ops in categories.items():
            if not args.category:
                print(f"\n📂 {category.upper()} ({len(ops)}个):")
            
            for op in ops:
                print(f"  - {op.name}: {op.description}")
                if op.execution_count > 0:
                    success_rate = op.success_count / op.execution_count
                    print(f"    执行: {op.execution_count}次, 成功率: {success_rate:.1%}, "
                          f"平均耗时: {op.average_execution_time:.2f}s")
    
    async def show_stats(self, args):
        """显示统计信息"""
        print("📊 系统统计信息")
        print("=" * 50)
        
        stats = self.claude_sdk.get_stats()
        
        # 系统统计
        sys_stats = stats['system_stats']
        print(f"\n📈 请求统计:")
        print(f"  - 总请求数: {sys_stats['total_requests']}")
        print(f"  - 成功请求: {sys_stats['successful_requests']}")
        print(f"  - 失败请求: {sys_stats['failed_requests']}")
        if sys_stats['total_requests'] > 0:
            success_rate = sys_stats['successful_requests'] / sys_stats['total_requests']
            print(f"  - 成功率: {success_rate:.1%}")
        print(f"  - 平均处理时间: {sys_stats['average_processing_time']:.2f}s")
        
        # Claude API统计
        api_stats = stats['claude_api_stats']
        print(f"\n🤖 Claude API统计:")
        print(f"  - API请求数: {api_stats['request_count']}")
        print(f"  - API错误数: {api_stats['error_count']}")
        print(f"  - API成功率: {api_stats['success_rate']:.1%}")
        
        # 系统信息
        print(f"\n🏗️ 系统信息:")
        print(f"  - 专家数量: {stats['expert_count']}")
        print(f"  - 操作数量: {stats['operation_count']}")
        print(f"  - 缓存大小: {stats['cache_size']}")
        print(f"  - 运行时间: {stats['uptime']:.0f}秒")
        
        # 专家使用情况
        if sys_stats['expert_usage']:
            print(f"\n👥 专家使用排行:")
            sorted_experts = sorted(sys_stats['expert_usage'].items(), 
                                  key=lambda x: x[1], reverse=True)
            for expert, count in sorted_experts[:5]:
                print(f"  - {expert}: {count}次")
        
        # 操作使用情况
        if sys_stats['operation_usage']:
            print(f"\n⚙️ 操作使用排行:")
            sorted_operations = sorted(sys_stats['operation_usage'].items(), 
                                     key=lambda x: x[1], reverse=True)
            for operation, count in sorted_operations[:5]:
                print(f"  - {operation}: {count}次")
        
        # 场景分布
        if sys_stats['scenario_distribution']:
            print(f"\n🎯 场景分布:")
            for scenario, count in sys_stats['scenario_distribution'].items():
                print(f"  - {scenario}: {count}次")
    
    async def interactive_mode(self, args):
        """交互模式"""
        print("💬 ClaudeSDKMCP 交互模式")
        print("=" * 50)
        print("输入 'help' 查看帮助，输入 'quit' 退出")
        
        while True:
            try:
                user_input = input("\n🤔 请输入您的问题: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("👋 再见!")
                    break
                
                if user_input.lower() == 'help':
                    self._show_interactive_help()
                    continue
                
                if user_input.lower() == 'stats':
                    await self.show_stats(None)
                    continue
                
                if user_input.lower() == 'experts':
                    await self.list_experts(None)
                    continue
                
                print("🔄 正在分析...")
                start_time = time.time()
                
                result = await self.claude_sdk.process_request(user_input)
                
                end_time = time.time()
                
                print(f"\n✅ 分析完成! (耗时: {end_time - start_time:.2f}s)")
                self._display_result(result, compact=True)
                
            except KeyboardInterrupt:
                print("\n👋 再见!")
                break
            except Exception as e:
                print(f"❌ 处理失败: {e}")
    
    def _show_interactive_help(self):
        """显示交互模式帮助"""
        print("\n📖 交互模式帮助:")
        print("  - 直接输入问题进行分析")
        print("  - 'help' - 显示此帮助")
        print("  - 'stats' - 显示统计信息")
        print("  - 'experts' - 显示专家列表")
        print("  - 'quit' 或 'exit' - 退出交互模式")
        print("\n💡 示例问题:")
        print("  - 分析这段代码的性能问题")
        print("  - 设计一个用户管理系统的架构")
        print("  - 如何优化数据库查询性能")
        print("  - 审查API的安全性")
    
    def _display_result(self, result, compact=False):
        """显示分析结果"""
        if result.success:
            print(f"\n✅ 分析成功!")
            print(f"🧠 使用专家: {result.expert_used}")
            print(f"⚙️ 执行操作: {', '.join(result.operations_executed)}")
            print(f"🎯 置信度: {result.confidence_score:.1%}")
            print(f"⏱️ 处理时间: {result.processing_time:.2f}s")
            
            if not compact:
                print(f"\n📋 分析报告:")
                print("-" * 60)
                print(result.result_content)
                print("-" * 60)
            else:
                # 紧凑模式，只显示前500字符
                content = result.result_content
                if len(content) > 500:
                    content = content[:500] + "..."
                print(f"\n📋 分析报告:\n{content}")
        else:
            print(f"\n❌ 分析失败!")
            if result.error_message:
                print(f"错误信息: {result.error_message}")
    
    def _save_result(self, result, output_file):
        """保存结果到文件"""
        try:
            result_data = {
                "success": result.success,
                "expert_used": result.expert_used,
                "operations_executed": result.operations_executed,
                "result_content": result.result_content,
                "confidence_score": result.confidence_score,
                "processing_time": result.processing_time,
                "metadata": result.metadata,
                "timestamp": time.time()
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            print(f"❌ 保存失败: {e}")


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="ClaudeSDKMCP v2.0.0 - AI代码分析和专家咨询工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 分析代码文件
  python cli.py analyze --file example.py
  
  # 分析代码片段
  python cli.py analyze --code "def hello(): print('world')" --language python
  
  # 获取专家推荐
  python cli.py experts recommend --scenario code_analysis
  
  # 列出所有专家
  python cli.py experts list
  
  # 列出操作
  python cli.py operations --category performance
  
  # 查看统计信息
  python cli.py stats
  
  # 进入交互模式
  python cli.py interactive
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # analyze 命令
    analyze_parser = subparsers.add_parser('analyze', help='分析代码')
    analyze_group = analyze_parser.add_mutually_exclusive_group(required=True)
    analyze_group.add_argument('--file', '-f', help='代码文件路径')
    analyze_group.add_argument('--code', '-c', help='代码片段')
    analyze_parser.add_argument('--language', '-l', help='编程语言')
    analyze_parser.add_argument('--focus', help='分析重点 (如: performance, security, architecture)')
    analyze_parser.add_argument('--output', '-o', help='输出文件路径')
    
    # experts 命令
    experts_parser = subparsers.add_parser('experts', help='专家管理')
    experts_subparsers = experts_parser.add_subparsers(dest='experts_command')
    
    # experts list
    experts_subparsers.add_parser('list', help='列出所有专家')
    
    # experts recommend
    recommend_parser = experts_subparsers.add_parser('recommend', help='推荐专家')
    recommend_parser.add_argument('--scenario', '-s', required=True,
                                help='场景类型 (code_analysis, architecture_design, etc.)')
    recommend_parser.add_argument('--domains', '-d', help='领域列表 (逗号分隔)')
    
    # operations 命令
    operations_parser = subparsers.add_parser('operations', help='操作管理')
    operations_parser.add_argument('--category', '-c', 
                                 help='操作类别 (code_analysis, architecture, performance, etc.)')
    
    # stats 命令
    subparsers.add_parser('stats', help='显示统计信息')
    
    # interactive 命令
    subparsers.add_parser('interactive', help='进入交互模式')
    
    return parser


async def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 初始化CLI
    cli = ClaudeSDKMCPCLI()
    
    if not await cli.initialize():
        return
    
    try:
        # 执行命令
        if args.command == 'analyze':
            await cli.analyze_code(args)
        
        elif args.command == 'experts':
            if args.experts_command == 'list':
                await cli.list_experts(args)
            elif args.experts_command == 'recommend':
                await cli.recommend_experts(args)
            else:
                parser.print_help()
        
        elif args.command == 'operations':
            await cli.list_operations(args)
        
        elif args.command == 'stats':
            await cli.show_stats(args)
        
        elif args.command == 'interactive':
            await cli.interactive_mode(args)
        
        else:
            parser.print_help()
    
    finally:
        await cli.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        print(f"❌ 程序错误: {e}")
        sys.exit(1)

