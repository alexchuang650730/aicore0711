# PowerAutomation VSCode 擴展實施計劃

## 📋 基於Trae Agent架構的VSCode深度整合方案

基於對 `https://github.com/alexchuang650730/aicore0624/tree/main/PowerAutomation_local/vscode-extension` 和 Trae Agent 的詳細分析，制定以下實施計劃。

---

## 🎯 核心架構設計

### 1. 擴展架構概覽

```
powerautomation-vscode/
├── package.json                    # 擴展配置和依賴管理
├── src/
│   ├── extension.ts                # 主入口點 - 生命周期管理
│   ├── providers/
│   │   ├── ChatProvider.ts         # AI聊天界面提供者
│   │   ├── RepositoryProvider.ts   # 項目管理儀表板
│   │   ├── TaskProvider.ts         # 任務管理界面
│   │   └── DebugProvider.ts        # 調試增強提供者
│   ├── services/
│   │   ├── MCPService.ts           # MCP協議通信服務
│   │   ├── TraeAgentService.ts     # Trae Agent集成服務
│   │   ├── CodeAnalysisService.ts  # 代碼分析服務
│   │   └── AutomationService.ts    # 自動化任務服務
│   ├── utils/
│   │   ├── TaskRouter.ts           # 智能任務路由
│   │   ├── ConfigManager.ts        # 配置管理
│   │   └── Logger.ts               # 日誌服務
│   └── webview/
│       ├── chat/                   # 聊天界面資源
│       ├── dashboard/              # 儀表板界面
│       └── shared/                 # 共享組件
└── out/                           # TypeScript編譯輸出
```

---

## 🚀 實施階段規劃

### 第一階段：基礎框架搭建 (2週)

#### 1.1 項目初始化
```bash
# 創建VSCode擴展項目
yo code

# 安裝核心依賴
npm install --save vscode
npm install --save-dev @types/vscode typescript webpack
```

#### 1.2 基礎架構實現

**package.json 配置**
```json
{
  "name": "powerautomation-kilocode",
  "displayName": "PowerAutomation KiloCode",
  "description": "AI-powered coding assistant with deep VSCode integration",
  "version": "1.0.0",
  "engines": {
    "vscode": "^1.85.0"
  },
  "categories": ["Other"],
  "activationEvents": [
    "onStartupFinished"
  ],
  "main": "./out/extension.js",
  "contributes": {
    "views": {
      "powerautomation": [
        {
          "id": "powerautomation.chat",
          "name": "AI Assistant",
          "type": "webview"
        },
        {
          "id": "powerautomation.repository", 
          "name": "Project Dashboard",
          "type": "webview"
        }
      ]
    },
    "viewsContainers": {
      "activitybar": [
        {
          "id": "powerautomation",
          "title": "PowerAutomation",
          "icon": "$(robot)"
        }
      ]
    },
    "commands": [
      {
        "command": "powerautomation.chat.send",
        "title": "Send Message to AI"
      },
      {
        "command": "powerautomation.automation.run",
        "title": "Run Automation Task"
      }
    ],
    "configuration": {
      "title": "PowerAutomation",
      "properties": {
        "powerautomation.apiEndpoint": {
          "type": "string",
          "default": "http://localhost:8080",
          "description": "PowerAutomation API端點"
        },
        "powerautomation.enableTraeAgent": {
          "type": "boolean", 
          "default": true,
          "description": "啟用Trae Agent集成"
        }
      }
    }
  }
}
```

**extension.ts 主入口實現**
```typescript
import * as vscode from 'vscode';
import { ChatProvider } from './providers/ChatProvider';
import { RepositoryProvider } from './providers/RepositoryProvider';
import { MCPService } from './services/MCPService';
import { TraeAgentService } from './services/TraeAgentService';
import { Logger } from './utils/Logger';

export function activate(context: vscode.ExtensionContext) {
    Logger.info('PowerAutomation extension activating...');
    
    // 初始化服務
    const mcpService = new MCPService();
    const traeAgentService = new TraeAgentService();
    
    // 註冊提供者
    const chatProvider = new ChatProvider(context.extensionUri, mcpService);
    const repositoryProvider = new RepositoryProvider(context.extensionUri, mcpService);
    
    // 註冊WebView提供者
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider('powerautomation.chat', chatProvider),
        vscode.window.registerWebviewViewProvider('powerautomation.repository', repositoryProvider)
    );
    
    // 註冊命令
    context.subscriptions.push(
        vscode.commands.registerCommand('powerautomation.chat.send', async () => {
            await chatProvider.handleSendMessage();
        }),
        vscode.commands.registerCommand('powerautomation.automation.run', async () => {
            await traeAgentService.runAutomationTask();
        })
    );
    
    Logger.info('PowerAutomation extension activated successfully');
}

export function deactivate() {
    Logger.info('PowerAutomation extension deactivated');
}
```

### 第二階段：核心服務實現 (3週)

#### 2.1 MCP通信服務

**MCPService.ts**
```typescript
import * as vscode from 'vscode';
import { Logger } from '../utils/Logger';

export interface MCPMessage {
    type: 'chat' | 'automation' | 'status';
    content: any;
    timestamp: number;
}

export class MCPService {
    private apiEndpoint: string;
    private websocket?: WebSocket;
    
    constructor() {
        this.apiEndpoint = vscode.workspace.getConfiguration('powerautomation').get('apiEndpoint', 'http://localhost:8080');
        this.initializeConnection();
    }
    
    private async initializeConnection() {
        try {
            // WebSocket連接到PowerAutomation後端
            const wsEndpoint = this.apiEndpoint.replace('http', 'ws') + '/mcp';
            this.websocket = new WebSocket(wsEndpoint);
            
            this.websocket.onopen = () => {
                Logger.info('MCP WebSocket連接已建立');
            };
            
            this.websocket.onmessage = (event) => {
                const message: MCPMessage = JSON.parse(event.data);
                this.handleMessage(message);
            };
            
            this.websocket.onerror = (error) => {
                Logger.error('MCP WebSocket錯誤:', error);
            };
            
        } catch (error) {
            Logger.error('初始化MCP連接失敗:', error);
        }
    }
    
    async sendMessage(message: MCPMessage): Promise<void> {
        if (this.websocket?.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(message));
        } else {
            throw new Error('MCP連接未建立');
        }
    }
    
    async sendChatMessage(content: string): Promise<any> {
        const message: MCPMessage = {
            type: 'chat',
            content: { text: content, context: this.getWorkspaceContext() },
            timestamp: Date.now()
        };
        
        return this.sendMessage(message);
    }
    
    private getWorkspaceContext() {
        const activeEditor = vscode.window.activeTextEditor;
        return {
            workspacePath: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath,
            activeFile: activeEditor?.document.uri.fsPath,
            selection: activeEditor?.selection,
            language: activeEditor?.document.languageId
        };
    }
    
    private handleMessage(message: MCPMessage) {
        switch (message.type) {
            case 'chat':
                // 處理聊天回應
                vscode.commands.executeCommand('powerautomation.chat.receive', message.content);
                break;
            case 'automation':
                // 處理自動化任務結果
                vscode.commands.executeCommand('powerautomation.automation.complete', message.content);
                break;
            default:
                Logger.warn('未知的MCP消息類型:', message.type);
        }
    }
}
```

#### 2.2 Trae Agent集成服務

**TraeAgentService.ts**
```typescript
import * as vscode from 'vscode';
import { exec } from 'child_process';
import { promisify } from 'util';
import { Logger } from '../utils/Logger';
import { TaskRouter } from '../utils/TaskRouter';

const execAsync = promisify(exec);

export interface TraeTask {
    type: 'code_analysis' | 'architecture_design' | 'debugging' | 'refactoring';
    input: string;
    context: any;
    options?: any;
}

export class TraeAgentService {
    private taskRouter: TaskRouter;
    private isTraeAvailable: boolean = false;
    
    constructor() {
        this.taskRouter = new TaskRouter();
        this.checkTraeAvailability();
    }
    
    private async checkTraeAvailability() {
        try {
            await execAsync('trae --version');
            this.isTraeAvailable = true;
            Logger.info('Trae Agent 可用');
        } catch (error) {
            this.isTraeAvailable = false;
            Logger.warn('Trae Agent 不可用，將使用備用方案');
        }
    }
    
    async executeTask(task: TraeTask): Promise<any> {
        if (!this.isTraeAvailable) {
            return this.executeFallbackTask(task);
        }
        
        try {
            // 構建Trae命令
            const command = this.buildTraeCommand(task);
            
            // 執行Trae任務
            const result = await execAsync(command, {
                cwd: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath
            });
            
            return {
                success: true,
                output: result.stdout,
                error: result.stderr,
                task_type: task.type
            };
            
        } catch (error) {
            Logger.error('Trae任務執行失敗:', error);
            return this.executeFallbackTask(task);
        }
    }
    
    private buildTraeCommand(task: TraeTask): string {
        const baseCommand = 'trae';
        
        switch (task.type) {
            case 'code_analysis':
                return `${baseCommand} analyze "${task.input}"`;
            case 'architecture_design':
                return `${baseCommand} design --input "${task.input}"`;
            case 'debugging':
                return `${baseCommand} debug --code "${task.input}"`;
            case 'refactoring':
                return `${baseCommand} refactor --target "${task.input}"`;
            default:
                return `${baseCommand} chat "${task.input}"`;
        }
    }
    
    private async executeFallbackTask(task: TraeTask): Promise<any> {
        // 備用方案：直接調用PowerAutomation API
        Logger.info('使用PowerAutomation備用方案執行任務');
        
        // 這裡可以調用PowerAutomation的API或其他AI服務
        return {
            success: true,
            output: `使用備用方案處理任務: ${task.type}`,
            task_type: task.type,
            fallback: true
        };
    }
    
    async runAutomationTask(): Promise<void> {
        const activeEditor = vscode.window.activeTextEditor;
        if (!activeEditor) {
            vscode.window.showWarningMessage('請先打開一個文件');
            return;
        }
        
        const selection = activeEditor.selection;
        const selectedText = activeEditor.document.getText(selection);
        
        if (!selectedText) {
            vscode.window.showWarningMessage('請先選擇要處理的代碼');
            return;
        }
        
        // 智能判斷任務類型
        const taskType = this.taskRouter.determineTaskType(selectedText, activeEditor.document);
        
        const task: TraeTask = {
            type: taskType,
            input: selectedText,
            context: {
                fileName: activeEditor.document.fileName,
                language: activeEditor.document.languageId,
                lineNumber: selection.start.line
            }
        };
        
        // 顯示進度指示器
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: '正在執行自動化任務...',
            cancellable: true
        }, async (progress) => {
            const result = await this.executeTask(task);
            
            if (result.success) {
                vscode.window.showInformationMessage('任務執行成功');
                // 可以選擇性地將結果應用到編輯器
                this.applyResult(result, activeEditor);
            } else {
                vscode.window.showErrorMessage('任務執行失敗');
            }
        });
    }
    
    private applyResult(result: any, editor: vscode.TextEditor) {
        // 根據任務類型決定如何應用結果
        if (result.task_type === 'refactoring' && result.output) {
            // 可以選擇性地替換選中的代碼
            vscode.window.showInformationMessage('重構建議已生成，請查看輸出');
        }
    }
}
```

### 第三階段：WebView界面實現 (2週)

#### 3.1 聊天界面提供者

**ChatProvider.ts**
```typescript
import * as vscode from 'vscode';
import { MCPService } from '../services/MCPService';
import { Logger } from '../utils/Logger';

export class ChatProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'powerautomation.chat';
    
    private _view?: vscode.WebviewView;
    private mcpService: MCPService;
    
    constructor(
        private readonly _extensionUri: vscode.Uri,
        mcpService: MCPService
    ) {
        this.mcpService = mcpService;
    }
    
    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;
        
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [
                this._extensionUri
            ]
        };
        
        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);
        
        // 處理來自WebView的消息
        webviewView.webview.onDidReceiveMessage(async (data) => {
            switch (data.type) {
                case 'sendMessage':
                    await this.handleSendMessage(data.message);
                    break;
                case 'clearChat':
                    await this.handleClearChat();
                    break;
            }
        });
    }
    
    private async handleSendMessage(message?: string) {
        if (!this._view) {
            return;
        }
        
        try {
            // 如果沒有提供消息，從當前編輯器獲取上下文
            if (!message) {
                const activeEditor = vscode.window.activeTextEditor;
                if (activeEditor && activeEditor.selection) {
                    message = activeEditor.document.getText(activeEditor.selection);
                }
            }
            
            if (!message) {
                vscode.window.showWarningMessage('請輸入消息或選擇代碼');
                return;
            }
            
            // 顯示用戶消息
            this._view.webview.postMessage({
                type: 'userMessage',
                message: message,
                timestamp: Date.now()
            });
            
            // 發送到MCP服務
            const response = await this.mcpService.sendChatMessage(message);
            
            // 顯示AI回應
            this._view.webview.postMessage({
                type: 'aiResponse',
                message: response,
                timestamp: Date.now()
            });
            
        } catch (error) {
            Logger.error('發送消息失敗:', error);
            vscode.window.showErrorMessage('發送消息失敗: ' + error);
        }
    }
    
    private async handleClearChat() {
        if (this._view) {
            this._view.webview.postMessage({
                type: 'clearMessages'
            });
        }
    }
    
    private _getHtmlForWebview(webview: vscode.Webview) {
        // 獲取資源URI
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'out', 'webview', 'chat', 'main.js'));
        const styleUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'out', 'webview', 'chat', 'main.css'));
        
        return `<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link href="${styleUri}" rel="stylesheet">
                <title>PowerAutomation AI Assistant</title>
            </head>
            <body>
                <div id="chat-container">
                    <div id="messages"></div>
                    <div id="input-container">
                        <textarea id="message-input" placeholder="輸入消息或選擇代碼後點擊發送..."></textarea>
                        <button id="send-button">發送</button>
                        <button id="clear-button">清除</button>
                    </div>
                </div>
                <script src="${scriptUri}"></script>
            </body>
            </html>`;
    }
}
```

---

## 📊 實施時間線

### 總體時間表：6週

| 階段 | 時間 | 主要任務 | 交付物 |
|------|------|----------|--------|
| 第一階段 | 第1-2週 | 基礎框架搭建 | 基礎擴展架構、配置文件 |
| 第二階段 | 第3-5週 | 核心服務實現 | MCP服務、Trae Agent集成 |
| 第三階段 | 第6週 | WebView界面實現 | 聊天界面、項目儀表板 |

### 里程碑檢查點

- **第2週末**: 基礎框架可運行，能夠激活擴展
- **第4週末**: 核心服務完成，能夠與PowerAutomation後端通信
- **第6週末**: 完整功能實現，可進行端到端測試

---

## 🔧 關鍵技術決策

### 1. 架構選擇
- **Provider模式**: 使用VSCode的WebView Provider模式實現界面
- **服務導向**: 將核心功能抽象為服務，便於測試和維護
- **模塊化設計**: 每個功能模塊獨立，便於逐步開發和測試

### 2. 通信機制
- **MCP協議**: 與PowerAutomation後端的標準通信方式
- **WebSocket**: 實時雙向通信，支持流式響應
- **命令系統**: 利用VSCode命令系統實現功能調用

### 3. Trae Agent集成
- **CLI調用**: 直接調用Trae命令行工具
- **備用方案**: 當Trae不可用時回退到PowerAutomation API
- **智能路由**: 根據任務類型選擇最佳處理方式

---

## 🎯 成功指標

### 功能指標
- [ ] VSCode擴展成功安裝和激活
- [ ] 聊天界面正常工作，能夠發送和接收消息
- [ ] 項目儀表板正確顯示項目信息
- [ ] Trae Agent集成功能正常

### 性能指標
- 擴展激活時間 < 2秒
- 消息響應時間 < 1秒
- 內存占用 < 50MB

### 用戶體驗指標
- 界面響應流暢，無明顯卡頓
- 錯誤處理完善，有清晰的錯誤提示
- 符合VSCode的設計規範和交互慣例

這個實施計劃基於對現有Trae Agent和PowerAutomation VSCode擴展的深入分析，提供了完整的技術路線圖和實施細節。