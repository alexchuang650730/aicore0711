#!/usr/bin/env python3
"""
PowerAutomation v4.6.6 手動配置部署目標
Manual Deployment Target Configuration

快速配置你的公網IP作為部署目標
"""

import json
import os
import socket
from pathlib import Path

def setup_manual_deployment():
    """手動設置部署目標"""
    print("🎯 PowerAutomation v4.6.6 手動部署目標配置")
    print("=" * 50)
    
    # 獲取當前設備信息
    hostname = socket.gethostname()
    username = os.getenv('USER') or os.getenv('USERNAME')
    
    print(f"📱 當前設備信息:")
    print(f"  🖥️ 主機名: {hostname}")
    print(f"  👤 用戶名: {username}")
    print()
    
    # 詢問公網IP
    print("🌍 請提供你的公網IP地址:")
    print("  提示: 你可以通過 https://ifconfig.me 查看你的公網IP")
    
    while True:
        public_ip = input("請輸入公網IP: ").strip()
        if public_ip:
            # 簡單的IP格式驗證
            parts = public_ip.split('.')
            if len(parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in parts):
                break
            else:
                print("❌ IP格式不正確，請重新輸入")
        else:
            print("❌ IP不能為空，請重新輸入")
    
    # 詢問SSH端口
    print("\n🔐 SSH配置:")
    ssh_port = input("SSH端口 (默認22): ").strip()
    if not ssh_port:
        ssh_port = "22"
    
    # 詢問用戶名
    actual_username = input(f"SSH用戶名 (默認{username}): ").strip()
    if not actual_username:
        actual_username = username
    
    # 詢問SSH密鑰路徑
    ssh_key = input("SSH密鑰路徑 (默認~/.ssh/id_rsa): ").strip()
    if not ssh_key:
        ssh_key = "~/.ssh/id_rsa"
    
    # 生成配置
    config = {
        "deployment_method": "public_ip_deployment",
        "deployment_targets": [
            {
                "name": f"dev_mac_{hostname}",
                "host": public_ip,
                "username": actual_username,
                "ssh_port": int(ssh_port),
                "ssh_key_path": ssh_key,
                "platform": "macos",
                "connection_type": "public_ip",
                "is_manual_config": True
            }
        ],
        "config_notes": [
            "這是手動配置的部署目標",
            "確保SSH服務已在目標設備上啟用",
            "確保SSH密鑰已正確配置",
            "如果使用非標準端口，確保防火牆允許該端口"
        ]
    }
    
    # 保存配置
    config_file = Path("deployment_targets_config.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 配置已保存!")
    print(f"📄 配置文件: {config_file}")
    print(f"🎯 部署目標: {public_ip}:{ssh_port}")
    print(f"👤 用戶: {actual_username}")
    
    # 提供測試建議
    print(f"\n🧪 測試連接:")
    if ssh_port == "22":
        test_cmd = f"ssh {actual_username}@{public_ip}"
    else:
        test_cmd = f"ssh -p {ssh_port} {actual_username}@{public_ip}"
    
    print(f"  {test_cmd}")
    
    print(f"\n🚀 下一步:")
    print("1. 測試SSH連接是否正常")
    print("2. 運行雲端到邊緣部署:")
    print("   python deployment/cloud_edge_deployment.py")
    
    print(f"\n💡 提示: 部署系統會自動使用這個配置文件")
    
    return config

def main():
    try:
        config = setup_manual_deployment()
        return 0
    except KeyboardInterrupt:
        print("\n⚠️ 配置已取消")
        return 1
    except Exception as e:
        print(f"\n💥 配置失敗: {e}")
        return 1

if __name__ == "__main__":
    exit(main())