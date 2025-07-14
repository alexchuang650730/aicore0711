#!/bin/bash

# PowerAutomation 4.0 自动化安装脚本
# 适用于 Ubuntu EC2 服务器
# 服务器: ec2-44-206-225-192.compute-1.amazonaws.com

set -e  # 遇到错误立即退出

echo "🚀 开始安装 PowerAutomation 4.0..."
echo "服务器: $(hostname)"
echo "时间: $(date)"
echo "用户: $(whoami)"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "请不要使用root用户运行此脚本"
        exit 1
    fi
}

# 更新系统
update_system() {
    log_info "更新系统包..."
    sudo apt update -y
    sudo apt upgrade -y
    log_success "系统更新完成"
}

# 安装基础依赖
install_dependencies() {
    log_info "安装基础依赖..."
    sudo apt install -y \
        curl \
        wget \
        git \
        unzip \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        ufw \
        nginx
    log_success "基础依赖安装完成"
}

# 安装Node.js
install_nodejs() {
    log_info "安装Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
    
    # 验证安装
    node_version=$(node --version)
    npm_version=$(npm --version)
    log_success "Node.js安装完成: $node_version, npm: $npm_version"
}

# 安装Docker
install_docker() {
    log_info "安装Docker..."
    
    # 添加Docker官方GPG密钥
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # 添加Docker仓库
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 安装Docker
    sudo apt update -y
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # 将当前用户添加到docker组
    sudo usermod -aG docker $USER
    
    # 启动Docker服务
    sudo systemctl start docker
    sudo systemctl enable docker
    
    log_success "Docker安装完成"
}

# 安装Docker Compose
install_docker_compose() {
    log_info "安装Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    # 验证安装
    compose_version=$(docker-compose --version)
    log_success "Docker Compose安装完成: $compose_version"
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."
    sudo ufw --force enable
    sudo ufw allow ssh
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 3000/tcp  # Node.js应用端口
    log_success "防火墙配置完成"
}

# 创建应用目录
create_app_directory() {
    log_info "创建应用目录..."
    sudo mkdir -p /opt/powerautomation
    sudo chown $USER:$USER /opt/powerautomation
    cd /opt/powerautomation
    log_success "应用目录创建完成: /opt/powerautomation"
}

# 下载PowerAutomation网站内容
download_website() {
    log_info "下载PowerAutomation网站内容..."
    
    # 创建网站HTML文件
    cat > index.html << 'EOF'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PowerAutomation 4.0 - 智能自动化平台</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 50px;
        }
        
        .header h1 {
            font-size: 3.5rem;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.3rem;
            opacity: 0.9;
        }
        
        .demo-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-bottom: 50px;
        }
        
        .demo-card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .demo-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }
        
        .demo-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        
        .demo-card h3 {
            color: #333;
            margin-bottom: 15px;
            font-size: 1.5rem;
        }
        
        .demo-card p {
            color: #666;
            margin-bottom: 20px;
            line-height: 1.6;
        }
        
        .demo-features {
            list-style: none;
            margin-bottom: 25px;
        }
        
        .demo-features li {
            padding: 5px 0;
            color: #555;
            position: relative;
            padding-left: 20px;
        }
        
        .demo-features li::before {
            content: '✓';
            position: absolute;
            left: 0;
            color: #4CAF50;
            font-weight: bold;
        }
        
        .play-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
            transition: all 0.3s ease;
            width: 100%;
        }
        
        .play-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .footer {
            text-align: center;
            color: white;
            margin-top: 50px;
            opacity: 0.8;
        }
        
        /* 视频模态框样式 */
        .video-modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.9);
            animation: fadeIn 0.3s ease;
        }
        
        .video-modal-content {
            position: relative;
            margin: 5% auto;
            width: 90%;
            max-width: 800px;
            background: white;
            border-radius: 15px;
            overflow: hidden;
            animation: slideIn 0.3s ease;
        }
        
        .video-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            position: relative;
        }
        
        .video-header h3 {
            margin: 0;
            font-size: 1.5rem;
        }
        
        .video-header p {
            margin: 5px 0 0 0;
            opacity: 0.9;
        }
        
        .close-btn {
            position: absolute;
            top: 15px;
            right: 20px;
            background: none;
            border: none;
            color: white;
            font-size: 2rem;
            cursor: pointer;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background-color 0.3s ease;
        }
        
        .close-btn:hover {
            background-color: rgba(255,255,255,0.2);
        }
        
        .video-container {
            padding: 20px;
            text-align: center;
        }
        
        .video-player {
            width: 100%;
            max-width: 100%;
            height: auto;
            border-radius: 10px;
        }
        
        .video-info {
            margin-top: 15px;
            text-align: left;
        }
        
        .video-info h4 {
            color: #333;
            margin-bottom: 10px;
        }
        
        .video-info ul {
            list-style: none;
            padding: 0;
        }
        
        .video-info li {
            padding: 5px 0;
            color: #666;
            position: relative;
            padding-left: 20px;
        }
        
        .video-info li::before {
            content: '▶';
            position: absolute;
            left: 0;
            color: #667eea;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes slideIn {
            from { transform: translateY(-50px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2.5rem;
            }
            
            .demo-grid {
                grid-template-columns: 1fr;
                gap: 20px;
            }
            
            .video-modal-content {
                margin: 10% auto;
                width: 95%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>PowerAutomation 4.0</h1>
            <p>下一代智能自动化平台 - 重新定义工作流程</p>
        </div>
        
        <div class="demo-grid" id="demo">
            <div class="demo-card">
                <h3>SmartUI + MemoryOS</h3>
                <p>智能界面自适应与长期记忆系统，让AI真正理解用户习惯</p>
                <ul class="demo-features">
                    <li>SmartUI智能自适应界面</li>
                    <li>MemoryOS长期记忆系统</li>
                    <li>49.11%性能提升</li>
                    <li>个性化用户体验</li>
                </ul>
                <button class="play-btn" onclick="playDemo('smartui')">播放演示</button>
            </div>
            
            <div class="demo-card">
                <h3>MCP工具发现</h3>
                <p>革命性的MCP-Zero引擎，智能发现和推荐最适合的工具</p>
                <ul class="demo-features">
                    <li>MCP-Zero智能引擎</li>
                    <li>14种工具自动发现</li>
                    <li>智能匹配推荐</li>
                    <li>零配置即用</li>
                </ul>
                <button class="play-btn" onclick="playDemo('mcp')">播放演示</button>
            </div>
            
            <div class="demo-card">
                <h3>端云多模型协同</h3>
                <p>Claude 3.5 Sonnet与Gemini 1.5 Pro智能协同，性能翻倍</p>
                <ul class="demo-features">
                    <li>Claude 3.5 Sonnet集成</li>
                    <li>Gemini 1.5 Pro协同</li>
                    <li>智能模型切换</li>
                    <li>性能优化算法</li>
                </ul>
                <button class="play-btn" onclick="playDemo('multimodel')">播放演示</button>
            </div>
            
            <div class="demo-card">
                <h3>端到端自动化测试</h3>
                <p>Stagewise MCP与录制即测试技术，实现真正的端到端自动化</p>
                <ul class="demo-features">
                    <li>Stagewise MCP架构</li>
                    <li>录制即测试技术</li>
                    <li>端到端自动化</li>
                    <li>智能测试生成</li>
                </ul>
                <button class="play-btn" onclick="playDemo('e2e')">播放演示</button>
            </div>
        </div>
        
        <div class="footer">
            <p>&copy; 2024 PowerAutomation 4.0 - 智能自动化的未来</p>
        </div>
    </div>
    
    <!-- 视频模态框 -->
    <div id="videoModal" class="video-modal">
        <div class="video-modal-content">
            <div class="video-header">
                <h3 id="videoTitle">演示标题</h3>
                <p id="videoDescription">演示描述</p>
                <button class="close-btn" onclick="closeVideoModal()">&times;</button>
            </div>
            <div class="video-container">
                <video id="videoPlayer" class="video-player" controls>
                    <source id="videoSource" src="" type="video/mp4">
                    您的浏览器不支持视频播放。
                </video>
                <div class="video-info">
                    <h4>功能亮点:</h4>
                    <ul id="videoFeatures">
                        <!-- 动态生成功能列表 -->
                    </ul>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // 演示配置
        const demoConfig = {
            smartui: {
                title: "SmartUI + MemoryOS演示",
                description: "智能界面与长期记忆系统，49.11%性能提升",
                videoUrl: "/demo_videos/tc_demo_001_recorded.mp4",
                features: [
                    "SmartUI智能自适应界面调整",
                    "MemoryOS长期记忆系统管理",
                    "49.11%总体性能提升",
                    "个性化用户体验优化"
                ]
            },
            mcp: {
                title: "MCP工具发现演示",
                description: "MCP-Zero引擎智能工具发现与推荐",
                videoUrl: "/demo_videos/tc_demo_002.mp4",
                features: [
                    "MCP-Zero智能引擎",
                    "14种工具自动发现",
                    "智能匹配推荐算法",
                    "零配置即用体验"
                ]
            },
            multimodel: {
                title: "端云多模型协同演示",
                description: "Claude 3.5 Sonnet与Gemini 1.5 Pro智能协同",
                videoUrl: "/demo_videos/tc_demo_003.mp4",
                features: [
                    "Claude 3.5 Sonnet深度集成",
                    "Gemini 1.5 Pro协同处理",
                    "智能模型自动切换",
                    "性能优化算法"
                ]
            },
            e2e: {
                title: "端到端自动化测试演示",
                description: "Stagewise MCP与录制即测试技术",
                videoUrl: "/demo_videos/tc_demo_004.mp4",
                features: [
                    "Stagewise MCP架构",
                    "录制即测试技术",
                    "端到端自动化流程",
                    "智能测试用例生成"
                ]
            }
        };
        
        // 播放演示函数
        function playDemo(demoType) {
            const config = demoConfig[demoType];
            if (!config) {
                alert('演示暂时不可用');
                return;
            }
            
            // 设置模态框内容
            document.getElementById('videoTitle').textContent = config.title;
            document.getElementById('videoDescription').textContent = config.description;
            document.getElementById('videoSource').src = config.videoUrl;
            
            // 设置功能列表
            const featuresContainer = document.getElementById('videoFeatures');
            featuresContainer.innerHTML = '';
            config.features.forEach(feature => {
                const li = document.createElement('li');
                li.textContent = feature;
                featuresContainer.appendChild(li);
            });
            
            // 重新加载视频
            const videoPlayer = document.getElementById('videoPlayer');
            videoPlayer.load();
            
            // 显示模态框
            document.getElementById('videoModal').style.display = 'block';
            document.body.style.overflow = 'hidden';
        }
        
        // 关闭视频模态框
        function closeVideoModal() {
            const modal = document.getElementById('videoModal');
            const videoPlayer = document.getElementById('videoPlayer');
            
            // 暂停视频
            videoPlayer.pause();
            videoPlayer.currentTime = 0;
            
            // 隐藏模态框
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
        
        // 点击模态框背景关闭
        document.getElementById('videoModal').addEventListener('click', function(e) {
            if (e.target === this) {
                closeVideoModal();
            }
        });
        
        // ESC键关闭模态框
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeVideoModal();
            }
        });
        
        // 空格键控制播放/暂停
        document.addEventListener('keydown', function(e) {
            if (e.key === ' ' && document.getElementById('videoModal').style.display === 'block') {
                e.preventDefault();
                const videoPlayer = document.getElementById('videoPlayer');
                if (videoPlayer.paused) {
                    videoPlayer.play();
                } else {
                    videoPlayer.pause();
                }
            }
        });
        
        console.log('PowerAutomation 4.0 演示系统已加载');
        console.log('支持的演示类型:', Object.keys(demoConfig));
    </script>
</body>
</html>
EOF
    
    log_success "网站内容创建完成"
}

# 创建Node.js服务器
create_nodejs_server() {
    log_info "创建Node.js服务器..."
    
    # 创建package.json
    cat > package.json << 'EOF'
{
  "name": "powerautomation-website",
  "version": "1.0.0",
  "description": "PowerAutomation 4.0 官方网站",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js",
    "pm2:start": "pm2 start server.js --name powerautomation",
    "pm2:stop": "pm2 stop powerautomation",
    "pm2:restart": "pm2 restart powerautomation"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "helmet": "^7.1.0",
    "compression": "^1.7.4"
  },
  "devDependencies": {
    "nodemon": "^3.0.2"
  },
  "keywords": ["powerautomation", "automation", "ai"],
  "author": "PowerAutomation Team",
  "license": "MIT"
}
EOF
    
    # 创建服务器文件
    cat > server.js << 'EOF'
const express = require('express');
const path = require('path');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');

const app = express();
const PORT = process.env.PORT || 3000;

// 安全中间件
app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            styleSrc: ["'self'", "'unsafe-inline'"],
            scriptSrc: ["'self'", "'unsafe-inline'"],
            imgSrc: ["'self'", "data:", "https:"],
            mediaSrc: ["'self'"],
            fontSrc: ["'self'"]
        }
    }
}));

// CORS配置
app.use(cors());

// 压缩响应
app.use(compression());

// 静态文件服务
app.use(express.static('.', {
    maxAge: '1d',
    etag: true
}));

// 健康检查端点
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        version: '1.0.0'
    });
});

// 主页路由
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// 404处理
app.use((req, res) => {
    res.status(404).json({
        error: 'Page not found',
        path: req.path
    });
});

// 错误处理
app.use((err, req, res, next) => {
    console.error('Server error:', err);
    res.status(500).json({
        error: 'Internal server error'
    });
});

// 启动服务器
app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 PowerAutomation 4.0 服务器运行在端口 ${PORT}`);
    console.log(`📱 本地访问: http://localhost:${PORT}`);
    console.log(`🌐 外部访问: http://$(hostname -I | awk '{print $1}'):${PORT}`);
    console.log(`💚 健康检查: http://localhost:${PORT}/health`);
});

// 优雅关闭
process.on('SIGTERM', () => {
    console.log('收到SIGTERM信号，正在关闭服务器...');
    process.exit(0);
});

process.on('SIGINT', () => {
    console.log('收到SIGINT信号，正在关闭服务器...');
    process.exit(0);
});
EOF
    
    log_success "Node.js服务器创建完成"
}

# 安装Node.js依赖
install_npm_dependencies() {
    log_info "安装Node.js依赖..."
    npm install
    log_success "Node.js依赖安装完成"
}

# 创建演示视频目录
create_demo_videos_directory() {
    log_info "创建演示视频目录..."
    mkdir -p demo_videos
    
    # 创建占位符视频文件（实际部署时需要替换为真实视频）
    log_warning "注意: 演示视频文件需要手动上传到 demo_videos/ 目录"
    log_info "需要的视频文件:"
    echo "  - tc_demo_001_recorded.mp4 (SmartUI + MemoryOS)"
    echo "  - tc_demo_002.mp4 (MCP工具发现)"
    echo "  - tc_demo_003.mp4 (端云多模型协同)"
    echo "  - tc_demo_004.mp4 (端到端自动化测试)"
    
    log_success "演示视频目录创建完成"
}

# 配置Nginx
configure_nginx() {
    log_info "配置Nginx..."
    
    # 创建Nginx配置
    sudo tee /etc/nginx/sites-available/powerautomation << 'EOF'
server {
    listen 80;
    server_name _;
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # 反向代理到Node.js应用
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://localhost:3000;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 视频文件特殊处理
    location /demo_videos/ {
        proxy_pass http://localhost:3000;
        proxy_buffering off;
        add_header Cache-Control "public, max-age=3600";
    }
    
    # 健康检查
    location /health {
        proxy_pass http://localhost:3000;
        access_log off;
    }
}
EOF
    
    # 启用站点
    sudo ln -sf /etc/nginx/sites-available/powerautomation /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # 测试Nginx配置
    sudo nginx -t
    
    # 重启Nginx
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    
    log_success "Nginx配置完成"
}

# 创建系统服务
create_systemd_service() {
    log_info "创建系统服务..."
    
    sudo tee /etc/systemd/system/powerautomation.service << EOF
[Unit]
Description=PowerAutomation 4.0 Website
Documentation=https://powerautomation.com
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/powerautomation
Environment=NODE_ENV=production
Environment=PORT=3000
ExecStart=/usr/bin/node server.js
Restart=on-failure
RestartSec=10
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=5

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/powerautomation

# 日志设置
StandardOutput=journal
StandardError=journal
SyslogIdentifier=powerautomation

[Install]
WantedBy=multi-user.target
EOF
    
    # 重新加载systemd
    sudo systemctl daemon-reload
    sudo systemctl enable powerautomation
    
    log_success "系统服务创建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 启动PowerAutomation服务
    sudo systemctl start powerautomation
    
    # 检查服务状态
    sleep 3
    if sudo systemctl is-active --quiet powerautomation; then
        log_success "PowerAutomation服务启动成功"
    else
        log_error "PowerAutomation服务启动失败"
        sudo systemctl status powerautomation
        exit 1
    fi
    
    # 检查Nginx状态
    if sudo systemctl is-active --quiet nginx; then
        log_success "Nginx服务运行正常"
    else
        log_error "Nginx服务异常"
        sudo systemctl status nginx
        exit 1
    fi
}

# 验证安装
verify_installation() {
    log_info "验证安装..."
    
    # 获取服务器IP
    SERVER_IP=$(curl -s http://checkip.amazonaws.com/ || hostname -I | awk '{print $1}')
    
    # 测试健康检查
    if curl -s http://localhost:3000/health > /dev/null; then
        log_success "应用健康检查通过"
    else
        log_error "应用健康检查失败"
        exit 1
    fi
    
    # 测试Nginx代理
    if curl -s http://localhost/ > /dev/null; then
        log_success "Nginx代理测试通过"
    else
        log_error "Nginx代理测试失败"
        exit 1
    fi
    
    log_success "安装验证完成"
    
    echo ""
    echo "🎉 PowerAutomation 4.0 安装完成！"
    echo ""
    echo "📱 访问地址:"
    echo "   http://$SERVER_IP"
    echo "   http://localhost"
    echo ""
    echo "🔧 管理命令:"
    echo "   sudo systemctl status powerautomation    # 查看服务状态"
    echo "   sudo systemctl restart powerautomation   # 重启服务"
    echo "   sudo systemctl logs powerautomation      # 查看日志"
    echo ""
    echo "📁 应用目录: /opt/powerautomation"
    echo "📹 视频目录: /opt/powerautomation/demo_videos"
    echo ""
    echo "⚠️  重要提醒:"
    echo "   请将演示视频文件上传到 /opt/powerautomation/demo_videos/ 目录"
    echo "   需要的文件: tc_demo_001_recorded.mp4, tc_demo_002.mp4, tc_demo_003.mp4, tc_demo_004.mp4"
    echo ""
}

# 主函数
main() {
    echo "🚀 PowerAutomation 4.0 自动化安装开始..."
    echo "================================================"
    
    check_root
    update_system
    install_dependencies
    install_nodejs
    install_docker
    install_docker_compose
    configure_firewall
    create_app_directory
    download_website
    create_nodejs_server
    install_npm_dependencies
    create_demo_videos_directory
    configure_nginx
    create_systemd_service
    start_services
    verify_installation
    
    echo "================================================"
    echo "✅ PowerAutomation 4.0 安装完成！"
}

# 执行主函数
main "$@"

