"""
Enhanced AI Assistant - PowerAutomation AICore Integration
增强的AI助手，连接真实Claude API和PowerAutomation AICore的完整能力
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid

from ..api.enhanced_claude_client import EnhancedClaudeClient, AIRequest, AIResponse, AIModelType

class AssistantMode(Enum):
    """AI助手模式"""
    CODE_ASSISTANT = "code_assistant"
    GENERAL_ASSISTANT = "general_assistant"
    UI_DESIGNER = "ui_designer"
    ARCHITECT = "architect"
    DEBUGGER = "debugger"
    OPTIMIZER = "optimizer"
    TEACHER = "teacher"

class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class AssistantTask:
    """AI助手任务"""
    id: str
    prompt: str
    mode: AssistantMode
    priority: TaskPriority = TaskPriority.NORMAL
    context: Optional[Dict[str, Any]] = None
    callback: Optional[Callable] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[AIResponse] = None
    error: Optional[str] = None

@dataclass
class ConversationContext:
    """对话上下文"""
    session_id: str
    messages: List[Dict[str, str]] = field(default_factory=list)
    mode: AssistantMode = AssistantMode.GENERAL_ASSISTANT
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    project_context: Optional[Dict[str, Any]] = None
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)

class EnhancedAIAssistant:
    """
    增强的AI助手 - 集成PowerAutomation AICore
    提供智能的AI驱动编程助手功能
    """
    
    def __init__(self, 
                 claude_api_key: str,
                 gemini_api_key: Optional[str] = None,
                 enable_aicore: bool = True,
                 max_concurrent_tasks: int = 5,
                 conversation_timeout: int = 3600):
        """
        初始化增强AI助手
        
        Args:
            claude_api_key: Claude API密钥
            gemini_api_key: Gemini API密钥
            enable_aicore: 是否启用AICore集成
            max_concurrent_tasks: 最大并发任务数
            conversation_timeout: 对话超时时间（秒）
        """
        self.claude_api_key = claude_api_key
        self.gemini_api_key = gemini_api_key
        self.enable_aicore = enable_aicore
        self.max_concurrent_tasks = max_concurrent_tasks
        self.conversation_timeout = conversation_timeout
        
        # 核心组件
        self.claude_client: Optional[EnhancedClaudeClient] = None
        
        # 任务管理
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.active_tasks: Dict[str, AssistantTask] = {}
        self.task_workers: List[asyncio.Task] = []
        
        # 对话管理
        self.conversations: Dict[str, ConversationContext] = {}
        
        # 模式配置
        self.mode_configs = {
            AssistantMode.CODE_ASSISTANT: {
                'system_prompt': """You are an expert programming assistant with deep knowledge of multiple programming languages, frameworks, and best practices. You help developers write better code, debug issues, and learn new concepts. Always provide practical, working solutions with clear explanations.""",
                'temperature': 0.3,
                'use_aicore': True,
                'use_expert_system': True
            },
            AssistantMode.GENERAL_ASSISTANT: {
                'system_prompt': """You are a helpful, knowledgeable assistant that can help with a wide range of topics. Provide clear, accurate, and useful information while being conversational and engaging.""",
                'temperature': 0.7,
                'use_aicore': False,
                'use_expert_system': False
            },
            AssistantMode.UI_DESIGNER: {
                'system_prompt': """You are an expert UI/UX designer with extensive knowledge of modern design principles, accessibility, and user experience. Help create beautiful, functional, and user-friendly interfaces.""",
                'temperature': 0.5,
                'use_aicore': True,
                'use_expert_system': True,
                'enable_ui_generation': True
            },
            AssistantMode.ARCHITECT: {
                'system_prompt': """You are a senior software architect with expertise in system design, scalability, and best practices. Help design robust, maintainable, and scalable software systems.""",
                'temperature': 0.2,
                'use_aicore': True,
                'use_expert_system': True
            },
            AssistantMode.DEBUGGER: {
                'system_prompt': """You are an expert debugger who excels at identifying and fixing bugs in code. Analyze code systematically, identify root causes, and provide clear solutions.""",
                'temperature': 0.1,
                'use_aicore': True,
                'use_expert_system': True
            },
            AssistantMode.OPTIMIZER: {
                'system_prompt': """You are a performance optimization expert. Analyze code and systems for performance bottlenecks and provide specific optimization recommendations.""",
                'temperature': 0.2,
                'use_aicore': True,
                'use_expert_system': True
            },
            AssistantMode.TEACHER: {
                'system_prompt': """You are an expert programming teacher who excels at explaining complex concepts in simple, understandable terms. Use examples, analogies, and step-by-step explanations.""",
                'temperature': 0.6,
                'use_aicore': True,
                'use_expert_system': True
            }
        }
        
        # 日志
        self.logger = logging.getLogger(__name__)
        
        # 统计信息
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'active_conversations': 0,
            'mode_usage': {mode.value: 0 for mode in AssistantMode},
            'average_response_time': 0.0,
            'total_response_time': 0.0
        }
    
    async def initialize(self):
        """初始化AI助手"""
        try:
            # 初始化增强Claude客户端
            self.claude_client = EnhancedClaudeClient(
                claude_api_key=self.claude_api_key,
                gemini_api_key=self.gemini_api_key,
                enable_aicore=self.enable_aicore
            )
            await self.claude_client.initialize()
            
            # 启动任务工作器
            for i in range(self.max_concurrent_tasks):
                worker = asyncio.create_task(self._task_worker(f"worker_{i}"))
                self.task_workers.append(worker)
            
            # 启动对话清理任务
            asyncio.create_task(self._conversation_cleanup_task())
            
            self.logger.info("Enhanced AI Assistant initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI Assistant: {e}")
            raise
    
    async def close(self):
        """关闭AI助手"""
        try:
            # 停止任务工作器
            for worker in self.task_workers:
                worker.cancel()
            
            # 等待所有任务完成
            if self.task_workers:
                await asyncio.gather(*self.task_workers, return_exceptions=True)
            
            # 关闭Claude客户端
            if self.claude_client:
                await self.claude_client.close()
            
            self.logger.info("Enhanced AI Assistant closed")
            
        except Exception as e:
            self.logger.error(f"Error closing AI Assistant: {e}")
    
    async def _task_worker(self, worker_name: str):
        """任务工作器"""
        self.logger.info(f"Task worker {worker_name} started")
        
        try:
            while True:
                try:
                    # 获取任务
                    task = await self.task_queue.get()
                    
                    if task is None:  # 停止信号
                        break
                    
                    # 处理任务
                    await self._process_task(task)
                    
                    # 标记任务完成
                    self.task_queue.task_done()
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Task worker {worker_name} error: {e}")
                    
        except asyncio.CancelledError:
            pass
        finally:
            self.logger.info(f"Task worker {worker_name} stopped")
    
    async def _process_task(self, task: AssistantTask):
        """处理单个任务"""
        try:
            task.started_at = time.time()
            self.active_tasks[task.id] = task
            
            # 获取模式配置
            mode_config = self.mode_configs.get(task.mode, self.mode_configs[AssistantMode.GENERAL_ASSISTANT])
            
            # 创建AI请求
            ai_request = AIRequest(
                prompt=task.prompt,
                system_prompt=mode_config['system_prompt'],
                temperature=mode_config['temperature'],
                context=task.context,
                use_aicore=mode_config.get('use_aicore', False),
                use_expert_system=mode_config.get('use_expert_system', False),
                enable_ui_generation=mode_config.get('enable_ui_generation', False)
            )
            
            # 发送请求
            response = await self.claude_client.send_ai_request(ai_request)
            
            # 更新任务结果
            task.result = response
            task.completed_at = time.time()
            
            # 更新统计
            self.stats['completed_tasks'] += 1
            response_time = task.completed_at - task.started_at
            self.stats['total_response_time'] += response_time
            self.stats['average_response_time'] = self.stats['total_response_time'] / self.stats['completed_tasks']
            self.stats['mode_usage'][task.mode.value] += 1
            
            # 调用回调函数
            if task.callback:
                try:
                    await task.callback(task)
                except Exception as e:
                    self.logger.error(f"Task callback error: {e}")
            
            self.logger.info(f"Task {task.id} completed in {response_time:.2f}s")
            
        except Exception as e:
            task.error = str(e)
            task.completed_at = time.time()
            self.stats['failed_tasks'] += 1
            self.logger.error(f"Task {task.id} failed: {e}")
            
        finally:
            # 从活动任务中移除
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]
    
    async def _conversation_cleanup_task(self):
        """对话清理任务"""
        while True:
            try:
                current_time = time.time()
                expired_sessions = []
                
                for session_id, context in self.conversations.items():
                    if current_time - context.last_activity > self.conversation_timeout:
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    del self.conversations[session_id]
                    self.logger.info(f"Conversation {session_id} expired and cleaned up")
                
                self.stats['active_conversations'] = len(self.conversations)
                
                # 每5分钟清理一次
                await asyncio.sleep(300)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Conversation cleanup error: {e}")
                await asyncio.sleep(60)
    
    async def ask(self, 
                  prompt: str, 
                  mode: AssistantMode = AssistantMode.GENERAL_ASSISTANT,
                  session_id: Optional[str] = None,
                  context: Optional[Dict[str, Any]] = None,
                  priority: TaskPriority = TaskPriority.NORMAL,
                  callback: Optional[Callable] = None) -> str:
        """
        向AI助手提问
        
        Args:
            prompt: 问题或请求
            mode: 助手模式
            session_id: 会话ID（用于保持对话上下文）
            context: 额外上下文信息
            priority: 任务优先级
            callback: 完成回调函数
            
        Returns:
            任务ID
        """
        # 创建任务
        task_id = str(uuid.uuid4())
        
        # 处理对话上下文
        if session_id:
            if session_id not in self.conversations:
                self.conversations[session_id] = ConversationContext(
                    session_id=session_id,
                    mode=mode
                )
            
            conversation = self.conversations[session_id]
            conversation.last_activity = time.time()
            conversation.messages.append({
                'role': 'user',
                'content': prompt
            })
            
            # 将对话历史添加到上下文
            if context is None:
                context = {}
            context['conversation_history'] = conversation.messages[-10:]  # 保留最近10条消息
            context['session_id'] = session_id
        
        # 创建任务
        task = AssistantTask(
            id=task_id,
            prompt=prompt,
            mode=mode,
            priority=priority,
            context=context,
            callback=callback
        )
        
        # 添加到队列
        await self.task_queue.put(task)
        self.stats['total_tasks'] += 1
        
        self.logger.info(f"Task {task_id} queued with mode {mode.value}")
        return task_id
    
    async def get_task_result(self, task_id: str, timeout: float = 30.0) -> Optional[AIResponse]:
        """
        获取任务结果
        
        Args:
            task_id: 任务ID
            timeout: 超时时间
            
        Returns:
            AI响应或None
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 检查活动任务
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                if task.completed_at:
                    return task.result
            
            await asyncio.sleep(0.1)
        
        self.logger.warning(f"Task {task_id} timeout after {timeout}s")
        return None
    
    async def ask_and_wait(self, 
                          prompt: str, 
                          mode: AssistantMode = AssistantMode.GENERAL_ASSISTANT,
                          session_id: Optional[str] = None,
                          context: Optional[Dict[str, Any]] = None,
                          timeout: float = 30.0) -> Optional[AIResponse]:
        """
        提问并等待结果
        
        Args:
            prompt: 问题或请求
            mode: 助手模式
            session_id: 会话ID
            context: 额外上下文信息
            timeout: 超时时间
            
        Returns:
            AI响应或None
        """
        task_id = await self.ask(prompt, mode, session_id, context)
        return await self.get_task_result(task_id, timeout)
    
    # 便捷方法
    async def code_complete(self, 
                           code: str, 
                           language: str = "python",
                           session_id: Optional[str] = None) -> Optional[AIResponse]:
        """代码补全"""
        prompt = f"Complete this {language} code:\n\n```{language}\n{code}\n```"
        return await self.ask_and_wait(
            prompt=prompt,
            mode=AssistantMode.CODE_ASSISTANT,
            session_id=session_id,
            context={'language': language, 'code': code}
        )
    
    async def code_explain(self, 
                          code: str, 
                          language: str = "python",
                          session_id: Optional[str] = None) -> Optional[AIResponse]:
        """代码解释"""
        prompt = f"Explain this {language} code:\n\n```{language}\n{code}\n```"
        return await self.ask_and_wait(
            prompt=prompt,
            mode=AssistantMode.TEACHER,
            session_id=session_id,
            context={'language': language, 'code': code}
        )
    
    async def code_debug(self, 
                        code: str, 
                        error_message: str,
                        language: str = "python",
                        session_id: Optional[str] = None) -> Optional[AIResponse]:
        """代码调试"""
        prompt = f"Debug this {language} code that has an error:\n\nCode:\n```{language}\n{code}\n```\n\nError: {error_message}"
        return await self.ask_and_wait(
            prompt=prompt,
            mode=AssistantMode.DEBUGGER,
            session_id=session_id,
            context={'language': language, 'code': code, 'error': error_message}
        )
    
    async def code_optimize(self, 
                           code: str, 
                           language: str = "python",
                           optimization_type: str = "performance",
                           session_id: Optional[str] = None) -> Optional[AIResponse]:
        """代码优化"""
        prompt = f"Optimize this {language} code for {optimization_type}:\n\n```{language}\n{code}\n```"
        return await self.ask_and_wait(
            prompt=prompt,
            mode=AssistantMode.OPTIMIZER,
            session_id=session_id,
            context={'language': language, 'code': code, 'optimization_type': optimization_type}
        )
    
    async def design_ui(self, 
                       description: str, 
                       ui_type: str = "web",
                       session_id: Optional[str] = None) -> Optional[AIResponse]:
        """UI设计"""
        prompt = f"Design a {ui_type} user interface for: {description}"
        return await self.ask_and_wait(
            prompt=prompt,
            mode=AssistantMode.UI_DESIGNER,
            session_id=session_id,
            context={'description': description, 'ui_type': ui_type}
        )
    
    async def architect_system(self, 
                              requirements: str,
                              session_id: Optional[str] = None) -> Optional[AIResponse]:
        """系统架构设计"""
        prompt = f"Design a software system architecture for these requirements:\n\n{requirements}"
        return await self.ask_and_wait(
            prompt=prompt,
            mode=AssistantMode.ARCHITECT,
            session_id=session_id,
            context={'requirements': requirements}
        )
    
    def get_conversation_context(self, session_id: str) -> Optional[ConversationContext]:
        """获取对话上下文"""
        return self.conversations.get(session_id)
    
    def clear_conversation(self, session_id: str):
        """清除对话上下文"""
        if session_id in self.conversations:
            del self.conversations[session_id]
            self.logger.info(f"Conversation {session_id} cleared")
    
    def get_active_tasks(self) -> List[AssistantTask]:
        """获取活动任务列表"""
        return list(self.active_tasks.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """获取助手统计信息"""
        return {
            **self.stats,
            'queue_size': self.task_queue.qsize(),
            'active_tasks_count': len(self.active_tasks),
            'worker_count': len(self.task_workers),
            'claude_client_stats': self.claude_client.get_stats() if self.claude_client else {}
        }

# 使用示例
async def main():
    """使用示例"""
    # 使用提供的API密钥
    claude_key = "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"
    gemini_key = "AIzaSyC_EsNirr14s8ypd3KafqWazSi_RW0NiqA"
    
    assistant = EnhancedAIAssistant(
        claude_api_key=claude_key,
        gemini_api_key=gemini_key,
        enable_aicore=True
    )
    
    try:
        await assistant.initialize()
        
        # 创建会话
        session_id = "demo_session"
        
        # 代码补全示例
        code = "def fibonacci(n):\n    if n <= 1:\n        return n\n    "
        response = await assistant.code_complete(code, "python", session_id)
        if response:
            print("Code completion:", response.content[:200] + "...")
        
        # 代码解释示例
        full_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
        response = await assistant.code_explain(full_code, "python", session_id)
        if response:
            print("Code explanation:", response.content[:200] + "...")
        
        # UI设计示例
        response = await assistant.design_ui("A todo list application with add, edit, delete functionality", "web", session_id)
        if response:
            print("UI design:", response.content[:200] + "...")
        
        # 获取统计信息
        stats = assistant.get_stats()
        print("Assistant stats:", {k: v for k, v in stats.items() if k in ['completed_tasks', 'average_response_time', 'active_conversations']})
        
    finally:
        await assistant.close()

if __name__ == "__main__":
    asyncio.run(main())

