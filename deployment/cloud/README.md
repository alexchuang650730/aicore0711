# PowerAutomation 4.0 云端部署方案

## 📋 概述

PowerAutomation 4.0 云端部署方案提供了完整的自动化部署解决方案，支持多种云平台和服务器环境。本目录包含了所有必要的部署文件、脚本和文档。

## 🏗️ 目录结构

```
deployment/cloud/
├── README.md                    # 主说明文档
├── ubuntu/                      # Ubuntu服务器部署
│   └── powerautomation-ubuntu-deployment.tar.gz
├── ec2/                         # AWS EC2部署
│   ├── powerautomation-ec2-deployment.tar.gz
│   └── powerautomation-ec2-35.174.109.61.tar.gz
├── scripts/                     # 部署脚本
│   ├── auto_install_powerautomation.sh
│   └── QUICK_INSTALL.sh
├── docs/                        # 文档
│   ├── UBUNTU_SERVER_INSTALL_COMMANDS.md
│   ├── UBUNTU_DEPLOYMENT_GUIDE.md
│   └── deployment_summary.md
└── videos/                      # 演示视频
    └── tc_demo_001_recorded.mp4
```

## 🚀 快速开始

### Ubuntu 服务器部署 (推荐)

适用于 Ubuntu 22.04 LTS 服务器：

```bash
# 1. 下载部署包
wget https://github.com/[your-repo]/deployment/cloud/ubuntu/powerautomation-ubuntu-deployment.tar.gz

# 2. 解压并安装
tar -xzf powerautomation-ubuntu-deployment.tar.gz
cd ubuntu_deployment_package
./QUICK_INSTALL.sh
```

### AWS EC2 部署

适用于 Amazon Linux 和 Ubuntu EC2 实例：

```bash
# 下载对应的EC2部署包
wget https://github.com/[your-repo]/deployment/cloud/ec2/powerautomation-ec2-deployment.tar.gz

# 解压并执行部署
tar -xzf powerautomation-ec2-deployment.tar.gz
cd ec2_deployment
./deploy.sh
```

## 📦 部署包说明

### Ubuntu 部署包
- **文件**: `ubuntu/powerautomation-ubuntu-deployment.tar.gz`
- **大小**: 573KB
- **包含**: 完整的Ubuntu自动化安装脚本和配置
- **支持系统**: Ubuntu 22.04 LTS
- **安装时间**: 约5-10分钟

### EC2 部署包
- **文件**: `ec2/powerautomation-ec2-deployment.tar.gz`
- **大小**: 14KB
- **包含**: AWS EC2优化的部署配置
- **支持系统**: Amazon Linux 2, Ubuntu 22.04
- **特色**: Docker容器化部署

## 🎬 演示功能

部署完成后，网站将包含以下演示功能：

### 1. SmartUI + MemoryOS ✅
- **演示视频**: 已包含 (25.5秒)
- **功能**: 智能界面自适应与长期记忆系统
- **性能提升**: 49.11%

### 2. MCP工具发现
- **功能**: MCP-Zero引擎智能工具发现
- **特色**: 14种工具自动发现和智能匹配

### 3. 端云多模型协同
- **功能**: Claude 3.5 Sonnet与Gemini 1.5 Pro协同
- **特色**: 智能模型切换和性能优化

### 4. 端到端自动化测试
- **功能**: Stagewise MCP与录制即测试技术
- **特色**: 真正的端到端自动化流程

## 🛠️ 技术栈

### 前端
- **框架**: 原生HTML5 + CSS3 + JavaScript
- **特色**: 响应式设计，移动端兼容
- **视频播放器**: 自定义模态框播放器

### 后端
- **运行时**: Node.js 20.x
- **框架**: Express.js
- **特色**: 健康检查、CORS支持、安全头配置

### 基础设施
- **Web服务器**: Nginx (反向代理)
- **进程管理**: systemd服务
- **容器化**: Docker (可选)
- **安全**: UFW防火墙，SSL/TLS支持

## 📋 系统要求

### 最低要求
- **CPU**: 1 vCPU
- **内存**: 1GB RAM
- **存储**: 10GB 可用空间
- **网络**: 公网IP，开放端口80/443

### 推荐配置
- **CPU**: 2 vCPU
- **内存**: 2GB RAM
- **存储**: 20GB SSD
- **网络**: 稳定的互联网连接

### 支持的操作系统
- ✅ Ubuntu 22.04 LTS
- ✅ Ubuntu 20.04 LTS
- ✅ Amazon Linux 2
- ✅ CentOS 8+
- ✅ Debian 11+

## 🔧 安装选项

### 选项1: 一键自动安装 (推荐)
```bash
curl -fsSL https://raw.githubusercontent.com/[your-repo]/deployment/cloud/scripts/auto_install_powerautomation.sh | bash
```

### 选项2: 手动部署
1. 下载部署包
2. 解压到目标目录
3. 执行安装脚本
4. 配置服务和防火墙

### 选项3: Docker部署
```bash
docker run -d -p 80:3000 --name powerautomation powerautomation:latest
```

## 🌐 访问和验证

### 部署完成后访问
- **HTTP**: http://your-server-ip
- **健康检查**: http://your-server-ip/health
- **演示页面**: http://your-server-ip/#demo

### 验证命令
```bash
# 检查服务状态
sudo systemctl status powerautomation

# 检查网站响应
curl -I http://localhost

# 检查健康状态
curl http://localhost/health
```

## 📊 性能和监控

### 性能指标
- **启动时间**: < 5秒
- **响应时间**: < 100ms
- **并发支持**: 100+ 用户
- **内存使用**: < 200MB

### 监控端点
- **健康检查**: `/health`
- **状态信息**: 包含运行时间、版本信息
- **日志**: systemd journal 集成

## 🔒 安全配置

### 自动配置的安全措施
- ✅ UFW防火墙配置
- ✅ Nginx安全头
- ✅ 进程权限限制
- ✅ 文件系统保护

### 安全头配置
- X-Frame-Options: SAMEORIGIN
- X-XSS-Protection: 1; mode=block
- X-Content-Type-Options: nosniff
- Referrer-Policy: no-referrer-when-downgrade

## 🛠️ 故障排除

### 常见问题

#### 1. 安装失败
```bash
# 检查系统要求
lsb_release -a
free -h
df -h

# 查看安装日志
tail -f /var/log/syslog
```

#### 2. 服务无法启动
```bash
# 检查服务状态
sudo systemctl status powerautomation

# 查看详细日志
sudo journalctl -u powerautomation -f

# 手动启动测试
cd /opt/powerautomation
node server.js
```

#### 3. 网站无法访问
```bash
# 检查端口监听
sudo netstat -tlnp | grep :80

# 检查防火墙
sudo ufw status

# 测试本地连接
curl -I http://localhost
```

#### 4. 视频无法播放
```bash
# 检查视频文件
ls -la /opt/powerautomation/demo_videos/

# 检查文件权限
sudo chown -R ubuntu:ubuntu /opt/powerautomation/demo_videos/
```

## 📞 技术支持

### 获取帮助
- **文档**: 查看 `docs/` 目录中的详细文档
- **日志**: 使用 `sudo journalctl -u powerautomation` 查看日志
- **社区**: 提交 GitHub Issue

### 报告问题时请提供
1. 操作系统版本: `lsb_release -a`
2. 服务状态: `sudo systemctl status powerautomation`
3. 错误日志: `sudo journalctl -u powerautomation -n 50`
4. 网络配置: `ip addr show`

## 🔄 更新和维护

### 更新网站内容
```bash
# 备份当前版本
sudo cp /opt/powerautomation/index.html /opt/powerautomation/index.html.backup

# 更新后重启服务
sudo systemctl restart powerautomation
```

### 更新系统依赖
```bash
# 更新Node.js依赖
cd /opt/powerautomation
npm update

# 重启服务
sudo systemctl restart powerautomation
```

### 备份和恢复
```bash
# 备份应用目录
sudo tar -czf powerautomation-backup-$(date +%Y%m%d).tar.gz /opt/powerautomation

# 恢复应用
sudo tar -xzf powerautomation-backup-YYYYMMDD.tar.gz -C /
```

## 📈 扩展和定制

### 添加新的演示视频
1. 将视频文件上传到 `/opt/powerautomation/demo_videos/`
2. 更新 `index.html` 中的视频配置
3. 重启服务

### 自定义界面
1. 修改 `/opt/powerautomation/index.html`
2. 更新CSS样式和JavaScript功能
3. 测试并重启服务

### 集成其他服务
- **数据库**: 可集成 MongoDB, PostgreSQL
- **缓存**: 可添加 Redis 缓存层
- **CDN**: 可配置 CloudFlare 等CDN服务

## 📄 许可证

PowerAutomation 4.0 采用 MIT 许可证。详见项目根目录的 LICENSE 文件。

## 🤝 贡献

欢迎提交 Pull Request 和 Issue。请确保：
1. 遵循代码规范
2. 添加适当的测试
3. 更新相关文档

---

**PowerAutomation 4.0 Team**  
*让智能自动化触手可及*

最后更新: 2024年7月9日

