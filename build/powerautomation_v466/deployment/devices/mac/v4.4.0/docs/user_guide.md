# ClaudEditor 4.4.0 用户指南

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
