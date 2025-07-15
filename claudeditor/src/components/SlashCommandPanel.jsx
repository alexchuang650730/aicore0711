import React, { useState, useEffect } from 'react';
import './SlashCommandPanel.css';

const SlashCommandPanel = ({ onCommandExecute, visible = true }) => {
  const [commands, setCommands] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCommand, setSelectedCommand] = useState(null);

  // Claude Code 斜槓指令定義
  const claudeCodeCommands = [
    {
      command: '/config',
      description: '配置管理',
      usage: '/config [set key value | get key | reset]',
      examples: ['/config get api.baseUrl', '/config set ui.theme dark', '/config reset'],
      category: '配置'
    },
    {
      command: '/status',
      description: '查看當前狀態和統計信息',
      usage: '/status',
      examples: ['/status'],
      category: '狀態'
    },
    {
      command: '/help',
      description: '顯示幫助信息',
      usage: '/help [command]',
      examples: ['/help', '/help config'],
      category: '幫助'
    },
    {
      command: '/model',
      description: '切換模型',
      usage: '/model [model_name]',
      examples: ['/model', '/model kimi-k2-instruct', '/model claude-3-sonnet'],
      category: '模型'
    },
    {
      command: '/models',
      description: '顯示可用模型列表',
      usage: '/models',
      examples: ['/models'],
      category: '模型'
    },
    {
      command: '/clear',
      description: '清除對話歷史',
      usage: '/clear',
      examples: ['/clear'],
      category: '會話'
    },
    {
      command: '/history',
      description: '顯示命令歷史',
      usage: '/history',
      examples: ['/history'],
      category: '會話'
    },
    {
      command: '/tools',
      description: '工具管理',
      usage: '/tools [enable/disable tool_name]',
      examples: ['/tools', '/tools enable Bash', '/tools disable WebFetch'],
      category: '工具'
    },
    {
      command: '/version',
      description: '顯示版本信息',
      usage: '/version',
      examples: ['/version'],
      category: '系統'
    },
    {
      command: '/exit',
      description: '退出Claude Code',
      usage: '/exit',
      examples: ['/exit'],
      category: '系統'
    },
    {
      command: '/quit',
      description: '退出Claude Code',
      usage: '/quit',
      examples: ['/quit'],
      category: '系統'
    },
    {
      command: '/reset',
      description: '重置所有設定',
      usage: '/reset',
      examples: ['/reset'],
      category: '系統'
    },
    {
      command: '/theme',
      description: '切換主題',
      usage: '/theme [dark/light]',
      examples: ['/theme', '/theme dark', '/theme light'],
      category: 'UI'
    },
    {
      command: '/lang',
      description: '切換語言',
      usage: '/lang [zh-TW/zh-CN/en]',
      examples: ['/lang', '/lang zh-TW', '/lang en'],
      category: 'UI'
    },
    {
      command: '/api',
      description: 'API配置',
      usage: '/api [baseUrl/timeout/retryCount] [value]',
      examples: ['/api', '/api baseUrl http://localhost:8765/v1', '/api timeout 30000'],
      category: '配置'
    },
    {
      command: '/debug',
      description: '調試模式切換',
      usage: '/debug',
      examples: ['/debug'],
      category: '開發'
    },
    {
      command: '/export',
      description: '導出配置',
      usage: '/export [config/history]',
      examples: ['/export config', '/export history'],
      category: '數據'
    },
    {
      command: '/import',
      description: '導入配置',
      usage: '/import [config/history] [file_path]',
      examples: ['/import config ./config.json'],
      category: '數據'
    }
  ];

  useEffect(() => {
    setCommands(claudeCodeCommands);
  }, []);

  const filteredCommands = commands.filter(cmd => 
    cmd.command.toLowerCase().includes(searchTerm.toLowerCase()) ||
    cmd.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    cmd.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const groupedCommands = filteredCommands.reduce((groups, cmd) => {
    const category = cmd.category;
    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push(cmd);
    return groups;
  }, {});

  const handleCommandClick = (command) => {
    setSelectedCommand(command);
  };

  const handleExecuteCommand = (commandText) => {
    if (onCommandExecute) {
      onCommandExecute(commandText);
    }
  };

  const getCategoryColor = (category) => {
    const colors = {
      '配置': '#4CAF50',
      '狀態': '#2196F3',
      '幫助': '#FF9800',
      '模型': '#9C27B0',
      '會話': '#00BCD4',
      '工具': '#607D8B',
      '系統': '#F44336',
      'UI': '#8BC34A',
      '開發': '#FFC107',
      '數據': '#795548'
    };
    return colors[category] || '#666';
  };

  if (!visible) return null;

  return (
    <div className="slash-command-panel">
      <div className="panel-header">
        <h3>🔧 Claude Code 斜槓指令</h3>
        <div className="search-container">
          <input
            type="text"
            placeholder="搜索指令..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>
      </div>

      <div className="panel-content">
        <div className="commands-grid">
          <div className="commands-list">
            {Object.entries(groupedCommands).map(([category, categoryCommands]) => (
              <div key={category} className="command-category">
                <div 
                  className="category-header"
                  style={{ borderLeftColor: getCategoryColor(category) }}
                >
                  <span 
                    className="category-indicator"
                    style={{ backgroundColor: getCategoryColor(category) }}
                  ></span>
                  {category} ({categoryCommands.length})
                </div>
                <div className="category-commands">
                  {categoryCommands.map((cmd, index) => (
                    <div
                      key={index}
                      className={`command-item ${selectedCommand?.command === cmd.command ? 'selected' : ''}`}
                      onClick={() => handleCommandClick(cmd)}
                    >
                      <div className="command-name">{cmd.command}</div>
                      <div className="command-description">{cmd.description}</div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {selectedCommand && (
            <div className="command-details">
              <div className="details-header">
                <h4>{selectedCommand.command}</h4>
                <span 
                  className="command-category-badge"
                  style={{ backgroundColor: getCategoryColor(selectedCommand.category) }}
                >
                  {selectedCommand.category}
                </span>
              </div>
              
              <div className="details-content">
                <div className="detail-section">
                  <h5>描述</h5>
                  <p>{selectedCommand.description}</p>
                </div>
                
                <div className="detail-section">
                  <h5>用法</h5>
                  <code>{selectedCommand.usage}</code>
                </div>
                
                <div className="detail-section">
                  <h5>範例</h5>
                  <div className="examples">
                    {selectedCommand.examples.map((example, index) => (
                      <div key={index} className="example-item">
                        <code 
                          className="example-code"
                          onClick={() => handleExecuteCommand(example)}
                          title="點擊執行"
                        >
                          {example}
                        </code>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="panel-footer">
        <div className="status-info">
          <span className="status-indicator active"></span>
          <span>Command MCP 已啟用</span>
          <span className="separator">|</span>
          <span>支援 {commands.length} 個指令</span>
          <span className="separator">|</span>
          <span>🔄 Mirror Code 代理已啟用</span>
        </div>
      </div>
    </div>
  );
};

export default SlashCommandPanel;