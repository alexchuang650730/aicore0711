# 🐧 PowerAutomation v4.1.0 SmartUI - Linux 使用说明

## 📋 **系统要求**

### **支持的发行版**
- **Ubuntu**: 20.04 LTS, 22.04 LTS, 24.04 LTS
- **Debian**: 11 (Bullseye), 12 (Bookworm)
- **CentOS**: 8, 9
- **RHEL**: 8, 9
- **Fedora**: 36, 37, 38, 39
- **openSUSE**: Leap 15.4+, Tumbleweed

### **最低要求**
- **内存**: 8GB RAM
- **存储**: 20GB 可用空间
- **处理器**: x86_64 架构
- **网络**: 稳定的互联网连接
- **显示**: X11 或 Wayland (GUI功能)

### **推荐配置**
- **内存**: 16GB RAM
- **存储**: 50GB 可用空间
- **处理器**: 4核心 CPU
- **显示**: 1920x1080 或更高分辨率

### **必需软件**
- **Python**: 3.11+ (自动安装)
- **Node.js**: 20.x+ (自动安装)
- **Git**: 2.25+ (自动安装)
- **Build Tools**: gcc, make, cmake (自动安装)

---

## 🚀 **安装步骤**

### **1. 下载安装包**

#### **Ubuntu/Debian**
```bash
# 使用wget下载
wget https://github.com/alexchuang650730/aicore0707/releases/download/v4.1.0/PowerAutomation_v4.1.0_SmartUI_Linux.tar.gz

# 或使用curl下载
curl -L -o PowerAutomation_v4.1.0_SmartUI_Linux.tar.gz \
  https://github.com/alexchuang650730/aicore0707/releases/download/v4.1.0/PowerAutomation_v4.1.0_SmartUI_Linux.tar.gz
```

#### **CentOS/RHEL/Fedora**
```bash
# 使用curl下载
curl -L -o PowerAutomation_v4.1.0_SmartUI_Linux.tar.gz \
  https://github.com/alexchuang650730/aicore0707/releases/download/v4.1.0/PowerAutomation_v4.1.0_SmartUI_Linux.tar.gz
```

### **2. 验证下载完整性**
```bash
# 验证SHA256校验和
sha256sum PowerAutomation_v4.1.0_SmartUI_Linux.tar.gz
# 应该输出: [校验和将在发布时提供]
```

### **3. 解压安装包**
```bash
tar -xzf PowerAutomation_v4.1.0_SmartUI_Linux.tar.gz
cd PowerAutomation_v4.1.0_SmartUI_Linux
```

### **4. 运行安装脚本**

#### **Ubuntu/Debian**
```bash
# 赋予执行权限
chmod +x install_ubuntu.sh

# 运行安装 (需要sudo权限)
sudo ./install_ubuntu.sh
```

#### **CentOS/RHEL/Fedora**
```bash
# 赋予执行权限
chmod +x install_centos.sh

# 运行安装 (需要sudo权限)
sudo ./install_centos.sh
```

#### **通用安装脚本**
```bash
# 通用安装脚本 (自动检测发行版)
chmod +x install_linux.sh
sudo ./install_linux.sh
```

### **5. 验证安装**
```bash
# 检查安装状态
powerautomation --version

# 启动SmartUI MCP服务
powerautomation smartui start

# 验证核心功能
powerautomation test p0
```

---

## 🎨 **SmartUI功能使用**

### **1. 启动SmartUI服务**
```bash
# 启动服务
powerautomation smartui start

# 检查服务状态
powerautomation smartui status

# 查看服务日志
powerautomation smartui logs

# 后台运行服务
powerautomation smartui start --daemon
```

### **2. 生成UI组件**
```bash
# 生成基础按钮组件
powerautomation smartui generate button MyButton \
  --variant primary \
  --size large \
  --theme default

# 生成表单输入组件
powerautomation smartui generate input EmailInput \
  --type email \
  --label "邮箱地址" \
  --required true

# 生成复杂表单
powerautomation smartui generate form UserForm \
  --fields "name,email,password" \
  --validation true \
  --theme dark
```

### **3. 主题管理**
```bash
# 列出可用主题
powerautomation smartui themes list

# 应用主题
powerautomation smartui themes apply dark

# 创建自定义主题
powerautomation smartui themes create MyTheme \
  --primary "#007AFF" \
  --secondary "#5856D6" \
  --background "#000000"
```

### **4. 组件预览**
```bash
# 启动预览服务器
powerautomation smartui preview start

# 在浏览器中打开预览
xdg-open http://localhost:3000/preview

# 实时预览组件
powerautomation smartui preview component MyButton
```

---

## 🎬 **录制即测试功能**

### **1. 启动录制**
```bash
# 启动录制会话
powerautomation record start "我的测试场景"

# 指定浏览器
powerautomation record start "登录测试" --browser firefox

# 录制移动端视图
powerautomation record start "移动端测试" --device mobile

# 无头模式录制
powerautomation record start "后台测试" --headless
```

### **2. 录制过程**
1. **打开目标网页**: 录制器会自动打开浏览器
2. **执行操作**: 正常使用网页，所有操作都会被记录
3. **添加断言**: 使用快捷键 `Ctrl+Shift+A` 添加验证点
4. **停止录制**: 使用快捷键 `Ctrl+Shift+S` 或关闭浏览器

### **3. 生成测试代码**
```bash
# 生成测试代码
powerautomation record generate "我的测试场景" \
  --format pytest \
  --output tests/

# 优化测试代码
powerautomation record optimize "我的测试场景" \
  --ai-enhance true

# 运行生成的测试
powerautomation test run tests/my_test_scenario.py
```

---

## 🧪 **测试系统使用**

### **1. 运行测试**
```bash
# 运行P0核心测试
powerautomation test p0

# 运行UI测试
powerautomation test ui --browser firefox

# 运行所有测试
powerautomation test all --report html

# 运行特定测试套件
powerautomation test suite login_workflow

# 并行运行测试
powerautomation test all --parallel 4
```

### **2. 测试报告**
```bash
# 生成HTML报告
powerautomation test report --format html --output reports/

# 生成JSON报告
powerautomation test report --format json --output reports/

# 查看最新报告
xdg-open reports/latest_report.html
```

### **3. 测试配置**
```bash
# 查看测试配置
powerautomation test config show

# 更新测试配置
powerautomation test config set browser firefox
powerautomation test config set timeout 30
powerautomation test config set parallel true
powerautomation test config set display :99  # 虚拟显示
```

---

## 🔧 **ClaudEditor集成**

### **1. 启动ClaudEditor**
```bash
# 启动ClaudEditor with SmartUI
powerautomation claudeditor start --with-smartui

# 启动测试平台
powerautomation claudeditor start --with-testing

# 启动完整功能
powerautomation claudeditor start --full

# 后台运行
powerautomation claudeditor start --full --daemon
```

### **2. 在ClaudEditor中使用SmartUI**
1. **打开SmartUI面板**: 在ClaudEditor中按 `Ctrl+Shift+U`
2. **选择组件类型**: 从组件库中选择需要的组件
3. **配置参数**: 设置组件属性和样式
4. **生成代码**: 点击"生成"按钮自动生成代码
5. **插入项目**: 将生成的代码插入到当前项目中

### **3. 测试集成**
1. **打开测试面板**: 在ClaudEditor中按 `Ctrl+Shift+T`
2. **录制测试**: 点击"开始录制"按钮
3. **执行操作**: 在预览窗口中执行测试操作
4. **生成测试**: 录制完成后自动生成测试代码
5. **运行测试**: 在测试面板中运行生成的测试

---

## 🛠️ **故障排除**

### **常见问题**

#### **1. 安装失败**
```bash
# 检查sudo权限
sudo -v

# 更新包管理器
# Ubuntu/Debian
sudo apt update && sudo apt upgrade

# CentOS/RHEL/Fedora
sudo dnf update

# 清理之前的安装
sudo rm -rf /opt/powerautomation

# 重新安装
sudo ./install_linux.sh --clean-install
```

#### **2. 服务启动失败**
```bash
# 检查端口占用
sudo netstat -tlnp | grep :8080

# 杀死占用进程
sudo kill -9 [PID]

# 检查防火墙
sudo ufw status  # Ubuntu
sudo firewall-cmd --list-all  # CentOS/RHEL

# 重启服务
powerautomation smartui restart
```

#### **3. 显示问题 (无头服务器)**
```bash
# 安装虚拟显示
sudo apt install xvfb  # Ubuntu/Debian
sudo dnf install xorg-x11-server-Xvfb  # CentOS/RHEL/Fedora

# 启动虚拟显示
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 &

# 配置PowerAutomation使用虚拟显示
powerautomation config set display :99
```

#### **4. 浏览器兼容性问题**
```bash
# 安装浏览器
# Firefox
sudo apt install firefox  # Ubuntu/Debian
sudo dnf install firefox  # CentOS/RHEL/Fedora

# Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
sudo apt update && sudo apt install google-chrome-stable

# 更新浏览器驱动
powerautomation drivers update

# 使用无头模式
powerautomation test ui --headless
```

#### **5. 权限问题**
```bash
# 修复权限
sudo chown -R $USER:$USER /opt/powerautomation
sudo chmod -R 755 /opt/powerautomation

# 添加用户到必要的组
sudo usermod -a -G video $USER
sudo usermod -a -G audio $USER

# 重新登录以应用组变更
```

### **性能优化**

#### **1. 内存优化**
```bash
# 设置内存限制
powerautomation config set memory_limit 8GB

# 启用内存监控
powerautomation monitor memory --alert 80%

# 配置交换空间
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### **2. 生成速度优化**
```bash
# 启用缓存
powerautomation config set cache_enabled true

# 设置并行生成
powerautomation config set parallel_generation $(nproc)

# 预热缓存
powerautomation smartui cache warm

# 使用SSD存储
powerautomation config set cache_dir /path/to/ssd/cache
```

---

## 📚 **高级功能**

### **1. 自定义模板**
```bash
# 创建自定义模板
powerautomation smartui template create MyTemplate \
  --base button \
  --custom-props "icon,tooltip"

# 使用自定义模板
powerautomation smartui generate MyTemplate IconButton \
  --icon "star" \
  --tooltip "收藏"
```

### **2. 批量生成**
```bash
# 从配置文件批量生成
powerautomation smartui batch generate \
  --config components_config.json

# 批量应用主题
powerautomation smartui batch theme apply \
  --theme dark \
  --components "Button,Input,Form"
```

### **3. API集成**
```bash
# 启动API服务
powerautomation api start --port 8080 --host 0.0.0.0

# 测试API
curl http://localhost:8080/api/v1/smartui/generate \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"type":"button","name":"TestButton","props":{"variant":"primary"}}'
```

### **4. 容器化部署**
```bash
# 构建Docker镜像
docker build -t powerautomation:v4.1.0 .

# 运行容器
docker run -d \
  --name powerautomation \
  -p 8080:8080 \
  -v $(pwd)/data:/opt/powerautomation/data \
  powerautomation:v4.1.0

# 使用Docker Compose
docker-compose up -d
```

---

## 🔄 **升级和维护**

### **从v4.0.x升级**
```bash
# 备份当前配置
powerautomation backup create v4.0.x-backup

# 下载升级包
wget https://github.com/alexchuang650730/aicore0707/releases/download/v4.1.0/upgrade_v4.1.0_linux.tar.gz

# 运行升级
tar -xzf upgrade_v4.1.0_linux.tar.gz
sudo ./upgrade_to_v4.1.0.sh

# 验证升级
powerautomation --version
powerautomation test p0
```

### **定期维护**
```bash
# 清理缓存
powerautomation cache clean

# 更新依赖
powerautomation update dependencies

# 检查系统健康
powerautomation health check

# 备份配置
powerautomation backup create daily-backup

# 设置定时任务
crontab -e
# 添加: 0 2 * * * /opt/powerautomation/bin/powerautomation backup create daily-backup
```

---

## 🔧 **Linux特定配置**

### **1. 系统服务配置**
```bash
# 创建systemd服务
sudo tee /etc/systemd/system/powerautomation.service > /dev/null <<EOF
[Unit]
Description=PowerAutomation Service
After=network.target

[Service]
Type=forking
User=powerautomation
Group=powerautomation
ExecStart=/opt/powerautomation/bin/powerautomation service start
ExecStop=/opt/powerautomation/bin/powerautomation service stop
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
sudo systemctl enable powerautomation
sudo systemctl start powerautomation
```

### **2. 防火墙配置**
```bash
# Ubuntu (ufw)
sudo ufw allow 8080/tcp
sudo ufw enable

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

### **3. 环境变量**
```bash
# 添加到shell配置文件
echo 'export PATH="/opt/powerautomation/bin:$PATH"' >> ~/.bashrc
echo 'export POWERAUTOMATION_HOME="/opt/powerautomation"' >> ~/.bashrc
source ~/.bashrc

# 系统级环境变量
sudo tee /etc/environment >> /dev/null <<EOF
POWERAUTOMATION_HOME="/opt/powerautomation"
PATH="/opt/powerautomation/bin:$PATH"
EOF
```

---

## 📞 **技术支持**

### **获取帮助**
- **命令行帮助**: `powerautomation --help`
- **在线文档**: https://docs.powerautomation.ai
- **GitHub Issues**: https://github.com/alexchuang650730/aicore0707/issues

### **日志和诊断**
```bash
# 查看系统日志
powerautomation logs system

# 查看错误日志
powerautomation logs error

# 查看systemd日志
sudo journalctl -u powerautomation -f

# 生成诊断报告
powerautomation diagnose --output diagnostic_report.tar.gz
```

### **社区支持**
- **官方论坛**: https://forum.powerautomation.ai
- **Discord社区**: https://discord.gg/powerautomation
- **Telegram群**: @PowerAutomationLinux

---

## 🔒 **安全注意事项**

### **1. 用户权限**
- 避免以root用户运行PowerAutomation
- 创建专用用户账户
- 使用sudo仅在必要时

### **2. 网络安全**
- 配置防火墙规则
- 使用HTTPS进行生产部署
- 限制API访问来源

### **3. 数据保护**
- 定期备份重要数据
- 加密敏感配置文件
- 设置适当的文件权限

---

**🚀 享受PowerAutomation v4.1.0 SmartUI带来的革命性AI开发体验！**

*最后更新: 2025年7月9日*

