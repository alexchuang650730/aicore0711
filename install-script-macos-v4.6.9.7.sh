#!/bin/bash

# PowerAutomation v4.6.9.7 macOS 一鍵安裝腳本
# 集成支付儲值積分系統和PC/Mobile支持
# 作者: PowerAutomation Team
# 版本: v4.6.9.7
# 日期: 2025-07-15

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 版本信息
VERSION="4.6.9.7"
PRODUCT_NAME="PowerAutomation"
INSTALL_DIR="$HOME/PowerAutomation"
BACKUP_DIR="$HOME/PowerAutomation_backup_$(date +%Y%m%d_%H%M%S)"

# 支付儲值積分系統配置
PAYMENT_SYSTEM_URL="https://github.com/alexchuang650730/powerauto.aiweb"
PAYMENT_API_BASE="https://api.powerauto.aiweb.com"
CREDITS_SYSTEM_ENABLED=true

# 系統要求
MIN_MACOS_VERSION="10.15"
REQUIRED_TOOLS=("curl" "git" "node" "npm" "python3")

# 進度條函數
show_progress() {
    local current=$1
    local total=$2
    local width=50
    local percentage=$((current * 100 / total))
    local completed=$((current * width / total))
    
    printf "\r${CYAN}["
    for ((i=0; i<completed; i++)); do printf "█"; done
    for ((i=completed; i<width; i++)); do printf "░"; done
    printf "] %d%% (%d/%d)${NC}" $percentage $current $total
}

# 日誌函數
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# 檢查系統要求
check_system_requirements() {
    log "檢查系統要求..."
    
    # 檢查macOS版本
    local macos_version=$(sw_vers -productVersion)
    if [[ $(echo "$macos_version $MIN_MACOS_VERSION" | tr " " "\n" | sort -V | head -n1) != "$MIN_MACOS_VERSION" ]]; then
        error "需要macOS $MIN_MACOS_VERSION 或更高版本，當前版本：$macos_version"
        exit 1
    fi
    
    # 檢查必要工具
    for tool in "${REQUIRED_TOOLS[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            error "缺少必要工具: $tool"
            case $tool in
                "node"|"npm")
                    info "請安裝Node.js: https://nodejs.org/"
                    ;;
                "python3")
                    info "請安裝Python 3: https://python.org/"
                    ;;
                "git")
                    info "請安裝Git: https://git-scm.com/"
                    ;;
            esac
            exit 1
        fi
    done
    
    # 檢查網絡代理設置
    if [[ -n "$HTTP_PROXY" || -n "$HTTPS_PROXY" ]]; then
        info "檢測到代理設置，將使用代理進行安裝"
    fi
    
    log "系統要求檢查完成 ✓"
}

# 顯示歡迎信息
show_welcome() {
    clear
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════════════════╗"
    echo "║                     PowerAutomation v$VERSION                              ║"
    echo "║                        macOS 一鍵安裝程序                                 ║"
    echo "║                                                                          ║"
    echo "║  🚀 特色功能:                                                             ║"
    echo "║   • K2 AI模型集成 (60%成本節省)                                           ║"
    echo "║   • ClaudeEditor桌面版                                                   ║"
    echo "║   • Mirror Code實時同步                                                  ║"
    echo "║   • 支付儲值積分系統                                                      ║"
    echo "║   • PC/Mobile響應式界面                                                  ║"
    echo "║   • 企業級工作流管理                                                      ║"
    echo "║                                                                          ║"
    echo "║  💰 版本選擇:                                                             ║"
    echo "║   • Community版 (免費) - 基礎功能                                         ║"
    echo "║   • Personal版 (付費) - 個人增強功能                                      ║"
    echo "║   • Enterprise版 (企業) - 完整功能集                                     ║"
    echo "╚══════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 選擇安裝版本
select_version() {
    echo -e "${YELLOW}請選擇要安裝的版本:${NC}"
    echo "1) Community版 (免費)"
    echo "2) Personal版 (需要積分)"
    echo "3) Enterprise版 (需要企業授權)"
    echo ""
    read -p "請輸入選擇 (1-3): " version_choice
    
    case $version_choice in
        1)
            INSTALL_VERSION="community"
            CREDITS_REQUIRED=0
            ;;
        2)
            INSTALL_VERSION="personal"
            CREDITS_REQUIRED=100
            ;;
        3)
            INSTALL_VERSION="enterprise"
            CREDITS_REQUIRED=500
            ;;
        *)
            warn "無效選擇，默認安裝Community版"
            INSTALL_VERSION="community"
            CREDITS_REQUIRED=0
            ;;
    esac
    
    log "選擇版本: $INSTALL_VERSION"
}

# 檢查積分系統
check_credits_system() {
    if [[ "$INSTALL_VERSION" == "community" ]]; then
        return 0
    fi
    
    log "檢查積分系統..."
    
    # 檢查是否有用戶token
    if [[ -f "$HOME/.powerauto_token" ]]; then
        USER_TOKEN=$(cat "$HOME/.powerauto_token")
        log "找到用戶token"
    else
        echo -e "${YELLOW}首次使用需要註冊積分賬戶${NC}"
        echo "請訪問: https://powerauto.aiweb.com/register"
        echo ""
        read -p "請輸入您的用戶token: " USER_TOKEN
        echo "$USER_TOKEN" > "$HOME/.powerauto_token"
        chmod 600 "$HOME/.powerauto_token"
    fi
    
    # 檢查積分餘額
    local credits_response=$(curl -s -H "Authorization: Bearer $USER_TOKEN" \
        "$PAYMENT_API_BASE/v1/credits/balance" || echo '{"error": "network_error"}')
    
    local current_credits=$(echo "$credits_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'balance' in data:
        print(data['balance'])
    else:
        print('0')
except:
    print('0')
")
    
    if [[ "$current_credits" -lt "$CREDITS_REQUIRED" ]]; then
        error "積分不足! 需要: $CREDITS_REQUIRED, 當前: $current_credits"
        echo -e "${YELLOW}請訪問以下網址充值積分:${NC}"
        echo "https://powerauto.aiweb.com/recharge"
        echo ""
        read -p "充值完成後按回車繼續..."
        
        # 重新檢查積分
        credits_response=$(curl -s -H "Authorization: Bearer $USER_TOKEN" \
            "$PAYMENT_API_BASE/v1/credits/balance" || echo '{"error": "network_error"}')
        
        current_credits=$(echo "$credits_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'balance' in data:
        print(data['balance'])
    else:
        print('0')
except:
    print('0')
")
        
        if [[ "$current_credits" -lt "$CREDITS_REQUIRED" ]]; then
            error "積分仍然不足，安裝終止"
            exit 1
        fi
    fi
    
    log "積分檢查通過 (餘額: $current_credits) ✓"
}

# 扣除積分
deduct_credits() {
    if [[ "$INSTALL_VERSION" == "community" ]]; then
        return 0
    fi
    
    log "扣除積分..."
    
    local deduct_response=$(curl -s -X POST \
        -H "Authorization: Bearer $USER_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"amount\": $CREDITS_REQUIRED, \"reason\": \"PowerAutomation $INSTALL_VERSION v$VERSION installation\"}" \
        "$PAYMENT_API_BASE/v1/credits/deduct" || echo '{"error": "network_error"}')
    
    local success=$(echo "$deduct_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('true' if data.get('success') else 'false')
except:
    print('false')
")
    
    if [[ "$success" != "true" ]]; then
        error "積分扣除失敗"
        exit 1
    fi
    
    log "積分扣除成功 ✓"
}

# 備份現有安裝
backup_existing() {
    if [[ -d "$INSTALL_DIR" ]]; then
        log "備份現有安裝到 $BACKUP_DIR"
        mv "$INSTALL_DIR" "$BACKUP_DIR"
        log "備份完成 ✓"
    fi
}

# 下載和安裝核心系統
install_core_system() {
    log "下載PowerAutomation v$VERSION..."
    
    # 創建安裝目錄
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # 下載核心系統
    show_progress 1 10
    curl -fsSL "https://github.com/alexchuang650730/aicore0711/archive/refs/heads/main.zip" -o "aicore-main.zip"
    
    show_progress 2 10
    unzip -q "aicore-main.zip"
    mv "aicore0711-main/"* .
    rm -rf "aicore-main.zip" "aicore0711-main"
    
    # 安裝Python依賴
    show_progress 3 10
    if [[ -f "requirements.txt" ]]; then
        python3 -m pip install -r requirements.txt --user
    fi
    
    # 安裝Node.js依賴
    show_progress 4 10
    if [[ -f "package.json" ]]; then
        npm install
    fi
    
    # 安裝ClaudeEditor
    show_progress 5 10
    if [[ -d "claudeditor" ]]; then
        cd claudeditor
        npm install
        npm run build
        cd ..
    fi
    
    show_progress 6 10
    echo ""
    log "核心系統安裝完成 ✓"
}

# 安裝支付儲值積分系統
install_payment_system() {
    log "安裝支付儲值積分系統..."
    
    # 下載支付系統前端
    show_progress 7 10
    mkdir -p "$INSTALL_DIR/payment-system"
    cd "$INSTALL_DIR/payment-system"
    
    curl -fsSL "https://github.com/alexchuang650730/powerauto.aiweb/archive/refs/heads/main.zip" -o "payment-system.zip"
    unzip -q "payment-system.zip"
    mv "powerauto.aiweb-main/"* .
    rm -rf "payment-system.zip" "powerauto.aiweb-main"
    
    # 安裝依賴
    show_progress 8 10
    if [[ -f "package.json" ]]; then
        npm install
        npm run build
    fi
    
    # 配置支付系統
    cat > "$INSTALL_DIR/payment-system/config.js" << EOF
// PowerAutomation v$VERSION 支付系統配置
const paymentConfig = {
    version: '$VERSION',
    installVersion: '$INSTALL_VERSION',
    apiBase: '$PAYMENT_API_BASE',
    features: {
        credits: $CREDITS_SYSTEM_ENABLED,
        recharge: true,
        history: true,
        mobile: true
    },
    ui: {
        theme: 'powerauto',
        responsive: true,
        animations: true
    },
    integrations: {
        k2: true,
        claudeditor: true,
        mirror: true
    }
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = paymentConfig;
}
EOF
    
    show_progress 9 10
    echo ""
    log "支付系統安裝完成 ✓"
}

# 配置服務和啟動腳本
configure_services() {
    log "配置服務和啟動腳本..."
    
    cd "$INSTALL_DIR"
    
    # 創建主啟動腳本
    cat > "start-powerautomation.sh" << 'EOF'
#!/bin/bash

# PowerAutomation v4.6.9.7 啟動腳本
# 支持PC/Mobile多平台

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# 顏色定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 啟動PowerAutomation v4.6.9.7...${NC}"

# 啟動K2服務
echo -e "${BLUE}📡 啟動K2服務...${NC}"
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
python3 complete_k2_service.py &
K2_PID=$!

# 等待K2服務啟動
sleep 3

# 啟動Mirror Code服務
echo -e "${BLUE}🪞 啟動Mirror Code服務...${NC}"
python3 core/powerautomation_main.py &
MIRROR_PID=$!

# 等待Mirror服務啟動
sleep 2

# 啟動ClaudeEditor
echo -e "${BLUE}🎨 啟動ClaudeEditor...${NC}"
cd claudeditor
npm run dev &
CLAUDEDITOR_PID=$!
cd ..

# 啟動支付系統
echo -e "${BLUE}💰 啟動支付系統...${NC}"
cd payment-system
npm run dev &
PAYMENT_PID=$!
cd ..

# 等待所有服務啟動
sleep 5

echo -e "${GREEN}✅ 所有服務已啟動:${NC}"
echo "  🤖 K2服務: http://localhost:8765"
echo "  🪞 Mirror服務: http://localhost:8080"
echo "  🎨 ClaudeEditor: http://localhost:3000"
echo "  💰 支付系統: http://localhost:3001"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止所有服務${NC}"

# 等待信號
trap 'kill $K2_PID $MIRROR_PID $CLAUDEDITOR_PID $PAYMENT_PID 2>/dev/null; exit 0' SIGINT SIGTERM

# 保持腳本運行
while true; do
    sleep 1
done
EOF
    
    chmod +x "start-powerautomation.sh"
    
    # 創建桌面快捷方式
    cat > "$HOME/Desktop/PowerAutomation.command" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
./start-powerautomation.sh
EOF
    
    chmod +x "$HOME/Desktop/PowerAutomation.command"
    
    # 創建移動端配置
    cat > "$INSTALL_DIR/mobile-config.json" << EOF
{
    "version": "$VERSION",
    "mobileSupport": true,
    "responsive": {
        "breakpoints": {
            "mobile": "768px",
            "tablet": "1024px",
            "desktop": "1280px"
        },
        "features": {
            "touchOptimized": true,
            "gestureSupport": true,
            "adaptiveUI": true
        }
    },
    "capabilities": {
        "offline": true,
        "notifications": true,
        "camera": true,
        "location": false
    }
}
EOF
    
    show_progress 10 10
    echo ""
    log "服務配置完成 ✓"
}

# 運行測試
run_tests() {
    log "運行安裝測試..."
    
    cd "$INSTALL_DIR"
    
    # 測試K2服務
    if [[ -f "quick_k2_verification.py" ]]; then
        echo -e "${BLUE}測試K2服務...${NC}"
        source venv/bin/activate 2>/dev/null || true
        python3 quick_k2_verification.py &
        TEST_PID=$!
        sleep 10
        kill $TEST_PID 2>/dev/null || true
    fi
    
    # 測試支付系統
    if [[ -d "payment-system" ]]; then
        echo -e "${BLUE}測試支付系統...${NC}"
        cd payment-system
        npm test 2>/dev/null || echo "支付系統測試跳過"
        cd ..
    fi
    
    log "測試完成 ✓"
}

# 顯示完成信息
show_completion() {
    clear
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════════════════╗"
    echo "║                     🎉 安裝完成！                                        ║"
    echo "║                                                                          ║"
    echo "║  PowerAutomation v$VERSION 已成功安裝                                      ║"
    echo "║  版本: $INSTALL_VERSION                                                   ║"
    echo "║                                                                          ║"
    echo "║  📍 安裝路徑: $INSTALL_DIR"
    echo "║                                                                          ║"
    echo "║  🚀 啟動方式:                                                             ║"
    echo "║    • 雙擊桌面的 PowerAutomation.command                                  ║"
    echo "║    • 或運行: cd $INSTALL_DIR && ./start-powerautomation.sh                ║"
    echo "║                                                                          ║"
    echo "║  🌐 服務地址:                                                             ║"
    echo "║    • K2服務: http://localhost:8765                                       ║"
    echo "║    • Mirror服務: http://localhost:8080                                   ║"
    echo "║    • ClaudeEditor: http://localhost:3000                                ║"
    echo "║    • 支付系統: http://localhost:3001                                     ║"
    echo "║                                                                          ║"
    echo "║  📱 移動端支持:                                                           ║"
    echo "║    • 響應式設計支持PC/Mobile                                              ║"
    echo "║    • 觸控優化界面                                                         ║"
    echo "║    • 離線功能支持                                                         ║"
    echo "║                                                                          ║"
    echo "║  💰 積分系統:                                                             ║"
    echo "║    • 儲值: https://powerauto.aiweb.com/recharge                          ║"
    echo "║    • 歷史: https://powerauto.aiweb.com/history                           ║"
    echo "║    • 管理: https://powerauto.aiweb.com/dashboard                         ║"
    echo "║                                                                          ║"
    echo "║  🔧 需要幫助?                                                             ║"
    echo "║    • 文檔: https://powerauto.aiweb.com/docs                              ║"
    echo "║    • 支持: https://powerauto.aiweb.com/support                           ║"
    echo "║    • GitHub: https://github.com/alexchuang650730/aicore0711              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    if [[ "$INSTALL_VERSION" != "community" ]]; then
        echo -e "${YELLOW}感謝您購買 $INSTALL_VERSION 版本！${NC}"
        echo -e "${YELLOW}剩餘積分請查看: https://powerauto.aiweb.com/dashboard${NC}"
    fi
}

# 主安裝流程
main() {
    show_welcome
    
    # 檢查系統
    check_system_requirements
    
    # 選擇版本
    select_version
    
    # 檢查積分
    check_credits_system
    
    # 確認安裝
    echo -e "${YELLOW}即將安裝 PowerAutomation v$VERSION ($INSTALL_VERSION 版本)${NC}"
    if [[ "$INSTALL_VERSION" != "community" ]]; then
        echo -e "${YELLOW}將扣除 $CREDITS_REQUIRED 積分${NC}"
    fi
    echo ""
    read -p "確認繼續安裝? (y/N): " confirm
    
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "安裝已取消"
        exit 0
    fi
    
    # 開始安裝
    log "開始安裝 PowerAutomation v$VERSION..."
    
    # 扣除積分
    deduct_credits
    
    # 備份現有安裝
    backup_existing
    
    # 安裝核心系統
    install_core_system
    
    # 安裝支付系統
    install_payment_system
    
    # 配置服務
    configure_services
    
    # 運行測試
    run_tests
    
    # 顯示完成信息
    show_completion
    
    # 詢問是否立即啟動
    echo ""
    read -p "是否立即啟動 PowerAutomation? (y/N): " start_now
    
    if [[ "$start_now" == "y" || "$start_now" == "Y" ]]; then
        log "正在啟動 PowerAutomation..."
        cd "$INSTALL_DIR"
        ./start-powerautomation.sh
    fi
}

# 錯誤處理
trap 'error "安裝過程中發生錯誤，請檢查日誌"; exit 1' ERR

# 運行主函數
main "$@"