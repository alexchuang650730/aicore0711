# PowerAutomation v4.2.0 Linux 使用说明

**版本**: v4.2.0 "AI Testing Revolution"  
**适用系统**: Ubuntu 22.04+ / CentOS 8+ / Debian 11+ / Fedora 36+  
**发布日期**: 2025年7月9日

---

## 🐧 **Linux专属特性**

### **发行版深度支持**
- **Ubuntu 22.04+ LTS**: 完整支持Ubuntu LTS版本和最新特性
- **CentOS/RHEL 8+**: 企业级Red Hat生态系统集成
- **Debian 11+**: 稳定版本支持和包管理集成
- **Fedora 36+**: 最新技术栈和创新功能支持
- **Arch Linux**: 滚动更新和AUR包支持

### **系统集成优化**
- **Systemd集成**: 原生systemd服务管理
- **Docker/Podman支持**: 容器化部署和开发
- **Kubernetes集成**: 云原生应用开发和测试
- **X11/Wayland支持**: 图形界面和无头模式
- **SSH远程管理**: 完整的远程开发和测试支持

### **开发环境集成**
- **VS Code Server**: 远程开发环境支持
- **Vim/Neovim插件**: 命令行编辑器集成
- **Tmux集成**: 终端会话管理
- **Git Hooks**: 自动化工作流集成
- **CI/CD管道**: Jenkins、GitLab CI、GitHub Actions集成

---

## 📋 **系统要求**

### **最低要求**
- **操作系统**: Ubuntu 22.04 / CentOS 8 / Debian 11 / Fedora 36
- **架构**: x86_64 (AMD64) / ARM64 (aarch64)
- **内存**: 8GB RAM
- **存储**: 30GB 可用空间
- **网络**: 稳定的互联网连接
- **显示**: X11或Wayland (GUI功能)

### **推荐配置**
- **操作系统**: Ubuntu 22.04 LTS / Fedora 38+
- **架构**: x86_64 (推荐Intel/AMD 64位)
- **CPU**: 4核心 2.5GHz+
- **内存**: 16GB RAM
- **存储**: 50GB SSD
- **GPU**: NVIDIA GPU (CUDA支持，AI功能)

### **开发环境要求**
- **Python**: 3.11+ (推荐使用pyenv)
- **Node.js**: 20.x+ (推荐使用nvm)
- **Git**: 2.34+
- **Docker**: 24.0+ (可选)
- **浏览器**: Chrome/Chromium 120+, Firefox 120+

---

## 🚀 **安装指南**

### **方法一: 自动安装脚本 (推荐)**

#### **一键安装**
```bash
# 下载并运行自动安装脚本
curl -fsSL https://raw.githubusercontent.com/alexchuang650730/aicore0707/main/install-linux.sh | bash

# 或者先下载再执行
curl -O https://raw.githubusercontent.com/alexchuang650730/aicore0707/main/install-linux.sh
chmod +x install-linux.sh
./install-linux.sh --with-ai-features --enable-gpu
```

#### **分步安装**
```bash
# 检测系统环境
./install-linux.sh --check-requirements

# 安装依赖
./install-linux.sh --install-dependencies

# 安装PowerAutomation
./install-linux.sh --install-powerautomation

# 配置服务
./install-linux.sh --configure-services
```

### **方法二: 包管理器安装**

#### **Ubuntu/Debian (APT)**
```bash
# 添加PowerAutomation仓库
curl -fsSL https://packages.powerautomation.ai/gpg | sudo gpg --dearmor -o /usr/share/keyrings/powerautomation.gpg
echo "deb [signed-by=/usr/share/keyrings/powerautomation.gpg] https://packages.powerautomation.ai/ubuntu $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/powerautomation.list

# 更新包列表
sudo apt update

# 安装PowerAutomation
sudo apt install powerautomation

# 启动服务
sudo systemctl enable powerautomation
sudo systemctl start powerautomation
```

#### **CentOS/RHEL/Fedora (YUM/DNF)**
```bash
# 添加PowerAutomation仓库
sudo tee /etc/yum.repos.d/powerautomation.repo << EOF
[powerautomation]
name=PowerAutomation Repository
baseurl=https://packages.powerautomation.ai/rhel/\$releasever/\$basearch/
enabled=1
gpgcheck=1
gpgkey=https://packages.powerautomation.ai/gpg
EOF

# 安装PowerAutomation (CentOS/RHEL)
sudo yum install powerautomation

# 安装PowerAutomation (Fedora)
sudo dnf install powerautomation

# 启动服务
sudo systemctl enable powerautomation
sudo systemctl start powerautomation
```

#### **Arch Linux (AUR)**
```bash
# 使用yay安装
yay -S powerautomation

# 或使用paru
paru -S powerautomation

# 启动服务
sudo systemctl enable powerautomation
sudo systemctl start powerautomation
```

### **方法三: 手动安装**

#### **1. 下载安装包**
```bash
# 创建安装目录
sudo mkdir -p /opt/powerautomation
cd /tmp

# 下载最新版本
wget https://github.com/alexchuang650730/aicore0707/releases/download/v4.2.0/PowerAutomation_v4.2.0_Linux_x86_64.tar.gz

# 验证下载完整性
sha256sum PowerAutomation_v4.2.0_Linux_x86_64.tar.gz
```

#### **2. 解压安装**
```bash
# 解压到安装目录
sudo tar -xzf PowerAutomation_v4.2.0_Linux_x86_64.tar.gz -C /opt/powerautomation --strip-components=1

# 设置权限
sudo chown -R root:root /opt/powerautomation
sudo chmod +x /opt/powerautomation/bin/*
```

#### **3. 安装依赖**

**Ubuntu/Debian**
```bash
# 更新包列表
sudo apt update

# 安装基础依赖
sudo apt install -y python3.11 python3.11-pip nodejs npm git curl wget

# 安装系统依赖
sudo apt install -y build-essential libssl-dev libffi-dev python3.11-dev

# 安装浏览器和驱动
sudo apt install -y chromium-browser firefox-esr

# 安装可选依赖
sudo apt install -y docker.io docker-compose redis-server postgresql
```

**CentOS/RHEL**
```bash
# 启用EPEL仓库
sudo yum install -y epel-release

# 安装基础依赖
sudo yum install -y python311 python311-pip nodejs npm git curl wget

# 安装开发工具
sudo yum groupinstall -y "Development Tools"
sudo yum install -y openssl-devel libffi-devel python311-devel

# 安装浏览器
sudo yum install -y chromium firefox
```

**Fedora**
```bash
# 安装基础依赖
sudo dnf install -y python3.11 python3-pip nodejs npm git curl wget

# 安装开发工具
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y openssl-devel libffi-devel python3-devel

# 安装浏览器
sudo dnf install -y chromium firefox
```

#### **4. 配置环境**
```bash
# 创建符号链接
sudo ln -sf /opt/powerautomation/bin/powerautomation /usr/local/bin/powerautomation

# 配置环境变量
echo 'export PATH="/opt/powerautomation/bin:$PATH"' | sudo tee /etc/profile.d/powerautomation.sh
echo 'export POWERAUTOMATION_HOME="/opt/powerautomation"' | sudo tee -a /etc/profile.d/powerautomation.sh

# 重新加载环境变量
source /etc/profile.d/powerautomation.sh

# 安装Python依赖
cd /opt/powerautomation
sudo pip3.11 install -r requirements.txt

# 安装Node.js依赖
sudo npm install -g @powerautomation/cli
```

#### **5. 配置systemd服务**
```bash
# 创建systemd服务文件
sudo tee /etc/systemd/system/powerautomation.service << EOF
[Unit]
Description=PowerAutomation AI Development Platform
After=network.target

[Service]
Type=forking
User=powerautomation
Group=powerautomation
WorkingDirectory=/opt/powerautomation
ExecStart=/opt/powerautomation/bin/powerautomation start --daemon
ExecStop=/opt/powerautomation/bin/powerautomation stop
ExecReload=/opt/powerautomation/bin/powerautomation reload
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 创建服务用户
sudo useradd -r -s /bin/false powerautomation
sudo chown -R powerautomation:powerautomation /opt/powerautomation

# 重新加载systemd并启动服务
sudo systemctl daemon-reload
sudo systemctl enable powerautomation
sudo systemctl start powerautomation
```

---

## ⚙️ **配置指南**

### **基础配置**
```bash
# 初始化配置
powerautomation init --platform linux

# 配置AI服务
powerautomation config set ai.provider claude
powerautomation config set ai.api_key $CLAUDE_API_KEY

# 配置浏览器
powerautomation config set browser.default chromium
powerautomation config set browser.headless true
```

### **Linux特定配置**
```bash
# 启用Linux集成功能
powerautomation config set linux.systemd_integration true
powerautomation config set linux.docker_support true
powerautomation config set linux.ssh_remote true

# 配置显示服务器
powerautomation config set display.server wayland  # 或 x11
powerautomation config set display.headless true   # 无头模式

# 配置容器支持
powerautomation config set container.runtime docker  # 或 podman
powerautomation config set container.enable_gpu true
```

### **开发环境配置**
```bash
# 配置Python环境 (使用pyenv)
curl https://pyenv.run | bash
echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc

pyenv install 3.11.7
pyenv global 3.11.7

# 配置Node.js环境 (使用nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc

nvm install 20
nvm use 20

# 配置Git
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
powerautomation git configure
```

### **Docker集成配置**
```bash
# 安装Docker (如果未安装)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 配置PowerAutomation Docker集成
powerautomation docker configure
powerautomation config set docker.enable_gpu true
powerautomation config set docker.default_image "powerautomation/runtime:latest"

# 启动Docker服务
sudo systemctl enable docker
sudo systemctl start docker
```

---

## 🎯 **快速开始**

### **1. 验证安装**
```bash
# 检查版本
powerautomation --version

# 检查系统状态
powerautomation status

# 运行健康检查
powerautomation health-check --full --linux-specific
```

### **2. 启动服务**
```bash
# 启动所有服务
powerautomation start

# 启动特定服务
powerautomation start smartui
powerautomation start testing

# 查看服务状态
powerautomation ps
systemctl status powerautomation
```

### **3. 创建第一个组件**
```bash
# 生成简单按钮组件
powerautomation generate component button MyButton \
  --framework react \
  --theme linux

# 生成GTK组件 (Linux原生)
powerautomation generate component gtk-button GtkButton \
  --style adwaita \
  --binding python
```

### **4. 录制第一个测试**
```bash
# 启动录制模式 (需要图形界面)
DISPLAY=:0 powerautomation record start --name "登录测试" --browser chromium

# 无头模式录制
powerautomation record start --name "API测试" --headless --browser chromium

# 停止录制并生成测试
powerautomation record stop
powerautomation record generate --optimize-with-ai
```

---

## 🛠️ **开发工具集成**

### **VS Code Server集成**

#### **安装和配置**
```bash
# 安装VS Code Server
curl -fsSL https://code-server.dev/install.sh | sh

# 配置PowerAutomation扩展
code-server --install-extension powerautomation.vscode-extension

# 启动VS Code Server
code-server --bind-addr 0.0.0.0:8080 --auth password
```

#### **远程开发配置**
```bash
# 配置SSH隧道
ssh -L 8080:localhost:8080 user@remote-server

# 在本地浏览器访问
# http://localhost:8080
```

### **Vim/Neovim集成**

#### **安装Vim插件**
```bash
# 安装vim-plug
curl -fLo ~/.vim/autoload/plug.vim --create-dirs \
    https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim

# 添加PowerAutomation插件到.vimrc
echo "Plug 'powerautomation/vim-powerautomation'" >> ~/.vimrc

# 安装插件
vim +PlugInstall +qall
```

#### **Neovim配置**
```lua
-- ~/.config/nvim/init.lua
require('packer').startup(function()
  use 'powerautomation/nvim-powerautomation'
end)

-- 配置PowerAutomation
require('powerautomation').setup({
  ai_provider = 'claude',
  auto_generate = true,
  keymaps = {
    generate_component = '<leader>pg',
    start_recording = '<leader>pr',
    run_tests = '<leader>pt'
  }
})
```

### **Tmux集成**
```bash
# 安装Tmux PowerAutomation插件
git clone https://github.com/powerautomation/tmux-powerautomation ~/.tmux/plugins/tmux-powerautomation

# 添加到.tmux.conf
echo "run-shell ~/.tmux/plugins/tmux-powerautomation/powerautomation.tmux" >> ~/.tmux.conf

# 重新加载配置
tmux source-file ~/.tmux.conf
```

### **终端集成**
```bash
# 添加bash补全
powerautomation completion bash > ~/.bash_completion.d/powerautomation

# 添加zsh补全
powerautomation completion zsh > ~/.zsh/completions/_powerautomation

# 添加fish补全
powerautomation completion fish > ~/.config/fish/completions/powerautomation.fish

# 添加有用的别名
echo 'alias pa="powerautomation"' >> ~/.bashrc
echo 'alias pag="powerautomation generate"' >> ~/.bashrc
echo 'alias par="powerautomation record"' >> ~/.bashrc
echo 'alias pat="powerautomation test"' >> ~/.bashrc
```

---

## 🎨 **SmartUI功能使用**

### **Linux原生组件生成**

#### **GTK组件**
```bash
# 生成GTK4按钮
powerautomation generate component gtk4-button ModernButton \
  --style adwaita \
  --language python \
  --binding gi

# 生成GTK4窗口
powerautomation generate component gtk4-window MainWindow \
  --layout box \
  --widgets "header,content,footer" \
  --responsive true
```

#### **Qt组件**
```bash
# 生成Qt6按钮
powerautomation generate component qt6-button StyledButton \
  --style fusion \
  --language python \
  --binding pyside6

# 生成Qt6对话框
powerautomation generate component qt6-dialog SettingsDialog \
  --layout form \
  --fields "name,email,preferences"
```

#### **Tkinter组件**
```bash
# 生成Tkinter窗口
powerautomation generate component tkinter-window AppWindow \
  --theme dark \
  --layout grid \
  --widgets "menu,toolbar,status"
```

### **Web组件生成**
```bash
# 生成React组件 (Linux风格)
powerautomation generate component react-button LinuxButton \
  --theme adwaita \
  --framework react \
  --typescript true

# 生成Vue组件
powerautomation generate component vue-form ContactForm \
  --validation true \
  --theme linux-dark \
  --responsive true
```

### **容器化组件**
```bash
# 生成Docker化的组件
powerautomation generate component docker-app WebApp \
  --framework react \
  --include-dockerfile \
  --base-image node:20-alpine

# 生成Kubernetes部署
powerautomation generate k8s-deployment WebApp \
  --replicas 3 \
  --service-type LoadBalancer \
  --ingress true
```

---

## 🧪 **测试功能使用**

### **无头浏览器测试**
```bash
# 配置无头模式
powerautomation config set browser.headless true
powerautomation config set browser.virtual_display true

# 启动虚拟显示 (如果需要)
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 &

# 运行无头测试
powerautomation test run ui --headless --browser chromium
```

### **Docker容器测试**
```bash
# 在Docker容器中运行测试
powerautomation test run docker \
  --image "powerautomation/test-runner:latest" \
  --mount-source \
  --network host

# 创建测试容器
powerautomation docker create-test-container \
  --name "ui-test-container" \
  --browsers "chromium,firefox" \
  --vnc-enabled
```

### **分布式测试**
```bash
# 配置测试集群
powerautomation cluster configure \
  --nodes "node1.example.com,node2.example.com,node3.example.com" \
  --ssh-key ~/.ssh/id_rsa

# 运行分布式测试
powerautomation test run distributed \
  --suite "full-regression" \
  --parallel-nodes 3 \
  --load-balance
```

### **CI/CD集成**

#### **GitLab CI配置**
```yaml
# .gitlab-ci.yml
stages:
  - test
  - deploy

powerautomation_tests:
  stage: test
  image: powerautomation/ci-runner:latest
  services:
    - docker:dind
  script:
    - powerautomation start --ci-mode
    - powerautomation test run p0 --report --junit-output
    - powerautomation test run ui --headless --parallel
  artifacts:
    reports:
      junit: test-results.xml
    paths:
      - test-reports/
  only:
    - merge_requests
    - main
```

#### **GitHub Actions配置**
```yaml
# .github/workflows/powerautomation.yml
name: PowerAutomation Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup PowerAutomation
      uses: powerautomation/setup-action@v1
      with:
        version: '4.2.0'
        enable-ai: true
        
    - name: Run P0 Tests
      run: powerautomation test run p0 --report
      
    - name: Run UI Tests
      run: powerautomation test run ui --headless --parallel
      
    - name: Upload Test Reports
      uses: actions/upload-artifact@v3
      with:
        name: test-reports
        path: test-reports/
```

#### **Jenkins Pipeline**
```groovy
// Jenkinsfile
pipeline {
    agent {
        docker {
            image 'powerautomation/jenkins-agent:latest'
            args '-v /var/run/docker.sock:/var/run/docker.sock'
        }
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'powerautomation start --ci-mode'
            }
        }
        
        stage('P0 Tests') {
            steps {
                sh 'powerautomation test run p0 --report --junit-output'
            }
        }
        
        stage('UI Tests') {
            parallel {
                stage('Chrome Tests') {
                    steps {
                        sh 'powerautomation test run ui --browser chromium --parallel'
                    }
                }
                stage('Firefox Tests') {
                    steps {
                        sh 'powerautomation test run ui --browser firefox --parallel'
                    }
                }
            }
        }
    }
    
    post {
        always {
            publishTestResults testResultsPattern: 'test-results.xml'
            archiveArtifacts artifacts: 'test-reports/**/*'
        }
    }
}
```

---

## 📊 **监控和报告**

### **系统监控**
```bash
# 启动监控仪表板
powerautomation monitor start \
  --port 3000 \
  --bind-address 0.0.0.0 \
  --enable-metrics

# 查看系统指标
powerautomation monitor metrics \
  --live \
  --format json \
  --output /var/log/powerautomation/metrics.log

# 集成Prometheus
powerautomation monitor prometheus-config \
  --output /etc/prometheus/powerautomation.yml
```

### **日志管理**
```bash
# 配置日志轮转
sudo tee /etc/logrotate.d/powerautomation << EOF
/var/log/powerautomation/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 powerautomation powerautomation
    postrotate
        systemctl reload powerautomation
    endscript
}
EOF

# 集成rsyslog
echo 'local0.*    /var/log/powerautomation/app.log' | sudo tee -a /etc/rsyslog.conf
sudo systemctl restart rsyslog

# 实时日志监控
tail -f /var/log/powerautomation/app.log | powerautomation logs parse --live
```

### **报告生成**
```bash
# 生成HTML报告
powerautomation report generate html \
  --template linux-professional \
  --output /var/www/html/reports/test-report.html \
  --include-system-info

# 生成PDF报告
powerautomation report generate pdf \
  --template executive \
  --output /tmp/executive-report.pdf \
  --include-charts

# 发送邮件报告
powerautomation report email \
  --smtp-server smtp.company.com \
  --to team@company.com \
  --subject "PowerAutomation 每日报告" \
  --format html \
  --attach-logs
```

---

## 🔧 **故障排除**

### **常见问题**

#### **1. 权限问题**
```bash
# 问题: 无法访问某些系统资源
# 解决方案: 配置正确的权限
sudo usermod -aG docker $USER
sudo usermod -aG video $USER
sudo usermod -aG audio $USER

# 重新登录以应用组权限
newgrp docker
```

#### **2. 显示服务器问题**
```bash
# 问题: 无法启动图形界面测试
# 解决方案: 配置虚拟显示
sudo apt install xvfb

# 启动虚拟显示
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 &

# 或使用xvfb-run
xvfb-run -a powerautomation test run ui
```

#### **3. 浏览器驱动问题**
```bash
# 问题: Chrome/Chromium驱动不匹配
# 解决方案: 更新浏览器驱动
powerautomation browser update-drivers --browser chromium

# 问题: Firefox驱动问题
# 解决方案: 安装geckodriver
wget https://github.com/mozilla/geckodriver/releases/latest/download/geckodriver-v0.33.0-linux64.tar.gz
tar -xzf geckodriver-v0.33.0-linux64.tar.gz
sudo mv geckodriver /usr/local/bin/
```

#### **4. 依赖问题**
```bash
# 问题: Python包冲突
# 解决方案: 使用虚拟环境
python3.11 -m venv ~/.powerautomation-venv
source ~/.powerautomation-venv/bin/activate
pip install powerautomation

# 问题: Node.js版本问题
# 解决方案: 使用nvm管理版本
nvm install 20
nvm use 20
npm install -g @powerautomation/cli
```

### **诊断工具**
```bash
# 运行完整系统诊断
powerautomation diagnose --full --linux-specific --output /tmp/diagnosis.log

# 检查Linux兼容性
powerautomation check linux-compatibility --distro $(lsb_release -si)

# 验证所有配置
powerautomation config validate --strict

# 测试网络连接
powerautomation network test --all-services --timeout 30

# 检查系统资源
powerautomation system check-resources --memory --disk --cpu
```

### **性能调优**
```bash
# 优化系统性能
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'fs.file-max=65536' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# 优化PowerAutomation性能
powerautomation config set performance.max_workers $(nproc)
powerautomation config set performance.memory_limit "8G"
powerautomation config set performance.enable_gpu true

# 启用性能监控
powerautomation monitor enable --cpu --memory --disk --network
```

---

## 🔄 **更新和维护**

### **包管理器更新**
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade powerautomation

# CentOS/RHEL
sudo yum update powerautomation

# Fedora
sudo dnf update powerautomation

# Arch Linux
yay -Syu powerautomation
```

### **手动更新**
```bash
# 备份当前配置
powerautomation backup create \
  --name "v4.2.0-backup" \
  --include-config \
  --include-data \
  --output /opt/backups

# 下载新版本
wget https://github.com/alexchuang650730/aicore0707/releases/latest/download/PowerAutomation_latest_Linux_x86_64.tar.gz

# 停止服务
sudo systemctl stop powerautomation

# 备份当前安装
sudo mv /opt/powerautomation /opt/powerautomation.backup

# 安装新版本
sudo tar -xzf PowerAutomation_latest_Linux_x86_64.tar.gz -C /opt/powerautomation --strip-components=1

# 恢复配置
sudo cp -r /opt/powerautomation.backup/config/* /opt/powerautomation/config/

# 启动服务
sudo systemctl start powerautomation
```

### **Docker更新**
```bash
# 更新Docker镜像
docker pull powerautomation/runtime:latest
docker pull powerautomation/test-runner:latest

# 重新创建容器
powerautomation docker recreate --update-images
```

### **系统维护**
```bash
# 清理临时文件
powerautomation maintenance cleanup \
  --temp-files \
  --logs-older-than 30d \
  --cache-files

# 优化数据库
powerautomation maintenance optimize-database --vacuum --reindex

# 检查磁盘使用
powerautomation maintenance disk-usage --detailed

# 系统健康检查
powerautomation maintenance health-check --full --fix-issues
```

---

## 🐳 **容器化部署**

### **Docker部署**

#### **单容器部署**
```bash
# 运行PowerAutomation容器
docker run -d \
  --name powerautomation \
  -p 3000:3000 \
  -p 8080:8080 \
  -v powerautomation-data:/data \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e POWERAUTOMATION_AI_PROVIDER=claude \
  -e POWERAUTOMATION_AI_API_KEY=$CLAUDE_API_KEY \
  powerautomation/runtime:latest
```

#### **Docker Compose部署**
```yaml
# docker-compose.yml
version: '3.8'

services:
  powerautomation:
    image: powerautomation/runtime:latest
    ports:
      - "3000:3000"
      - "8080:8080"
    volumes:
      - powerautomation-data:/data
      - /var/run/docker.sock:/var/run/docker.sock
      - ./config:/opt/powerautomation/config
    environment:
      - POWERAUTOMATION_AI_PROVIDER=claude
      - POWERAUTOMATION_AI_API_KEY=${CLAUDE_API_KEY}
      - POWERAUTOMATION_DATABASE_URL=postgresql://user:pass@postgres:5432/powerautomation
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=powerautomation
      - POSTGRES_USER=powerautomation
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - powerautomation
    restart: unless-stopped

volumes:
  powerautomation-data:
  postgres-data:
  redis-data:
```

### **Kubernetes部署**

#### **基础部署**
```yaml
# powerautomation-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: powerautomation
  labels:
    app: powerautomation
spec:
  replicas: 3
  selector:
    matchLabels:
      app: powerautomation
  template:
    metadata:
      labels:
        app: powerautomation
    spec:
      containers:
      - name: powerautomation
        image: powerautomation/runtime:latest
        ports:
        - containerPort: 3000
        - containerPort: 8080
        env:
        - name: POWERAUTOMATION_AI_PROVIDER
          value: "claude"
        - name: POWERAUTOMATION_AI_API_KEY
          valueFrom:
            secretKeyRef:
              name: powerautomation-secrets
              key: ai-api-key
        volumeMounts:
        - name: config
          mountPath: /opt/powerautomation/config
        - name: data
          mountPath: /data
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
      volumes:
      - name: config
        configMap:
          name: powerautomation-config
      - name: data
        persistentVolumeClaim:
          claimName: powerautomation-data

---
apiVersion: v1
kind: Service
metadata:
  name: powerautomation-service
spec:
  selector:
    app: powerautomation
  ports:
  - name: web
    port: 3000
    targetPort: 3000
  - name: api
    port: 8080
    targetPort: 8080
  type: LoadBalancer

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: powerautomation-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - powerautomation.yourdomain.com
    secretName: powerautomation-tls
  rules:
  - host: powerautomation.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: powerautomation-service
            port:
              number: 3000
```

#### **Helm部署**
```bash
# 添加PowerAutomation Helm仓库
helm repo add powerautomation https://charts.powerautomation.ai
helm repo update

# 安装PowerAutomation
helm install powerautomation powerautomation/powerautomation \
  --set ai.provider=claude \
  --set ai.apiKey=$CLAUDE_API_KEY \
  --set ingress.enabled=true \
  --set ingress.hostname=powerautomation.yourdomain.com \
  --set persistence.enabled=true \
  --set persistence.size=50Gi

# 升级部署
helm upgrade powerautomation powerautomation/powerautomation \
  --set image.tag=v4.2.0
```

---

## 🔒 **安全和合规**

### **安全配置**
```bash
# 启用SSL/TLS
powerautomation config set security.ssl_enabled true
powerautomation config set security.ssl_cert_path "/etc/ssl/certs/powerautomation.crt"
powerautomation config set security.ssl_key_path "/etc/ssl/private/powerautomation.key"

# 配置防火墙
sudo ufw allow 3000/tcp
sudo ufw allow 8080/tcp
sudo ufw enable

# 配置SELinux (CentOS/RHEL)
sudo setsebool -P httpd_can_network_connect 1
sudo semanage port -a -t http_port_t -p tcp 3000
sudo semanage port -a -t http_port_t -p tcp 8080
```

### **用户认证**
```bash
# 配置LDAP认证
powerautomation config set auth.provider ldap
powerautomation config set auth.ldap_server "ldap://ldap.company.com"
powerautomation config set auth.ldap_base_dn "dc=company,dc=com"

# 配置OAuth2
powerautomation config set auth.provider oauth2
powerautomation config set auth.oauth2_provider google
powerautomation config set auth.oauth2_client_id $OAUTH2_CLIENT_ID
powerautomation config set auth.oauth2_client_secret $OAUTH2_CLIENT_SECRET
```

### **审计和日志**
```bash
# 启用审计日志
powerautomation config set audit.enabled true
powerautomation config set audit.log_level detailed
powerautomation config set audit.retention_days 365

# 配置日志转发
powerautomation config set logging.syslog_enabled true
powerautomation config set logging.syslog_server "syslog.company.com:514"

# 集成ELK Stack
powerautomation logging configure-elk \
  --elasticsearch-url "http://elasticsearch:9200" \
  --kibana-url "http://kibana:5601"
```

---

## 📞 **技术支持**

### **获取帮助**
- **官方文档**: https://docs.powerautomation.ai/linux
- **Linux专区**: https://community.powerautomation.ai/linux
- **GitHub Issues**: https://github.com/alexchuang650730/aicore0707/issues
- **IRC频道**: #powerautomation on Libera.Chat

### **社区支持**
```bash
# 生成支持包
powerautomation support generate-package \
  --include-logs \
  --include-config \
  --include-system-info \
  --include-docker-info \
  --output /tmp/support-package.tar.gz

# 提交问题报告
powerautomation support submit \
  --title "Linux安装问题" \
  --description "详细描述问题" \
  --attach /tmp/support-package.tar.gz \
  --priority normal
```

### **企业支持**
- **企业邮箱**: enterprise@powerautomation.ai
- **技术支持**: support@powerautomation.ai
- **培训服务**: training@powerautomation.ai
- **专业服务**: consulting@powerautomation.ai

---

## 🎉 **结语**

PowerAutomation v4.2.0 为Linux用户提供了完整的AI驱动开发和测试解决方案。通过深度的Linux系统集成，您可以享受到：

- **原生性能**: 针对Linux优化的高性能体验
- **开源生态**: 与Linux开源生态系统的完美融合
- **容器化支持**: Docker和Kubernetes的原生支持
- **企业级功能**: 适合企业环境的安全和管理功能

无论您是个人开发者、开源项目维护者还是企业团队，PowerAutomation都将成为您在Linux平台上最强大的AI开发伙伴！

---

**🐧 PowerAutomation v4.2.0 - Linux平台的AI开发革命**

*发布团队: PowerAutomation Linux团队*  
*更新日期: 2025年7月9日*

