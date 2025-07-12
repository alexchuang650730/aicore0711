# 🚀 PowerAutomation + ClaudeEditor 快速開始指南

歡迎使用 PowerAutomation + ClaudeEditor 整合系統！本指南將幫助您在15分鐘內完成從購買到使用的完整流程。

---

## 📱 Step 1: 飛書購買與激活

### 🛒 飛書小程序購買流程

1. **點擊購買鏈接**
   ```
   https://applink.feishu.cn/client/message/link/open?token=AmfoKtFagQATaHK7JJIAQAI%3D
   ```

2. **選擇適合的版本**
   
   | 版本 | 價格 | 適用場景 | 推薦指數 |
   |------|------|----------|----------|
   | 🔰 個人版 | 免費 | 個人學習、小項目 | ⭐⭐⭐ |
   | 💼 專業版 | $39/月 | 專業開發者、小團隊 | ⭐⭐⭐⭐⭐ |
   | 👥 團隊版 | $129/月 | 中等團隊、協作需求 | ⭐⭐⭐⭐ |
   | 🏢 企業版 | $499/月 | 大型企業、私有雲 | ⭐⭐⭐⭐⭐ |

3. **完成支付**
   - 🇨🇳 中國用戶: 微信支付、支付寶
   - 🌍 國際用戶: PayPal、Stripe
   - 🏢 企業用戶: 對公轉帳

4. **獲取許可證**
   - 📬 飛書消息通知
   - 🔑 許可證密鑰: `PA-EDITION-YYYYMMDD-XXXX`
   - 📲 下載鏈接自動發送

---

## 📱 Step 2: Mobile ClaudeEditor 安裝

### iOS 安裝
```bash
# 方式1: 直接下載 (推薦)
點擊飛書消息中的 iOS 下載鏈接

# 方式2: App Store 搜索
搜索 "PowerAutomation ClaudeEditor"
```

### Android 安裝
```bash
# 方式1: 直接下載 (推薦)
點擊飛書消息中的 Android 下載鏈接

# 方式2: Google Play 搜索
搜索 "PowerAutomation ClaudeEditor"
```

### 首次配置
```yaml
1. 打開 ClaudeEditor Mobile
2. 輸入許可證密鑰: PA-EDITION-YYYYMMDD-XXXX
3. 綁定飛書賬號 (可選)
4. 選擇雲端同步設置
5. 完成初始化設置
```

---

## 💻 Step 3: Desktop ClaudeEditor 安裝

### Windows 安裝
```powershell
# 下載並運行安裝程序
PowerAutomation-ClaudeEditor-Setup.exe

# 或使用 Chocolatey
choco install powerautomation-claudeeditor
```

### macOS 安裝
```bash
# 下載 DMG 文件並安裝
open PowerAutomation-ClaudeEditor.dmg

# 或使用 Homebrew
brew install --cask powerautomation-claudeeditor
```

### Linux 安裝
```bash
# Ubuntu/Debian
wget https://releases.powerautomation.com/claudeeditor-linux.deb
sudo dpkg -i claudeeditor-linux.deb

# CentOS/RHEL
wget https://releases.powerautomation.com/claudeeditor-linux.rpm
sudo rpm -i claudeeditor-linux.rpm

# Arch Linux
yay -S powerautomation-claudeeditor
```

### Desktop 初始配置
```yaml
啟動配置向導:
  1. 許可證驗證: 輸入您的許可證密鑰
  2. Claude Code CLI 集成: 自動檢測並配置
  3. 工作空間設置: 選擇默認項目目錄
  4. 同步設置: 配置與 Mobile 端同步
  5. 插件安裝: 選擇需要的擴展功能
```

---

## 📦 Step 4: NPM 包安裝與配置

### 安裝核心包
```bash
# 安裝對應版本的核心包
npm install @powerautomation/core

# 根據您的版本安裝額外功能
# 專業版及以上
npm install @powerautomation/claude-editor-desktop

# 團隊版及以上  
npm install @powerautomation/collaboration

# 企業版
npm install @powerautomation/enterprise-cli
```

### 項目初始化
```javascript
// 創建新項目
const { PowerAutomation } = require('@powerautomation/core');

// 初始化 PowerAutomation
const pa = new PowerAutomation({
    license: 'your-license-key',
    edition: 'professional', // personal/professional/team/enterprise
    workspace: './my-project'
});

// 驗證許可證
await pa.validateLicense();
console.log('✅ PowerAutomation 初始化完成!');
```

### 配置文件設置
```yaml
# .powerautomation/config.yaml
license:
  key: "PA-PROFESSIONAL-20241213-1234"
  edition: "professional"

features:
  mobile_sync: true
  desktop_integration: true
  claude_code_cli: true

mcp_components:
  - codeflow
  - smartui  
  - test
  - ag-ui

workflows:
  - code_generation
  - ui_design
  - api_development
  - test_automation
```

---

## 🔧 Step 5: Claude Code CLI 集成

### 安裝 Claude Code CLI (如果尚未安裝)
```bash
# macOS/Linux
curl -fsSL https://claude.ai/install.sh | sh

# Windows (PowerShell)
iwr https://claude.ai/install.ps1 | iex

# 驗證安裝
claude-code --version
```

### PowerAutomation 集成配置
```bash
# 連接 PowerAutomation 與 Claude Code
powerautomation-cli connect claude-code

# 驗證集成
powerautomation-cli status
# ✅ Claude Code CLI: Connected
# ✅ License: Valid (Professional)
# ✅ Mobile Sync: Enabled
# ✅ Desktop Integration: Active
```

### 基本使用示例
```bash
# 使用 PowerAutomation 增強的 Claude Code
claude-code generate --template powerautomation-react
claude-code deploy --platform vercel --config professional
claude-code collaborate --team your-team --editor claudeeditor
```

---

## 🎯 Step 6: 創建第一個項目

### 使用 Mobile ClaudeEditor
```yaml
創建移動端項目:
  1. 打開 ClaudeEditor Mobile
  2. 點擊 "新建項目"
  3. 選擇模板: React Native App
  4. 項目名稱: MyFirstApp
  5. 使用 Claude Code 生成初始代碼
  6. 實時預覽和編輯
```

### 使用 Desktop ClaudeEditor
```yaml
創建桌面端項目:
  1. 打開 ClaudeEditor Desktop
  2. 文件 → 新建項目
  3. 選擇框架: Next.js
  4. 集成 PowerAutomation MCP 組件
  5. 使用內置終端運行 Claude Code CLI
  6. 實時協作 (團隊版+)
```

### 項目結構示例
```
my-powerautomation-project/
├── .powerautomation/
│   ├── config.yaml
│   └── license.key
├── src/
│   ├── components/
│   ├── pages/
│   └── utils/
├── .clauderc
├── package.json
└── README.md
```

---

## 🔄 Step 7: 跨設備同步驗證

### 測試同步功能
```yaml
同步測試步驟:
  1. 在 Mobile 端創建文件
  2. 在 Desktop 端查看是否同步
  3. 修改代碼並保存
  4. 驗證實時同步狀態
  5. 檢查版本歷史記錄
```

### 同步狀態檢查
```bash
# 檢查同步狀態
powerautomation-cli sync status

# 手動觸發同步
powerautomation-cli sync force

# 查看同步日誌
powerautomation-cli sync logs
```

---

## ✅ Step 8: 功能驗證清單

### 基礎功能驗證
- [ ] ✅ 許可證激活成功
- [ ] ✅ Mobile ClaudeEditor 正常運行
- [ ] ✅ Desktop ClaudeEditor 正常運行  
- [ ] ✅ NPM 包安裝無誤
- [ ] ✅ Claude Code CLI 集成成功
- [ ] ✅ 跨設備同步正常
- [ ] ✅ 項目創建和編輯功能

### 版本特定功能驗證

#### 專業版功能
- [ ] ✅ Claude Code CLI 深度集成
- [ ] ✅ 智能代碼補全
- [ ] ✅ Web 平台部署
- [ ] ✅ 高級 UI 組件

#### 團隊版功能
- [ ] ✅ 實時協作編輯
- [ ] ✅ 團隊項目管理
- [ ] ✅ 代碼審查工作流
- [ ] ✅ 多平台部署

#### 企業版功能
- [ ] ✅ 私有雲配置
- [ ] ✅ 多 AI 模型訪問
- [ ] ✅ 企業 CLI 工具
- [ ] ✅ 安全審計日誌

---

## 🆘 常見問題與解決方案

### 許可證問題
```yaml
問題: 許可證驗證失敗
解決: 
  1. 檢查網絡連接
  2. 確認許可證格式正確
  3. 聯繫飛書客服重新發送
  4. 檢查系統時間是否正確
```

### 同步問題
```yaml
問題: 跨設備同步失敗
解決:
  1. 檢查網絡連接
  2. 重啟同步服務
  3. 清除本地緩存
  4. 重新登錄賬號
```

### CLI 集成問題
```yaml
問題: Claude Code CLI 無法連接
解決:
  1. 更新 Claude Code 到最新版本
  2. 重新運行 powerautomation-cli connect
  3. 檢查防火牆設置
  4. 查看詳細錯誤日誌
```

---

## 📞 技術支持

### 支持渠道
- 📱 **飛書客服**: 在飛書中搜索 "PowerAutomation"
- 📧 **郵件支持**: support@powerautomation.com
- 💬 **在線聊天**: https://powerautomation.com/support
- 📚 **文檔中心**: https://docs.powerautomation.com

### 響應時間
- 🔰 **個人版**: 社群支持 (24-48小時)
- 💼 **專業版**: 優先支持 (4-8小時)
- 👥 **團隊版**: 專屬支持 (2-4小時)
- 🏢 **企業版**: 24/7專屬企業支持 (1小時內)

---

## 🎉 恭喜！您已完成 PowerAutomation + ClaudeEditor 的快速設置

現在您可以：
- 🚀 在任何設備上使用 ClaudeEditor 進行開發
- 🤖 享受 Claude Code CLI 的 AI 輔助編程
- 📱 體驗無縫的跨設備同步
- 🔧 使用 PowerAutomation 的強大 MCP 組件
- 👥 與團隊成員實時協作 (團隊版+)

**下一步**: 探索 [高級功能指南](../technical-docs/) 🚀