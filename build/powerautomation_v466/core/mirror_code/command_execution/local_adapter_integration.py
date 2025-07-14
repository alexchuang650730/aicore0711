#!/usr/bin/env python3
"""
Local Adapter Integration - 本地適配器集成
集成本地MCP適配器，提供跨平台命令執行能力
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
import platform

logger = logging.getLogger(__name__)

class LocalAdapterIntegration:
    """本地適配器集成"""
    
    def __init__(self):
        self.adapters = {}
        self.current_platform = self._detect_platform()
        self.is_initialized = False
        
    async def initialize(self, adapter_configs: List[str] = None):
        """初始化本地適配器"""
        print("🔧 初始化本地適配器集成...")
        
        try:
            # 導入本地適配器管理器
            from ....local_mcp_adapter_integration import LocalMCPIntegrationManager
            
            self.adapter_manager = LocalMCPIntegrationManager()
            init_result = await self.adapter_manager.initialize_all_adapters()
            
            if init_result.get("cross_platform_capability"):
                self.adapters = self.adapter_manager.adapters
                self.is_initialized = True
                print(f"✅ 本地適配器初始化成功: {len(self.adapters)}個適配器")
            else:
                print("⚠️ 本地適配器初始化部分成功")
                
        except Exception as e:
            logger.error(f"本地適配器初始化失敗: {e}")
            # 創建基本適配器
            await self._create_basic_adapter()
    
    async def _create_basic_adapter(self):
        """創建基本適配器"""
        self.basic_adapter = True
        self.is_initialized = True
        print("✅ 基本適配器已創建")
    
    def _detect_platform(self) -> str:
        """檢測當前平台"""
        system = platform.system().lower()
        
        if system == "darwin":
            return "macos"
        elif system == "linux":
            # 檢測是否為WSL
            try:
                with open('/proc/version', 'r') as f:
                    if 'microsoft' in f.read().lower():
                        return "wsl"
            except:
                pass
            return "linux"
        elif system == "windows":
            return "windows"
        else:
            return "unknown"
    
    async def execute_command(self, command: str, platform: str = "auto") -> Dict[str, Any]:
        """執行命令"""
        if not self.is_initialized:
            return {"error": "適配器未初始化"}
        
        try:
            # 選擇平台
            target_platform = platform if platform != "auto" else self.current_platform
            
            # 使用適配器管理器執行命令
            if hasattr(self, 'adapter_manager') and self.adapter_manager:
                # 將平台字符串轉換為LocalPlatform枚舉
                from ....local_mcp_adapter_integration import LocalPlatform
                
                platform_map = {
                    "macos": LocalPlatform.MACOS,
                    "linux": LocalPlatform.LINUX,
                    "wsl": LocalPlatform.WSL
                }
                
                if target_platform in platform_map:
                    platform_enum = platform_map[target_platform]
                    result = await self.adapter_manager.execute_cross_platform_command(
                        platform_enum, command
                    )
                else:
                    return {"error": f"不支持的平台: {target_platform}"}
            else:
                # 使用基本適配器
                result = await self._execute_basic_command(command)
            
            return result
            
        except Exception as e:
            logger.error(f"命令執行失敗: {e}")
            return {"error": str(e)}
    
    async def _execute_basic_command(self, command: str) -> Dict[str, Any]:
        """基本命令執行"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "status": "success" if process.returncode == 0 else "failed",
                "return_code": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "platform": self.current_platform
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "platform": self.current_platform
            }
    
    def get_available_platforms(self) -> List[str]:
        """獲取可用平台"""
        if hasattr(self, 'adapter_manager') and self.adapter_manager:
            return [platform.value for platform in self.adapter_manager.adapters.keys()]
        else:
            return [self.current_platform]
    
    def get_status(self) -> Dict[str, Any]:
        """獲取狀態"""
        return {
            "initialized": self.is_initialized,
            "current_platform": self.current_platform,
            "available_platforms": self.get_available_platforms(),
            "adapter_count": len(self.adapters) if hasattr(self, 'adapters') else 0,
            "has_manager": hasattr(self, 'adapter_manager') and bool(self.adapter_manager)
        }