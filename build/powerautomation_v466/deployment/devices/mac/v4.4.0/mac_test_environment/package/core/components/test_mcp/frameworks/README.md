# PowerAutomation 4.0 测试系统

## 📁 目录结构

```
test/
├── __init__.py                    # 测试包初始化
├── README.md                      # 本文档
├── test_manager.py                # 统一测试管理器
├── test_cli.py                    # 命令行接口
├── ui_test_registry.py            # UI测试注册器
├── config/                        # 配置文件
│   ├── test_config.yaml           # 主配置文件
│   └── ui_test_config.yaml        # UI测试配置
├── testcases/                     # 测试用例
│   ├── __init__.py
│   └── tc_demo_tests.py           # 四个演示用例测试
├── runners/                       # 测试运行器
│   ├── __init__.py
│   ├── run_p0_tests.py            # P0测试运行器
│   ├── run_p0_tests_headless.py   # P0无头测试运行器
│   └── run_ui_tests.py            # UI测试运行器
├── demos/                         # 演示系统
│   ├── __init__.py
│   ├── demo_record_as_test.py     # 录制即测试演示
│   └── record_as_test_demo_system.py  # 演示系统
├── integration/                   # 集成测试
│   ├── __init__.py
│   └── test_ui_integration_demo.py # UI集成测试演示
├── ui_tests/                      # UI测试用例
│   ├── __init__.py
│   ├── test_basic_ui_operations.py    # 基础UI操作测试
│   ├── test_complex_ui_workflows.py   # 复杂UI工作流测试
│   └── test_responsive_ui.py          # 响应式UI测试
├── fixtures/                      # 测试数据和固定装置
├── reports/                       # 测试报告输出目录
└── assets/                        # 测试资源文件
```

## 🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行所有测试
```bash
# 使用CLI
python test/test_cli.py run

# 或使用管理器
python -m test.test_manager
```

### 运行P0核心测试
```bash
python test/test_cli.py p0 --report
```

### 运行UI测试
```bash
python test/test_cli.py ui --browser chrome --report
```

### 运行演示测试
```bash
python test/test_cli.py demo --record --report
```

## 📊 测试分类

### 按类型分类
- **unit**: 单元测试
- **integration**: 集成测试
- **ui**: UI测试
- **e2e**: 端到端测试
- **performance**: 性能测试
- **demo**: 演示测试

### 按优先级分类
- **P0**: 核心功能，必须通过
- **P1**: 重要功能，高优先级
- **P2**: 一般功能，中优先级
- **P3**: 边缘功能，低优先级

## 🛠️ 使用指南

### 1. 命令行接口

#### 基本命令
```bash
# 查看帮助
python test/test_cli.py --help

# 列出所有测试套件
python test/test_cli.py list

# 查看测试套件信息
python test/test_cli.py info tc_demo

# 查看系统状态
python test/test_cli.py status
```

#### 运行测试
```bash
# 运行指定测试套件
python test/test_cli.py run --suite tc_demo

# 按类型运行测试
python test/test_cli.py run --type ui

# 按优先级运行测试
python test/test_cli.py run --priority p0

# 生成报告
python test/test_cli.py run --report --format html
```

#### 快捷命令
```bash
# P0测试
python test/test_cli.py p0 --report

# UI测试
python test/test_cli.py ui --browser chrome --headless

# 演示测试
python test/test_cli.py demo --demo tc_demo_001 --record
```

#### 维护命令
```bash
# 清理旧结果
python test/test_cli.py cleanup --days 30 --confirm
```

### 2. 编程接口

#### 使用测试管理器
```python
from test.test_manager import get_test_manager, TestType, TestPriority

# 获取管理器实例
manager = get_test_manager()

# 运行测试套件
result = await manager.run_test_suite('tc_demo')

# 按优先级运行测试
results = await manager.run_tests_by_priority(TestPriority.P0)

# 按类型运行测试
results = await manager.run_tests_by_type(TestType.UI)

# 生成报告
report_file = manager.generate_report(results, 'html')
```

#### 创建自定义测试套件
```python
from test.test_manager import TestResult, TestStatus, TestType, TestPriority
from datetime import datetime

class MyTestSuite:
    async def run_all_tests(self, **kwargs):
        results = []
        
        # 测试方法1
        start_time = datetime.now()
        try:
            # 执行测试逻辑
            self.test_method_1()
            
            result = TestResult(
                test_id="MyTestSuite.test_method_1",
                test_name="测试方法1",
                test_type=TestType.UNIT,
                priority=TestPriority.P1,
                status=TestStatus.PASSED,
                start_time=start_time,
                end_time=datetime.now()
            )
        except Exception as e:
            result = TestResult(
                test_id="MyTestSuite.test_method_1",
                test_name="测试方法1",
                test_type=TestType.UNIT,
                priority=TestPriority.P1,
                status=TestStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e)
            )
        
        results.append(result)
        return results
    
    def test_method_1(self):
        # 测试逻辑
        assert True
```

### 3. 配置管理

#### 主配置文件 (test/config/test_config.yaml)
```yaml
basic:
  output_dir: "./test_results"
  parallel_execution: true
  max_workers: 4
  timeout: 300

reporting:
  generate_reports: true
  report_formats: ["html", "json"]
  include_screenshots: true

test_suites:
  tc_demo:
    enabled: true
    priority: "p0"
    timeout: 600
```

#### UI测试配置 (test/config/ui_test_config.yaml)
```yaml
browser:
  default_browser: "chrome"
  headless: false
  window_size: [1920, 1080]
  implicit_wait: 10

test_data:
  base_url: "http://localhost:8080"
  test_users:
    admin:
      username: "admin"
      password: "password"
```

## 📋 测试套件详情

### 1. TC Demo Tests (testcases/tc_demo_tests.py)
四个核心演示用例测试：
- **TC_DEMO_001**: SmartUI + MemoryOS演示
- **TC_DEMO_002**: 录制即测试演示
- **TC_DEMO_003**: AI辅助开发演示
- **TC_DEMO_004**: 端到端集成演示

### 2. UI Tests (ui_tests/)
完整的UI测试套件：
- **基础UI操作**: 点击、输入、滚动等
- **复杂工作流**: 登录、表单提交、购物车等
- **响应式测试**: 多设备、多分辨率测试

### 3. Integration Tests (integration/)
系统集成测试：
- **UI集成测试**: UI组件与后端服务集成
- **API集成测试**: 第三方API集成
- **数据库集成测试**: 数据持久化测试

## 📊 报告系统

### HTML报告
- 美观的可视化界面
- 详细的测试结果展示
- 错误信息和截图
- 性能统计图表

### JSON报告
- 结构化数据格式
- 便于程序处理
- 完整的测试元数据
- 支持数据分析

### 报告内容
- 测试总结统计
- 每个测试套件详情
- 失败测试的错误信息
- 执行时间和性能数据
- 截图和日志文件

## 🔧 故障排除

### 常见问题

#### 1. 导入错误
```bash
# 确保项目路径正确
export PYTHONPATH="${PYTHONPATH}:/path/to/aicore0707"

# 或在代码中添加路径
import sys
sys.path.insert(0, '/path/to/aicore0707')
```

#### 2. 浏览器驱动问题
```bash
# 安装Chrome驱动
brew install chromedriver  # macOS
sudo apt-get install chromium-chromedriver  # Ubuntu

# 检查驱动版本
chromedriver --version
```

#### 3. 权限问题
```bash
# 给予执行权限
chmod +x test/test_cli.py
chmod +x test/runners/*.py
```

#### 4. 依赖问题
```bash
# 安装测试依赖
pip install pytest selenium click pyyaml
```

### 调试技巧

#### 启用详细日志
```bash
python test/test_cli.py run --verbose
```

#### 查看测试日志
```bash
tail -f test_results/test.log
```

#### 单独运行测试方法
```python
# 在测试文件中添加
if __name__ == '__main__':
    suite = MyTestSuite()
    asyncio.run(suite.test_specific_method())
```

## 🚀 扩展开发

### 添加新测试套件

1. **创建测试类**
```python
# test/testcases/my_new_tests.py
class MyNewTestSuite:
    async def run_all_tests(self, **kwargs):
        # 实现测试逻辑
        return test_results
```

2. **注册测试套件**
```python
# 在 test_manager.py 中添加
self.test_suites['my_new_tests'] = {
    'class': MyNewTestSuite,
    'type': TestType.UNIT,
    'priority': TestPriority.P1,
    'description': '我的新测试套件'
}
```

3. **添加配置**
```yaml
# test/config/test_config.yaml
test_suites:
  my_new_tests:
    enabled: true
    priority: "p1"
    timeout: 300
```

### 自定义报告格式

```python
def _generate_custom_report(self, results, timestamp):
    # 实现自定义报告逻辑
    pass
```

### 集成CI/CD

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run P0 tests
        run: python test/test_cli.py p0 --report
      - name: Upload test results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test_results/
```

## 📞 支持

### 获取帮助
- 查看命令帮助: `python test/test_cli.py --help`
- 查看测试状态: `python test/test_cli.py status`
- 查看日志文件: `test_results/test.log`

### 报告问题
- 在GitHub Issues中报告问题
- 提供详细的错误信息和日志
- 包含复现步骤和环境信息

---

**PowerAutomation 4.0 测试系统** - 确保代码质量，提升开发效率！ 🚀

