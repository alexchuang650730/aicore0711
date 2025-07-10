# WebUI MCP 与 Claudia UI 整合方案

## 🎯 **整合概览**

WebUI MCP与Claudia UI的整合将创造一个革命性的AI协作开发界面，结合我们已有的MCP架构优势和Claudia的成熟GUI经验。

### 🔗 **整合价值**
- **技术互补**: WebUI MCP的后端架构 + Claudia的前端体验
- **功能增强**: MCP协议标准化 + Claudia的GUI管理经验
- **生态融合**: PowerAutomation生态 + Claude Code生态

## 🏗️ **整合架构设计**

### 📊 **整体架构图**
```
┌─────────────────────────────────────────────────────────────┐
│                    🎨 Claudia-Inspired UI Layer             │
├─────────────────────────────────────────────────────────────┤
│  📊 项目管理面板  │  🤖 智能体管理  │  📈 使用分析  │  ⚙️ MCP配置  │
│  (Claudia风格)   │  (CC Agents)   │  (Analytics) │  (Servers)  │
├─────────────────────────────────────────────────────────────┤
│                   🔌 WebUI MCP Adapter Layer                │
├─────────────────────────────────────────────────────────────┤
│  🌐 SmartUI适配器  │  📡 Claudia桥接  │  🔄 状态同步  │  📊 事件路由  │
│  (已完成2000+行)  │  (新增)         │  (增强)      │  (扩展)      │
├─────────────────────────────────────────────────────────────┤
│                   💾 Claudia Integration Layer              │
├─────────────────────────────────────────────────────────────┤
│  📝 会话管理      │  📚 项目浏览     │  🏛️ MCP服务器  │  👤 用户分析  │
│  (Session Mgmt)  │  (Project Exp)  │  (Server Mgmt)│  (Analytics) │
├─────────────────────────────────────────────────────────────┤
│                   🛠️ Claude Code Integration                │
├─────────────────────────────────────────────────────────────┤
│  🔧 Claude CLI    │  ⚡ CC Agents    │  🎨 CLAUDE.md │  🔍 工具发现  │
│  (命令行集成)     │  (智能体)        │  (文档管理)   │  (Tool Disc) │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 **核心整合组件**

### 1. **Claudia Bridge Adapter** - 核心桥接器

```python
# components/claudia_integration/claudia_bridge_adapter.py

import asyncio
import json
import subprocess
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from ..web_ui_mcp.smartui_adapter import SmartUIAdapter, WebSocketMessage, MessageType


@dataclass
class ClaudiaSession:
    """Claudia会话数据结构"""
    id: str
    project_path: str
    first_message: str
    timestamp: datetime
    status: str
    metadata: Dict[str, Any]


@dataclass
class ClaudiaProject:
    """Claudia项目数据结构"""
    name: str
    path: str
    sessions: List[ClaudiaSession]
    last_accessed: datetime
    description: str


@dataclass
class ClaudiaMCPServer:
    """Claudia MCP服务器配置"""
    name: str
    command: str
    args: List[str]
    env: Dict[str, str]
    status: str
    capabilities: List[str]


class ClaudiaBridgeAdapter:
    """
    Claudia Bridge Adapter
    
    将Claudia的功能桥接到WebUI MCP系统中
    """
    
    def __init__(self, smartui_adapter: SmartUIAdapter):
        self.smartui_adapter = smartui_adapter
        self.claude_projects_path = "~/.claude/projects/"
        self.claudia_config_path = "~/.claudia/"
        
        # Claudia数据管理
        self.projects: Dict[str, ClaudiaProject] = {}
        self.sessions: Dict[str, ClaudiaSession] = {}
        self.mcp_servers: Dict[str, ClaudiaMCPServer] = {}
        
        # 使用分析数据
        self.usage_analytics = {
            "total_tokens": 0,
            "total_cost": 0.0,
            "sessions_count": 0,
            "projects_count": 0,
            "daily_usage": {}
        }
        
        self._setup_claudia_integration()
    
    def _setup_claudia_integration(self):
        """设置Claudia集成"""
        # 注册Claudia特定的消息处理器
        self.smartui_adapter.add_event_listener(
            "claudia_project_request", 
            self._handle_project_request
        )
        self.smartui_adapter.add_event_listener(
            "claudia_session_request", 
            self._handle_session_request
        )
        self.smartui_adapter.add_event_listener(
            "claudia_mcp_server_request", 
            self._handle_mcp_server_request
        )
        self.smartui_adapter.add_event_listener(
            "claudia_analytics_request", 
            self._handle_analytics_request
        )
    
    async def discover_claude_projects(self) -> List[ClaudiaProject]:
        """发现Claude Code项目"""
        try:
            # 扫描~/.claude/projects/目录
            import os
            import glob
            
            projects_path = os.path.expanduser(self.claude_projects_path)
            project_dirs = glob.glob(f"{projects_path}*/")
            
            projects = []
            for project_dir in project_dirs:
                project_name = os.path.basename(project_dir.rstrip('/'))
                
                # 读取项目会话
                sessions = await self._discover_project_sessions(project_dir)
                
                project = ClaudiaProject(
                    name=project_name,
                    path=project_dir,
                    sessions=sessions,
                    last_accessed=datetime.now(),
                    description=f"Claude Code项目: {project_name}"
                )
                
                projects.append(project)
                self.projects[project_name] = project
            
            return projects
            
        except Exception as e:
            print(f"发现Claude项目时出错: {e}")
            return []
    
    async def _discover_project_sessions(self, project_path: str) -> List[ClaudiaSession]:
        """发现项目会话"""
        try:
            import os
            import json
            
            sessions = []
            session_files = glob.glob(f"{project_path}*.json")
            
            for session_file in session_files:
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    session = ClaudiaSession(
                        id=os.path.basename(session_file).replace('.json', ''),
                        project_path=project_path,
                        first_message=session_data.get('messages', [{}])[0].get('content', '')[:100],
                        timestamp=datetime.fromisoformat(session_data.get('created_at', datetime.now().isoformat())),
                        status='completed',
                        metadata=session_data.get('metadata', {})
                    )
                    
                    sessions.append(session)
                    self.sessions[session.id] = session
                    
                except Exception as e:
                    print(f"读取会话文件 {session_file} 时出错: {e}")
                    continue
            
            return sessions
            
        except Exception as e:
            print(f"发现项目会话时出错: {e}")
            return []
    
    async def discover_mcp_servers(self) -> List[ClaudiaMCPServer]:
        """发现MCP服务器配置"""
        try:
            # 从Claude Desktop配置导入
            claude_desktop_config = await self._read_claude_desktop_config()
            
            # 从Claudia配置读取
            claudia_config = await self._read_claudia_config()
            
            servers = []
            
            # 处理Claude Desktop配置
            if claude_desktop_config and 'mcpServers' in claude_desktop_config:
                for server_name, server_config in claude_desktop_config['mcpServers'].items():
                    server = ClaudiaMCPServer(
                        name=server_name,
                        command=server_config.get('command', ''),
                        args=server_config.get('args', []),
                        env=server_config.get('env', {}),
                        status='configured',
                        capabilities=server_config.get('capabilities', [])
                    )
                    servers.append(server)
                    self.mcp_servers[server_name] = server
            
            return servers
            
        except Exception as e:
            print(f"发现MCP服务器时出错: {e}")
            return []
    
    async def _read_claude_desktop_config(self) -> Optional[Dict]:
        """读取Claude Desktop配置"""
        try:
            import os
            import json
            
            # macOS路径
            macos_path = "~/Library/Application Support/Claude/claude_desktop_config.json"
            # Windows路径
            windows_path = "~/AppData/Roaming/Claude/claude_desktop_config.json"
            # Linux路径
            linux_path = "~/.config/Claude/claude_desktop_config.json"
            
            for config_path in [macos_path, windows_path, linux_path]:
                expanded_path = os.path.expanduser(config_path)
                if os.path.exists(expanded_path):
                    with open(expanded_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
            
            return None
            
        except Exception as e:
            print(f"读取Claude Desktop配置时出错: {e}")
            return None
    
    async def _read_claudia_config(self) -> Optional[Dict]:
        """读取Claudia配置"""
        try:
            import os
            import json
            
            config_path = os.path.expanduser(f"{self.claudia_config_path}config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            return None
            
        except Exception as e:
            print(f"读取Claudia配置时出错: {e}")
            return None
    
    async def create_cc_agent(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """创建CC Agent"""
        try:
            # 验证配置
            required_fields = ['name', 'system_prompt', 'model']
            for field in required_fields:
                if field not in agent_config:
                    raise ValueError(f"缺少必需字段: {field}")
            
            # 创建智能体配置
            agent = {
                'id': f"cc_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'name': agent_config['name'],
                'description': agent_config.get('description', ''),
                'system_prompt': agent_config['system_prompt'],
                'model': agent_config['model'],
                'capabilities': agent_config.get('capabilities', []),
                'permissions': agent_config.get('permissions', {}),
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            # 保存智能体配置
            await self._save_cc_agent(agent)
            
            return {
                'success': True,
                'agent_id': agent['id'],
                'message': f"CC Agent '{agent['name']}' 创建成功"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f"创建CC Agent失败: {e}"
            }
    
    async def _save_cc_agent(self, agent: Dict[str, Any]):
        """保存CC Agent配置"""
        try:
            import os
            import json
            
            agents_dir = os.path.expanduser(f"{self.claudia_config_path}agents/")
            os.makedirs(agents_dir, exist_ok=True)
            
            agent_file = f"{agents_dir}{agent['id']}.json"
            with open(agent_file, 'w', encoding='utf-8') as f:
                json.dump(agent, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"保存CC Agent时出错: {e}")
            raise
    
    async def execute_cc_agent(self, agent_id: str, task: str, project_path: str = None) -> Dict[str, Any]:
        """执行CC Agent"""
        try:
            # 加载智能体配置
            agent = await self._load_cc_agent(agent_id)
            if not agent:
                raise ValueError(f"未找到智能体: {agent_id}")
            
            # 构建Claude Code命令
            cmd = ['claude']
            
            # 添加系统提示
            if agent.get('system_prompt'):
                cmd.extend(['--system', agent['system_prompt']])
            
            # 添加模型
            if agent.get('model'):
                cmd.extend(['--model', agent['model']])
            
            # 添加项目路径
            if project_path:
                cmd.extend(['--project', project_path])
            
            # 添加任务
            cmd.append(task)
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=project_path
            )
            
            stdout, stderr = await process.communicate()
            
            result = {
                'success': process.returncode == 0,
                'agent_id': agent_id,
                'task': task,
                'output': stdout.decode('utf-8') if stdout else '',
                'error': stderr.decode('utf-8') if stderr else '',
                'return_code': process.returncode,
                'executed_at': datetime.now().isoformat()
            }
            
            # 记录执行历史
            await self._record_agent_execution(result)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f"执行CC Agent失败: {e}"
            }
    
    async def _load_cc_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """加载CC Agent配置"""
        try:
            import os
            import json
            
            agent_file = os.path.expanduser(f"{self.claudia_config_path}agents/{agent_id}.json")
            if os.path.exists(agent_file):
                with open(agent_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            return None
            
        except Exception as e:
            print(f"加载CC Agent时出错: {e}")
            return None
    
    async def _record_agent_execution(self, execution_result: Dict[str, Any]):
        """记录智能体执行历史"""
        try:
            import os
            import json
            
            history_dir = os.path.expanduser(f"{self.claudia_config_path}history/")
            os.makedirs(history_dir, exist_ok=True)
            
            history_file = f"{history_dir}agent_executions.jsonl"
            with open(history_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(execution_result, ensure_ascii=False) + '\n')
                
        except Exception as e:
            print(f"记录执行历史时出错: {e}")
    
    async def get_usage_analytics(self) -> Dict[str, Any]:
        """获取使用分析数据"""
        try:
            # 从Claude CLI获取使用数据
            usage_data = await self._fetch_claude_usage_data()
            
            # 从执行历史获取统计
            execution_stats = await self._get_execution_statistics()
            
            analytics = {
                'overview': {
                    'total_tokens': usage_data.get('total_tokens', 0),
                    'total_cost': usage_data.get('total_cost', 0.0),
                    'sessions_count': len(self.sessions),
                    'projects_count': len(self.projects),
                    'agents_count': len(await self._get_all_agents())
                },
                'usage_by_model': usage_data.get('by_model', {}),
                'usage_by_project': usage_data.get('by_project', {}),
                'daily_usage': usage_data.get('daily_usage', {}),
                'execution_stats': execution_stats,
                'cost_breakdown': usage_data.get('cost_breakdown', {}),
                'generated_at': datetime.now().isoformat()
            }
            
            return analytics
            
        except Exception as e:
            print(f"获取使用分析时出错: {e}")
            return {
                'overview': {
                    'total_tokens': 0,
                    'total_cost': 0.0,
                    'sessions_count': 0,
                    'projects_count': 0,
                    'agents_count': 0
                },
                'error': str(e)
            }
    
    async def _fetch_claude_usage_data(self) -> Dict[str, Any]:
        """从Claude CLI获取使用数据"""
        try:
            # 执行claude usage命令
            process = await asyncio.create_subprocess_exec(
                'claude', 'usage', '--json',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and stdout:
                return json.loads(stdout.decode('utf-8'))
            else:
                print(f"获取Claude使用数据失败: {stderr.decode('utf-8') if stderr else 'Unknown error'}")
                return {}
                
        except Exception as e:
            print(f"获取Claude使用数据时出错: {e}")
            return {}
    
    async def _get_execution_statistics(self) -> Dict[str, Any]:
        """获取执行统计数据"""
        try:
            import os
            import json
            
            history_file = os.path.expanduser(f"{self.claudia_config_path}history/agent_executions.jsonl")
            if not os.path.exists(history_file):
                return {}
            
            stats = {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'by_agent': {},
                'by_date': {}
            }
            
            with open(history_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        execution = json.loads(line.strip())
                        stats['total_executions'] += 1
                        
                        if execution.get('success'):
                            stats['successful_executions'] += 1
                        else:
                            stats['failed_executions'] += 1
                        
                        # 按智能体统计
                        agent_id = execution.get('agent_id', 'unknown')
                        if agent_id not in stats['by_agent']:
                            stats['by_agent'][agent_id] = {'total': 0, 'success': 0, 'failed': 0}
                        
                        stats['by_agent'][agent_id]['total'] += 1
                        if execution.get('success'):
                            stats['by_agent'][agent_id]['success'] += 1
                        else:
                            stats['by_agent'][agent_id]['failed'] += 1
                        
                        # 按日期统计
                        date = execution.get('executed_at', '')[:10]  # YYYY-MM-DD
                        if date not in stats['by_date']:
                            stats['by_date'][date] = 0
                        stats['by_date'][date] += 1
                        
                    except json.JSONDecodeError:
                        continue
            
            return stats
            
        except Exception as e:
            print(f"获取执行统计时出错: {e}")
            return {}
    
    async def _get_all_agents(self) -> List[Dict[str, Any]]:
        """获取所有智能体"""
        try:
            import os
            import json
            import glob
            
            agents_dir = os.path.expanduser(f"{self.claudia_config_path}agents/")
            if not os.path.exists(agents_dir):
                return []
            
            agents = []
            agent_files = glob.glob(f"{agents_dir}*.json")
            
            for agent_file in agent_files:
                try:
                    with open(agent_file, 'r', encoding='utf-8') as f:
                        agent = json.load(f)
                        agents.append(agent)
                except Exception as e:
                    print(f"读取智能体文件 {agent_file} 时出错: {e}")
                    continue
            
            return agents
            
        except Exception as e:
            print(f"获取所有智能体时出错: {e}")
            return []
    
    # WebSocket消息处理器
    async def _handle_project_request(self, data: Dict[str, Any]):
        """处理项目请求"""
        try:
            action = data.get('action')
            
            if action == 'list_projects':
                projects = await self.discover_claude_projects()
                return {
                    'type': 'project_response',
                    'action': 'list_projects',
                    'projects': [
                        {
                            'name': p.name,
                            'path': p.path,
                            'sessions_count': len(p.sessions),
                            'last_accessed': p.last_accessed.isoformat(),
                            'description': p.description
                        }
                        for p in projects
                    ]
                }
            
            elif action == 'get_project_sessions':
                project_name = data.get('project_name')
                if project_name in self.projects:
                    project = self.projects[project_name]
                    return {
                        'type': 'project_response',
                        'action': 'get_project_sessions',
                        'project_name': project_name,
                        'sessions': [
                            {
                                'id': s.id,
                                'first_message': s.first_message,
                                'timestamp': s.timestamp.isoformat(),
                                'status': s.status
                            }
                            for s in project.sessions
                        ]
                    }
                else:
                    return {
                        'type': 'error',
                        'message': f'项目未找到: {project_name}'
                    }
            
        except Exception as e:
            return {
                'type': 'error',
                'message': f'处理项目请求时出错: {e}'
            }
    
    async def _handle_session_request(self, data: Dict[str, Any]):
        """处理会话请求"""
        try:
            action = data.get('action')
            
            if action == 'resume_session':
                session_id = data.get('session_id')
                project_path = data.get('project_path')
                
                # 执行Claude Code恢复会话命令
                cmd = ['claude', 'resume', session_id]
                if project_path:
                    cmd.extend(['--project', project_path])
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                return {
                    'type': 'session_response',
                    'action': 'resume_session',
                    'session_id': session_id,
                    'success': process.returncode == 0,
                    'output': stdout.decode('utf-8') if stdout else '',
                    'error': stderr.decode('utf-8') if stderr else ''
                }
            
        except Exception as e:
            return {
                'type': 'error',
                'message': f'处理会话请求时出错: {e}'
            }
    
    async def _handle_mcp_server_request(self, data: Dict[str, Any]):
        """处理MCP服务器请求"""
        try:
            action = data.get('action')
            
            if action == 'list_servers':
                servers = await self.discover_mcp_servers()
                return {
                    'type': 'mcp_server_response',
                    'action': 'list_servers',
                    'servers': [
                        {
                            'name': s.name,
                            'command': s.command,
                            'args': s.args,
                            'status': s.status,
                            'capabilities': s.capabilities
                        }
                        for s in servers
                    ]
                }
            
            elif action == 'test_connection':
                server_name = data.get('server_name')
                if server_name in self.mcp_servers:
                    server = self.mcp_servers[server_name]
                    
                    # 测试MCP服务器连接
                    test_result = await self._test_mcp_server_connection(server)
                    
                    return {
                        'type': 'mcp_server_response',
                        'action': 'test_connection',
                        'server_name': server_name,
                        'success': test_result['success'],
                        'message': test_result['message']
                    }
                else:
                    return {
                        'type': 'error',
                        'message': f'MCP服务器未找到: {server_name}'
                    }
            
        except Exception as e:
            return {
                'type': 'error',
                'message': f'处理MCP服务器请求时出错: {e}'
            }
    
    async def _handle_analytics_request(self, data: Dict[str, Any]):
        """处理分析请求"""
        try:
            analytics = await self.get_usage_analytics()
            
            return {
                'type': 'analytics_response',
                'analytics': analytics
            }
            
        except Exception as e:
            return {
                'type': 'error',
                'message': f'处理分析请求时出错: {e}'
            }
    
    async def _test_mcp_server_connection(self, server: ClaudiaMCPServer) -> Dict[str, Any]:
        """测试MCP服务器连接"""
        try:
            # 构建测试命令
            cmd = [server.command] + server.args
            
            # 设置环境变量
            env = os.environ.copy()
            env.update(server.env)
            
            # 执行测试
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10.0)
                
                return {
                    'success': process.returncode == 0,
                    'message': 'MCP服务器连接成功' if process.returncode == 0 else f'连接失败: {stderr.decode("utf-8")}'
                }
                
            except asyncio.TimeoutError:
                process.kill()
                return {
                    'success': False,
                    'message': 'MCP服务器连接超时'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'测试MCP服务器连接时出错: {e}'
            }


# 使用示例
if __name__ == "__main__":
    async def main():
        # 创建SmartUI适配器
        smartui_adapter = SmartUIAdapter()
        
        # 创建Claudia桥接适配器
        claudia_bridge = ClaudiaBridgeAdapter(smartui_adapter)
        
        # 发现项目和服务器
        projects = await claudia_bridge.discover_claude_projects()
        servers = await claudia_bridge.discover_mcp_servers()
        
        print(f"发现 {len(projects)} 个Claude项目")
        print(f"发现 {len(servers)} 个MCP服务器")
        
        # 获取使用分析
        analytics = await claudia_bridge.get_usage_analytics()
        print(f"使用分析: {analytics}")
    
    asyncio.run(main())
```

### 2. **Claudia-Style UI Components** - 界面组件

```typescript
// components/claudia_integration/claudia_ui_components.tsx

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  FolderOpen, 
  MessageSquare, 
  Server, 
  BarChart3, 
  Play, 
  Settings,
  Clock,
  CheckCircle,
  XCircle
} from 'lucide-react';

interface ClaudiaProject {
  name: string;
  path: string;
  sessions_count: number;
  last_accessed: string;
  description: string;
}

interface ClaudiaSession {
  id: string;
  first_message: string;
  timestamp: string;
  status: string;
}

interface ClaudiaMCPServer {
  name: string;
  command: string;
  args: string[];
  status: string;
  capabilities: string[];
}

interface UsageAnalytics {
  overview: {
    total_tokens: number;
    total_cost: number;
    sessions_count: number;
    projects_count: number;
    agents_count: number;
  };
  usage_by_model: Record<string, number>;
  daily_usage: Record<string, number>;
}

export const ClaudiaProjectBrowser: React.FC = () => {
  const [projects, setProjects] = useState<ClaudiaProject[]>([]);
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ClaudiaSession[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    setLoading(true);
    try {
      // 通过WebSocket请求项目列表
      const response = await sendWebSocketMessage({
        type: 'claudia_project_request',
        data: { action: 'list_projects' }
      });
      
      if (response.type === 'project_response') {
        setProjects(response.projects);
      }
    } catch (error) {
      console.error('加载项目失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadProjectSessions = async (projectName: string) => {
    try {
      const response = await sendWebSocketMessage({
        type: 'claudia_project_request',
        data: { 
          action: 'get_project_sessions',
          project_name: projectName
        }
      });
      
      if (response.type === 'project_response') {
        setSessions(response.sessions);
        setSelectedProject(projectName);
      }
    } catch (error) {
      console.error('加载项目会话失败:', error);
    }
  };

  const resumeSession = async (sessionId: string, projectPath: string) => {
    try {
      const response = await sendWebSocketMessage({
        type: 'claudia_session_request',
        data: { 
          action: 'resume_session',
          session_id: sessionId,
          project_path: projectPath
        }
      });
      
      if (response.success) {
        // 处理会话恢复成功
        console.log('会话恢复成功');
      }
    } catch (error) {
      console.error('恢复会话失败:', error);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FolderOpen className="h-5 w-5" />
            Claude Code 项目
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">加载中...</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {projects.map((project) => (
                <Card 
                  key={project.name}
                  className={`cursor-pointer transition-colors hover:bg-gray-50 ${
                    selectedProject === project.name ? 'ring-2 ring-blue-500' : ''
                  }`}
                  onClick={() => loadProjectSessions(project.name)}
                >
                  <CardContent className="p-4">
                    <h3 className="font-semibold text-lg mb-2">{project.name}</h3>
                    <p className="text-sm text-gray-600 mb-3">{project.description}</p>
                    <div className="flex justify-between items-center">
                      <Badge variant="secondary">
                        {project.sessions_count} 会话
                      </Badge>
                      <span className="text-xs text-gray-500">
                        {new Date(project.last_accessed).toLocaleDateString()}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {selectedProject && sessions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              {selectedProject} - 会话历史
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {sessions.map((session) => (
                <div 
                  key={session.id}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
                >
                  <div className="flex-1">
                    <p className="text-sm font-medium mb-1">
                      {session.first_message || '无消息内容'}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <Clock className="h-3 w-3" />
                      {new Date(session.timestamp).toLocaleString()}
                      <Badge 
                        variant={session.status === 'completed' ? 'default' : 'secondary'}
                        className="ml-2"
                      >
                        {session.status}
                      </Badge>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => resumeSession(session.id, projects.find(p => p.name === selectedProject)?.path || '')}
                  >
                    <Play className="h-4 w-4 mr-1" />
                    恢复
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export const ClaudiaMCPServerManager: React.FC = () => {
  const [servers, setServers] = useState<ClaudiaMCPServer[]>([]);
  const [loading, setLoading] = useState(false);
  const [testingServer, setTestingServer] = useState<string | null>(null);

  useEffect(() => {
    loadMCPServers();
  }, []);

  const loadMCPServers = async () => {
    setLoading(true);
    try {
      const response = await sendWebSocketMessage({
        type: 'claudia_mcp_server_request',
        data: { action: 'list_servers' }
      });
      
      if (response.type === 'mcp_server_response') {
        setServers(response.servers);
      }
    } catch (error) {
      console.error('加载MCP服务器失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const testServerConnection = async (serverName: string) => {
    setTestingServer(serverName);
    try {
      const response = await sendWebSocketMessage({
        type: 'claudia_mcp_server_request',
        data: { 
          action: 'test_connection',
          server_name: serverName
        }
      });
      
      if (response.type === 'mcp_server_response') {
        // 更新服务器状态
        setServers(prev => prev.map(server => 
          server.name === serverName 
            ? { ...server, status: response.success ? 'connected' : 'error' }
            : server
        ));
      }
    } catch (error) {
      console.error('测试服务器连接失败:', error);
    } finally {
      setTestingServer(null);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Server className="h-5 w-5" />
          MCP 服务器管理
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-center py-8">加载中...</div>
        ) : (
          <div className="space-y-4">
            {servers.map((server) => (
              <div 
                key={server.name}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <div className="flex-1">
                  <h3 className="font-semibold text-lg mb-1">{server.name}</h3>
                  <p className="text-sm text-gray-600 mb-2">
                    命令: {server.command} {server.args.join(' ')}
                  </p>
                  <div className="flex items-center gap-2">
                    <Badge 
                      variant={
                        server.status === 'connected' ? 'default' :
                        server.status === 'error' ? 'destructive' : 'secondary'
                      }
                    >
                      {server.status === 'connected' && <CheckCircle className="h-3 w-3 mr-1" />}
                      {server.status === 'error' && <XCircle className="h-3 w-3 mr-1" />}
                      {server.status}
                    </Badge>
                    <div className="flex gap-1">
                      {server.capabilities.map((capability) => (
                        <Badge key={capability} variant="outline" className="text-xs">
                          {capability}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => testServerConnection(server.name)}
                    disabled={testingServer === server.name}
                  >
                    {testingServer === server.name ? '测试中...' : '测试连接'}
                  </Button>
                  <Button size="sm" variant="outline">
                    <Settings className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export const ClaudiaUsageAnalytics: React.FC = () => {
  const [analytics, setAnalytics] = useState<UsageAnalytics | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const response = await sendWebSocketMessage({
        type: 'claudia_analytics_request',
        data: {}
      });
      
      if (response.type === 'analytics_response') {
        setAnalytics(response.analytics);
      }
    } catch (error) {
      console.error('加载使用分析失败:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8">加载中...</div>;
  }

  if (!analytics) {
    return <div className="text-center py-8">无法加载使用分析数据</div>;
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">总Token数</p>
                <p className="text-2xl font-bold">{analytics.overview.total_tokens.toLocaleString()}</p>
              </div>
              <BarChart3 className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">总成本</p>
                <p className="text-2xl font-bold">${analytics.overview.total_cost.toFixed(2)}</p>
              </div>
              <BarChart3 className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">会话数</p>
                <p className="text-2xl font-bold">{analytics.overview.sessions_count}</p>
              </div>
              <MessageSquare className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">项目数</p>
                <p className="text-2xl font-bold">{analytics.overview.projects_count}</p>
              </div>
              <FolderOpen className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>使用详情</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="models">
            <TabsList>
              <TabsTrigger value="models">按模型</TabsTrigger>
              <TabsTrigger value="daily">每日使用</TabsTrigger>
            </TabsList>
            
            <TabsContent value="models" className="space-y-4">
              {Object.entries(analytics.usage_by_model).map(([model, usage]) => (
                <div key={model} className="flex items-center justify-between p-3 border rounded">
                  <span className="font-medium">{model}</span>
                  <Badge variant="secondary">{usage.toLocaleString()} tokens</Badge>
                </div>
              ))}
            </TabsContent>
            
            <TabsContent value="daily" className="space-y-4">
              {Object.entries(analytics.daily_usage).map(([date, usage]) => (
                <div key={date} className="flex items-center justify-between p-3 border rounded">
                  <span className="font-medium">{date}</span>
                  <Badge variant="secondary">{usage.toLocaleString()} tokens</Badge>
                </div>
              ))}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export const ClaudiaMainDashboard: React.FC = () => {
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8">Claudia 集成控制台</h1>
      
      <Tabs defaultValue="projects" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="projects">项目管理</TabsTrigger>
          <TabsTrigger value="servers">MCP服务器</TabsTrigger>
          <TabsTrigger value="analytics">使用分析</TabsTrigger>
        </TabsList>
        
        <TabsContent value="projects">
          <ClaudiaProjectBrowser />
        </TabsContent>
        
        <TabsContent value="servers">
          <ClaudiaMCPServerManager />
        </TabsContent>
        
        <TabsContent value="analytics">
          <ClaudiaUsageAnalytics />
        </TabsContent>
      </Tabs>
    </div>
  );
};

// WebSocket通信辅助函数
const sendWebSocketMessage = async (message: any): Promise<any> => {
  return new Promise((resolve, reject) => {
    // 这里应该使用实际的WebSocket连接
    // 示例实现
    const ws = new WebSocket('ws://localhost:8765');
    
    ws.onopen = () => {
      ws.send(JSON.stringify(message));
    };
    
    ws.onmessage = (event) => {
      const response = JSON.parse(event.data);
      resolve(response);
      ws.close();
    };
    
    ws.onerror = (error) => {
      reject(error);
      ws.close();
    };
  });
};
```

## 🎯 **整合效果预期**

### 📊 **技术指标**
- **界面响应时间**: <200ms (Claudia级别)
- **项目加载速度**: <500ms
- **MCP服务器连接**: <1秒
- **使用分析更新**: 实时

### 👥 **用户体验**
- **熟悉的界面**: Claudia用户零学习成本
- **无缝集成**: Claude Code项目直接导入
- **实时协作**: WebUI MCP的实时功能
- **智能管理**: MCP服务器自动发现和管理

### 🚀 **商业价值**
- **用户迁移**: Claudia用户平滑迁移到PowerAutomation
- **功能增强**: 在Claudia基础上增加MCP协作能力
- **生态融合**: Claude Code生态与PowerAutomation生态融合
- **竞争优势**: 业界首个Claudia + MCP的完整解决方案

这个整合方案将使PowerAutomation 4.0成为Claude Code用户的最佳选择，同时为现有用户提供熟悉而强大的界面体验！🎨

