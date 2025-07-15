#!/usr/bin/env python3
"""
Mirror Code 使用追踪器
实时追踪模型切换、Token消耗和成本分析
"""

import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    K2_LOCAL = "k2_local"
    CLAUDE_MIRROR = "claude_mirror"
    CLAUDE_DIRECT = "claude_direct"

@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    
    def add(self, other: 'TokenUsage'):
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.total_tokens += other.total_tokens

@dataclass
class ModelUsageRecord:
    timestamp: str
    command: str
    model_provider: ModelProvider
    model_name: str
    token_usage: TokenUsage
    response_time_ms: int
    cost_usd: float
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self):
        return {
            **asdict(self),
            'model_provider': self.model_provider.value,
            'token_usage': asdict(self.token_usage)
        }

class MirrorCodeUsageTracker:
    """Mirror Code 使用追踪器"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "/tmp/mirror_code_usage.json"
        self.session_records: List[ModelUsageRecord] = []
        self.session_stats = {
            "session_start": datetime.now().isoformat(),
            "total_commands": 0,
            "k2_local_count": 0,
            "claude_mirror_count": 0,
            "claude_direct_count": 0,
            "total_cost_usd": 0.0,
            "total_tokens": TokenUsage(),
            "average_response_time": 0.0
        }
        
        # 模型定价配置 (每1K tokens的价格，USD)
        self.pricing = {
            ModelProvider.K2_LOCAL: {
                "input_price_per_1k": 0.0001,  # K2本地成本很低
                "output_price_per_1k": 0.0002,
                "model_name": "Kimi-K2-Instruct"
            },
            ModelProvider.CLAUDE_MIRROR: {
                "input_price_per_1k": 0.003,   # Claude通过Mirror Code
                "output_price_per_1k": 0.015,
                "model_name": "Claude-3-Sonnet"
            },
            ModelProvider.CLAUDE_DIRECT: {
                "input_price_per_1k": 0.003,   # Claude直接调用
                "output_price_per_1k": 0.015,
                "model_name": "Claude-3-Sonnet"
            }
        }
    
    def calculate_cost(self, provider: ModelProvider, token_usage: TokenUsage) -> float:
        """计算Token使用成本"""
        pricing = self.pricing[provider]
        input_cost = (token_usage.input_tokens / 1000) * pricing["input_price_per_1k"]
        output_cost = (token_usage.output_tokens / 1000) * pricing["output_price_per_1k"]
        return input_cost + output_cost
    
    def record_usage(self, 
                    command: str,
                    model_provider: ModelProvider,
                    token_usage: TokenUsage,
                    response_time_ms: int,
                    success: bool = True,
                    error_message: Optional[str] = None) -> ModelUsageRecord:
        """记录模型使用情况"""
        
        cost = self.calculate_cost(model_provider, token_usage)
        model_name = self.pricing[model_provider]["model_name"]
        
        record = ModelUsageRecord(
            timestamp=datetime.now().isoformat(),
            command=command,
            model_provider=model_provider,
            model_name=model_name,
            token_usage=token_usage,
            response_time_ms=response_time_ms,
            cost_usd=cost,
            success=success,
            error_message=error_message
        )
        
        # 添加到会话记录
        self.session_records.append(record)
        
        # 更新会话统计
        self._update_session_stats(record)
        
        # 保存到文件
        self._save_usage_data()
        
        return record
    
    def _update_session_stats(self, record: ModelUsageRecord):
        """更新会话统计信息"""
        self.session_stats["total_commands"] += 1
        self.session_stats["total_cost_usd"] += record.cost_usd
        self.session_stats["total_tokens"].add(record.token_usage)
        
        # 更新模型使用计数
        if record.model_provider == ModelProvider.K2_LOCAL:
            self.session_stats["k2_local_count"] += 1
        elif record.model_provider == ModelProvider.CLAUDE_MIRROR:
            self.session_stats["claude_mirror_count"] += 1
        elif record.model_provider == ModelProvider.CLAUDE_DIRECT:
            self.session_stats["claude_direct_count"] += 1
        
        # 更新平均响应时间
        total_time = sum(r.response_time_ms for r in self.session_records)
        self.session_stats["average_response_time"] = total_time / len(self.session_records)
    
    def _save_usage_data(self):
        """保存使用数据到文件"""
        try:
            # 修复TokenUsage序列化问题
            session_stats_serializable = {
                **self.session_stats,
                "total_tokens": asdict(self.session_stats["total_tokens"])
            }
            
            data = {
                "session_stats": session_stats_serializable,
                "records": [record.to_dict() for record in self.session_records[-100:]]  # 只保存最近100条
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存使用数据失败: {e}")
    
    def get_current_session_summary(self) -> Dict[str, Any]:
        """获取当前会话摘要"""
        total_commands = self.session_stats["total_commands"]
        if total_commands == 0:
            return {"message": "本会话暂无指令执行记录"}
        
        k2_percentage = (self.session_stats["k2_local_count"] / total_commands) * 100
        claude_percentage = ((self.session_stats["claude_mirror_count"] + 
                            self.session_stats["claude_direct_count"]) / total_commands) * 100
        
        # 计算节省的成本（如果全部使用Claude的话）
        total_tokens = self.session_stats["total_tokens"]
        if_all_claude_cost = self.calculate_cost(ModelProvider.CLAUDE_DIRECT, total_tokens)
        actual_cost = self.session_stats["total_cost_usd"]
        cost_savings = if_all_claude_cost - actual_cost
        savings_percentage = (cost_savings / if_all_claude_cost * 100) if if_all_claude_cost > 0 else 0
        
        return {
            "session_duration": self._get_session_duration(),
            "total_commands": total_commands,
            "model_distribution": {
                "k2_local": {
                    "count": self.session_stats["k2_local_count"],
                    "percentage": round(k2_percentage, 1)
                },
                "claude_mirror": {
                    "count": self.session_stats["claude_mirror_count"],
                    "percentage": round((self.session_stats["claude_mirror_count"] / total_commands) * 100, 1)
                },
                "claude_direct": {
                    "count": self.session_stats["claude_direct_count"],
                    "percentage": round((self.session_stats["claude_direct_count"] / total_commands) * 100, 1)
                }
            },
            "token_usage": {
                "total_tokens": total_tokens.total_tokens,
                "input_tokens": total_tokens.input_tokens,
                "output_tokens": total_tokens.output_tokens
            },
            "cost_analysis": {
                "actual_cost_usd": round(actual_cost, 4),
                "if_all_claude_cost_usd": round(if_all_claude_cost, 4),
                "cost_savings_usd": round(cost_savings, 4),
                "savings_percentage": round(savings_percentage, 1)
            },
            "performance": {
                "average_response_time_ms": round(self.session_stats["average_response_time"], 1),
                "k2_efficiency": f"{round(k2_percentage, 1)}% 指令由K2本地处理"
            }
        }
    
    def _get_session_duration(self) -> str:
        """获取会话持续时间"""
        start_time = datetime.fromisoformat(self.session_stats["session_start"])
        duration = datetime.now() - start_time
        
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        seconds = duration.seconds % 60
        
        if hours > 0:
            return f"{hours}小时{minutes}分钟"
        elif minutes > 0:
            return f"{minutes}分钟{seconds}秒"
        else:
            return f"{seconds}秒"
    
    def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的活动记录"""
        recent_records = self.session_records[-limit:] if self.session_records else []
        
        return [{
            "timestamp": record.timestamp,
            "command": record.command,
            "model": record.model_name,
            "provider": record.model_provider.value,
            "tokens": record.token_usage.total_tokens,
            "cost_usd": round(record.cost_usd, 4),
            "response_time_ms": record.response_time_ms,
            "success": record.success
        } for record in recent_records]
    
    def get_model_switch_analysis(self) -> Dict[str, Any]:
        """分析模型切换模式"""
        if not self.session_records:
            return {"message": "暂无数据"}
        
        # 分析切换模式
        switches = []
        for i in range(1, len(self.session_records)):
            prev_provider = self.session_records[i-1].model_provider
            curr_provider = self.session_records[i].model_provider
            
            if prev_provider != curr_provider:
                switches.append({
                    "from": prev_provider.value,
                    "to": curr_provider.value,
                    "timestamp": self.session_records[i].timestamp,
                    "command": self.session_records[i].command
                })
        
        # 统计切换频率
        switch_patterns = {}
        for switch in switches:
            pattern = f"{switch['from']} → {switch['to']}"
            switch_patterns[pattern] = switch_patterns.get(pattern, 0) + 1
        
        return {
            "total_switches": len(switches),
            "switch_patterns": switch_patterns,
            "recent_switches": switches[-5:] if switches else [],
            "switch_rate": round(len(switches) / len(self.session_records) * 100, 1) if self.session_records else 0
        }
    
    def generate_usage_report(self) -> str:
        """生成使用报告"""
        summary = self.get_current_session_summary()
        recent_activity = self.get_recent_activity(5)
        switch_analysis = self.get_model_switch_analysis()
        
        report = f"""
🔄 **Mirror Code 使用报告**

📊 **会话概览**
• 会话时长: {summary.get('session_duration', 'N/A')}
• 总指令数: {summary.get('total_commands', 0)}
• 平均响应时间: {summary.get('performance', {}).get('average_response_time_ms', 0)}ms

🤖 **模型使用分布**
• K2 本地处理: {summary.get('model_distribution', {}).get('k2_local', {}).get('count', 0)} 次 ({summary.get('model_distribution', {}).get('k2_local', {}).get('percentage', 0)}%)
• Claude Mirror: {summary.get('model_distribution', {}).get('claude_mirror', {}).get('count', 0)} 次 ({summary.get('model_distribution', {}).get('claude_mirror', {}).get('percentage', 0)}%)
• Claude 直接: {summary.get('model_distribution', {}).get('claude_direct', {}).get('count', 0)} 次 ({summary.get('model_distribution', {}).get('claude_direct', {}).get('percentage', 0)}%)

💰 **成本分析**
• 实际成本: ${summary.get('cost_analysis', {}).get('actual_cost_usd', 0)}
• 如全用Claude: ${summary.get('cost_analysis', {}).get('if_all_claude_cost_usd', 0)}
• 节省成本: ${summary.get('cost_analysis', {}).get('cost_savings_usd', 0)} ({summary.get('cost_analysis', {}).get('savings_percentage', 0)}%)

🔢 **Token 使用**
• 总Token: {summary.get('token_usage', {}).get('total_tokens', 0)}
• 输入Token: {summary.get('token_usage', {}).get('input_tokens', 0)}
• 输出Token: {summary.get('token_usage', {}).get('output_tokens', 0)}

🔄 **模型切换分析**
• 切换次数: {switch_analysis.get('total_switches', 0)}
• 切换率: {switch_analysis.get('switch_rate', 0)}%

📝 **最近活动** (最近5条)
"""
        
        for activity in recent_activity:
            report += f"• {activity['timestamp'][-8:]} | {activity['command']} | {activity['model']} | {activity['tokens']} tokens | ${activity['cost_usd']}\n"
        
        return report

# 全局追踪器实例
usage_tracker = MirrorCodeUsageTracker()

# 便捷函数
def track_k2_usage(command: str, input_tokens: int, output_tokens: int, response_time_ms: int):
    """追踪K2本地使用"""
    token_usage = TokenUsage(input_tokens, output_tokens, input_tokens + output_tokens)
    return usage_tracker.record_usage(command, ModelProvider.K2_LOCAL, token_usage, response_time_ms)

def track_claude_mirror_usage(command: str, input_tokens: int, output_tokens: int, response_time_ms: int):
    """追踪Claude Mirror使用"""
    token_usage = TokenUsage(input_tokens, output_tokens, input_tokens + output_tokens)
    return usage_tracker.record_usage(command, ModelProvider.CLAUDE_MIRROR, token_usage, response_time_ms)

def track_claude_direct_usage(command: str, input_tokens: int, output_tokens: int, response_time_ms: int):
    """追踪Claude直接使用"""
    token_usage = TokenUsage(input_tokens, output_tokens, input_tokens + output_tokens)
    return usage_tracker.record_usage(command, ModelProvider.CLAUDE_DIRECT, token_usage, response_time_ms)

def get_current_usage_summary():
    """获取当前使用摘要"""
    return usage_tracker.get_current_session_summary()

def generate_usage_report():
    """生成使用报告"""
    return usage_tracker.generate_usage_report()

if __name__ == "__main__":
    # 测试追踪器
    print("🔄 测试 Mirror Code 使用追踪器")
    
    # 模拟一些使用记录
    track_k2_usage("/help", 10, 50, 120)
    track_k2_usage("/status", 8, 30, 95)
    track_claude_mirror_usage("/review", 150, 300, 2500)
    track_k2_usage("/config", 12, 40, 110)
    track_claude_mirror_usage("/add-dir", 80, 120, 1800)
    
    print("\n" + generate_usage_report())

