# PowerAutomation v4.5 Mac版本使用說明

## 🚀 ClaudEditor 4.5 - Manus競爭者版本

**版本**: 4.5.0  
**發布日期**: 2025-01-10  
**平台**: macOS 10.15+  
**代號**: "Manus Competitor"

---

## 📥 快速下載

### 官方下載連結
- **GitHub Release**: https://github.com/alexchuang650730/aicore0711/releases/tag/v4.5.0
- **直接下載**: https://github.com/alexchuang650730/aicore0711/archive/refs/heads/main.zip

### 系統要求
- **macOS**: 10.15 (Catalina) 或更新版本
- **Python**: 3.8+ (建議 3.11)
- **記憶體**: 8GB RAM (推薦 16GB)
- **磁盤空間**: 2GB 可用空間
- **網路**: 用於API調用 (支援離線工作)

---

## ⚡ 一鍵安裝指南

### 方法一：自動安裝腳本 (推薦)
```bash
# 1. 下載並解壓
curl -L https://github.com/alexchuang650730/aicore0711/archive/refs/heads/main.zip -o aicore0711.zip
unzip aicore0711.zip
cd aicore0711-main

# 2. 一鍵安裝和啟動
./start_claudeditor_mac.sh
```

### 方法二：Git克隆
```bash
# 1. 克隆倉庫
git clone https://github.com/alexchuang650730/aicore0711.git
cd aicore0711

# 2. 啟動安裝
./start_claudeditor_mac.sh
```

### 方法三：手動安裝
```bash
# 1. 創建虛擬環境
python3 -m venv venv
source venv/bin/activate

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 安裝Mac專用依賴
pip install pyobjc-framework-Cocoa pyobjc-framework-Quartz

# 4. 啟動服務
./start_claudeditor_mac.sh start
```

---

## 🎯 第一次使用配置

### 1. 配置Claude API密鑰
```bash
# 編輯配置文件
nano config/claudeditor_config.yaml

# 在claude.api_key處填入您的API密鑰
claude:
  api_key: "your-claude-api-key-here"
```

### 2. 驗證安裝
```bash
# 檢查服務狀態
curl http://localhost:8080/health
curl http://localhost:8082/health

# 查看日誌
tail -f logs/claudeditor.log
```

### 3. 訪問界面
- **主界面**: http://localhost:8080
- **React前端**: http://localhost:5173 (如果有Node.js)
- **AI助手**: 直接在界面中使用

---

## 🔧 常用命令

### 服務管理
```bash
# 啟動所有服務
./start_claudeditor_mac.sh start

# 僅安裝依賴
./start_claudeditor_mac.sh install

# 編輯配置
./start_claudeditor_mac.sh config

# 運行測試
./start_claudeditor_mac.sh test

# 查看幫助
./start_claudeditor_mac.sh help
```

### 故障排除
```bash
# 檢查Python版本
python3 --version

# 檢查依賴
pip list | grep -E "(anthropic|fastapi|uvicorn)"

# 檢查端口占用
lsof -i :8080
lsof -i :8082
lsof -i :8083

# 重置環境
rm -rf venv
./start_claudeditor_mac.sh install
```

---

## 🆕 v4.5 新功能使用指南

### 1. 自主任務執行
```javascript
// 在AI助手中直接描述任務
"創建一個React登錄組件，包含表單驗證"

// AI會自動：
✅ 分析需求
✅ 制定計劃  
✅ 生成代碼
✅ 創建測試
✅ 編寫文檔
```

### 2. 項目分析功能
```bash
# 點擊"🧠 分析項目"按鈕，或使用命令：
python -m core.components.project_analyzer_mcp.project_analyzer

# 獲得：
• 完整架構分析
• 依賴關係圖
• API端點列表
• 代碼質量報告
```

### 3. 智能錯誤檢測
```bash
# 自動掃描錯誤
python -m core.components.intelligent_error_handler_mcp.error_handler

# 功能：
• 語法錯誤檢測
• 邏輯問題分析
• 性能瓶頸識別
• 自動修復建議
```

### 4. 會話分享
```javascript
// 在AI助手中
1. 點擊分享按鈕
2. 生成分享連結
3. 邀請團隊成員
4. 實時協作編程
```

---

## 🎨 界面指南

### 主界面布局
```
┌─────────────────────────────────────────┐
│ 🤖 自主AI助手 (Claude) - vs Manus準備就緒   │
├─────────────────────────────────────────┤
│ 🧠 分析項目 (超越Manus的關鍵)               │
├─────────────────────────────────────────┤
│ 🚀 創建React應用  🐛 自動調試             │
│ ⚡ 性能優化      🧪 生成測試               │
│ 📝 API文檔      🔍 代碼審查               │
├─────────────────────────────────────────┤
│ 💬 對話區域                             │
│ [基於項目上下文回復] [本地降級回復]          │
└─────────────────────────────────────────┘
```

### 快速操作
- **Ctrl+Enter**: 發送消息
- **Ctrl+N**: 新建會話
- **Ctrl+S**: 保存會話
- **Ctrl+R**: 重新分析項目
- **Cmd+,**: 打開設置

---

## 🏆 與Manus對比

### 使用體驗對比
| 功能 | ClaudEditor v4.5 | Manus | 優勢說明 |
|------|------------------|-------|----------|
| **啟動速度** | ⚡ 10-15秒 | 🐌 30-60秒 | 本地啟動更快 |
| **響應時間** | 🚀 50-200ms | 🐌 500-2000ms | 本地處理優勢 |
| **離線使用** | ✅ 完全支援 | ❌ 必須聯網 | 隱私和穩定性 |
| **項目理解** | 🧠 完整分析 | 🤔 片段理解 | 全局上下文 |
| **協作功能** | 🎬 高級分享 | 📤 基礎分享 | 回放和實時 |
| **定價** | 💰 ¥99/月 | 💸 ¥300+/月 | 3-15倍更便宜 |

### 實際使用建議
1. **隱私敏感項目**: 選擇ClaudEditor (代碼不離開本機)
2. **團隊協作**: 使用會話分享功能
3. **大型項目**: 利用項目級分析能力
4. **快速原型**: 自主任務執行功能

---

## 🛡️ 安全和隱私

### 數據保護
- ✅ **代碼本地處理**: 所有代碼分析在本機進行
- ✅ **API密鑰安全**: 僅存儲在本地配置文件
- ✅ **會話加密**: 協作會話端到端加密
- ✅ **無遙測**: 不收集使用統計或代碼內容

### 企業部署
- 🏢 **內網部署**: 支援完全內網環境
- 🔐 **訪問控制**: 可配置用戶權限
- 📋 **審計日誌**: 詳細的操作記錄
- 🛡️ **安全掃描**: 內建代碼安全檢查

---

## 📊 性能優化

### 系統調優
```bash
# 增加文件描述符限制
ulimit -n 65536

# 優化Python性能
export PYTHONOPTIMIZE=1

# 調整並發數
export MAX_CONCURRENT_TASKS=5
```

### 記憶體管理
```yaml
# config/claudeditor_config.yaml
performance:
  max_concurrent_tasks: 5    # 根據RAM調整
  response_cache: true       # 啟用緩存
  memory_limit: "4GB"        # 記憶體限制
```

---

## 🔄 更新和維護

### 自動更新
```bash
# 檢查更新
git fetch origin
git status

# 更新到最新版本
git pull origin main
./start_claudeditor_mac.sh install
```

### 手動維護
```bash
# 清理緩存
rm -rf logs/*.log
rm -rf temp/*

# 重建虛擬環境
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 備份重要數據
```bash
# 備份配置
cp config/claudeditor_config.yaml ~/claudeditor_backup.yaml

# 備份會話數據
cp -r sessions/ ~/claudeditor_sessions_backup/
```

---

## 🆘 故障排除

### 常見問題

#### 1. 服務啟動失敗
```bash
# 問題：端口被占用
Error: Address already in use

# 解決：
lsof -i :8080
kill -9 [PID]
```

#### 2. Python版本問題
```bash
# 問題：Python版本過低
Error: Python 3.8+ required

# 解決：
brew install python@3.11
```

#### 3. 依賴安裝失敗
```bash
# 問題：pip安裝失敗
# 解決：
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

#### 4. API調用失敗
```bash
# 問題：Claude API無響應
# 解決：
1. 檢查API密鑰是否正確
2. 確認網路連接
3. 查看API使用額度
```

### 日誌分析
```bash
# 查看錯誤日誌
tail -f logs/claudeditor.log | grep ERROR

# 查看性能日誌
grep "performance" logs/claudeditor.log

# 實時監控
watch -n 1 'ps aux | grep python'
```

---

## 🤝 社群和支援

### 獲取幫助
- **GitHub Issues**: https://github.com/alexchuang650730/aicore0711/issues
- **討論區**: GitHub Discussions
- **文檔**: 查看CLAUDE.md文件
- **示例**: 查看deployment/examples/

### 反饋和建議
- 🐛 **Bug報告**: 使用GitHub Issues
- 💡 **功能建議**: 提交Feature Request
- ⭐ **評價**: 在GitHub給我們Star
- 📢 **分享**: 推薦給其他開發者

---

## 🎯 下一步

### 學習路徑
1. **基礎使用** (30分鐘)
   - 完成安裝和配置
   - 嘗試基本AI對話
   - 體驗代碼生成功能

2. **進階功能** (1小時)
   - 使用項目分析功能
   - 嘗試自主任務執行
   - 體驗錯誤檢測和修復

3. **協作功能** (30分鐘)
   - 創建和分享會話
   - 邀請團隊成員協作
   - 使用會話回放功能

4. **高級定制** (按需)
   - 配置自定義設定
   - 開發自定義組件
   - 集成到現有工作流

### 最佳實踐
- 🔑 **定期備份**: 重要配置和會話數據
- 🔄 **保持更新**: 追蹤新版本發布
- 🛡️ **安全意識**: 妥善管理API密鑰
- 📊 **監控性能**: 關注系統資源使用

---

**享受使用 PowerAutomation v4.5！讓我們一起重新定義AI編程的未來！** 🚀

*如有任何問題，歡迎透過GitHub Issues聯繫我們。*