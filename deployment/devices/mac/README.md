# 🍎 PowerAutomation v4.1 - macOS版本

[![Platform](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](https://www.apple.com/macos/)
[![Status](https://img.shields.io/badge/status-Available-green.svg)](https://github.com/alexchuang650730/aicore0707)
[![Version](https://img.shields.io/badge/version-4.1.0-blue.svg)](https://github.com/alexchuang650730/aicore0707)

## 📦 macOS部署包

欢迎使用PowerAutomation v4.1的macOS版本！这个目录包含了在Mac上安装和使用ClaudEditor 4.1的完整资源。

### 📁 文件清单

| 文件名 | 大小 | 描述 | SHA256校验 |
|--------|------|------|------------|
| `PowerAutomation_v4.1_ClaudEditor_Mac.tar.gz` | 33MB | 主程序包 | ✅ 已提供 |
| `PowerAutomation_v4.1_ClaudEditor_Mac.tar.gz.sha256` | 65B | 校验和文件 | - |
| `PowerAutomation_v4.1_Mac_使用说明.md` | 45KB | 详细使用说明 | - |
| `README.md` | 8KB | 本文档 | - |

### 🚀 快速开始

#### 第一步：下载和验证
```bash
# 下载主程序包
curl -L -O https://github.com/alexchuang650730/aicore0707/raw/main/deployment/devices/mac/PowerAutomation_v4.1_ClaudEditor_Mac.tar.gz

# 下载校验和文件
curl -L -O https://github.com/alexchuang650730/aicore0707/raw/main/deployment/devices/mac/PowerAutomation_v4.1_ClaudEditor_Mac.tar.gz.sha256

# 验证文件完整性
shasum -a 256 -c PowerAutomation_v4.1_ClaudEditor_Mac.tar.gz.sha256
```

#### 第二步：解压和安装
```bash
# 解压文件
tar -xzf PowerAutomation_v4.1_ClaudEditor_Mac.tar.gz

# 进入项目目录
cd aicore0707

# 运行自动安装程序
./install_mac.sh
```

#### 第三步：启动ClaudEditor
```bash
# 方式1：使用全局命令
claudeditor

# 方式2：使用启动脚本
./start_claudeditor_mac.sh

# 方式3：双击桌面快捷方式
# ClaudEditor.app (安装后自动创建)
```

### 📋 系统要求

#### 最低要求
- **操作系统**: macOS 10.15 (Catalina) 或更高版本
- **处理器**: Intel x64 或 Apple Silicon (M1/M2/M3)
- **内存**: 8GB RAM
- **存储**: 2GB 可用空间
- **网络**: 互联网连接（用于Claude API）

#### 推荐配置
- **操作系统**: macOS 12.0 (Monterey) 或更高版本
- **处理器**: Apple Silicon (M1/M2/M3) 或 Intel i5+
- **内存**: 16GB RAM
- **存储**: 5GB 可用空间
- **网络**: 稳定的宽带连接

### 🎯 核心功能

#### 🎬 录制即测试 (Record-as-Test)
- **零代码测试生成**: 无需编写任何测试代码
- **智能操作识别**: AI自动识别用户操作
- **视频录制回放**: 完整记录操作过程
- **自动验证点**: 智能生成测试验证点

#### 🤖 AI生态系统集成
- **MemoryOS集成**: 智能上下文记忆管理
- **Agent Zero集成**: 有机智能体协作框架
- **Claude深度集成**: 强大的AI代码助手

#### 🛠️ Zen MCP工具生态
- **开发工具集**: 代码生成、调试、测试、文档
- **协作工具集**: 实时编辑、团队沟通、项目管理
- **生产力工具集**: 数据分析、工作流自动化
- **集成工具集**: API集成、数据同步
- **安全工具集**: 身份验证、权限控制、安全扫描

### ⚙️ 配置说明

#### Claude API配置
```yaml
# 编辑 config/claudeditor_config.yaml
claude:
  api_key: "your-claude-api-key-here"  # 必需：您的Claude API密钥
  model: "claude-3-sonnet-20240229"    # 推荐模型
  max_tokens: 4000
  temperature: 0.7
```

#### Mac专用设置
```yaml
# Mac系统集成
mac:
  system_integration:
    dock_icon: true        # 显示Dock图标
    menu_bar: true         # 显示菜单栏
    notifications: true    # 启用通知
  
  shortcuts:
    toggle_recording: "Cmd+Shift+R"    # 切换录制
    quick_test: "Cmd+T"                # 快速测试
    open_ai_chat: "Cmd+Shift+A"        # 打开AI聊天
```

### 🔧 故障排除

#### 常见问题

**1. 安装失败**
```bash
# 检查系统权限
sudo xcode-select --install

# 重新运行安装
./install_mac.sh
```

**2. 启动失败**
```bash
# 检查Python版本
python3 --version

# 查看错误日志
tail -f ~/Applications/PowerAutomation/logs/claudeditor.log
```

**3. API连接问题**
```bash
# 测试API连接
claudeditor test-connection

# 检查网络连接
ping api.anthropic.com
```

#### 获取帮助
- **详细文档**: [PowerAutomation_v4.1_Mac_使用说明.md](PowerAutomation_v4.1_Mac_使用说明.md)
- **GitHub Issues**: [提交问题](https://github.com/alexchuang650730/aicore0707/issues)
- **社区讨论**: [GitHub Discussions](https://github.com/alexchuang650730/aicore0707/discussions)

### 📈 性能指标

#### 响应性能
- **启动时间**: < 10秒
- **代码补全延迟**: < 200ms
- **录制响应时间**: < 100ms
- **AI分析时间**: < 2秒

#### 资源使用
- **内存占用**: 200-500MB (空闲时)
- **CPU使用**: < 5% (空闲时)
- **磁盘空间**: 150MB (安装后)

### 🔄 更新和维护

#### 检查更新
```bash
# 检查新版本
claudeditor --check-updates

# 手动更新
claudeditor --update
```

#### 备份数据
```bash
# 备份配置和数据
tar -czf powerautomation_backup_$(date +%Y%m%d).tar.gz \
  ~/Applications/PowerAutomation/config/ \
  ~/Applications/PowerAutomation/data/
```

### 🎉 开始使用

1. **阅读完整文档**: [PowerAutomation_v4.1_Mac_使用说明.md](PowerAutomation_v4.1_Mac_使用说明.md)
2. **配置Claude API**: 获取并配置您的API密钥
3. **探索功能**: 尝试录制即测试和AI代码助手
4. **加入社区**: 参与GitHub讨论和反馈

---

**PowerAutomation v4.1 macOS版本** - 为Mac用户量身定制的AI自动化体验 🚀

*开始您的AI辅助开发之旅！*

