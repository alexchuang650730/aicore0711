#!/usr/bin/env python3
"""
ClaudeEditor 4.6.0 测试运行脚本
提供便捷的测试执行和报告功能
"""

import sys
import subprocess
import argparse
import os
from pathlib import Path

def run_command(cmd, cwd=None):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd,
            capture_output=True, 
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def install_dependencies():
    """安装测试依赖"""
    print("📦 安装测试依赖...")
    
    dependencies = [
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0",
        "pytest-mock>=3.10.0",
        "pytest-cov>=4.0.0",
        "pytest-timeout>=2.1.0",
        "pytest-xdist>=3.0.0",
        "psutil>=5.9.0"
    ]
    
    for dep in dependencies:
        print(f"  安装 {dep}...")
        success, output = run_command(f"pip install {dep}")
        if not success:
            print(f"  ❌ 安装失败: {dep}")
            print(output)
            return False
        else:
            print(f"  ✅ 安装成功: {dep}")
    
    return True

def run_unit_tests(verbose=False, coverage=False):
    """运行单元测试"""
    print("🧪 运行单元测试...")
    
    cmd = "python -m pytest tests/unit/ -m unit"
    
    if verbose:
        cmd += " -v"
    
    if coverage:
        cmd += " --cov=core --cov-report=html --cov-report=term-missing"
    
    success, output = run_command(cmd)
    
    if success:
        print("✅ 单元测试通过")
        print(output)
    else:
        print("❌ 单元测试失败")
        print(output)
    
    return success

def run_integration_tests(verbose=False):
    """运行集成测试"""
    print("🔗 运行集成测试...")
    
    cmd = "python -m pytest tests/integration/ -m integration"
    
    if verbose:
        cmd += " -v"
    
    success, output = run_command(cmd)
    
    if success:
        print("✅ 集成测试通过")
        print(output)
    else:
        print("❌ 集成测试失败")
        print(output)
    
    return success

def run_e2e_tests(verbose=False):
    """运行端到端测试"""
    print("🎯 运行端到端测试...")
    
    cmd = "python -m pytest tests/e2e/ -m e2e"
    
    if verbose:
        cmd += " -v"
    
    success, output = run_command(cmd)
    
    if success:
        print("✅ 端到端测试通过")
        print(output)
    else:
        print("❌ 端到端测试失败")
        print(output)
    
    return success

def run_all_tests(verbose=False, coverage=False, parallel=False):
    """运行所有测试"""
    print("🚀 运行所有测试...")
    
    cmd = "python -m pytest tests/"
    
    if verbose:
        cmd += " -v"
    
    if coverage:
        cmd += " --cov=core --cov-report=html --cov-report=term-missing"
    
    if parallel:
        cmd += " -n auto"
    
    success, output = run_command(cmd)
    
    if success:
        print("✅ 所有测试通过")
        print(output)
    else:
        print("❌ 部分测试失败")
        print(output)
    
    return success

def run_specific_test(test_path, verbose=False):
    """运行特定测试"""
    print(f"🎯 运行特定测试: {test_path}")
    
    cmd = f"python -m pytest {test_path}"
    
    if verbose:
        cmd += " -v"
    
    success, output = run_command(cmd)
    
    if success:
        print("✅ 测试通过")
        print(output)
    else:
        print("❌ 测试失败")
        print(output)
    
    return success

def generate_test_report():
    """生成测试报告"""
    print("📊 生成测试报告...")
    
    # 运行带覆盖率的测试
    cmd = "python -m pytest tests/ --cov=core --cov-report=html --cov-report=xml --junit-xml=test-results.xml"
    
    success, output = run_command(cmd)
    
    if success:
        print("✅ 测试报告生成成功")
        print("  📁 HTML覆盖率报告: htmlcov/index.html")
        print("  📄 XML覆盖率报告: coverage.xml")
        print("  📄 JUnit测试报告: test-results.xml")
    else:
        print("❌ 测试报告生成失败")
        print(output)
    
    return success

def check_test_environment():
    """检查测试环境"""
    print("🔍 检查测试环境...")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version < (3, 8):
        print(f"❌ Python版本过低: {python_version.major}.{python_version.minor}")
        print("   需要Python 3.8或更高版本")
        return False
    else:
        print(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查必要的模块
    required_modules = ["pytest", "asyncio", "pathlib"]
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ 模块可用: {module}")
        except ImportError:
            print(f"❌ 模块缺失: {module}")
            return False
    
    # 检查测试目录
    test_dirs = ["tests/unit", "tests/integration", "tests/e2e"]
    for test_dir in test_dirs:
        if Path(test_dir).exists():
            print(f"✅ 测试目录存在: {test_dir}")
        else:
            print(f"❌ 测试目录缺失: {test_dir}")
            return False
    
    print("✅ 测试环境检查通过")
    return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="ClaudeEditor 4.6.0 测试运行器")
    
    parser.add_argument("--install-deps", action="store_true", help="安装测试依赖")
    parser.add_argument("--check-env", action="store_true", help="检查测试环境")
    parser.add_argument("--unit", action="store_true", help="运行单元测试")
    parser.add_argument("--integration", action="store_true", help="运行集成测试")
    parser.add_argument("--e2e", action="store_true", help="运行端到端测试")
    parser.add_argument("--all", action="store_true", help="运行所有测试")
    parser.add_argument("--test", type=str, help="运行特定测试文件或目录")
    parser.add_argument("--report", action="store_true", help="生成测试报告")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--coverage", action="store_true", help="生成覆盖率报告")
    parser.add_argument("--parallel", action="store_true", help="并行运行测试")
    
    args = parser.parse_args()
    
    # 如果没有指定任何参数，显示帮助
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    success = True
    
    # 安装依赖
    if args.install_deps:
        success = install_dependencies() and success
    
    # 检查环境
    if args.check_env:
        success = check_test_environment() and success
    
    # 运行测试
    if args.unit:
        success = run_unit_tests(args.verbose, args.coverage) and success
    
    if args.integration:
        success = run_integration_tests(args.verbose) and success
    
    if args.e2e:
        success = run_e2e_tests(args.verbose) and success
    
    if args.all:
        success = run_all_tests(args.verbose, args.coverage, args.parallel) and success
    
    if args.test:
        success = run_specific_test(args.test, args.verbose) and success
    
    if args.report:
        success = generate_test_report() and success
    
    # 退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

