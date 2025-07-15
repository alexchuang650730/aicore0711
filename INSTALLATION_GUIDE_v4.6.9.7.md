# PowerAutomation v4.6.9.7 安裝指南

## 🚀 macOS 一鍵安裝

### 方法1: curl 一行命令安裝
```bash
curl -fsSL https://raw.githubusercontent.com/alexchuang650730/aicore0711/main/install-script-macos-v4.6.9.7.sh | bash
```

### 方法2: npm 全局安裝
```bash
# 安裝安裝工具
npm install -g powerautomation-installer

# 運行安裝
powerautomation install
```

### 方法3: 手動下載安裝
```bash
# 下載安裝腳本
wget https://raw.githubusercontent.com/alexchuang650730/aicore0711/main/install-script-macos-v4.6.9.7.sh

# 添加執行權限
chmod +x install-script-macos-v4.6.9.7.sh

# 運行安裝
./install-script-macos-v4.6.9.7.sh
```

---

## 📱 特色功能

### 🤖 K2 AI模型集成
- **成本節省**: 60% vs Claude Code
- **高性能**: 500 QPS處理能力
- **智能路由**: 自動選擇最佳模型
- **無縫遷移**: 從Claude Code平滑遷移

### 💰 支付儲值積分系統
- **多版本支持**: Community/Personal/Enterprise
- **靈活儲值**: 支持多種支付方式
- **積分管理**: 完整的積分歷史和管理
- **企業授權**: 支持企業級批量授權

### 📱 PC/Mobile 響應式支持
- **智能UI適配**: 根據設備自動調整界面
- **觸控優化**: 專為移動設備優化的交互
- **離線功能**: 核心功能支持離線使用
- **手勢支持**: 支持滑動、縮放等手勢操作

### 🎨 ClaudeEditor 桌面版
- **實時編輯**: 支持多人協作編輯
- **語法高亮**: 支持主流編程語言
- **AI輔助**: 集成K2模型提供編程助手
- **插件系統**: 可擴展的插件架構

---

## 🌐 網站地址

### 主要服務
- **主站**: https://powerauto.aiweb.com
- **支付系統**: https://powerauto.aiweb.com/payment
- **積分管理**: https://powerauto.aiweb.com/credits
- **用戶面板**: https://powerauto.aiweb.com/dashboard

### 支持服務
- **文檔中心**: https://powerauto.aiweb.com/docs
- **API文檔**: https://powerauto.aiweb.com/api
- **技術支持**: https://powerauto.aiweb.com/support
- **社區論壇**: https://powerauto.aiweb.com/community

---

## 💳 版本和定價

### Community版 (免費)
- ✅ 基礎AI功能
- ✅ 基本編輯器
- ✅ 有限的K2調用
- ✅ 社區支持
- **價格**: 免費
- **積分**: 0積分

### Personal版 (個人版)
- ✅ 完整AI功能
- ✅ 高級編輯器
- ✅ 無限K2調用
- ✅ 優先支持
- ✅ 移動端優化
- **價格**: 100積分
- **積分**: 100積分/月

### Enterprise版 (企業版)
- ✅ 全部功能
- ✅ 企業級支持
- ✅ 自定義集成
- ✅ 專屬服務器
- ✅ SLA保障
- **價格**: 500積分
- **積分**: 500積分/月

---

## 🔧 系統要求

### macOS要求
- **操作系統**: macOS 10.15 (Catalina) 或更高版本
- **處理器**: Intel 或 Apple Silicon
- **內存**: 4GB RAM (推薦8GB)
- **存儲**: 2GB 可用空間
- **網絡**: 穩定的互聯網連接

### 必要工具
- **Node.js**: 16.0.0 或更高版本
- **npm**: 8.0.0 或更高版本
- **Python**: 3.8 或更高版本
- **Git**: 最新版本
- **curl**: 系統自帶

---

## 🚀 啟動和使用

### 安裝後啟動
```bash
# 方法1: 使用桌面快捷方式
# 雙擊桌面上的 PowerAutomation.command

# 方法2: 命令行啟動
cd ~/PowerAutomation
./start-powerautomation.sh

# 方法3: 後台啟動
nohup ./start-powerautomation.sh > powerautomation.log 2>&1 &
```

### 服務地址
安裝完成後，以下服務將自動啟動：

| 服務 | 地址 | 說明 |
|------|------|------|
| K2服務 | http://localhost:8765 | AI模型服務 |
| Mirror服務 | http://localhost:8080 | 代碼同步服務 |
| ClaudeEditor | http://localhost:3000 | 桌面編輯器 |
| 支付系統 | http://localhost:3001 | 積分管理系統 |

### 移動端訪問
- **iPhone/iPad**: 在Safari中訪問上述地址
- **Android**: 在Chrome中訪問上述地址
- **響應式設計**: 自動適配移動設備屏幕
- **PWA支持**: 可添加到主屏幕使用

---

## 🔒 積分系統使用

### 註冊賬戶
1. 訪問 https://powerauto.aiweb.com/register
2. 填寫註冊信息
3. 驗證郵箱
4. 獲取用戶token

### 儲值流程
1. 登錄 https://powerauto.aiweb.com/recharge
2. 選擇充值金額
3. 選擇支付方式
4. 完成支付
5. 積分自動到賬

### 積分管理
- **查看餘額**: https://powerauto.aiweb.com/dashboard
- **消費記錄**: https://powerauto.aiweb.com/history
- **充值記錄**: https://powerauto.aiweb.com/recharge/history
- **發票下載**: https://powerauto.aiweb.com/invoice

---

## 📱 移動端使用指南

### iOS設備
1. **Safari瀏覽器**: 打開服務地址
2. **添加到主屏幕**: 點擊分享按鈕 → 添加到主屏幕
3. **全屏模式**: 支持全屏運行
4. **觸控優化**: 支持手勢操作

### Android設備
1. **Chrome瀏覽器**: 打開服務地址
2. **安裝應用**: 點擊"添加到主屏幕"提示
3. **離線使用**: 支持離線功能
4. **通知支持**: 支持系統通知

### 功能對比

| 功能 | 桌面版 | 移動版 | 說明 |
|------|--------|--------|------|
| AI對話 | ✅ | ✅ | 完整支持 |
| 代碼編輯 | ✅ | ✅ | 觸控優化 |
| 文件管理 | ✅ | ✅ | 響應式界面 |
| 積分管理 | ✅ | ✅ | 完整功能 |
| 離線使用 | ✅ | ✅ | 核心功能 |
| 通知推送 | ✅ | ✅ | 系統通知 |

---

## 🔧 故障排除

### 常見問題

#### 1. 安裝失敗
```bash
# 檢查系統要求
sw_vers -productVersion  # 檢查macOS版本
node --version           # 檢查Node.js版本
python3 --version        # 檢查Python版本

# 清理並重新安裝
rm -rf ~/PowerAutomation
curl -fsSL https://raw.githubusercontent.com/alexchuang650730/aicore0711/main/install-script-macos-v4.6.9.7.sh | bash
```

#### 2. 服務啟動失敗
```bash
# 檢查端口占用
lsof -i :8765  # K2服務端口
lsof -i :8080  # Mirror服務端口
lsof -i :3000  # ClaudeEditor端口

# 重新啟動服務
cd ~/PowerAutomation
./start-powerautomation.sh
```

#### 3. 積分系統問題
```bash
# 檢查token
cat ~/.powerauto_token

# 重新設置token
echo "YOUR_NEW_TOKEN" > ~/.powerauto_token
chmod 600 ~/.powerauto_token

# 測試積分API
curl -H "Authorization: Bearer $(cat ~/.powerauto_token)" \
  https://api.powerauto.aiweb.com/v1/credits/balance
```

#### 4. 移動端問題
- **清除瀏覽器緩存**: 設置 → 清除瀏覽數據
- **重新添加到主屏幕**: 刪除舊圖標，重新添加
- **檢查網絡連接**: 確保WiFi或移動網絡正常
- **更新瀏覽器**: 使用最新版本瀏覽器

### 日誌查看
```bash
# 主服務日誌
tail -f ~/PowerAutomation/powerautomation.log

# K2服務日誌
tail -f ~/PowerAutomation/k2_service.log

# Mirror服務日誌
tail -f ~/PowerAutomation/mirror_service.log

# 系統日誌
tail -f /var/log/system.log | grep PowerAutomation
```

---

## 🆘 獲取幫助

### 技術支持
- **在線客服**: https://powerauto.aiweb.com/support
- **技術論壇**: https://powerauto.aiweb.com/community
- **GitHub Issues**: https://github.com/alexchuang650730/aicore0711/issues
- **郵件支持**: support@powerauto.aiweb.com

### 文檔資源
- **API文檔**: https://powerauto.aiweb.com/api
- **開發者指南**: https://powerauto.aiweb.com/docs/dev
- **用戶手冊**: https://powerauto.aiweb.com/docs/user
- **視頻教程**: https://powerauto.aiweb.com/videos

### 社區資源
- **Discord**: https://discord.gg/powerauto
- **Telegram**: https://t.me/powerauto
- **微信群**: 關注公眾號獲取群二維碼
- **QQ群**: 123456789

---

## 📄 許可證

PowerAutomation v4.6.9.7 使用 MIT 許可證發布。

更多信息請查看 [LICENSE](LICENSE) 文件。

---

## 🔄 更新日誌

### v4.6.9.7 (2025-07-15)
- ✅ 新增支付儲值積分系統
- ✅ 完善PC/Mobile響應式支持
- ✅ 優化K2模型集成
- ✅ 增強安裝腳本功能
- ✅ 改進移動端用戶體驗

### v4.6.9.6 (2025-07-14)
- ✅ K2遷移測試完成
- ✅ Mirror Code配置修正
- ✅ 全面測試套件
- ✅ 性能優化

---

**PowerAutomation Team**  
© 2025 PowerAutomation. All rights reserved.