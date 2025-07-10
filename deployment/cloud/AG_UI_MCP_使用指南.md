# AG-UI MCP 使用指南

## 🎯 概述

AG-UI MCP是PowerAutomation 4.1中集成的智能体-用户交互协议服务，基于AG-UI (4.8k⭐) 开源协议标准，提供标准化的智能体与前端应用连接方式。

## 🏗️ 核心组件

### 1. **AGUIProtocolAdapter** - 协议适配器
负责AG-UI协议的解析、验证和标准化处理。

### 2. **AGUIInteractionManager** - 交互管理器
管理智能体与用户界面之间的交互会话和状态。

### 3. **AGUIComponentGenerator** - UI组件生成器
动态生成用户界面组件，支持生成式UI。

### 4. **AGUIEventHandler** - 事件处理器
处理智能体和用户界面之间的事件通信。

### 5. **AGUIStateManager** - 状态管理器
管理交互状态、会话持久化和上下文同步。

## 🚀 快速开始

### 基础使用示例

```python
import asyncio
from core.components.ag_ui_mcp import (
    AGUIProtocolAdapter,
    AGUIInteractionManager,
    AGUIComponentGenerator,
    AGUIEventHandler
)

async def basic_usage_example():
    """基础使用示例"""
    
    # 1. 初始化AG-UI组件
    protocol_adapter = AGUIProtocolAdapter()
    interaction_manager = AGUIInteractionManager()
    component_generator = AGUIComponentGenerator()
    event_handler = AGUIEventHandler()
    
    # 2. 创建智能体会话
    session = await interaction_manager.create_session(
        agent_id="claude_assistant",
        user_id="user_123",
        session_config={
            "mode": "streaming",
            "ui_theme": "dark",
            "language": "zh-CN"
        }
    )
    
    # 3. 发送消息给智能体
    message = await protocol_adapter.create_message(
        message_type="user_input",
        content="请帮我分析这段代码",
        metadata={
            "code": "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
            "language": "python"
        }
    )
    
    # 4. 处理智能体响应
    response = await interaction_manager.send_message(session.session_id, message)
    
    # 5. 生成动态UI组件
    ui_component = await component_generator.generate_component(
        component_type="code_analysis_panel",
        data=response.content,
        style_config={
            "theme": "vscode_dark",
            "highlight": True,
            "interactive": True
        }
    )
    
    print(f"会话ID: {session.session_id}")
    print(f"智能体响应: {response.content}")
    print(f"生成的UI组件: {ui_component.component_id}")

# 运行示例
asyncio.run(basic_usage_example())
```

## 📋 详细使用方法

### 1. 协议适配器使用

```python
from core.components.ag_ui_mcp import AGUIProtocolAdapter

async def protocol_adapter_example():
    """协议适配器使用示例"""
    
    adapter = AGUIProtocolAdapter()
    
    # 创建不同类型的消息
    
    # 文本消息
    text_message = await adapter.create_message(
        message_type="text",
        content="Hello from agent!",
        metadata={"timestamp": "2025-01-07T10:30:00Z"}
    )
    
    # 结构化数据消息
    data_message = await adapter.create_message(
        message_type="structured_data",
        content={
            "type": "analysis_result",
            "data": {
                "complexity": "O(2^n)",
                "suggestions": ["使用动态规划优化", "添加缓存机制"]
            }
        }
    )
    
    # UI组件消息
    component_message = await adapter.create_message(
        message_type="ui_component",
        content={
            "component_type": "chart",
            "data": [1, 2, 3, 4, 5],
            "config": {"type": "line", "color": "#007acc"}
        }
    )
    
    # 验证消息格式
    is_valid = await adapter.validate_message(text_message)
    print(f"消息验证结果: {is_valid}")
```

### 2. 交互管理器使用

```python
from core.components.ag_ui_mcp import AGUIInteractionManager, AgentProfile

async def interaction_manager_example():
    """交互管理器使用示例"""
    
    manager = AGUIInteractionManager()
    
    # 注册智能体
    agent_profile = AgentProfile(
        agent_id="claude_assistant",
        name="Claude编程助手",
        capabilities=["code_analysis", "code_generation", "debugging"],
        supported_components=["text", "code_block", "chart", "form"],
        interaction_modes=["streaming", "synchronous"],
        max_concurrent_sessions=50,
        session_timeout=7200
    )
    
    await manager.register_agent(agent_profile)
    
    # 创建会话
    session = await manager.create_session(
        agent_id="claude_assistant",
        user_id="developer_001",
        session_config={
            "mode": "streaming",
            "context_window": 8000,
            "ui_preferences": {
                "theme": "dark",
                "language": "zh-CN",
                "code_highlighting": True
            }
        }
    )
    
    # 发送消息
    message = await manager.send_message(
        session_id=session.session_id,
        message={
            "type": "user_input",
            "content": "请优化这个函数",
            "context": {
                "code": "def slow_function(n): return sum(i for i in range(n))",
                "file_path": "/src/utils.py"
            }
        }
    )
    
    # 获取会话历史
    history = await manager.get_session_history(session.session_id)
    
    # 更新会话状态
    await manager.update_session_status(session.session_id, "active")
    
    print(f"活跃会话数: {len(await manager.get_active_sessions())}")
```

### 3. UI组件生成器使用

```python
from core.components.ag_ui_mcp import AGUIComponentGenerator

async def component_generator_example():
    """UI组件生成器使用示例"""
    
    generator = AGUIComponentGenerator()
    
    # 生成代码编辑器组件
    code_editor = await generator.generate_component(
        component_type="code_editor",
        data={
            "code": "def fibonacci(n):\n    return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
            "language": "python",
            "theme": "vscode_dark"
        },
        style_config={
            "width": "100%",
            "height": "400px",
            "show_line_numbers": True,
            "enable_autocomplete": True
        }
    )
    
    # 生成数据可视化组件
    chart_component = await generator.generate_component(
        component_type="chart",
        data={
            "type": "performance_chart",
            "datasets": [
                {"label": "响应时间", "data": [120, 95, 87, 102, 78]},
                {"label": "成功率", "data": [98, 99, 97, 99, 100]}
            ],
            "labels": ["周一", "周二", "周三", "周四", "周五"]
        },
        style_config={
            "chart_type": "line",
            "colors": ["#007acc", "#28a745"],
            "responsive": True
        }
    )
    
    # 生成表单组件
    form_component = await generator.generate_component(
        component_type="form",
        data={
            "title": "代码审查配置",
            "fields": [
                {"name": "language", "type": "select", "options": ["Python", "JavaScript", "TypeScript"]},
                {"name": "strict_mode", "type": "checkbox", "label": "严格模式"},
                {"name": "max_issues", "type": "number", "min": 1, "max": 100, "default": 10}
            ]
        },
        style_config={
            "layout": "vertical",
            "submit_button": "开始审查",
            "validation": True
        }
    )
    
    # 获取组件HTML
    html_output = await generator.render_component(code_editor)
    
    print(f"生成的组件: {code_editor.component_id}")
    print(f"组件类型: {code_editor.component_type}")
```

### 4. 事件处理器使用

```python
from core.components.ag_ui_mcp import AGUIEventHandler

async def event_handler_example():
    """事件处理器使用示例"""
    
    handler = AGUIEventHandler()
    
    # 注册事件监听器
    @handler.on("user_input")
    async def handle_user_input(event):
        print(f"收到用户输入: {event.data}")
        # 处理用户输入逻辑
        return {"status": "processed", "response": "输入已处理"}
    
    @handler.on("agent_response")
    async def handle_agent_response(event):
        print(f"智能体响应: {event.data}")
        # 更新UI显示
        return {"status": "ui_updated"}
    
    @handler.on("component_interaction")
    async def handle_component_interaction(event):
        print(f"组件交互: {event.data}")
        # 处理组件交互
        return {"status": "interaction_handled"}
    
    # 发射事件
    await handler.emit("user_input", {
        "message": "请分析这段代码",
        "context": {"file": "main.py", "line": 42}
    })
    
    # 批量处理事件
    events = [
        {"type": "user_input", "data": {"message": "Hello"}},
        {"type": "agent_response", "data": {"response": "Hi there!"}},
        {"type": "component_interaction", "data": {"action": "click", "target": "submit_btn"}}
    ]
    
    results = await handler.process_events(events)
    print(f"处理了 {len(results)} 个事件")
```

## 🔧 高级功能

### 1. 流式交互

```python
async def streaming_interaction_example():
    """流式交互示例"""
    
    manager = AGUIInteractionManager()
    
    # 创建流式会话
    session = await manager.create_session(
        agent_id="claude_assistant",
        user_id="user_123",
        session_config={"mode": "streaming"}
    )
    
    # 开始流式对话
    async for chunk in manager.stream_conversation(
        session_id=session.session_id,
        message="请详细解释这个算法的工作原理",
        context={"algorithm": "quicksort"}
    ):
        print(f"流式响应: {chunk.content}")
        # 实时更新UI
        await update_ui_with_chunk(chunk)
```

### 2. 批量处理

```python
async def batch_processing_example():
    """批量处理示例"""
    
    manager = AGUIInteractionManager()
    
    # 批量创建会话
    sessions = await manager.create_batch_sessions([
        {"agent_id": "claude_assistant", "user_id": "user_1"},
        {"agent_id": "gemini_assistant", "user_id": "user_2"},
        {"agent_id": "local_assistant", "user_id": "user_3"}
    ])
    
    # 批量发送消息
    messages = [
        {"session_id": sessions[0].session_id, "content": "分析代码A"},
        {"session_id": sessions[1].session_id, "content": "分析代码B"},
        {"session_id": sessions[2].session_id, "content": "分析代码C"}
    ]
    
    results = await manager.batch_send_messages(messages)
    
    for result in results:
        print(f"会话 {result.session_id}: {result.response}")
```

### 3. 自定义组件

```python
async def custom_component_example():
    """自定义组件示例"""
    
    generator = AGUIComponentGenerator()
    
    # 注册自定义组件类型
    await generator.register_component_type(
        component_type="ai_code_reviewer",
        template_path="/templates/ai_code_reviewer.html",
        script_path="/scripts/ai_code_reviewer.js",
        style_path="/styles/ai_code_reviewer.css"
    )
    
    # 生成自定义组件
    custom_component = await generator.generate_component(
        component_type="ai_code_reviewer",
        data={
            "code": "function example() { return 'hello'; }",
            "language": "javascript",
            "review_level": "strict"
        },
        style_config={
            "theme": "github_dark",
            "show_suggestions": True,
            "highlight_issues": True
        }
    )
    
    print(f"自定义组件ID: {custom_component.component_id}")
```

## 🔗 与其他MCP组件集成

### 1. 与MCP-Zero Smart Engine集成

```python
from core.components.mcp_zero_smart_engine import UnifiedToolManager
from core.components.ag_ui_mcp import AGUIInteractionManager

async def mcp_zero_integration_example():
    """与MCP-Zero Smart Engine集成"""
    
    tool_manager = UnifiedToolManager()
    ui_manager = AGUIInteractionManager()
    
    # 发现可用工具
    tools = await tool_manager.discover_tools()
    
    # 为每个工具生成UI组件
    for tool in tools:
        ui_component = await ui_manager.generate_tool_interface(
            tool_id=tool.id,
            tool_config=tool.config,
            ui_style="modern_card"
        )
        
        print(f"为工具 {tool.name} 生成了UI组件: {ui_component.component_id}")
```

### 2. 与Stagewise MCP集成

```python
from core.components.stagewise_mcp import StagewiseRecorderMCP
from core.components.ag_ui_mcp import AGUIEventHandler

async def stagewise_integration_example():
    """与Stagewise MCP集成"""
    
    stagewise = StagewiseRecorderMCP()
    event_handler = AGUIEventHandler()
    
    # 监听UI交互事件并录制
    @event_handler.on("component_interaction")
    async def record_interaction(event):
        await stagewise.record_step(
            stage="user_interaction",
            action_type=event.data.get("action", "unknown"),
            target=event.data.get("target", ""),
            take_screenshot=True
        )
    
    # 开始录制会话
    recording_id = await stagewise.start_recording("ag_ui_session", ["user_interaction"])
    
    print(f"开始录制AG-UI交互: {recording_id}")
```

## 📊 监控和分析

### 1. 性能监控

```python
async def performance_monitoring_example():
    """性能监控示例"""
    
    manager = AGUIInteractionManager()
    
    # 获取性能统计
    stats = await manager.get_performance_stats()
    
    print(f"活跃会话数: {stats['active_sessions']}")
    print(f"平均响应时间: {stats['avg_response_time']}ms")
    print(f"消息处理率: {stats['message_throughput']}/s")
    print(f"错误率: {stats['error_rate']}%")
    
    # 获取详细分析
    analysis = await manager.analyze_interaction_patterns()
    
    print(f"最常用的组件类型: {analysis['popular_components']}")
    print(f"用户交互热点: {analysis['interaction_hotspots']}")
```

### 2. 会话分析

```python
async def session_analysis_example():
    """会话分析示例"""
    
    manager = AGUIInteractionManager()
    
    # 分析特定会话
    session_id = "session_123"
    analysis = await manager.analyze_session(session_id)
    
    print(f"会话时长: {analysis['duration']}秒")
    print(f"消息数量: {analysis['message_count']}")
    print(f"组件使用: {analysis['component_usage']}")
    print(f"用户满意度: {analysis['satisfaction_score']}")
    
    # 导出会话数据
    session_data = await manager.export_session_data(
        session_id=session_id,
        format="json",
        include_components=True
    )
    
    print(f"会话数据已导出: {len(session_data)} 字节")
```

## 🛠️ 配置和自定义

### 1. 配置文件示例

```json
{
  "ag_ui_mcp": {
    "protocol_version": "1.0",
    "default_interaction_mode": "streaming",
    "session_timeout": 3600,
    "max_concurrent_sessions": 100,
    "ui_themes": {
      "default": "modern_light",
      "available": ["modern_light", "modern_dark", "classic", "minimal"]
    },
    "component_config": {
      "code_editor": {
        "default_theme": "vscode_dark",
        "supported_languages": ["python", "javascript", "typescript", "java", "cpp"],
        "features": ["autocomplete", "syntax_highlighting", "error_detection"]
      },
      "chart": {
        "default_type": "line",
        "supported_types": ["line", "bar", "pie", "scatter", "area"],
        "max_data_points": 1000
      }
    },
    "event_config": {
      "max_event_queue_size": 1000,
      "event_timeout": 30,
      "retry_attempts": 3
    }
  }
}
```

### 2. 环境变量配置

```bash
# AG-UI MCP配置
export AGUI_MCP_HOST=0.0.0.0
export AGUI_MCP_PORT=8080
export AGUI_MCP_DEBUG=true
export AGUI_MCP_LOG_LEVEL=INFO

# 会话配置
export AGUI_SESSION_TIMEOUT=3600
export AGUI_MAX_SESSIONS=100
export AGUI_SESSION_CLEANUP_INTERVAL=300

# UI配置
export AGUI_DEFAULT_THEME=modern_dark
export AGUI_COMPONENT_CACHE_SIZE=500
export AGUI_ENABLE_ANIMATIONS=true
```

## 🚀 部署和集成

### 1. 独立服务部署

```python
# ag_ui_mcp_server.py
from flask import Flask, request, jsonify
from core.components.ag_ui_mcp import AGUIInteractionManager

app = Flask(__name__)
manager = AGUIInteractionManager()

@app.route('/api/ag-ui/session', methods=['POST'])
async def create_session():
    data = request.json
    session = await manager.create_session(
        agent_id=data['agent_id'],
        user_id=data['user_id'],
        session_config=data.get('config', {})
    )
    return jsonify({"session_id": session.session_id})

@app.route('/api/ag-ui/message', methods=['POST'])
async def send_message():
    data = request.json
    response = await manager.send_message(
        session_id=data['session_id'],
        message=data['message']
    )
    return jsonify({"response": response.content})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

### 2. 前端集成示例

```javascript
// ag-ui-client.js
class AGUIClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.sessionId = null;
    }
    
    async createSession(agentId, userId, config = {}) {
        const response = await fetch(`${this.baseUrl}/api/ag-ui/session`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                agent_id: agentId,
                user_id: userId,
                config: config
            })
        });
        
        const data = await response.json();
        this.sessionId = data.session_id;
        return this.sessionId;
    }
    
    async sendMessage(message) {
        const response = await fetch(`${this.baseUrl}/api/ag-ui/message`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                session_id: this.sessionId,
                message: message
            })
        });
        
        return await response.json();
    }
}

// 使用示例
const client = new AGUIClient('http://localhost:8080');
await client.createSession('claude_assistant', 'user_123');
const response = await client.sendMessage({
    type: 'user_input',
    content: '请帮我分析这段代码'
});
console.log(response);
```

## 📚 最佳实践

### 1. 性能优化
- 使用连接池管理会话
- 实现组件缓存机制
- 优化事件处理队列
- 定期清理过期会话

### 2. 安全考虑
- 验证用户输入
- 实现会话认证
- 限制并发连接数
- 记录安全审计日志

### 3. 用户体验
- 提供流畅的实时交互
- 实现优雅的错误处理
- 支持多语言界面
- 优化移动端体验

### 4. 可维护性
- 模块化组件设计
- 完善的日志记录
- 全面的单元测试
- 详细的API文档

AG-UI MCP为ClaudEditor 4.1提供了标准化的智能体交互能力，是实现现代AI应用用户界面的重要基础设施。

