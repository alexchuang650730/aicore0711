# AICore0624 目录结构和测试方法分析

## 项目目录结构

```
aicore0624/
├── README.md                    # 项目说明文档
├── requirements.txt             # Python 依赖清单
├── .gitignore                   # Git 忽略规则
├── PowerAutomation/             # 核心系统目录
├── PowerAutomation_local/       # 插件生产部署目录
├── backup/                      # 备份目录
├── config/                      # 配置文件
├── development/                 # 开发相关文件
├── docs/                        # 项目文档
├── powerautomation_web/         # Web 相关组件
│   ├── frontend/                # 原有前端应用
│   ├── backend/                 # 原有后端服务
│   └── smartui/                 # SmartUI 智能界面
├── scripts/                     # 通用脚本
└── tests/                       # 测试相关文件
    ├── api_tests/               # API 接口功能测试
    │   ├── admin_tests/         # 管理员角色 API 测试
    │   ├── developer_tests/     # 开发者角色 API 测试
    │   ├── user_tests/          # 使用者角色 API 测试
    │   ├── smartinvention_examples/  # SmartInvention API 范例
    │   ├── test_flow_tests/     # 测试流程测试
    │   └── run_all_api_tests.py # 统一 API 测试运行器
    ├── ui_operation_tests/      # UI 界面操作测试
    ├── ui_usability_tests/      # UI 易用性测试
    ├── templates/               # 测试模板
    ├── generators/              # 测试生成器
    ├── testcases/               # 测试案例
    │   └── requirement_analysis/ # 需求分析测试
    └── results/                 # 测试结果
```

## 测试方法和原则

### 三种实用测试分类

1. **API 测试 (api_tests/)**
   - 目的：测试接口功能和数据交互
   - 内容：REST API、GraphQL、WebSocket 等接口测试
   - 角色分类：admin_tests、developer_tests、user_tests
   - 范例：SmartInvention API 使用范例

2. **UI 操作测试 (ui_operation_tests/)**
   - 目的：测试界面操作和功能流程
   - 内容：按钮点击、表单提交、页面导航等操作测试
   - 技术：Selenium、Playwright 等自动化工具

3. **UI 易用性测试 (ui_usability_tests/)**
   - 目的：测试用户体验和界面易用性
   - 内容：用户流程、界面响应、可访问性等测试
   - 重点：真实用户场景和体验评估

### 测试原则

**拋棄傳統無意義分類：**
- ❌ unit test - 大多是 mock test，測假數據
- ❌ integration test - 很少真正集成多個系統
- ❌ e2e test - 從來不是真正的端到端

**採用實用分類：**
- ✅ API 測試 - 真實的 API 調用和響應
- ✅ UI 操作測試 - 真實的界面操作和用戶行為
- ✅ UI 易用性測試 - 真實的用戶體驗和使用場景

### 测试运行方式

```shell
# API 测试
cd tests/api_tests/
python run_all_api_tests.py

# SmartInvention API 测试
cd tests/api_tests/smartinvention_examples/
python run_tests.py

# 需求分析测试
cd tests/testcases/requirement_analysis/
python test_requirement_analysis_integration.py
```

### 测试结果管理

- 测试结果自动保存到相应目录下的 JSON 文件中
- 命名格式：`{test_name}_test_results_{timestamp}.json`
- 支持多个 PowerAutomation 实体的配置

### 关键特性

1. **角色权限测试**：按照admin、developer、user三种角色进行API权限测试
2. **真实API调用**：不使用mock，直接调用真实API接口
3. **结果持久化**：测试结果保存为JSON格式，便于分析
4. **统一运行器**：run_all_api_tests.py提供统一的测试入口
5. **配置化测试**：支持通过配置文件指定不同的测试环境

