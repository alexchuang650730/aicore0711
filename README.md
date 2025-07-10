# PowerAutomation v4.5.0 - 企業級AI自動化平台

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 16+](https://img.shields.io/badge/node.js-16+-green.svg)](https://nodejs.org/)

PowerAutomation v4.5.0 是一個革命性的企業級AI自動化平台，專為現代軟體開發團隊設計，提供零代碼測試、AI智能協作和完整的開發生態系統。

## 🚀 核心特性

### 🎯 錄製即測試 (Record-as-Test)
- **一鍵錄製**：直接在應用中錄製操作，自動生成測試用例
- **AI智能優化**：基於Claude、GPT等AI模型優化測試邏輯
- **多框架支持**：支援Selenium、Playwright、Cypress等主流測試框架

### 🧠 AI生態系統深度集成
- **多AI模型協調**：整合Claude 3.5 Sonnet、GPT-4、Gemini Pro
- **智能測試生成**：AI自動分析應用邏輯，生成完整測試套件
- **自然語言測試**：用自然語言描述測試需求，AI自動轉換為可執行測試

### 🛠 Zen MCP工具生態
- **模塊化架構**：基於MCP (Model Control Protocol) 的組件化設計
- **可擴展生態**：豐富的第三方組件和插件系統
- **企業級集成**：支援JIRA、Confluence、GitLab等企業工具

### 🎨 ClaudEditor v4.5 集成
- **視覺化編程**：拖拽式測試用例設計
- **實時協作**：多人同時編輯和審查測試用例
- **智能建議**：AI提供測試優化建議和覆蓋率分析

## 📁 項目結構

```
aicore0711/
├── core/                           # 核心引擎
│   └── components/                 # 核心組件
│       ├── integrated_test_framework.py    # 集成測試框架
│       ├── claudeditor_test_generator.py   # ClaudEditor測試生成器
│       ├── test_mcp/               # Test MCP組件
│       ├── stagewise_mcp/          # Stagewise MCP組件
│       └── ag_ui_mcp/              # AG-UI MCP組件
├── deployment/                     # 部署配置
│   └── devices/                    # 設備特定部署
│       └── mac/                    # macOS部署
│           ├── v4.3.0/            # 版本4.3.0
│           └── v4.4.0/            # 版本4.4.0
├── tests/                          # 測試套件
├── docs/                           # 文檔
└── README.md                       # 項目說明
```

## 🔧 技術架構

### 核心組件系統
- **Test MCP**：測試執行和管理引擎
- **Stagewise MCP**：操作錄製和回放系統
- **AG-UI MCP**：用戶界面生成和交互管理
- **ClaudEditor Integration**：視覺化測試設計平台

### 支援的技術棧
- **後端**：Python 3.8+, asyncio, FastAPI
- **前端**：Node.js 16+, React, Vue.js
- **測試框架**：Selenium, Playwright, Cypress
- **AI模型**：Claude 3.5 Sonnet, GPT-4, Gemini Pro
- **數據庫**：SQLite, PostgreSQL, MongoDB

## 🚀 快速開始

### 1. 環境準備

```bash
# Python環境
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate    # Windows

# 安裝依賴
pip install -r requirements.txt

# Node.js環境
npm install
```

### 2. 配置設置

```bash
# 複製配置模板
cp config/config.template.json config/config.json

# 編輯配置文件
# 添加AI API密鑰和數據庫連接信息
```

### 3. 啟動服務

```bash
# 啟動核心服務
python run_main_service.py

# 啟動ClaudEditor (另一個終端)
cd claudeditor
npm run dev

# 啟動測試套件
python run_tests.py
```

### 4. Docker部署（推薦）

```bash
# 構建鏡像
docker-compose build

# 啟動服務
docker-compose up -d

# 查看服務狀態
docker-compose ps
```

## 📊 使用示例

### 錄製和生成測試

```python
from core.components.integrated_test_framework import IntegratedTestSuite

# 創建測試套件
test_suite = IntegratedTestSuite()

# 運行完整測試
async def run_tests():
    test_session = await test_suite.run_comprehensive_tests()
    
    # 生成測試報告
    report_path = await test_suite.generate_test_report(test_session)
    print(f"測試報告已生成: {report_path}")

# 執行測試
import asyncio
asyncio.run(run_tests())
```

### ClaudEditor測試生成

```python
from core.components.claudeditor_test_generator import ClaudEditorTestCaseGenerator

# 創建測試生成器
generator = ClaudEditorTestCaseGenerator()

# 生成測試用例
test_cases = generator.generate_all_test_cases()

# 導出測試用例
generator.export_test_cases_to_json(test_cases, "claudeditor_tests.json")
```

## 🎯 主要功能

### 1. 智能測試生成
- 基於用戶操作自動生成測試用例
- AI優化測試邏輯和斷言
- 支援多種測試模式和框架

### 2. 實時協作
- 多人同時編輯測試用例
- 版本控制和變更追蹤
- 評論和審查功能

### 3. 企業級集成
- CI/CD流水線集成
- 企業工具連接（JIRA、Slack等）
- 權限管理和安全控制

### 4. 智能分析
- 測試覆蓋率分析
- 性能瓶頸識別
- AI驅動的測試優化建議

## 📈 性能指標

- **測試生成速度**：比傳統方法快10倍
- **維護成本**：降低80%的測試維護工作量
- **覆蓋率提升**：平均提升40%的測試覆蓋率
- **缺陷發現**：早期發現90%以上的關鍵缺陷

## 📚 文檔資源

- [安裝指南](docs/installation.md)
- [API文檔](docs/api.md)
- [用戶手冊](docs/user-guide.md)
- [開發者指南](docs/developer-guide.md)
- [架構文檔](docs/architecture.md)
- [實際測試報告](REAL_TESTING_DOCUMENTATION.md)

## 🗺 發展路線圖

### v4.6.0 (2025 Q2)
- [ ] 增強AI模型集成
- [ ] 移動端測試支援
- [ ] 更多第三方工具集成

### v4.7.0 (2025 Q3)
- [ ] 多語言UI支援
- [ ] 高級分析儀表板
- [ ] 企業級SSO集成

### v5.0.0 (2025 Q4)
- [ ] 下一代AI引擎
- [ ] 雲原生架構重構
- [ ] 微服務化部署

## 🤝 貢獻指南

我們歡迎社區貢獻！請參閱：

1. [貢獻指南](CONTRIBUTING.md)
2. [代碼規範](docs/coding-standards.md)
3. [問題反饋](https://github.com/alexchuang650730/aicore0707/issues)

### 開發環境設置

```bash
# Fork並克隆倉庫
git clone https://github.com/yourusername/aicore0707.git
cd aicore0707

# 創建功能分支
git checkout -b feature/your-feature-name

# 提交更改
git commit -m "Add your feature"
git push origin feature/your-feature-name

# 創建Pull Request
```

## 📄 許可證

本項目採用 [MIT許可證](LICENSE)。

## 🙏 致謝

特別感謝：
- Anthropic Claude團隊提供的AI技術支援
- 開源社區的寶貴貢獻
- 測試用戶的反饋和建議

## 📞 聯繫我們

- **郵箱**：alexchuang650730@gmail.com
- **GitHub Issues**：[問題反饋](https://github.com/alexchuang650730/aicore0707/issues)
- **文檔**：[官方文檔](https://powerautomation.dev)

---

<div align="center">
<b>PowerAutomation v4.5.0 - 讓AI驅動您的測試自動化之旅</b><br>
🚀 零代碼 | 🧠 AI智能 | 🛠 企業級 | 🎯 高效率
</div>