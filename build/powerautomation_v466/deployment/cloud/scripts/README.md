# 部署脚本

## 📜 脚本列表

### auto_install_powerautomation.sh
- **功能**: PowerAutomation 4.0 完整自动化安装脚本
- **大小**: 28KB
- **支持系统**: Ubuntu 22.04 LTS
- **安装时间**: 5-10分钟

### QUICK_INSTALL.sh
- **功能**: 快速安装脚本，调用主安装脚本
- **大小**: 1.6KB
- **特色**: 用户友好的安装界面

## 🚀 使用方法

### 直接下载执行
```bash
# 下载主安装脚本
wget https://github.com/[your-repo]/raw/main/deployment/cloud/scripts/auto_install_powerautomation.sh

# 设置执行权限
chmod +x auto_install_powerautomation.sh

# 执行安装
./auto_install_powerautomation.sh
```

### 一键安装命令
```bash
curl -fsSL https://github.com/[your-repo]/raw/main/deployment/cloud/scripts/auto_install_powerautomation.sh | bash
```

## 🔧 脚本功能

### auto_install_powerautomation.sh 包含功能

#### 系统准备
- ✅ 系统包更新
- ✅ 基础依赖安装
- ✅ 用户权限检查

#### 软件安装
- ✅ Node.js 20.x 安装
- ✅ Docker 和 Docker Compose 安装
- ✅ Nginx Web服务器安装

#### 应用配置
- ✅ PowerAutomation网站部署
- ✅ Node.js服务器配置
- ✅ 演示视频集成

#### 系统服务
- ✅ systemd服务创建
- ✅ Nginx反向代理配置
- ✅ UFW防火墙设置

#### 安全配置
- ✅ 安全头配置
- ✅ 文件权限设置
- ✅ 进程权限限制

### QUICK_INSTALL.sh 特色
- 🎯 用户友好的安装界面
- 🔍 安装前确认提示
- ✅ 安装结果验证
- 📋 安装后信息显示

## 📋 安装流程

### 1. 环境检查
- 检查操作系统版本
- 验证用户权限
- 确认网络连接

### 2. 依赖安装
- 更新系统包管理器
- 安装Node.js和npm
- 安装Docker容器平台
- 安装Nginx Web服务器

### 3. 应用部署
- 创建应用目录 `/opt/powerautomation`
- 下载并配置网站文件
- 安装Node.js依赖包
- 配置演示视频目录

### 4. 服务配置
- 创建systemd服务文件
- 配置Nginx反向代理
- 设置防火墙规则
- 启动所有服务

### 5. 验证测试
- 检查服务运行状态
- 测试网站访问
- 验证健康检查端点
- 显示访问信息

## 🛠️ 自定义配置

### 修改安装路径
编辑脚本中的变量：
```bash
APP_DIR="/opt/powerautomation"  # 应用安装目录
PORT="3000"                     # 应用端口
```

### 修改服务配置
编辑脚本中的systemd服务配置部分：
```bash
# 修改服务名称
SERVICE_NAME="powerautomation"

# 修改运行用户
SERVICE_USER="ubuntu"
```

### 添加额外功能
在脚本末尾添加自定义函数：
```bash
# 自定义配置函数
custom_configuration() {
    log_info "执行自定义配置..."
    # 添加您的自定义配置代码
}
```

## 🔍 故障排除

### 常见问题

#### 1. 权限错误
```bash
# 确保不使用root用户
whoami  # 应该显示 ubuntu 或其他非root用户

# 检查sudo权限
sudo -l
```

#### 2. 网络连接问题
```bash
# 测试网络连接
ping -c 3 google.com

# 检查DNS解析
nslookup nodejs.org
```

#### 3. 端口冲突
```bash
# 检查端口占用
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :3000

# 停止冲突服务
sudo systemctl stop apache2  # 如果安装了Apache
```

#### 4. 磁盘空间不足
```bash
# 检查磁盘空间
df -h

# 清理系统缓存
sudo apt clean
sudo apt autoremove
```

## 📊 安装日志

### 日志位置
- **系统日志**: `/var/log/syslog`
- **安装日志**: 脚本执行时的终端输出
- **服务日志**: `sudo journalctl -u powerautomation`

### 调试模式
启用详细日志输出：
```bash
# 设置调试模式
export DEBUG=1
./auto_install_powerautomation.sh
```

## 🔄 更新和维护

### 更新脚本
```bash
# 下载最新版本
wget -O auto_install_powerautomation.sh.new https://github.com/[your-repo]/raw/main/deployment/cloud/scripts/auto_install_powerautomation.sh

# 比较差异
diff auto_install_powerautomation.sh auto_install_powerautomation.sh.new

# 替换旧版本
mv auto_install_powerautomation.sh.new auto_install_powerautomation.sh
chmod +x auto_install_powerautomation.sh
```

### 重新安装
```bash
# 备份当前配置
sudo cp -r /opt/powerautomation /opt/powerautomation.backup

# 重新执行安装
./auto_install_powerautomation.sh
```

