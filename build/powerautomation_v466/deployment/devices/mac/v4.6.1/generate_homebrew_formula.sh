#!/bin/bash

# Homebrew Formula 更新腳本
# PowerAutomation v4.6.1

set -e

# 配置
VERSION="v4.6.1"
GITHUB_REPO="alexchuang650730/aicore0711"
FORMULA_NAME="powerautomation"

# 顏色輸出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# 生成Homebrew Formula
generate_formula() {
    header "生成Homebrew Formula"
    
    cat > "${FORMULA_NAME}.rb" << EOF
class Powerautomation < Formula
  desc "PowerAutomation - AI-driven development platform with complete MCP ecosystem"
  homepage "https://github.com/${GITHUB_REPO}"
  version "${VERSION#v}"
  
  if Hardware::CPU.arm?
    url "https://github.com/${GITHUB_REPO}/releases/download/${VERSION}/PowerAutomation-${VERSION}-macOS-arm64.dmg"
    sha256 "ARM64_SHA256_PLACEHOLDER"
  else
    url "https://github.com/${GITHUB_REPO}/releases/download/${VERSION}/PowerAutomation-${VERSION}-macOS-x64.dmg"
    sha256 "X64_SHA256_PLACEHOLDER"
  end

  depends_on "python@3.11"
  depends_on macos: :monterey

  def install
    # 掛載DMG
    system "hdiutil", "attach", cached_download, "-quiet"
    
    # 查找掛載點
    mount_point = \`hdiutil info | grep "PowerAutomation #{version}" | awk '{print \$3}'\`.strip
    
    # 複製應用程序
    prefix.install "\#{mount_point}/PowerAutomation.app"
    
    # 卸載DMG
    system "hdiutil", "detach", mount_point, "-quiet"
    
    # 創建命令行工具
    (bin/"powerautomation").write <<~EOS
      #!/bin/bash
      
      # PowerAutomation #{version} 命令行工具
      
      POWERAUTOMATION_APP="#{prefix}/PowerAutomation.app"
      POWERAUTOMATION_CLI="\$POWERAUTOMATION_APP/Contents/MacOS/powerautomation"
      
      # 檢查應用程序是否存在
      if [ ! -f "\$POWERAUTOMATION_CLI" ]; then
          echo "錯誤: PowerAutomation未正確安裝"
          echo "請重新安裝PowerAutomation"
          exit 1
      fi
      
      # 設置環境變量
      export POWERAUTOMATION_HOME="\$HOME/.powerautomation"
      export POWERAUTOMATION_VERSION="#{version}"
      
      # 執行命令
      exec "\$POWERAUTOMATION_CLI" "\$@"
    EOS
    
    # 設置可執行權限
    chmod "+x", bin/"powerautomation"
    
    # 創建.app快捷方式
    (prefix/"bin").install_symlink prefix/"PowerAutomation.app/Contents/MacOS/powerautomation" => "powerautomation-gui"
  end

  def post_install
    # 創建配置目錄
    (var/"powerautomation").mkpath
    
    # 初始化配置
    system bin/"powerautomation", "config", "init" if which("powerautomation")
    
    ohai "PowerAutomation #{version} 已安裝完成！"
    ohai "使用 'powerautomation --help' 查看可用命令"
    ohai "使用 'powerautomation claudeditor' 啟動ClaudEditor"
    ohai "配置目錄: ~/.powerautomation"
  end

  test do
    # 測試命令行工具
    assert_match "PowerAutomation #{version}", shell_output("#{bin}/powerautomation --version")
    
    # 測試配置命令
    system bin/"powerautomation", "config", "validate"
    
    # 測試MCP狀態
    system bin/"powerautomation", "mcp", "status"
  end

  service do
    run [opt_bin/"powerautomation", "service", "start"]
    working_dir var/"powerautomation"
    log_path var/"log/powerautomation.log"
    error_log_path var/"log/powerautomation.error.log"
    environment_variables POWERAUTOMATION_HOME: var/"powerautomation"
  end
end
EOF
    
    log "Homebrew Formula 生成完成: ${FORMULA_NAME}.rb"
}

# 生成Tap Repository說明
generate_tap_readme() {
    header "生成Tap Repository說明"
    
    cat > "README.md" << EOF
# PowerAutomation Homebrew Tap

Official Homebrew tap for PowerAutomation - AI-driven development platform with complete MCP ecosystem.

## Installation

### Add the tap
\`\`\`bash
brew tap ${GITHUB_REPO%/*}/powerautomation
\`\`\`

### Install PowerAutomation
\`\`\`bash
brew install powerautomation
\`\`\`

### Upgrade PowerAutomation
\`\`\`bash
brew upgrade powerautomation
\`\`\`

## Usage

### Command Line Interface
\`\`\`bash
# Show version
powerautomation --version

# Show help
powerautomation --help

# Start ClaudEditor
powerautomation claudeditor

# Initialize MCP ecosystem
powerautomation mcp init-all

# Check MCP status
powerautomation mcp status
\`\`\`

### GUI Application
\`\`\`bash
# Start GUI mode
powerautomation --gui

# Or use the GUI launcher
powerautomation-gui
\`\`\`

## Configuration

PowerAutomation stores its configuration in \`~/.powerautomation/\`:

- \`config/\` - Configuration files
- \`logs/\` - Log files
- \`data/\` - Application data
- \`sessions/\` - Session recordings
- \`recordings/\` - Stagewise recordings
- \`interfaces/\` - AG-UI generated interfaces

## Features

### Complete MCP Ecosystem (22 Components)
- **Test MCP** - Unified testing management
- **Stagewise MCP** - UI recording and playback
- **AG-UI MCP** - Intelligent UI component generation
- **Claude MCP** - Claude API management
- **Security MCP** - Enterprise security management
- **Zen MCP** - Intelligent workflow orchestration
- **Trae Agent MCP** - Multi-agent collaboration
- And 15+ more specialized components

### ClaudEditor Three-Column UI
- **Left Column**: Project management and file browser
- **Middle Column**: Code editor with real-time preview
- **Right Column**: AI assistant and intelligent chat

### Enterprise Features
- **Autonomous Task Execution** - Complete complex tasks without guidance
- **Project-Level Code Understanding** - Full architecture awareness
- **5-10x Performance Advantage** - Local processing, <200ms response
- **Offline Capability** - Full offline development environment

## Requirements

- macOS 12.0 (Monterey) or later
- Python 3.11 or later
- 8GB RAM minimum (16GB recommended)
- 2GB available disk space

## Support

- **Documentation**: https://github.com/${GITHUB_REPO}/wiki
- **Issues**: https://github.com/${GITHUB_REPO}/issues
- **Discussions**: https://github.com/${GITHUB_REPO}/discussions

## License

See the [LICENSE](https://github.com/${GITHUB_REPO}/blob/main/LICENSE) file for details.
EOF
    
    log "Tap README 生成完成: README.md"
}

# 生成更新說明
generate_update_instructions() {
    header "生成更新說明"
    
    cat > "UPDATE_INSTRUCTIONS.md" << EOF
# PowerAutomation Homebrew Tap 更新說明

## 更新流程

### 1. 計算新版本的SHA256
\`\`\`bash
# 下載並計算SHA256
curl -L -s "https://github.com/${GITHUB_REPO}/releases/download/${VERSION}/PowerAutomation-${VERSION}-macOS-arm64.dmg" | shasum -a 256
curl -L -s "https://github.com/${GITHUB_REPO}/releases/download/${VERSION}/PowerAutomation-${VERSION}-macOS-x64.dmg" | shasum -a 256
\`\`\`

### 2. 更新Formula文件
編輯 \`${FORMULA_NAME}.rb\` 文件：
1. 更新版本號
2. 更新下載URL
3. 替換SHA256校驗碼

### 3. 測試Formula
\`\`\`bash
# 測試Formula語法
brew audit --strict ${FORMULA_NAME}

# 測試安裝
brew install --build-from-source ${FORMULA_NAME}

# 測試功能
powerautomation --version
powerautomation test system
\`\`\`

### 4. 提交更新
\`\`\`bash
git add ${FORMULA_NAME}.rb
git commit -m "Update PowerAutomation to ${VERSION}"
git push origin main
\`\`\`

## 自動化更新腳本

\`\`\`bash
#!/bin/bash

# PowerAutomation Homebrew Formula 自動更新腳本
VERSION="${VERSION}"
GITHUB_REPO="${GITHUB_REPO}"

# 計算SHA256
ARM64_SHA256=\$(curl -L -s "https://github.com/\${GITHUB_REPO}/releases/download/\${VERSION}/PowerAutomation-\${VERSION}-macOS-arm64.dmg" | shasum -a 256 | cut -d' ' -f1)
X64_SHA256=\$(curl -L -s "https://github.com/\${GITHUB_REPO}/releases/download/\${VERSION}/PowerAutomation-\${VERSION}-macOS-x64.dmg" | shasum -a 256 | cut -d' ' -f1)

# 更新Formula
sed -i "" "s/ARM64_SHA256_PLACEHOLDER/\${ARM64_SHA256}/g" ${FORMULA_NAME}.rb
sed -i "" "s/X64_SHA256_PLACEHOLDER/\${X64_SHA256}/g" ${FORMULA_NAME}.rb

echo "Formula updated with new SHA256 checksums"
echo "ARM64 SHA256: \${ARM64_SHA256}"
echo "X64 SHA256: \${X64_SHA256}"
\`\`\`

## 驗證清單

- [ ] 版本號正確
- [ ] 下載URL可訪問
- [ ] SHA256校驗碼正確
- [ ] Formula語法正確
- [ ] 安裝測試通過
- [ ] 功能測試通過
- [ ] 文檔已更新
- [ ] 提交並推送

## 常見問題

### Formula審核失敗
- 檢查語法: \`brew audit --strict ${FORMULA_NAME}\`
- 檢查依賴: 確保所有依賴都可用
- 檢查測試: 確保test塊正確

### 安裝失敗
- 檢查下載URL是否正確
- 檢查SHA256是否匹配
- 檢查系統要求是否滿足

### 功能測試失敗
- 檢查可執行文件路徑
- 檢查環境變量設置
- 檢查權限設置
EOF
    
    log "更新說明生成完成: UPDATE_INSTRUCTIONS.md"
}

# 主函數
main() {
    header "PowerAutomation v4.6.1 Homebrew Formula 生成器"
    
    generate_formula
    generate_tap_readme
    generate_update_instructions
    
    echo
    echo -e "${GREEN}🎉 Homebrew Formula 文件已生成完成！${NC}"
    echo
    echo -e "${BLUE}📁 生成的文件：${NC}"
    echo -e "   • ${FORMULA_NAME}.rb"
    echo -e "   • README.md"
    echo -e "   • UPDATE_INSTRUCTIONS.md"
    echo
    echo -e "${BLUE}🚀 下一步：${NC}"
    echo -e "   1. 創建Homebrew tap repository"
    echo -e "   2. 上傳這些文件到tap repository"
    echo -e "   3. 計算並更新SHA256校驗碼"
    echo -e "   4. 測試Formula安裝"
    echo -e "   5. 提交到官方tap（如果需要）"
    echo
}

# 執行主函數
main "$@"