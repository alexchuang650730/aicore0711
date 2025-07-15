# PowerAutomation NPM 包生態系統 v4.6.9.7

## 📦 包結構

### 核心包系列
- `@powerautomation/core` - 核心功能包
- `@powerautomation/claude-editor-mobile` - 移動端編輯器
- `@powerautomation/claude-editor-desktop` - 桌面端編輯器
- `@powerautomation/enterprise-cli` - 企業版CLI工具
- `@powerautomation/feishu-integration` - 飛書深度集成
- `@powerautomation/payment-system` - 統一支付系統
- `@powerautomation/k2-router` - K2智能路由

### 安裝方式

#### 1. 一鍵安裝（推薦）
```bash
# curl 方式
curl -fsSL https://raw.githubusercontent.com/alexchuang650730/aicore0711/main/install-script-macos-v4.6.9.7.sh | bash

# npm 方式
npm install -g @powerautomation/installer
powerautomation install
```

#### 2. 分包安裝
```bash
# 核心包
npm install @powerautomation/core

# 移動端編輯器
npm install @powerautomation/claude-editor-mobile

# 桌面端編輯器
npm install @powerautomation/claude-editor-desktop

# 企業版CLI
npm install @powerautomation/enterprise-cli

# 飛書集成
npm install @powerautomation/feishu-integration
```

## 🚀 快速開始

### 基礎使用
```javascript
const { PowerAutomation } = require('@powerautomation/core');

const pa = new PowerAutomation({
  version: 'personal', // community, personal, enterprise
  k2Provider: 'infini-ai-cloud', // infini-ai-cloud, moonshot-official
  features: {
    feishu: true,
    payment: true,
    mobile: true
  }
});

// 初始化
await pa.initialize();

// 使用K2服務
const response = await pa.k2.chat('Hello, world!');
console.log(response);
```

### 飛書集成
```javascript
const { FeishuIntegration } = require('@powerautomation/feishu-integration');

const feishu = new FeishuIntegration({
  appId: 'your-feishu-app-id',
  appSecret: 'your-feishu-app-secret',
  powerAutomationToken: 'your-pa-token'
});

// 飛書購買流程
await feishu.initiatePurchase({
  version: 'personal',
  userId: 'feishu-user-id',
  redirectUrl: 'https://your-app.com/callback'
});
```

## 💳 支付系統集成

### 支持的支付方式
- **微信支付** - 中國大陸用戶
- **支付寶** - 中國大陸用戶
- **PayPal** - 海外用戶
- **Stripe** - 國際信用卡
- **企業對公轉賬** - 企業用戶
- **飛書內購** - 飛書用戶專屬

### 支付系統使用
```javascript
const { PaymentSystem } = require('@powerautomation/payment-system');

const payment = new PaymentSystem({
  apiKey: 'your-api-key',
  environment: 'production' // production, sandbox
});

// 創建支付訂單
const order = await payment.createOrder({
  amount: 100,
  currency: 'CNY',
  method: 'wechat', // wechat, alipay, paypal, stripe, bank_transfer
  credits: 100,
  version: 'personal'
});

// 處理支付結果
payment.on('payment_success', (data) => {
  console.log('Payment successful:', data);
});
```

## 📱 移動端編輯器

### 安裝和使用
```bash
npm install @powerautomation/claude-editor-mobile
```

```javascript
const { MobileEditor } = require('@powerautomation/claude-editor-mobile');

const editor = new MobileEditor({
  container: '#editor-container',
  theme: 'auto', // light, dark, auto
  responsive: true,
  features: {
    smartui: true,
    gestures: true,
    offline: true
  }
});

// 初始化編輯器
await editor.initialize();

// 集成K2服務
editor.setK2Provider('infini-ai-cloud');

// 移動端優化
editor.enableMobileOptimizations();
```

## 🖥️ 桌面端編輯器

### 安裝和使用
```bash
npm install @powerautomation/claude-editor-desktop
```

```javascript
const { DesktopEditor } = require('@powerautomation/claude-editor-desktop');

const editor = new DesktopEditor({
  window: {
    width: 1200,
    height: 800,
    resizable: true
  },
  features: {
    multiWindow: true,
    nativeMenus: true,
    fileSystem: true
  }
});

// 啟動桌面應用
await editor.launch();
```

## 🏢 企業版CLI工具

### 安裝
```bash
npm install -g @powerautomation/enterprise-cli
```

### 使用
```bash
# 初始化企業環境
pa-enterprise init --company "Your Company" --license "your-license-key"

# 部署到私有服務器
pa-enterprise deploy --target private-cloud

# 用戶管理
pa-enterprise users add --email user@company.com --role admin

# 批量許可證管理
pa-enterprise licenses bulk-generate --count 100 --type team
```

## 🔗 飛書深度集成

### 特色功能
- **飛書單點登錄** - 企業級SSO
- **飛書群組管理** - 智能群組助手
- **飛書審批流程** - 自動化審批
- **飛書日曆集成** - 智能提醒
- **飛書文檔協作** - 實時同步編輯
- **飛書會議記錄** - 自動化會議紀錄

### 飛書購買鏈接
```
https://applink.feishu.cn/client/message/link/open?token=AmfoKtFagQATaHK7JJIAQAI%3D
```

### 飛書小程序集成
```javascript
const { FeishuMiniProgram } = require('@powerautomation/feishu-integration');

const miniProgram = new FeishuMiniProgram({
  appId: 'your-mini-program-id',
  appSecret: 'your-mini-program-secret'
});

// 初始化小程序
await miniProgram.initialize();

// 處理支付
miniProgram.on('payment_request', async (data) => {
  const paymentResult = await miniProgram.processPayment({
    userId: data.userId,
    amount: data.amount,
    version: data.version
  });
  
  return paymentResult;
});
```

## 🎯 版本管理

### 版本對比
| 功能 | Community | Personal | Team | Enterprise |
|------|-----------|----------|------|------------|
| 基礎AI功能 | ✅ | ✅ | ✅ | ✅ |
| K2模型 | 有限 | 無限 | 無限 | 無限 |
| 移動端支持 | ❌ | ✅ | ✅ | ✅ |
| 飛書集成 | ❌ | 基礎 | 完整 | 完整 |
| 團隊協作 | ❌ | ❌ | ✅ | ✅ |
| 企業SSO | ❌ | ❌ | ❌ | ✅ |
| 私有部署 | ❌ | ❌ | ❌ | ✅ |
| 技術支持 | 社區 | 標準 | 優先 | 專屬 |

### 價格體系
- **Community版**: 免費
- **Personal版**: 100積分/月
- **Team版**: 300積分/月 (最多10人)
- **Enterprise版**: 800積分/月 (無限人數)

## 🛠️ 開發者工具

### 本地開發
```bash
# 克隆開發環境
git clone https://github.com/alexchuang650730/aicore0711.git
cd aicore0711

# 安裝依賴
npm install

# 啟動開發服務
npm run dev

# 構建生產版本
npm run build
```

### 自定義集成
```javascript
const { Plugin } = require('@powerautomation/core');

class CustomPlugin extends Plugin {
  constructor(options) {
    super(options);
    this.name = 'custom-plugin';
  }
  
  async initialize() {
    // 插件初始化邏輯
  }
  
  async execute(input) {
    // 插件執行邏輯
    return { success: true, data: input };
  }
}

// 註冊插件
PowerAutomation.registerPlugin(CustomPlugin);
```

## 📊 監控和分析

### 使用統計
```javascript
const { Analytics } = require('@powerautomation/core');

const analytics = new Analytics({
  apiKey: 'your-analytics-key',
  userId: 'user-id'
});

// 追蹤事件
analytics.track('k2_request', {
  provider: 'infini-ai-cloud',
  tokens: 150,
  credits: 1
});

// 獲取統計數據
const stats = await analytics.getStats('daily');
```

### 性能監控
```javascript
const { Performance } = require('@powerautomation/core');

const perf = new Performance();

// 監控API響應時間
perf.monitor('k2_api', async () => {
  return await k2.chat('Hello');
});

// 獲取性能報告
const report = await perf.getReport();
```

## 🔒 安全和合規

### 數據加密
- **傳輸加密**: TLS 1.3
- **存儲加密**: AES-256
- **密鑰管理**: 硬件安全模塊

### 合規認證
- **SOC 2 Type II**
- **ISO 27001**
- **GDPR 合規**
- **CCPA 合規**

## 📞 技術支持

### 支持渠道
- **GitHub Issues**: https://github.com/alexchuang650730/aicore0711/issues
- **官方文檔**: https://powerauto.aiweb.com/docs
- **社區論壇**: https://powerauto.aiweb.com/community
- **企業支持**: enterprise@powerauto.com

### 服務等級協議 (SLA)
- **Community版**: 社區支持
- **Personal版**: 24小時響應
- **Team版**: 12小時響應
- **Enterprise版**: 4小時響應，99.9%可用性

---

**版本**: v4.6.9.7  
**更新時間**: 2025-07-15  
**NPM包**: https://www.npmjs.com/org/powerautomation