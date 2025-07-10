# 🐧 PowerAutomation v4.1 - Linux版本

[![Platform](https://img.shields.io/badge/platform-Linux-orange.svg)](https://www.linux.org/)
[![Status](https://img.shields.io/badge/status-Coming%20Soon-yellow.svg)](https://github.com/alexchuang650730/aicore0707)

## 🚧 开发中

PowerAutomation v4.1的Linux版本正在积极开发中，即将发布！

### 📅 预计发布时间
- **Beta版本**: 2025年1月
- **正式版本**: 2025年2月

### 🎯 计划功能
- ✅ 完整的ClaudEditor 4.1功能
- ✅ 多发行版支持 (Ubuntu, CentOS, Debian, Fedora)
- ✅ AppImage便携版本
- ✅ Snap包支持
- ✅ 系统集成
- ✅ 命令行工具

### 📋 系统要求 (预计)
- **发行版**: Ubuntu 20.04+, CentOS 8+, Debian 11+, Fedora 35+
- **架构**: x86_64, ARM64
- **内存**: 最低 4GB RAM，推荐 8GB
- **存储**: 最低 1GB 可用空间
- **依赖**: Python 3.8+, Node.js 16+

### 🎯 支持的发行版

#### Ubuntu/Debian系列
```bash
# 预计安装方式
wget https://github.com/alexchuang650730/aicore0707/releases/download/v4.1.0/powerautomation_4.1.0_amd64.deb
sudo dpkg -i powerautomation_4.1.0_amd64.deb
```

#### Red Hat/CentOS/Fedora系列
```bash
# 预计安装方式
wget https://github.com/alexchuang650730/aicore0707/releases/download/v4.1.0/powerautomation-4.1.0-1.x86_64.rpm
sudo rpm -i powerautomation-4.1.0-1.x86_64.rpm
```

#### AppImage (通用)
```bash
# 预计安装方式
wget https://github.com/alexchuang650730/aicore0707/releases/download/v4.1.0/PowerAutomation-4.1.0-x86_64.AppImage
chmod +x PowerAutomation-4.1.0-x86_64.AppImage
./PowerAutomation-4.1.0-x86_64.AppImage
```

### 🔔 获取更新通知
- **GitHub Watch**: [关注仓库](https://github.com/alexchuang650730/aicore0707)
- **GitHub Releases**: [订阅发布通知](https://github.com/alexchuang650730/aicore0707/releases)

### 💡 临时解决方案
在Linux版本发布之前，您可以：
1. 从源码编译运行
2. 使用Docker容器运行
3. 参考macOS版本进行手动配置

### 🛠️ 从源码运行 (高级用户)
```bash
# 克隆仓库
git clone https://github.com/alexchuang650730/aicore0707.git
cd aicore0707

# 安装依赖
pip3 install -r requirements.txt

# 配置环境
cp config/claudeditor_config.yaml.example config/claudeditor_config.yaml
# 编辑配置文件，添加Claude API密钥

# 启动服务
python3 claudeditor_ui_main.py
```

---

*敬请期待Linux版本的发布！* 🚀

