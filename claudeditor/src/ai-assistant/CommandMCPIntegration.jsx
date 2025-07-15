import React, { useState, useEffect } from 'react';

/**
 * Command MCP 集成组件
 * 优先处理所有斜杠指令，包括 Claude Code 指令
 */
class CommandMCPIntegration {
  constructor() {
    this.apiBase = 'http://localhost:5001';
    this.commandHistory = [];
    this.isInitialized = false;
  }

  async initialize() {
    if (this.isInitialized) return;
    
    try {
      // 初始化 Command MCP 连接
      const response = await fetch(`${this.apiBase}/api/command/status`);
      if (response.ok) {
        this.isInitialized = true;
        console.log('✅ Command MCP 集成初始化成功');
      }
    } catch (error) {
      console.warn('⚠️ Command MCP 服务未启动，使用本地处理');
      this.isInitialized = false;
    }
  }

  /**
   * 检查是否为斜杠指令
   */
  isSlashCommand(message) {
    return message.trim().startsWith('/');
  }

  /**
   * 获取支持的斜杠指令列表
   */
  getSupportedCommands() {
    return [
      // K2 本地支持的指令 (22个)
      '/config', '/status', '/help', '/model', '/models', 
      '/clear', '/history', '/tools', '/version', '/exit', 
      '/quit', '/reset', '/theme', '/lang', '/api', 
      '/debug', '/export', '/import', '/cost', '/memory', 
      '/doctor', '/compact',
      
      // Mirror Code 代理的指令 (10个)
      '/add-dir', '/bug', '/init', '/login', '/logout', 
      '/mcp', '/permissions', '/pr_comments', '/review', 
      '/terminal-setup', '/vim'
    ];
  }

  /**
   * 优先处理斜杠指令
   */
  async handleSlashCommand(message, context = {}) {
    if (!this.isSlashCommand(message)) {
      return null; // 不是斜杠指令，返回 null 让其他处理器处理
    }

    try {
      // 优先使用 Command MCP 处理
      if (this.isInitialized) {
        return await this.handleViaCommandMCP(message, context);
      } else {
        // 降级到本地处理
        return await this.handleLocally(message, context);
      }
    } catch (error) {
      console.error('Command MCP 处理失败:', error);
      return {
        type: 'error',
        message: `指令处理失败: ${error.message}`,
        suggestion: '请检查 Command MCP 服务状态'
      };
    }
  }

  /**
   * 通过 Command MCP 服务处理指令
   */
  async handleViaCommandMCP(message, context) {
    const response = await fetch(`${this.apiBase}/api/command/slash`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        command: message,
        context: {
          ...context,
          timestamp: new Date().toISOString(),
          source: 'claudeditor'
        }
      })
    });

    if (!response.ok) {
      throw new Error(`Command MCP 服务错误: ${response.status}`);
    }

    const result = await response.json();
    
    // 记录到历史
    this.commandHistory.push({
      command: message,
      result: result,
      timestamp: new Date().toISOString(),
      source: 'command_mcp'
    });

    return this.formatCommandResult(result);
  }

  /**
   * 本地处理指令（降级方案）
   */
  async handleLocally(message, context) {
    const parts = message.trim().split(' ');
    const command = parts[0];
    const args = parts.slice(1);

    // 本地支持的基础指令
    const localHandlers = {
      '/help': () => this.handleLocalHelp(),
      '/status': () => this.handleLocalStatus(),
      '/version': () => this.handleLocalVersion(),
      '/clear': () => this.handleLocalClear(),
      '/history': () => this.handleLocalHistory()
    };

    if (localHandlers[command]) {
      const result = localHandlers[command](args);
      
      this.commandHistory.push({
        command: message,
        result: result,
        timestamp: new Date().toISOString(),
        source: 'local'
      });

      return this.formatCommandResult(result);
    }

    // 不支持的指令
    return {
      type: 'error',
      message: `本地不支持指令: ${command}`,
      suggestion: '请启动 Command MCP 服务以获得完整功能支持'
    };
  }

  /**
   * 格式化指令结果为统一格式
   */
  formatCommandResult(result) {
    if (result.error) {
      return {
        type: 'error',
        message: result.error,
        suggestion: result.suggestion || '使用 /help 查看可用指令'
      };
    }

    switch (result.type) {
      case 'config':
        return {
          type: 'config',
          title: '配置信息',
          content: this.formatConfigDisplay(result),
          data: result.config
        };

      case 'status':
        return {
          type: 'status',
          title: '系统状态',
          content: this.formatStatusDisplay(result),
          data: result
        };

      case 'help':
        return {
          type: 'help',
          title: '帮助信息',
          content: this.formatHelpDisplay(result),
          data: result.commands
        };

      case 'mirror_code_proxy':
        return {
          type: 'mirror_code',
          title: 'Mirror Code 代理结果',
          content: `✅ 通过 Mirror Code 转送到 Claude Code 处理\n\n${result.response}`,
          source: 'claude_code_via_mirror',
          executionTime: result.execution_time
        };

      default:
        return {
          type: 'command_result',
          title: '指令执行结果',
          content: result.message || JSON.stringify(result, null, 2),
          data: result
        };
    }
  }

  formatConfigDisplay(result) {
    if (result.key && result.value !== undefined) {
      return `配置项: ${result.key}\n值: ${JSON.stringify(result.value, null, 2)}`;
    }
    
    return `当前配置:\n${JSON.stringify(result.config, null, 2)}`;
  }

  formatStatusDisplay(result) {
    return `当前模型: ${result.current_model}
API 状态: ${result.api_status}
路由地址: ${result.router_url}
已执行指令: ${result.session_stats?.commands_executed || 0}
最后活动: ${result.last_activity}
启用工具: ${result.tools_enabled?.join(', ') || '无'}`;
  }

  formatHelpDisplay(result) {
    if (result.command && result.description) {
      return `指令: ${result.command}\n说明: ${result.description}`;
    }

    const commands = result.commands || {};
    return Object.entries(commands)
      .map(([cmd, desc]) => `${cmd} - ${desc}`)
      .join('\n');
  }

  handleLocalHelp() {
    return {
      type: 'help',
      message: 'ClaudeEditor 本地指令帮助',
      commands: {
        '/help': '显示帮助信息',
        '/status': '显示系统状态',
        '/version': '显示版本信息',
        '/clear': '清除对话历史',
        '/history': '显示指令历史'
      }
    };
  }

  handleLocalStatus() {
    return {
      type: 'status',
      current_model: 'local',
      api_status: 'local_mode',
      router_url: 'localhost',
      session_stats: {
        commands_executed: this.commandHistory.length
      },
      last_activity: new Date().toISOString(),
      tools_enabled: ['local_commands']
    };
  }

  handleLocalVersion() {
    return {
      type: 'version',
      message: 'ClaudeEditor v4.6.9.5 (本地模式)',
      claude_code_version: '4.6.9.5',
      command_mcp_version: 'local'
    };
  }

  handleLocalClear() {
    return {
      type: 'clear',
      message: '对话历史已清除'
    };
  }

  handleLocalHistory() {
    return {
      type: 'history',
      message: `指令历史 (${this.commandHistory.length} 条)`,
      data: this.commandHistory.slice(-10) // 最近10条
    };
  }

  /**
   * 获取指令历史
   */
  getCommandHistory() {
    return this.commandHistory;
  }

  /**
   * 清除指令历史
   */
  clearCommandHistory() {
    this.commandHistory = [];
  }
}

// 创建全局实例
const commandMCPIntegration = new CommandMCPIntegration();

// React Hook for Command MCP Integration
export const useCommandMCP = () => {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const initializeCommandMCP = async () => {
      await commandMCPIntegration.initialize();
      setIsReady(true);
    };

    initializeCommandMCP();
  }, []);

  return {
    isReady,
    handleSlashCommand: commandMCPIntegration.handleSlashCommand.bind(commandMCPIntegration),
    isSlashCommand: commandMCPIntegration.isSlashCommand.bind(commandMCPIntegration),
    getSupportedCommands: commandMCPIntegration.getSupportedCommands.bind(commandMCPIntegration),
    getCommandHistory: commandMCPIntegration.getCommandHistory.bind(commandMCPIntegration),
    clearCommandHistory: commandMCPIntegration.clearCommandHistory.bind(commandMCPIntegration)
  };
};

export default commandMCPIntegration;

