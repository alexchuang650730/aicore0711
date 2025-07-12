#!/usr/bin/env python3
"""
PowerAutomation v4.6.6 網絡環境檢測工具
Network Environment Detection Tool

檢測你的網絡環境並推薦最適合的部署方案：
1. 檢測公網IP和內網IP
2. 檢測SSH服務狀態  
3. 推薦部署方案
4. 生成配置文件
"""

import asyncio
import json
import platform
import socket
import subprocess
import requests
import os
from pathlib import Path
from typing import Dict, Any, Optional

class NetworkEnvironmentDetector:
    """網絡環境檢測器"""
    
    def __init__(self):
        self.public_ip = None
        self.private_ip = None
        self.hostname = None
        self.username = None
        self.ssh_enabled = False
        self.router_supports_portforward = None
        
    async def detect_environment(self) -> Dict[str, Any]:
        """檢測網絡環境"""
        print("🔍 檢測網絡環境...")
        
        # 1. 基本設備信息
        await self._detect_device_info()
        
        # 2. IP地址檢測
        await self._detect_ip_addresses()
        
        # 3. SSH服務檢測
        await self._detect_ssh_service()
        
        # 4. 網絡可達性檢測
        await self._test_network_connectivity()
        
        return self._generate_environment_report()
    
    async def _detect_device_info(self):
        """檢測設備基本信息"""
        print("  📱 檢測設備信息...")
        
        self.hostname = socket.gethostname()
        self.username = os.getenv('USER') or os.getenv('USERNAME')
        self.platform = platform.system()
        
        print(f"    🖥️ 主機名: {self.hostname}")
        print(f"    👤 用戶: {self.username}")
        print(f"    💻 系統: {self.platform}")
    
    async def _detect_ip_addresses(self):
        """檢測IP地址"""
        print("  🌐 檢測IP地址...")
        
        # 檢測公網IP
        try:
            response = requests.get('https://ifconfig.me/ip', timeout=10)
            self.public_ip = response.text.strip()
            print(f"    🌍 公網IP: {self.public_ip}")
        except:
            print("    ❌ 無法獲取公網IP")
        
        # 檢測內網IP
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                self.private_ip = s.getsockname()[0]
            print(f"    🏠 內網IP: {self.private_ip}")
        except:
            print("    ❌ 無法獲取內網IP")
    
    async def _detect_ssh_service(self):
        """檢測SSH服務"""
        print("  🔐 檢測SSH服務...")
        
        try:
            if self.platform == "Darwin":  # macOS
                result = subprocess.run(
                    ["sudo", "systemsetup", "-getremotelogin"],
                    capture_output=True, text=True, timeout=10
                )
                self.ssh_enabled = "On" in result.stdout
            elif self.platform == "Linux":
                result = subprocess.run(
                    ["systemctl", "is-active", "ssh"],
                    capture_output=True, text=True, timeout=10
                )
                self.ssh_enabled = result.returncode == 0
            
            status = "✅ 已啟用" if self.ssh_enabled else "❌ 未啟用"
            print(f"    🔐 SSH服務: {status}")
            
        except Exception as e:
            print(f"    ⚠️ SSH檢測失敗: {e}")
    
    async def _test_network_connectivity(self):
        """測試網絡連通性"""
        print("  📡 測試網絡連通性...")
        
        # 測試到AWS的連通性
        try:
            response = requests.get('https://aws.amazon.com', timeout=10)
            aws_reachable = response.status_code == 200
            print(f"    ☁️ AWS連通性: {'✅ 正常' if aws_reachable else '❌ 異常'}")
        except:
            print("    ☁️ AWS連通性: ❌ 無法連接")
        
        # 測試到GitHub的連通性
        try:
            response = requests.get('https://github.com', timeout=10)
            github_reachable = response.status_code == 200
            print(f"    🐙 GitHub連通性: {'✅ 正常' if github_reachable else '❌ 異常'}")
        except:
            print("    🐙 GitHub連通性: ❌ 無法連接")
    
    def _generate_environment_report(self) -> Dict[str, Any]:
        """生成環境報告"""
        return {
            "device_info": {
                "hostname": self.hostname,
                "username": self.username,
                "platform": self.platform
            },
            "network_info": {
                "public_ip": self.public_ip,
                "private_ip": self.private_ip,
                "ssh_enabled": self.ssh_enabled
            },
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> Dict[str, Any]:
        """生成部署方案推薦"""
        recommendations = {}
        
        if self.public_ip and self.ssh_enabled:
            recommendations["primary"] = {
                "method": "public_ip_deployment",
                "name": "公網IP直接部署",
                "description": "EC2直接通過公網IP連接到你的設備",
                "requirements": [
                    "確保SSH服務已啟用",
                    "配置防火牆允許SSH連接",
                    "考慮修改SSH默認端口22以提高安全性"
                ],
                "config": {
                    "host": self.public_ip,
                    "username": self.username,
                    "ssh_port": 22,
                    "connection_type": "public_ip"
                }
            }
        else:
            recommendations["primary"] = {
                "method": "local_deployment", 
                "name": "本地構建部署",
                "description": "在本地構建並部署到同網段設備",
                "requirements": [
                    "在本地運行構建腳本",
                    "配置本地SSH連接",
                    "適合個人和小團隊使用"
                ],
                "config": {
                    "host": self.private_ip,
                    "username": self.username,
                    "ssh_port": 22,
                    "connection_type": "local"
                }
            }
        
        # 備選方案
        recommendations["alternatives"] = [
            {
                "method": "vpn_deployment",
                "name": "VPN隧道部署", 
                "description": "通過VPN連接EC2和本地網絡",
                "use_case": "企業環境或需要安全連接時"
            },
            {
                "method": "reverse_tunnel",
                "name": "反向隧道部署",
                "description": "本地主動連接到EC2建立隧道",
                "use_case": "公網IP不穩定或NAT環境"
            }
        ]
        
        return recommendations

async def main():
    """主函數"""
    print("🌐 PowerAutomation v4.6.6 網絡環境檢測工具")
    print("=" * 60)
    print("正在檢測你的網絡環境以推薦最佳部署方案...")
    print()
    
    try:
        detector = NetworkEnvironmentDetector()
        report = await detector.detect_environment()
        
        print("\n📊 環境檢測完成!")
        print("=" * 40)
        
        # 顯示設備信息
        device_info = report["device_info"]
        print(f"🖥️ 設備: {device_info['hostname']} ({device_info['platform']})")
        print(f"👤 用戶: {device_info['username']}")
        
        # 顯示網絡信息  
        network_info = report["network_info"]
        print(f"🌍 公網IP: {network_info['public_ip'] or '未檢測到'}")
        print(f"🏠 內網IP: {network_info['private_ip'] or '未檢測到'}")
        print(f"🔐 SSH服務: {'✅ 已啟用' if network_info['ssh_enabled'] else '❌ 未啟用'}")
        
        # 顯示推薦方案
        recommendations = report["recommendations"]
        primary = recommendations["primary"]
        
        print(f"\n🎯 推薦部署方案: {primary['name']}")
        print(f"📝 說明: {primary['description']}")
        print(f"📋 要求:")
        for req in primary['requirements']:
            print(f"  • {req}")
        
        # 生成配置文件
        config = {
            "deployment_method": primary['method'],
            "deployment_targets": [
                {
                    "name": f"primary_{device_info['hostname']}",
                    **primary['config']
                }
            ],
            "environment_report": report
        }
        
        config_file = Path("deployment_config_auto.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 配置已保存到: {config_file}")
        
        # 顯示備選方案
        print(f"\n🔄 備選方案:")
        for alt in recommendations.get('alternatives', []):
            print(f"  📌 {alt['name']}: {alt['description']}")
            print(f"    適用場景: {alt['use_case']}")
        
        # 下一步指引
        print(f"\n🚀 下一步操作:")
        if primary['method'] == 'public_ip_deployment':
            print("1. 確保SSH服務已啟用")
            print("2. 配置SSH密鑰認證")
            print("3. 運行雲端到邊緣部署:")
            print("   python deployment/cloud_edge_deployment.py")
        else:
            print("1. 配置本地SSH連接")
            print("2. 運行本地構建部署:")
            print("   python deployment/local_deployment.py")
        
        print(f"\n💡 提示: 部署系統會自動使用生成的配置文件")
        
        return 0
        
    except Exception as e:
        print(f"\n💥 檢測過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)