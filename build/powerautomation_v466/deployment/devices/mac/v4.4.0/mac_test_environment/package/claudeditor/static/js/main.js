// ClaudEditor v4.1 主JavaScript文件

class ClaudEditorApp {
    constructor() {
        this.ws = null;
        this.editor = null;
        this.currentPanel = 'editor';
        this.isRecording = false;
        
        this.init();
    }
    
    async init() {
        console.log('初始化ClaudEditor v4.1...');
        
        // 初始化WebSocket连接
        this.initWebSocket();
        
        // 初始化Monaco编辑器
        await this.initMonacoEditor();
        
        // 初始化事件监听器
        this.initEventListeners();
        
        // 加载初始数据
        await this.loadInitialData();
        
        console.log('ClaudEditor v4.1初始化完成');
    }
    
    initWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket连接已建立');
            this.updateStatus('已连接', 'connected');
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket连接已断开');
            this.updateStatus('连接断开', 'disconnected');
            
            // 尝试重连
            setTimeout(() => {
                this.initWebSocket();
            }, 3000);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket错误:', error);
            this.updateStatus('连接错误', 'error');
        };
    }
    
    async initMonacoEditor() {
        return new Promise((resolve) => {
            require.config({ 
                paths: { 
                    'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' 
                }
            });
            
            require(['vs/editor/editor.main'], () => {
                this.editor = monaco.editor.create(document.getElementById('monaco-editor'), {
                    value: `// 欢迎使用ClaudEditor v4.1
// 这是一个集成了AI助手、记忆系统和智能工具的代码编辑器

function helloClaudEditor() {
    console.log("Hello, ClaudEditor v4.1!");
    console.log("AI协作开发神器已就绪");
}

helloClaudEditor();`,
                    language: 'javascript',
                    theme: 'vs-dark',
                    fontSize: 14,
                    minimap: { enabled: true },
                    automaticLayout: true,
                    wordWrap: 'on',
                    lineNumbers: 'on',
                    folding: true,
                    autoClosingBrackets: 'always',
                    autoClosingQuotes: 'always',
                    formatOnPaste: true,
                    formatOnType: true
                });
                
                // 监听编辑器内容变化
                this.editor.onDidChangeModelContent(() => {
                    this.onEditorContentChange();
                });
                
                resolve();
            });
        });
    }
    
    initEventListeners() {
        // 导航切换
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const tab = e.currentTarget.dataset.tab;
                this.switchPanel(tab);
            });
        });
        
        // 语言选择
        document.getElementById('language-select').addEventListener('change', (e) => {
            const language = e.target.value;
            monaco.editor.setModelLanguage(this.editor.getModel(), language);
        });
        
        // 格式化代码
        document.getElementById('format-code').addEventListener('click', () => {
            this.editor.getAction('editor.action.formatDocument').run();
        });
        
        // 保存文件
        document.getElementById('save-file').addEventListener('click', () => {
            this.saveFile();
        });
        
        // AI聊天
        document.getElementById('send-message').addEventListener('click', () => {
            this.sendAIMessage();
        });
        
        document.getElementById('chat-input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendAIMessage();
            }
        });
        
        // 记忆搜索
        document.getElementById('search-memory').addEventListener('click', () => {
            this.searchMemory();
        });
        
        document.getElementById('memory-search-input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.searchMemory();
            }
        });
        
        // 工具管理
        document.getElementById('refresh-tools').addEventListener('click', () => {
            this.loadMCPTools();
        });
        
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const category = e.target.dataset.category;
                this.filterTools(category);
            });
        });
        
        // Stagewise录制
        document.getElementById('start-recording').addEventListener('click', () => {
            this.startStagewiseRecording();
        });
        
        document.getElementById('stop-recording').addEventListener('click', () => {
            this.stopStagewiseRecording();
        });
    }
    
    async loadInitialData() {
        try {
            // 加载系统状态
            await this.loadSystemStatus();
            
            // 加载MCP工具
            await this.loadMCPTools();
            
            // 加载记忆统计
            await this.loadMemoryStats();
            
        } catch (error) {
            console.error('加载初始数据失败:', error);
        }
    }
    
    switchPanel(panelName) {
        // 更新导航状态
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-tab="${panelName}"]`).classList.add('active');
        
        // 切换面板
        document.querySelectorAll('.panel').forEach(panel => {
            panel.classList.remove('active');
        });
        document.getElementById(`${panelName}-panel`).classList.add('active');
        
        this.currentPanel = panelName;
        
        // 如果切换到编辑器面板，重新布局Monaco编辑器
        if (panelName === 'editor' && this.editor) {
            setTimeout(() => {
                this.editor.layout();
            }, 100);
        }
    }
    
    updateStatus(text, status) {
        const indicator = document.getElementById('status-indicator');
        const span = indicator.querySelector('span');
        const icon = indicator.querySelector('i');
        
        span.textContent = text;
        
        // 移除所有状态类
        icon.classList.remove('connected', 'disconnected', 'error');
        
        // 添加新状态类
        if (status === 'connected') {
            icon.style.color = '#4caf50';
        } else if (status === 'disconnected') {
            icon.style.color = '#ff9800';
        } else if (status === 'error') {
            icon.style.color = '#f44336';
        }
    }
    
    async loadSystemStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            // 更新性能指标
            document.getElementById('system-status').textContent = data.status === 'running' ? '正常' : '异常';
            
        } catch (error) {
            console.error('加载系统状态失败:', error);
        }
    }
    
    async loadMCPTools() {
        try {
            const response = await fetch('/api/mcp/tools');
            const data = await response.json();
            
            // 更新工具统计
            document.getElementById('tools-count').textContent = data.count;
            document.getElementById('active-tools-count').textContent = data.tools.filter(t => t.status === 'active').length;
            
            // 渲染工具列表
            this.renderToolsList(data.tools);
            
        } catch (error) {
            console.error('加载MCP工具失败:', error);
        }
    }
    
    renderToolsList(tools) {
        const container = document.getElementById('tools-list');
        container.innerHTML = '';
        
        tools.forEach(tool => {
            const toolElement = document.createElement('div');
            toolElement.className = 'tool-item';
            toolElement.innerHTML = `
                <div class="tool-header">
                    <span class="tool-name">${tool.name}</span>
                    <div class="tool-status ${tool.status === 'active' ? '' : 'inactive'}"></div>
                </div>
                <div class="tool-description">${tool.description || '暂无描述'}</div>
                <div class="tool-actions">
                    <button class="btn btn-sm" onclick="app.executeTool('${tool.name}')">
                        <i class="fas fa-play"></i>
                        执行
                    </button>
                    <button class="btn btn-sm" onclick="app.configTool('${tool.name}')">
                        <i class="fas fa-cog"></i>
                        配置
                    </button>
                </div>
            `;
            container.appendChild(toolElement);
        });
    }
    
    async loadMemoryStats() {
        try {
            // 这里应该调用实际的API获取记忆统计
            // 暂时使用模拟数据
            document.getElementById('short-term-count').textContent = '12';
            document.getElementById('medium-term-count').textContent = '8';
            document.getElementById('long-term-count').textContent = '25';
            
        } catch (error) {
            console.error('加载记忆统计失败:', error);
        }
    }
    
    async sendAIMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        // 添加用户消息到聊天界面
        this.addChatMessage('user', message);
        
        // 清空输入框
        input.value = '';
        
        try {
            // 发送消息到后端
            const response = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    model: document.getElementById('ai-model-select').value
                })
            });
            
            const data = await response.json();
            
            // 添加AI回复到聊天界面
            this.addChatMessage('assistant', data.response);
            
        } catch (error) {
            console.error('发送AI消息失败:', error);
            this.addChatMessage('assistant', '抱歉，发生了错误，请稍后重试。');
        }
    }
    
    addChatMessage(role, content) {
        const messagesContainer = document.getElementById('chat-messages');
        
        const messageElement = document.createElement('div');
        messageElement.className = `message ${role}`;
        messageElement.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-${role === 'user' ? 'user' : 'robot'}"></i>
            </div>
            <div class="message-content">
                <p>${content}</p>
            </div>
        `;
        
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    async searchMemory() {
        const query = document.getElementById('memory-search-input').value.trim();
        
        if (!query) return;
        
        try {
            const response = await fetch(`/api/memory/search?query=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            this.renderMemoryList(data.memories);
            
        } catch (error) {
            console.error('搜索记忆失败:', error);
        }
    }
    
    renderMemoryList(memories) {
        const container = document.getElementById('memory-list');
        container.innerHTML = '';
        
        memories.forEach(memory => {
            const memoryElement = document.createElement('div');
            memoryElement.className = 'memory-item';
            memoryElement.innerHTML = `
                <div class="memory-item-header">
                    <span class="memory-type">${memory.type}</span>
                    <span class="memory-timestamp">${new Date(memory.timestamp).toLocaleString()}</span>
                </div>
                <div class="memory-content">${memory.content}</div>
            `;
            container.appendChild(memoryElement);
        });
    }
    
    filterTools(category) {
        // 更新过滤按钮状态
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-category="${category}"]`).classList.add('active');
        
        // 过滤工具列表
        const tools = document.querySelectorAll('.tool-item');
        tools.forEach(tool => {
            if (category === 'all') {
                tool.style.display = 'block';
            } else {
                // 这里应该根据实际的工具分类进行过滤
                tool.style.display = 'block';
            }
        });
    }
    
    async startStagewiseRecording() {
        try {
            const response = await fetch('/api/stagewise/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: 'default_user',
                    project_id: 'default_project'
                })
            });
            
            const data = await response.json();
            
            this.isRecording = true;
            this.updateRecordingStatus('录制中', true);
            
            document.getElementById('start-recording').disabled = true;
            document.getElementById('stop-recording').disabled = false;
            
        } catch (error) {
            console.error('启动Stagewise录制失败:', error);
        }
    }
    
    stopStagewiseRecording() {
        this.isRecording = false;
        this.updateRecordingStatus('未录制', false);
        
        document.getElementById('start-recording').disabled = false;
        document.getElementById('stop-recording').disabled = true;
    }
    
    updateRecordingStatus(text, isRecording) {
        const status = document.getElementById('recording-status');
        const span = status.querySelector('span');
        const icon = status.querySelector('i');
        
        span.textContent = text;
        
        if (isRecording) {
            icon.style.color = '#f44336';
            icon.classList.add('pulse');
        } else {
            icon.style.color = '#888';
            icon.classList.remove('pulse');
        }
    }
    
    onEditorContentChange() {
        // 如果正在录制，可以在这里记录代码变化
        if (this.isRecording) {
            // 记录编辑器内容变化
        }
    }
    
    saveFile() {
        const content = this.editor.getValue();
        const language = this.editor.getModel().getLanguageId();
        
        // 创建下载链接
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `code.${this.getFileExtension(language)}`;
        a.click();
        URL.revokeObjectURL(url);
    }
    
    getFileExtension(language) {
        const extensions = {
            'javascript': 'js',
            'typescript': 'ts',
            'python': 'py',
            'html': 'html',
            'css': 'css',
            'json': 'json'
        };
        return extensions[language] || 'txt';
    }
    
    async executeTool(toolName) {
        try {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({
                    type: 'mcp_tool_execute',
                    tool_name: toolName,
                    parameters: {}
                }));
            }
        } catch (error) {
            console.error('执行工具失败:', error);
        }
    }
    
    configTool(toolName) {
        // 打开工具配置对话框
        alert(`配置工具: ${toolName}`);
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'mcp_tool_result':
                console.log('工具执行结果:', data.result);
                break;
            case 'memory_results':
                this.renderMemoryList(data.results);
                break;
            case 'ai_response':
                this.addChatMessage('assistant', data.response);
                break;
            default:
                console.log('未知WebSocket消息:', data);
        }
    }
}

// 初始化应用
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new ClaudEditorApp();
});

// 全局函数，供HTML调用
window.app = app;

