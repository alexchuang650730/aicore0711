#!/usr/bin/env python3
"""
ClaudEditor 4.4.0 Mac版本打包工具
基于PowerAutomation AICore + ag-ui协议
"""

import os
import sys
import shutil
import tarfile
import json
import subprocess
from datetime import datetime
from pathlib import Path

class MacPackageBuilder:
    def __init__(self):
        self.version = "4.4.0"
        self.build_date = datetime.now().strftime("%Y%m%d-%H%M")
        self.base_dir = Path(__file__).parent
        self.package_dir = self.base_dir / "package"
        self.output_dir = self.base_dir / "release"
        
    def create_package_structure(self):
        """创建Mac包结构"""
        print("🏗️ 创建Mac包结构...")
        
        # 清理并创建目录
        if self.package_dir.exists():
            shutil.rmtree(self.package_dir)
        self.package_dir.mkdir(parents=True)
        
        # 创建标准Mac应用结构
        app_dir = self.package_dir / "ClaudEditor.app"
        contents_dir = app_dir / "Contents"
        macos_dir = contents_dir / "MacOS"
        resources_dir = contents_dir / "Resources"
        
        for dir_path in [app_dir, contents_dir, macos_dir, resources_dir]:
            dir_path.mkdir(parents=True)
            
        return app_dir, contents_dir, macos_dir, resources_dir
    
    def copy_core_components(self, resources_dir):
        """复制核心组件"""
        print("📦 复制PowerAutomation AICore组件...")
        
        # 复制核心组件
        core_src = Path("/home/ubuntu/aicore0707/core")
        core_dst = resources_dir / "core"
        if core_src.exists():
            shutil.copytree(core_src, core_dst)
            
        # 复制ClaudEditor UI
        ui_src = Path("/home/ubuntu/aicore0707/claudeditor/claudeditor-ui")
        ui_dst = resources_dir / "claudeditor-ui"
        if ui_src.exists():
            # 构建生产版本
            self.build_ui_production(ui_src, ui_dst)
        
        # 复制配置文件
        config_files = [
            "claude.api.config.json",
            "memory.config.json", 
            "collaboration.config.json",
            "agui.protocol.json"
        ]
        
        config_dir = resources_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        for config_file in config_files:
            self.create_config_file(config_dir / config_file, config_file)
    
    def build_ui_production(self, src_dir, dst_dir):
        """构建生产版本UI"""
        print("🎨 构建ClaudEditor UI生产版本...")
        
        try:
            # 进入源目录并构建
            os.chdir(src_dir)
            subprocess.run(["npm", "run", "build"], check=True)
            
            # 复制构建结果
            dist_dir = src_dir / "dist"
            if dist_dir.exists():
                shutil.copytree(dist_dir, dst_dir)
            else:
                # 如果没有dist目录，复制源代码
                shutil.copytree(src_dir, dst_dir, ignore=shutil.ignore_patterns('node_modules', '.git'))
                
        except subprocess.CalledProcessError:
            print("⚠️ UI构建失败，使用开发版本")
            shutil.copytree(src_dir, dst_dir, ignore=shutil.ignore_patterns('node_modules', '.git'))
    
    def create_config_file(self, file_path, config_type):
        """创建配置文件"""
        configs = {
            "claude.api.config.json": {
                "api_key": "${CLAUDE_API_KEY}",
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 4096,
                "temperature": 0.7,
                "timeout": 30
            },
            "memory.config.json": {
                "enabled": True,
                "storage_path": "~/Library/Application Support/ClaudEditor/memory",
                "max_memories": 10000,
                "cleanup_interval": 86400,
                "importance_threshold": 0.3
            },
            "collaboration.config.json": {
                "enabled": True,
                "max_agents": 10,
                "collaboration_types": ["peer_to_peer", "hierarchical", "swarm", "pipeline"],
                "message_timeout": 30,
                "knowledge_sharing": True
            },
            "agui.protocol.json": {
                "version": "1.0.0",
                "enabled": True,
                "component_library": "shadcn/ui",
                "theme_support": True,
                "responsive_design": True,
                "auto_optimization": True
            }
        }
        
        with open(file_path, 'w') as f:
            json.dump(configs.get(config_type, {}), f, indent=2)
    
    def create_info_plist(self, contents_dir):
        """创建Info.plist文件"""
        print("📄 创建Info.plist...")
        
        info_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>ClaudEditor</string>
    <key>CFBundleDisplayName</key>
    <string>ClaudEditor 4.4</string>
    <key>CFBundleIdentifier</key>
    <string>com.powerautomation.claudeditor</string>
    <key>CFBundleVersion</key>
    <string>{self.version}</string>
    <key>CFBundleShortVersionString</key>
    <string>{self.version}</string>
    <key>CFBundleExecutable</key>
    <string>claudeditor</string>
    <key>CFBundleIconFile</key>
    <string>claudeditor.icns</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>CLED</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSSupportsAutomaticGraphicsSwitching</key>
    <true/>
    <key>CFBundleDocumentTypes</key>
    <array>
        <dict>
            <key>CFBundleTypeExtensions</key>
            <array>
                <string>py</string>
                <string>js</string>
                <string>ts</string>
                <string>jsx</string>
                <string>tsx</string>
                <string>md</string>
                <string>json</string>
                <string>yaml</string>
                <string>yml</string>
            </array>
            <key>CFBundleTypeName</key>
            <string>Source Code</string>
            <key>CFBundleTypeRole</key>
            <string>Editor</string>
            <key>LSHandlerRank</key>
            <string>Owner</string>
        </dict>
    </array>
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <true/>
    </dict>
</dict>
</plist>"""
        
        with open(contents_dir / "Info.plist", 'w') as f:
            f.write(info_plist)
    
    def create_launcher_script(self, macos_dir):
        """创建启动脚本"""
        print("🚀 创建启动脚本...")
        
        launcher_script = f"""#!/bin/bash
# ClaudEditor 4.4.0 Mac启动脚本
# PowerAutomation AICore + ag-ui协议

# 获取应用路径
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RESOURCES_DIR="$APP_DIR/Resources"

# 设置环境变量
export CLAUDEDITOR_VERSION="{self.version}"
export CLAUDEDITOR_BUILD="{self.build_date}"
export CLAUDEDITOR_HOME="$RESOURCES_DIR"
export PYTHONPATH="$RESOURCES_DIR/core:$PYTHONPATH"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    osascript -e 'display alert "Python 3 Required" message "ClaudEditor requires Python 3.8 or later. Please install Python from python.org" buttons {{"OK"}} default button "OK"'
    exit 1
fi

# 检查依赖
REQUIREMENTS_FILE="$RESOURCES_DIR/requirements.txt"
if [ -f "$REQUIREMENTS_FILE" ]; then
    python3 -m pip install -r "$REQUIREMENTS_FILE" --user --quiet
fi

# 启动ClaudEditor
cd "$RESOURCES_DIR"

# 检查是否有UI构建版本
if [ -d "$RESOURCES_DIR/claudeditor-ui/dist" ]; then
    # 启动生产版本
    python3 -m http.server 8080 --directory "$RESOURCES_DIR/claudeditor-ui/dist" &
    SERVER_PID=$!
    sleep 2
    open "http://localhost:8080"
elif [ -d "$RESOURCES_DIR/claudeditor-ui" ]; then
    # 启动开发版本
    cd "$RESOURCES_DIR/claudeditor-ui"
    if command -v npm &> /dev/null; then
        npm run dev --host &
        SERVER_PID=$!
        sleep 3
        open "http://localhost:5173"
    else
        osascript -e 'display alert "Node.js Required" message "Development mode requires Node.js. Please install from nodejs.org or use the built version." buttons {{"OK"}} default button "OK"'
        exit 1
    fi
else
    osascript -e 'display alert "UI Not Found" message "ClaudEditor UI components not found. Please reinstall the application." buttons {{"OK"}} default button "OK"'
    exit 1
fi

# 等待用户关闭
echo "ClaudEditor {self.version} is running..."
echo "Press Ctrl+C to stop"
wait $SERVER_PID
"""
        
        launcher_path = macos_dir / "claudeditor"
        with open(launcher_path, 'w') as f:
            f.write(launcher_script)
        
        # 设置执行权限
        os.chmod(launcher_path, 0o755)
    
    def create_requirements_file(self, resources_dir):
        """创建requirements.txt"""
        print("📋 创建requirements.txt...")
        
        requirements = """# ClaudEditor 4.4.0 Mac版本依赖
# PowerAutomation AICore + ag-ui协议

# 核心依赖
anthropic>=0.25.0
google-generativeai>=0.5.0
requests>=2.31.0
aiohttp>=3.9.0
asyncio-mqtt>=0.16.0

# AI和机器学习
numpy>=1.24.0
pandas>=2.0.0
scikit-learn>=1.3.0
transformers>=4.30.0

# Web和UI
fastapi>=0.100.0
uvicorn>=0.22.0
websockets>=11.0.0
jinja2>=3.1.0

# 数据处理
sqlite3
json5>=0.9.0
pyyaml>=6.0
toml>=0.10.0

# 系统集成
psutil>=5.9.0
watchdog>=3.0.0
keyring>=24.0.0

# Mac平台特定
pyobjc-core>=9.0.0
pyobjc-framework-Cocoa>=9.0.0
pyobjc-framework-Quartz>=9.0.0

# 开发和调试
pytest>=7.4.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.4.0
"""
        
        with open(resources_dir / "requirements.txt", 'w') as f:
            f.write(requirements)
    
    def create_documentation(self):
        """创建文档"""
        print("📚 创建文档...")
        
        docs_dir = self.base_dir / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        # 用户指南
        user_guide = """# ClaudEditor 4.4.0 用户指南

## 快速开始

### 1. 安装
1. 双击 `ClaudEditor_4.4.0_Mac.dmg`
2. 将ClaudEditor拖拽到Applications文件夹
3. 首次启动时，右键点击选择"打开"

### 2. 配置API密钥
```bash
# 方法1: 环境变量
export CLAUDE_API_KEY="your-claude-api-key"
export GEMINI_API_KEY="your-gemini-api-key"

# 方法2: 在应用设置中配置
```

### 3. 界面介绍

#### 左栏: Agent协同面板
- **实时状态**: 显示系统运行状态和统计
- **代码统计**: 今日处理量、准确率等指标
- **快速操作**: 新建任务、查看报告等
- **最近活动**: 最近编辑的文件和任务

#### 中栏: 代码编辑器
- **Monaco编辑器**: 专业的代码编辑体验
- **AI建议**: 实时代码优化和重构建议
- **记忆提示**: 基于用户偏好的智能提示
- **底部面板**: 终端、问题、输出、AI对话、协作

#### 右栏: AI助手
- **对话模式**: 与Claude/Gemini实时对话
- **记忆模式**: 查看和管理AI记忆
- **代理模式**: 多代理协同工作状态

## 核心功能

### AI编程助手
- **代码补全**: 智能代码补全和建议
- **错误检测**: 实时错误检测和修复建议
- **代码重构**: AI驱动的代码重构和优化
- **性能分析**: 代码性能分析和优化建议

### 记忆系统
- **学习偏好**: AI学习您的编程习惯和偏好
- **上下文记忆**: 记住项目上下文和历史对话
- **知识积累**: 积累编程知识和最佳实践
- **智能检索**: 基于当前任务智能检索相关记忆

### 多代理协作
- **任务分解**: 自动将复杂任务分解给不同代理
- **并行处理**: 多个代理同时工作提升效率
- **知识共享**: 代理间共享知识和经验
- **质量保证**: 多重检查确保代码质量

## 快捷键

### Mac快捷键
- `Cmd + Shift + A`: 打开AI助手
- `Cmd + Shift + C`: 代码补全
- `Cmd + Shift + M`: 打开记忆面板
- `Cmd + Shift + T`: 切换主题
- `Cmd + ,`: 打开设置

### 编辑器快捷键
- `Cmd + /`: 注释/取消注释
- `Cmd + D`: 选择下一个相同单词
- `Cmd + Shift + L`: 选择所有相同单词
- `Cmd + Shift + K`: 删除行
- `Alt + Shift + F`: 格式化代码

## 故障排除

### 常见问题

#### 1. 应用无法启动
- 检查macOS版本 (需要10.15+)
- 确保Python 3.8+已安装
- 检查网络连接

#### 2. AI功能不可用
- 验证API密钥配置
- 检查网络连接
- 查看控制台错误信息

#### 3. 性能问题
- 关闭不必要的标签页
- 清理AI记忆缓存
- 重启应用

### 日志位置
- 应用日志: `~/Library/Logs/ClaudEditor/`
- AI记忆: `~/Library/Application Support/ClaudEditor/memory/`
- 配置文件: `~/Library/Preferences/com.powerautomation.claudeditor/`

## 高级功能

### 自定义配置
编辑配置文件以自定义AI行为:
```json
{
  "claude": {
    "temperature": 0.7,
    "max_tokens": 4096
  },
  "memory": {
    "max_memories": 10000,
    "importance_threshold": 0.3
  }
}
```

### 插件开发
ClaudEditor支持插件扩展:
```python
from claudeditor.plugin import Plugin

class MyPlugin(Plugin):
    def activate(self):
        # 插件激活逻辑
        pass
```

## 支持

### 获取帮助
- GitHub: https://github.com/alexchuang650730/aicore0707
- 邮箱: support@powerautomation.ai
- 社区: https://community.powerautomation.ai

### 反馈问题
请在GitHub Issues中报告问题，包含:
- 操作系统版本
- ClaudEditor版本
- 错误信息和日志
- 重现步骤
"""
        
        with open(docs_dir / "user_guide.md", 'w') as f:
            f.write(user_guide)
    
    def create_release_package(self):
        """创建发布包"""
        print("📦 创建发布包...")
        
        self.output_dir.mkdir(exist_ok=True)
        
        # 创建tar.gz包
        package_name = f"ClaudEditor_{self.version}_Mac_{self.build_date}.tar.gz"
        package_path = self.output_dir / package_name
        
        with tarfile.open(package_path, "w:gz") as tar:
            tar.add(self.package_dir, arcname="ClaudEditor_4.4.0_Mac")
            tar.add(self.base_dir / "README.md", arcname="README.md")
            tar.add(self.base_dir / "RELEASE_NOTES.md", arcname="RELEASE_NOTES.md")
            tar.add(self.base_dir / "docs", arcname="docs")
            tar.add(self.base_dir / "mac_test_environment", arcname="mac_test_environment")
        
        return package_path
    
    def build(self):
        """执行完整构建流程"""
        print(f"🚀 开始构建ClaudEditor {self.version} Mac版本...")
        print(f"📅 构建时间: {self.build_date}")
        
        try:
            # 1. 创建包结构
            app_dir, contents_dir, macos_dir, resources_dir = self.create_package_structure()
            
            # 2. 复制核心组件
            self.copy_core_components(resources_dir)
            
            # 3. 创建Info.plist
            self.create_info_plist(contents_dir)
            
            # 4. 创建启动脚本
            self.create_launcher_script(macos_dir)
            
            # 5. 创建requirements.txt
            self.create_requirements_file(resources_dir)
            
            # 6. 创建文档
            self.create_documentation()
            
            # 7. 创建发布包
            package_path = self.create_release_package()
            
            print(f"✅ 构建完成!")
            print(f"📦 发布包: {package_path}")
            print(f"📊 包大小: {package_path.stat().st_size / 1024 / 1024:.1f} MB")
            
            return package_path
            
        except Exception as e:
            print(f"❌ 构建失败: {e}")
            return None

if __name__ == "__main__":
    builder = MacPackageBuilder()
    result = builder.build()
    
    if result:
        print(f"\n🎉 ClaudEditor {builder.version} Mac版本构建成功!")
        print(f"📦 发布包位置: {result}")
        print(f"\n📋 下一步:")
        print(f"1. 测试安装包")
        print(f"2. 创建DMG镜像")
        print(f"3. 代码签名和公证")
        print(f"4. 发布到GitHub Release")
    else:
        print("\n❌ 构建失败，请检查错误信息")
        sys.exit(1)

