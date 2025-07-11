# PowerAutomation v4.6.1 macOS 安裝指南

## 🚀 PowerAutomation v4.6.1 - 完整MCP生態系統

**發布日期**: 2025年7月11日  
**版本**: v4.6.1  
**平台**: macOS (Intel & Apple Silicon)

---

## 📋 系統需求

### 最低需求
- **操作系統**: macOS 12.0 (Monterey) 或更高版本
- **處理器**: Intel x64 或 Apple Silicon (M1/M2/M3)
- **記憶體**: 8GB RAM (推薦 16GB)
- **儲存空間**: 2GB 可用空間
- **網絡**: 穩定的網絡連接 (用於初始下載和Claude API)

### 推薦配置
- **操作系統**: macOS 14.0 (Sonoma) 或更高版本
- **處理器**: Apple Silicon M2 或更高
- **記憶體**: 16GB RAM 或更高
- **儲存空間**: 5GB 可用空間

---

## 📦 安裝方式

### 方式一：一鍵安裝腳本 (推薦)

```bash
# 下載並執行安裝腳本
curl -fsSL https://github.com/alexchuang650730/aicore0711/releases/download/v4.6.1/install_mac_v4.6.1.sh | bash

# 或者下載後手動執行
wget https://github.com/alexchuang650730/aicore0711/releases/download/v4.6.1/install_mac_v4.6.1.sh
chmod +x install_mac_v4.6.1.sh
./install_mac_v4.6.1.sh
```

### 方式二：Homebrew 安裝

```bash
# 添加PowerAutomation tap
brew tap alexchuang650730/powerautomation

# 安裝PowerAutomation
brew install powerautomation

# 升級到最新版本
brew upgrade powerautomation
```

### 方式三：手動安裝

```bash
# 1. 下載發布包
curl -L -o PowerAutomation-v4.6.1-macOS.dmg \
  https://github.com/alexchuang650730/aicore0711/releases/download/v4.6.1/PowerAutomation-v4.6.1-macOS.dmg

# 2. 掛載DMG
hdiutil attach PowerAutomation-v4.6.1-macOS.dmg

# 3. 複製應用到Applications
cp -R "/Volumes/PowerAutomation v4.6.1/PowerAutomation.app" /Applications/

# 4. 卸載DMG
hdiutil detach "/Volumes/PowerAutomation v4.6.1"
```

---

## ⚙️ 初始化配置

### 1. 首次啟動

```bash
# 啟動PowerAutomation
powerautomation --init

# 或直接從應用程序啟動
open /Applications/PowerAutomation.app
```

### 2. 配置Claude API

```bash
# 設置Claude API密鑰
powerautomation config set claude.api_key "your-claude-api-key"

# 驗證API連接
powerautomation test claude-connection
```

### 3. 初始化MCP生態系統

```bash
# 初始化所有22個MCP組件
powerautomation mcp init-all

# 驗證MCP組件狀態
powerautomation mcp status

# 啟動核心MCP組件
powerautomation mcp start test_mcp stagewise_mcp ag_ui_mcp
```

---

## 🎯 核心功能驗證

### 1. ClaudEditor 三欄式UI測試

```bash
# 啟動ClaudEditor
powerautomation claudeditor

# 驗證三欄式界面
# - 左欄：項目管理
# - 中欄：代碼編輯器
# - 右欄：AI助手
```

### 2. 測試MCP協作

```bash
# 測試Test MCP + Stagewise MCP協作
powerautomation test mcp-collaboration

# 測試AG-UI MCP組件生成
powerautomation agui generate-test-interface

# 測試完整工作流
powerautomation test full-workflow
```

### 3. 性能基準測試

```bash
# 運行性能測試
powerautomation benchmark

# 驗證響應時間 (目標：<200ms)
powerautomation test response-time

# 測試並發處理能力
powerautomation test concurrent-load
```

---

## 🔧 配置管理

### 主配置文件位置

```
~/.powerautomation/
├── config/
│   ├── main.yaml                 # 主配置
│   ├── mcp_ecosystem.yaml       # MCP生態系統配置
│   ├── claudeditor.yaml         # ClaudEditor配置
│   ├── collaboration.yaml       # 協作配置
│   └── agents.yaml              # 智能代理配置
├── logs/
│   ├── main.log                 # 主日誌
│   ├── mcp_coordinator.log      # MCP協調器日誌
│   └── claudeditor.log          # ClaudEditor日誌
└── data/
    ├── sessions/                # 會話數據
    ├── recordings/              # Stagewise錄製
    └── interfaces/              # AG-UI生成界面
```

### 環境變量配置

```bash
# 在 ~/.zshrc 或 ~/.bash_profile 中添加
export POWERAUTOMATION_HOME="$HOME/.powerautomation"
export CLAUDE_API_KEY="your-claude-api-key"
export POWERAUTOMATION_LOG_LEVEL="INFO"
export POWERAUTOMATION_MCP_AUTO_START="true"
```

---

## 🚀 快速開始

### 第一個項目

```bash
# 1. 創建新項目
powerautomation project create "我的第一個AI項目"

# 2. 啟動ClaudEditor
powerautomation claudeditor

# 3. 在AI助手中輸入
"創建一個React登錄組件，包含表單驗證和樣式"

# 4. 觀察自主任務執行
# PowerAutomation將自動：
# - 分析需求
# - 生成代碼
# - 創建測試
# - 配置環境
```

### 第一個自動化測試

```bash
# 1. 開始UI錄製
powerautomation stagewise start-recording "登錄流程測試"

# 2. 在瀏覽器中執行操作
# - 打開登錄頁面
# - 填寫用戶名密碼
# - 點擊登錄按鈕

# 3. 停止錄製
powerautomation stagewise stop-recording

# 4. 生成測試代碼
powerautomation stagewise generate-test selenium

# 5. 執行測試
powerautomation test run-generated
```

---

## 📊 監控和診斷

### 健康檢查

```bash
# 系統健康檢查
powerautomation health-check

# MCP組件診斷
powerautomation mcp diagnose

# 性能監控
powerautomation monitor start
```

### 日誌查看

```bash
# 實時日誌
powerautomation logs follow

# 特定組件日誌
powerautomation logs mcp test_mcp
powerautomation logs claudeditor

# 錯誤日誌
powerautomation logs error
```

---

## 🔄 升級和維護

### 從舊版本升級

```bash
# 備份現有配置
powerautomation backup create

# 升級到v4.6.1
brew upgrade powerautomation
# 或
powerautomation self-update

# 驗證升級
powerautomation --version
powerautomation test system
```

### 重置和清理

```bash
# 重置配置
powerautomation reset config

# 清理日誌
powerautomation cleanup logs

# 完全重置
powerautomation reset all
```

---

## 🛠️ 開發者配置

### 開發模式

```bash
# 啟用開發模式
powerautomation config set development.enabled true

# 熱重載
powerautomation dev watch

# 調試模式
powerautomation --debug
```

### 自定義MCP組件

```bash
# 創建自定義MCP組件
powerautomation mcp create-component "my_custom_mcp"

# 註冊組件
powerautomation mcp register ./my_custom_mcp

# 測試組件
powerautomation mcp test my_custom_mcp
```

---

## ❗ 故障排除

### 常見問題

**Q: Claude API連接失敗**
```bash
# 檢查API密鑰
powerautomation config get claude.api_key

# 測試網絡連接
powerautomation test network

# 重新配置API
powerautomation config set claude.api_key "new-api-key"
```

**Q: MCP組件啟動失敗**
```bash
# 檢查組件狀態
powerautomation mcp status

# 重啟組件
powerautomation mcp restart test_mcp

# 查看錯誤日誌
powerautomation logs mcp test_mcp --level error
```

**Q: ClaudEditor界面異常**
```bash
# 重置ClaudEditor
powerautomation claudeditor reset

# 清除緩存
powerautomation claudeditor clear-cache

# 重新初始化
powerautomation claudeditor init
```

### 性能優化

```bash
# 性能分析
powerautomation profile start

# 內存使用分析
powerautomation memory analyze

# 優化建議
powerautomation optimize suggest
```

---

## 📞 支持和幫助

### 命令行幫助

```bash
# 全局幫助
powerautomation --help

# 特定命令幫助
powerautomation mcp --help
powerautomation claudeditor --help
```

### 在線資源

- **GitHub倉庫**: https://github.com/alexchuang650730/aicore0711
- **問題報告**: https://github.com/alexchuang650730/aicore0711/issues
- **文檔中心**: https://github.com/alexchuang650730/aicore0711/wiki
- **社區討論**: https://github.com/alexchuang650730/aicore0711/discussions

### 聯繫方式

- **技術支持**: support@powerautomation.ai
- **功能建議**: features@powerautomation.ai
- **安全問題**: security@powerautomation.ai

---

## 🎉 開始使用

恭喜！您已成功安裝PowerAutomation v4.6.1。現在您可以：

1. **探索22個MCP組件**的強大功能
2. **體驗ClaudEditor三欄式UI**的高效開發環境
3. **使用自主任務執行**完成複雜編程任務
4. **記錄和回放UI操作**進行自動化測試
5. **享受5-10倍於Manus的響應速度**

立即開始您的AI驅動開發之旅！

```bash
powerautomation welcome
```

---

**PowerAutomation v4.6.1 - 重新定義AI驅動的開發體驗** 🚀

*本指南包含完整的安裝、配置和使用說明。如有疑問，請參考故障排除部分或聯繫技術支持。*