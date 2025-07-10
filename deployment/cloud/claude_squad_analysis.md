# Claude Squad 项目分析

## 项目概述
- **项目名称**: claude-squad
- **GitHub地址**: https://github.com/smtg-ai/claude-squad
- **Stars**: 2.6k
- **许可证**: AGPL-3.0
- **最新版本**: v1.0.8 (2025年6月30日)

## 核心功能
Claude Squad 是一个终端应用程序，用于管理多个AI终端代理，包括：
- Claude Code
- Codex
- Gemini
- Aider
- 其他本地代理

## 主要特性
1. **后台任务完成** - 包括yolo/自动接受模式
2. **多实例管理** - 在一个终端窗口中管理实例和任务
3. **变更审查** - 在应用变更前进行审查，在推送前检出变更
4. **隔离工作空间** - 每个任务都有自己的隔离git工作空间，避免冲突

## 技术架构
### 核心技术栈
- **tmux** - 为每个代理创建隔离的终端会话
- **git worktrees** - 隔离代码库，每个会话在自己的分支上工作
- **TUI界面** - 简单的文本用户界面用于导航和管理

### 项目结构
从GitHub页面可以看到的主要目录：
- `.github/workflows` - CI/CD工作流
- `app` - 应用程序核心代码
- `cmd` - 命令行接口
- `config` - 配置管理
- `daemon` - 守护进程
- `keys` - 按键处理
- `log` - 日志系统
- `session` - 会话管理
- `ui` - 用户界面
- `web` - Web组件

### 支持的AI助手
- Claude Code
- Codex (需要OPENAI_API_KEY)
- Gemini
- Aider

## 安装和使用
- 支持Homebrew安装
- 手动安装脚本
- 命令行工具名称: `cs`
- 依赖: tmux, gh

## 核心命令
- `n` - 创建新会话
- `N` - 创建带提示的新会话
- `D` - 删除选定会话
- `↵/o` - 附加到选定会话
- `s` - 提交并推送分支到GitHub
- `c` - 检出（提交变更并暂停会话）
- `r` - 恢复暂停的会话

