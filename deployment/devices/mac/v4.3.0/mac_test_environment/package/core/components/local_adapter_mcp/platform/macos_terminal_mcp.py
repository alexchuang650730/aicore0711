"""
macOS Terminal MCP Adapter - macOS终端MCP适配器
支持macOS平台特有的终端功能和工具

特性：Homebrew、Xcode工具链、Apple Silicon优化、代码签名等
"""

import asyncio
import subprocess
import os
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

class MacOSTerminalMCP:
    """macOS终端MCP适配器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.platform = "macos"
        
        # 检查macOS特有工具
        self.homebrew_available = self._check_homebrew()
        self.xcode_available = self._check_xcode_tools()
        self.apple_silicon = self._check_apple_silicon()
        
        self.logger.info(f"macOS终端MCP初始化完成 - Homebrew: {self.homebrew_available}, Xcode: {self.xcode_available}, Apple Silicon: {self.apple_silicon}")
    
    def _check_homebrew(self) -> bool:
        """检查Homebrew是否可用"""
        try:
            result = subprocess.run(["brew", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_xcode_tools(self) -> bool:
        """检查Xcode命令行工具是否可用"""
        try:
            result = subprocess.run(["xcode-select", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_apple_silicon(self) -> bool:
        """检查是否是Apple Silicon Mac"""
        try:
            result = subprocess.run(["uname", "-m"], 
                                  capture_output=True, text=True, timeout=5)
            return result.stdout.strip() == "arm64"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def execute_command(self, command: str, args: List[str] = None, 
                            working_dir: str = None, env: Dict[str, str] = None) -> Dict[str, Any]:
        """
        执行macOS命令
        
        Args:
            command: 要执行的命令
            args: 命令参数
            working_dir: 工作目录
            env: 环境变量
            
        Returns:
            Dict: 执行结果
        """
        args = args or []
        full_command = [command] + args
        
        try:
            self.logger.info(f"执行macOS命令: {' '.join(full_command)}")
            
            # 设置环境变量
            exec_env = os.environ.copy()
            if env:
                exec_env.update(env)
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env=exec_env
            )
            
            stdout, stderr = await process.communicate()
            
            result = {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "command": ' '.join(full_command),
                "working_dir": working_dir
            }
            
            if process.returncode != 0:
                self.logger.warning(f"命令执行失败: {result['stderr']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"执行命令失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": ' '.join(full_command),
                "working_dir": working_dir
            }
    
    # Homebrew相关方法
    async def brew_install(self, package: str, options: List[str] = None) -> Dict[str, Any]:
        """使用Homebrew安装包"""
        if not self.homebrew_available:
            return {"success": False, "error": "Homebrew不可用"}
        
        args = ["install", package]
        if options:
            args.extend(options)
        
        return await self.execute_command("brew", args)
    
    async def brew_uninstall(self, package: str, force: bool = False) -> Dict[str, Any]:
        """使用Homebrew卸载包"""
        if not self.homebrew_available:
            return {"success": False, "error": "Homebrew不可用"}
        
        args = ["uninstall", package]
        if force:
            args.append("--force")
        
        return await self.execute_command("brew", args)
    
    async def brew_update(self) -> Dict[str, Any]:
        """更新Homebrew"""
        if not self.homebrew_available:
            return {"success": False, "error": "Homebrew不可用"}
        
        return await self.execute_command("brew", ["update"])
    
    async def brew_upgrade(self, package: str = None) -> Dict[str, Any]:
        """升级Homebrew包"""
        if not self.homebrew_available:
            return {"success": False, "error": "Homebrew不可用"}
        
        args = ["upgrade"]
        if package:
            args.append(package)
        
        return await self.execute_command("brew", args)
    
    async def brew_search(self, query: str) -> Dict[str, Any]:
        """搜索Homebrew包"""
        if not self.homebrew_available:
            return {"success": False, "error": "Homebrew不可用"}
        
        return await self.execute_command("brew", ["search", query])
    
    async def brew_list(self, installed_only: bool = True) -> Dict[str, Any]:
        """列出Homebrew包"""
        if not self.homebrew_available:
            return {"success": False, "error": "Homebrew不可用"}
        
        args = ["list"]
        if installed_only:
            args.append("--versions")
        
        return await self.execute_command("brew", args)
    
    async def brew_info(self, package: str) -> Dict[str, Any]:
        """获取包信息"""
        if not self.homebrew_available:
            return {"success": False, "error": "Homebrew不可用"}
        
        return await self.execute_command("brew", ["info", package])
    
    # Xcode相关方法
    async def xcode_build(self, project_path: str, scheme: str = None, 
                         configuration: str = "Release", 
                         destination: str = None) -> Dict[str, Any]:
        """使用xcodebuild构建项目"""
        if not self.xcode_available:
            return {"success": False, "error": "Xcode命令行工具不可用"}
        
        args = ["-project", project_path]
        
        if scheme:
            args.extend(["-scheme", scheme])
        
        args.extend(["-configuration", configuration])
        
        if destination:
            args.extend(["-destination", destination])
        
        args.append("build")
        
        return await self.execute_command("xcodebuild", args)
    
    async def xcode_clean(self, project_path: str, scheme: str = None) -> Dict[str, Any]:
        """清理Xcode项目"""
        if not self.xcode_available:
            return {"success": False, "error": "Xcode命令行工具不可用"}
        
        args = ["-project", project_path]
        
        if scheme:
            args.extend(["-scheme", scheme])
        
        args.append("clean")
        
        return await self.execute_command("xcodebuild", args)
    
    async def xcode_test(self, project_path: str, scheme: str = None, 
                        destination: str = None) -> Dict[str, Any]:
        """运行Xcode测试"""
        if not self.xcode_available:
            return {"success": False, "error": "Xcode命令行工具不可用"}
        
        args = ["-project", project_path]
        
        if scheme:
            args.extend(["-scheme", scheme])
        
        if destination:
            args.extend(["-destination", destination])
        
        args.append("test")
        
        return await self.execute_command("xcodebuild", args)
    
    async def xcode_archive(self, project_path: str, scheme: str, 
                           archive_path: str) -> Dict[str, Any]:
        """创建Xcode归档"""
        if not self.xcode_available:
            return {"success": False, "error": "Xcode命令行工具不可用"}
        
        args = [
            "-project", project_path,
            "-scheme", scheme,
            "-archivePath", archive_path,
            "archive"
        ]
        
        return await self.execute_command("xcodebuild", args)
    
    # 代码签名相关方法
    async def codesign_app(self, app_path: str, identity: str, 
                          entitlements: str = None, deep: bool = True) -> Dict[str, Any]:
        """对应用进行代码签名"""
        args = ["--sign", identity]
        
        if deep:
            args.append("--deep")
        
        if entitlements:
            args.extend(["--entitlements", entitlements])
        
        args.append(app_path)
        
        return await self.execute_command("codesign", args)
    
    async def verify_signature(self, app_path: str, verbose: bool = False) -> Dict[str, Any]:
        """验证代码签名"""
        args = ["--verify"]
        
        if verbose:
            args.append("--verbose")
        
        args.append(app_path)
        
        return await self.execute_command("codesign", args)
    
    async def list_signing_identities(self) -> Dict[str, Any]:
        """列出可用的签名身份"""
        return await self.execute_command("security", ["find-identity", "-v", "-p", "codesigning"])
    
    # 系统信息方法
    async def get_system_info(self) -> Dict[str, Any]:
        """获取macOS系统信息"""
        try:
            # 获取系统版本
            version_result = await self.execute_command("sw_vers", ["-productVersion"])
            build_result = await self.execute_command("sw_vers", ["-buildVersion"])
            
            # 获取硬件信息
            hardware_result = await self.execute_command("system_profiler", ["SPHardwareDataType", "-json"])
            
            info = {
                "platform": "macos",
                "version": version_result.get("stdout", "").strip() if version_result.get("success") else "unknown",
                "build": build_result.get("stdout", "").strip() if build_result.get("success") else "unknown",
                "apple_silicon": self.apple_silicon,
                "homebrew_available": self.homebrew_available,
                "xcode_available": self.xcode_available
            }
            
            # 解析硬件信息
            if hardware_result.get("success"):
                try:
                    hardware_data = json.loads(hardware_result["stdout"])
                    if "SPHardwareDataType" in hardware_data:
                        hw_info = hardware_data["SPHardwareDataType"][0]
                        info.update({
                            "model": hw_info.get("machine_model", "unknown"),
                            "processor": hw_info.get("cpu_type", "unknown"),
                            "memory": hw_info.get("physical_memory", "unknown"),
                            "serial": hw_info.get("serial_number", "unknown")
                        })
                except json.JSONDecodeError:
                    pass
            
            return {"success": True, "info": info}
            
        except Exception as e:
            self.logger.error(f"获取系统信息失败: {e}")
            return {"success": False, "error": str(e)}
    
    # 文件系统方法
    async def spotlight_search(self, query: str, kind: str = None, 
                              limit: int = 10) -> Dict[str, Any]:
        """使用Spotlight搜索文件"""
        args = [query]
        
        if kind:
            args.extend(["-kind", kind])
        
        args.extend(["-count", str(limit)])
        
        return await self.execute_command("mdfind", args)
    
    async def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """获取文件元数据"""
        return await self.execute_command("mdls", [file_path])
    
    async def open_with_default_app(self, file_path: str) -> Dict[str, Any]:
        """使用默认应用打开文件"""
        return await self.execute_command("open", [file_path])
    
    async def open_with_app(self, file_path: str, app_name: str) -> Dict[str, Any]:
        """使用指定应用打开文件"""
        return await self.execute_command("open", ["-a", app_name, file_path])
    
    async def reveal_in_finder(self, file_path: str) -> Dict[str, Any]:
        """在Finder中显示文件"""
        return await self.execute_command("open", ["-R", file_path])
    
    # 网络方法
    async def get_network_info(self) -> Dict[str, Any]:
        """获取网络信息"""
        try:
            # 获取网络接口信息
            interfaces_result = await self.execute_command("networksetup", ["-listallhardwareports"])
            
            # 获取Wi-Fi信息
            wifi_result = await self.execute_command("networksetup", ["-getairportnetwork", "en0"])
            
            # 获取IP地址
            ip_result = await self.execute_command("ifconfig", ["en0"])
            
            return {
                "success": True,
                "interfaces": interfaces_result.get("stdout", "") if interfaces_result.get("success") else "",
                "wifi": wifi_result.get("stdout", "") if wifi_result.get("success") else "",
                "ip_info": ip_result.get("stdout", "") if ip_result.get("success") else ""
            }
            
        except Exception as e:
            self.logger.error(f"获取网络信息失败: {e}")
            return {"success": False, "error": str(e)}
    
    # 开发环境方法
    async def setup_development_environment(self, tools: List[str]) -> Dict[str, Any]:
        """设置开发环境"""
        results = {}
        
        for tool in tools:
            if tool == "homebrew" and not self.homebrew_available:
                # 安装Homebrew
                install_script = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
                result = await self.execute_command("bash", ["-c", install_script])
                results["homebrew"] = result
                
            elif tool == "xcode" and not self.xcode_available:
                # 安装Xcode命令行工具
                result = await self.execute_command("xcode-select", ["--install"])
                results["xcode"] = result
                
            elif tool in ["node", "python", "git", "docker"]:
                # 使用Homebrew安装工具
                if self.homebrew_available:
                    result = await self.brew_install(tool)
                    results[tool] = result
                else:
                    results[tool] = {"success": False, "error": "Homebrew不可用"}
        
        return {"success": True, "results": results}
    
    async def get_installed_apps(self) -> Dict[str, Any]:
        """获取已安装的应用列表"""
        return await self.execute_command("ls", ["/Applications"])
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """获取macOS平台能力"""
        return {
            "platform": "macos",
            "homebrew_available": self.homebrew_available,
            "xcode_available": self.xcode_available,
            "apple_silicon": self.apple_silicon,
            "supported_features": [
                "package_management",
                "code_signing",
                "spotlight_search",
                "xcode_build",
                "app_store_connect",
                "system_preferences",
                "finder_integration"
            ],
            "development_tools": [
                "xcode",
                "homebrew",
                "git",
                "node",
                "python",
                "docker",
                "cocoapods",
                "fastlane"
            ]
        }


            
            return result
            
        except Exception as e:
            self.logger.error(f"执行macOS命令失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": ' '.join(full_command)
            }
    
    # ==================== 代码签名功能 ====================
    
    async def code_sign_app(self, app_path: str, identity: str, 
                           entitlements_path: str = None, 
                           deep_sign: bool = True) -> Dict[str, Any]:
        """
        对应用进行代码签名
        
        Args:
            app_path: 应用路径
            identity: 签名身份
            entitlements_path: 权限文件路径
            deep_sign: 是否深度签名
            
        Returns:
            Dict: 签名结果
        """
        try:
            self.logger.info(f"开始代码签名: {app_path}")
            
            # 构建codesign命令
            args = ["--sign", identity, "--force"]
            
            if deep_sign:
                args.append("--deep")
            
            if entitlements_path:
                args.extend(["--entitlements", entitlements_path])
            
            args.append(app_path)
            
            result = await self.execute_command("codesign", args)
            
            if result["success"]:
                self.logger.info(f"代码签名成功: {app_path}")
                
                # 验证签名
                verify_result = await self.verify_code_signature(app_path)
                result["verification"] = verify_result
            
            return result
            
        except Exception as e:
            self.logger.error(f"代码签名失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "app_path": app_path
            }
    
    async def verify_code_signature(self, app_path: str, 
                                   deep_verify: bool = True) -> Dict[str, Any]:
        """
        验证代码签名
        
        Args:
            app_path: 应用路径
            deep_verify: 是否深度验证
            
        Returns:
            Dict: 验证结果
        """
        try:
            self.logger.info(f"验证代码签名: {app_path}")
            
            args = ["--verify", "--verbose"]
            
            if deep_verify:
                args.append("--deep")
            
            args.append(app_path)
            
            result = await self.execute_command("codesign", args)
            
            # 获取签名信息
            info_result = await self.get_code_signature_info(app_path)
            result["signature_info"] = info_result
            
            return result
            
        except Exception as e:
            self.logger.error(f"验证代码签名失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "app_path": app_path
            }
    
    async def get_code_signature_info(self, app_path: str) -> Dict[str, Any]:
        """
        获取代码签名信息
        
        Args:
            app_path: 应用路径
            
        Returns:
            Dict: 签名信息
        """
        try:
            result = await self.execute_command("codesign", 
                                              ["--display", "--verbose=4", app_path])
            
            if result["success"]:
                # 解析签名信息
                info = self._parse_signature_info(result["stderr"])
                return {
                    "success": True,
                    "info": info,
                    "raw_output": result["stderr"]
                }
            else:
                return result
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_signature_info(self, output: str) -> Dict[str, Any]:
        """解析签名信息输出"""
        info = {}
        
        for line in output.split('\n'):
            line = line.strip()
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                if key == "Identifier":
                    info["identifier"] = value
                elif key == "Authority":
                    if "authorities" not in info:
                        info["authorities"] = []
                    info["authorities"].append(value)
                elif key == "TeamIdentifier":
                    info["team_identifier"] = value
                elif key == "Sealed Resources":
                    info["sealed_resources"] = value
        
        return info
    
    async def list_signing_identities(self) -> Dict[str, Any]:
        """
        列出可用的签名身份
        
        Returns:
            Dict: 签名身份列表
        """
        try:
            result = await self.execute_command("security", 
                                              ["find-identity", "-v", "-p", "codesigning"])
            
            if result["success"]:
                identities = self._parse_identities(result["stdout"])
                return {
                    "success": True,
                    "identities": identities,
                    "count": len(identities)
                }
            else:
                return result
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_identities(self, output: str) -> List[Dict[str, str]]:
        """解析身份列表输出"""
        identities = []
        
        for line in output.split('\n'):
            line = line.strip()
            if ') ' in line and '"' in line:
                # 提取身份信息
                parts = line.split(') ', 1)
                if len(parts) == 2:
                    index = parts[0].strip()
                    name_part = parts[1]
                    
                    # 提取名称
                    if '"' in name_part:
                        name = name_part.split('"')[1]
                        identities.append({
                            "index": index,
                            "name": name,
                            "full_line": line
                        })
        
        return identities
    
    async def notarize_app(self, app_path: str, apple_id: str, 
                          password: str, team_id: str = None) -> Dict[str, Any]:
        """
        公证应用
        
        Args:
            app_path: 应用路径
            apple_id: Apple ID
            password: 应用专用密码
            team_id: 团队ID
            
        Returns:
            Dict: 公证结果
        """
        try:
            self.logger.info(f"开始公证应用: {app_path}")
            
            # 创建zip文件用于公证
            zip_path = f"{app_path}.zip"
            zip_result = await self.execute_command("ditto", 
                                                   ["-c", "-k", "--keepParent", app_path, zip_path])
            
            if not zip_result["success"]:
                return zip_result
            
            # 提交公证
            args = ["notarytool", "submit", zip_path, 
                   "--apple-id", apple_id, 
                   "--password", password,
                   "--wait"]
            
            if team_id:
                args.extend(["--team-id", team_id])
            
            result = await self.execute_command("xcrun", args)
            
            # 清理zip文件
            try:
                os.remove(zip_path)
            except:
                pass
            
            return result
            
        except Exception as e:
            self.logger.error(f"公证应用失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "app_path": app_path
            }
    
    # ==================== Spotlight 搜索功能 ====================
    
    async def spotlight_search(self, query: str, limit: int = 20, 
                              content_types: List[str] = None) -> Dict[str, Any]:
        """
        使用Spotlight搜索文件
        
        Args:
            query: 搜索查询
            limit: 结果数量限制
            content_types: 内容类型过滤
            
        Returns:
            Dict: 搜索结果
        """
        try:
            self.logger.info(f"Spotlight搜索: {query}")
            
            args = ["-name", query]
            
            if limit:
                args.extend(["-count", str(limit)])
            
            if content_types:
                for content_type in content_types:
                    args.extend(["-kind", content_type])
            
            result = await self.execute_command("mdfind", args)
            
            if result["success"]:
                files = [f.strip() for f in result["stdout"].split('\n') if f.strip()]
                return {
                    "success": True,
                    "files": files,
                    "count": len(files),
                    "query": query
                }
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"Spotlight搜索失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    async def get_file_metadata(self, file_path: str, 
                               attributes: List[str] = None) -> Dict[str, Any]:
        """
        获取文件元数据
        
        Args:
            file_path: 文件路径
            attributes: 要获取的属性列表
            
        Returns:
            Dict: 文件元数据
        """
        try:
            self.logger.info(f"获取文件元数据: {file_path}")
            
            args = [file_path]
            
            if attributes:
                for attr in attributes:
                    args.extend(["-name", attr])
            
            result = await self.execute_command("mdls", args)
            
            if result["success"]:
                metadata = self._parse_metadata(result["stdout"])
                return {
                    "success": True,
                    "metadata": metadata,
                    "file_path": file_path
                }
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"获取文件元数据失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }
    
    def _parse_metadata(self, output: str) -> Dict[str, Any]:
        """解析元数据输出"""
        metadata = {}
        
        for line in output.split('\n'):
            line = line.strip()
            if ' = ' in line:
                key, value = line.split(' = ', 1)
                key = key.strip()
                value = value.strip()
                
                # 移除引号
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith('(') and value.endswith(')'):
                    # 处理数组
                    value = value[1:-1].split(', ')
                    value = [v.strip('"') for v in value if v.strip()]
                
                metadata[key] = value
        
        return metadata
    
    async def spotlight_index_file(self, file_path: str) -> Dict[str, Any]:
        """
        强制Spotlight索引文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict: 索引结果
        """
        try:
            self.logger.info(f"强制索引文件: {file_path}")
            
            result = await self.execute_command("mdimport", [file_path])
            
            return result
            
        except Exception as e:
            self.logger.error(f"索引文件失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }
    
    async def search_by_content_type(self, content_type: str, 
                                   limit: int = 20) -> Dict[str, Any]:
        """
        按内容类型搜索
        
        Args:
            content_type: 内容类型 (如: image, document, application)
            limit: 结果数量限制
            
        Returns:
            Dict: 搜索结果
        """
        try:
            query = f"kMDItemContentType == '*{content_type}*'"
            
            args = [query]
            if limit:
                args.extend(["-count", str(limit)])
            
            result = await self.execute_command("mdfind", args)
            
            if result["success"]:
                files = [f.strip() for f in result["stdout"].split('\n') if f.strip()]
                return {
                    "success": True,
                    "files": files,
                    "count": len(files),
                    "content_type": content_type
                }
            else:
                return result
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content_type": content_type
            }
    
    # ==================== Homebrew 包管理增强 ====================
    
    async def homebrew_install(self, package: str, options: List[str] = None) -> Dict[str, Any]:
        """
        使用Homebrew安装包
        
        Args:
            package: 包名
            options: 安装选项
            
        Returns:
            Dict: 安装结果
        """
        try:
            args = ["install", package]
            if options:
                args.extend(options)
            
            result = await self.execute_command("brew", args)
            
            if result["success"]:
                self.logger.info(f"Homebrew安装成功: {package}")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "package": package
            }
    
    async def homebrew_uninstall(self, package: str, force: bool = False) -> Dict[str, Any]:
        """
        使用Homebrew卸载包
        
        Args:
            package: 包名
            force: 是否强制卸载
            
        Returns:
            Dict: 卸载结果
        """
        try:
            args = ["uninstall", package]
            if force:
                args.append("--force")
            
            result = await self.execute_command("brew", args)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "package": package
            }
    
    async def homebrew_update(self) -> Dict[str, Any]:
        """更新Homebrew"""
        try:
            result = await self.execute_command("brew", ["update"])
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def homebrew_upgrade(self, package: str = None) -> Dict[str, Any]:
        """
        升级包
        
        Args:
            package: 包名，如果为None则升级所有包
            
        Returns:
            Dict: 升级结果
        """
        try:
            args = ["upgrade"]
            if package:
                args.append(package)
            
            result = await self.execute_command("brew", args)
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "package": package
            }
    
    async def homebrew_search(self, query: str) -> Dict[str, Any]:
        """
        搜索包
        
        Args:
            query: 搜索查询
            
        Returns:
            Dict: 搜索结果
        """
        try:
            result = await self.execute_command("brew", ["search", query])
            
            if result["success"]:
                packages = [p.strip() for p in result["stdout"].split('\n') if p.strip()]
                return {
                    "success": True,
                    "packages": packages,
                    "count": len(packages),
                    "query": query
                }
            else:
                return result
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    async def homebrew_info(self, package: str) -> Dict[str, Any]:
        """
        获取包信息
        
        Args:
            package: 包名
            
        Returns:
            Dict: 包信息
        """
        try:
            result = await self.execute_command("brew", ["info", package])
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "package": package
            }
    
    async def homebrew_list_installed(self) -> Dict[str, Any]:
        """列出已安装的包"""
        try:
            result = await self.execute_command("brew", ["list"])
            
            if result["success"]:
                packages = [p.strip() for p in result["stdout"].split('\n') if p.strip()]
                return {
                    "success": True,
                    "packages": packages,
                    "count": len(packages)
                }
            else:
                return result
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== 系统信息和能力 ====================
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """获取macOS平台能力"""
        return {
            "platform": self.platform,
            "homebrew_available": self.homebrew_available,
            "xcode_available": self.xcode_available,
            "apple_silicon": self.apple_silicon,
            "supported_features": {
                "code_signing": True,
                "notarization": True,
                "spotlight_search": True,
                "homebrew_management": self.homebrew_available,
                "xcode_tools": self.xcode_available
            },
            "code_signing_capabilities": {
                "sign_applications": True,
                "verify_signatures": True,
                "list_identities": True,
                "notarize_apps": True
            },
            "spotlight_capabilities": {
                "file_search": True,
                "metadata_extraction": True,
                "content_type_search": True,
                "force_indexing": True
            },
            "homebrew_capabilities": {
                "install_packages": True,
                "uninstall_packages": True,
                "update_homebrew": True,
                "upgrade_packages": True,
                "search_packages": True,
                "package_info": True,
                "list_installed": True
            }
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态信息"""
        return {
            "platform": self.platform,
            "homebrew_available": self.homebrew_available,
            "xcode_available": self.xcode_available,
            "apple_silicon": self.apple_silicon,
            "ready": True
        }

