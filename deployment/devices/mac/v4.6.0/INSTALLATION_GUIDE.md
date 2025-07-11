# PowerAutomation + ClaudEditor v4.6.0 Mac安裝指南

## 🚀 PowerAutomation v4.6.0 企業自動化平台 macOS安裝

### 📋 系統要求

#### 硬件要求
- **處理器**: Apple Silicon (M1/M2/M3) 或 Intel x64
- **內存**: 最少8GB RAM，推薦16GB+
- **存儲**: 至少5GB可用空間
- **網絡**: 寬帶互聯網連接

#### 軟件要求
- **操作系統**: macOS 12.0 (Monterey) 或更新版本
- **Python**: 3.11+ (自動安裝)
- **Node.js**: 18.0+ (自動安裝)
- **Git**: 2.30+ (可選，用於版本控制)

---

## 🔽 下載與安裝

### 方法1：直接下載 (推薦)

1. **下載安裝包**
   ```bash
   # 訪問GitHub Releases
   open https://github.com/alexchuang650730/aicore0711/releases/latest
   
   # 或直接下載
   curl -L -o PowerAutomation-v4.6.0.dmg \
     https://github.com/alexchuang650730/aicore0711/releases/download/v4.6.0/PowerAutomation-v4.6.0.dmg
   ```

2. **驗證校驗和**
   ```bash
   # 下載校驗和文件
   curl -L -o checksums.txt \
     https://github.com/alexchuang650730/aicore0711/releases/download/v4.6.0/checksums.txt
   
   # 驗證文件完整性
   shasum -c checksums.txt
   ```

3. **安裝應用程序**
   ```bash
   # 掛載DMG
   hdiutil attach PowerAutomation-v4.6.0.dmg
   
   # 複製到Applications文件夾
   cp -R "/Volumes/PowerAutomation v4.6.0/PowerAutomation.app" /Applications/
   
   # 卸載DMG
   hdiutil detach "/Volumes/PowerAutomation v4.6.0"
   ```

### 方法2：Homebrew安裝

```bash
# 添加我們的tap
brew tap alexchuang650730/powerautomation

# 安裝PowerAutomation
brew install --cask powerautomation

# 驗證安裝
powerautomation --version
```

### 方法3：從源碼構建

```bash
# 克隆倉庫
git clone https://github.com/alexchuang650730/aicore0711.git
cd aicore0711

# 切換到v4.6.0標籤
git checkout v4.6.0

# 安裝依賴
pip install -r requirements.txt
npm install

# 構建應用
make build-mac

# 安裝
make install
```

---

## ⚙️ 首次配置

### 1. 啟動應用程序

```bash
# 從Applications啟動
open -a PowerAutomation

# 或從命令行啟動
/Applications/PowerAutomation.app/Contents/MacOS/PowerAutomation
```

### 2. 完成初始設置

啟動後會自動打開設置向導：

1. **選擇安裝類型**
   - 個人專業版 (推薦個人開發者)
   - 團隊版 (小團隊協作)
   - 企業版 (企業級功能)

2. **配置工作區**
   ```bash
   # 設置默認工作區目錄
   PowerAutomation config set workspace.default ~/PowerAutomation
   
   # 創建工作區目錄
   mkdir -p ~/PowerAutomation/{projects,templates,exports}
   ```

3. **AI助手配置**
   ```bash
   # 配置Claude API
   PowerAutomation config set ai.provider claude
   PowerAutomation config set ai.model sonnet-4
   PowerAutomation config set ai.api_key YOUR_API_KEY
   ```

4. **MCP服務配置**
   ```bash
   # 啟用MCP組件
   PowerAutomation mcp enable test_mcp
   PowerAutomation mcp enable stagewise_mcp
   PowerAutomation mcp enable ag_ui_mcp
   PowerAutomation mcp enable claude_mcp
   PowerAutomation mcp enable security_mcp
   ```

### 3. 驗證安裝

```bash
# 檢查版本
PowerAutomation --version
# 輸出: PowerAutomation v4.6.0

# 檢查組件狀態
PowerAutomation status
# 應顯示所有MCP組件為healthy

# 運行快速測試
PowerAutomation test --quick
# 運行基本功能測試
```

---

## 🔧 高級配置

### 環境變量設置

```bash
# 添加到 ~/.zshrc 或 ~/.bash_profile
export POWERAUTOMATION_HOME="/Applications/PowerAutomation.app"
export POWERAUTOMATION_CONFIG="$HOME/.powerautomation"
export POWERAUTOMATION_WORKSPACE="$HOME/PowerAutomation"

# 添加到PATH
export PATH="$POWERAUTOMATION_HOME/Contents/MacOS:$PATH"

# 重新載入配置
source ~/.zshrc
```

### 配置文件

主配置文件位置：`~/.powerautomation/config.yaml`

```yaml
# PowerAutomation v4.6.0 配置
version: "4.6.0"
workspace:
  default: "~/PowerAutomation"
  auto_save: true
  backup_enabled: true

ai:
  provider: "claude"
  model: "sonnet-4"
  auto_complete: true
  code_generation: true

mcp:
  enabled_components:
    - test_mcp
    - stagewise_mcp
    - ag_ui_mcp
    - claude_mcp
    - security_mcp
  auto_start: true

ui:
  theme: "dark"
  three_column_layout: true
  font_size: 14

testing:
  auto_run: true
  parallel_execution: true
  coverage_threshold: 80

security:
  auto_scan: true
  compliance_check: true
  audit_logging: true
```

### ClaudEditor集成

```bash
# 啟用ClaudEditor UI
PowerAutomation ui enable claudeditor

# 配置三欄式布局
PowerAutomation ui config --layout three-column

# 設置編輯器主題
PowerAutomation ui theme dark
```

---

## 🛠️ 疑難排解

### 常見問題

#### 1. 應用程序無法啟動

**問題**: macOS Gatekeeper阻止應用啟動
```bash
# 解決方案：暫時解除Gatekeeper限制
sudo spctl --master-disable

# 運行應用程序一次後重新啟用
sudo spctl --master-enable
```

**問題**: "應用程序已損壞"錯誤
```bash
# 清除隔離屬性
sudo xattr -rd com.apple.quarantine /Applications/PowerAutomation.app
```

#### 2. 權限問題

```bash
# 修復應用程序權限
sudo chmod -R 755 /Applications/PowerAutomation.app

# 修復配置目錄權限
chmod -R 755 ~/.powerautomation
```

#### 3. MCP組件無法啟動

```bash
# 檢查MCP服務狀態
PowerAutomation mcp status

# 重啟MCP服務
PowerAutomation mcp restart

# 檢查日誌
tail -f ~/.powerautomation/logs/mcp.log
```

#### 4. AI助手連接失敗

```bash
# 檢查網絡連接
curl -I https://api.anthropic.com

# 驗證API密鑰
PowerAutomation ai test-connection

# 重置AI配置
PowerAutomation config reset ai
```

#### 5. 內存不足

```bash
# 檢查系統資源
PowerAutomation system-info

# 調整內存設置
PowerAutomation config set memory.limit 4GB
PowerAutomation config set memory.cleanup_threshold 80
```

### 日誌文件位置

- **主日誌**: `~/.powerautomation/logs/main.log`
- **MCP日誌**: `~/.powerautomation/logs/mcp.log`
- **UI日誌**: `~/.powerautomation/logs/ui.log`
- **測試日誌**: `~/.powerautomation/logs/test.log`

### 獲取支持

```bash
# 生成診斷報告
PowerAutomation diagnostic --export

# 檢查系統兼容性
PowerAutomation system-check

# 聯繫支持
open https://github.com/alexchuang650730/aicore0711/issues
```

---

## 🔄 卸載指南

### 完全卸載

```bash
# 1. 停止所有服務
PowerAutomation shutdown

# 2. 刪除應用程序
sudo rm -rf /Applications/PowerAutomation.app

# 3. 清理配置文件
rm -rf ~/.powerautomation

# 4. 清理緩存
rm -rf ~/Library/Caches/PowerAutomation

# 5. 清理偏好設置
rm -rf ~/Library/Preferences/com.powerautomation.*

# 6. 清理Homebrew安裝 (如果使用)
brew uninstall --cask powerautomation
brew untap alexchuang650730/powerautomation
```

---

## 📈 性能優化

### 系統優化建議

1. **內存設置**
   ```bash
   # 為PowerAutomation分配足夠內存
   PowerAutomation config set memory.max 8GB
   ```

2. **SSD優化**
   ```bash
   # 啟用SSD優化
   PowerAutomation config set storage.ssd_mode true
   ```

3. **網絡優化**
   ```bash
   # 配置CDN加速
   PowerAutomation config set network.cdn_enabled true
   ```

### 監控和維護

```bash
# 定期清理
PowerAutomation cleanup --cache --logs --temp

# 更新檢查
PowerAutomation update check

# 性能報告
PowerAutomation performance report
```

---

## 🚀 下一步

安裝完成後：

1. **查看快速開始指南**: `PowerAutomation help getting-started`
2. **觀看教學視頻**: `PowerAutomation tutorial`
3. **加入社區**: [GitHub Discussions](https://github.com/alexchuang650730/aicore0711/discussions)
4. **閱讀文檔**: [完整文檔](https://docs.powerautomation.com)

---

**PowerAutomation v4.6.0 - 企業級自動化平台，現已就緒！** 🎉

*本安裝指南適用於 PowerAutomation v4.6.0 macOS版本*