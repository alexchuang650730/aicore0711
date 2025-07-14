# Test MCP - 统一测试管理组件

PowerAutomation 4.2.0 的核心测试管理组件，整合了所有测试相关功能，并与 SmartUI MCP、Stagewise MCP 和 AG-UI MCP 协同工作。

## 🎯 **组件概述**

Test MCP 是一个统一的测试管理平台，提供完整的AI驱动测试解决方案：

- **🧪 测试框架管理** - 统一管理所有测试框架和工具
- **📋 模板化测试** - 基于模板的快速测试创建
- **📊 结果分析** - 智能测试结果分析和报告
- **🎼 套件编排** - 自动化测试套件编排和执行
- **🔗 跨组件集成** - 与其他MCP组件的深度集成

## 📁 **目录结构**

```
test_mcp/
├── __init__.py                    # 组件初始化和导出
├── test_mcp_service.py           # 主服务类
├── test_orchestrator.py          # 测试编排器
├── smartui_integration.py        # SmartUI MCP集成
├── stagewise_integration.py      # Stagewise MCP集成
├── agui_integration.py           # AG-UI MCP集成
├── config/                       # 配置文件
│   └── test_mcp_config.json     # 主配置文件
├── frameworks/                   # 测试框架
│   ├── ui_tests/                # UI测试框架
│   ├── config/                  # 框架配置
│   ├── demos/                   # 演示和示例
│   ├── integration/             # 集成测试
│   ├── reports/                 # 测试报告
│   ├── runners/                 # 测试运行器
│   └── testcases/              # 测试用例
├── templates/                    # 测试模板
│   ├── pages/                   # 页面模板
│   ├── scenarios/               # 场景模板
│   ├── assets/                  # 资源文件
│   └── *.py                     # 模板执行器
├── results/                      # 测试结果
│   └── *.json                   # 结果文件
└── suites/                      # 测试套件
    ├── unit_tests/              # 单元测试
    ├── reports/                 # 套件报告
    └── *.py                     # 测试套件文件
```

## 🚀 **核心功能**

### **1. 统一测试管理**
- **多框架支持**: UI测试、API测试、E2E测试、集成测试
- **并行执行**: 支持多线程并行测试执行
- **智能调度**: 基于资源和依赖的智能测试调度
- **实时监控**: 测试执行过程的实时监控和控制

### **2. AI驱动测试生成**
- **SmartUI集成**: 自动生成UI组件测试
- **Stagewise集成**: 可视化测试和录制即测试
- **AG-UI集成**: 智能测试管理界面生成
- **模板化生成**: 基于模板的快速测试生成

### **3. 智能结果分析**
- **多格式支持**: JSON、HTML、XML等多种报告格式
- **可视化展示**: 图表和仪表板形式的结果展示
- **趋势分析**: 测试结果的历史趋势分析
- **智能洞察**: AI驱动的测试结果洞察和建议

### **4. 跨组件协同**
- **SmartUI MCP**: UI组件生成和自动化测试
- **Stagewise MCP**: 可视化测试和元素检查
- **AG-UI MCP**: 测试管理界面的动态生成
- **MemoryOS MCP**: 测试历史和学习记忆

## 🔧 **使用方法**

### **基础使用**

```python
from core.components.test_mcp import TestMCPService

# 初始化服务
service = TestMCPService()
await service.start_service()

# 运行测试套件
result = await service.run_test_suite("ui_tests")

# 生成UI测试
ui_test = await service.generate_ui_test({
    "component_type": "button",
    "props": {"text": "Click Me", "variant": "primary"}
})

# 运行可视化测试
visual_result = await service.run_visual_test({
    "page_url": "http://localhost:3000",
    "baseline": "baseline.png"
})
```

### **高级功能**

```python
# 生成测试管理界面
ui_result = await service.generate_test_ui({
    "type": "complete",
    "theme": "claudeditor_dark",
    "features": ["dashboard", "monitor", "ai_suggestions"]
})

# 开始录制测试
recording = await service.start_recording({
    "name": "用户登录流程",
    "target_url": "http://localhost:3000/login"
})

# 从录制生成测试
test_code = await service.generate_test_from_recording(
    recording["recording_id"],
    {"test_name": "login_flow_test"}
)
```

## ⚙️ **配置说明**

### **主要配置项**

```json
{
  "test_frameworks": {
    "ui_tests": {
      "enabled": true,
      "parallel": true,
      "browser": "chromium",
      "timeout": 30
    }
  },
  "integrations": {
    "smartui_mcp": {
      "enabled": true,
      "auto_generate": true
    },
    "stagewise_mcp": {
      "enabled": true,
      "visual_testing": true
    },
    "ag_ui_mcp": {
      "enabled": true,
      "auto_generate_ui": true,
      "default_theme": "claudeditor_dark"
    }
  }
}
```

### **集成配置**

- **SmartUI集成**: 自动UI组件测试生成
- **Stagewise集成**: 可视化测试和录制功能
- **AG-UI集成**: 测试管理界面自动生成

## 🔗 **组件集成**

### **SmartUI MCP 集成**
```python
# 生成UI组件测试
component_spec = {
    "type": "form",
    "fields": ["username", "password"],
    "validation": True
}
test_result = await service.generate_ui_test(component_spec)
```

### **Stagewise MCP 集成**
```python
# 可视化测试
visual_spec = {
    "page_url": "http://localhost:3000",
    "elements": [".header", ".nav", ".content"],
    "threshold": 0.1
}
visual_result = await service.run_visual_test(visual_spec)
```

### **AG-UI MCP 集成**
```python
# 生成测试仪表板
dashboard_spec = {
    "theme": "claudeditor_dark",
    "features": ["overview", "metrics", "logs"],
    "real_time": True
}
dashboard = await service.generate_test_ui({
    "type": "dashboard",
    **dashboard_spec
})
```

## 📊 **测试类型支持**

### **UI测试**
- **基础操作测试**: 点击、输入、导航等
- **复杂工作流测试**: 多步骤业务流程测试
- **响应式测试**: 不同设备和屏幕尺寸测试
- **可访问性测试**: WCAG合规性测试

### **API测试**
- **RESTful API测试**: GET、POST、PUT、DELETE等
- **GraphQL测试**: 查询和变更测试
- **认证测试**: 各种认证机制测试
- **性能测试**: API响应时间和吞吐量测试

### **E2E测试**
- **用户旅程测试**: 完整用户流程测试
- **跨浏览器测试**: 多浏览器兼容性测试
- **数据驱动测试**: 基于数据集的测试
- **环境集成测试**: 不同环境的集成测试

### **可视化测试**
- **视觉回归测试**: 界面变化检测
- **截图对比测试**: 像素级对比
- **布局测试**: 响应式布局验证
- **主题测试**: 不同主题下的视觉验证

## 🎨 **UI生成功能**

### **支持的UI组件**
- **测试仪表板**: 测试概览和状态监控
- **执行监控器**: 实时测试执行监控
- **结果查看器**: 测试结果的可视化展示
- **录制控制面板**: 测试录制的控制界面
- **AI建议面板**: 智能测试建议和优化
- **代码生成面板**: 测试代码的生成和编辑

### **主题支持**
- **ClaudEditor Dark**: 深色主题，适合开发环境
- **ClaudEditor Light**: 浅色主题，适合日常使用
- **Testing Focused**: 专注测试的主题设计
- **Developer Mode**: 开发者模式主题

## 📈 **性能特性**

- **并行执行**: 支持最多16个并发测试任务
- **智能缓存**: 测试结果和组件的智能缓存
- **资源优化**: 内存和CPU使用的优化管理
- **增量测试**: 只运行变更相关的测试

## 🔒 **安全特性**

- **输入验证**: 所有输入的安全验证
- **安全存储**: 敏感数据的加密存储
- **审计日志**: 完整的操作审计日志
- **权限控制**: 基于角色的权限管理

## 🚀 **快速开始**

### **1. 安装依赖**
```bash
pip install -r requirements.txt
```

### **2. 启动服务**
```python
from core.components.test_mcp import get_test_mcp_service

service = get_test_mcp_service()
await service.start_service()
```

### **3. 运行第一个测试**
```python
# 运行UI测试套件
result = await service.run_test_suite("ui_tests")
print(f"测试结果: {result}")
```

### **4. 生成测试界面**
```python
# 生成完整的测试管理界面
interface = await service.generate_test_ui({
    "type": "complete",
    "theme": "claudeditor_dark"
})
```

## 🔄 **版本历史**

### **v4.2.0 (当前版本)**
- ✅ 完整的MCP组件集成
- ✅ AG-UI测试界面生成
- ✅ 智能测试编排
- ✅ 多框架统一管理
- ✅ 实时监控和报告

### **v4.1.0**
- ✅ SmartUI和Stagewise集成
- ✅ 基础测试框架整合
- ✅ 录制即测试功能

## 🤝 **贡献指南**

1. Fork 项目仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📞 **技术支持**

- **GitHub Issues**: https://github.com/alexchuang650730/aicore0707/issues
- **文档**: https://docs.powerautomation.ai/test-mcp
- **社区**: https://community.powerautomation.ai

---

**🧪 Test MCP - PowerAutomation 4.2.0 统一测试管理组件**

*让AI驱动的测试管理变得简单而强大*

