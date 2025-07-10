# Local Adapter MCP - 端云一键部署本地适配器

## 🌟 概述

Local Adapter MCP 是 PowerAutomation 4.0 端云一键部署系统的核心组件，负责管理本地环境资源，提供跨平台终端支持，并与 Deployment MCP 协调实现真正的端云一体化部署。

## 🏗️ 架构设计

```
EC2 云端 ←→ Deployment MCP ←→ Local Adapter MCP ←→ 本地环境
```

### 核心组件

- **Local Adapter Engine**: 本地适配器引擎，统一管理本地资源
- **Platform Detector**: 智能平台检测器，自动识别操作系统
- **Command Adapter**: 跨平台命令适配器，统一命令接口
- **Terminal MCPs**: 平台特有终端适配器
  - macOS Terminal MCP
  - Windows Terminal MCP  
  - WSL Terminal MCP
  - Linux Terminal MCP
- **Deployment MCP Client**: 与云端部署协调器的通信客户端
- **Remote Environment Interface**: 标准化远程环境接口

## 🚀 核心特性

### 🌐 真正的跨平台支持
- **macOS**: Homebrew、Xcode、代码签名、Spotlight 搜索
- **Windows**: Winget、Visual Studio、PowerShell、Windows 服务
- **WSL**: 跨系统调用、网络桥接、文件系统桥接
- **Linux**: 多发行版包管理器、systemd、Docker 集成

### 🔧 智能适配和协调
- **自动平台检测**: 智能识别 macOS/Windows/Linux/WSL
- **命令自动适配**: ls↔dir, cat↔type, cp↔copy
- **路径格式转换**: Unix/Windows 路径自动转换
- **端云智能协调**: 基于资源状态的智能任务分配

### 🛡️ 企业级特性
- **标准化接口**: 符合 Deployment MCP 规范
- **完整的错误处理**: 多层级错误处理和恢复
- **详细的日志记录**: 完整的操作审计
- **性能监控**: 实时资源状态监控

## 📦 安装和配置

### 系统要求

- **Python**: 3.8+
- **操作系统**: macOS 10.15+, Windows 10+, Linux (Ubuntu 18.04+, CentOS 7+, etc.)
- **网络**: 能够访问 Deployment MCP 服务

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd aicore0707/core/components/local_adapter_mcp
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境**
```bash
cp config/config.example.json config/config.json
# 编辑配置文件
```

4. **运行测试**
```bash
python test_local_adapter_mcp.py
```

## 🔧 使用指南

### 基本使用

```python
from local_adapter_engine import LocalAdapterEngine

# 初始化本地适配器
adapter = LocalAdapterEngine()

# 获取平台能力
capabilities = await adapter.get_capabilities()
print(f"平台支持: {capabilities}")

# 执行跨平台命令
result = await adapter.execute_cross_platform_command(
    "list_files", 
    args=["/home/user"],
    platform="auto"  # 自动检测
)
```

### 平台特有功能

#### macOS 平台

```python
from platform.macos_terminal_mcp import MacOSTerminalMCP

macos_mcp = MacOSTerminalMCP()

# 代码签名
await macos_mcp.code_sign_app(
    app_path="/path/to/MyApp.app",
    identity="Developer ID Application: Company Name"
)

# Spotlight 搜索
results = await macos_mcp.spotlight_search("PowerAutomation")

# Homebrew 包管理
await macos_mcp.homebrew_install("node")
```

#### Windows 平台

```python
from platform.windows_terminal_mcp import WindowsTerminalMCP

windows_mcp = WindowsTerminalMCP()

# Winget 包管理
await windows_mcp.winget_install("Git.Git")
await windows_mcp.winget_upgrade(all_packages=True)

# Visual Studio 构建
await windows_mcp.vs_build_solution("MyProject.sln")

# Windows 服务管理
await windows_mcp.service_start("nginx")
```

#### WSL 平台

```python
from platform.wsl_terminal_mcp import WSLTerminalMCP

wsl_mcp = WSLTerminalMCP()

# 跨系统命令执行
await wsl_mcp.execute_windows_command("dir", ["C:\\Users"])

# 网络桥接
await wsl_mcp.setup_port_forwarding(
    linux_port=3000,
    windows_port=8080
)

# 文件系统桥接
await wsl_mcp.copy_file_to_windows(
    "/home/user/project.zip",
    "C:\\Users\\username\\Desktop\\project.zip"
)
```

#### Linux 平台

```python
from platform.linux_terminal_mcp import LinuxTerminalMCP

linux_mcp = LinuxTerminalMCP()

# 多发行版包管理（自动适配）
await linux_mcp.install_package("docker.io")  # Ubuntu: apt
await linux_mcp.install_package("docker")     # Arch: pacman

# systemd 服务管理
await linux_mcp.systemd_start_service("nginx")
await linux_mcp.systemd_enable_service("nginx")

# Docker 集成
await linux_mcp.docker_run(
    image="node:18",
    ports=["3000:3000"],
    volumes=["/host/data:/container/data"]
)
```

### Deployment MCP 集成

```python
from deployment_mcp_client import DeploymentMCPClient

# 创建客户端
client = DeploymentMCPClient(
    deployment_mcp_url="http://deployment-mcp:8080"
)

# 注册环境
await client.register_environment({
    "environment_id": "local_dev",
    "environment_type": "LOCAL",
    "platform": "macos",
    "capabilities": await adapter.get_capabilities()
})

# 发送心跳
await client.send_heartbeat()

# 接收部署任务
task = await client.receive_deployment_task()
if task:
    result = await adapter.execute_deployment_task(task)
    await client.report_deployment_result(task["task_id"], result)
```

## 📋 API 参考

### LocalAdapterEngine

#### 核心方法

- `get_capabilities() -> Dict[str, Any]`: 获取平台能力
- `get_status() -> Dict[str, Any]`: 获取当前状态
- `execute_cross_platform_command(command, args, platform) -> Dict[str, Any]`: 执行跨平台命令
- `get_resource_usage() -> Dict[str, Any]`: 获取资源使用情况

### Platform MCPs

#### 通用接口

所有平台 MCP 都实现以下接口：

- `execute_command(command, args, **kwargs) -> Dict[str, Any]`: 执行命令
- `get_capabilities() -> Dict[str, Any]`: 获取平台能力
- `get_status() -> Dict[str, Any]`: 获取状态信息

#### macOS Terminal MCP

**代码签名**
- `code_sign_app(app_path, identity, **kwargs) -> Dict[str, Any]`
- `verify_code_signature(app_path, **kwargs) -> Dict[str, Any]`
- `list_signing_identities() -> Dict[str, Any]`
- `notarize_app(app_path, apple_id, password, **kwargs) -> Dict[str, Any]`

**Spotlight 搜索**
- `spotlight_search(query, limit, content_types) -> Dict[str, Any]`
- `get_file_metadata(file_path, attributes) -> Dict[str, Any]`
- `spotlight_index_file(file_path) -> Dict[str, Any]`

**Homebrew 包管理**
- `homebrew_install(package, options) -> Dict[str, Any]`
- `homebrew_uninstall(package, force) -> Dict[str, Any]`
- `homebrew_search(query) -> Dict[str, Any]`
- `homebrew_list_installed() -> Dict[str, Any]`

#### Windows Terminal MCP

**Winget 包管理**
- `winget_search(query, source) -> Dict[str, Any]`
- `winget_install(package_id, version, source, silent) -> Dict[str, Any]`
- `winget_uninstall(package_id, silent) -> Dict[str, Any]`
- `winget_upgrade(package_id, all_packages) -> Dict[str, Any]`

**Visual Studio 集成**
- `vs_build_solution(solution_path, configuration, platform) -> Dict[str, Any]`
- `vs_clean_solution(solution_path, configuration) -> Dict[str, Any]`
- `vs_restore_packages(solution_path) -> Dict[str, Any]`

**Windows 服务管理**
- `service_start(service_name) -> Dict[str, Any]`
- `service_stop(service_name) -> Dict[str, Any]`
- `service_restart(service_name) -> Dict[str, Any]`
- `service_status(service_name) -> Dict[str, Any]`

#### WSL Terminal MCP

**跨系统调用**
- `execute_windows_command(command, args, use_powershell) -> Dict[str, Any]`
- `execute_windows_executable(exe_path, args, working_dir) -> Dict[str, Any]`
- `linux_to_windows_path(linux_path) -> str`
- `windows_to_linux_path(windows_path) -> str`

**网络桥接**
- `setup_port_forwarding(linux_port, windows_port, protocol) -> Dict[str, Any]`
- `remove_port_forwarding(windows_port) -> Dict[str, Any]`
- `list_port_forwardings() -> Dict[str, Any]`
- `test_network_connectivity(target, from_windows) -> Dict[str, Any]`

#### Linux Terminal MCP

**多发行版包管理**
- `install_package(package, options) -> Dict[str, Any]`
- `remove_package(package, options) -> Dict[str, Any]`
- `update_package_list() -> Dict[str, Any]`
- `upgrade_packages(package) -> Dict[str, Any]`
- `search_package(query) -> Dict[str, Any]`

**systemd 服务管理**
- `systemd_start_service(service_name) -> Dict[str, Any]`
- `systemd_stop_service(service_name) -> Dict[str, Any]`
- `systemd_restart_service(service_name) -> Dict[str, Any]`
- `systemd_enable_service(service_name) -> Dict[str, Any]`
- `systemd_service_status(service_name) -> Dict[str, Any]`

## 🧪 测试

### 运行测试

```bash
# 运行完整测试套件
python test_local_adapter_mcp.py

# 运行特定平台测试
python -m pytest tests/test_macos_mcp.py
python -m pytest tests/test_windows_mcp.py
python -m pytest tests/test_wsl_mcp.py
python -m pytest tests/test_linux_mcp.py
```

### 测试覆盖

- ✅ 平台检测和适配
- ✅ 跨平台命令执行
- ✅ 平台特有功能
- ✅ Deployment MCP 集成
- ✅ 错误处理和恢复
- ✅ 性能和资源监控

## 🔧 配置

### 配置文件结构

```json
{
  "deployment_mcp": {
    "url": "http://deployment-mcp:8080",
    "environment_id": "local_dev",
    "heartbeat_interval": 30,
    "retry_attempts": 3
  },
  "local_adapter": {
    "log_level": "INFO",
    "resource_monitoring": true,
    "performance_tracking": true
  },
  "platform_specific": {
    "macos": {
      "homebrew_auto_update": true,
      "spotlight_indexing": true
    },
    "windows": {
      "winget_auto_upgrade": false,
      "service_monitoring": true
    },
    "wsl": {
      "port_forwarding_range": "8000-9000",
      "auto_path_conversion": true
    },
    "linux": {
      "package_manager_auto_detect": true,
      "systemd_monitoring": true
    }
  }
}
```

## 🚀 部署指南

### 开发环境部署

1. **本地开发**
```bash
# 启动本地适配器
python -m local_adapter_engine --config config/dev.json

# 启动测试模式
python -m local_adapter_engine --test-mode
```

2. **与 Deployment MCP 集成**
```bash
# 连接到开发环境的 Deployment MCP
python -m local_adapter_engine --deployment-mcp-url http://dev-deployment-mcp:8080
```

### 生产环境部署

1. **系统服务安装**
```bash
# 安装为系统服务（Linux/macOS）
sudo ./scripts/install_service.sh

# Windows 服务安装
./scripts/install_windows_service.ps1
```

2. **Docker 部署**
```bash
# 构建镜像
docker build -t local-adapter-mcp .

# 运行容器
docker run -d \
  --name local-adapter-mcp \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd)/config:/app/config \
  local-adapter-mcp
```

## 🔍 故障排除

### 常见问题

1. **平台检测失败**
   - 检查操作系统版本支持
   - 确认必要的系统工具已安装

2. **Deployment MCP 连接失败**
   - 检查网络连接
   - 验证 Deployment MCP 服务状态
   - 检查认证配置

3. **平台特有功能不可用**
   - 检查相关工具安装状态
   - 验证权限配置
   - 查看详细错误日志

### 日志分析

```bash
# 查看详细日志
tail -f logs/local_adapter_mcp.log

# 按级别过滤
grep "ERROR" logs/local_adapter_mcp.log
grep "WARNING" logs/local_adapter_mcp.log
```

## 🤝 贡献指南

### 开发环境设置

1. **Fork 项目**
2. **创建开发分支**
```bash
git checkout -b feature/new-platform-support
```

3. **安装开发依赖**
```bash
pip install -r requirements-dev.txt
```

4. **运行测试**
```bash
python -m pytest tests/ -v
```

### 代码规范

- 遵循 PEP 8 代码风格
- 添加类型注解
- 编写完整的文档字符串
- 确保测试覆盖率 > 90%

### 提交流程

1. **运行完整测试套件**
2. **更新文档**
3. **提交 Pull Request**
4. **代码审查**

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 📞 支持

- **文档**: [完整文档](docs/)
- **问题报告**: [GitHub Issues](issues/)
- **讨论**: [GitHub Discussions](discussions/)

---

**Local Adapter MCP - 让端云部署真正一键完成！** 🚀

