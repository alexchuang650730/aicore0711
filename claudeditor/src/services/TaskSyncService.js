/**
 * 任务同步服务
 * 实现 Claude Code 和 ClaudeEditor 之间的双向任务沟通
 */
class TaskSyncService {
  constructor() {
    this.claudeCodeEndpoint = 'http://localhost:5001';
    this.websocketUrl = 'ws://localhost:5002';
    this.websocket = null;
    this.isConnected = false;
    this.taskListeners = new Set();
    this.messageListeners = new Set();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000;
    
    // 任务状态映射
    this.taskStatusMap = {
      'created': 'pending',
      'assigned': 'in_progress',
      'in_progress': 'in_progress',
      'completed': 'completed',
      'failed': 'blocked',
      'cancelled': 'cancelled'
    };
  }

  /**
   * 初始化任务同步服务
   */
  async initialize() {
    try {
      // 建立 WebSocket 连接
      await this.connectWebSocket();
      
      // 同步现有任务
      await this.syncExistingTasks();
      
      console.log('✅ 任务同步服务初始化成功');
      return true;
    } catch (error) {
      console.error('❌ 任务同步服务初始化失败:', error);
      return false;
    }
  }

  /**
   * 建立 WebSocket 连接
   */
  connectWebSocket() {
    return new Promise((resolve, reject) => {
      try {
        this.websocket = new WebSocket(this.websocketUrl);
        
        this.websocket.onopen = () => {
          console.log('🔗 WebSocket 连接已建立');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          
          // 注册为 ClaudeEditor 客户端
          this.sendMessage({
            type: 'register',
            client: 'claudeditor',
            capabilities: ['task_management', 'code_editing', 'ui_interaction']
          });
          
          resolve();
        };

        this.websocket.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.handleIncomingMessage(message);
          } catch (error) {
            console.error('WebSocket 消息解析失败:', error);
          }
        };

        this.websocket.onclose = () => {
          console.log('🔌 WebSocket 连接已断开');
          this.isConnected = false;
          this.attemptReconnect();
        };

        this.websocket.onerror = (error) => {
          console.error('WebSocket 连接错误:', error);
          reject(error);
        };

        // 连接超时处理
        setTimeout(() => {
          if (!this.isConnected) {
            reject(new Error('WebSocket 连接超时'));
          }
        }, 5000);

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * 重连机制
   */
  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('❌ WebSocket 重连次数已达上限');
      return;
    }

    this.reconnectAttempts++;
    console.log(`🔄 尝试重连 WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    setTimeout(() => {
      this.connectWebSocket().catch(error => {
        console.error('重连失败:', error);
      });
    }, this.reconnectDelay);
  }

  /**
   * 处理传入消息
   */
  handleIncomingMessage(message) {
    console.log('📨 收到消息:', message);

    switch (message.type) {
      case 'task_created':
        this.handleTaskCreated(message.data);
        break;
      
      case 'task_updated':
        this.handleTaskUpdated(message.data);
        break;
      
      case 'task_assigned':
        this.handleTaskAssigned(message.data);
        break;
      
      case 'task_completed':
        this.handleTaskCompleted(message.data);
        break;
      
      case 'task_message':
        this.handleTaskMessage(message.data);
        break;
      
      case 'claude_code_request':
        this.handleClaudeCodeRequest(message.data);
        break;
      
      case 'sync_response':
        this.handleSyncResponse(message.data);
        break;
      
      default:
        console.log('未知消息类型:', message.type);
    }

    // 通知所有消息监听器
    this.messageListeners.forEach(listener => {
      try {
        listener(message);
      } catch (error) {
        console.error('消息监听器错误:', error);
      }
    });
  }

  /**
   * 处理新任务创建
   */
  handleTaskCreated(taskData) {
    const claudeEditorTask = this.convertClaudeCodeTaskToClaudeEditor(taskData);
    
    // 通知任务列表更新
    this.notifyTaskListeners('task_created', claudeEditorTask);
    
    // 发送确认消息
    this.sendMessage({
      type: 'task_received',
      taskId: taskData.id,
      client: 'claudeditor',
      timestamp: new Date().toISOString()
    });
  }

  /**
   * 处理任务更新
   */
  handleTaskUpdated(taskData) {
    const claudeEditorTask = this.convertClaudeCodeTaskToClaudeEditor(taskData);
    this.notifyTaskListeners('task_updated', claudeEditorTask);
  }

  /**
   * 处理任务分配
   */
  handleTaskAssigned(taskData) {
    const claudeEditorTask = this.convertClaudeCodeTaskToClaudeEditor(taskData);
    this.notifyTaskListeners('task_assigned', claudeEditorTask);
  }

  /**
   * 处理任务完成
   */
  handleTaskCompleted(taskData) {
    const claudeEditorTask = this.convertClaudeCodeTaskToClaudeEditor(taskData);
    this.notifyTaskListeners('task_completed', claudeEditorTask);
  }

  /**
   * 处理任务消息
   */
  handleTaskMessage(messageData) {
    this.notifyTaskListeners('task_message', messageData);
  }

  /**
   * 处理 Claude Code 请求
   */
  handleClaudeCodeRequest(requestData) {
    switch (requestData.action) {
      case 'open_file':
        this.notifyTaskListeners('open_file_request', requestData);
        break;
      
      case 'edit_code':
        this.notifyTaskListeners('edit_code_request', requestData);
        break;
      
      case 'run_command':
        this.notifyTaskListeners('run_command_request', requestData);
        break;
      
      case 'show_diff':
        this.notifyTaskListeners('show_diff_request', requestData);
        break;
      
      default:
        console.log('未知 Claude Code 请求:', requestData.action);
    }
  }

  /**
   * 处理同步响应
   */
  handleSyncResponse(syncData) {
    if (syncData.tasks) {
      syncData.tasks.forEach(task => {
        const claudeEditorTask = this.convertClaudeCodeTaskToClaudeEditor(task);
        this.notifyTaskListeners('task_synced', claudeEditorTask);
      });
    }
  }

  /**
   * 将 Claude Code 任务格式转换为 ClaudeEditor 格式
   */
  convertClaudeCodeTaskToClaudeEditor(claudeCodeTask) {
    return {
      id: claudeCodeTask.id || `cc_${Date.now()}`,
      title: claudeCodeTask.title || claudeCodeTask.description || '未命名任务',
      description: claudeCodeTask.description || '',
      priority: this.mapPriority(claudeCodeTask.priority),
      status: this.taskStatusMap[claudeCodeTask.status] || 'pending',
      assignedAgent: claudeCodeTask.assigned_to || null,
      estimatedTime: claudeCodeTask.estimated_duration || '未知',
      tags: claudeCodeTask.tags || ['Claude Code'],
      subtasks: (claudeCodeTask.subtasks || []).map(subtask => ({
        id: subtask.id,
        title: subtask.title || subtask.description,
        status: this.taskStatusMap[subtask.status] || 'pending'
      })),
      createdAt: claudeCodeTask.created_at || new Date().toISOString(),
      deadline: claudeCodeTask.deadline,
      progress: claudeCodeTask.progress || 0,
      source: 'claude_code',
      claudeCodeData: claudeCodeTask, // 保留原始数据
      communication: {
        messages: claudeCodeTask.messages || [],
        lastMessage: claudeCodeTask.last_message,
        canReply: true
      }
    };
  }

  /**
   * 将 ClaudeEditor 任务格式转换为 Claude Code 格式
   */
  convertClaudeEditorTaskToClaudeCode(claudeEditorTask) {
    return {
      id: claudeEditorTask.id,
      title: claudeEditorTask.title,
      description: claudeEditorTask.description,
      priority: this.mapPriorityReverse(claudeEditorTask.priority),
      status: this.getClaudeCodeStatus(claudeEditorTask.status),
      assigned_to: claudeEditorTask.assignedAgent,
      estimated_duration: claudeEditorTask.estimatedTime,
      tags: claudeEditorTask.tags?.filter(tag => tag !== 'Claude Code') || [],
      subtasks: (claudeEditorTask.subtasks || []).map(subtask => ({
        id: subtask.id,
        title: subtask.title,
        status: this.getClaudeCodeStatus(subtask.status)
      })),
      created_at: claudeEditorTask.createdAt,
      deadline: claudeEditorTask.deadline,
      progress: claudeEditorTask.progress || 0,
      source: 'claudeditor'
    };
  }

  /**
   * 映射优先级
   */
  mapPriority(claudeCodePriority) {
    const priorityMap = {
      'urgent': 'high',
      'high': 'high',
      'normal': 'medium',
      'medium': 'medium',
      'low': 'low'
    };
    return priorityMap[claudeCodePriority] || 'medium';
  }

  mapPriorityReverse(claudeEditorPriority) {
    const priorityMap = {
      'high': 'high',
      'medium': 'normal',
      'low': 'low'
    };
    return priorityMap[claudeEditorPriority] || 'normal';
  }

  /**
   * 获取 Claude Code 状态
   */
  getClaudeCodeStatus(claudeEditorStatus) {
    const statusMap = {
      'pending': 'created',
      'in_progress': 'in_progress',
      'completed': 'completed',
      'blocked': 'failed',
      'cancelled': 'cancelled'
    };
    return statusMap[claudeEditorStatus] || 'created';
  }

  /**
   * 同步现有任务
   */
  async syncExistingTasks() {
    try {
      const response = await fetch(`${this.claudeCodeEndpoint}/api/tasks/sync`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Client': 'claudeditor'
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('📋 同步现有任务:', data.tasks?.length || 0, '个');
        
        if (data.tasks) {
          data.tasks.forEach(task => {
            const claudeEditorTask = this.convertClaudeCodeTaskToClaudeEditor(task);
            this.notifyTaskListeners('task_synced', claudeEditorTask);
          });
        }
      }
    } catch (error) {
      console.error('同步现有任务失败:', error);
    }
  }

  /**
   * 发送消息到 Claude Code
   */
  sendMessage(message) {
    if (this.isConnected && this.websocket) {
      this.websocket.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket 未连接，消息发送失败');
    }
  }

  /**
   * 创建新任务（从 ClaudeEditor 发送到 Claude Code）
   */
  async createTask(task) {
    const claudeCodeTask = this.convertClaudeEditorTaskToClaudeCode(task);
    
    try {
      const response = await fetch(`${this.claudeCodeEndpoint}/api/tasks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Client': 'claudeditor'
        },
        body: JSON.stringify(claudeCodeTask)
      });

      if (response.ok) {
        const result = await response.json();
        console.log('✅ 任务已发送到 Claude Code:', result);
        return result;
      } else {
        throw new Error(`创建任务失败: ${response.status}`);
      }
    } catch (error) {
      console.error('创建任务失败:', error);
      throw error;
    }
  }

  /**
   * 更新任务状态
   */
  async updateTaskStatus(taskId, status, message = null) {
    const updateData = {
      status: this.getClaudeCodeStatus(status),
      updated_by: 'claudeditor',
      timestamp: new Date().toISOString()
    };

    if (message) {
      updateData.message = message;
    }

    try {
      const response = await fetch(`${this.claudeCodeEndpoint}/api/tasks/${taskId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Client': 'claudeditor'
        },
        body: JSON.stringify(updateData)
      });

      if (response.ok) {
        console.log('✅ 任务状态已更新:', taskId, status);
        return await response.json();
      } else {
        throw new Error(`更新任务状态失败: ${response.status}`);
      }
    } catch (error) {
      console.error('更新任务状态失败:', error);
      throw error;
    }
  }

  /**
   * 发送任务消息
   */
  async sendTaskMessage(taskId, message, messageType = 'comment') {
    const messageData = {
      task_id: taskId,
      message: message,
      type: messageType,
      sender: 'claudeditor',
      timestamp: new Date().toISOString()
    };

    try {
      const response = await fetch(`${this.claudeCodeEndpoint}/api/tasks/${taskId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Client': 'claudeditor'
        },
        body: JSON.stringify(messageData)
      });

      if (response.ok) {
        console.log('✅ 任务消息已发送:', taskId);
        return await response.json();
      } else {
        throw new Error(`发送任务消息失败: ${response.status}`);
      }
    } catch (error) {
      console.error('发送任务消息失败:', error);
      throw error;
    }
  }

  /**
   * 响应 Claude Code 请求
   */
  async respondToClaudeCodeRequest(requestId, response, data = null) {
    const responseData = {
      request_id: requestId,
      response: response,
      data: data,
      client: 'claudeditor',
      timestamp: new Date().toISOString()
    };

    this.sendMessage({
      type: 'request_response',
      data: responseData
    });
  }

  /**
   * 添加任务监听器
   */
  addTaskListener(listener) {
    this.taskListeners.add(listener);
  }

  /**
   * 移除任务监听器
   */
  removeTaskListener(listener) {
    this.taskListeners.delete(listener);
  }

  /**
   * 添加消息监听器
   */
  addMessageListener(listener) {
    this.messageListeners.add(listener);
  }

  /**
   * 移除消息监听器
   */
  removeMessageListener(listener) {
    this.messageListeners.delete(listener);
  }

  /**
   * 通知任务监听器
   */
  notifyTaskListeners(eventType, data) {
    this.taskListeners.forEach(listener => {
      try {
        listener(eventType, data);
      } catch (error) {
        console.error('任务监听器错误:', error);
      }
    });
  }

  /**
   * 获取连接状态
   */
  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.maxReconnectAttempts
    };
  }

  /**
   * 断开连接
   */
  disconnect() {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
    this.isConnected = false;
    console.log('🔌 任务同步服务已断开');
  }
}

// 创建全局实例
const taskSyncService = new TaskSyncService();

export default taskSyncService;

