import React, { useState, useEffect } from 'react';
import taskSyncService from '../services/TaskSyncService';

/**
 * 任务列表组件 - 支持多智能体开发和 Claude Code 双向沟通
 * 管理多个AI智能体的任务分配和协作
 */
const TaskList = ({ onTaskSelect, onAgentAssign }) => {
  const [tasks, setTasks] = useState([]);
  const [agents, setAgents] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [showNewTaskForm, setShowNewTaskForm] = useState(false);
  const [filter, setFilter] = useState('all'); // all, pending, in_progress, completed
  const [connectionStatus, setConnectionStatus] = useState({ isConnected: false });
  const [taskMessages, setTaskMessages] = useState({}); // 任务消息存储
  const [showTaskChat, setShowTaskChat] = useState(null); // 显示任务聊天的任务ID
  const [newMessage, setNewMessage] = useState(''); // 新消息输入

  // 初始化智能体列表
  useEffect(() => {
    const defaultAgents = [
      {
        id: 'claude',
        name: '🔵 Claude',
        type: 'claude',
        status: 'online',
        capabilities: ['代码生成', '代码审查', '文档编写', '调试'],
        currentTask: null,
        performance: { completed: 15, success_rate: 95 }
      },
      {
        id: 'kimi_k2',
        name: '🌙 Kimi K2',
        type: 'kimi',
        status: 'online',
        capabilities: ['中文处理', '复杂推理', '数据分析', '创意写作'],
        currentTask: null,
        performance: { completed: 12, success_rate: 92 }
      },
      {
        id: 'command_mcp',
        name: '⚡ Command MCP',
        type: 'command',
        status: 'online',
        capabilities: ['指令执行', '系统管理', '工具调用', '自动化'],
        currentTask: null,
        performance: { completed: 28, success_rate: 98 }
      },
      {
        id: 'zen_workflow',
        name: '🧘 Zen Workflow',
        type: 'workflow',
        status: 'online',
        capabilities: ['工作流编排', '任务调度', '状态管理', '监控'],
        currentTask: null,
        performance: { completed: 8, success_rate: 100 }
      },
      {
        id: 'xmasters',
        name: '🎯 X-Masters',
        type: 'expert',
        status: 'online',
        capabilities: ['专家分析', '质量保证', '性能优化', '架构设计'],
        currentTask: null,
        performance: { completed: 6, success_rate: 100 }
      },
      {
        id: 'claude_code',
        name: '🚀 Claude Code',
        type: 'claude_code',
        status: 'online',
        capabilities: ['项目管理', '代码生成', '自动化开发', '任务协调'],
        currentTask: null,
        performance: { completed: 20, success_rate: 96 }
      }
    ];
    setAgents(defaultAgents);

    // 初始化示例任务
    const sampleTasks = [
      {
        id: 'task_1',
        title: '实现用户认证系统',
        description: '创建完整的用户登录、注册和权限管理系统',
        priority: 'high',
        status: 'pending',
        assignedAgent: null,
        estimatedTime: '2小时',
        tags: ['前端', '后端', '安全'],
        subtasks: [
          { id: 'sub_1', title: '设计数据库模型', status: 'pending' },
          { id: 'sub_2', title: '实现API接口', status: 'pending' },
          { id: 'sub_3', title: '创建前端组件', status: 'pending' },
          { id: 'sub_4', title: '添加安全验证', status: 'pending' }
        ],
        createdAt: new Date().toISOString(),
        deadline: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        source: 'local'
      },
      {
        id: 'task_2',
        title: '优化代码性能',
        description: '分析并优化现有代码的性能瓶颈',
        priority: 'medium',
        status: 'in_progress',
        assignedAgent: 'xmasters',
        estimatedTime: '1.5小时',
        tags: ['性能', '优化'],
        subtasks: [
          { id: 'sub_5', title: '性能基准测试', status: 'completed' },
          { id: 'sub_6', title: '识别瓶颈', status: 'in_progress' },
          { id: 'sub_7', title: '实施优化', status: 'pending' }
        ],
        createdAt: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
        deadline: new Date(Date.now() + 12 * 60 * 60 * 1000).toISOString(),
        progress: 40,
        source: 'local'
      }
    ];
    setTasks(sampleTasks);
  }, []);

  // 初始化任务同步服务
  useEffect(() => {
    const initializeTaskSync = async () => {
      try {
        const success = await taskSyncService.initialize();
        if (success) {
          setConnectionStatus({ isConnected: true });
          console.log('✅ 任务同步服务已连接');
        }
      } catch (error) {
        console.error('任务同步服务初始化失败:', error);
        setConnectionStatus({ isConnected: false, error: error.message });
      }
    };

    initializeTaskSync();

    // 添加任务监听器
    const taskListener = (eventType, data) => {
      console.log('📨 收到任务事件:', eventType, data);
      
      switch (eventType) {
        case 'task_created':
        case 'task_synced':
          setTasks(prev => {
            const existingIndex = prev.findIndex(t => t.id === data.id);
            if (existingIndex >= 0) {
              // 更新现有任务
              const updated = [...prev];
              updated[existingIndex] = { ...updated[existingIndex], ...data };
              return updated;
            } else {
              // 添加新任务
              return [data, ...prev];
            }
          });
          break;
        
        case 'task_updated':
          setTasks(prev => prev.map(task => 
            task.id === data.id ? { ...task, ...data } : task
          ));
          break;
        
        case 'task_assigned':
          setTasks(prev => prev.map(task => 
            task.id === data.id ? { ...task, assignedAgent: data.assignedAgent, status: 'in_progress' } : task
          ));
          break;
        
        case 'task_completed':
          setTasks(prev => prev.map(task => 
            task.id === data.id ? { ...task, status: 'completed', progress: 100 } : task
          ));
          break;
        
        case 'task_message':
          setTaskMessages(prev => ({
            ...prev,
            [data.task_id]: [...(prev[data.task_id] || []), data]
          }));
          break;
        
        case 'open_file_request':
          handleOpenFileRequest(data);
          break;
        
        case 'edit_code_request':
          handleEditCodeRequest(data);
          break;
        
        case 'run_command_request':
          handleRunCommandRequest(data);
          break;
        
        case 'show_diff_request':
          handleShowDiffRequest(data);
          break;
      }
    };

    taskSyncService.addTaskListener(taskListener);

    // 清理函数
    return () => {
      taskSyncService.removeTaskListener(taskListener);
    };
  }, []);

  // 处理 Claude Code 请求
  const handleOpenFileRequest = (data) => {
    console.log('📂 Claude Code 请求打开文件:', data.file_path);
    // 这里可以触发编辑器打开文件
    if (onTaskSelect) {
      onTaskSelect({
        type: 'open_file',
        filePath: data.file_path,
        taskId: data.task_id
      });
    }
    
    // 发送响应
    taskSyncService.respondToClaudeCodeRequest(data.request_id, 'success', {
      message: '文件已在 ClaudeEditor 中打开'
    });
  };

  const handleEditCodeRequest = (data) => {
    console.log('✏️ Claude Code 请求编辑代码:', data);
    if (onTaskSelect) {
      onTaskSelect({
        type: 'edit_code',
        filePath: data.file_path,
        changes: data.changes,
        taskId: data.task_id
      });
    }
    
    taskSyncService.respondToClaudeCodeRequest(data.request_id, 'success', {
      message: '代码编辑请求已处理'
    });
  };

  const handleRunCommandRequest = (data) => {
    console.log('⚡ Claude Code 请求执行命令:', data.command);
    // 这里可以集成终端执行
    taskSyncService.respondToClaudeCodeRequest(data.request_id, 'success', {
      message: '命令执行请求已处理',
      output: '模拟命令输出...'
    });
  };

  const handleShowDiffRequest = (data) => {
    console.log('🔍 Claude Code 请求显示差异:', data);
    if (onTaskSelect) {
      onTaskSelect({
        type: 'show_diff',
        before: data.before,
        after: data.after,
        taskId: data.task_id
      });
    }
    
    taskSyncService.respondToClaudeCodeRequest(data.request_id, 'success', {
      message: '差异视图已显示'
    });
  };

  // 过滤任务
  const filteredTasks = tasks.filter(task => {
    if (filter === 'all') return true;
    return task.status === filter;
  });

  // 获取优先级颜色
  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return '#ff4757';
      case 'medium': return '#ffa502';
      case 'low': return '#2ed573';
      default: return '#747d8c';
    }
  };

  // 获取状态颜色
  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return '#747d8c';
      case 'in_progress': return '#3742fa';
      case 'completed': return '#2ed573';
      case 'blocked': return '#ff4757';
      default: return '#747d8c';
    }
  };

  // 获取任务来源图标
  const getSourceIcon = (source) => {
    switch (source) {
      case 'claude_code': return '🚀';
      case 'local': return '💻';
      default: return '📋';
    }
  };

  // 创建新任务
  const createNewTask = async () => {
    if (!newTaskTitle.trim()) return;

    const newTask = {
      id: `task_${Date.now()}`,
      title: newTaskTitle,
      description: '',
      priority: 'medium',
      status: 'pending',
      assignedAgent: null,
      estimatedTime: '1小时',
      tags: [],
      subtasks: [],
      createdAt: new Date().toISOString(),
      deadline: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      source: 'local'
    };

    setTasks(prev => [newTask, ...prev]);
    setNewTaskTitle('');
    setShowNewTaskForm(false);

    // 如果连接到 Claude Code，同步任务
    if (connectionStatus.isConnected) {
      try {
        await taskSyncService.createTask(newTask);
        console.log('✅ 任务已同步到 Claude Code');
      } catch (error) {
        console.error('同步任务到 Claude Code 失败:', error);
      }
    }
  };

  // 发送任务消息
  const sendTaskMessage = async (taskId) => {
    if (!newMessage.trim()) return;

    const message = {
      id: Date.now(),
      task_id: taskId,
      message: newMessage,
      sender: 'claudeditor',
      timestamp: new Date().toISOString(),
      type: 'comment'
    };

    // 本地添加消息
    setTaskMessages(prev => ({
      ...prev,
      [taskId]: [...(prev[taskId] || []), message]
    }));

    // 发送到 Claude Code
    if (connectionStatus.isConnected) {
      try {
        await taskSyncService.sendTaskMessage(taskId, newMessage);
        console.log('✅ 消息已发送到 Claude Code');
      } catch (error) {
        console.error('发送消息失败:', error);
      }
    }

    setNewMessage('');
  };

  // 选择任务
  const selectTask = (task) => {
    setSelectedTask(task);
    if (onTaskSelect) {
      onTaskSelect(task);
    }
  };

  // 获取智能体信息
  const getAgentInfo = (agentId) => {
    return agents.find(agent => agent.id === agentId);
  };

  return (
    <div style={{
      width: '350px',
      height: '100%',
      backgroundColor: '#f8f9fa',
      borderRight: '1px solid #e9ecef',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Header */}
      <div style={{
        padding: '15px',
        backgroundColor: '#1e3a8a',
        color: 'white',
        borderBottom: '1px solid #e9ecef'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '16px' }}>🎯 多智能体任务管理</h3>
            <p style={{ margin: '4px 0 0 0', fontSize: '12px', opacity: 0.9 }}>
              PowerAutomation v4.6.9.5 - 协同开发
            </p>
          </div>
          <div style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: connectionStatus.isConnected ? '#2ed573' : '#ff4757',
            title: connectionStatus.isConnected ? 'Claude Code 已连接' : 'Claude Code 未连接'
          }} />
        </div>
      </div>

      {/* Connection Status */}
      {!connectionStatus.isConnected && (
        <div style={{
          padding: '8px 15px',
          backgroundColor: '#fff3cd',
          borderBottom: '1px solid #e9ecef',
          fontSize: '11px',
          color: '#856404'
        }}>
          ⚠️ Claude Code 未连接 - 仅本地任务管理
        </div>
      )}

      {/* Filter Tabs */}
      <div style={{
        display: 'flex',
        backgroundColor: 'white',
        borderBottom: '1px solid #e9ecef'
      }}>
        {[
          { key: 'all', label: '全部', count: tasks.length },
          { key: 'pending', label: '待处理', count: tasks.filter(t => t.status === 'pending').length },
          { key: 'in_progress', label: '进行中', count: tasks.filter(t => t.status === 'in_progress').length },
          { key: 'completed', label: '已完成', count: tasks.filter(t => t.status === 'completed').length }
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            style={{
              flex: 1,
              padding: '8px 4px',
              border: 'none',
              backgroundColor: filter === tab.key ? '#e3f2fd' : 'transparent',
              color: filter === tab.key ? '#1976d2' : '#666',
              fontSize: '11px',
              cursor: 'pointer',
              borderBottom: filter === tab.key ? '2px solid #1976d2' : 'none'
            }}
          >
            {tab.label} ({tab.count})
          </button>
        ))}
      </div>

      {/* New Task Button */}
      <div style={{ padding: '10px', backgroundColor: 'white', borderBottom: '1px solid #e9ecef' }}>
        {!showNewTaskForm ? (
          <button
            onClick={() => setShowNewTaskForm(true)}
            style={{
              width: '100%',
              padding: '8px',
              backgroundColor: '#1e3a8a',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            ➕ 创建新任务
          </button>
        ) : (
          <div style={{ display: 'flex', gap: '5px' }}>
            <input
              type="text"
              value={newTaskTitle}
              onChange={(e) => setNewTaskTitle(e.target.value)}
              placeholder="输入任务标题..."
              style={{
                flex: 1,
                padding: '6px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '12px'
              }}
              onKeyPress={(e) => e.key === 'Enter' && createNewTask()}
              autoFocus
            />
            <button
              onClick={createNewTask}
              style={{
                padding: '6px 10px',
                backgroundColor: '#2ed573',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              ✓
            </button>
            <button
              onClick={() => setShowNewTaskForm(false)}
              style={{
                padding: '6px 10px',
                backgroundColor: '#ff4757',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              ✕
            </button>
          </div>
        )}
      </div>

      {/* Task List */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        backgroundColor: 'white'
      }}>
        {filteredTasks.map(task => {
          const agent = getAgentInfo(task.assignedAgent);
          const hasMessages = taskMessages[task.id] && taskMessages[task.id].length > 0;
          
          return (
            <div key={task.id}>
              <div
                onClick={() => selectTask(task)}
                style={{
                  padding: '12px',
                  borderBottom: '1px solid #f0f0f0',
                  cursor: 'pointer',
                  backgroundColor: selectedTask?.id === task.id ? '#e3f2fd' : 'white',
                  borderLeft: selectedTask?.id === task.id ? '3px solid #1976d2' : 'none'
                }}
              >
                {/* Task Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                    <span style={{ marginRight: '4px', fontSize: '12px' }}>
                      {getSourceIcon(task.source)}
                    </span>
                    <h4 style={{
                      margin: 0,
                      fontSize: '13px',
                      fontWeight: 'bold',
                      color: '#333',
                      flex: 1
                    }}>
                      {task.title}
                    </h4>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    {hasMessages && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowTaskChat(showTaskChat === task.id ? null : task.id);
                        }}
                        style={{
                          width: '16px',
                          height: '16px',
                          borderRadius: '50%',
                          backgroundColor: '#1976d2',
                          color: 'white',
                          border: 'none',
                          fontSize: '10px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}
                      >
                        💬
                      </button>
                    )}
                    <div style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      backgroundColor: getPriorityColor(task.priority),
                      marginLeft: '4px'
                    }} />
                  </div>
                </div>

                {/* Task Description */}
                {task.description && (
                  <p style={{
                    margin: '0 0 6px 0',
                    fontSize: '11px',
                    color: '#666',
                    lineHeight: '1.3'
                  }}>
                    {task.description.length > 60 ? task.description.substring(0, 60) + '...' : task.description}
                  </p>
                )}

                {/* Task Status and Agent */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{
                    padding: '2px 6px',
                    borderRadius: '10px',
                    fontSize: '10px',
                    backgroundColor: getStatusColor(task.status),
                    color: 'white'
                  }}>
                    {task.status === 'pending' ? '待处理' :
                     task.status === 'in_progress' ? '进行中' :
                     task.status === 'completed' ? '已完成' : task.status}
                  </span>
                  {agent && (
                    <span style={{
                      fontSize: '10px',
                      color: '#666',
                      backgroundColor: '#f0f0f0',
                      padding: '2px 6px',
                      borderRadius: '10px'
                    }}>
                      {agent.name}
                    </span>
                  )}
                </div>

                {/* Progress Bar */}
                {task.progress !== undefined && (
                  <div style={{
                    width: '100%',
                    height: '4px',
                    backgroundColor: '#e9ecef',
                    borderRadius: '2px',
                    marginBottom: '6px'
                  }}>
                    <div style={{
                      width: `${task.progress}%`,
                      height: '100%',
                      backgroundColor: getStatusColor(task.status),
                      borderRadius: '2px',
                      transition: 'width 0.3s ease'
                    }} />
                  </div>
                )}

                {/* Task Meta */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '10px', color: '#999' }}>
                    ⏱️ {task.estimatedTime}
                  </span>
                  <span style={{ fontSize: '10px', color: '#999' }}>
                    📋 {task.subtasks?.length || 0} 子任务
                  </span>
                </div>

                {/* Tags */}
                {task.tags && task.tags.length > 0 && (
                  <div style={{ marginTop: '6px' }}>
                    {task.tags.map(tag => (
                      <span
                        key={tag}
                        style={{
                          display: 'inline-block',
                          padding: '1px 4px',
                          margin: '0 2px 2px 0',
                          fontSize: '9px',
                          backgroundColor: tag === 'Claude Code' ? '#e3f2fd' : '#e9ecef',
                          color: tag === 'Claude Code' ? '#1976d2' : '#666',
                          borderRadius: '8px'
                        }}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Task Chat */}
              {showTaskChat === task.id && (
                <div style={{
                  backgroundColor: '#f8f9fa',
                  borderBottom: '1px solid #e9ecef',
                  padding: '8px 12px'
                }}>
                  <div style={{
                    fontSize: '11px',
                    fontWeight: 'bold',
                    marginBottom: '6px',
                    color: '#333'
                  }}>
                    💬 任务沟通 {task.source === 'claude_code' && '(与 Claude Code 同步)'}
                  </div>
                  
                  {/* Messages */}
                  <div style={{
                    maxHeight: '120px',
                    overflowY: 'auto',
                    marginBottom: '6px'
                  }}>
                    {(taskMessages[task.id] || []).map(msg => (
                      <div key={msg.id} style={{
                        fontSize: '10px',
                        marginBottom: '4px',
                        padding: '4px 6px',
                        backgroundColor: msg.sender === 'claudeditor' ? '#e3f2fd' : '#f0f0f0',
                        borderRadius: '4px'
                      }}>
                        <div style={{ fontWeight: 'bold', color: '#666' }}>
                          {msg.sender === 'claudeditor' ? '📝 ClaudeEditor' : '🚀 Claude Code'}
                        </div>
                        <div>{msg.message}</div>
                      </div>
                    ))}
                  </div>

                  {/* Message Input */}
                  <div style={{ display: 'flex', gap: '4px' }}>
                    <input
                      type="text"
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      placeholder="输入消息..."
                      style={{
                        flex: 1,
                        padding: '4px 6px',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '11px'
                      }}
                      onKeyPress={(e) => e.key === 'Enter' && sendTaskMessage(task.id)}
                    />
                    <button
                      onClick={() => sendTaskMessage(task.id)}
                      style={{
                        padding: '4px 8px',
                        backgroundColor: '#1976d2',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '11px'
                      }}
                    >
                      发送
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Agent Status Panel */}
      <div style={{
        backgroundColor: '#f8f9fa',
        borderTop: '1px solid #e9ecef',
        maxHeight: '200px',
        overflowY: 'auto'
      }}>
        <div style={{
          padding: '8px 12px',
          backgroundColor: '#e9ecef',
          fontSize: '12px',
          fontWeight: 'bold',
          color: '#333'
        }}>
          🤖 智能体状态 ({agents.filter(a => a.status === 'online').length}/{agents.length} 在线)
        </div>
        {agents.map(agent => (
          <div
            key={agent.id}
            style={{
              padding: '6px 12px',
              borderBottom: '1px solid #f0f0f0',
              fontSize: '11px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 'bold' }}>{agent.name}</span>
              <span style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                backgroundColor: agent.status === 'online' ? '#2ed573' : '#ff4757'
              }} />
            </div>
            <div style={{ color: '#666', marginTop: '2px' }}>
              {agent.currentTask ? `执行中: ${tasks.find(t => t.id === agent.currentTask)?.title || '未知任务'}` : '空闲中'}
            </div>
            <div style={{ color: '#999', fontSize: '10px', marginTop: '2px' }}>
              完成: {agent.performance.completed} | 成功率: {agent.performance.success_rate}%
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TaskList;

