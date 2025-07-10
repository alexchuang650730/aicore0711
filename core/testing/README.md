# PowerAutomation 端到端測試系統

## 🎯 系統概述

PowerAutomation 端到端測試系統是一個完整的自動化測試解決方案，支持多環境、多瀏覽器的全棧測試，確保平台功能的穩定性和可靠性。

### 核心特性

- 🔄 **完整測試流程**：從單元測試到E2E測試的完整覆蓋
- 🌐 **多環境支持**：本地、Docker、預發布、生產環境
- 🔍 **多瀏覽器測試**：Chrome、Firefox 跨瀏覽器兼容性測試
- ⚡ **並行執行**：支持測試用例並行執行，提高效率
- 📊 **詳細報告**：自動生成測試報告和覆蓋率分析
- 🚀 **CI/CD集成**：與GitHub Actions深度集成

## 🏗️ 系統架構

```
PowerAutomation E2E測試系統
├── 測試執行引擎 (e2e_test_workflow.py)
├── 環境管理器 (EnvironmentManager)
├── WebDriver管理器 (WebDriverManager)
├── 測試數據管理器 (TestDataManager)
├── GitHub Actions工作流 (e2e-test-workflow.yml)
└── 測試報告系統 (TestReporter)
```

## 📋 測試覆蓋範圍

### 測試類型

#### 1. 單元測試 (Unit Tests)
- JavaScript/TypeScript 組件測試
- Python 後端邏輯測試
- API 端點單元測試
- 工具函數測試

#### 2. 集成測試 (Integration Tests)
- 前後端API集成
- 數據庫操作測試
- 第三方服務集成
- 微服務間通信測試

#### 3. 端到端測試 (E2E Tests)
- 用戶登錄流程
- 項目創建和管理
- AI助手功能
- 代碼生成和編輯
- 文件上傳和處理

#### 4. 性能測試 (Performance Tests)
- 頁面加載性能
- API響應時間
- 並發用戶負載測試
- 資源使用監控

#### 5. 安全測試 (Security Tests)
- OWASP漏洞掃描
- 依賴包安全檢查
- 認證授權測試
- 數據加密驗證

## 🚀 快速開始

### 1. 環境準備

```bash
# 安裝Python依賴
pip install -r core/testing/requirements.txt

# 安裝Node.js依賴
npm install

# 安裝瀏覽器驅動
# Chrome
wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip
unzip /tmp/chromedriver.zip -d /tmp
sudo mv /tmp/chromedriver /usr/local/bin/

# Firefox
wget -O /tmp/geckodriver.tar.gz https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz
tar -xzf /tmp/geckodriver.tar.gz -C /tmp
sudo mv /tmp/geckodriver /usr/local/bin/
```

### 2. 配置文件

創建 `core/testing/e2e_config.yaml`：

```yaml
environments:
  local:
    base_url: 'http://localhost:3000'
    api_url: 'http://localhost:8000'
    browser: 'chrome'
    services: []

  docker:
    compose_file: 'docker-compose.test.yml'
    services:
      - name: 'web'
        image: 'powerautomation:test'
        ports:
          '3000/tcp': 3000
        environment:
          NODE_ENV: 'test'

test_data_dir: 'test_data'
results_dir: 'test_results'
parallel_execution: true
max_workers: 4
default_timeout: 300
```

### 3. 運行測試

```bash
# 運行本地E2E測試
cd core/testing
python e2e_test_workflow.py

# 運行特定測試套件
python e2e_test_workflow.py --suite "login_tests"

# 運行Docker環境測試
python e2e_test_workflow.py --environment docker

# 運行性能測試
python e2e_test_workflow.py --type performance
```

## 📊 測試用例設計

### 核心功能測試用例

#### 1. 用戶認證測試
```python
TestCase(
    id="pa_login_test",
    name="用戶登錄測試",
    description="測試PowerAutomation用戶登錄功能",
    test_type=TestType.E2E,
    steps=[
        {"action": "navigate", "params": {"url": "{base_url}/login"}},
        {"action": "input", "params": {"locator": "id=username", "value": "{user[username]}"}},
        {"action": "input", "params": {"locator": "id=password", "value": "{user[password]}"}},
        {"action": "click", "params": {"locator": "id=login-button"}},
        {"action": "wait_for_element", "params": {"locator": "class=dashboard", "timeout": 10}}
    ],
    expected_results=[
        "url_contains:/dashboard",
        "page_title:PowerAutomation Dashboard"
    ]
)
```

#### 2. 項目管理測試
```python
TestCase(
    id="pa_project_creation_test",
    name="項目創建測試",
    description="測試PowerAutomation項目創建功能",
    dependencies=["pa_login_test"],
    steps=[
        {"action": "click", "params": {"locator": "id=new-project-btn"}},
        {"action": "input", "params": {"locator": "id=project-name", "value": "{project[name]}"}},
        {"action": "click", "params": {"locator": "id=create-project-btn"}},
        {"action": "validate", "params": {"type": "element_text", "locator": "id=project-title", "expected": "{project[name]}"}}
    ]
)
```

#### 3. AI助手測試
```python
TestCase(
    id="pa_ai_assistant_test",
    name="AI助手功能測試",
    description="測試PowerAutomation AI助手的對話和代碼生成功能",
    steps=[
        {"action": "click", "params": {"locator": "id=ai-assistant-tab"}},
        {"action": "input", "params": {"locator": "id=ai-chat-input", "value": "請幫我生成一個React組件"}},
        {"action": "click", "params": {"locator": "id=send-message-btn"}},
        {"action": "wait_for_element", "params": {"locator": "class=ai-response", "timeout": 30}},
        {"action": "validate", "params": {"type": "element_exists", "locator": "class=code-block"}}
    ]
)
```

## 🔧 環境管理

### 測試環境類型

#### 本地環境 (Local)
```python
async def _setup_local_environment(self, config):
    env_info = {
        'type': 'local',
        'base_url': 'http://localhost:3000',
        'api_url': 'http://localhost:8000',
        'browser': 'chrome'
    }
    await self._wait_for_services(env_info)
    return env_info
```

#### Docker環境 (Docker)
```python
async def _setup_docker_environment(self, config):
    # 創建測試網絡
    network = self.docker_client.networks.create(network_name)
    
    # 啟動容器
    containers = []
    for service_config in config.get('services', []):
        container = await self._start_docker_container(service_config, network_name)
        containers.append(container)
    
    return env_info
```

### 服務健康檢查
```python
async def _wait_for_services(self, env_info):
    for i in range(max_retries):
        try:
            # 檢查Web服務
            response = requests.get(f"{env_info['base_url']}/health", timeout=5)
            if response.status_code == 200:
                return
        except Exception:
            await asyncio.sleep(retry_interval)
```

## 🧪 測試數據管理

### 動態測試數據生成
```python
def _generate_default_data(self, test_case_id):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    return {
        'user': {
            'username': f'test_user_{timestamp}',
            'email': f'test_{timestamp}@example.com',
            'password': 'Test123!@#'
        },
        'project': {
            'name': f'Test Project {timestamp}',
            'description': f'Automated test project created at {timestamp}',
            'type': 'web_application'
        }
    }
```

### 測試數據隔離
- 每個測試用例使用獨立的測試數據
- 時間戳確保數據唯一性
- 支持自定義測試數據覆蓋

## 📈 GitHub Actions集成

### 工作流觸發條件
```yaml
on:
  push:
    branches: [ main, develop ]
    paths: ['src/**', 'core/**', 'tests/**']
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * *'  # 每日凌晨2點
  workflow_dispatch:     # 手動觸發
```

### 並行測試執行
```yaml
strategy:
  matrix:
    browser: [chrome, firefox]
  fail-fast: false
```

### 測試階段
1. **環境準備**：依賴安裝和緩存
2. **單元測試**：快速反饋基礎功能
3. **集成測試**：驗證服務間交互
4. **E2E測試**：多瀏覽器端到端驗證
5. **性能測試**：性能指標監控
6. **安全測試**：安全漏洞掃描
7. **結果匯總**：生成綜合報告

## 📊 測試報告系統

### 自動生成報告
```python
async def _generate_test_report(self, test_suite):
    report_lines = [
        "# PowerAutomation 端到端測試報告",
        f"**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 📊 測試總覽",
        f"**測試套件**: {test_suite.name}",
        f"**執行狀態**: {test_suite.status.value}",
        "",
        "## 📈 測試統計",
        f"- **總測試數**: {len(test_suite.test_cases)}",
        f"- **通過**: {test_suite.passed_count} ✅",
        f"- **失敗**: {test_suite.failed_count} ❌",
        f"- **成功率**: {(test_suite.passed_count / len(test_suite.test_cases) * 100):.1f}%"
    ]
```

### 測試覆蓋率分析
- 代碼覆蓋率報告
- 功能覆蓋率統計
- 瀏覽器兼容性報告
- 性能指標趨勢

## 🔍 故障診斷

### 自動截圖
```python
async def _take_screenshot(self, driver, test_case_id, suffix=""):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{test_case_id}_{suffix}_{timestamp}.png"
    filepath = self.screenshots_dir / filename
    driver.save_screenshot(str(filepath))
    return str(filepath)
```

### 詳細日誌記錄
- 測試執行步驟日誌
- 瀏覽器控制台日誌
- 網絡請求日誌
- 錯誤堆棧追蹤

### 失敗重試機制
- 網絡請求自動重試
- 元素查找超時重試
- 環境啟動失敗重試

## 🚀 性能優化

### 並行執行策略
```python
async def _execute_tests_parallel(self, test_suite, env_info):
    # 根據依賴關係分組測試用例
    test_groups = self._group_tests_by_dependencies(test_suite.test_cases)
    
    for group in test_groups:
        semaphore = asyncio.Semaphore(test_suite.max_workers)
        tasks = [self._execute_test_case_with_semaphore(tc, env_info, semaphore) 
                for tc in group if not self._should_skip_test(tc, test_suite)]
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
```

### 資源管理
- WebDriver會話復用
- Docker容器生命週期管理
- 測試數據自動清理
- 內存使用監控

## 📚 最佳實踐

### 1. 測試設計原則
- **獨立性**：每個測試用例獨立運行
- **冪等性**：重複執行結果一致
- **可讀性**：測試步驟清晰易懂
- **可維護性**：模塊化設計便於維護

### 2. 數據管理
- 使用動態生成的測試數據
- 避免硬編碼的測試數據
- 確保測試數據隔離
- 及時清理測試數據

### 3. 錯誤處理
- 詳細的錯誤信息記錄
- 失敗場景截圖保存
- 優雅的資源清理
- 合理的重試策略

### 4. 持續改進
- 定期檢查測試覆蓋率
- 監控測試執行時間
- 優化不穩定的測試
- 更新測試用例以適應功能變更

## 🔧 配置選項

### 測試執行配置
```yaml
parallel_execution: true     # 是否並行執行
max_workers: 4              # 最大並行數
default_timeout: 300        # 默認超時時間(秒)
screenshot_on_failure: true # 失敗時自動截圖
retry_count: 3              # 失敗重試次數
```

### 瀏覽器配置
```yaml
browser_options:
  chrome:
    headless: true
    window_size: "1920,1080"
    disable_gpu: true
  firefox:
    headless: true
    window_size: "1920,1080"
```

### 環境特定配置
```yaml
environments:
  staging:
    base_url: 'https://staging.powerautomation.com'
    api_url: 'https://api-staging.powerautomation.com'
    auth_token: '${STAGING_AUTH_TOKEN}'
  production:
    base_url: 'https://powerautomation.com'
    api_url: 'https://api.powerautomation.com'
    read_only: true  # 生產環境只讀測試
```

## 📞 支持與維護

### 監控和警報
- 測試失敗率監控
- 執行時間趨勢分析
- 自動失敗通知
- 週期性健康檢查

### 技術支持
- **問題報告**: [創建Issue](https://github.com/alexchuang650730/aicore0711/issues)
- **功能請求**: [提交Enhancement](https://github.com/alexchuang650730/aicore0711/issues/new?template=enhancement.md)
- **文檔改進**: [編輯文檔](https://github.com/alexchuang650730/aicore0711/edit/main/core/testing/README.md)

---

**🧪 PowerAutomation E2E測試系統 - 確保每個功能都經過全面驗證**