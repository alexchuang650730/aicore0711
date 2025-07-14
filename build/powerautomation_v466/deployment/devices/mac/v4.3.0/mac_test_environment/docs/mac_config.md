# PowerAutomation v4.3.0 Mac配置说明

## 📁 配置文件结构

```
config/
├── mac_config.json          # Mac专用配置
├── claude.yaml             # Claude API配置
├── mac.yaml                # Mac系统集成配置
└── powerautomation.yaml    # 主配置文件
```

## ⚙️ 配置详解

### mac_config.json
Mac平台的核心配置文件，包含版本信息、系统集成设置、快捷键配置等。

### claude.yaml
Claude API的配置文件：
```yaml
claude:
  api_key: "your-api-key-here"
  model: "claude-3-5-sonnet-20241022"
  max_tokens: 8000
  temperature: 0.7
```

### mac.yaml
Mac系统集成配置：
```yaml
mac:
  system_integration:
    dock_icon: true
    menu_bar: true
    notifications: true
  shortcuts:
    toggle_recording: "Cmd+Shift+R"
    quick_test: "Cmd+T"
```

## 🔧 自定义配置

### 修改快捷键
编辑 `config/mac.yaml` 文件中的 shortcuts 部分。

### 调整性能设置
编辑 `config/mac_config.json` 文件中的 performance 部分。

### 配置API密钥
编辑 `config/claude.yaml` 文件，设置您的Claude API密钥。

## 🔄 配置重载

修改配置后，重启ClaudEditor或运行：
```bash
claudeditor --reload-config
```
