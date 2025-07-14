#!/bin/bash

# PowerAutomation v4.6.1 macOS 打包腳本
# 用於創建DMG安裝包

set -e

# 配置變量
VERSION="v4.6.1"
APP_NAME="PowerAutomation"
DMG_NAME="PowerAutomation-${VERSION}-macOS"
BUILD_DIR="./build"
PACKAGE_DIR="./package_template"
SOURCE_DIR="../../../.."  # 指向項目根目錄

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# 清理舊的構建文件
cleanup() {
    header "清理構建環境"
    
    if [ -d "$BUILD_DIR" ]; then
        rm -rf "$BUILD_DIR"
        log "清理舊的構建目錄"
    fi
    
    if [ -f "${DMG_NAME}.dmg" ]; then
        rm -f "${DMG_NAME}.dmg"
        log "清理舊的DMG文件"
    fi
}

# 創建應用程序包結構
create_app_bundle() {
    header "創建應用程序包結構"
    
    # 創建.app目錄結構
    mkdir -p "$BUILD_DIR/${APP_NAME}.app/Contents"/{MacOS,Resources,Frameworks}
    
    # 創建Info.plist
    cat > "$BUILD_DIR/${APP_NAME}.app/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>powerautomation</string>
    <key>CFBundleIconFile</key>
    <string>icon.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.powerautomation.app</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>PowerAutomation</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>4.6.1</string>
    <key>CFBundleVersion</key>
    <string>4.6.1</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
    <key>CFBundleSupportedPlatforms</key>
    <array>
        <string>MacOSX</string>
    </array>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.developer-tools</string>
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <true/>
    </dict>
    <key>NSMicrophoneUsageDescription</key>
    <string>PowerAutomation需要麥克風權限用於語音輸入功能</string>
    <key>NSCameraUsageDescription</key>
    <string>PowerAutomation需要攝像頭權限用於視覺測試功能</string>
</dict>
</plist>
EOF
    
    log "創建Info.plist完成"
}

# 複製核心文件
copy_core_files() {
    header "複製核心文件"
    
    # 複製主執行文件
    mkdir -p "$BUILD_DIR/${APP_NAME}.app/Contents/MacOS"
    
    # 創建主執行腳本
    cat > "$BUILD_DIR/${APP_NAME}.app/Contents/MacOS/powerautomation" << 'EOF'
#!/bin/bash

# PowerAutomation v4.6.1 主執行腳本

# 獲取應用程序目錄
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESOURCES_DIR="$APP_DIR/Resources"

# 設置環境變量
export POWERAUTOMATION_HOME="$HOME/.powerautomation"
export POWERAUTOMATION_APP_DIR="$APP_DIR"
export POWERAUTOMATION_VERSION="v4.6.1"
export PYTHONPATH="$RESOURCES_DIR/core:$PYTHONPATH"

# 創建配置目錄（如果不存在）
mkdir -p "$POWERAUTOMATION_HOME"/{config,logs,data,sessions,recordings,interfaces}

# 檢查Python
if ! command -v python3 &> /dev/null; then
    osascript -e 'display dialog "PowerAutomation需要Python 3.8或更高版本。請安裝Python後重試。" buttons {"確定"} default button "確定"'
    exit 1
fi

# 安裝依賴（如果需要）
if [ ! -f "$POWERAUTOMATION_HOME/.deps_installed" ]; then
    echo "正在安裝依賴..."
    python3 -m pip install -r "$RESOURCES_DIR/requirements.txt" --user
    touch "$POWERAUTOMATION_HOME/.deps_installed"
fi

# 根據參數決定啟動方式
if [ "$1" = "--gui" ] || [ $# -eq 0 ]; then
    # 啟動GUI模式
    cd "$RESOURCES_DIR"
    python3 -m powerautomation_main --gui
else
    # 命令行模式
    cd "$RESOURCES_DIR"
    python3 -m powerautomation_main "$@"
fi
EOF
    
    chmod +x "$BUILD_DIR/${APP_NAME}.app/Contents/MacOS/powerautomation"
    log "創建主執行腳本完成"
}

# 複製資源文件
copy_resources() {
    header "複製資源文件"
    
    # 複製核心代碼
    cp -r "$SOURCE_DIR/core" "$BUILD_DIR/${APP_NAME}.app/Contents/Resources/"
    log "複製core目錄完成"
    
    # 複製ClaudEditor
    cp -r "$SOURCE_DIR/claudeditor" "$BUILD_DIR/${APP_NAME}.app/Contents/Resources/"
    log "複製claudeditor目錄完成"
    
    # 複製配置文件
    mkdir -p "$BUILD_DIR/${APP_NAME}.app/Contents/Resources/config"
    cp -r "$SOURCE_DIR/config"/* "$BUILD_DIR/${APP_NAME}.app/Contents/Resources/config/" 2>/dev/null || true
    log "複製配置文件完成"
    
    # 創建requirements.txt
    cat > "$BUILD_DIR/${APP_NAME}.app/Contents/Resources/requirements.txt" << EOF
# PowerAutomation v4.6.1 依賴
fastapi>=0.100.0
uvicorn>=0.22.0
websockets>=11.0
aiofiles>=23.0
pydantic>=2.0
jinja2>=3.1.0
python-multipart>=0.0.6
selenium>=4.11.0
playwright>=1.36.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
requests>=2.31.0
pyyaml>=6.0
python-dotenv>=1.0.0
psutil>=5.9.0
httpx>=0.24.0
asyncio-mqtt>=0.13.0
anthropic>=0.3.0
openai>=0.27.0
langchain>=0.0.200
streamlit>=1.25.0
gradio>=3.35.0
EOF
    
    log "創建requirements.txt完成"
}

# 創建圖標
create_icon() {
    header "創建應用程序圖標"
    
    # 創建臨時PNG圖標（實際項目中應該有真實的圖標文件）
    if command -v sips &> /dev/null; then
        # 創建一個簡單的圖標佔位符
        mkdir -p /tmp/icon.iconset
        
        # 生成不同尺寸的圖標（這裡使用系統圖標作為佔位符）
        for size in 16 32 128 256 512; do
            sips -z $size $size /System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/KEXT.icns --out "/tmp/icon.iconset/icon_${size}x${size}.png" 2>/dev/null || true
        done
        
        # 生成@2x版本
        for size in 16 32 128 256; do
            double_size=$((size * 2))
            sips -z $double_size $double_size /System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/KEXT.icns --out "/tmp/icon.iconset/icon_${size}x${size}@2x.png" 2>/dev/null || true
        done
        
        # 創建.icns文件
        iconutil -c icns /tmp/icon.iconset -o "$BUILD_DIR/${APP_NAME}.app/Contents/Resources/icon.icns" 2>/dev/null || true
        
        # 清理臨時文件
        rm -rf /tmp/icon.iconset
        
        log "創建應用程序圖標完成"
    else
        warn "未找到sips工具，跳過圖標創建"
    fi
}

# 設置權限
set_permissions() {
    header "設置文件權限"
    
    # 設置執行權限
    chmod +x "$BUILD_DIR/${APP_NAME}.app/Contents/MacOS/powerautomation"
    
    # 設置資源權限
    find "$BUILD_DIR/${APP_NAME}.app/Contents/Resources" -name "*.py" -exec chmod 644 {} \;
    find "$BUILD_DIR/${APP_NAME}.app/Contents/Resources" -name "*.sh" -exec chmod 755 {} \;
    
    log "文件權限設置完成"
}

# 創建DMG
create_dmg() {
    header "創建DMG安裝包"
    
    # 創建臨時DMG目錄
    DMG_TEMP_DIR="/tmp/${APP_NAME}_dmg"
    rm -rf "$DMG_TEMP_DIR"
    mkdir -p "$DMG_TEMP_DIR"
    
    # 複製.app到臨時目錄
    cp -R "$BUILD_DIR/${APP_NAME}.app" "$DMG_TEMP_DIR/"
    
    # 創建Applications快捷方式
    ln -s "/Applications" "$DMG_TEMP_DIR/Applications"
    
    # 創建README
    cat > "$DMG_TEMP_DIR/README.txt" << EOF
PowerAutomation v4.6.1 for macOS

安裝說明：
1. 將PowerAutomation.app拖拽到Applications文件夾
2. 首次運行時，系統可能要求您確認打開來源不明的應用程序
3. 在系統偏好設置 > 安全性與隱私中點擊"仍要打開"

更多信息：
- 官方網站：https://github.com/alexchuang650730/aicore0711
- 安裝指南：https://github.com/alexchuang650730/aicore0711/wiki
- 問題報告：https://github.com/alexchuang650730/aicore0711/issues

感謝使用PowerAutomation！
EOF
    
    # 創建DMG
    hdiutil create -srcfolder "$DMG_TEMP_DIR" \
                   -volname "PowerAutomation v4.6.1" \
                   -ov -format UDZO \
                   "${DMG_NAME}.dmg"
    
    # 清理臨時目錄
    rm -rf "$DMG_TEMP_DIR"
    
    log "DMG創建完成: ${DMG_NAME}.dmg"
}

# 驗證包
verify_package() {
    header "驗證安裝包"
    
    # 檢查DMG文件
    if [ -f "${DMG_NAME}.dmg" ]; then
        dmg_size=$(du -h "${DMG_NAME}.dmg" | cut -f1)
        log "✓ DMG文件: ${DMG_NAME}.dmg (${dmg_size})"
    else
        error "✗ DMG文件未找到"
        exit 1
    fi
    
    # 檢查.app結構
    if [ -d "$BUILD_DIR/${APP_NAME}.app" ]; then
        log "✓ 應用程序包結構完整"
    else
        error "✗ 應用程序包結構不完整"
        exit 1
    fi
    
    # 檢查關鍵文件
    key_files=(
        "$BUILD_DIR/${APP_NAME}.app/Contents/Info.plist"
        "$BUILD_DIR/${APP_NAME}.app/Contents/MacOS/powerautomation"
        "$BUILD_DIR/${APP_NAME}.app/Contents/Resources/core"
        "$BUILD_DIR/${APP_NAME}.app/Contents/Resources/claudeditor"
    )
    
    for file in "${key_files[@]}"; do
        if [ -e "$file" ]; then
            log "✓ $(basename "$file")"
        else
            error "✗ $(basename "$file") 缺失"
            exit 1
        fi
    done
    
    log "包驗證完成"
}

# 生成校驗碼
generate_checksums() {
    header "生成校驗碼"
    
    # 生成SHA256校驗碼
    if command -v shasum &> /dev/null; then
        shasum -a 256 "${DMG_NAME}.dmg" > "${DMG_NAME}.dmg.sha256"
        log "SHA256校驗碼: $(cat "${DMG_NAME}.dmg.sha256")"
    fi
    
    # 生成MD5校驗碼
    if command -v md5 &> /dev/null; then
        md5 "${DMG_NAME}.dmg" > "${DMG_NAME}.dmg.md5"
        log "MD5校驗碼已生成"
    fi
}

# 顯示完成信息
show_completion() {
    header "打包完成"
    
    echo
    echo -e "${GREEN}🎉 PowerAutomation v4.6.1 macOS安裝包已成功創建！${NC}"
    echo
    echo -e "${BLUE}📦 生成的文件：${NC}"
    echo -e "   • ${DMG_NAME}.dmg"
    echo -e "   • ${DMG_NAME}.dmg.sha256"
    echo -e "   • ${DMG_NAME}.dmg.md5"
    echo
    echo -e "${BLUE}📊 包信息：${NC}"
    if [ -f "${DMG_NAME}.dmg" ]; then
        dmg_size=$(du -h "${DMG_NAME}.dmg" | cut -f1)
        echo -e "   • 文件大小: ${dmg_size}"
    fi
    echo -e "   • 支持平台: macOS 12.0+"
    echo -e "   • 架構: Universal (Intel + Apple Silicon)"
    echo
    echo -e "${BLUE}🚀 下一步：${NC}"
    echo -e "   1. 測試安裝包: 雙擊 ${DMG_NAME}.dmg"
    echo -e "   2. 上傳到GitHub Releases"
    echo -e "   3. 更新Homebrew formula"
    echo -e "   4. 發布Release Notes"
    echo
}

# 主函數
main() {
    cd "$(dirname "$0")"
    
    header "PowerAutomation v4.6.1 macOS 打包器"
    echo -e "${BLUE}目標版本：${NC}${VERSION}"
    echo -e "${BLUE}應用程序名：${NC}${APP_NAME}"
    echo -e "${BLUE}輸出文件：${NC}${DMG_NAME}.dmg"
    echo
    
    # 檢查必要工具
    if ! command -v hdiutil &> /dev/null; then
        error "需要hdiutil工具來創建DMG"
        exit 1
    fi
    
    # 執行打包步驟
    cleanup
    create_app_bundle
    copy_core_files
    copy_resources
    create_icon
    set_permissions
    create_dmg
    verify_package
    generate_checksums
    show_completion
}

# 錯誤處理
trap 'error "打包過程中發生錯誤"; exit 1' ERR

# 執行主函數
main "$@"