#!/bin/bash

# PowerAutomation v4.6.1 macOS 安裝腳本
# 發布日期：2025年7月11日
# 支持平台：macOS 12.0+ (Intel & Apple Silicon)

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# 版本信息
VERSION="v4.6.1"
RELEASE_DATE="2025-07-11"
GITHUB_REPO="alexchuang650730/aicore0711"
DOWNLOAD_BASE="https://github.com/${GITHUB_REPO}/releases/download/${VERSION}"

# 安裝路徑
INSTALL_DIR="/Applications/PowerAutomation.app"
CONFIG_DIR="$HOME/.powerautomation"
BIN_DIR="/usr/local/bin"
TEMP_DIR="/tmp/powerautomation_install"

# 輸出函數
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

header() {
    echo -e "${PURPLE}========================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}========================================${NC}"
}

# 檢查系統環境
check_system() {
    header "檢查系統環境"
    
    # 檢查macOS版本
    macos_version=$(sw_vers -productVersion)
    log "檢測到macOS版本: $macos_version"
    
    # 檢查最低版本要求 (macOS 12.0)
    if ! printf '%s\n' "$macos_version" "12.0" | sort -C -V; then
        error "需要macOS 12.0或更高版本，當前版本: $macos_version"
        exit 1
    fi
    
    # 檢查處理器類型
    arch=$(uname -m)
    log "檢測到處理器架構: $arch"
    
    # 檢查可用空間
    available_space=$(df -h . | tail -1 | awk '{print $4}' | sed 's/G//')
    log "可用儲存空間: ${available_space}GB"
    
    if [ "${available_space%.*}" -lt 2 ]; then
        error "需要至少2GB可用空間，當前可用: ${available_space}GB"
        exit 1
    fi
    
    # 檢查網絡連接
    if ! ping -c 1 github.com > /dev/null 2>&1; then
        error "無法連接到GitHub，請檢查網絡連接"
        exit 1
    fi
    
    success "系統環境檢查通過"
}

# 檢查權限
check_permissions() {
    header "檢查安裝權限"
    
    # 檢查是否有寫入Applications目錄的權限
    if [ ! -w "/Applications" ]; then
        warn "需要管理員權限安裝到Applications目錄"
        if ! sudo -n true 2>/dev/null; then
            log "請輸入管理員密碼以繼續安裝..."
            sudo -v
        fi
    fi
    
    success "權限檢查完成"
}

# 創建目錄結構
create_directories() {
    header "創建目錄結構"
    
    # 創建臨時目錄
    mkdir -p "$TEMP_DIR"
    log "創建臨時目錄: $TEMP_DIR"
    
    # 創建配置目錄
    mkdir -p "$CONFIG_DIR"/{config,logs,data,sessions,recordings,interfaces}
    log "創建配置目錄: $CONFIG_DIR"
    
    success "目錄結構創建完成"
}

# 下載安裝包
download_package() {
    header "下載PowerAutomation v4.6.1"
    
    cd "$TEMP_DIR"
    
    # 根據架構選擇下載包
    if [ "$arch" = "arm64" ]; then
        package_name="PowerAutomation-v4.6.1-macOS-arm64.dmg"
    else
        package_name="PowerAutomation-v4.6.1-macOS-x64.dmg"
    fi
    
    download_url="${DOWNLOAD_BASE}/${package_name}"
    log "下載地址: $download_url"
    
    # 下載安裝包
    if command -v curl > /dev/null; then
        curl -L -o "$package_name" "$download_url"
    elif command -v wget > /dev/null; then
        wget -O "$package_name" "$download_url"
    else
        error "未找到curl或wget，無法下載安裝包"
        exit 1
    fi
    
    # 驗證下載
    if [ ! -f "$package_name" ]; then
        error "下載失敗: $package_name"
        exit 1
    fi
    
    log "下載完成: $package_name"
    success "安裝包下載完成"
}

# 安裝應用程序
install_app() {
    header "安裝PowerAutomation應用程序"
    
    cd "$TEMP_DIR"
    
    # 掛載DMG
    log "掛載安裝映像..."
    hdiutil attach "$package_name" -quiet
    
    # 查找掛載點
    mount_point=$(hdiutil info | grep "PowerAutomation v4.6.1" | awk '{print $3}')
    if [ -z "$mount_point" ]; then
        error "無法找到掛載點"
        exit 1
    fi
    
    log "掛載點: $mount_point"
    
    # 刪除舊版本
    if [ -d "$INSTALL_DIR" ]; then
        log "刪除舊版本..."
        sudo rm -rf "$INSTALL_DIR"
    fi
    
    # 複製應用程序
    log "複製應用程序到Applications目錄..."
    sudo cp -R "$mount_point/PowerAutomation.app" "/Applications/"
    
    # 設置權限
    sudo chown -R "$(whoami):admin" "$INSTALL_DIR"
    sudo chmod -R 755 "$INSTALL_DIR"
    
    # 卸載DMG
    log "卸載安裝映像..."
    hdiutil detach "$mount_point" -quiet
    
    success "應用程序安裝完成"
}

# 創建命令行工具
create_cli_tool() {
    header "創建命令行工具"
    
    # 創建powerautomation命令
    cat > "$TEMP_DIR/powerautomation" << 'EOF'
#!/bin/bash

# PowerAutomation v4.6.1 命令行工具
# 自動生成於安裝時

POWERAUTOMATION_APP="/Applications/PowerAutomation.app"
POWERAUTOMATION_CLI="$POWERAUTOMATION_APP/Contents/MacOS/powerautomation"

# 檢查應用程序是否存在
if [ ! -f "$POWERAUTOMATION_CLI" ]; then
    echo "錯誤: PowerAutomation未正確安裝"
    echo "請重新安裝PowerAutomation"
    exit 1
fi

# 設置環境變量
export POWERAUTOMATION_HOME="$HOME/.powerautomation"
export POWERAUTOMATION_VERSION="v4.6.1"

# 執行命令
exec "$POWERAUTOMATION_CLI" "$@"
EOF
    
    # 安裝命令行工具
    sudo cp "$TEMP_DIR/powerautomation" "$BIN_DIR/"
    sudo chmod +x "$BIN_DIR/powerautomation"
    
    success "命令行工具創建完成"
}

# 初始化配置
initialize_config() {
    header "初始化配置文件"
    
    # 創建主配置文件
    cat > "$CONFIG_DIR/config/main.yaml" << EOF
# PowerAutomation v4.6.1 主配置文件
# 自動生成於 $(date)

version: "4.6.1"
installation_date: "$(date -Iseconds)"

# 基本配置
app:
  name: "PowerAutomation"
  version: "v4.6.1"
  log_level: "INFO"
  debug: false

# Claude API配置
claude:
  api_key: ""  # 請在此設置您的Claude API密鑰
  model: "claude-3-sonnet-20240229"
  max_tokens: 4000
  temperature: 0.7

# 服務器配置
server:
  host: "localhost"
  port: 8080
  auto_start: true

# ClaudEditor配置
claudeditor:
  ui_port: 5173
  api_port: 8082
  session_port: 8083
  three_column_layout: true
  theme: "dark"

# MCP生態系統配置
mcp:
  auto_start: true
  coordinator_enabled: true
  health_check_interval: 30
  max_parallel_components: 10
  
# 啟用的MCP組件
enabled_components:
  - test_mcp
  - stagewise_mcp
  - ag_ui_mcp
  - claude_mcp
  - security_mcp
  - zen_mcp
  - trae_agent_mcp
  - collaboration_mcp

# 日誌配置
logging:
  level: "INFO"
  file_rotation: true
  max_size: "100MB"
  backup_count: 10
EOF
    
    # 創建MCP生態系統配置
    cat > "$CONFIG_DIR/config/mcp_ecosystem.yaml" << EOF
# MCP生態系統配置
# PowerAutomation v4.6.1

coordinator:
  enabled: true
  port: 8090
  health_check_interval: 30

components:
  test_mcp:
    enabled: true
    port: 8091
    auto_start: true
    dependencies: []
    
  stagewise_mcp:
    enabled: true
    port: 8092
    auto_start: true
    dependencies: []
    
  ag_ui_mcp:
    enabled: true
    port: 8093
    auto_start: true
    dependencies: []
    
  claude_mcp:
    enabled: true
    port: 8094
    auto_start: true
    dependencies: []
    
  security_mcp:
    enabled: true
    port: 8095
    auto_start: true
    dependencies: []
EOF
    
    # 創建ClaudEditor配置
    cat > "$CONFIG_DIR/config/claudeditor.yaml" << EOF
# ClaudEditor配置
# PowerAutomation v4.6.1

ui:
  port: 5173
  host: "localhost"
  three_column_layout: true
  theme: "dark"
  auto_save: true
  
api:
  port: 8082
  host: "localhost"
  cors_enabled: true
  
session:
  port: 8083
  host: "localhost"
  timeout: 3600
  
ai_assistant:
  enabled: true
  model: "claude-3-sonnet-20240229"
  autonomous_mode: true
  context_window: 200000
  
project_management:
  enabled: true
  auto_analysis: true
  git_integration: true
  
collaboration:
  enabled: true
  real_time_sync: true
  session_sharing: true
EOF
    
    success "配置文件初始化完成"
}

# 驗證安裝
verify_installation() {
    header "驗證安裝"
    
    # 檢查應用程序
    if [ -d "$INSTALL_DIR" ]; then
        log "✓ 應用程序安裝成功"
    else
        error "✗ 應用程序安裝失敗"
        exit 1
    fi
    
    # 檢查命令行工具
    if [ -f "$BIN_DIR/powerautomation" ]; then
        log "✓ 命令行工具安裝成功"
    else
        error "✗ 命令行工具安裝失敗"
        exit 1
    fi
    
    # 檢查配置目錄
    if [ -d "$CONFIG_DIR" ]; then
        log "✓ 配置目錄創建成功"
    else
        error "✗ 配置目錄創建失敗"
        exit 1
    fi
    
    # 測試命令行工具
    if powerautomation --version > /dev/null 2>&1; then
        log "✓ 命令行工具測試成功"
    else
        warn "⚠ 命令行工具測試失敗（可能需要重新啟動終端）"
    fi
    
    success "安裝驗證完成"
}

# 清理臨時文件
cleanup() {
    header "清理臨時文件"
    
    if [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
        log "臨時文件清理完成"
    fi
    
    success "清理完成"
}

# 顯示安裝完成信息
show_completion() {
    header "PowerAutomation v4.6.1 安裝完成！"
    
    echo
    echo -e "${GREEN}🎉 恭喜！PowerAutomation v4.6.1 已成功安裝到您的Mac上${NC}"
    echo
    echo -e "${BLUE}📍 安裝位置：${NC}"
    echo -e "   應用程序：$INSTALL_DIR"
    echo -e "   配置目錄：$CONFIG_DIR"
    echo -e "   命令行工具：$BIN_DIR/powerautomation"
    echo
    echo -e "${BLUE}🚀 快速開始：${NC}"
    echo -e "   1. 設置Claude API密鑰："
    echo -e "      ${YELLOW}powerautomation config set claude.api_key \"your-api-key\"${NC}"
    echo
    echo -e "   2. 啟動應用程序："
    echo -e "      ${YELLOW}powerautomation start${NC}"
    echo -e "      或從Applications目錄啟動PowerAutomation.app"
    echo
    echo -e "   3. 初始化MCP生態系統："
    echo -e "      ${YELLOW}powerautomation mcp init-all${NC}"
    echo
    echo -e "   4. 啟動ClaudEditor："
    echo -e "      ${YELLOW}powerautomation claudeditor${NC}"
    echo
    echo -e "${BLUE}📚 更多信息：${NC}"
    echo -e "   安裝指南：https://github.com/$GITHUB_REPO/wiki/Installation-Guide"
    echo -e "   用戶手冊：https://github.com/$GITHUB_REPO/wiki/User-Manual"
    echo -e "   問題報告：https://github.com/$GITHUB_REPO/issues"
    echo
    echo -e "${GREEN}感謝使用PowerAutomation v4.6.1！${NC}"
    echo -e "${GREEN}開始您的AI驅動開發之旅吧！${NC}"
    echo
}

# 主安裝流程
main() {
    clear
    header "PowerAutomation v4.6.1 macOS 安裝器"
    echo -e "${BLUE}版本：${NC}$VERSION"
    echo -e "${BLUE}發布日期：${NC}$RELEASE_DATE"
    echo -e "${BLUE}目標平台：${NC}macOS 12.0+ (Intel & Apple Silicon)"
    echo
    
    # 詢問用戶確認
    read -p "$(echo -e ${YELLOW}是否繼續安裝？[y/N]: ${NC})" -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "安裝已取消"
        exit 0
    fi
    
    # 執行安裝步驟
    check_system
    check_permissions
    create_directories
    download_package
    install_app
    create_cli_tool
    initialize_config
    verify_installation
    cleanup
    show_completion
    
    # 詢問是否立即啟動
    echo
    read -p "$(echo -e ${YELLOW}是否立即啟動PowerAutomation？[y/N]: ${NC})" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "啟動PowerAutomation..."
        open "$INSTALL_DIR"
    fi
}

# 錯誤處理
trap 'error "安裝過程中發生錯誤，正在清理..."; cleanup; exit 1' ERR

# 執行主函數
main "$@"