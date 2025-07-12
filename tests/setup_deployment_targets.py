#!/usr/bin/env python3
"""
PowerAutomation v4.6.6 快速設備發現工具
Quick Device Discovery Tool

這個工具幫助你快速發現和配置部署目標：
1. 自動檢測你的IP地址
2. 掃描局域網內的其他設備  
3. 生成部署配置文件
4. 提供SSH配置建議
"""

import asyncio
import sys
import os
sys.path.append('.')

# 檢查依賴
try:
    import netifaces
except ImportError:
    print("❌ 缺少依賴 netifaces，請安裝: pip install netifaces")
    sys.exit(1)

from deployment.device_discovery import device_discovery_manager

async def main():
    """快速設備發現主函數"""
    print("🔍 PowerAutomation v4.6.6 快速設備發現工具")
    print("=" * 60)
    print("這個工具將幫助你：")
    print("  1. 🖥️ 檢測當前設備信息")
    print("  2. 🌐 掃描局域網內設備")
    print("  3. 📋 生成部署配置")
    print("  4. 💡 提供SSH配置建議")
    print()
    
    try:
        # 步驟1: 初始化
        print("🚀 步驟1: 初始化設備發現...")
        await device_discovery_manager.initialize()
        
        # 步驟2: 顯示當前設備
        print("\n📱 步驟2: 當前設備信息")
        current = device_discovery_manager.current_device
        if current:
            print(f"  🖥️ 設備名稱: {current.device_name}")
            print(f"  🌐 IP地址: {current.ip_address}")
            print(f"  👤 用戶名: {current.username}")
            print(f"  💻 系統: {current.platform}")
            print()
            print("✅ 這個設備將被自動添加為部署目標")
        
        # 步驟3: 顯示網絡信息
        print("\n🌐 步驟3: 網絡接口信息")
        for ni in device_discovery_manager.network_interfaces:
            print(f"  📡 {ni.interface_name}: {ni.ip_address}")
            print(f"    🌍 網段: {ni.network_cidr}")
            print(f"    🚪 網關: {ni.gateway}")
        
        # 步驟4: 詢問是否掃描
        print("\n🔍 步驟4: 設備掃描")
        print("是否要掃描局域網內的其他設備？")
        print("  ⚡ 快速模式：只掃描當前設備 (y)")
        print("  🌐 完整模式：掃描整個局域網 (n)")
        
        choice = input("請選擇 [y/n]: ").lower().strip()
        
        discovered_devices = []
        if choice == 'n':
            print("\n🔍 正在掃描局域網內設備...")
            print("⏱️ 這可能需要1-2分鐘，請耐心等待...")
            discovered_devices = await device_discovery_manager.discover_devices_in_network()
            
            if discovered_devices:
                print(f"\n✅ 發現 {len(discovered_devices)} 個設備:")
                for i, device in enumerate(discovered_devices, 1):
                    status = "🔵 當前設備" if device.is_current_device else "🟢 其他設備"
                    print(f"  {i}. {status} {device.hostname} ({device.ip_address})")
            else:
                print("\n⚠️ 未發現其他可達設備")
        else:
            print("\n⚡ 使用快速模式，只配置當前設備")
        
        # 步驟5: 生成配置
        print("\n📋 步驟5: 生成部署配置")
        config = device_discovery_manager.generate_deployment_targets_config(
            discovered_devices, 
            include_current_device=True
        )
        
        # 保存配置
        config_file = device_discovery_manager.save_deployment_config(
            config, 
            "deployment_targets_config.json"
        )
        
        # 步驟6: 顯示結果
        print(f"\n🎉 步驟6: 配置完成!")
        print(f"📄 配置文件: {config_file}")
        print(f"🎯 部署目標數: {len(config['deployment_targets'])}")
        
        print(f"\n📋 部署目標列表:")
        for target in config['deployment_targets']:
            current_flag = " (當前設備)" if target.get('is_current_device') else ""
            print(f"  📱 {target['name']}: {target['host']}{current_flag}")
            print(f"    👤 用戶: {target['username']}")
        
        # 步驟7: SSH配置建議
        print(f"\n🔐 步驟7: SSH配置建議")
        print("為了讓部署系統能夠連接到設備，請確保：")
        print()
        print("1. 📡 啟用SSH服務:")
        print("   macOS: 系統偏好設定 → 共享 → 遠程登錄")
        print("   Linux: sudo systemctl enable ssh")
        print()
        print("2. 🔑 配置SSH密鑰:")
        print("   # 生成密鑰對 (如果還沒有)")
        print("   ssh-keygen -t rsa -b 4096")
        print()
        print("   # 複製公鑰到目標設備")
        for target in config['deployment_targets']:
            if not target.get('is_current_device'):
                print(f"   ssh-copy-id {target['username']}@{target['host']}")
        print()
        print("3. 🧪 測試連接:")
        for target in config['deployment_targets']:
            if not target.get('is_current_device'):
                print(f"   ssh {target['username']}@{target['host']}")
        print()
        
        # 步驟8: 下一步指引
        print("🚀 下一步指引:")
        print("1. 根據上述建議配置SSH連接")
        print("2. 編輯配置文件中的用戶名（如果需要）")
        print("3. 運行雲端到邊緣部署:")
        print("   python deployment/cloud_edge_deployment.py")
        print()
        print("💡 提示: 部署系統會自動使用生成的配置文件")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ 用戶中斷操作")
        return 1
    except Exception as e:
        print(f"\n💥 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    print("🔍 啟動設備發現工具...")
    exit_code = asyncio.run(main())
    exit(exit_code)