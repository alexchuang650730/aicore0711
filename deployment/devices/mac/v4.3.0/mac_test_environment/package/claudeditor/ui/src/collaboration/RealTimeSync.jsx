import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Users, 
  Wifi, 
  WifiOff, 
  MessageCircle, 
  Send, 
  UserPlus,
  Settings,
  Eye,
  EyeOff,
  Clock,
  AlertCircle,
  CheckCircle
} from 'lucide-react';

// 模拟WebSocket连接状态
const CONNECTION_STATES = {
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  RECONNECTING: 'reconnecting',
  ERROR: 'error'
};

// 协作事件类型
const COLLABORATION_EVENTS = {
  USER_JOIN: 'user_join',
  USER_LEAVE: 'user_leave',
  CURSOR_MOVE: 'cursor_move',
  TEXT_CHANGE: 'text_change',
  SELECTION_CHANGE: 'selection_change',
  CHAT_MESSAGE: 'chat_message',
  FILE_CHANGE: 'file_change',
  PRESENCE_UPDATE: 'presence_update'
};

// 用户状态
const USER_STATUS = {
  ACTIVE: 'active',
  IDLE: 'idle',
  AWAY: 'away',
  OFFLINE: 'offline'
};

const RealTimeSync = ({ 
  editorRef,
  currentUser,
  sessionId,
  onCollaborationEvent,
  onConnectionChange,
  className = ''
}) => {
  // 连接状态
  const [connectionState, setConnectionState] = useState(CONNECTION_STATES.DISCONNECTED);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [lastSyncTime, setLastSyncTime] = useState(null);

  // 协作用户
  const [collaborators, setCollaborators] = useState([]);
  const [userCursors, setUserCursors] = useState(new Map());
  const [userSelections, setUserSelections] = useState(new Map());

  // 聊天功能
  const [chatVisible, setChatVisible] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [unreadCount, setUnreadCount] = useState(0);

  // 同步状态
  const [pendingChanges, setPendingChanges] = useState([]);
  const [conflictResolution, setConflictResolution] = useState(null);
  const [syncQueue, setSyncQueue] = useState([]);

  // WebSocket引用
  const wsRef = useRef(null);
  const heartbeatRef = useRef(null);
  const syncTimeoutRef = useRef(null);

  // 初始化WebSocket连接
  useEffect(() => {
    if (sessionId && currentUser) {
      connectToSession();
    }

    return () => {
      disconnect();
    };
  }, [sessionId, currentUser]);

  // 连接到协作会话
  const connectToSession = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionState(CONNECTION_STATES.CONNECTING);

    try {
      // 模拟WebSocket连接
      // 在实际实现中，这里应该连接到真实的WebSocket服务器
      const mockWs = {
        readyState: WebSocket.OPEN,
        send: (data) => {
          console.log('Sending:', JSON.parse(data));
          // 模拟服务器响应
          setTimeout(() => {
            handleMockServerResponse(JSON.parse(data));
          }, 100);
        },
        close: () => {
          setConnectionState(CONNECTION_STATES.DISCONNECTED);
        }
      };

      wsRef.current = mockWs;
      setConnectionState(CONNECTION_STATES.CONNECTED);
      setReconnectAttempts(0);
      setLastSyncTime(new Date());

      // 发送加入会话事件
      sendEvent(COLLABORATION_EVENTS.USER_JOIN, {
        user: currentUser,
        sessionId,
        timestamp: Date.now()
      });

      // 启动心跳
      startHeartbeat();

      onConnectionChange?.(CONNECTION_STATES.CONNECTED);

    } catch (error) {
      console.error('Connection failed:', error);
      setConnectionState(CONNECTION_STATES.ERROR);
      scheduleReconnect();
    }
  }, [sessionId, currentUser]);

  // 模拟服务器响应
  const handleMockServerResponse = (data) => {
    switch (data.type) {
      case COLLABORATION_EVENTS.USER_JOIN:
        // 模拟其他用户加入
        const mockUsers = [
          { id: 'user1', name: 'Alice', avatar: '👩‍💻', color: '#3b82f6', status: USER_STATUS.ACTIVE },
          { id: 'user2', name: 'Bob', avatar: '👨‍💻', color: '#10b981', status: USER_STATUS.ACTIVE },
          { id: 'user3', name: 'Charlie', avatar: '👨‍🎨', color: '#f59e0b', status: USER_STATUS.IDLE }
        ];
        setCollaborators(mockUsers);
        break;

      case COLLABORATION_EVENTS.CHAT_MESSAGE:
        // 模拟接收聊天消息
        if (Math.random() > 0.7) {
          const mockMessage = {
            id: Date.now(),
            user: collaborators[Math.floor(Math.random() * collaborators.length)] || { name: 'Unknown', avatar: '👤' },
            message: 'This is a mock collaboration message',
            timestamp: Date.now()
          };
          setChatMessages(prev => [...prev, mockMessage]);
          if (!chatVisible) {
            setUnreadCount(prev => prev + 1);
          }
        }
        break;
    }
  };

  // 断开连接
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current);
      heartbeatRef.current = null;
    }

    if (syncTimeoutRef.current) {
      clearTimeout(syncTimeoutRef.current);
      syncTimeoutRef.current = null;
    }

    setConnectionState(CONNECTION_STATES.DISCONNECTED);
    onConnectionChange?.(CONNECTION_STATES.DISCONNECTED);
  }, []);

  // 重连调度
  const scheduleReconnect = useCallback(() => {
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
    
    setTimeout(() => {
      setReconnectAttempts(prev => prev + 1);
      setConnectionState(CONNECTION_STATES.RECONNECTING);
      connectToSession();
    }, delay);
  }, [reconnectAttempts, connectToSession]);

  // 启动心跳
  const startHeartbeat = useCallback(() => {
    heartbeatRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        sendEvent('heartbeat', { timestamp: Date.now() });
      }
    }, 30000);
  }, []);

  // 发送事件
  const sendEvent = useCallback((type, data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const event = {
        type,
        sessionId,
        user: currentUser,
        data,
        timestamp: Date.now()
      };

      wsRef.current.send(JSON.stringify(event));
      onCollaborationEvent?.(event);
    }
  }, [sessionId, currentUser, onCollaborationEvent]);

  // 同步文本变化
  const syncTextChange = useCallback((change) => {
    const changeEvent = {
      type: 'text_change',
      change,
      version: Date.now(),
      user: currentUser
    };

    // 添加到同步队列
    setSyncQueue(prev => [...prev, changeEvent]);

    // 发送变化
    sendEvent(COLLABORATION_EVENTS.TEXT_CHANGE, changeEvent);

    // 设置同步超时
    if (syncTimeoutRef.current) {
      clearTimeout(syncTimeoutRef.current);
    }

    syncTimeoutRef.current = setTimeout(() => {
      processSyncQueue();
    }, 500);
  }, [currentUser, sendEvent]);

  // 处理同步队列
  const processSyncQueue = useCallback(() => {
    if (syncQueue.length > 0) {
      // 批量处理变化
      const batchedChanges = syncQueue.splice(0);
      
      // 应用变化到编辑器
      batchedChanges.forEach(change => {
        applyChangeToEditor(change);
      });

      setSyncQueue([]);
      setLastSyncTime(new Date());
    }
  }, [syncQueue]);

  // 应用变化到编辑器
  const applyChangeToEditor = useCallback((change) => {
    if (editorRef.current && change.user.id !== currentUser.id) {
      // 避免应用自己的变化
      const editor = editorRef.current;
      const model = editor.getModel();
      
      if (model && change.data.change) {
        // 应用文本变化
        const edit = {
          range: change.data.change.range,
          text: change.data.change.text
        };
        
        model.applyEdits([edit]);
      }
    }
  }, [currentUser, editorRef]);

  // 同步光标位置
  const syncCursorPosition = useCallback((position) => {
    sendEvent(COLLABORATION_EVENTS.CURSOR_MOVE, {
      position,
      user: currentUser
    });

    // 更新本地光标显示
    setUserCursors(prev => {
      const newCursors = new Map(prev);
      newCursors.set(currentUser.id, {
        position,
        user: currentUser,
        timestamp: Date.now()
      });
      return newCursors;
    });
  }, [currentUser, sendEvent]);

  // 发送聊天消息
  const sendChatMessage = useCallback(() => {
    if (newMessage.trim() && connectionState === CONNECTION_STATES.CONNECTED) {
      const message = {
        id: Date.now(),
        user: currentUser,
        message: newMessage.trim(),
        timestamp: Date.now()
      };

      setChatMessages(prev => [...prev, message]);
      sendEvent(COLLABORATION_EVENTS.CHAT_MESSAGE, message);
      setNewMessage('');
    }
  }, [newMessage, currentUser, connectionState, sendEvent]);

  // 切换聊天可见性
  const toggleChat = useCallback(() => {
    setChatVisible(!chatVisible);
    if (!chatVisible) {
      setUnreadCount(0);
    }
  }, [chatVisible]);

  // 获取连接状态图标
  const getConnectionIcon = () => {
    switch (connectionState) {
      case CONNECTION_STATES.CONNECTED:
        return <Wifi className="text-green-500" size={16} />;
      case CONNECTION_STATES.CONNECTING:
      case CONNECTION_STATES.RECONNECTING:
        return <Wifi className="text-yellow-500 animate-pulse" size={16} />;
      default:
        return <WifiOff className="text-red-500" size={16} />;
    }
  };

  // 获取连接状态文本
  const getConnectionText = () => {
    switch (connectionState) {
      case CONNECTION_STATES.CONNECTED:
        return 'Connected';
      case CONNECTION_STATES.CONNECTING:
        return 'Connecting...';
      case CONNECTION_STATES.RECONNECTING:
        return `Reconnecting... (${reconnectAttempts})`;
      case CONNECTION_STATES.DISCONNECTED:
        return 'Disconnected';
      case CONNECTION_STATES.ERROR:
        return 'Connection Error';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className={`real-time-sync ${className}`}>
      {/* 协作状态栏 */}
      <div className="collaboration-status bg-gray-800 border-b border-gray-700 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {/* 连接状态 */}
          <div className="flex items-center space-x-2">
            {getConnectionIcon()}
            <span className="text-sm text-gray-300">{getConnectionText()}</span>
            {lastSyncTime && (
              <span className="text-xs text-gray-500">
                Last sync: {lastSyncTime.toLocaleTimeString()}
              </span>
            )}
          </div>

          {/* 协作用户 */}
          <div className="flex items-center space-x-2">
            <Users size={16} className="text-gray-400" />
            <div className="flex -space-x-2">
              {collaborators.slice(0, 5).map(user => (
                <div
                  key={user.id}
                  className="relative"
                  title={`${user.name} (${user.status})`}
                >
                  <div 
                    className="w-8 h-8 rounded-full border-2 border-gray-700 flex items-center justify-center text-sm"
                    style={{ backgroundColor: user.color }}
                  >
                    {user.avatar}
                  </div>
                  <div 
                    className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full border border-gray-700 ${
                      user.status === USER_STATUS.ACTIVE ? 'bg-green-500' :
                      user.status === USER_STATUS.IDLE ? 'bg-yellow-500' :
                      'bg-gray-500'
                    }`}
                  />
                </div>
              ))}
              {collaborators.length > 5 && (
                <div className="w-8 h-8 rounded-full bg-gray-600 border-2 border-gray-700 flex items-center justify-center text-xs text-gray-300">
                  +{collaborators.length - 5}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* 聊天按钮 */}
          <button
            onClick={toggleChat}
            className="relative p-2 text-gray-400 hover:text-white transition-colors"
            title="Toggle Chat"
          >
            <MessageCircle size={16} />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {unreadCount}
              </span>
            )}
          </button>

          {/* 设置按钮 */}
          <button
            className="p-2 text-gray-400 hover:text-white transition-colors"
            title="Collaboration Settings"
          >
            <Settings size={16} />
          </button>
        </div>
      </div>

      {/* 聊天面板 */}
      {chatVisible && (
        <div className="chat-panel bg-gray-900 border-b border-gray-700 h-64 flex flex-col">
          {/* 聊天头部 */}
          <div className="chat-header bg-gray-800 px-4 py-2 border-b border-gray-700 flex items-center justify-between">
            <h3 className="text-sm font-medium text-white">Team Chat</h3>
            <button
              onClick={toggleChat}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <EyeOff size={14} />
            </button>
          </div>

          {/* 聊天消息 */}
          <div className="chat-messages flex-1 overflow-y-auto p-4 space-y-3">
            {chatMessages.map(msg => (
              <div key={msg.id} className="flex items-start space-x-3">
                <div 
                  className="w-6 h-6 rounded-full flex items-center justify-center text-xs flex-shrink-0"
                  style={{ backgroundColor: msg.user.color || '#6b7280' }}
                >
                  {msg.user.avatar || '👤'}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-white">{msg.user.name}</span>
                    <span className="text-xs text-gray-500">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-300 mt-1">{msg.message}</p>
                </div>
              </div>
            ))}
          </div>

          {/* 聊天输入 */}
          <div className="chat-input p-4 border-t border-gray-700">
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendChatMessage()}
                placeholder="Type a message..."
                className="flex-1 bg-gray-800 text-white text-sm rounded px-3 py-2 border border-gray-600 focus:border-blue-500 focus:outline-none"
                disabled={connectionState !== CONNECTION_STATES.CONNECTED}
              />
              <button
                onClick={sendChatMessage}
                disabled={!newMessage.trim() || connectionState !== CONNECTION_STATES.CONNECTED}
                className="p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded transition-colors"
              >
                <Send size={14} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 冲突解决对话框 */}
      {conflictResolution && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center space-x-2 mb-4">
              <AlertCircle className="text-yellow-500" size={20} />
              <h3 className="text-lg font-medium text-white">Merge Conflict</h3>
            </div>
            
            <p className="text-gray-300 mb-4">
              There are conflicting changes that need to be resolved.
            </p>
            
            <div className="flex space-x-3">
              <button
                onClick={() => setConflictResolution(null)}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
              >
                Accept Mine
              </button>
              <button
                onClick={() => setConflictResolution(null)}
                className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded transition-colors"
              >
                Accept Theirs
              </button>
              <button
                onClick={() => setConflictResolution(null)}
                className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded transition-colors"
              >
                Manual Merge
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 样式 */}
      <style jsx>{`
        .real-time-sync {
          background: #1f2937;
          border-radius: 8px;
          overflow: hidden;
        }
        
        .chat-messages::-webkit-scrollbar {
          width: 6px;
        }
        
        .chat-messages::-webkit-scrollbar-track {
          background: #374151;
        }
        
        .chat-messages::-webkit-scrollbar-thumb {
          background: #6b7280;
          border-radius: 3px;
        }
        
        .chat-messages::-webkit-scrollbar-thumb:hover {
          background: #9ca3af;
        }
      `}</style>
    </div>
  );
};

export default RealTimeSync;

