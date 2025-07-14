#!/usr/bin/env python3
"""
安装依赖包的脚本
"""

import subprocess
import sys

def install_package(package):
    """安装单个包"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ 成功安装: {package}")
    except subprocess.CalledProcessError as e:
        print(f"❌ 安装失败: {package} - {e}")

def main():
    """安装所有必需的依赖包"""
    
    print("🔧 开始安装OCR系统依赖包...")
    
    packages = [
        "torch",
        "torchvision", 
        "numpy",
        "opencv-python",
        "Pillow",
        "google-generativeai",
        "requests",
        "asyncio"
    ]
    
    for package in packages:
        install_package(package)
    
    print("\n🎉 依赖包安装完成!")
    print("现在可以运行OCR系统了:")
    print("python sota_ondevice_ocr.py")
    print("python hybrid_edge_cloud_ocr.py")

if __name__ == "__main__":
    main()