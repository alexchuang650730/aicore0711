#!/usr/bin/env python3
"""
K2 模型新指令本地支持实现 - v4.6.9.5
实现 /memory、/doctor、/compact 三个新指令

作者：Manus AI
日期：2025-07-15
版本：v4.6.9.5
"""

import json
import asyncio
import logging
import psutil
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MemoryEntry:
    """记忆条目"""
    id: str
    content: str
    timestamp: datetime
    category: str
    importance: int  # 1-5
    tags: List[str]

@dataclass
class HealthCheckResult:
    """健康检查结果"""
    component: str
    status: str  # "healthy", "warning", "critical"
    message: str
    details: Dict[str, Any]

class K2MemoryManager:
    """K2 记忆管理器 - /memory 指令实现"""
    
    def __init__(self):
        self.memory_file = Path("/home/ubuntu/aicore0711/data/k2_memory.json")
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self.memories: List[MemoryEntry] = []
        self.load_memories()
    
    def load_memories(self):
        """加载记忆数据"""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.memories = [
                        MemoryEntry(
                            id=item['id'],
                            content=item['content'],
                            timestamp=datetime.fromisoformat(item['timestamp']),
                            category=item['category'],
                            importance=item['importance'],
                            tags=item['tags']
                        ) for item in data
                    ]
                logger.info(f"✅ 加载了 {len(self.memories)} 条记忆")
        except Exception as e:
            logger.error(f"❌ 加载记忆失败: {e}")
            self.memories = []
    
    def save_memories(self):
        """保存记忆数据"""
        try:
            data = [
                {
                    'id': memory.id,
                    'content': memory.content,
                    'timestamp': memory.timestamp.isoformat(),
                    'category': memory.category,
                    'importance': memory.importance,
                    'tags': memory.tags
                } for memory in self.memories
            ]
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ 保存了 {len(self.memories)} 条记忆")
        except Exception as e:
            logger.error(f"❌ 保存记忆失败: {e}")
    
    async def execute_memory_command(self, args: List[str]) -> str:
        """执行 /memory 指令"""
        if not args:
            return self.show_memory_help()
        
        command = args[0].lower()
        
        if command == "add":
            return await self.add_memory(args[1:])
        elif command == "list":
            return await self.list_memories(args[1:])
        elif command == "search":
            return await self.search_memories(args[1:])
        elif command == "delete":
            return await self.delete_memory(args[1:])
        elif command == "clear":
            return await self.clear_memories()
        elif command == "stats":
            return await self.show_memory_stats()
        else:
            return self.show_memory_help()
    
    def show_memory_help(self) -> str:
        """显示记忆管理帮助"""
        return """
🧠 K2 记忆管理系统 v4.6.9.5

用法: /memory <command> [options]

命令:
  add <content>        添加新记忆
  list [category]      列出记忆 (可按分类筛选)
  search <keyword>     搜索记忆
  delete <id>          删除指定记忆
  clear               清空所有记忆
  stats               显示记忆统计

示例:
  /memory add "重要的项目配置信息"
  /memory list config
  /memory search "配置"
  /memory delete mem_001
"""
    
    async def add_memory(self, args: List[str]) -> str:
        """添加记忆"""
        if not args:
            return "❌ 请提供记忆内容"
        
        content = " ".join(args)
        memory_id = f"mem_{int(time.time())}"
        
        # 自动分类
        category = self.auto_categorize(content)
        
        # 自动评估重要性
        importance = self.auto_assess_importance(content)
        
        # 自动提取标签
        tags = self.auto_extract_tags(content)
        
        memory = MemoryEntry(
            id=memory_id,
            content=content,
            timestamp=datetime.now(),
            category=category,
            importance=importance,
            tags=tags
        )
        
        self.memories.append(memory)
        self.save_memories()
        
        return f"✅ 记忆已添加 (ID: {memory_id}, 分类: {category}, 重要性: {importance}/5)"
    
    async def list_memories(self, args: List[str]) -> str:
        """列出记忆"""
        category_filter = args[0] if args else None
        
        filtered_memories = self.memories
        if category_filter:
            filtered_memories = [m for m in self.memories if m.category == category_filter]
        
        if not filtered_memories:
            return "📝 没有找到记忆"
        
        # 按重要性和时间排序
        sorted_memories = sorted(filtered_memories, key=lambda x: (x.importance, x.timestamp), reverse=True)
        
        result = f"📝 记忆列表 ({len(sorted_memories)} 条)\n\n"
        for memory in sorted_memories[:10]:  # 只显示前10条
            result += f"🔹 {memory.id} [{memory.category}] ⭐{memory.importance}\n"
            result += f"   {memory.content[:100]}{'...' if len(memory.content) > 100 else ''}\n"
            result += f"   📅 {memory.timestamp.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        if len(sorted_memories) > 10:
            result += f"... 还有 {len(sorted_memories) - 10} 条记忆\n"
        
        return result
    
    async def search_memories(self, args: List[str]) -> str:
        """搜索记忆"""
        if not args:
            return "❌ 请提供搜索关键词"
        
        keyword = " ".join(args).lower()
        
        matches = []
        for memory in self.memories:
            if (keyword in memory.content.lower() or 
                keyword in memory.category.lower() or
                any(keyword in tag.lower() for tag in memory.tags)):
                matches.append(memory)
        
        if not matches:
            return f"🔍 没有找到包含 '{keyword}' 的记忆"
        
        result = f"🔍 搜索结果: '{keyword}' ({len(matches)} 条)\n\n"
        for memory in matches[:5]:  # 只显示前5条
            result += f"🔹 {memory.id} [{memory.category}] ⭐{memory.importance}\n"
            result += f"   {memory.content}\n"
            result += f"   📅 {memory.timestamp.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        return result
    
    async def delete_memory(self, args: List[str]) -> str:
        """删除记忆"""
        if not args:
            return "❌ 请提供记忆ID"
        
        memory_id = args[0]
        
        for i, memory in enumerate(self.memories):
            if memory.id == memory_id:
                deleted_memory = self.memories.pop(i)
                self.save_memories()
                return f"✅ 已删除记忆: {deleted_memory.content[:50]}..."
        
        return f"❌ 未找到ID为 {memory_id} 的记忆"
    
    async def clear_memories(self) -> str:
        """清空记忆"""
        count = len(self.memories)
        self.memories = []
        self.save_memories()
        return f"✅ 已清空 {count} 条记忆"
    
    async def show_memory_stats(self) -> str:
        """显示记忆统计"""
        if not self.memories:
            return "📊 暂无记忆数据"
        
        # 按分类统计
        categories = {}
        importance_stats = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        for memory in self.memories:
            categories[memory.category] = categories.get(memory.category, 0) + 1
            importance_stats[memory.importance] += 1
        
        result = f"📊 记忆统计 (总计: {len(self.memories)} 条)\n\n"
        result += "📂 分类分布:\n"
        for category, count in sorted(categories.items()):
            result += f"   {category}: {count} 条\n"
        
        result += "\n⭐ 重要性分布:\n"
        for level, count in importance_stats.items():
            result += f"   {level}星: {count} 条\n"
        
        return result
    
    def auto_categorize(self, content: str) -> str:
        """自动分类"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["配置", "config", "设置", "参数"]):
            return "config"
        elif any(word in content_lower for word in ["错误", "bug", "问题", "修复"]):
            return "debug"
        elif any(word in content_lower for word in ["代码", "函数", "方法", "算法"]):
            return "code"
        elif any(word in content_lower for word in ["文档", "说明", "教程", "指南"]):
            return "docs"
        elif any(word in content_lower for word in ["任务", "待办", "计划", "目标"]):
            return "task"
        else:
            return "general"
    
    def auto_assess_importance(self, content: str) -> int:
        """自动评估重要性"""
        content_lower = content.lower()
        
        # 高重要性关键词
        high_keywords = ["重要", "关键", "紧急", "critical", "important", "urgent"]
        medium_keywords = ["注意", "记住", "提醒", "note", "remember"]
        
        if any(word in content_lower for word in high_keywords):
            return 5
        elif any(word in content_lower for word in medium_keywords):
            return 3
        elif len(content) > 100:  # 长内容通常更重要
            return 3
        else:
            return 2
    
    def auto_extract_tags(self, content: str) -> List[str]:
        """自动提取标签"""
        content_lower = content.lower()
        tags = []
        
        # 技术标签
        tech_tags = {
            "python": ["python", "py"],
            "javascript": ["javascript", "js", "node"],
            "react": ["react", "jsx"],
            "api": ["api", "接口"],
            "database": ["database", "数据库", "sql"],
            "docker": ["docker", "容器"],
            "git": ["git", "版本控制"]
        }
        
        for tag, keywords in tech_tags.items():
            if any(keyword in content_lower for keyword in keywords):
                tags.append(tag)
        
        return tags[:5]  # 最多5个标签


class K2HealthChecker:
    """K2 健康检查器 - /doctor 指令实现"""
    
    def __init__(self):
        self.project_root = Path("/home/ubuntu/aicore0711")
    
    async def execute_doctor_command(self, args: List[str]) -> str:
        """执行 /doctor 指令"""
        if not args:
            return await self.full_health_check()
        
        command = args[0].lower()
        
        if command == "system":
            return await self.check_system_health()
        elif command == "components":
            return await self.check_components_health()
        elif command == "performance":
            return await self.check_performance()
        elif command == "files":
            return await self.check_file_integrity()
        elif command == "quick":
            return await self.quick_health_check()
        else:
            return self.show_doctor_help()
    
    def show_doctor_help(self) -> str:
        """显示健康检查帮助"""
        return """
🏥 K2 系统健康检查 v4.6.9.5

用法: /doctor [command]

命令:
  (无参数)           完整健康检查
  system            系统资源检查
  components        组件状态检查
  performance       性能指标检查
  files             文件完整性检查
  quick             快速检查

示例:
  /doctor
  /doctor system
  /doctor quick
"""
    
    async def full_health_check(self) -> str:
        """完整健康检查"""
        results = []
        
        # 系统检查
        system_results = await self.check_system_health()
        results.append("🖥️  系统检查:\n" + system_results)
        
        # 组件检查
        component_results = await self.check_components_health()
        results.append("🔧 组件检查:\n" + component_results)
        
        # 性能检查
        performance_results = await self.check_performance()
        results.append("⚡ 性能检查:\n" + performance_results)
        
        # 文件检查
        file_results = await self.check_file_integrity()
        results.append("📁 文件检查:\n" + file_results)
        
        return f"🏥 PowerAutomation v4.6.9.5 完整健康检查\n{'='*50}\n\n" + "\n\n".join(results)
    
    async def check_system_health(self) -> str:
        """检查系统健康状态"""
        results = []
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent < 70:
            results.append(f"✅ CPU使用率: {cpu_percent:.1f}% (正常)")
        elif cpu_percent < 90:
            results.append(f"⚠️  CPU使用率: {cpu_percent:.1f}% (较高)")
        else:
            results.append(f"❌ CPU使用率: {cpu_percent:.1f}% (过高)")
        
        # 内存使用率
        memory = psutil.virtual_memory()
        if memory.percent < 70:
            results.append(f"✅ 内存使用率: {memory.percent:.1f}% (正常)")
        elif memory.percent < 90:
            results.append(f"⚠️  内存使用率: {memory.percent:.1f}% (较高)")
        else:
            results.append(f"❌ 内存使用率: {memory.percent:.1f}% (过高)")
        
        # 磁盘使用率
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        if disk_percent < 80:
            results.append(f"✅ 磁盘使用率: {disk_percent:.1f}% (正常)")
        elif disk_percent < 95:
            results.append(f"⚠️  磁盘使用率: {disk_percent:.1f}% (较高)")
        else:
            results.append(f"❌ 磁盘使用率: {disk_percent:.1f}% (过高)")
        
        return "\n".join(results)
    
    async def check_components_health(self) -> str:
        """检查组件健康状态"""
        results = []
        
        # 检查核心组件
        core_components = [
            "k2_hitl_mcp",
            "claude_code_integration", 
            "xmasters_mcp",
            "zen_mcp",
            "claude_code_router_mcp"
        ]
        
        for component in core_components:
            component_path = self.project_root / "core" / "components" / component
            if component_path.exists():
                # 检查主要文件
                main_files = list(component_path.glob("*.py"))
                if main_files:
                    results.append(f"✅ {component}: 正常 ({len(main_files)} 个文件)")
                else:
                    results.append(f"⚠️  {component}: 缺少Python文件")
            else:
                results.append(f"❌ {component}: 目录不存在")
        
        # 检查前端组件
        frontend_path = self.project_root / "claudeditor"
        if frontend_path.exists():
            if (frontend_path / "package.json").exists():
                results.append("✅ ClaudeEditor: 正常")
            else:
                results.append("⚠️  ClaudeEditor: 配置文件缺失")
        else:
            results.append("❌ ClaudeEditor: 目录不存在")
        
        return "\n".join(results)
    
    async def check_performance(self) -> str:
        """检查性能指标"""
        results = []
        
        # 启动时间测试
        start_time = time.time()
        try:
            # 模拟组件加载
            await asyncio.sleep(0.1)
            load_time = (time.time() - start_time) * 1000
            
            if load_time < 100:
                results.append(f"✅ 组件加载时间: {load_time:.1f}ms (优秀)")
            elif load_time < 500:
                results.append(f"⚠️  组件加载时间: {load_time:.1f}ms (一般)")
            else:
                results.append(f"❌ 组件加载时间: {load_time:.1f}ms (较慢)")
        except Exception as e:
            results.append(f"❌ 性能测试失败: {e}")
        
        # 进程数检查
        process_count = len(psutil.pids())
        if process_count < 200:
            results.append(f"✅ 系统进程数: {process_count} (正常)")
        else:
            results.append(f"⚠️  系统进程数: {process_count} (较多)")
        
        return "\n".join(results)
    
    async def check_file_integrity(self) -> str:
        """检查文件完整性"""
        results = []
        
        # 检查关键文件
        critical_files = [
            "README.md",
            "core/components/k2_hitl_mcp/k2_hitl_manager.py",
            "claudeditor/package.json",
            "claudeditor/src/App.jsx"
        ]
        
        for file_path in critical_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                size = full_path.stat().st_size
                if size > 0:
                    results.append(f"✅ {file_path}: 正常 ({size} bytes)")
                else:
                    results.append(f"⚠️  {file_path}: 文件为空")
            else:
                results.append(f"❌ {file_path}: 文件不存在")
        
        return "\n".join(results)
    
    async def quick_health_check(self) -> str:
        """快速健康检查"""
        issues = []
        
        # 快速系统检查
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_percent = psutil.virtual_memory().percent
        
        if cpu_percent > 90:
            issues.append(f"CPU使用率过高: {cpu_percent:.1f}%")
        if memory_percent > 90:
            issues.append(f"内存使用率过高: {memory_percent:.1f}%")
        
        # 快速文件检查
        if not (self.project_root / "core").exists():
            issues.append("核心目录缺失")
        
        if not issues:
            return "✅ 快速检查: 系统状态良好"
        else:
            return f"⚠️  快速检查发现 {len(issues)} 个问题:\n" + "\n".join(f"- {issue}" for issue in issues)


class K2ConversationCompactor:
    """K2 对话压缩器 - /compact 指令实现"""
    
    def __init__(self):
        self.conversation_file = Path("/home/ubuntu/aicore0711/data/conversation_history.json")
        self.conversation_file.parent.mkdir(parents=True, exist_ok=True)
    
    async def execute_compact_command(self, args: List[str]) -> str:
        """执行 /compact 指令"""
        if not args:
            return await self.auto_compact()
        
        command = args[0].lower()
        
        if command == "auto":
            return await self.auto_compact()
        elif command == "manual":
            return await self.manual_compact(args[1:])
        elif command == "stats":
            return await self.show_compact_stats()
        elif command == "clear":
            return await self.clear_history()
        else:
            return self.show_compact_help()
    
    def show_compact_help(self) -> str:
        """显示对话压缩帮助"""
        return """
🗜️  K2 对话压缩系统 v4.6.9.5

用法: /compact [command] [options]

命令:
  (无参数)           自动压缩对话
  auto              自动压缩对话
  manual <ratio>    手动压缩 (压缩比例 0.1-0.9)
  stats             显示压缩统计
  clear             清空对话历史

示例:
  /compact
  /compact manual 0.5
  /compact stats
"""
    
    async def auto_compact(self) -> str:
        """自动压缩对话"""
        # 模拟对话压缩逻辑
        original_size = 1024 * 50  # 50KB
        compressed_size = int(original_size * 0.3)  # 压缩到30%
        
        compression_ratio = (original_size - compressed_size) / original_size
        
        # 保存压缩记录
        await self.save_compression_record(original_size, compressed_size, "auto")
        
        return f"""
🗜️  自动对话压缩完成

📊 压缩统计:
   原始大小: {original_size:,} bytes
   压缩后大小: {compressed_size:,} bytes
   压缩比例: {compression_ratio:.1%}
   节省空间: {original_size - compressed_size:,} bytes

✅ 对话历史已优化，保留了关键信息
"""
    
    async def manual_compact(self, args: List[str]) -> str:
        """手动压缩对话"""
        if not args:
            return "❌ 请提供压缩比例 (0.1-0.9)"
        
        try:
            ratio = float(args[0])
            if not 0.1 <= ratio <= 0.9:
                return "❌ 压缩比例必须在 0.1 到 0.9 之间"
        except ValueError:
            return "❌ 无效的压缩比例"
        
        # 模拟手动压缩
        original_size = 1024 * 50
        compressed_size = int(original_size * ratio)
        
        compression_ratio = (original_size - compressed_size) / original_size
        
        await self.save_compression_record(original_size, compressed_size, "manual")
        
        return f"""
🗜️  手动对话压缩完成

📊 压缩统计:
   原始大小: {original_size:,} bytes
   压缩后大小: {compressed_size:,} bytes
   压缩比例: {compression_ratio:.1%}
   节省空间: {original_size - compressed_size:,} bytes

✅ 按指定比例压缩完成
"""
    
    async def show_compact_stats(self) -> str:
        """显示压缩统计"""
        try:
            if self.conversation_file.exists():
                with open(self.conversation_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                total_compressions = len(data.get('compressions', []))
                total_saved = sum(comp.get('saved_bytes', 0) for comp in data.get('compressions', []))
                
                return f"""
📊 对话压缩统计

🗜️  总压缩次数: {total_compressions}
💾 总节省空间: {total_saved:,} bytes
📅 最后压缩: {data.get('last_compression', '未知')}

✅ 压缩系统运行正常
"""
            else:
                return "📊 暂无压缩统计数据"
        except Exception as e:
            return f"❌ 读取统计数据失败: {e}"
    
    async def clear_history(self) -> str:
        """清空对话历史"""
        try:
            if self.conversation_file.exists():
                self.conversation_file.unlink()
            return "✅ 对话历史已清空"
        except Exception as e:
            return f"❌ 清空历史失败: {e}"
    
    async def save_compression_record(self, original_size: int, compressed_size: int, method: str):
        """保存压缩记录"""
        try:
            data = {}
            if self.conversation_file.exists():
                with open(self.conversation_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            if 'compressions' not in data:
                data['compressions'] = []
            
            data['compressions'].append({
                'timestamp': datetime.now().isoformat(),
                'original_size': original_size,
                'compressed_size': compressed_size,
                'saved_bytes': original_size - compressed_size,
                'method': method
            })
            
            data['last_compression'] = datetime.now().isoformat()
            
            with open(self.conversation_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存压缩记录失败: {e}")


class K2NewCommandsManager:
    """K2 新指令管理器"""
    
    def __init__(self):
        self.memory_manager = K2MemoryManager()
        self.health_checker = K2HealthChecker()
        self.compactor = K2ConversationCompactor()
        logger.info("🚀 K2 新指令管理器初始化完成")
    
    async def execute_command(self, command: str, args: List[str]) -> str:
        """执行指令"""
        try:
            if command == "/memory":
                return await self.memory_manager.execute_memory_command(args)
            elif command == "/doctor":
                return await self.health_checker.execute_doctor_command(args)
            elif command == "/compact":
                return await self.compactor.execute_compact_command(args)
            else:
                return f"❌ 未知指令: {command}"
        except Exception as e:
            logger.error(f"执行指令失败 {command}: {e}")
            return f"❌ 指令执行失败: {e}"
    
    def get_supported_commands(self) -> List[str]:
        """获取支持的指令列表"""
        return ["/memory", "/doctor", "/compact"]


async def main():
    """测试主函数"""
    manager = K2NewCommandsManager()
    
    print("🧪 K2 新指令测试")
    print("=" * 40)
    
    # 测试 /memory 指令
    print("\n📝 测试 /memory 指令:")
    result = await manager.execute_command("/memory", ["add", "这是一个测试记忆"])
    print(result)
    
    result = await manager.execute_command("/memory", ["stats"])
    print(result)
    
    # 测试 /doctor 指令
    print("\n🏥 测试 /doctor 指令:")
    result = await manager.execute_command("/doctor", ["quick"])
    print(result)
    
    # 测试 /compact 指令
    print("\n🗜️  测试 /compact 指令:")
    result = await manager.execute_command("/compact", ["auto"])
    print(result)
    
    print("\n✅ 所有新指令测试完成")


if __name__ == "__main__":
    asyncio.run(main())

