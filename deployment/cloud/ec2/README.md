# AWS EC2 部署

## 📦 部署包内容

### powerautomation-ec2-deployment.tar.gz
- **大小**: 14KB
- **包含**: 通用EC2部署配置
- **支持系统**: Amazon Linux 2, Ubuntu 22.04

### powerautomation-ec2-35.174.109.61.tar.gz
- **大小**: 16KB
- **包含**: 针对特定IP的定制化部署
- **目标服务器**: 35.174.109.61

## 🚀 快速部署

### Amazon Linux 部署
```bash
# 下载部署包
wget https://github.com/[your-repo]/raw/main/deployment/cloud/ec2/powerautomation-ec2-deployment.tar.gz

# 解压并部署
tar -xzf powerautomation-ec2-deployment.tar.gz
cd ec2_deployment
./deploy-amazon-linux.sh
```

### Ubuntu EC2 部署
```bash
# 下载部署包
wget https://github.com/[your-repo]/raw/main/deployment/cloud/ec2/powerautomation-ec2-deployment.tar.gz

# 解压并部署
tar -xzf powerautomation-ec2-deployment.tar.gz
cd ec2_deployment
./deploy.sh production
```

## 🏗️ 部署特色

### Docker 容器化
- 使用Docker容器运行应用
- 包含docker-compose配置
- 支持一键启动和停止

### Nginx 反向代理
- 自动配置Nginx
- SSL/TLS支持
- 安全头配置

### 系统服务集成
- systemd服务配置
- 自动启动设置
- 健康检查监控

## 📋 EC2 要求

### 实例配置
- **类型**: t3.medium (推荐) 或更高
- **存储**: 20GB GP3 SSD
- **网络**: VPC with public subnet

### 安全组设置
```
入站规则:
- SSH (22) - 您的IP
- HTTP (80) - 0.0.0.0/0
- HTTPS (443) - 0.0.0.0/0
```

### IAM 权限
基本EC2权限即可，无需额外IAM角色。

## 🔧 管理命令

### Docker 管理
```bash
# 查看容器状态
docker ps

# 查看日志
docker logs powerautomation

# 重启容器
docker-compose restart
```

### 系统服务管理
```bash
# 查看服务状态
sudo systemctl status powerautomation

# 重启服务
sudo systemctl restart powerautomation
```

## 🌐 访问配置

### 域名配置 (可选)
如需使用自定义域名：
1. 在DNS提供商添加A记录指向EC2公网IP
2. 更新Nginx配置中的server_name
3. 配置SSL证书 (Let's Encrypt推荐)

### 负载均衡 (可选)
可配置Application Load Balancer：
1. 创建ALB
2. 配置目标组指向EC2实例
3. 设置健康检查路径为 `/health`

## 🔒 安全最佳实践

### 网络安全
- 限制SSH访问IP范围
- 使用密钥对而非密码
- 定期更新安全组规则

### 应用安全
- 启用Nginx安全头
- 配置防火墙规则
- 定期更新系统包

### 监控和日志
- 启用CloudWatch监控
- 配置日志收集
- 设置告警通知

