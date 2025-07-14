# PowerAutomation v4.6.1 macOS 自動部署系統

## 🚀 概述

PowerAutomation v4.6.1 macOS自動部署系統提供一鍵式部署、測試和驗證功能，讓您輕鬆在macOS系統上安裝和運行PowerAutomation。

## ✨ 功能特性

- **🔄 全自動部署**: 一鍵完成從下載到配置的全部過程
- **🧪 自動測試**: 自動運行測試套件驗證安裝結果
- **📊 智能報告**: 生成詳細的部署和測試報告
- **⚡ 快速啟動**: 自動創建啟動腳本和環境配置
- **🔒 安全驗證**: 系統需求檢查和權限驗證

## 📋 系統需求

- **操作系統**: macOS 10.14+ (推薦 macOS 11+)
- **Python版本**: Python 3.8+ (推薦 Python 3.9+)
- **磁盤空間**: 至少1GB可用空間
- **權限**: 用戶目錄寫入權限

## 🛠️ 安裝步驟

### 方法1: 直接下載執行

```bash
# 下載部署腳本
curl -O https://raw.githubusercontent.com/alexchuang650730/aicore0711/main/deployment/devices/mac/v4.6.1/deploy_mac_auto.py

# 運行自動部署
python3 deploy_mac_auto.py
```

### 方法2: 克隆倉庫

```bash
# 克隆完整倉庫
git clone https://github.com/alexchuang650730/aicore0711.git

# 進入部署目錄
cd aicore0711/deployment/devices/mac/v4.6.1

# 運行部署腳本
python3 deploy_mac_auto.py
```

## 📊 部署過程

部署腳本會自動執行以下步驟：

### 1. 🔍 系統檢查
- 驗證macOS版本
- 檢查Python版本
- 確認磁盤空間
- 驗證用戶權限

### 2. 📁 環境準備
- 創建安裝目錄 (`~/PowerAutomation`)
- 備份現有版本（如果存在）
- 設置目錄結構

### 3. 📋 文件部署
- 複製核心組件
- 安裝必要文件
- 配置環境變量

### 4. ⚙️ 系統配置
- 生成配置文件
- 創建啟動腳本
- 設置自動啟動（可選）

### 5. 🧪 自動測試
- 部署驗證測試
- 發布就緒測試
- 最終發布測試
- 集成測試

### 6. 📊 報告生成
- 詳細測試報告
- 部署狀態總結
- 故障排除建議

## 🎯 測試結果

部署完成後，系統會自動運行測試套件：

- **部署測試**: 驗證文件和權限
- **發布就緒測試**: 核心功能驗證
- **最終發布測試**: 完整系統測試
- **集成測試**: 組件互操作性測試

## 📍 安裝位置

默認安裝路徑：`/Users/[用戶名]/PowerAutomation`

目錄結構：
```
PowerAutomation/
├── core/                    # 核心組件
├── claudeditor/            # ClaudEditor組件
├── cli/                    # 命令行界面
├── config/                 # 配置文件
├── logs/                   # 日誌文件
├── reports/                # 測試報告
├── launch_powerautomation.sh  # 啟動腳本
└── run_tests.sh           # 測試腳本
```

## 🚀 啟動方式

部署完成後，可以通過以下方式啟動：

### 命令行啟動
```bash
~/PowerAutomation/launch_powerautomation.sh
```

### 手動測試
```bash
~/PowerAutomation/run_tests.sh
```

### Python直接啟動
```bash
cd ~/PowerAutomation
python3 -c "import sys; sys.path.append('.'); print('PowerAutomation v4.6.1 Ready!')"
```

## 📊 測試報告示例

部署完成後會生成詳細測試報告，包含：

- 系統基本信息
- 部署執行結果  
- 詳細測試結果
- 性能指標統計
- 故障排除建議

## 🔧 故障排除

### 常見問題

1. **權限錯誤**
   ```bash
   chmod +x deploy_mac_auto.py
   ```

2. **Python版本問題**
   ```bash
   # 使用Homebrew安裝Python 3.9+
   brew install python@3.9
   ```

3. **磁盤空間不足**
   - 清理至少1GB空間
   - 檢查`~/Downloads`和垃圾桶

### 日誌查看

```bash
# 查看部署日誌
tail -f ~/PowerAutomation/logs/stdout.log

# 查看錯誤日誌  
tail -f ~/PowerAutomation/logs/stderr.log

# 查看部署腳本日誌
tail -f mac_deployment.log
```

## 🆘 技術支持

如遇到問題，請提供：

1. macOS版本：`sw_vers`
2. Python版本：`python3 --version`
3. 錯誤信息和日誌
4. 測試報告文件

**聯繫方式：**
- GitHub Issues: https://github.com/alexchuang650730/aicore0711/issues
- 技術支持: support@powerautomation.com

## 🎉 成功部署確認

部署成功的標誌：

✅ 部署腳本返回成功狀態  
✅ 啟動腳本運行正常  
✅ 測試報告顯示高通過率  
✅ PowerAutomation功能可正常使用  

## 📚 下一步

部署完成後，您可以：

1. **瀏覽功能**: 探索22個MCP組件
2. **配置AI助手**: 集成7大AI助手
3. **創建項目**: 開始AI輔助開發
4. **查看文檔**: 閱讀完整用戶指南
5. **加入社群**: 參與開發者社群

---

**PowerAutomation v4.6.1 - 重新定義企業級AI輔助開發平台** 🚀

*讓每個開發者都能享受AI帶來的效率革命*