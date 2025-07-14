# PowerAutomation 4.0 Ubuntu服务器部署指南

## 🎯 目标服务器
- **服务器**: ec2-44-206-225-192.compute-1.amazonaws.com
- **系统**: Ubuntu 22.04 LTS
- **用户**: ubuntu
- **SSH密钥**: alexchuang.pem

## 🚀 一键自动化安装

### 步骤1: 上传部署包
```bash
# 在本地执行
scp -i "alexchuang.pem" -r ubuntu_deployment_package ubuntu@ec2-44-206-225-192.compute-1.amazonaws.com:~/
```

### 步骤2: 连接服务器并安装
```bash
# 连接服务器
ssh -i "alexchuang.pem" ubuntu@ec2-44-206-225-192.compute-1.amazonaws.com

# 在服务器上执行
cd ubuntu_deployment_package
./auto_install_powerautomation.sh
```

## ✅ 安装完成后

### 🌐 访问网站
- **主要地址**: http://ec2-44-206-225-192.compute-1.amazonaws.com
- **备用地址**: http://44.206.225.192
- **健康检查**: http://44.206.225.192/health

### 🎬 演示功能
安装完成后，网站将包含四个演示卡片：
1. **SmartUI + MemoryOS** - 智能界面与长期记忆系统
2. **MCP工具发现** - MCP-Zero引擎智能工具发现
3. **端云多模型协同** - Claude 3.5 Sonnet与Gemini 1.5 Pro协同
4. **端到端自动化测试** - Stagewise MCP与录制即测试技术

### 🔧 管理命令
```bash
# 查看服务状态
sudo systemctl status powerautomation

# 重启服务
sudo systemctl restart powerautomation

# 查看日志
sudo journalctl -u powerautomation -f

# 查看Nginx状态
sudo systemctl status nginx
```

## 📁 重要目录

### 应用目录
- **主目录**: `/opt/powerautomation`
- **网站文件**: `/opt/powerautomation/index.html`
- **服务器文件**: `/opt/powerautomation/server.js`
- **视频目录**: `/opt/powerautomation/demo_videos`

### 配置文件
- **Nginx配置**: `/etc/nginx/sites-available/powerautomation`
- **系统服务**: `/etc/systemd/system/powerautomation.service`

## 🎥 演示视频管理

### 当前包含的视频
- ✅ `tc_demo_001_recorded.mp4` - SmartUI + MemoryOS演示 (25.5秒)

### 需要添加的视频
如需完整演示功能，请将以下视频文件上传到 `/opt/powerautomation/demo_videos/`:
- `tc_demo_002.mp4` - MCP工具发现演示
- `tc_demo_003.mp4` - 端云多模型协同演示  
- `tc_demo_004.mp4` - 端到端自动化测试演示

### 上传视频命令
```bash
# 从本地上传视频到服务器
scp -i "alexchuang.pem" tc_demo_002.mp4 ubuntu@ec2-44-206-225-192.compute-1.amazonaws.com:/opt/powerautomation/demo_videos/
scp -i "alexchuang.pem" tc_demo_003.mp4 ubuntu@ec2-44-206-225-192.compute-1.amazonaws.com:/opt/powerautomation/demo_videos/
scp -i "alexchuang.pem" tc_demo_004.mp4 ubuntu@ec2-44-206-225-192.compute-1.amazonaws.com:/opt/powerautomation/demo_videos/
```

## 🔒 安全配置

### 防火墙设置
安装脚本会自动配置UFW防火墙：
- ✅ SSH (端口22)
- ✅ HTTP (端口80)  
- ✅ HTTPS (端口443)
- ✅ Node.js应用 (端口3000)

### Nginx安全头
自动配置的安全头包括：
- X-Frame-Options
- X-XSS-Protection
- X-Content-Type-Options
- Referrer-Policy
- Content-Security-Policy

## 🛠️ 故障排除

### 常见问题

#### 1. 服务启动失败
```bash
# 检查服务状态
sudo systemctl status powerautomation

# 查看详细日志
sudo journalctl -u powerautomation -n 50

# 手动启动测试
cd /opt/powerautomation
node server.js
```

#### 2. 网站无法访问
```bash
# 检查Nginx状态
sudo systemctl status nginx

# 测试Nginx配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

#### 3. 视频无法播放
```bash
# 检查视频文件权限
ls -la /opt/powerautomation/demo_videos/

# 修复权限
sudo chown -R ubuntu:ubuntu /opt/powerautomation/demo_videos/
sudo chmod 644 /opt/powerautomation/demo_videos/*.mp4
```

### 性能优化

#### 1. 启用Gzip压缩
Nginx配置已包含压缩设置，Node.js服务器也启用了compression中间件。

#### 2. 静态文件缓存
静态文件（CSS、JS、图片）设置了1年缓存期，视频文件设置了1小时缓存期。

#### 3. 进程管理
可选择使用PM2进行进程管理：
```bash
# 安装PM2
sudo npm install -g pm2

# 使用PM2启动
cd /opt/powerautomation
pm2 start server.js --name powerautomation

# 设置开机自启
pm2 startup
pm2 save
```

## 📊 监控和日志

### 健康检查
- **端点**: `/health`
- **返回**: JSON格式的健康状态信息
- **监控**: 可配置外部监控服务定期检查

### 日志管理
- **应用日志**: `sudo journalctl -u powerautomation`
- **Nginx访问日志**: `/var/log/nginx/access.log`
- **Nginx错误日志**: `/var/log/nginx/error.log`

## 🔄 更新和维护

### 更新网站内容
```bash
# 备份当前版本
sudo cp /opt/powerautomation/index.html /opt/powerautomation/index.html.backup

# 更新文件后重启服务
sudo systemctl restart powerautomation
```

### 更新Node.js依赖
```bash
cd /opt/powerautomation
npm update
sudo systemctl restart powerautomation
```

## 📞 技术支持

如遇到问题，请检查：
1. 服务器系统要求是否满足
2. 网络连接是否正常
3. 防火墙设置是否正确
4. 日志文件中的错误信息

---

**PowerAutomation 4.0 Team**  
*智能自动化的未来*

