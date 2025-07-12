# 🏠 PowerAutomation + ClaudeEditor 本地部署指南

本指南將幫助您在本地環境快速部署 PowerAutomation + ClaudeEditor 整合系統，包括開發環境設置和生產環境配置。

---

## 🎯 部署概覽

### 支持的部署方式
- 🖥️ **開發環境**: 本地開發和測試
- 🐳 **Docker 容器**: 一鍵部署解決方案
- 📦 **NPM 包安裝**: 集成到現有項目
- 🔧 **源碼編譯**: 自定義構建

### 系統需求
- **操作系統**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **Node.js**: v16+ (推薦 v18 LTS)
- **內存**: 最少 4GB, 推薦 8GB+
- **存儲**: 最少 2GB 可用空間
- **網絡**: 穩定的互聯網連接

---

## 🚀 快速部署 (推薦)

### 方式一: Docker 一鍵部署

```bash
# 1. 克隆倉庫
git clone https://github.com/alexchuang650730/aicore0711.git
cd aicore0711

# 2. 配置環境變量
cp .env.example .env
# 編輯 .env 文件，填入您的許可證密鑰

# 3. 啟動 Docker 服務
docker-compose up -d

# 4. 驗證部署
curl http://localhost:8080/health
# 預期返回: {"status": "healthy", "version": "4.6.9"}
```

### Docker Compose 配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  powerautomation-core:
    image: powerautomation/core:4.6.9
    ports:
      - "8080:8080"
    environment:
      - PA_LICENSE=${PA_LICENSE}
      - PA_EDITION=${PA_EDITION}
      - NODE_ENV=production
    volumes:
      - ./workspace:/app/workspace
      - ./config:/app/config
    depends_on:
      - redis
      - postgres

  claude-editor-desktop:
    image: powerautomation/claude-editor-desktop:1.2.0
    ports:
      - "3000:3000"
    environment:
      - PA_CORE_URL=http://powerautomation-core:8080
      - CLAUDE_CLI_ENABLED=true
    volumes:
      - ./projects:/app/projects

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=powerautomation
      - POSTGRES_USER=pa_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  redis_data:
  postgres_data:
```

---

## 📦 NPM 包部署

### 方式二: 集成到現有項目

```bash
# 1. 初始化項目（如果是新項目）
mkdir my-powerautomation-project
cd my-powerautomation-project
npm init -y

# 2. 安裝核心包
npm install @powerautomation/core

# 3. 根據版本安裝對應功能包
# 專業版
npm install @powerautomation/claude-editor-desktop

# 團隊版（包含協作功能）
npm install @powerautomation/collaboration

# 企業版（完整功能）
npm install @powerautomation/enterprise-cli
```

### 項目配置

```javascript
// app.js
const { PowerAutomation } = require('@powerautomation/core');
const { ClaudeEditorDesktop } = require('@powerautomation/claude-editor-desktop');

async function initializePowerAutomation() {
  // 初始化核心系統
  const pa = new PowerAutomation({
    license: process.env.PA_LICENSE,
    workspace: './workspace',
    config: {
      redis: {
        host: 'localhost',
        port: 6379
      },
      database: {
        host: 'localhost',
        port: 5432,
        database: 'powerautomation'
      }
    }
  });

  // 驗證許可證
  const isValid = await pa.validateLicense();
  if (!isValid) {
    throw new Error('許可證驗證失敗');
  }

  // 初始化 ClaudeEditor
  const editor = new ClaudeEditorDesktop({
    powerAutomation: pa,
    port: 3000,
    features: {
      claudeCodeIntegration: true,
      realTimeSync: true,
      collaboration: pa.edition !== 'personal'
    }
  });

  // 啟動服務
  await pa.start();
  await editor.start();

  console.log('✅ PowerAutomation + ClaudeEditor 啟動成功!');
  console.log(`🌐 ClaudeEditor 訪問地址: http://localhost:3000`);
  console.log(`📊 API 文檔: http://localhost:8080/docs`);
}

// 啟動應用
initializePowerAutomation().catch(console.error);
```

---

## 🔧 開發環境設置

### 方式三: 源碼開發部署

```bash
# 1. 克隆並設置開發環境
git clone https://github.com/alexchuang650730/aicore0711.git
cd aicore0711

# 2. 安裝依賴
npm install

# 3. 設置環境變量
cp .env.development .env
# 編輯 .env 配置開發參數

# 4. 啟動開發數據庫
docker-compose -f docker-compose.dev.yml up -d redis postgres

# 5. 運行數據庫遷移
npm run db:migrate

# 6. 啟動開發服務器
npm run dev

# 7. 並行啟動 ClaudeEditor
cd claude-editor
npm install
npm run dev
```

### 開發環境配置

```yaml
# .env.development
# PowerAutomation 核心配置
PA_LICENSE=PA-DEV-20241213-0000
PA_EDITION=professional
NODE_ENV=development
LOG_LEVEL=debug

# 數據庫配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=powerautomation_dev
DB_USER=dev_user
DB_PASSWORD=dev_password

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379

# Claude Code CLI 配置
CLAUDE_CLI_PATH=/usr/local/bin/claude-code
CLAUDE_CLI_ENABLED=true

# ClaudeEditor 配置
EDITOR_PORT=3000
EDITOR_DEBUG=true
```

### 開發腳本

```json
{
  "scripts": {
    "dev": "concurrently \"npm run dev:core\" \"npm run dev:editor\"",
    "dev:core": "nodemon src/index.js",
    "dev:editor": "cd claude-editor && npm run dev",
    "build": "npm run build:core && npm run build:editor",
    "test": "jest --coverage",
    "test:watch": "jest --watch",
    "db:migrate": "knex migrate:latest",
    "db:seed": "knex seed:run",
    "docker:dev": "docker-compose -f docker-compose.dev.yml up",
    "lint": "eslint src/ claude-editor/src/",
    "format": "prettier --write \"src/**/*.js\" \"claude-editor/src/**/*.{js,jsx}\""
  }
}
```

---

## 🐳 Docker 部署詳解

### 完整 Docker 配置

```dockerfile
# Dockerfile.core
FROM node:18-alpine

WORKDIR /app

# 安裝系統依賴
RUN apk add --no-cache \
    git \
    python3 \
    make \
    g++ \
    && rm -rf /var/cache/apk/*

# 複製 package files
COPY package*.json ./
COPY lerna.json ./
COPY packages/core/package*.json ./packages/core/

# 安裝依賴
RUN npm ci --only=production

# 複製源碼
COPY packages/core ./packages/core
COPY shared ./shared

# 構建應用
RUN npm run build

# 健康檢查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# 啟動應用
EXPOSE 8080
CMD ["npm", "start"]
```

```dockerfile
# Dockerfile.editor
FROM node:18-alpine

WORKDIR /app

# 安裝 ClaudeEditor 依賴
RUN apk add --no-cache \
    git \
    curl \
    && rm -rf /var/cache/apk/*

# 安裝 Claude Code CLI
RUN curl -fsSL https://claude.ai/install.sh | sh

# 複製並構建編輯器
COPY claude-editor/package*.json ./
RUN npm ci --only=production

COPY claude-editor ./
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

### 多環境 Docker Compose

```yaml
# docker-compose.production.yml
version: '3.8'

services:
  powerautomation-core:
    image: powerautomation/core:4.6.9
    restart: unless-stopped
    environment:
      - NODE_ENV=production
      - PA_LICENSE=${PA_LICENSE}
      - DB_HOST=postgres
      - REDIS_HOST=redis
    networks:
      - powerautomation-network
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  claude-editor:
    image: powerautomation/claude-editor:1.2.0
    restart: unless-stopped
    environment:
      - NODE_ENV=production
      - PA_CORE_URL=http://powerautomation-core:8080
    networks:
      - powerautomation-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - powerautomation-core
      - claude-editor
    networks:
      - powerautomation-network

networks:
  powerautomation-network:
    driver: bridge
```

---

## ⚙️ 配置管理

### 環境配置文件

```yaml
# config/local.yaml
server:
  port: 8080
  host: localhost

database:
  client: postgresql
  connection:
    host: localhost
    port: 5432
    database: powerautomation
    user: pa_user
    password: ${DB_PASSWORD}
  pool:
    min: 2
    max: 10

redis:
  host: localhost
  port: 6379
  password: ${REDIS_PASSWORD}
  db: 0

powerautomation:
  license: ${PA_LICENSE}
  edition: ${PA_EDITION}
  workspace: ./workspace
  
  features:
    mcp_components:
      enabled: true
      cache_ttl: 3600
    workflows:
      enabled: true
      max_concurrent: 10
    collaboration:
      enabled: true
      websocket_port: 3001

claude_editor:
  port: 3000
  claude_cli:
    enabled: true
    path: /usr/local/bin/claude-code
  features:
    real_time_sync: true
    offline_mode: false
    collaboration: true

logging:
  level: info
  format: json
  file: ./logs/powerautomation.log
```

### Nginx 配置

```nginx
# nginx.conf
upstream powerautomation_core {
    server powerautomation-core:8080;
}

upstream claude_editor {
    server claude-editor:3000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # PowerAutomation Core API
    location /api/ {
        proxy_pass http://powerautomation_core;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # ClaudeEditor
    location / {
        proxy_pass http://claude_editor;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 🔍 部署驗證

### 健康檢查腳本

```bash
#!/bin/bash
# health-check.sh

echo "🔍 PowerAutomation + ClaudeEditor 部署驗證"
echo "============================================"

# 檢查核心服務
echo "📡 檢查 PowerAutomation Core..."
CORE_HEALTH=$(curl -s http://localhost:8080/health | jq -r '.status')
if [ "$CORE_HEALTH" = "healthy" ]; then
    echo "✅ PowerAutomation Core: 正常"
else
    echo "❌ PowerAutomation Core: 異常"
    exit 1
fi

# 檢查 ClaudeEditor
echo "📝 檢查 ClaudeEditor..."
EDITOR_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [ "$EDITOR_STATUS" = "200" ]; then
    echo "✅ ClaudeEditor: 正常"
else
    echo "❌ ClaudeEditor: 異常"
    exit 1
fi

# 檢查數據庫連接
echo "🗄️ 檢查數據庫連接..."
DB_STATUS=$(curl -s http://localhost:8080/api/health/db | jq -r '.connected')
if [ "$DB_STATUS" = "true" ]; then
    echo "✅ 數據庫: 連接正常"
else
    echo "❌ 數據庫: 連接失敗"
    exit 1
fi

# 檢查 Redis 連接
echo "📦 檢查 Redis 連接..."
REDIS_STATUS=$(curl -s http://localhost:8080/api/health/redis | jq -r '.connected')
if [ "$REDIS_STATUS" = "true" ]; then
    echo "✅ Redis: 連接正常"
else
    echo "❌ Redis: 連接失敗"
    exit 1
fi

# 檢查許可證
echo "🔑 檢查許可證狀態..."
LICENSE_STATUS=$(curl -s http://localhost:8080/api/license/status | jq -r '.valid')
if [ "$LICENSE_STATUS" = "true" ]; then
    echo "✅ 許可證: 有效"
    EDITION=$(curl -s http://localhost:8080/api/license/status | jq -r '.edition')
    echo "📋 版本: $EDITION"
else
    echo "❌ 許可證: 無效或過期"
    exit 1
fi

echo ""
echo "🎉 所有服務部署驗證通過!"
echo "🌐 ClaudeEditor 訪問地址: http://localhost:3000"
echo "📊 API 文檔: http://localhost:8080/docs"
```

### 性能基準測試

```bash
#!/bin/bash
# benchmark.sh

echo "📊 PowerAutomation 性能基準測試"
echo "================================="

# API 響應時間測試
echo "⚡ API 響應時間測試..."
for i in {1..10}; do
    RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:8080/api/health)
    echo "請求 $i: ${RESPONSE_TIME}s"
done

# 代碼生成性能測試
echo "🤖 代碼生成性能測試..."
START_TIME=$(date +%s.%N)
curl -s -X POST http://localhost:8080/api/mcp/codeflow/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "創建React組件", "language": "javascript"}' > /dev/null
END_TIME=$(date +%s.%N)
DURATION=$(echo "$END_TIME - $START_TIME" | bc)
echo "代碼生成耗時: ${DURATION}s"

# 併發測試
echo "🔄 併發測試 (10個併發請求)..."
ab -n 100 -c 10 http://localhost:8080/api/health
```

---

## 🚨 故障排除

### 常見問題解決

#### 1. 許可證驗證失敗
```bash
# 檢查許可證格式
echo $PA_LICENSE
# 應該類似: PA-PROFESSIONAL-20241213-1234

# 檢查網絡連接
curl -I https://api.powerautomation.com/license/validate

# 重新生成許可證
powerautomation-cli license refresh
```

#### 2. ClaudeEditor 無法啟動
```bash
# 檢查 Node.js 版本
node --version  # 需要 v16+

# 檢查端口占用
lsof -i :3000

# 清除緩存重新安裝
rm -rf node_modules claude-editor/node_modules
npm install
cd claude-editor && npm install
```

#### 3. 數據庫連接問題
```bash
# 檢查 PostgreSQL 狀態
docker-compose logs postgres

# 重置數據庫
docker-compose down
docker volume rm aicore0711_postgres_data
docker-compose up -d postgres
npm run db:migrate
```

#### 4. Claude Code CLI 集成失敗
```bash
# 檢查 Claude Code CLI 安裝
claude-code --version

# 重新配置集成
powerautomation-cli claude-code disconnect
powerautomation-cli claude-code connect

# 檢查權限
which claude-code
ls -la $(which claude-code)
```

### 日誌分析

```bash
# 查看應用日誌
docker-compose logs -f powerautomation-core
docker-compose logs -f claude-editor

# 查看詳細錯誤日誌
tail -f logs/powerautomation.log | grep ERROR

# 實時監控系統資源
htop
docker stats
```

---

## 📈 生產環境優化

### 性能優化配置

```yaml
# config/production.yaml
server:
  workers: 4  # CPU 核心數
  timeout: 30000
  
database:
  pool:
    min: 5
    max: 20
    idle_timeout: 300000
    
redis:
  pool:
    min: 5
    max: 15
    
powerautomation:
  cache:
    enabled: true
    ttl: 3600
  queue:
    concurrency: 10
    retry_attempts: 3
```

### 監控配置

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  grafana_data:
```

---

## 🎯 部署總結

本地部署 PowerAutomation + ClaudeEditor 提供了：

1. **🚀 快速部署**: Docker 一鍵啟動
2. **🔧 靈活配置**: 支持多種部署方式
3. **📊 完整監控**: 健康檢查和性能監控
4. **🛡️ 安全可靠**: SSL、認證和權限控制
5. **📈 可擴展性**: 支持集群和負載均衡

遵循本指南，您可以快速在本地搭建完整的 PowerAutomation + ClaudeEditor 開發或生產環境。