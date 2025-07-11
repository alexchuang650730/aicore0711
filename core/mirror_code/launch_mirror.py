#!/usr/bin/env python3
"""
Launch Mirror - Mirror Code系統啟動腳本
提供簡單的啟動接口來運行完整的Mirror Code系統
"""

import asyncio
import argparse
import json
import os
import sys
from pathlib import Path

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.mirror_code.engine.mirror_engine import MirrorEngine, MirrorConfig

async def launch_mirror_system(config_file: str = None, debug: bool = False):
    """啟動Mirror系統"""
    print("🚀 啟動PowerAutomation Mirror Code系統...")
    print("=" * 60)
    
    # 加載配置
    config = load_config(config_file, debug)
    
    # 創建Mirror Engine
    engine = MirrorEngine(config)
    
    try:
        # 啟動引擎
        success = await engine.start()
        
        if not success:
            print("❌ Mirror系統啟動失敗")
            return 1
        
        print("\n🎉 Mirror系統啟動成功！")
        print_system_info(engine)
        
        # 保持運行
        print("\n⌨️  按 Ctrl+C 停止系統")
        
        try:
            while engine.status.value == "running":
                await asyncio.sleep(1)
                
                # 可以在這裡添加定期狀態檢查
                if debug and engine.sync_count % 10 == 0 and engine.sync_count > 0:
                    print(f"🔄 Debug: 已完成 {engine.sync_count} 次同步")
        
        except KeyboardInterrupt:
            print("\n\n🛑 接收到停止信號...")
        
        # 停止引擎
        print("🔄 正在停止Mirror系統...")
        await engine.stop()
        print("✅ Mirror系統已停止")
        
        return 0
        
    except Exception as e:
        print(f"❌ 系統運行錯誤: {e}")
        
        # 嘗試清理
        try:
            await engine.stop()
        except:
            pass
        
        return 1

def load_config(config_file: str = None, debug: bool = False) -> MirrorConfig:
    """加載配置"""
    config_data = {}
    
    # 從文件加載配置
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            print(f"📋 已加載配置文件: {config_file}")
        except Exception as e:
            print(f"⚠️ 配置文件加載失敗: {e}")
    
    # 創建配置對象
    config = MirrorConfig(
        enabled=config_data.get("enabled", True),
        auto_sync=config_data.get("auto_sync", True),
        sync_interval=config_data.get("sync_interval", 5),
        debug=debug or config_data.get("debug", False),
        websocket_port=config_data.get("websocket_port", 8765),
        claude_integration=config_data.get("claude_integration", True),
        local_adapters=config_data.get("local_adapters"),
        remote_endpoints=config_data.get("remote_endpoints")
    )
    
    print("🔧 Mirror配置:")
    print(f"  自動同步: {config.auto_sync}")
    print(f"  同步間隔: {config.sync_interval}秒")
    print(f"  Claude集成: {config.claude_integration}")
    print(f"  WebSocket端口: {config.websocket_port}")
    print(f"  調試模式: {config.debug}")
    
    return config

def print_system_info(engine: MirrorEngine):
    """打印系統信息"""
    status = engine.get_status()
    
    print("\n📊 系統狀態:")
    print(f"  會話ID: {status['session_id']}")
    print(f"  引擎狀態: {status['status']}")
    print(f"  同步次數: {status['sync_count']}")
    print(f"  活躍任務: {status['active_tasks']}")
    
    print("\n🔧 組件狀態:")
    components = status['components']
    for component, enabled in components.items():
        icon = "✅" if enabled else "❌"
        print(f"  {icon} {component.replace('_', ' ').title()}")
    
    print(f"\n🌐 WebSocket服務: ws://localhost:{engine.config.websocket_port}")
    print("💡 提示: 可以通過WebSocket連接來與Mirror系統交互")

def create_sample_config():
    """創建示例配置文件"""
    sample_config = {
        "enabled": True,
        "auto_sync": True,
        "sync_interval": 5,
        "debug": False,
        "websocket_port": 8765,
        "claude_integration": True,
        "local_adapters": ["macos", "linux", "wsl"],
        "remote_endpoints": [
            {
                "type": "ec2",
                "host": "your-ec2-instance.com",
                "port": 22,
                "username": "ubuntu",
                "key_file": "/path/to/your/key.pem"
            }
        ]
    }
    
    config_file = "mirror_config.json"
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(sample_config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 示例配置文件已創建: {config_file}")
        print("💡 請編輯配置文件後重新運行")
        
    except Exception as e:
        print(f"❌ 創建配置文件失敗: {e}")

async def test_mirror_system():
    """測試Mirror系統"""
    print("🧪 運行Mirror系統測試...")
    
    # 創建測試配置
    config = MirrorConfig(
        enabled=True,
        auto_sync=False,  # 測試時禁用自動同步
        debug=True
    )
    
    engine = MirrorEngine(config)
    
    try:
        # 啟動引擎
        print("🚀 啟動測試引擎...")
        success = await engine.start()
        
        if not success:
            print("❌ 測試引擎啟動失敗")
            return False
        
        # 執行測試
        print("🔧 執行基本功能測試...")
        
        # 測試狀態獲取
        status = engine.get_status()
        assert status["status"] == "running", "引擎狀態錯誤"
        print("  ✅ 狀態獲取測試通過")
        
        # 測試手動同步
        sync_success = await engine.sync_now()
        assert sync_success, "手動同步失敗"
        print("  ✅ 手動同步測試通過")
        
        # 測試命令執行
        if engine.local_adapter_integration:
            result = await engine.execute_command("echo 'test'")
            assert "test" in str(result), "命令執行失敗"
            print("  ✅ 命令執行測試通過")
        
        # 測試Claude集成
        if engine.claude_integration:
            claude_result = await engine.execute_claude_command("Hello")
            assert claude_result.get("success") or "output" in claude_result, "Claude集成失敗"
            print("  ✅ Claude集成測試通過")
        
        print("🎉 所有測試通過！")
        
        # 停止引擎
        await engine.stop()
        print("✅ 測試完成，引擎已停止")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        
        try:
            await engine.stop()
        except:
            pass
        
        return False

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="PowerAutomation Mirror Code系統啟動器")
    parser.add_argument("--config", "-c", help="配置文件路徑")
    parser.add_argument("--debug", "-d", action="store_true", help="啟用調試模式")
    parser.add_argument("--test", "-t", action="store_true", help="運行測試模式")
    parser.add_argument("--create-config", action="store_true", help="創建示例配置文件")
    
    args = parser.parse_args()
    
    if args.create_config:
        create_sample_config()
        return
    
    if args.test:
        result = asyncio.run(test_mirror_system())
        sys.exit(0 if result else 1)
    else:
        result = asyncio.run(launch_mirror_system(args.config, args.debug))
        sys.exit(result)

if __name__ == "__main__":
    main()