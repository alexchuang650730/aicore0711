# 🍎 PowerAutomation v4.1 - ClaudEditor 4.1 Mac使用说明

[![Version](https://img.shields.io/badge/version-4.1.0-blue.svg)](https://github.com/alexchuang650730/aicore0707)
[![Platform](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](https://www.apple.com/macos/)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)

欢迎使用PowerAutomation v4.1！这是一个专为Mac用户优化的企业级AI自动化平台，集成了革命性的录制即测试(Record-as-Test)功能、AI生态系统深度集成和完整的商业化解决方案。

## 📦 包装内容

您下载的 `PowerAutomation_v4.1_ClaudEditor_Mac.tar.gz` 包含：

- **完整的PowerAutomation v4.1源代码** (92,168行代码)
- **ClaudEditor 4.1完整功能**
- **Mac专用启动脚本和配置文件**
- **自动安装程序**
- **完整的文档和示例**

## 🚀 快速开始

### 第一步：解压文件

```bash
# 解压下载的文件
tar -xzf PowerAutomation_v4.1_ClaudEditor_Mac.tar.gz

# 进入项目目录
cd aicore0707
```

### 第二步：运行自动安装程序

```bash
# 运行Mac自动安装程序
./install_mac.sh
```

安装程序将自动：
- ✅ 检查macOS系统兼容性
- ✅ 安装Homebrew (如果未安装)
- ✅ 安装Python 3.11和Node.js
- ✅ 安装所有必要的系统依赖
- ✅ 创建应用程序目录和快捷方式
- ✅ 配置环境变量

### 第三步：启动ClaudEditor

安装完成后，您可以通过以下方式启动：

**方式1：使用桌面快捷方式**
```bash
# 双击桌面上的 ClaudEditor.app
```

**方式2：使用命令行**
```bash
# 在任何位置运行
claudeditor

# 或者直接运行启动脚本
./start_claudeditor_mac.sh
```

**方式3：使用完整路径**
```bash
# 从安装目录启动
~/Applications/PowerAutomation/start_claudeditor_mac.sh
```

## ⚙️ 配置设置

### 编辑配置文件

在首次启动前，您需要配置Claude API密钥：

```bash
# 打开配置文件
claudeditor config

# 或者手动编辑
nano ~/Applications/PowerAutomation/config/claudeditor_config.yaml
```

在配置文件中找到以下部分并填入您的API密钥：

```yaml
claude:
  api_key: "your-claude-api-key-here"  # 在此处填入您的Claude API密钥
  model: "claude-3-sonnet-20240229"
  max_tokens: 4000
```

### 重要配置项

```yaml
# 功能开关
features:
  record_as_test:
    enabled: true          # 启用录制即测试
    auto_save: true        # 自动保存录制
    video_recording: true  # 启用视频录制
  
  zen_mcp:
    enabled: true          # 启用Zen MCP工具生态
  
  realtime_collaboration:
    enabled: true          # 启用实时协作
    max_participants: 10   # 最大参与者数量

# Mac专用设置
mac:
  system_integration:
    dock_icon: true        # 显示Dock图标
    menu_bar: true         # 显示菜单栏
    notifications: true    # 启用通知
  
  shortcuts:
    toggle_recording: "Cmd+Shift+R"  # 切换录制快捷键
    quick_test: "Cmd+T"              # 快速测试快捷键
    open_ai_chat: "Cmd+Shift+A"      # 打开AI聊天快捷键
```

## 🎯 核心功能使用

### 1. 录制即测试 (Record-as-Test)

这是PowerAutomation v4.1的革命性功能：

```bash
# 启动ClaudEditor后，使用快捷键开始录制
Cmd+Shift+R  # 开始/停止录制

# 或者在Web界面中点击"开始录制"按钮
```

**录制流程：**
1. 🎬 点击"开始录制"或按 `Cmd+Shift+R`
2. 🖱️ 在应用程序中执行您想要自动化的操作
3. 🛑 完成后点击"停止录制"
4. 🤖 AI自动生成测试用例和验证点
5. ▶️ 点击"回放测试"验证自动化流程

**特性：**
- ✨ **零代码测试**：无需编写任何代码
- 🎥 **视频录制**：完整记录操作过程
- 🧠 **AI智能分析**：自动识别关键操作
- 🔄 **智能回放**：准确重现用户操作
- 📊 **自动验证**：智能生成验证点

### 2. AI生态系统集成

**MemoryOS集成：**
```python
# 在Python中使用
from core.components.ai_ecosystem_integration import MemoryOSIntegration

memory_os = MemoryOSIntegration()
await memory_os.save_context("项目背景", context_data)
context = await memory_os.retrieve_context("项目背景")
```

**Agent Zero集成：**
```python
# 创建智能体协作
from core.components.ai_ecosystem_integration import AgentZeroIntegration

agent_zero = AgentZeroIntegration()
collaboration = await agent_zero.create_collaboration_session()
```

### 3. Zen MCP工具生态

PowerAutomation v4.1包含5大工具集：

**开发工具集：**
- 🔧 智能代码生成
- 🐛 自动调试助手
- 🧪 测试用例生成
- 📝 代码文档生成

**协作工具集：**
- 👥 实时协作编辑
- 💬 团队沟通工具
- 📋 项目管理系统
- 🔄 版本控制集成

**生产力工具集：**
- 📄 文档自动生成
- 📊 数据分析工具
- 🤖 工作流自动化
- 📈 性能监控

**集成工具集：**
- 🔌 API集成工具
- 🔄 数据同步工具
- 🌐 第三方服务集成
- 📡 Webhook管理

**安全工具集：**
- 🔐 身份验证管理
- 🛡️ 权限控制系统
- 📋 审计日志
- 🔍 安全扫描

### 4. 实时协作功能

```bash
# 创建协作会话
curl -X POST http://localhost:8080/api/collaboration/sessions \
  -H "Content-Type: application/json" \
  -d '{"name": "代码审查会话", "owner_id": "user_123"}'

# 加入协作会话
curl -X POST http://localhost:8080/api/collaboration/sessions/{session_id}/join \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_456"}'
```

## 🌐 Web界面使用

启动ClaudEditor后，打开浏览器访问：

- **主界面**: http://127.0.0.1:8080
- **管理面板**: http://127.0.0.1:8081
- **API文档**: http://127.0.0.1:8080/docs

### 主要界面功能

**1. 录制控制面板**
- 🎬 开始/停止录制按钮
- 📹 录制状态指示器
- ⚙️ 录制设置选项
- 📊 录制统计信息

**2. 测试管理界面**
- 📋 测试用例列表
- ▶️ 测试执行控制
- 📈 测试结果分析
- 🔄 测试回放功能

**3. AI助手面板**
- 💬 智能对话界面
- 🧠 上下文管理
- 🔍 智能搜索
- 💡 建议和提示

**4. 协作工作区**
- 👥 在线用户列表
- 💬 实时聊天
- 📝 共享编辑器
- 🔄 变更同步

## 🛠️ 高级配置

### 性能优化

```yaml
# 在 claudeditor_config.yaml 中
performance:
  worker_processes: 4      # 工作进程数
  max_connections: 1000    # 最大连接数
  request_timeout: 30      # 请求超时时间
  keepalive_timeout: 5     # 保持连接超时

# 缓存配置
cache:
  type: "memory"           # 缓存类型
  max_size: 1000          # 最大缓存大小
  ttl: 3600               # 缓存生存时间
```

### 安全设置

```yaml
security:
  secret_key: "your-secret-key-here"  # 请更改为随机密钥
  session_timeout: 3600               # 会话超时时间
  max_login_attempts: 5               # 最大登录尝试次数
  password_min_length: 8              # 密码最小长度
```

### 日志配置

```yaml
logging:
  level: "INFO"                       # 日志级别
  file: "logs/claudeditor.log"        # 日志文件
  max_size: "10MB"                    # 最大文件大小
  backup_count: 5                     # 备份文件数量
```

## 🔧 故障排除

### 常见问题

**1. 启动失败**
```bash
# 检查Python版本
python3 --version

# 检查依赖安装
pip3 list | grep fastapi

# 查看错误日志
tail -f ~/Applications/PowerAutomation/logs/claudeditor.log
```

**2. 端口冲突**
```bash
# 检查端口占用
lsof -i :8080

# 修改配置文件中的端口
nano ~/Applications/PowerAutomation/config/claudeditor_config.yaml
```

**3. 权限问题**
```bash
# 修复权限
chmod +x ~/Applications/PowerAutomation/start_claudeditor_mac.sh
chmod -R 755 ~/Applications/PowerAutomation/
```

**4. 依赖问题**
```bash
# 重新安装依赖
cd ~/Applications/PowerAutomation
pip3 install -r requirements.txt --force-reinstall
```

### 重置配置

```bash
# 备份当前配置
cp ~/Applications/PowerAutomation/config/claudeditor_config.yaml ~/claudeditor_config_backup.yaml

# 重置为默认配置
cd ~/Applications/PowerAutomation
./start_claudeditor_mac.sh config
```

### 完全重新安装

```bash
# 删除应用程序目录
rm -rf ~/Applications/PowerAutomation

# 删除桌面快捷方式
rm -rf ~/Desktop/ClaudEditor.app

# 重新解压和安装
tar -xzf PowerAutomation_v4.1_ClaudEditor_Mac.tar.gz
cd aicore0707
./install_mac.sh
```

## 📚 使用示例

### 示例1：自动化Web测试

1. **启动录制**
   ```bash
   # 按 Cmd+Shift+R 开始录制
   ```

2. **执行操作**
   - 打开浏览器
   - 访问目标网站
   - 填写表单
   - 点击提交按钮
   - 验证结果

3. **停止录制**
   ```bash
   # 再次按 Cmd+Shift+R 停止录制
   ```

4. **生成测试**
   - AI自动分析操作序列
   - 生成测试用例代码
   - 创建验证点

5. **回放测试**
   - 点击"回放测试"按钮
   - 观察自动化执行过程
   - 查看测试结果

### 示例2：API开发和测试

1. **创建API项目**
   ```python
   # 使用代码生成工具
   from core.components.zen_mcp.development_tools import CodeGenerationToolkit
   
   toolkit = CodeGenerationToolkit()
   api_code = await toolkit.generate_api_endpoint(
       name="user_management",
       methods=["GET", "POST", "PUT", "DELETE"],
       database="postgresql"
   )
   ```

2. **自动生成测试**
   ```python
   # 自动生成API测试用例
   test_cases = await toolkit.generate_api_tests(api_code)
   ```

3. **协作开发**
   - 邀请团队成员加入协作会话
   - 实时编辑和讨论代码
   - 自动同步变更

### 示例3：数据分析自动化

1. **录制数据处理流程**
   - 启动录制
   - 打开Excel或数据分析工具
   - 执行数据清洗和分析操作
   - 生成图表和报告

2. **AI优化流程**
   - AI分析录制的操作
   - 建议优化方案
   - 自动生成Python脚本

3. **定期自动执行**
   - 设置定时任务
   - 自动处理新数据
   - 生成定期报告

## 🔄 更新和维护

### 检查更新

```bash
# 检查是否有新版本
claudeditor --check-updates

# 或者访问GitHub仓库
open https://github.com/alexchuang650730/aicore0707
```

### 备份数据

```bash
# 备份配置和数据
tar -czf powerautomation_backup_$(date +%Y%m%d).tar.gz \
  ~/Applications/PowerAutomation/config/ \
  ~/Applications/PowerAutomation/data/ \
  ~/Applications/PowerAutomation/logs/
```

### 性能监控

```bash
# 查看系统资源使用
top -p $(pgrep -f powerautomation)

# 查看日志
tail -f ~/Applications/PowerAutomation/logs/claudeditor.log

# 查看性能指标
curl http://localhost:8080/api/metrics
```

## 🆘 获取帮助

### 文档资源

- **GitHub仓库**: https://github.com/alexchuang650730/aicore0707
- **完整文档**: 查看项目根目录的 `README.md`
- **API文档**: http://localhost:8080/docs (启动后访问)
- **变更日志**: 查看 `CHANGELOG.md`

### 社区支持

- **问题反馈**: [GitHub Issues](https://github.com/alexchuang650730/aicore0707/issues)
- **功能请求**: [GitHub Discussions](https://github.com/alexchuang650730/aicore0707/discussions)
- **邮件支持**: support@powerautomation.com

### 命令行帮助

```bash
# 查看启动脚本帮助
./start_claudeditor_mac.sh help

# 查看所有可用命令
claudeditor --help
```

## 🎉 开始您的AI自动化之旅

PowerAutomation v4.1为您提供了前所未有的AI自动化能力。无论您是：

- 🧑‍💻 **开发者** - 使用录制即测试功能快速创建自动化测试
- 👥 **团队协作者** - 利用实时协作功能提高团队效率
- 📊 **数据分析师** - 自动化重复的数据处理任务
- 🏢 **企业用户** - 构建企业级自动化解决方案

PowerAutomation v4.1都能为您提供强大的支持！

---

**PowerAutomation v4.1** - 重新定义AI自动化的未来 🚀

*感谢选择PowerAutomation，祝您使用愉快！*

