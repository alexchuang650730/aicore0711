# PowerAutomation 4.0 Ubuntu服务器一键安装命令

## 🎯 目标服务器
- **地址**: ec2-44-206-225-192.compute-1.amazonaws.com
- **系统**: Ubuntu 22.04 LTS
- **用户**: ubuntu
- **SSH密钥**: alexchuang.pem

## 🚀 一键安装命令

### 方法1: 直接下载并安装 (推荐)

在您的本地电脑执行以下命令：

```bash
# 1. 下载部署包到本地
curl -L -o powerautomation-ubuntu-deployment.tar.gz [部署包下载链接]

# 2. 上传到服务器
scp -i "alexchuang.pem" powerautomation-ubuntu-deployment.tar.gz ubuntu@ec2-44-206-225-192.compute-1.amazonaws.com:~/

# 3. 连接服务器并安装
ssh -i "alexchuang.pem" ubuntu@ec2-44-206-225-192.compute-1.amazonaws.com
```

在服务器上执行：

```bash
# 解压部署包
tar -xzf powerautomation-ubuntu-deployment.tar.gz

# 进入目录并执行快速安装
cd ubuntu_deployment_package
./QUICK_INSTALL.sh
```

### 方法2: 直接在服务器上安装

如果您已经连接到服务器，可以直接执行：

```bash
# 连接服务器
ssh -i "alexchuang.pem" ubuntu@ec2-44-206-225-192.compute-1.amazonaws.com

# 在服务器上执行以下命令
wget -O auto_install_powerautomation.sh https://raw.githubusercontent.com/[您的仓库]/auto_install_powerautomation.sh
chmod +x auto_install_powerautomation.sh
./auto_install_powerautomation.sh
```

## ✅ 安装完成验证

安装完成后，执行以下命令验证：

```bash
# 检查服务状态
sudo systemctl status powerautomation

# 检查网站响应
curl -I http://localhost

# 检查健康状态
curl http://localhost/health
```

## 🌐 访问网站

安装成功后，您可以通过以下地址访问：

- **主要地址**: http://ec2-44-206-225-192.compute-1.amazonaws.com
- **IP地址**: http://44.206.225.192
- **健康检查**: http://44.206.225.192/health

## 🎬 演示功能测试

访问网站后，您将看到四个演示卡片：

1. **SmartUI + MemoryOS** ✅ (已包含真实演示视频)
2. **MCP工具发现** (需要上传视频文件)
3. **端云多模型协同** (需要上传视频文件)
4. **端到端自动化测试** (需要上传视频文件)

点击"播放演示"按钮测试视频播放功能。

## 📁 文件结构

安装完成后的文件结构：

```
/opt/powerautomation/
├── index.html              # 网站主页
├── server.js               # Node.js服务器
├── package.json            # 依赖配置
├── node_modules/           # Node.js依赖
└── demo_videos/            # 演示视频目录
    └── tc_demo_001_recorded.mp4  # SmartUI + MemoryOS演示
```

## 🔧 常用管理命令

```bash
# 查看服务状态
sudo systemctl status powerautomation

# 重启PowerAutomation服务
sudo systemctl restart powerautomation

# 查看服务日志
sudo journalctl -u powerautomation -f

# 重启Nginx
sudo systemctl restart nginx

# 查看Nginx状态
sudo systemctl status nginx
```

## 🎥 添加其他演示视频

如需添加其他演示视频，请将视频文件上传到服务器：

```bash
# 从本地上传视频文件
scp -i "alexchuang.pem" tc_demo_002.mp4 ubuntu@ec2-44-206-225-192.compute-1.amazonaws.com:/opt/powerautomation/demo_videos/
scp -i "alexchuang.pem" tc_demo_003.mp4 ubuntu@ec2-44-206-225-192.compute-1.amazonaws.com:/opt/powerautomation/demo_videos/
scp -i "alexchuang.pem" tc_demo_004.mp4 ubuntu@ec2-44-206-225-192.compute-1.amazonaws.com:/opt/powerautomation/demo_videos/
```

## 🛠️ 故障排除

### 如果安装失败：

1. **检查系统要求**：确保是Ubuntu 22.04 LTS
2. **检查网络连接**：确保服务器能访问互联网
3. **检查权限**：确保使用ubuntu用户而非root
4. **查看日志**：检查安装过程中的错误信息

### 如果网站无法访问：

1. **检查防火墙**：确保端口80已开放
2. **检查服务状态**：`sudo systemctl status powerautomation nginx`
3. **检查EC2安全组**：确保入站规则允许HTTP流量

### 如果视频无法播放：

1. **检查视频文件**：确保文件存在且权限正确
2. **检查浏览器控制台**：查看JavaScript错误
3. **清除浏览器缓存**：刷新页面重试

## 📞 技术支持

如遇到问题，请提供以下信息：
- 服务器系统信息：`uname -a`
- 服务状态：`sudo systemctl status powerautomation`
- 错误日志：`sudo journalctl -u powerautomation -n 50`

---

**PowerAutomation 4.0 Team**  
*让智能自动化触手可及*

