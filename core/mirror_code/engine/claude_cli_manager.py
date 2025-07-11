#!/usr/bin/env python3
"""
Claude CLI Manager - Claude CLI管理器
管理Claude CLI的安裝、配置和執行
"""

import asyncio
import logging
import subprocess
import shutil
import os
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class ClaudeCLIStatus(Enum):
    """Claude CLI狀態"""
    NOT_INSTALLED = "not_installed"
    INSTALLING = "installing"
    INSTALLED = "installed"
    ERROR = "error"

class ClaudeCLIManager:
    """Claude CLI管理器"""
    
    def __init__(self):
        self.status = ClaudeCLIStatus.NOT_INSTALLED
        self.claude_version = None
        self.installation_path = None
        self.is_installed = False
        self.last_check_time = None
        
    async def check_installation_status(self) -> Dict[str, Any]:
        """檢查Claude CLI安裝狀態"""
        try:
            # 檢查claude命令是否存在
            claude_path = shutil.which('claude')
            
            if claude_path:
                self.installation_path = claude_path
                
                # 獲取版本信息
                result = await self._run_command(['claude', '--version'])
                
                if result['success']:
                    self.claude_version = result['output'].strip()
                    self.is_installed = True
                    self.status = ClaudeCLIStatus.INSTALLED
                    
                    return {
                        "installed": True,
                        "version": self.claude_version,
                        "path": self.installation_path,
                        "status": self.status.value
                    }
            
            # Claude CLI未安裝
            self.is_installed = False
            self.status = ClaudeCLIStatus.NOT_INSTALLED
            
            return {
                "installed": False,
                "version": None,
                "path": None,
                "status": self.status.value
            }
            
        except Exception as e:
            logger.error(f"檢查Claude CLI狀態失敗: {e}")
            self.status = ClaudeCLIStatus.ERROR
            
            return {
                "installed": False,
                "error": str(e),
                "status": self.status.value
            }
    
    async def install_claude_cli(self) -> bool:
        """安裝Claude CLI"""
        if self.status == ClaudeCLIStatus.INSTALLING:
            logger.warning("Claude CLI正在安裝中")
            return False
        
        print("🔄 開始安裝Claude CLI...")
        self.status = ClaudeCLIStatus.INSTALLING
        
        try:
            # 檢查npm是否可用
            npm_result = await self._run_command(['which', 'npm'])
            if not npm_result['success']:
                print("❌ 需要安裝npm才能安裝Claude CLI")
                self.status = ClaudeCLIStatus.ERROR
                return False
            
            # 使用npm安裝Claude CLI
            print("📦 使用npm安裝Claude CLI...")
            install_result = await self._run_command([
                'npm', 'install', '-g', '@anthropic-ai/claude-cli'
            ], timeout=120)
            
            if not install_result['success']:
                print(f"❌ Claude CLI安裝失敗: {install_result['output']}")
                self.status = ClaudeCLIStatus.ERROR
                return False
            
            # 驗證安裝
            print("🔍 驗證Claude CLI安裝...")
            verification = await self.check_installation_status()
            
            if verification['installed']:
                print(f"✅ Claude CLI安裝成功: {verification['version']}")
                
                # 測試基本功能
                test_result = await self.test_claude_cli()
                if test_result:
                    print("✅ Claude CLI功能測試通過")
                else:
                    print("⚠️ Claude CLI功能測試失敗，但安裝成功")
                
                return True
            else:
                print("❌ Claude CLI安裝驗證失敗")
                self.status = ClaudeCLIStatus.ERROR
                return False
                
        except Exception as e:
            logger.error(f"Claude CLI安裝失敗: {e}")
            self.status = ClaudeCLIStatus.ERROR
            return False
    
    async def test_claude_cli(self) -> bool:
        """測試Claude CLI功能"""
        if not self.is_installed:
            return False
        
        try:
            # 測試help命令
            result = await self._run_command(['claude', '--help'])
            if result['success']:
                return True
            
            # 如果有API key，測試實際功能
            test_result = await self._run_command([
                'claude', '--model', 'test', 'Hello, Claude!'
            ])
            
            return test_result['success']
            
        except Exception as e:
            logger.error(f"Claude CLI測試失敗: {e}")
            return False
    
    async def execute_claude_command(self, args: List[str]) -> Dict[str, Any]:
        """執行Claude命令"""
        if not self.is_installed:
            return {
                "success": False,
                "error": "Claude CLI未安裝"
            }
        
        try:
            command = ['claude'] + args
            result = await self._run_command(command)
            
            return {
                "success": result['success'],
                "output": result['output'],
                "error": result.get('error', ''),
                "return_code": result['return_code']
            }
            
        except Exception as e:
            logger.error(f"執行Claude命令失敗: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _run_command(self, command: List[str], timeout: int = 30) -> Dict[str, Any]:
        """運行命令"""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            return {
                "success": process.returncode == 0,
                "output": stdout.decode('utf-8', errors='ignore'),
                "error": stderr.decode('utf-8', errors='ignore'),
                "return_code": process.returncode
            }
            
        except asyncio.TimeoutError:
            try:
                process.kill()
            except:
                pass
            
            return {
                "success": False,
                "error": f"命令執行超時 ({timeout}s)",
                "return_code": -1
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "return_code": -1
            }
    
    def get_status(self) -> Dict[str, Any]:
        """獲取狀態"""
        return {
            "status": self.status.value,
            "is_installed": self.is_installed,
            "claude_version": self.claude_version,
            "installation_path": self.installation_path,
            "last_check_time": self.last_check_time
        }
    
    async def update_claude_cli(self) -> bool:
        """更新Claude CLI"""
        if not self.is_installed:
            return await self.install_claude_cli()
        
        try:
            print("🔄 更新Claude CLI...")
            
            update_result = await self._run_command([
                'npm', 'update', '-g', '@anthropic-ai/claude-cli'
            ], timeout=120)
            
            if update_result['success']:
                # 重新檢查版本
                await self.check_installation_status()
                print(f"✅ Claude CLI已更新到: {self.claude_version}")
                return True
            else:
                print(f"❌ Claude CLI更新失敗: {update_result['error']}")
                return False
                
        except Exception as e:
            logger.error(f"Claude CLI更新失敗: {e}")
            return False
    
    async def uninstall_claude_cli(self) -> bool:
        """卸載Claude CLI"""
        if not self.is_installed:
            return True
        
        try:
            print("🗑️ 卸載Claude CLI...")
            
            uninstall_result = await self._run_command([
                'npm', 'uninstall', '-g', '@anthropic-ai/claude-cli'
            ])
            
            if uninstall_result['success']:
                self.is_installed = False
                self.status = ClaudeCLIStatus.NOT_INSTALLED
                self.claude_version = None
                self.installation_path = None
                print("✅ Claude CLI已卸載")
                return True
            else:
                print(f"❌ Claude CLI卸載失敗: {uninstall_result['error']}")
                return False
                
        except Exception as e:
            logger.error(f"Claude CLI卸載失敗: {e}")
            return False