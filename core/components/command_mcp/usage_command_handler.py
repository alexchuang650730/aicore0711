#!/usr/bin/env python3
"""
使用统计指令处理器
为Command MCP添加/usage指令支持
"""

import sys
import os
from typing import Dict, List, Any

# 导入Mirror Code使用追踪器
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'mirror_code_tracker'))
from usage_tracker import get_current_usage_summary, generate_usage_report, usage_tracker

class UsageCommandHandler:
    """使用统计指令处理器"""
    
    async def handle_usage_command(self, args: List[str]) -> Dict[str, Any]:
        """处理/usage指令"""
        
        if not args:
            # 显示基本使用摘要
            summary = get_current_usage_summary()
            return {
                "type": "usage_summary",
                "title": "🔄 Mirror Code 使用摘要",
                "data": summary,
                "formatted_output": self._format_usage_summary(summary)
            }
        
        subcommand = args[0].lower()
        
        if subcommand == "report":
            # 生成详细报告
            report = generate_usage_report()
            return {
                "type": "usage_report",
                "title": "📊 详细使用报告",
                "report": report
            }
        
        elif subcommand == "recent":
            # 显示最近活动
            limit = int(args[1]) if len(args) > 1 and args[1].isdigit() else 10
            recent_activity = usage_tracker.get_recent_activity(limit)
            return {
                "type": "recent_activity",
                "title": f"📝 最近 {limit} 条活动",
                "data": recent_activity,
                "formatted_output": self._format_recent_activity(recent_activity)
            }
        
        elif subcommand == "switch":
            # 显示模型切换分析
            switch_analysis = usage_tracker.get_model_switch_analysis()
            return {
                "type": "switch_analysis",
                "title": "🔄 模型切换分析",
                "data": switch_analysis,
                "formatted_output": self._format_switch_analysis(switch_analysis)
            }
        
        elif subcommand == "cost":
            # 显示成本分析
            summary = get_current_usage_summary()
            cost_analysis = summary.get("cost_analysis", {})
            return {
                "type": "cost_analysis",
                "title": "💰 成本分析",
                "data": cost_analysis,
                "formatted_output": self._format_cost_analysis(cost_analysis)
            }
        
        elif subcommand == "help":
            # 显示usage指令帮助
            return {
                "type": "usage_help",
                "title": "📖 /usage 指令帮助",
                "formatted_output": self._get_usage_help()
            }
        
        else:
            return {
                "error": f"未知的usage子指令: {subcommand}",
                "suggestion": "使用 /usage help 查看所有可用选项"
            }
    
    def _format_usage_summary(self, summary: Dict[str, Any]) -> str:
        """格式化使用摘要"""
        if "message" in summary:
            return summary["message"]
        
        model_dist = summary.get("model_distribution", {})
        cost_analysis = summary.get("cost_analysis", {})
        performance = summary.get("performance", {})
        
        return f"""
🔄 **当前会话使用摘要**

⏱️ **会话信息**
• 会话时长: {summary.get('session_duration', 'N/A')}
• 总指令数: {summary.get('total_commands', 0)}
• 平均响应时间: {performance.get('average_response_time_ms', 0)}ms

🤖 **模型使用分布**
• K2 本地: {model_dist.get('k2_local', {}).get('count', 0)} 次 ({model_dist.get('k2_local', {}).get('percentage', 0)}%)
• Claude Mirror: {model_dist.get('claude_mirror', {}).get('count', 0)} 次 ({model_dist.get('claude_mirror', {}).get('percentage', 0)}%)
• Claude 直接: {model_dist.get('claude_direct', {}).get('count', 0)} 次 ({model_dist.get('claude_direct', {}).get('percentage', 0)}%)

💰 **成本效益**
• 实际成本: ${cost_analysis.get('actual_cost_usd', 0)}
• 节省成本: ${cost_analysis.get('cost_savings_usd', 0)} ({cost_analysis.get('savings_percentage', 0)}%)

⚡ **效率指标**
• {performance.get('k2_efficiency', 'K2本地处理率未知')}

💡 **提示**: 使用 /usage help 查看更多选项
"""
    
    def _format_recent_activity(self, activities: List[Dict[str, Any]]) -> str:
        """格式化最近活动"""
        if not activities:
            return "📝 暂无活动记录"
        
        output = "📝 **最近活动记录**\n\n"
        
        for activity in activities:
            timestamp = activity['timestamp'][-8:]  # 只显示时间部分
            model_icon = "🤖" if activity['provider'] == 'k2_local' else "🌐"
            cost_icon = "💚" if activity['cost_usd'] < 0.001 else "💰"
            
            output += f"• {timestamp} | {model_icon} {activity['command']} | {activity['model']} | {activity['tokens']} tokens | {cost_icon} ${activity['cost_usd']}\n"
        
        return output
    
    def _format_switch_analysis(self, analysis: Dict[str, Any]) -> str:
        """格式化切换分析"""
        if "message" in analysis:
            return analysis["message"]
        
        output = f"""
🔄 **模型切换分析**

📊 **切换统计**
• 总切换次数: {analysis.get('total_switches', 0)}
• 切换率: {analysis.get('switch_rate', 0)}%

🔀 **切换模式**
"""
        
        patterns = analysis.get('switch_patterns', {})
        for pattern, count in patterns.items():
            output += f"• {pattern}: {count} 次\n"
        
        recent_switches = analysis.get('recent_switches', [])
        if recent_switches:
            output += "\n📝 **最近切换**\n"
            for switch in recent_switches[-3:]:  # 只显示最近3次
                timestamp = switch['timestamp'][-8:]
                output += f"• {timestamp} | {switch['from']} → {switch['to']} | {switch['command']}\n"
        
        return output
    
    def _format_cost_analysis(self, cost_analysis: Dict[str, Any]) -> str:
        """格式化成本分析"""
        if not cost_analysis:
            return "💰 暂无成本数据"
        
        return f"""
💰 **成本分析详情**

💵 **实际支出**
• 当前会话成本: ${cost_analysis.get('actual_cost_usd', 0)}

🔮 **假设对比**
• 如全用Claude: ${cost_analysis.get('if_all_claude_cost_usd', 0)}

💚 **节省效果**
• 节省金额: ${cost_analysis.get('cost_savings_usd', 0)}
• 节省比例: {cost_analysis.get('savings_percentage', 0)}%

📈 **效率评估**
• K2本地处理越多，成本节省越大
• 建议优先使用K2支持的指令
"""
    
    def _get_usage_help(self) -> str:
        """获取usage指令帮助"""
        return """
📖 **/usage 指令帮助**

🔧 **基本用法**
• `/usage` - 显示基本使用摘要
• `/usage help` - 显示此帮助信息

📊 **详细分析**
• `/usage report` - 生成详细使用报告
• `/usage recent [数量]` - 显示最近活动 (默认10条)
• `/usage switch` - 显示模型切换分析
• `/usage cost` - 显示详细成本分析

💡 **使用示例**
• `/usage recent 5` - 显示最近5条活动
• `/usage switch` - 查看模型切换模式
• `/usage cost` - 查看成本节省情况

🎯 **功能说明**
此指令帮助您了解Mirror Code服务的使用情况，包括：
- K2本地处理 vs Claude代理的使用比例
- Token消耗和成本分析
- 响应时间和性能指标
- 模型切换模式分析

通过这些数据，您可以优化指令使用策略，最大化成本效益。
"""

# 创建全局处理器实例
usage_handler = UsageCommandHandler()

