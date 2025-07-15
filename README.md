# PowerAutomation Core v4.6.9.4

[![CI/CD](https://github.com/alexchuang650730/aicore0711/actions/workflows/ci.yml/badge.svg)](https://github.com/alexchuang650730/aicore0711/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/alexchuang650730/aicore0711/branch/main/graph/badge.svg)](https://codecov.io/gh/alexchuang650730/aicore0711)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

PowerAutomation Core 是一個集成了 MemoryOS MCP、Claude Code 雙向學習和 RLLM/DeepSeek-R1 SWE 訓練的強大自動化平台。

**最新版本**: v4.6.9.4 - 修复增强版本
**發布日期**: 2025年07月15日  
**核心突破**: MemoryOS MCP 第13個服務、Claude Code 真實 API 雙向學習、RLLM/DeepSeek-R1 SWE 訓練集成

## 🎯 核心定位

### 📱 Mobile/Desktop 優先
- **跨平台 ClaudeEditor**: iOS, Android, Windows, macOS, Linux 統一體驗
- **實時同步**: 移動端與桌面端項目和配置實時同步
- **離線支持**: 完整的離線編輯和本地 AI 模型支持
- **觸控優化**: 移動端專用的觸控界面和手勢操作

### 🌐 Web/Community 展示推廣
- **在線體驗**: Web 版本用於產品展示和社區推廣
- **功能演示**: 完整功能展示和交互式教程
- **社區平台**: 開發者交流和分享平台
- **技術支持**: 在線文檔和支持中心

## 🚀 核心特性

### 🔗 飛書生態深度集成
- **購買流程**: 飛書小程序一站式購買和激活
- **企業管理**: 企業管理員統一管理團隊許可證
- **消息推送**: 重要通知通過飛書直接推送
- **中國市場**: 針對中國企業市場的本地化優勢

### 📱 ClaudeEditor Mobile/Desktop
- **跨平台原生**: Tauri + React 技術棧，原生性能
- **Claude Code 集成**: 深度集成 Claude Code CLI 功能
- **實時協作**: 多人實時編輯和項目協作
- **AI 輔助編程**: 內置 AI 助手，智能代碼生成和優化

### 🤖 多 AI 模型支持
- **Claude Enterprise**: 企業級私有部署
- **Gemini Private**: Google Gemini 私有實例
- **Kimi K2 Local**: 本地化 Kimi K2 模型
- **Grok Private**: X.AI Grok 私有集成
- **智能路由**: 根據任務類型自動選擇最佳模型

### 🏢 企業私有雲部署
- **完全私有化**: 所有數據和 AI 模型企業內部部署
- **Kubernetes 集群**: 企業級容器編排和管理
- **SSO 集成**: 與企業 LDAP/AD 系統集成
- **審計日誌**: 完整的用戶行為和數據訪問審計

### 🔧 統一 CLI 工具集
- **claude-code-cli**: Claude Code 命令行工具
- **gemini-cli**: Google Gemini 命令行接口
- **powerautomation-cli**: PowerAutomation 核心工具
- **統一管理**: 一個工具管理所有 AI 模型和服務

## 📊 版本功能分級

### 🔰 個人版 (免費)
- 3個基礎 MCP 組件
- ClaudeEditor 基礎版 (單平台)
- 1GB 存儲空間
- 社群支持

### 💼 專業版 ($39/月)
- 4個進階 MCP 組件
- ClaudeEditor 完整版 (跨平台)
- Claude Code 深度集成
- 10GB 存儲空間
- 優先技術支持

### 👥 團隊版 ($129/月)
- 8個協作 MCP 組件
- 實時協作功能
- 多平台部署支持
- 50GB 存儲空間
- 團隊管理功能

### 🏢 企業版 ($499/月起)
- 14個完整 MCP 組件
- 私有雲 AI 模型部署
- 企業級安全和合規
- 無限存儲空間
- 24/7 企業支持

## 🛠️ 技術架構

### Mobile/Desktop 技術棧
- **前端框架**: React 18 + TypeScript
- **桌面應用**: Tauri (Rust + WebView)
- **移動應用**: React Native + Expo
- **狀態管理**: Zustand + React Query
- **UI 組件**: Radix UI + Tailwind CSS

### 後端架構
- **核心服務**: Python 3.11+ FastAPI
- **AI 模型服務**: 多模型統一接口
- **數據庫**: PostgreSQL + Redis
- **消息隊列**: RabbitMQ
- **容器編排**: Docker + Kubernetes

### NPM 生態系統
```
@powerautomation/
├── core                    # 核心 PowerAutomation 包
├── claude-editor-mobile    # 移動端編輯器
├── claude-editor-desktop   # 桌面端編輯器
├── collaboration          # 協作功能包 (團隊版+)
└── enterprise-cli          # 企業版命令行工具
```

## 🚀 快速開始

### 📱 移動端安裝
```bash
# iOS App Store
https://apps.apple.com/app/claudeditor

# Android Play Store  
https://play.google.com/store/apps/claudeditor

# 或通過飛書購買後下載
https://applink.feishu.cn/client/message/link/open?token=AmfoKtFagQATaHK7JJIAQAI%3D
```

### 🖥️ 桌面端安裝
```bash
# macOS
brew install powerautomation/tap/claudeditor

# Windows
winget install PowerAutomation.ClaudEditor

# Linux
snap install claudeditor

# 或 NPM 安裝
npm install -g @powerautomation/claude-editor-desktop
```

### 🌐 Web 版體驗
訪問 https://demo.claudeditor.com 體驗完整功能

## 📚 展示中心

詳細產品展示請訪問: **[PowerAutomation Showcase](https://github.com/alexchuang19760730/showcase)**

### 核心展示內容
- [**商業模式分析**](https://github.com/alexchuang19760730/showcase/blob/main/business/business-model.md) - 完整定價策略和收入預測
- [**企業估值分析**](https://github.com/alexchuang19760730/showcase/blob/main/business/valuation-analysis.md) - $6M ARR 估值報告
- [**技術架構設計**](https://github.com/alexchuang19760730/showcase/blob/main/technical-docs/architecture.md) - 完整系統架構
- [**本地部署指南**](https://github.com/alexchuang19760730/showcase/blob/main/deployment/local-deployment.md) - Docker/NPM/源碼部署
- [**企業私有雲部署**](https://github.com/alexchuang19760730/showcase/blob/main/deployment/enterprise-deployment.md) - Kubernetes 企業部署
- [**NPM 生態系統**](https://github.com/alexchuang19760730/showcase/blob/main/ecosystem/npm-ecosystem.md) - 完整包管理體系
- [**快速集成指南**](https://github.com/alexchuang19760730/showcase/blob/main/integration-guide/quick-start.md) - 15分鐘上手指南
- [**互動技術演示**](https://github.com/alexchuang19760730/showcase/blob/main/presentations/tech-architecture.html) - 在線架構展示

## 🎯 五階段實施路線圖

### Phase 0: 飛書生態集成 (v4.6.10) - 3週
- 飛書小程序購買流程
- NPM 包生態建立  
- Mobile/Desktop ClaudeEditor 基礎版

### Phase 1: 核心配額系統 (v4.7.0) - 2週
- 統一許可證管理
- 跨設備配額同步
- 實時使用監控

### Phase 2: 工作流分級系統 (v4.7.5) - 3週
- AI 模型智能路由
- 分級工作流控制
- 可視化編輯器

### Phase 3: 部署平台控制 (v4.8.0) - 4週
- 多平台部署支持
- 企業級配置管理
- 自動化 CI/CD

### Phase 4-5: 企業級功能 (v4.9.0) - 8週
- 私有雲 AI 模型部署
- 統一 CLI 工具集
- 企業安全框架

## 💰 商業價值

### 投資回報分析
- **首年收入預期**: $6M+ ARR
- **投資回報率**: 476%
- **目標用戶數**: 25,000+
- **實施週期**: 21週

### 市場定位
- **全球 AI 開發工具市場**: $156億 (2024)
- **中國企業軟件市場**: $890億 (2024)
- **預期年增長率**: 45%
- **目標市場份額**: 5% (中國 AI 開發工具)

## 🤝 社區與支持

### 社區資源
- **GitHub 主倉庫**: https://github.com/alexchuang650730/aicore0711
- **展示中心**: https://github.com/alexchuang19760730/showcase
- **技術文檔**: https://docs.claudeditor.com
- **社區論壇**: https://community.powerautomation.dev

### 商業支持
- **飛書購買**: https://applink.feishu.cn/client/message/link/open?token=AmfoKtFagQATaHK7JJIAQAI%3D
- **企業銷售**: enterprise@powerautomation.dev
- **技術支持**: support@claudeditor.com
- **合作洽談**: partnerships@powerautomation.dev

## 📄 許可證

本項目採用 AGPL-3.0 許可證 - 詳見 [LICENSE](./LICENSE) 文件

---

**PowerAutomation v4.6.9 - 重新定義跨平台 AI 開發體驗！** 🚀📱🖥️

*© 2024 PowerAutomation Project. 版權所有。*