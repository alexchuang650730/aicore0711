#!/usr/bin/env python3
"""
PowerAutomation v4.6.6 設備發現和自動配置系統
Device Discovery and Auto-Configuration System

功能特性：
1. 自動發現局域網內的macOS設備
2. 檢測當前設備信息和網絡配置
3. 智能生成部署目標配置
4. 支持SSH密鑰自動配置
5. 動態更新部署目標列表
"""

import asyncio
import json
import logging
import socket
import subprocess
import platform
import os
import pwd
import netifaces
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import ipaddress
import concurrent.futures

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DeviceInfo:
    """設備信息"""
    hostname: str
    ip_address: str
    username: str
    platform: str
    ssh_port: int = 22
    ssh_key_path: str = "~/.ssh/id_rsa"
    is_reachable: bool = False
    is_current_device: bool = False
    device_name: str = None
    network_interface: str = None

@dataclass
class NetworkInfo:
    """網絡信息"""
    interface_name: str
    ip_address: str
    subnet_mask: str
    network_cidr: str
    gateway: str
    is_active: bool = True

class DeviceDiscoveryManager:
    """設備發現管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_device = None
        self.discovered_devices = []
        self.network_interfaces = []
        
    async def initialize(self):
        """初始化設備發現管理器"""
        self.logger.info("🔍 初始化設備發現管理器")
        
        # 獲取當前設備信息
        await self._detect_current_device()
        
        # 掃描網絡接口
        await self._scan_network_interfaces()
        
        self.logger.info("✅ 設備發現管理器初始化完成")
    
    async def _detect_current_device(self):
        """檢測當前設備信息"""
        self.logger.info("📱 檢測當前設備信息...")
        
        try:
            # 獲取基本系統信息
            hostname = socket.gethostname()
            username = pwd.getpwuid(os.getuid()).pw_name
            platform_name = platform.system().lower()
            
            # 獲取主要IP地址
            primary_ip = await self._get_primary_ip_address()
            
            # 獲取設備名稱 (macOS)
            device_name = hostname
            if platform_name == "darwin":
                try:
                    result = subprocess.run(
                        ["scutil", "--get", "ComputerName"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        device_name = result.stdout.strip()
                except:
                    pass
            
            self.current_device = DeviceInfo(
                hostname=hostname,
                ip_address=primary_ip,
                username=username,
                platform=platform_name,
                is_current_device=True,
                device_name=device_name,
                is_reachable=True
            )
            
            self.logger.info(f"✅ 當前設備: {device_name} ({primary_ip})")
            
        except Exception as e:
            self.logger.error(f"檢測當前設備失敗: {e}")
            raise
    
    async def _get_primary_ip_address(self) -> str:
        """獲取主要IP地址"""
        try:
            # 方法1: 連接到外部地址獲取本地IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            try:
                # 方法2: 通過hostname獲取
                return socket.gethostbyname(socket.gethostname())
            except:
                # 方法3: 默認回環地址
                return "127.0.0.1"
    
    async def _scan_network_interfaces(self):
        """掃描網絡接口"""
        self.logger.info("🌐 掃描網絡接口...")
        
        try:
            interfaces = netifaces.interfaces()
            
            for interface in interfaces:
                # 跳過回環接口
                if interface.startswith('lo'):
                    continue
                
                addrs = netifaces.ifaddresses(interface)
                
                # 獲取IPv4地址
                if netifaces.AF_INET in addrs:
                    for addr_info in addrs[netifaces.AF_INET]:
                        ip_addr = addr_info.get('addr')
                        netmask = addr_info.get('netmask')
                        
                        if ip_addr and not ip_addr.startswith('127.'):
                            # 計算網絡CIDR
                            try:
                                network = ipaddress.IPv4Network(f"{ip_addr}/{netmask}", strict=False)
                                cidr = str(network)
                            except:
                                cidr = f"{ip_addr}/24"  # 默認子網
                            
                            # 獲取網關
                            gateway = None
                            try:
                                gateways = netifaces.gateways()
                                default_gateway = gateways.get('default')
                                if default_gateway and netifaces.AF_INET in default_gateway:
                                    gateway = default_gateway[netifaces.AF_INET][0]
                            except:
                                pass
                            
                            network_info = NetworkInfo(
                                interface_name=interface,
                                ip_address=ip_addr,
                                subnet_mask=netmask,
                                network_cidr=cidr,
                                gateway=gateway or "未知"
                            )
                            
                            self.network_interfaces.append(network_info)
                            
                            self.logger.info(f"📡 發現網絡接口: {interface} ({ip_addr}/{netmask})")
            
        except Exception as e:
            self.logger.error(f"掃描網絡接口失敗: {e}")
    
    async def discover_devices_in_network(self, target_networks: List[str] = None) -> List[DeviceInfo]:
        """發現網絡內的設備"""
        self.logger.info("🔍 開始發現網絡內的設備...")
        
        if not target_networks:
            # 使用當前網絡接口的網段
            target_networks = [ni.network_cidr for ni in self.network_interfaces]
        
        discovered_devices = []
        
        for network_cidr in target_networks:
            self.logger.info(f"🌐 掃描網段: {network_cidr}")
            
            try:
                network = ipaddress.IPv4Network(network_cidr, strict=False)
                
                # 並行掃描網段內的IP
                tasks = []
                for ip in network.hosts():
                    # 限制掃描範圍，避免掃描過多IP
                    if len(tasks) >= 254:  # 限制最多掃描254個IP
                        break
                    tasks.append(self._check_device_at_ip(str(ip)))
                
                # 並行執行設備檢查
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 收集有效的設備
                for result in results:
                    if isinstance(result, DeviceInfo) and result.is_reachable:
                        discovered_devices.append(result)
                        
            except Exception as e:
                self.logger.error(f"掃描網段 {network_cidr} 失敗: {e}")
        
        self.discovered_devices = discovered_devices
        self.logger.info(f"✅ 發現 {len(discovered_devices)} 個可達設備")
        
        return discovered_devices
    
    async def _check_device_at_ip(self, ip_address: str) -> Optional[DeviceInfo]:
        """檢查指定IP的設備"""
        try:
            # 檢查IP是否可達 (ping)
            ping_result = await self._ping_host(ip_address)
            if not ping_result:
                return None
            
            # 檢查SSH端口是否開放
            ssh_available = await self._check_ssh_port(ip_address)
            
            # 嘗試獲取設備信息
            hostname = await self._get_hostname(ip_address)
            
            # 判斷是否為當前設備
            is_current = (ip_address == self.current_device.ip_address if self.current_device else False)
            
            device_info = DeviceInfo(
                hostname=hostname or f"device-{ip_address.replace('.', '-')}",
                ip_address=ip_address,
                username="unknown",  # 需要用戶配置
                platform="unknown",  # 需要進一步檢測
                is_reachable=True,
                is_current_device=is_current
            )
            
            return device_info
            
        except Exception as e:
            # 靜默處理錯誤，避免日誌過多
            return None
    
    async def _ping_host(self, ip_address: str) -> bool:
        """Ping主機檢查可達性"""
        try:
            # macOS/Linux使用ping命令
            ping_cmd = ["ping", "-c", "1", "-W", "1000", ip_address]
            
            process = await asyncio.create_subprocess_exec(
                *ping_cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            
            returncode = await process.wait()
            return returncode == 0
            
        except:
            return False
    
    async def _check_ssh_port(self, ip_address: str, port: int = 22) -> bool:
        """檢查SSH端口是否開放"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip_address, port),
                timeout=2.0
            )
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False
    
    async def _get_hostname(self, ip_address: str) -> Optional[str]:
        """獲取主機名"""
        try:
            hostname = socket.gethostbyaddr(ip_address)[0]
            return hostname
        except:
            return None
    
    def generate_deployment_targets_config(self, 
                                         discovered_devices: List[DeviceInfo] = None,
                                         include_current_device: bool = True) -> Dict[str, Any]:
        """生成部署目標配置"""
        self.logger.info("📋 生成部署目標配置...")
        
        if discovered_devices is None:
            discovered_devices = self.discovered_devices
        
        targets = []
        
        # 添加當前設備
        if include_current_device and self.current_device:
            current_target = {
                "name": f"current_device_{self.current_device.hostname}",
                "host": self.current_device.ip_address,
                "username": self.current_device.username,
                "platform": self.current_device.platform,
                "ssh_key_path": "~/.ssh/id_rsa",
                "is_current_device": True,
                "device_name": self.current_device.device_name
            }
            targets.append(current_target)
        
        # 添加發現的其他設備
        for i, device in enumerate(discovered_devices):
            if device.is_current_device and include_current_device:
                continue  # 已經添加了當前設備
            
            target = {
                "name": f"device_{i+1}_{device.hostname}",
                "host": device.ip_address,
                "username": "admin",  # 默認用戶名，需要用戶修改
                "platform": "macos",  # 默認macOS，需要用戶確認
                "ssh_key_path": "~/.ssh/id_rsa",
                "is_current_device": device.is_current_device,
                "hostname": device.hostname
            }
            targets.append(target)
        
        config = {
            "deployment_targets": targets,
            "discovery_info": {
                "current_device": asdict(self.current_device) if self.current_device else None,
                "network_interfaces": [asdict(ni) for ni in self.network_interfaces],
                "total_discovered_devices": len(discovered_devices),
                "discovery_timestamp": str(asyncio.get_event_loop().time())
            },
            "configuration_notes": [
                "請確認每個設備的用戶名和SSH密鑰路徑",
                "確保SSH服務在目標設備上已啟用",
                "確認SSH密鑰已正確配置且可訪問",
                "根據實際情況調整平台類型 (macos/linux/windows)"
            ]
        }
        
        return config
    
    def save_deployment_config(self, config: Dict[str, Any], file_path: str = None) -> str:
        """保存部署配置到文件"""
        if file_path is None:
            file_path = "deployment_targets_config.json"
        
        config_path = Path(file_path)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"💾 部署配置已保存到: {config_path}")
        return str(config_path)
    
    def get_status(self) -> Dict[str, Any]:
        """獲取設備發現管理器狀態"""
        return {
            "component": "Device Discovery Manager",
            "version": "4.6.6",
            "current_device": asdict(self.current_device) if self.current_device else None,
            "network_interfaces": len(self.network_interfaces),
            "discovered_devices": len(self.discovered_devices),
            "capabilities": [
                "network_scanning",
                "device_discovery", 
                "ssh_detection",
                "auto_configuration",
                "config_generation"
            ],
            "supported_platforms": ["macos", "linux", "windows"]
        }

# 單例實例
device_discovery_manager = DeviceDiscoveryManager()

async def main():
    """主函數 - 設備發現演示"""
    print("🔍 PowerAutomation v4.6.6 設備發現系統")
    print("=" * 60)
    
    try:
        # 1. 初始化設備發現管理器
        print("🚀 階段1: 初始化設備發現管理器...")
        await device_discovery_manager.initialize()
        
        # 2. 顯示當前設備信息
        print("\n📱 當前設備信息:")
        current = device_discovery_manager.current_device
        if current:
            print(f"  🖥️ 設備名稱: {current.device_name}")
            print(f"  🌐 主機名: {current.hostname}")
            print(f"  📡 IP地址: {current.ip_address}")
            print(f"  👤 用戶名: {current.username}")
            print(f"  💻 平台: {current.platform}")
        
        # 3. 顯示網絡接口
        print("\n🌐 網絡接口信息:")
        for ni in device_discovery_manager.network_interfaces:
            print(f"  📡 {ni.interface_name}: {ni.ip_address}/{ni.subnet_mask}")
            print(f"    🌍 網段: {ni.network_cidr}")
            print(f"    🚪 網關: {ni.gateway}")
        
        # 4. 發現網絡內設備
        print("\n🔍 階段2: 發現網絡內設備...")
        discovered = await device_discovery_manager.discover_devices_in_network()
        
        if discovered:
            print(f"\n✅ 發現 {len(discovered)} 個設備:")
            for device in discovered:
                status = "🔵 當前設備" if device.is_current_device else "🟢 其他設備"
                print(f"  {status} {device.hostname} ({device.ip_address})")
        else:
            print("\n⚠️ 未發現其他設備")
        
        # 5. 生成部署配置
        print("\n📋 階段3: 生成部署配置...")
        config = device_discovery_manager.generate_deployment_targets_config()
        
        # 6. 保存配置
        config_file = device_discovery_manager.save_deployment_config(config)
        
        # 7. 顯示配置摘要
        print(f"\n📊 配置摘要:")
        print(f"  🎯 部署目標數: {len(config['deployment_targets'])}")
        print(f"  🌐 網絡接口數: {len(config['discovery_info']['network_interfaces'])}")
        print(f"  📱 發現設備數: {config['discovery_info']['total_discovered_devices']}")
        print(f"  💾 配置文件: {config_file}")
        
        # 8. 顯示部署目標
        print(f"\n🎯 部署目標列表:")
        for target in config['deployment_targets']:
            current_flag = " (當前設備)" if target.get('is_current_device') else ""
            print(f"  📱 {target['name']}: {target['host']}{current_flag}")
            print(f"    👤 用戶: {target['username']}")
            print(f"    💻 平台: {target['platform']}")
        
        # 9. 顯示配置說明
        print(f"\n📝 配置說明:")
        for note in config['configuration_notes']:
            print(f"  • {note}")
        
        print(f"\n🎉 設備發現完成!")
        print(f"✨ 請檢查 {config_file} 並根據實際情況調整配置")
        
        return 0
        
    except Exception as e:
        logger.error(f"設備發現過程中發生錯誤: {e}")
        print(f"💥 發現失敗: {e}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ 用戶中斷發現")
        exit(2)
    except Exception as e:
        print(f"\n💥 未預期的錯誤: {e}")
        exit(3)