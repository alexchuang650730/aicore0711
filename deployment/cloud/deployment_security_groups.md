# PowerAutomation + ClaudEditor AWS 安全组配置

## 🔒 需要开放的端口

### 1. **SSH 访问**
- **端口**: 22
- **协议**: TCP
- **来源**: 您的IP地址或0.0.0.0/0（不推荐）
- **用途**: 远程管理和部署

### 2. **PowerAutomation 主服务**
- **端口**: 8000
- **协议**: TCP
- **来源**: 0.0.0.0/0
- **用途**: PowerAutomation FastAPI 主服务

### 3. **ClaudEditor API 服务**
- **端口**: 5000
- **协议**: TCP
- **来源**: 0.0.0.0/0
- **用途**: ClaudEditor Flask API 后端

### 4. **ClaudEditor UI 开发服务**
- **端口**: 3000
- **协议**: TCP
- **来源**: 0.0.0.0/0
- **用途**: React 开发服务器（如果需要）

### 5. **Vite 开发服务器**
- **端口**: 5173
- **协议**: TCP
- **来源**: 0.0.0.0/0
- **用途**: Vite 开发服务器（如果需要）

### 6. **HTTP 服务**
- **端口**: 80
- **协议**: TCP
- **来源**: 0.0.0.0/0
- **用途**: 标准 HTTP 访问

### 7. **HTTPS 服务**
- **端口**: 443
- **协议**: TCP
- **来源**: 0.0.0.0/0
- **用途**: 标准 HTTPS 访问

## 🛡️ 安全组规则配置

### 入站规则 (Inbound Rules)

| 类型 | 协议 | 端口范围 | 来源 | 描述 |
|------|------|----------|------|------|
| SSH | TCP | 22 | 您的IP/32 | SSH 管理访问 |
| 自定义TCP | TCP | 8000 | 0.0.0.0/0 | PowerAutomation 主服务 |
| 自定义TCP | TCP | 5000 | 0.0.0.0/0 | ClaudEditor API |
| 自定义TCP | TCP | 3000 | 0.0.0.0/0 | React 开发服务器 |
| 自定义TCP | TCP | 5173 | 0.0.0.0/0 | Vite 开发服务器 |
| HTTP | TCP | 80 | 0.0.0.0/0 | HTTP 访问 |
| HTTPS | TCP | 443 | 0.0.0.0/0 | HTTPS 访问 |

### 出站规则 (Outbound Rules)
- **全部流量**: 允许所有出站流量（默认）

## 🚀 部署架构

```
Internet
    ↓
AWS Security Group
    ↓
EC2 Instance (Ubuntu)
    ├── PowerAutomation (Port 8000)
    ├── ClaudEditor API (Port 5000)
    ├── ClaudEditor UI (Port 3000/5173)
    └── Nginx (Port 80/443) - 可选反向代理
```

## 📝 AWS CLI 配置命令

```bash
# 创建安全组
aws ec2 create-security-group \
    --group-name powerautomation-sg \
    --description "PowerAutomation + ClaudEditor Security Group"

# 添加SSH规则
aws ec2 authorize-security-group-ingress \
    --group-name powerautomation-sg \
    --protocol tcp \
    --port 22 \
    --cidr YOUR_IP/32

# 添加PowerAutomation主服务规则
aws ec2 authorize-security-group-ingress \
    --group-name powerautomation-sg \
    --protocol tcp \
    --port 8000 \
    --cidr 0.0.0.0/0

# 添加ClaudEditor API规则
aws ec2 authorize-security-group-ingress \
    --group-name powerautomation-sg \
    --protocol tcp \
    --port 5000 \
    --cidr 0.0.0.0/0

# 添加HTTP/HTTPS规则
aws ec2 authorize-security-group-ingress \
    --group-name powerautomation-sg \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-name powerautomation-sg \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0
```

## ⚠️ 安全建议

1. **限制SSH访问**: 仅允许您的IP地址访问SSH端口
2. **使用HTTPS**: 在生产环境中配置SSL证书
3. **防火墙配置**: 在EC2实例内部配置ufw防火墙
4. **定期更新**: 保持系统和依赖包的更新
5. **监控日志**: 配置CloudWatch监控和日志记录

## 🔧 下一步部署步骤

1. 配置AWS安全组
2. 连接到EC2实例
3. 安装依赖环境
4. 部署PowerAutomation + ClaudEditor
5. 配置反向代理（可选）
6. 设置SSL证书（推荐）

