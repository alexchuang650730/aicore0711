# PowerAutomation v4.3.0 Mac版本测试指南

## 🎯 测试目标

验证PowerAutomation v4.3.0在macOS平台上的完整功能和性能。

## 📋 测试环境要求

### 系统要求
- **操作系统**: macOS 11.0 (Big Sur) 或更高版本
- **处理器**: Intel x64 或 Apple Silicon (M1/M2/M3/M4)
- **内存**: 8GB RAM (推荐16GB)
- **存储**: 5GB 可用空间
- **网络**: 稳定的互联网连接

### 软件要求
- Python 3.8+
- Node.js 18+
- npm 9+
- Git
- Xcode命令行工具

## 🚀 测试步骤

### 1. 环境准备
```bash
# 克隆测试环境
git clone https://github.com/alexchuang650730/aicore0707.git
cd aicore0707/mac_test_environment

# 检查系统要求
./test_scripts/test_install_mac.sh --check-only
```

### 2. 安装测试
```bash
# 运行安装测试
./test_scripts/test_install_mac.sh

# 验证安装结果
ls -la /Applications/ClaudEditor.app
claudeditor --version
```

### 3. 功能测试
```bash
# 运行功能测试
python3 test_scripts/test_mac_functions.py

# 查看测试结果
cat test_results/mac_function_test_*.json
```

### 4. 性能测试
```bash
# 运行性能测试
python3 test_scripts/test_mac_performance.py

# 查看性能报告
cat test_results/mac_performance_test_*.json
```

### 5. 用户体验测试
```bash
# 启动ClaudEditor
claudeditor

# 测试以下功能:
# - 创建新项目
# - AI代码助手
# - 录制即测试
# - 实时协作
# - MCP工具
```

## 📊 测试检查清单

### 安装验证 ✅
- [ ] 应用程序已安装到 /Applications/ClaudEditor.app
- [ ] 命令行工具 claudeditor 可用
- [ ] 配置文件已创建
- [ ] 依赖包已安装
- [ ] 系统集成正常 (Dock图标、菜单栏)

### 功能验证 ✅
- [ ] 应用程序正常启动
- [ ] AI代码助手工作正常
- [ ] 录制即测试功能可用
- [ ] 文件操作正常
- [ ] 项目管理功能正常
- [ ] MCP工具集成正常

### 性能验证 ✅
- [ ] 启动时间 < 10秒
- [ ] 内存使用 < 500MB
- [ ] CPU使用 < 15% (空闲时)
- [ ] 磁盘占用 < 300MB
- [ ] 响应时间 < 2秒

### 用户体验验证 ✅
- [ ] 界面美观易用
- [ ] 快捷键工作正常
- [ ] 通知系统正常
- [ ] 文件关联正确
- [ ] 错误处理友好

## 🐛 问题报告

如果发现问题，请按以下格式报告：

```
**问题描述**: 简要描述问题
**重现步骤**: 详细的重现步骤
**预期结果**: 期望的正确行为
**实际结果**: 实际发生的情况
**系统信息**: macOS版本、硬件信息
**日志文件**: 相关的日志文件内容
```

## 📞 获取帮助

- **GitHub Issues**: https://github.com/alexchuang650730/aicore0707/issues
- **测试文档**: ./docs/test_guide.md
- **配置说明**: ./docs/mac_config.md
