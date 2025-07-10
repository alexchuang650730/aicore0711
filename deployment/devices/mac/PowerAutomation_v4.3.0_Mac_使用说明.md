# PowerAutomation v4.3.0 - macOS版本使用指南

## 🍎 ClaudEditor 4.3 Mac版本

欢迎使用PowerAutomation v4.3.0的macOS版本！本指南将帮助您在Mac上安装和使用ClaudEditor 4.3。

## 📦 系统要求

### 最低要求
- **操作系统**: macOS 11.0 (Big Sur) 或更高版本
- **处理器**: Intel x64 或 Apple Silicon (M1/M2/M3/M4)
- **内存**: 8GB RAM
- **存储**: 3GB 可用空间
- **网络**: 互联网连接（用于Claude API）

### 推荐配置
- **操作系统**: macOS 13.0 (Ventura) 或更高版本
- **处理器**: Apple Silicon (M2/M3/M4) 或 Intel i7+
- **内存**: 16GB RAM
- **存储**: 8GB 可用空间
- **网络**: 稳定的宽带连接

## 🚀 安装指南

### 方式一：自动安装 (推荐)
```shell
# 下载安装包
curl -L -O https://github.com/alexchuang650730/aicore0707/releases/download/v4.3.0/PowerAutomation_v4.3.0_Mac.tar.gz

# 解压文件
tar -xzf PowerAutomation_v4.3.0_Mac.tar.gz

# 进入目录并安装
cd aicore0707
chmod +x install_mac.sh
./install_mac.sh
```

### 方式二：手动安装
```shell
# 克隆仓库
git clone https://github.com/alexchuang650730/aicore0707.git
cd aicore0707

# 安装依赖
pip3 install -r requirements.txt

# 安装ClaudEditor
cd claudeditor
npm install
npm run tauri:build
```

## 🎯 ClaudEditor 4.3 核心功能

### **🤖 AI代码助手**
- **Claude 3.5 Sonnet集成**: 最先进的AI代码生成
- **智能补全**: 上下文感知的代码补全
- **代码解释**: AI驱动的代码解释和优化建议
- **错误修复**: 自动检测和修复代码错误

### **🎬 录制即测试 (Record-as-Test)**
- **零代码测试**: 无需编写测试代码
- **智能录制**: AI识别用户操作并生成测试
- **视频回放**: 完整记录操作过程
- **自动验证**: 智能生成测试验证点

### **🛠️ MCP工具生态**
- **2,797+ MCP工具**: 完整的工具生态系统
- **一键安装**: 快速安装和配置MCP工具
- **智能推荐**: AI推荐适合的工具
- **自定义工具**: 支持创建自定义MCP工具

### **👥 实时协作**
- **多人编辑**: 支持多人同时编辑代码
- **实时同步**: 即时同步代码变更
- **语音通话**: 内置语音通话功能
- **屏幕共享**: 支持屏幕共享和演示

## ⚙️ 配置说明

### Claude API配置
```yaml
# 编辑 ~/.powerautomation/config/claude.yaml
claude:
  api_key: "your-claude-api-key-here"  # 必需：您的Claude API密钥
  model: "claude-3-5-sonnet-20241022"  # 推荐模型
  max_tokens: 8000
  temperature: 0.7
```

### Mac系统集成
```yaml
# 编辑 ~/.powerautomation/config/mac.yaml
mac:
  system_integration:
    dock_icon: true        # 显示Dock图标
    menu_bar: true         # 显示菜单栏
    notifications: true    # 启用通知
    file_associations: true # 文件关联
  
  shortcuts:
    toggle_recording: "Cmd+Shift+R"    # 切换录制
    quick_test: "Cmd+T"                # 快速测试
    open_ai_chat: "Cmd+Shift+A"        # 打开AI聊天
    save_project: "Cmd+S"              # 保存项目
```

## 🎮 使用指南

### 启动ClaudEditor 4.3
```shell
# 方式1：使用应用程序
# 在Launchpad中找到ClaudEditor 4.3并点击

# 方式2：使用命令行
claudeditor

# 方式3：使用启动脚本
./start_claudeditor_mac.sh
```

### 基本操作
1. **创建项目**: File → New Project 或 Cmd+N
2. **打开文件**: File → Open 或 Cmd+O
3. **AI助手**: 点击AI图标或 Cmd+Shift+A
4. **录制测试**: Tools → Record Test 或 Cmd+Shift+R
5. **运行测试**: Tools → Run Tests 或 Cmd+T

### 高级功能
1. **MCP工具管理**: Tools → MCP Tools Manager
2. **实时协作**: Collaboration → Start Session
3. **项目模板**: File → New from Template
4. **代码生成**: AI → Generate Code
5. **自动重构**: AI → Refactor Code

## 🔧 故障排除

### 常见问题

**1. 安装失败**
```shell
# 检查Xcode命令行工具
xcode-select --install

# 检查Python版本
python3 --version

# 重新安装
./install_mac.sh --force
```

**2. 启动失败**
```shell
# 检查权限
sudo chmod +x /Applications/ClaudEditor.app/Contents/MacOS/ClaudEditor

# 查看日志
tail -f ~/Library/Logs/ClaudEditor/app.log
```

**3. API连接问题**
```shell
# 测试API连接
claudeditor test-api

# 检查网络
ping api.anthropic.com

# 重新配置API
claudeditor config --api-key your-new-key
```

**4. 性能问题**
```shell
# 清理缓存
claudeditor clear-cache

# 重置配置
claudeditor reset-config

# 检查系统资源
top -pid $(pgrep ClaudEditor)
```

## 📈 性能指标

### 启动性能
- **冷启动**: < 8秒
- **热启动**: < 3秒
- **项目加载**: < 2秒

### 运行性能
- **代码补全延迟**: < 150ms
- **AI响应时间**: < 2秒
- **录制响应**: < 50ms
- **文件保存**: < 100ms

### 资源使用
- **内存占用**: 150-400MB (空闲时)
- **CPU使用**: < 3% (空闲时)
- **磁盘空间**: 200MB (安装后)

## 🔄 更新和维护

### 检查更新
```shell
# 检查新版本
claudeditor --check-updates

# 自动更新
claudeditor --update

# 手动更新
curl -L https://github.com/alexchuang650730/aicore0707/releases/latest | sh
```

### 备份数据
```shell
# 备份配置和项目
tar -czf claudeditor_backup_$(date +%Y%m%d).tar.gz   ~/.powerautomation/   ~/ClaudEditor/
```

### 卸载
```shell
# 完全卸载
sudo rm -rf /Applications/ClaudEditor.app
rm -rf ~/.powerautomation
rm -rf ~/ClaudEditor
```

## 🎉 开始使用

### 第一次使用
1. **获取Claude API密钥**: 访问 https://console.anthropic.com
2. **配置API**: 在设置中输入您的API密钥
3. **创建第一个项目**: 使用项目模板快速开始
4. **体验AI助手**: 尝试代码生成和解释功能
5. **录制测试**: 使用录制即测试功能

### 进阶使用
1. **探索MCP工具**: 安装和使用各种MCP工具
2. **团队协作**: 邀请团队成员进行实时协作
3. **自定义配置**: 根据需要调整设置和快捷键
4. **集成工作流**: 将ClaudEditor集成到现有工作流中

## 📞 获取帮助

- **官方文档**: https://docs.powerautomation.dev
- **GitHub Issues**: https://github.com/alexchuang650730/aicore0707/issues
- **社区讨论**: https://github.com/alexchuang650730/aicore0707/discussions
- **邮件支持**: support@powerautomation.dev

**ClaudEditor 4.3 macOS版本** - 为Mac用户量身定制的AI开发体验 🚀

_开始您的AI辅助开发之旅！_
