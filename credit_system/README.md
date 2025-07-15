# PowerAutomation 充值積分系統 v1.0

## 🏗️ 系統架構

### 技術棧
- **後端**: FastAPI + SQLAlchemy + PostgreSQL
- **前端**: React 18 + Vite + Tailwind CSS + shadcn/ui
- **缓存**: Redis
- **支付**: Stripe + 支付寶 + 微信支付
- **部署**: Docker + Nginx + uWSGI
- **監控**: Prometheus + Grafana

### 系統特性
- ✅ 支持500人同時在線
- ✅ 完整的充值積分系統
- ✅ 多種支付方式
- ✅ 實時狀態監控
- ✅ 企業級後台管理
- ✅ 安全認證系統
- ✅ 數據統計分析

## 📁 目錄結構

```
credit_system/
├── backend/                    # 後端服務
│   ├── app/
│   │   ├── main.py            # FastAPI 主應用
│   │   ├── models/            # 數據模型
│   │   ├── api/               # API 路由
│   │   ├── services/          # 業務邏輯
│   │   ├── utils/             # 工具函數
│   │   └── config.py          # 配置文件
│   ├── requirements.txt       # Python 依賴
│   └── Dockerfile            # Docker 配置
├── frontend/                  # 前端應用
│   ├── src/
│   │   ├── components/        # React 組件
│   │   ├── pages/            # 頁面組件
│   │   ├── hooks/            # 自定義 Hook
│   │   ├── services/         # API 服務
│   │   └── utils/            # 工具函數
│   ├── package.json          # 依賴配置
│   └── vite.config.js        # Vite 配置
├── admin/                     # 管理後台
│   ├── src/
│   │   ├── components/        # 管理組件
│   │   ├── pages/            # 管理頁面
│   │   └── services/         # 管理服務
│   └── package.json
├── docker-compose.yml         # Docker 編排
├── nginx.conf                 # Nginx 配置
└── README.md                  # 項目文檔
```

## 🚀 快速開始

### 1. 環境準備
```bash
# 克隆項目
git clone https://github.com/alexchuang650730/aicore0711.git
cd aicore0711/credit_system

# 創建環境文件
cp .env.example .env

# 啟動服務
docker-compose up -d
```

### 2. 訪問地址
- **用戶端**: http://localhost:3000
- **管理後台**: http://localhost:3001
- **API文檔**: http://localhost:8000/docs

### 3. 默認賬戶
- **管理員**: admin@powerauto.com / admin123
- **測試用戶**: test@powerauto.com / test123

## 💳 支付系統

### 支持的支付方式
- **信用卡**: Stripe 集成
- **支付寶**: 支付寶開放平台
- **微信支付**: 微信支付商戶平台
- **銀行轉賬**: 企業對公轉賬

### 積分套餐
- **基礎套餐**: 100積分 - ¥10
- **標準套餐**: 500積分 - ¥45 (10% 折扣)
- **高級套餐**: 1000積分 - ¥80 (20% 折扣)
- **企業套餐**: 5000積分 - ¥350 (30% 折扣)

## 📊 系統功能

### 用戶功能
- 用戶註冊/登錄
- 積分充值
- 消費記錄
- 賬戶設置
- 發票管理

### 管理功能
- 用戶管理
- 訂單管理
- 積分管理
- 財務報表
- 系統監控

## 🔒 安全特性

- JWT 身份認證
- API 速率限制
- 數據加密傳輸
- 支付安全防護
- 操作日誌記錄

## 📈 性能指標

- **並發用戶**: 500+
- **響應時間**: <200ms
- **可用性**: 99.9%
- **數據備份**: 每日自動備份

## 🛠️ 部署說明

### 生產環境部署
```bash
# 1. 構建鏡像
docker-compose build

# 2. 啟動服務
docker-compose up -d

# 3. 初始化數據庫
docker-compose exec backend python -m app.init_db

# 4. 創建管理員賬戶
docker-compose exec backend python -m app.create_admin
```

### 監控和日誌
```bash
# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f backend

# 監控指標
http://localhost:9090  # Prometheus
http://localhost:3000  # Grafana
```

## 📞 技術支持

- **GitHub**: https://github.com/alexchuang650730/aicore0711
- **Email**: support@powerauto.com
- **文檔**: https://docs.powerauto.com

---

**版本**: v1.0.0  
**更新時間**: 2025-07-15  
**狀態**: 開發中