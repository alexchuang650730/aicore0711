#!/bin/bash
# ClaudEditor UI自动化测试启动脚本
# 作者: PowerAutomation Team
# 版本: 4.1
# 日期: 2025-01-07

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    echo "ClaudEditor UI自动化测试启动脚本"
    echo ""
    echo "使用方法:"
    echo "  ./start_ui_tests.sh [选项]"
    echo ""
    echo "选项:"
    echo "  smoke       运行冒烟测试"
    echo "  core        运行核心功能测试"
    echo "  integration 运行集成测试"
    echo "  performance 运行性能测试"
    echo "  full        运行完整测试套件"
    echo "  setup       只设置环境，不运行测试"
    echo "  clean       清理测试结果和录制文件"
    echo "  help        显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  ./start_ui_tests.sh smoke           # 运行冒烟测试"
    echo "  ./start_ui_tests.sh core --headless # 无头模式运行核心测试"
    echo "  ./start_ui_tests.sh integration     # 运行集成测试"
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi
    
    # 检查Node.js (用于前端)
    if ! command -v node &> /dev/null; then
        print_warning "Node.js 未安装，可能影响前端服务"
    fi
    
    # 检查必要的Python包
    python3 -c "import asyncio, aiohttp, selenium" 2>/dev/null || {
        print_warning "某些Python依赖可能缺失，正在安装..."
        pip3 install asyncio aiohttp selenium webdriver-manager
    }
    
    print_success "依赖检查完成"
}

# 设置环境
setup_environment() {
    print_info "设置测试环境..."
    
    # 创建必要的目录
    mkdir -p test_results/{screenshots,recordings,reports}
    mkdir -p logs
    
    # 检查配置文件
    if [ ! -f "test_config.json" ]; then
        print_warning "配置文件不存在，将使用默认配置"
    fi
    
    # 检查服务状态
    check_services
    
    print_success "环境设置完成"
}

# 检查服务状态
check_services() {
    print_info "检查服务状态..."
    
    # 检查前端服务 (端口3000)
    if curl -s http://localhost:3000 > /dev/null; then
        print_success "前端服务 (3000) 运行正常"
    else
        print_warning "前端服务 (3000) 未运行"
        print_info "尝试启动前端服务..."
        start_frontend_service
    fi
    
    # 检查后端API (端口5000)
    if curl -s http://localhost:5000/api/ai-assistant/health > /dev/null; then
        print_success "后端API (5000) 运行正常"
    else
        print_warning "后端API (5000) 未运行"
        print_info "尝试启动后端服务..."
        start_backend_service
    fi
}

# 启动前端服务
start_frontend_service() {
    if [ -d "claudeditor-ui" ]; then
        cd claudeditor-ui
        if [ -f "package.json" ]; then
            print_info "启动React前端服务..."
            npm start &
            FRONTEND_PID=$!
            echo $FRONTEND_PID > ../frontend.pid
            sleep 10  # 等待服务启动
            cd ..
        else
            print_error "前端项目配置文件不存在"
        fi
    else
        print_error "前端项目目录不存在"
    fi
}

# 启动后端服务
start_backend_service() {
    if [ -f "claudeditor-api/src/main.py" ]; then
        print_info "启动Flask后端服务..."
        cd claudeditor-api/src
        python3 main.py &
        BACKEND_PID=$!
        echo $BACKEND_PID > ../../backend.pid
        sleep 5  # 等待服务启动
        cd ../..
    else
        print_error "后端项目文件不存在"
    fi
}

# 运行测试
run_tests() {
    local test_type=$1
    shift  # 移除第一个参数，剩下的作为额外参数
    
    print_info "运行 $test_type 测试..."
    
    case $test_type in
        "smoke")
            python3 run_ui_tests.py --smoke "$@"
            ;;
        "core")
            python3 run_ui_tests.py --core "$@"
            ;;
        "integration")
            python3 run_ui_tests.py --integration "$@"
            ;;
        "performance")
            python3 run_ui_tests.py --tags performance "$@"
            ;;
        "full")
            python3 run_ui_tests.py "$@"
            ;;
        *)
            print_error "未知的测试类型: $test_type"
            show_help
            exit 1
            ;;
    esac
}

# 清理函数
cleanup() {
    print_info "清理测试环境..."
    
    # 停止启动的服务
    if [ -f "frontend.pid" ]; then
        kill $(cat frontend.pid) 2>/dev/null || true
        rm frontend.pid
    fi
    
    if [ -f "backend.pid" ]; then
        kill $(cat backend.pid) 2>/dev/null || true
        rm backend.pid
    fi
    
    print_success "清理完成"
}

# 清理测试结果
clean_results() {
    print_info "清理测试结果和录制文件..."
    
    rm -rf test_results/*
    rm -rf logs/*
    
    print_success "清理完成"
}

# 信号处理
trap cleanup EXIT

# 主逻辑
main() {
    echo "🚀 ClaudEditor UI自动化测试系统 v4.1"
    echo "================================================"
    
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    case $1 in
        "help"|"-h"|"--help")
            show_help
            ;;
        "setup")
            check_dependencies
            setup_environment
            print_success "环境设置完成，可以运行测试了"
            ;;
        "clean")
            clean_results
            ;;
        "smoke"|"core"|"integration"|"performance"|"full")
            check_dependencies
            setup_environment
            run_tests "$@"
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"

