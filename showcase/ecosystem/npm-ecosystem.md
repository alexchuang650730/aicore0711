# 📦 PowerAutomation NPM 生態系統

PowerAutomation + ClaudeEditor 提供完整的 NPM 包生態系統，支持分級功能訪問，讓開發者可以根據許可證版本享受對應的功能集合。

---

## 🎯 NPM 包架構概覽

```mermaid
graph TB
    A[@powerautomation/core] --> B[基礎 MCP 組件]
    A --> C[工作流引擎]
    A --> D[許可證管理]
    
    E[@powerautomation/claude-editor-mobile] --> F[移動端編輯器]
    E --> G[跨平台同步]
    
    H[@powerautomation/claude-editor-desktop] --> I[桌面端編輯器]
    H --> J[CLI 集成]
    
    K[@powerautomation/enterprise-cli] --> L[統一 CLI 管理]
    K --> M[企業級工具]
```

---

## 📋 核心包詳解

### 🔧 @powerautomation/core

**核心功能包 - 所有版本必需**

```bash
npm install @powerautomation/core
```

#### 分級功能列表

| 功能模塊 | 個人版 | 專業版 | 團隊版 | 企業版 |
|---------|--------|--------|--------|--------|
| **MCP 組件** | 3個基礎 | 4個增強 | 8個高級 | 14個完整 |
| **工作流** | 2個基礎 | 4個標準 | 6個完整 | 7個+自定義 |
| **AI 模型** | 1個基礎 | 2個標準 | 3個高級 | 4個+私有 |
| **部署平台** | 1個本地 | 4個Web | 14個全部 | 無限制+自定義 |

#### 使用示例

```javascript
const { PowerAutomation } = require('@powerautomation/core');

// 初始化（自動根據許可證加載功能）
const pa = new PowerAutomation({
    license: 'PA-PROFESSIONAL-20241213-1234',
    workspace: './my-project'
});

// 獲取可用的 MCP 組件
const availableComponents = await pa.getMCPComponents();
console.log('可用組件:', availableComponents);
// 專業版輸出: ['codeflow', 'smartui', 'test', 'ag-ui']

// 使用 CodeFlow MCP 組件
const codeflow = pa.getMCP('codeflow');
const result = await codeflow.generateCode({
    prompt: '創建一個 React 登錄組件',
    framework: 'react',
    style: 'typescript'
});

// 執行工作流
const workflow = pa.getWorkflow('code_generation');
await workflow.execute({
    input: 'API端點設計',
    template: 'rest-api'
});
```

#### 配置文件

```yaml
# .powerautomation/config.yaml
core:
  license: "PA-PROFESSIONAL-20241213-1234"
  edition: "professional"
  
features:
  mcp_components:
    enabled: ['codeflow', 'smartui', 'test', 'ag-ui']
    access_level: 'standard'
  
  workflows:
    enabled: ['code_generation', 'ui_design', 'api_development', 'test_automation']
    custom_workflows: false
  
  ai_models:
    primary: 'claude_advanced'
    fallback: 'claude_basic'
    private_deployment: false
```

---

## 📱 移動端包

### @powerautomation/claude-editor-mobile

**移動端 ClaudeEditor 集成包**

```bash
npm install @powerautomation/claude-editor-mobile
```

#### 平台支持
- 📱 **React Native**: iOS 12+ / Android 8+
- 🌐 **Ionic**: 跨平台混合應用
- 📲 **Flutter**: Dart 集成 (實驗性)

#### 功能分級

```typescript
interface MobileEditorFeatures {
  personal: {
    editing: 'basic',
    sync: 'cloud_basic',
    offline: false,
    collaboration: false
  },
  professional: {
    editing: 'advanced',
    sync: 'real_time',
    offline: 'limited',
    collaboration: false,
    claude_integration: true
  },
  team: {
    editing: 'advanced',
    sync: 'real_time',
    offline: 'full',
    collaboration: true,
    version_control: true
  },
  enterprise: {
    editing: 'advanced',
    sync: 'enterprise_sync',
    offline: 'full',
    collaboration: true,
    version_control: true,
    security: 'enterprise_grade'
  }
}
```

#### React Native 集成示例

```javascript
// React Native 應用集成
import { PowerAutomationMobile } from '@powerautomation/claude-editor-mobile';

const App = () => {
  return (
    <PowerAutomationMobile 
      license="PA-TEAM-20241213-5678"
      features={{
        collaboration: true,
        realTimeSync: true,
        offlineMode: true
      }}
      onProjectLoad={(project) => {
        console.log('項目加載:', project.name);
      }}
      onCodeGenerated={(code) => {
        console.log('AI 生成代碼:', code);
      }}
    />
  );
};
```

---

## 💻 桌面端包

### @powerautomation/claude-editor-desktop

**桌面端 ClaudeEditor 集成包**

```bash
npm install @powerautomation/claude-editor-desktop
```

#### 桌面平台支持
- 🖥️ **Electron**: Windows 10+, macOS 10.14+, Ubuntu 18+
- 🌐 **Tauri**: 高性能 Rust 後端
- 💻 **Native**: 原生桌面應用 (企業版)

#### 核心功能

```typescript
interface DesktopEditorCapabilities {
  cliIntegration: {
    claudeCode: boolean;
    powerautomationCli: boolean;
    customCli: boolean; // 企業版
  };
  
  localAI: {
    enabled: boolean; // 企業版獨有
    models: string[];
    gpuAcceleration: boolean;
  };
  
  teamFeatures: {
    realTimeCollaboration: boolean;
    codeReview: boolean;
    projectSharing: boolean;
  };
  
  enterprise: {
    privateCloud: boolean;
    customBranding: boolean;
    auditLogging: boolean;
  };
}
```

#### Electron 應用集成

```javascript
// main.js - Electron 主進程
const { app, BrowserWindow } = require('electron');
const { PowerAutomationDesktop } = require('@powerautomation/claude-editor-desktop');

class PowerAutomationApp {
  constructor() {
    this.paDesktop = new PowerAutomationDesktop({
      license: process.env.PA_LICENSE,
      workspace: app.getPath('documents') + '/PowerAutomation'
    });
  }

  async initialize() {
    // 驗證許可證並加載功能
    await this.paDesktop.validateLicense();
    
    // 集成 Claude Code CLI
    await this.paDesktop.connectCLI('claude-code');
    
    // 設置本地 AI 模型 (企業版)
    if (this.paDesktop.edition === 'enterprise') {
      await this.paDesktop.setupLocalAI(['claude_local', 'kimi_k2']);
    }
    
    return this.createMainWindow();
  }

  createMainWindow() {
    const mainWindow = new BrowserWindow({
      width: 1200,
      height: 800,
      webPreferences: {
        nodeIntegration: true,
        contextIsolation: false
      }
    });

    // 加載 PowerAutomation 編輯器界面
    mainWindow.loadURL(this.paDesktop.getEditorURL());
    
    return mainWindow;
  }
}
```

---

## 🏢 企業級包

### @powerautomation/enterprise-cli

**企業版統一 CLI 工具包**

```bash
npm install @powerautomation/enterprise-cli
```

#### CLI 工具集成

```typescript
interface EnterpriseCliTools {
  claudeCode: {
    command: 'claude-code';
    features: ['generate', 'deploy', 'test', 'collaborate'];
    privateCloud: boolean;
  };
  
  gemini: {
    command: 'gemini-cli';
    features: ['analyze', 'multimodal', 'workspace-integration'];
    privateInstance: boolean;
  };
  
  powerautomation: {
    command: 'powerautomation-cli';
    features: ['workflow', 'deploy', 'monitor', 'manage'];
    customWorkflows: boolean;
  };
  
  kimiK2: {
    command: 'kimi-cli';
    features: ['local-inference', 'gpu-acceleration'];
    lanDeployment: boolean;
  };
  
  grok: {
    command: 'grok-cli'; 
    features: ['realtime-analysis', 'x-integration'];
    privateIntegration: boolean;
  };
}
```

#### 統一 CLI 管理

```bash
# 安裝企業 CLI 工具
npm install -g @powerautomation/enterprise-cli

# 初始化企業環境
pa-enterprise init --license "PA-ENTERPRISE-20241213-9999"

# 列出所有可用 CLI 工具
pa-enterprise list-tools
# ✅ claude-code: v2.1.0 (Connected)
# ✅ gemini-cli: v1.5.0 (Connected)  
# ✅ powerautomation-cli: v4.6.9 (Connected)
# ✅ kimi-cli: v1.0.0 (Local Deployment)
# ✅ grok-cli: v0.9.0 (Private Integration)

# 統一執行命令
pa-enterprise exec claude-code generate --template enterprise-api
pa-enterprise exec gemini analyze --multimodal --input project-docs/
pa-enterprise exec powerautomation workflow create --ai-models all

# 切換 AI 模型
pa-enterprise switch-model --from claude --to kimi-k2
pa-enterprise switch-model --from gemini --to grok --context realtime

# 企業級監控
pa-enterprise monitor --dashboard enterprise --alerts realtime
pa-enterprise audit-log --export json --period last-30-days
```

---

## 🔧 協作功能包

### @powerautomation/collaboration

**團隊協作功能包 (團隊版+)**

```bash
npm install @powerautomation/collaboration
```

#### 實時協作功能

```javascript
const { CollaborationService } = require('@powerautomation/collaboration');

// 初始化協作服務
const collab = new CollaborationService({
  projectId: 'project-123',
  userId: 'user-456',
  teamId: 'team-789'
});

// 加入協作會話
await collab.joinSession({
  onUserJoined: (user) => console.log(`${user.name} 加入協作`),
  onUserLeft: (user) => console.log(`${user.name} 離開協作`),
  onCodeChanged: (changes) => console.log('代碼變更:', changes),
  onCursorMoved: (cursor) => console.log('光標移動:', cursor)
});

// 實時代碼編輯
collab.on('text-change', (delta) => {
  // 應用文本變更
  editor.applyDelta(delta);
});

// 代碼審查
const review = await collab.createCodeReview({
  files: ['src/api.js', 'src/components.jsx'],
  reviewers: ['senior-dev-1', 'tech-lead-2'],
  description: '新功能代碼審查'
});

// 團隊聊天
collab.sendMessage({
  type: 'text',
  content: '這個 API 設計看起來不錯！',
  mentions: ['@tech-lead']
});
```

---

## 📊 使用統計與監控

### @powerautomation/analytics

**使用分析包 (專業版+)**

```javascript
const { Analytics } = require('@powerautomation/analytics');

const analytics = new Analytics({
  license: 'PA-PROFESSIONAL-20241213-1234',
  reportingLevel: 'detailed' // basic/detailed/enterprise
});

// 代碼生成統計
await analytics.track('code_generation', {
  language: 'javascript',
  framework: 'react',
  linesGenerated: 150,
  aiModel: 'claude_advanced'
});

// 部署統計
await analytics.track('deployment', {
  platform: 'vercel',
  buildTime: '45s',
  success: true
});

// 獲取使用報告
const report = await analytics.generateReport({
  period: 'last-30-days',
  metrics: ['code_generation', 'deployments', 'collaboration']
});

console.log('月度使用報告:', report);
```

---

## 🛠️ 開發者工具

### 版本檢查工具

```bash
# 檢查所有 PowerAutomation 包版本
npx @powerautomation/version-check

# 輸出示例:
# ✅ @powerautomation/core: v4.6.9 (最新)
# ✅ @powerautomation/claude-editor-desktop: v1.2.0 (最新)
# ⚠️ @powerautomation/collaboration: v1.1.0 (有更新 v1.1.2)
# ❌ @powerautomation/enterprise-cli: 未安裝
```

### 許可證驗證工具

```bash
# 驗證許可證有效性
npx @powerautomation/license-verify PA-PROFESSIONAL-20241213-1234

# 輸出示例:
# ✅ 許可證有效
# 📋 版本: Professional
# 📅 有效期至: 2025-12-13
# 👥 授權用戶: 5
# 🔧 可用功能: 4 MCP組件, 4 工作流
```

### 自動更新工具

```bash
# 自動更新所有 PowerAutomation 包
npx @powerautomation/auto-update

# 僅更新核心包
npx @powerautomation/auto-update --core-only

# 預覽更新 (不執行)
npx @powerautomation/auto-update --dry-run
```

---

## 📦 包管理最佳實踐

### 版本鎖定策略

```json
{
  "dependencies": {
    "@powerautomation/core": "~4.6.9",
    "@powerautomation/claude-editor-desktop": "^1.2.0",
    "@powerautomation/collaboration": "^1.1.0"
  },
  "powerautomation": {
    "license": "PA-PROFESSIONAL-20241213-1234",
    "autoUpdate": false,
    "features": {
      "collaboration": true,
      "analytics": true
    }
  }
}
```

### 環境變量配置

```bash
# .env
PA_LICENSE=PA-PROFESSIONAL-20241213-1234
PA_EDITION=professional
PA_WORKSPACE=/Users/dev/projects
PA_CLAUDE_CLI_PATH=/usr/local/bin/claude-code
PA_SYNC_ENABLED=true
PA_ANALYTICS_ENABLED=true
```

### TypeScript 支持

```typescript
// types/powerautomation.d.ts
declare module '@powerautomation/core' {
  export interface PowerAutomationConfig {
    license: string;
    edition: 'personal' | 'professional' | 'team' | 'enterprise';
    workspace?: string;
    features?: Partial<FeatureConfig>;
  }
  
  export class PowerAutomation {
    constructor(config: PowerAutomationConfig);
    getMCP(name: string): MCPComponent;
    getWorkflow(name: string): Workflow;
    validateLicense(): Promise<boolean>;
  }
}
```

---

## 🎯 總結

PowerAutomation NPM 生態系統提供：

1. **🔧 模塊化設計**: 按需安裝，減少項目體積
2. **📊 分級功能**: 許可證自動控制功能訪問
3. **🔄 無縫集成**: 與現有開發工具完美融合
4. **📱 跨平台支持**: Mobile/Desktop 統一 API
5. **🏢 企業級工具**: 完整的 CLI 工具集
6. **👥 協作友好**: 內置團隊協作功能
7. **📈 數據驅動**: 詳細的使用分析和監控

通過統一的 NPM 包管理，開發者可以輕鬆構建強大的 AI 輔助開發環境。