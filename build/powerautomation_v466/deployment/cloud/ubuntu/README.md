# Ubuntu 服务器部署

## 📦 部署包内容

### powerautomation-ubuntu-deployment.tar.gz
- **大小**: 573KB
- **包含**: 完整的Ubuntu自动化安装包
- **支持系统**: Ubuntu 22.04 LTS, Ubuntu 20.04 LTS

## 🚀 快速部署

### 一键安装命令
```bash
# 下载部署包
wget https://github.com/[your-repo]/raw/main/deployment/cloud/ubuntu/powerautomation-ubuntu-deployment.tar.gz

# 解压并安装
tar -xzf powerautomation-ubuntu-deployment.tar.gz
cd ubuntu_deployment_package
./QUICK_INSTALL.sh
```

### 部署包内容
解压后包含以下文件：
- `auto_install_powerautomation.sh` - 主安装脚本
- `QUICK_INSTALL.sh` - 快速安装脚本
- `UBUNTU_DEPLOYMENT_GUIDE.md` - 详细部署指南
- `demo_videos/tc_demo_001_recorded.mp4` - SmartUI + MemoryOS演示视频

## ✅ 安装完成后

### 访问地址
- **HTTP**: http://your-server-ip
- **健康检查**: http://your-server-ip/health

### 验证安装
```bash
sudo systemctl status powerautomation
curl -I http://localhost
```

## 📋 系统要求

- **操作系统**: Ubuntu 22.04 LTS (推荐) 或 Ubuntu 20.04 LTS
- **内存**: 最少1GB RAM (推荐2GB)
- **存储**: 最少10GB可用空间
- **网络**: 公网IP，开放端口80/443

## 🔧 管理命令

```bash
# 查看服务状态
sudo systemctl status powerautomation

# 重启服务
sudo systemctl restart powerautomation

# 查看日志
sudo journalctl -u powerautomation -f
```

