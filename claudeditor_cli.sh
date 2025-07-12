#!/bin/bash
"""
ClaudeEditor v4.6.7 快速啟動腳本
Quick Launch Script for ClaudeEditor
"""

# 設置顏色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🚀 ClaudeEditor v4.6.7 Command Interface${NC}"
echo -e "${CYAN}=======================================${NC}"

# 定義函數
claudeditor() {
    python3 ~/.local/bin/claudeditor "$@"
}

mcp() {
    python3 ~/.local/bin/mcp "$@"
}

workflow() {
    python3 ~/.local/bin/workflow "$@"
}

# 顯示可用命令
show_help() {
    echo -e "${GREEN}📋 可用命令:${NC}"
    echo -e "  ${YELLOW}claudeditor${NC} start/status/help     - ClaudeEditor主控制"
    echo -e "  ${YELLOW}mcp${NC} <component> <action>        - MCP組件控制"
    echo -e "  ${YELLOW}workflow${NC} <action> [name]         - 工作流控制"
    echo ""
    echo -e "${GREEN}🔧 MCP組件:${NC}"
    echo -e "  • ${BLUE}codeflow${NC} (整合) - 代碼生成核心"
    echo -e "  • ${BLUE}xmasters${NC} (獨立) - 深度推理"
    echo -e "  • ${BLUE}operations${NC} (獨立) - 系統運維"
    echo -e "  • ${BLUE}security${NC} (獨立) - 安全管控"
    echo -e "  • ${BLUE}collaboration${NC} (獨立) - 團隊協作"
    echo -e "  • ${BLUE}deployment${NC} (獨立) - 多平台部署"
    echo -e "  • ${BLUE}analytics${NC} (獨立) - 數據分析"
    echo ""
    echo -e "${GREEN}🔄 工作流:${NC}"
    echo -e "  • ${PURPLE}code_generation${NC} - 代碼生成工作流"
    echo -e "  • ${PURPLE}ui_design${NC} - UI設計工作流"
    echo -e "  • ${PURPLE}api_development${NC} - API開發工作流"
    echo -e "  • ${PURPLE}database_design${NC} - 數據庫設計工作流"
    echo -e "  • ${PURPLE}test_automation${NC} - 測試自動化工作流"
    echo -e "  • ${PURPLE}deployment_pipeline${NC} - 部署流水線工作流"
    echo ""
    echo -e "${GREEN}💡 使用示例:${NC}"
    echo -e "  ${CYAN}claudeditor status${NC}                    - 查看系統狀態"
    echo -e "  ${CYAN}mcp codeflow status${NC}                   - 查看CodeFlow狀態"
    echo -e "  ${CYAN}mcp xmasters solve \"性能優化問題\"${NC}      - X-Masters解決問題"
    echo -e "  ${CYAN}workflow start code_generation${NC}        - 啟動代碼生成工作流"
    echo -e "  ${CYAN}workflow list${NC}                         - 列出所有工作流"
    echo ""
    echo -e "${YELLOW}輸入 'exit' 或 Ctrl+C 退出${NC}"
}

# 交互式模式
interactive_mode() {
    show_help
    echo ""
    
    while true; do
        echo -ne "${GREEN}claudeditor>${NC} "
        read -r input
        
        case "$input" in
            "exit" | "quit")
                echo -e "${CYAN}👋 ClaudeEditor已退出${NC}"
                break
                ;;
            "help" | "")
                show_help
                ;;
            "status")
                claudeditor status
                ;;
            "quick-start")
                echo -e "${YELLOW}🚀 快速啟動演示...${NC}"
                echo ""
                claudeditor status
                echo ""
                workflow list
                echo ""
                mcp codeflow status
                ;;
            cloudeditor*)
                eval "$input"
                ;;
            mcp*)
                eval "$input"
                ;;
            workflow*)
                eval "$input"
                ;;
            *)
                if [[ $input == "!"* ]]; then
                    # 處理 ! 開頭的MCP指令
                    cmd=${input:1}  # 移除前綴 !
                    if [[ $cmd == workflow* ]]; then
                        eval "$cmd"
                    elif [[ $cmd == *masters* ]]; then
                        mcp xmasters ${cmd#*masters }
                    elif [[ $cmd == ops* ]]; then
                        mcp operations ${cmd#ops }
                    elif [[ $cmd == security* ]]; then
                        mcp security ${cmd#security }
                    elif [[ $cmd == deploy* ]]; then
                        mcp deployment ${cmd#deploy }
                    elif [[ $cmd == analytics* ]]; then
                        mcp analytics ${cmd#analytics }
                    elif [[ $cmd == collab* ]]; then
                        mcp collaboration ${cmd#collab }
                    else
                        echo -e "${RED}❌ 未知MCP指令: $cmd${NC}"
                    fi
                else
                    echo -e "${RED}❌ 未知命令: $input${NC}"
                    echo -e "輸入 'help' 查看可用命令"
                fi
                ;;
        esac
        echo ""
    done
}

# 如果有參數，直接執行；否則進入交互模式
if [ $# -eq 0 ]; then
    interactive_mode
else
    case "$1" in
        "claudeditor")
            shift
            claudeditor "$@"
            ;;
        "mcp")
            shift
            mcp "$@"
            ;;
        "workflow")
            shift
            workflow "$@"
            ;;
        *)
            echo -e "${RED}❌ 未知命令: $1${NC}"
            show_help
            ;;
    esac
fi