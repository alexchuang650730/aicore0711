# ClaudEditor UI自动化测试系统 v4.1

## 🎯 概述

ClaudEditor UI自动化测试系统是一个完整的端到端测试解决方案，集成了：

- **Stagewise MCP** - 阶段式测试管理
- **Recorder Workflow MCP** - UI操作录制和回放
- **智能测试模板** - 10个核心测试用例
- **多环境支持** - 本地、预发布、生产环境
- **可视化报告** - 详细的测试结果和录制文件

## 🚀 快速开始

### 1. 环境设置

```bash
# 设置测试环境
./start_ui_tests.sh setup
```

### 2. 运行测试

```bash
# 运行冒烟测试 (推荐首次使用)
./start_ui_tests.sh smoke

# 运行核心功能测试
./start_ui_tests.sh core

# 运行完整测试套件
./start_ui_tests.sh full
```

### 3. 查看结果

测试完成后，结果将保存在 `test_results/` 目录：
- `test_report_*.json` - 详细测试报告
- `screenshots/` - 测试截图
- `recordings/` - 操作录制视频

## 📋 测试用例

### 核心测试用例 (10个)

| ID | 名称 | 描述 | 阶段 | 优先级 |
|----|------|------|------|--------|
| TC001 | 应用启动和加载测试 | 验证ClaudEditor应用正常启动 | setup | 高 |
| TC002 | Monaco编辑器加载测试 | 验证代码编辑器功能 | ui_load | 高 |
| TC003 | AI助手面板测试 | 验证AI助手基本功能 | user_interaction | 高 |
| TC004 | 多模型选择测试 | 验证Claude/Gemini模型切换 | user_interaction | 中 |
| TC005 | 工具管理器测试 | 验证MCP-Zero Smart Engine | user_interaction | 中 |
| TC006 | 实时协作测试 | 验证协作功能 | user_interaction | 中 |
| TC007 | API集成测试 | 验证前后端API集成 | api_testing | 高 |
| TC008 | 性能监控测试 | 验证性能统计功能 | performance | 中 |
| TC009 | 端到端工作流测试 | 完整编程助手工作流 | integration | 高 |
| TC010 | 错误处理测试 | 验证错误处理能力 | integration | 中 |

### 测试阶段

1. **Setup** - 环境设置和服务启动
2. **UI Load** - 界面加载和基础元素验证
3. **User Interaction** - 用户交互功能测试
4. **API Testing** - 后端API功能测试
5. **Integration** - 端到端集成测试
6. **Performance** - 性能和监控测试
7. **Cleanup** - 清理和资源释放

## 🛠️ 使用方法

### 命令行选项

```bash
# 基础用法
python3 run_ui_tests.py [选项]

# 测试类型选择
--smoke              # 冒烟测试
--core               # 核心功能测试
--integration        # 集成测试
--tags <标签>        # 按标签过滤

# 优先级选择
--high-priority      # 高优先级测试
--medium-priority    # 中优先级测试
--low-priority       # 低优先级测试

# 阶段选择
--stage <阶段名>     # 特定阶段测试

# 环境选择
--environment <环境> # local/staging/production

# 浏览器选项
--headless           # 无头模式

# 录制功能
--replay <ID>        # 回放录制
--list-recordings    # 列出录制文件
```

### 使用示例

```bash
# 1. 快速冒烟测试
./start_ui_tests.sh smoke

# 2. 无头模式运行核心测试
./start_ui_tests.sh core --headless

# 3. 只测试AI功能
python3 run_ui_tests.py --tags ai,assistant

# 4. 测试特定阶段
python3 run_ui_tests.py --stage user_interaction

# 5. 预发布环境测试
python3 run_ui_tests.py --environment staging --smoke

# 6. 回放录制
python3 run_ui_tests.py --replay TC003_AI助手面板测试

# 7. 查看所有录制
python3 run_ui_tests.py --list-recordings
```

## 📊 测试报告

### 报告格式

测试完成后生成JSON格式报告：

```json
{
  "summary": {
    "total_tests": 10,
    "passed": 8,
    "failed": 1,
    "errors": 1,
    "success_rate": 80.0,
    "total_execution_time": 245.67,
    "timestamp": "2025-01-07T10:30:00"
  },
  "test_results": [...],
  "config": {...}
}
```

### 关键指标

- **成功率** - 通过测试的百分比
- **执行时间** - 总测试耗时
- **错误分析** - 失败测试的详细信息
- **录制文件** - 每个测试的操作录制

## 🎬 录制功能

### 自动录制

每个测试用例都会自动录制：
- **屏幕录制** - 完整的操作视频
- **步骤截图** - 关键操作的截图
- **操作数据** - JSON格式的操作序列

### 录制文件结构

```
test_results/
├── recordings/
│   ├── TC001_应用启动测试.mp4
│   ├── TC001_应用启动测试.json
│   └── ...
├── screenshots/
│   ├── TC001_app_loaded.png
│   ├── TC003_ai_assistant_response.png
│   └── ...
└── reports/
    └── test_report_20250107_103000.json
```

### 回放功能

```bash
# 回放特定录制
python3 run_ui_tests.py --replay TC003_AI助手面板测试

# 列出所有录制
python3 run_ui_tests.py --list-recordings
```

## ⚙️ 配置

### 测试配置文件 (test_config.json)

```json
{
  "base_url": "http://localhost:3000",
  "api_base_url": "http://localhost:5000",
  "output_directory": "./test_results",
  "screenshot_on_failure": true,
  "video_recording": true,
  "browser_options": {
    "headless": false,
    "window_size": [1920, 1080]
  },
  "test_environments": {
    "local": {...},
    "staging": {...},
    "production": {...}
  }
}
```

### 环境变量

```bash
# 设置API密钥
export CLAUDE_API_KEY="your-claude-api-key"
export GEMINI_API_KEY="your-gemini-api-key"

# 设置测试环境
export TEST_ENVIRONMENT="local"
export TEST_HEADLESS="false"
```

## 🔧 故障排除

### 常见问题

1. **服务未启动**
   ```bash
   # 检查服务状态
   curl http://localhost:3000
   curl http://localhost:5000/api/ai-assistant/health
   
   # 手动启动服务
   ./start_ui_tests.sh setup
   ```

2. **浏览器驱动问题**
   ```bash
   # 安装/更新浏览器驱动
   pip3 install webdriver-manager
   ```

3. **权限问题**
   ```bash
   # 设置执行权限
   chmod +x start_ui_tests.sh
   ```

4. **依赖缺失**
   ```bash
   # 安装Python依赖
   pip3 install asyncio aiohttp selenium
   ```

### 日志查看

```bash
# 查看测试日志
tail -f ui_test_$(date +%Y%m%d).log

# 查看详细输出
python3 run_ui_tests.py --verbose --smoke
```

## 📈 性能优化

### 并行执行

```json
{
  "parallel_execution": {
    "enabled": true,
    "max_workers": 3,
    "test_isolation": true
  }
}
```

### 录制优化

```json
{
  "recording": {
    "quality": "medium",
    "fps": 15,
    "auto_cleanup": true,
    "retention_days": 7
  }
}
```

## 🔄 CI/CD 集成

### GitHub Actions

```yaml
name: UI Tests
on: [push, pull_request]
jobs:
  ui-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run UI Tests
        run: ./start_ui_tests.sh smoke --headless
      - name: Upload test results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test_results/
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('UI Tests') {
            steps {
                sh './start_ui_tests.sh core --headless'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'test_results/**/*'
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'test_results',
                        reportFiles: '*.json',
                        reportName: 'UI Test Report'
                    ])
                }
            }
        }
    }
}
```

## 📚 扩展开发

### 添加新测试用例

1. 在 `ClaudEditorUITestTemplate.get_test_cases()` 中添加新的 `TestCase`
2. 定义测试步骤和预期结果
3. 设置适当的标签和优先级

### 自定义验证器

```python
async def custom_verification(self, target, expected):
    """自定义验证逻辑"""
    # 实现自定义验证
    return True
```

### 集成新的MCP组件

```python
from your_mcp_component import YourMCPComponent

class ExtendedTestTemplate(ClaudEditorUITestTemplate):
    def __init__(self):
        super().__init__()
        self.your_mcp = YourMCPComponent()
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 添加测试用例
4. 提交 Pull Request

## 📄 许可证

MIT License - 详见 LICENSE 文件

## 📞 支持

- 📧 Email: support@powerautomation.com
- 📱 GitHub Issues: [项目Issues页面]
- 📖 文档: [在线文档地址]

---

**ClaudEditor UI自动化测试系统 v4.1** - 让UI测试变得简单而强大！ 🚀

