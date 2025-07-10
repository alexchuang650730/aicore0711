# ClaudEditor UI Components

ClaudEditor用户界面组件集合，提供完整的测试管理和开发界面。

## 📁 **文件说明**

### **核心界面组件**

#### **claudeditor_ui_main.py**
- **功能**: ClaudEditor主界面入口
- **大小**: 11KB
- **用途**: 主要的用户界面控制器

#### **claudeditor_simple_ui_server.py**
- **功能**: 简化的UI服务器
- **大小**: 20KB
- **用途**: 轻量级的Web界面服务

#### **claudeditor_agui_interface.py**
- **功能**: AG-UI接口组件
- **大小**: 26KB
- **用途**: 智能UI生成和管理界面

#### **claudeditor_testing_management_ui.py**
- **功能**: 测试管理界面
- **大小**: 12KB
- **用途**: 测试用例管理和执行监控

## 🎯 **使用方式**

### **启动主界面**
```bash
python ui/claudeditor/claudeditor_ui_main.py
```

### **启动简化服务器**
```bash
python ui/claudeditor/claudeditor_simple_ui_server.py
```

### **启动测试管理界面**
```bash
python ui/claudeditor/claudeditor_testing_management_ui.py
```

## 🔧 **集成说明**

这些UI组件与以下系统深度集成：

- **core/components/test_mcp/** - 测试管理平台
- **core/components/ag_ui_mcp/** - AG-UI组件生成器
- **core/components/smartui_mcp/** - 智能UI组件
- **core/components/stagewise_mcp/** - 阶段式测试框架

## 📊 **架构关系**

```
ui/claudeditor/
├── claudeditor_ui_main.py              # 主界面控制器
├── claudeditor_simple_ui_server.py     # 轻量级Web服务
├── claudeditor_agui_interface.py       # AG-UI智能界面
└── claudeditor_testing_management_ui.py # 测试管理界面
```

## 🚀 **开发指南**

### **添加新界面组件**
1. 在此目录下创建新的Python文件
2. 遵循 `claudeditor_` 前缀命名规范
3. 集成相应的MCP组件
4. 更新此README文档

### **界面主题**
支持多种界面主题，与AG-UI MCP组件的主题系统保持一致。

---

**维护**: PowerAutomation Team  
**版本**: 4.2.0  
**更新**: 2025-01-09

