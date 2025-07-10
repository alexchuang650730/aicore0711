# VSCode擴展三欄式佈局優化方案

## 🎨 設計分析與優化

基於提供的三欄式UI設計，我們可以將其完美適配到VSCode擴展中，創造出色的用戶體驗。

---

## 📐 三欄式佈局適配方案

### 原設計分析
```
[左側仪表盘 300px] | [中間工作區 flex:1] | [右側聊天區 350px]
     ↓                      ↓                    ↓
  項目狀態監控           文件處理中心            AI對話界面
  統計數據顯示           拖放操作區域            實時交互助手
  快速操作按鈕           文件列表管理            輸入輸出窗口
```

### VSCode擴展適配版本
```
[項目儀表盤] | [代碼編輯增強] | [AI助手面板]
     ↓              ↓              ↓
  項目狀態          代碼分析         聊天界面
  Git狀態          智能建議         任務執行
  測試結果          重構工具         結果展示
  任務追蹤          調試輔助         配置管理
```

---

## 🚀 VSCode擴展WebView實現

### 1. 主要WebView Provider改進

**RepositoryProvider.ts (左側儀表盤)**
```typescript
export class RepositoryProvider implements vscode.WebviewViewProvider {
    private _getHtmlForWebview(webview: vscode.Webview) {
        return `<!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>PowerAutomation Project Dashboard</title>
            <style>
                /* 基於原設計的VSCode主題適配 */
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }

                body {
                    font-family: var(--vscode-font-family);
                    background: var(--vscode-sideBar-background);
                    color: var(--vscode-sideBar-foreground);
                    padding: 12px;
                    overflow-y: auto;
                }

                .dashboard-header {
                    display: flex;
                    align-items: center;
                    margin-bottom: 16px;
                    padding-bottom: 8px;
                    border-bottom: 1px solid var(--vscode-panel-border);
                }

                .dashboard-title {
                    font-size: 13px;
                    font-weight: 600;
                    margin-left: 8px;
                }

                .status-section {
                    margin-bottom: 20px;
                }

                .section-title {
                    font-size: 11px;
                    font-weight: 600;
                    margin-bottom: 8px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    color: var(--vscode-descriptionForeground);
                }

                .status-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 6px 8px;
                    margin-bottom: 4px;
                    background: var(--vscode-input-background);
                    border-radius: 3px;
                    border-left: 2px solid var(--vscode-focusBorder);
                    font-size: 11px;
                }

                .status-value {
                    font-weight: 600;
                }

                .status-positive {
                    color: var(--vscode-terminal-ansiGreen);
                }

                .status-warning {
                    color: var(--vscode-terminal-ansiYellow);
                }

                .status-error {
                    color: var(--vscode-terminal-ansiRed);
                }

                .action-button {
                    width: 100%;
                    padding: 8px 10px;
                    margin-bottom: 6px;
                    background: var(--vscode-button-background);
                    border: none;
                    border-radius: 3px;
                    color: var(--vscode-button-foreground);
                    font-size: 11px;
                    cursor: pointer;
                    transition: background-color 0.2s;
                }

                .action-button:hover {
                    background: var(--vscode-button-hoverBackground);
                }

                .action-button.secondary {
                    background: var(--vscode-button-secondaryBackground);
                    color: var(--vscode-button-secondaryForeground);
                }

                .action-button.secondary:hover {
                    background: var(--vscode-button-secondaryHoverBackground);
                }

                .stats-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 6px;
                    margin-bottom: 12px;
                }

                .stat-card {
                    background: var(--vscode-input-background);
                    padding: 8px;
                    border-radius: 3px;
                    text-align: center;
                    border: 1px solid var(--vscode-input-border);
                }

                .stat-number {
                    font-size: 14px;
                    font-weight: 700;
                    color: var(--vscode-terminal-ansiGreen);
                    display: block;
                }

                .stat-label {
                    font-size: 9px;
                    color: var(--vscode-descriptionForeground);
                    margin-top: 2px;
                }

                .activity-item {
                    display: flex;
                    align-items: center;
                    padding: 6px 8px;
                    margin-bottom: 4px;
                    background: var(--vscode-list-inactiveSelectionBackground);
                    border-radius: 3px;
                    font-size: 11px;
                }

                .activity-icon {
                    margin-right: 8px;
                    width: 16px;
                    text-align: center;
                }

                .activity-content {
                    flex: 1;
                }

                .activity-name {
                    font-weight: 500;
                    margin-bottom: 1px;
                }

                .activity-status {
                    font-size: 10px;
                    color: var(--vscode-descriptionForeground);
                }
            </style>
        </head>
        <body>
            <div class="dashboard-header">
                <span>🤖</span>
                <div class="dashboard-title">PowerAutomation</div>
            </div>

            <!-- 項目狀態 -->
            <div class="status-section">
                <div class="section-title">📊 項目狀態</div>
                <div class="status-item">
                    <span>🔥 代碼質量</span>
                    <span class="status-value status-positive">A+</span>
                </div>
                <div class="status-item">
                    <span>🧪 測試覆蓋</span>
                    <span class="status-value status-positive">87%</span>
                </div>
                <div class="status-item">
                    <span>🐛 已知問題</span>
                    <span class="status-value status-warning">3</span>
                </div>
                <div class="status-item">
                    <span>⚡ AI狀態</span>
                    <span class="status-value status-positive">就緒</span>
                </div>
            </div>

            <!-- 統計數據 -->
            <div class="status-section">
                <div class="section-title">📈 今日統計</div>
                <div class="stats-grid">
                    <div class="stat-card">
                        <span class="stat-number">42</span>
                        <div class="stat-label">代碼提交</div>
                    </div>
                    <div class="stat-card">
                        <span class="stat-number">156</span>
                        <div class="stat-label">AI建議</div>
                    </div>
                    <div class="stat-card">
                        <span class="stat-number">2.3s</span>
                        <div class="stat-label">平均響應</div>
                    </div>
                    <div class="stat-card">
                        <span class="stat-number">98%</span>
                        <div class="stat-label">成功率</div>
                    </div>
                </div>
            </div>

            <!-- 快速操作 -->
            <div class="status-section">
                <div class="section-title">🚀 快速操作</div>
                <button class="action-button" onclick="executeAction('analyze')">
                    🔍 代碼分析
                </button>
                <button class="action-button" onclick="executeAction('refactor')">
                    🛠️ 智能重構
                </button>
                <button class="action-button secondary" onclick="executeAction('test')">
                    🧪 運行測試
                </button>
                <button class="action-button secondary" onclick="executeAction('debug')">
                    🐛 調試助手
                </button>
                <button class="action-button secondary" onclick="executeAction('sync')">
                    🔄 同步狀態
                </button>
            </div>

            <!-- 最近活動 -->
            <div class="status-section">
                <div class="section-title">📋 最近活動</div>
                <div class="activity-item">
                    <span class="activity-icon">📄</span>
                    <div class="activity-content">
                        <div class="activity-name">main.ts</div>
                        <div class="activity-status">AI重構完成</div>
                    </div>
                </div>
                <div class="activity-item">
                    <span class="activity-icon">🧪</span>
                    <div class="activity-content">
                        <div class="activity-name">test-suite</div>
                        <div class="activity-status">測試通過 87%</div>
                    </div>
                </div>
                <div class="activity-item">
                    <span class="activity-icon">🔍</span>
                    <div class="activity-content">
                        <div class="activity-name">utils.js</div>
                        <div class="activity-status">代碼分析中</div>
                    </div>
                </div>
            </div>

            <script>
                const vscode = acquireVsCodeApi();
                
                function executeAction(action) {
                    vscode.postMessage({
                        type: 'executeAction',
                        action: action
                    });
                }

                // 接收來自擴展的狀態更新
                window.addEventListener('message', event => {
                    const message = event.data;
                    switch (message.type) {
                        case 'updateStatus':
                            updateProjectStatus(message.data);
                            break;
                        case 'updateStats':
                            updateStats(message.data);
                            break;
                        case 'updateActivity':
                            addActivityItem(message.data);
                            break;
                    }
                });

                function updateProjectStatus(status) {
                    // 更新項目狀態顯示
                }

                function updateStats(stats) {
                    // 更新統計數據
                }

                function addActivityItem(activity) {
                    // 添加新的活動項目
                }
            </script>
        </body>
        </html>`;
    }
}
```

### 2. 中間代碼增強區域

**CodeEnhancementProvider.ts (中間面板)**
```typescript
export class CodeEnhancementProvider implements vscode.WebviewViewProvider {
    private _getHtmlForWebview(webview: vscode.Webview) {
        return `<!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    background: var(--vscode-editor-background);
                    color: var(--vscode-editor-foreground);
                    padding: 0;
                    margin: 0;
                    height: 100vh;
                    display: flex;
                    flex-direction: column;
                }

                .enhancement-header {
                    padding: 12px 16px;
                    background: var(--vscode-titleBar-activeBackground);
                    border-bottom: 1px solid var(--vscode-panel-border);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }

                .enhancement-title {
                    font-size: 13px;
                    font-weight: 600;
                }

                .status-indicator {
                    font-size: 10px;
                    padding: 2px 6px;
                    border-radius: 3px;
                    background: var(--vscode-badge-background);
                    color: var(--vscode-badge-foreground);
                }

                .enhancement-area {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    padding: 16px;
                }

                .suggestion-zone {
                    border: 2px dashed var(--vscode-input-border);
                    border-radius: 6px;
                    padding: 40px 20px;
                    text-align: center;
                    margin-bottom: 16px;
                    transition: all 0.3s ease;
                    min-height: 200px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                }

                .suggestion-zone.active {
                    border-color: var(--vscode-focusBorder);
                    background: var(--vscode-input-background);
                }

                .suggestion-icon {
                    font-size: 32px;
                    margin-bottom: 12px;
                    opacity: 0.6;
                }

                .suggestion-text {
                    font-size: 14px;
                    margin-bottom: 8px;
                    color: var(--vscode-foreground);
                }

                .suggestion-subtext {
                    font-size: 11px;
                    color: var(--vscode-descriptionForeground);
                    margin-bottom: 16px;
                }

                .action-buttons {
                    display: flex;
                    gap: 8px;
                    flex-wrap: wrap;
                    justify-content: center;
                }

                .action-btn {
                    padding: 8px 12px;
                    background: var(--vscode-button-background);
                    border: none;
                    border-radius: 3px;
                    color: var(--vscode-button-foreground);
                    font-size: 11px;
                    cursor: pointer;
                    transition: background-color 0.2s;
                }

                .action-btn:hover {
                    background: var(--vscode-button-hoverBackground);
                }

                .action-btn.secondary {
                    background: var(--vscode-button-secondaryBackground);
                    color: var(--vscode-button-secondaryForeground);
                }

                .suggestions-list {
                    flex: 1;
                    overflow-y: auto;
                    background: var(--vscode-editor-background);
                    border-radius: 4px;
                    border: 1px solid var(--vscode-input-border);
                }

                .suggestion-item {
                    padding: 12px 16px;
                    border-bottom: 1px solid var(--vscode-input-border);
                    display: flex;
                    align-items: flex-start;
                    gap: 12px;
                }

                .suggestion-item:last-child {
                    border-bottom: none;
                }

                .suggestion-item:hover {
                    background: var(--vscode-list-hoverBackground);
                }

                .suggestion-item.selected {
                    background: var(--vscode-list-activeSelectionBackground);
                }

                .suggestion-type {
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    background: var(--vscode-badge-background);
                    color: var(--vscode-badge-foreground);
                    font-size: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-shrink: 0;
                    margin-top: 2px;
                }

                .suggestion-content {
                    flex: 1;
                }

                .suggestion-title {
                    font-size: 12px;
                    font-weight: 500;
                    margin-bottom: 4px;
                }

                .suggestion-description {
                    font-size: 11px;
                    color: var(--vscode-descriptionForeground);
                    line-height: 1.4;
                    margin-bottom: 6px;
                }

                .suggestion-actions {
                    display: flex;
                    gap: 6px;
                }

                .suggestion-action {
                    padding: 2px 6px;
                    background: var(--vscode-input-background);
                    border: 1px solid var(--vscode-input-border);
                    border-radius: 2px;
                    color: var(--vscode-foreground);
                    font-size: 9px;
                    cursor: pointer;
                    text-decoration: none;
                }

                .suggestion-action:hover {
                    background: var(--vscode-list-hoverBackground);
                }

                .enhancement-footer {
                    padding: 12px 16px;
                    background: var(--vscode-statusBar-background);
                    border-top: 1px solid var(--vscode-panel-border);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: 11px;
                    color: var(--vscode-statusBar-foreground);
                }

                .footer-stats {
                    display: flex;
                    gap: 16px;
                }
            </style>
        </head>
        <body>
            <div class="enhancement-header">
                <div class="enhancement-title">🧠 代碼增強中心</div>
                <div class="status-indicator">智能分析中</div>
            </div>

            <div class="enhancement-area">
                <div class="suggestion-zone" id="suggestionZone">
                    <div class="suggestion-icon">💡</div>
                    <div class="suggestion-text">選擇代碼獲取AI建議</div>
                    <div class="suggestion-subtext">支持重構、優化、調試、測試生成等功能</div>
                    <div class="action-buttons">
                        <button class="action-btn" onclick="analyzeSelection()">
                            🔍 分析選中代碼
                        </button>
                        <button class="action-btn secondary" onclick="analyzeFile()">
                            📄 分析整個文件
                        </button>
                        <button class="action-btn secondary" onclick="generateTests()">
                            🧪 生成測試
                        </button>
                    </div>
                </div>

                <div class="suggestions-list" id="suggestionsList" style="display: none;">
                    <!-- 動態生成的建議列表 -->
                </div>
            </div>

            <div class="enhancement-footer">
                <div class="footer-stats">
                    <span>📊 今日分析: <strong>42</strong></span>
                    <span>⚡ 平均耗時: <strong>1.2s</strong></span>
                    <span>✨ 建議採用率: <strong>78%</strong></span>
                </div>
                <div>🤖 PowerAutomation AI</div>
            </div>

            <script>
                const vscode = acquireVsCodeApi();

                function analyzeSelection() {
                    vscode.postMessage({
                        type: 'analyzeSelection'
                    });
                    showAnalyzing();
                }

                function analyzeFile() {
                    vscode.postMessage({
                        type: 'analyzeFile'
                    });
                    showAnalyzing();
                }

                function generateTests() {
                    vscode.postMessage({
                        type: 'generateTests'
                    });
                    showAnalyzing();
                }

                function showAnalyzing() {
                    const zone = document.getElementById('suggestionZone');
                    zone.classList.add('active');
                    zone.innerHTML = \`
                        <div class="suggestion-icon">⏳</div>
                        <div class="suggestion-text">AI正在分析代碼...</div>
                        <div class="suggestion-subtext">請稍候，這通常需要1-3秒</div>
                    \`;
                }

                function showSuggestions(suggestions) {
                    const zone = document.getElementById('suggestionZone');
                    const list = document.getElementById('suggestionsList');
                    
                    zone.style.display = 'none';
                    list.style.display = 'block';
                    
                    list.innerHTML = suggestions.map(suggestion => \`
                        <div class="suggestion-item" onclick="selectSuggestion('\${suggestion.id}')">
                            <div class="suggestion-type">\${suggestion.icon}</div>
                            <div class="suggestion-content">
                                <div class="suggestion-title">\${suggestion.title}</div>
                                <div class="suggestion-description">\${suggestion.description}</div>
                                <div class="suggestion-actions">
                                    <button class="suggestion-action" onclick="applySuggestion('\${suggestion.id}')">
                                        應用
                                    </button>
                                    <button class="suggestion-action" onclick="previewSuggestion('\${suggestion.id}')">
                                        預覽
                                    </button>
                                    <button class="suggestion-action" onclick="dismissSuggestion('\${suggestion.id}')">
                                        忽略
                                    </button>
                                </div>
                            </div>
                        </div>
                    \`).join('');
                }

                function applySuggestion(id) {
                    vscode.postMessage({
                        type: 'applySuggestion',
                        suggestionId: id
                    });
                }

                function previewSuggestion(id) {
                    vscode.postMessage({
                        type: 'previewSuggestion',
                        suggestionId: id
                    });
                }

                // 接收來自擴展的消息
                window.addEventListener('message', event => {
                    const message = event.data;
                    switch (message.type) {
                        case 'showSuggestions':
                            showSuggestions(message.suggestions);
                            break;
                        case 'analysisComplete':
                            updateStatus(message.status);
                            break;
                        case 'resetView':
                            resetToInitialState();
                            break;
                    }
                });

                function resetToInitialState() {
                    document.getElementById('suggestionZone').style.display = 'flex';
                    document.getElementById('suggestionsList').style.display = 'none';
                    document.getElementById('suggestionZone').classList.remove('active');
                }
            </script>
        </body>
        </html>`;
    }
}
```

### 3. 右側AI聊天面板改進

**ChatProvider.ts (右側面板) - 增強版**
```typescript
// 在之前的基礎上，添加更豐富的交互功能和視覺效果
private _getHtmlForWebview(webview: vscode.Webview) {
    return `<!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <style>
            /* 使用原設計的聊天樣式，但適配VSCode主題 */
            body {
                font-family: var(--vscode-font-family);
                background: var(--vscode-sideBar-background);
                color: var(--vscode-sideBar-foreground);
                margin: 0;
                padding: 0;
                height: 100vh;
                display: flex;
                flex-direction: column;
            }

            .chat-header {
                padding: 12px 16px;
                background: var(--vscode-titleBar-activeBackground);
                border-bottom: 1px solid var(--vscode-panel-border);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .chat-title {
                font-size: 13px;
                font-weight: 600;
            }

            .chat-status {
                font-size: 10px;
                background: var(--vscode-badge-background);
                color: var(--vscode-badge-foreground);
                padding: 2px 6px;
                border-radius: 3px;
            }

            .chat-messages {
                flex: 1;
                padding: 12px;
                overflow-y: auto;
                scroll-behavior: smooth;
            }

            .message {
                margin-bottom: 12px;
                display: flex;
                flex-direction: column;
            }

            .message.user {
                align-items: flex-end;
            }

            .message.assistant {
                align-items: flex-start;
            }

            .message-content {
                max-width: 85%;
                padding: 8px 12px;
                border-radius: 8px;
                font-size: 12px;
                line-height: 1.4;
                word-wrap: break-word;
            }

            .message.user .message-content {
                background: var(--vscode-button-background);
                color: var(--vscode-button-foreground);
                border-bottom-right-radius: 3px;
            }

            .message.assistant .message-content {
                background: var(--vscode-input-background);
                color: var(--vscode-input-foreground);
                border: 1px solid var(--vscode-input-border);
                border-bottom-left-radius: 3px;
            }

            .message-time {
                font-size: 9px;
                color: var(--vscode-descriptionForeground);
                margin-top: 2px;
                padding: 0 4px;
            }

            .message-actions {
                display: flex;
                gap: 4px;
                margin-top: 4px;
                opacity: 0;
                transition: opacity 0.2s;
            }

            .message:hover .message-actions {
                opacity: 1;
            }

            .message-action {
                padding: 2px 4px;
                background: var(--vscode-button-secondaryBackground);
                border: none;
                border-radius: 2px;
                color: var(--vscode-button-secondaryForeground);
                font-size: 9px;
                cursor: pointer;
            }

            .chat-input-area {
                padding: 12px;
                background: var(--vscode-input-background);
                border-top: 1px solid var(--vscode-panel-border);
            }

            .chat-input {
                width: 100%;
                padding: 8px 10px;
                background: var(--vscode-input-background);
                border: 1px solid var(--vscode-input-border);
                border-radius: 4px;
                color: var(--vscode-input-foreground);
                font-size: 12px;
                resize: none;
                min-height: 48px;
                max-height: 120px;
                font-family: var(--vscode-font-family);
            }

            .chat-input:focus {
                outline: none;
                border-color: var(--vscode-focusBorder);
            }

            .chat-actions {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 8px;
            }

            .input-actions {
                display: flex;
                gap: 4px;
            }

            .input-action {
                padding: 4px 6px;
                background: var(--vscode-button-secondaryBackground);
                border: none;
                border-radius: 2px;
                color: var(--vscode-button-secondaryForeground);
                font-size: 10px;
                cursor: pointer;
                transition: background-color 0.2s;
            }

            .input-action:hover {
                background: var(--vscode-button-secondaryHoverBackground);
            }

            .send-button {
                padding: 6px 12px;
                background: var(--vscode-button-background);
                border: none;
                border-radius: 3px;
                color: var(--vscode-button-foreground);
                font-size: 11px;
                cursor: pointer;
                transition: background-color 0.2s;
            }

            .send-button:hover {
                background: var(--vscode-button-hoverBackground);
            }

            .send-button:disabled {
                background: var(--vscode-button-secondaryBackground);
                color: var(--vscode-button-secondaryForeground);
                cursor: not-allowed;
            }

            .typing-indicator {
                display: none;
                align-items: center;
                gap: 4px;
                padding: 8px 12px;
                background: var(--vscode-input-background);
                border-radius: 8px;
                border-bottom-left-radius: 3px;
                margin-bottom: 12px;
                max-width: 85%;
            }

            .typing-dots {
                display: flex;
                gap: 2px;
            }

            .typing-dot {
                width: 4px;
                height: 4px;
                background: var(--vscode-descriptionForeground);
                border-radius: 50%;
                animation: typingAnimation 1.4s infinite;
            }

            .typing-dot:nth-child(2) {
                animation-delay: 0.2s;
            }

            .typing-dot:nth-child(3) {
                animation-delay: 0.4s;
            }

            @keyframes typingAnimation {
                0%, 60%, 100% {
                    opacity: 0.3;
                }
                30% {
                    opacity: 1;
                }
            }

            .quick-actions {
                display: flex;
                flex-wrap: wrap;
                gap: 4px;
                margin-bottom: 8px;
            }

            .quick-action {
                padding: 4px 8px;
                background: var(--vscode-button-secondaryBackground);
                border: none;
                border-radius: 12px;
                color: var(--vscode-button-secondaryForeground);
                font-size: 10px;
                cursor: pointer;
                transition: all 0.2s;
            }

            .quick-action:hover {
                background: var(--vscode-button-secondaryHoverBackground);
                transform: scale(1.02);
            }
        </style>
    </head>
    <body>
        <div class="chat-header">
            <div class="chat-title">💬 AI編程助手</div>
            <div class="chat-status" id="chatStatus">在線</div>
        </div>

        <div class="chat-messages" id="chatMessages">
            <div class="message assistant">
                <div class="message-content">
                    👋 您好！我是PowerAutomation AI助手。我可以幫您：<br>
                    • 🔍 分析和重構代碼<br>
                    • 🧪 生成測試用例<br>
                    • 🐛 調試和優化<br>
                    • 📚 解釋代碼邏輯<br><br>
                    請選擇代碼或輸入您的需求！
                </div>
                <div class="message-time">剛剛</div>
            </div>
        </div>

        <div class="typing-indicator" id="typingIndicator">
            <span>🤔</span>
            <span>AI正在思考</span>
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>

        <div class="chat-input-area">
            <div class="quick-actions">
                <button class="quick-action" onclick="sendQuickMessage('分析選中代碼')">
                    🔍 分析代碼
                </button>
                <button class="quick-action" onclick="sendQuickMessage('重構這段代碼')">
                    🛠️ 重構
                </button>
                <button class="quick-action" onclick="sendQuickMessage('生成測試用例')">
                    🧪 生成測試
                </button>
                <button class="quick-action" onclick="sendQuickMessage('解釋代碼邏輯')">
                    📚 解釋
                </button>
            </div>
            
            <textarea class="chat-input" id="chatInput" 
                      placeholder="輸入您的問題或選擇代碼後點擊快速操作..."></textarea>
            
            <div class="chat-actions">
                <div class="input-actions">
                    <button class="input-action" onclick="attachFile()" title="附加文件">📎</button>
                    <button class="input-action" onclick="insertCodeSnippet()" title="插入代碼">💻</button>
                    <button class="input-action" onclick="clearChat()" title="清除對話">🗑️</button>
                </div>
                <button class="send-button" id="sendButton" onclick="sendMessage()">
                    發送
                </button>
            </div>
        </div>

        <script>
            const vscode = acquireVsCodeApi();
            
            function sendMessage() {
                const input = document.getElementById('chatInput');
                const message = input.value.trim();
                if (!message) return;

                addUserMessage(message);
                input.value = '';
                showTyping();

                vscode.postMessage({
                    type: 'sendMessage',
                    message: message
                });
            }

            function sendQuickMessage(message) {
                addUserMessage(message);
                showTyping();

                vscode.postMessage({
                    type: 'sendMessage',
                    message: message
                });
            }

            function addUserMessage(message) {
                const messagesContainer = document.getElementById('chatMessages');
                const messageElement = document.createElement('div');
                messageElement.className = 'message user';
                messageElement.innerHTML = \`
                    <div class="message-content">\${message}</div>
                    <div class="message-time">\${new Date().toLocaleTimeString()}</div>
                \`;
                messagesContainer.appendChild(messageElement);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }

            function addAssistantMessage(message) {
                hideTyping();
                const messagesContainer = document.getElementById('chatMessages');
                const messageElement = document.createElement('div');
                messageElement.className = 'message assistant';
                messageElement.innerHTML = \`
                    <div class="message-content">\${message}</div>
                    <div class="message-time">\${new Date().toLocaleTimeString()}</div>
                    <div class="message-actions">
                        <button class="message-action" onclick="copyMessage(this)">📋</button>
                        <button class="message-action" onclick="applyCode(this)">✅</button>
                    </div>
                \`;
                messagesContainer.appendChild(messageElement);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }

            function showTyping() {
                document.getElementById('typingIndicator').style.display = 'flex';
                document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight;
            }

            function hideTyping() {
                document.getElementById('typingIndicator').style.display = 'none';
            }

            // 接收來自擴展的消息
            window.addEventListener('message', event => {
                const message = event.data;
                switch (message.type) {
                    case 'aiResponse':
                        addAssistantMessage(message.content);
                        break;
                    case 'updateStatus':
                        document.getElementById('chatStatus').textContent = message.status;
                        break;
                    case 'clearMessages':
                        clearChat();
                        break;
                }
            });

            // 鍵盤事件
            document.getElementById('chatInput').addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });

            function clearChat() {
                const messagesContainer = document.getElementById('chatMessages');
                messagesContainer.innerHTML = \`
                    <div class="message assistant">
                        <div class="message-content">對話已清除。有什麼我可以幫助您的嗎？</div>
                        <div class="message-time">\${new Date().toLocaleTimeString()}</div>
                    </div>
                \`;
            }
        </script>
    </body>
    </html>`;
}
```

---

## 📊 三欄式佈局的優勢

### 1. **信息密度優化**
- 左側：專注於狀態監控和快速操作
- 中間：主要工作區域，代碼增強功能
- 右側：AI交互，即時獲得幫助

### 2. **工作流程順暢**
```
查看狀態 → 選擇代碼 → 獲取建議 → AI對話 → 應用改進
   ↓           ↓          ↓         ↓        ↓
 左側面板    中間編輯器    中間面板   右側聊天   回到編輯器
```

### 3. **VSCode原生體驗**
- 完全遵循VSCode設計語言
- 使用VSCode主題系統
- 響應式設計適配不同螢幕

### 4. **高效的空間利用**
- 300px左側面板：足夠顯示重要信息
- flex:1中間區域：最大化編輯空間
- 350px右側面板：適合對話和交互

---

## 🎯 實施建議

1. **第一階段**：實現基礎三欄佈局
2. **第二階段**：添加智能交互功能
3. **第三階段**：完善視覺效果和動畫

這個三欄式設計將為VSCode用戶提供前所未有的AI編程體驗！