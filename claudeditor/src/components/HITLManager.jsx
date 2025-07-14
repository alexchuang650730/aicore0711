import React, { useState, useEffect } from 'react'

// AG-UI Smart Components - Agent Generated UI
const AGUINotificationCard = ({ notification, onAction, userInput, setUserInput }) => {
  // SmartUI - Intelligent adaptive styling based on notification type
  const getSmartUIStyle = (type, severity = 'normal') => {
    const baseStyles = {
      card: {
        margin: '8px 0',
        borderRadius: '12px',
        border: '2px solid',
        background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
        overflow: 'hidden',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        position: 'relative'
      },
      header: {
        padding: '16px 20px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        display: 'flex',
        alignItems: 'center',
        gap: '12px'
      },
      content: {
        padding: '16px 20px'
      },
      actions: {
        padding: '12px 20px',
        borderTop: '1px solid rgba(255, 255, 255, 0.1)',
        backgroundColor: 'rgba(255, 255, 255, 0.5)'
      }
    }

    // SmartUI adaptive theming
    const themes = {
      api_error: {
        gradient: 'linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)',
        borderColor: '#f87171',
        iconColor: '#dc2626',
        textColor: '#991b1b'
      },
      config_required: {
        gradient: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
        borderColor: '#f59e0b',
        iconColor: '#d97706',
        textColor: '#92400e'
      },
      network_error: {
        gradient: 'linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%)',
        borderColor: '#3b82f6',
        iconColor: '#2563eb',
        textColor: '#1e40af'
      },
      user_input_required: {
        gradient: 'linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)',
        borderColor: '#10b981',
        iconColor: '#059669',
        textColor: '#065f46'
      }
    }

    const theme = themes[type] || themes.user_input_required

    return {
      ...baseStyles,
      card: {
        ...baseStyles.card,
        background: theme.gradient,
        borderColor: theme.borderColor,
        color: theme.textColor
      },
      icon: {
        color: theme.iconColor,
        fontSize: '24px'
      },
      text: {
        color: theme.textColor
      }
    }
  }

  const styles = getSmartUIStyle(notification.type)

  // AG-UI Generated Action Buttons - Context-aware button generation
  const generateAGUIActions = () => {
    const baseButtonStyle = {
      padding: '10px 18px',
      borderRadius: '8px',
      border: 'none',
      cursor: 'pointer',
      fontSize: '14px',
      fontWeight: '600',
      transition: 'all 0.2s ease',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      textTransform: 'none'
    }

    const buttonVariants = {
      primary: {
        ...baseButtonStyle,
        background: 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)',
        color: 'white',
        boxShadow: '0 2px 8px rgba(59, 130, 246, 0.3)'
      },
      success: {
        ...baseButtonStyle,
        background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
        color: 'white',
        boxShadow: '0 2px 8px rgba(16, 185, 129, 0.3)'
      },
      warning: {
        ...baseButtonStyle,
        background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
        color: 'white',
        boxShadow: '0 2px 8px rgba(245, 158, 11, 0.3)'
      },
      secondary: {
        ...baseButtonStyle,
        background: 'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)',
        color: 'white',
        boxShadow: '0 2px 8px rgba(107, 114, 128, 0.3)'
      }
    }

    // AG-UI: Context-aware button generation
    switch (notification.type) {
      case 'api_error':
        return (
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <button
              style={buttonVariants.primary}
              onClick={() => onAction(notification.id, 'retry')}
            >
              🔄 智能重試
            </button>
            <button
              style={buttonVariants.warning}
              onClick={() => onAction(notification.id, 'manual_config')}
            >
              ⚙️ 配置修復
            </button>
            <button
              style={buttonVariants.secondary}
              onClick={() => onAction(notification.id, 'skip')}
            >
              ⏭️ 跳過
            </button>
          </div>
        )

      case 'config_required':
        return (
          <div>
            <div style={{ marginBottom: '12px' }}>
              <input
                type="text"
                placeholder={notification.placeholder || "輸入配置值..."}
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  border: '2px solid #e5e7eb',
                  borderRadius: '8px',
                  fontSize: '14px',
                  background: 'white',
                  boxShadow: 'inset 0 2px 4px rgba(0, 0, 0, 0.06)',
                  transition: 'border-color 0.2s ease',
                  outline: 'none'
                }}
                onFocus={(e) => e.target.style.borderColor = '#3b82f6'}
                onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
              />
            </div>
            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                style={{
                  ...buttonVariants.success,
                  opacity: userInput.trim() ? 1 : 0.5,
                  cursor: userInput.trim() ? 'pointer' : 'not-allowed'
                }}
                onClick={() => userInput.trim() && onAction(notification.id, 'configure', userInput)}
                disabled={!userInput.trim()}
              >
                ✅ 智能配置
              </button>
              <button
                style={buttonVariants.secondary}
                onClick={() => onAction(notification.id, 'skip')}
              >
                ⏭️ 稍後處理
              </button>
            </div>
          </div>
        )

      case 'network_error':
        return (
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <button
              style={buttonVariants.primary}
              onClick={() => onAction(notification.id, 'check_network')}
            >
              🔍 智能診斷
            </button>
            <button
              style={buttonVariants.warning}
              onClick={() => onAction(notification.id, 'use_local')}
            >
              💻 本地模式
            </button>
            <button
              style={buttonVariants.secondary}
              onClick={() => onAction(notification.id, 'dismiss')}
            >
              ❌ 忽略
            </button>
          </div>
        )

      default:
        return (
          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              style={buttonVariants.primary}
              onClick={() => onAction(notification.id, 'acknowledge')}
            >
              ✅ 確認處理
            </button>
          </div>
        )
    }
  }

  // SmartUI Icon Selection
  const getSmartIcon = (type) => {
    const icons = {
      api_error: '🚨',
      config_required: '⚙️',
      network_error: '🌐',
      user_input_required: '💬'
    }
    return icons[type] || 'ℹ️'
  }

  return (
    <div style={styles.card}>
      {/* AG-UI Generated Header */}
      <div style={styles.header}>
        <span style={styles.icon}>{getSmartIcon(notification.type)}</span>
        <div style={{ flex: 1 }}>
          <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '700' }}>
            {notification.title}
          </h4>
          <p style={{ margin: '4px 0 0 0', fontSize: '14px', opacity: 0.8 }}>
            {notification.message}
          </p>
        </div>
      </div>

      {/* SmartUI Content Area */}
      {notification.details && (
        <div style={styles.content}>
          <details>
            <summary style={{ 
              cursor: 'pointer', 
              fontSize: '13px', 
              opacity: 0.7,
              marginBottom: '8px'
            }}>
              📋 查看技術詳情
            </summary>
            <pre style={{
              fontSize: '11px',
              background: 'rgba(255, 255, 255, 0.7)',
              padding: '12px',
              borderRadius: '6px',
              overflow: 'auto',
              maxHeight: '120px',
              border: '1px solid rgba(0, 0, 0, 0.1)'
            }}>
              {notification.details}
            </pre>
          </details>
        </div>
      )}

      {/* AG-UI Generated Actions */}
      <div style={styles.actions}>
        {generateAGUIActions()}
      </div>
    </div>
  )
}

// Main HITL Manager with AG-UI and SmartUI
const HITLManager = ({ onUserAction, notifications = [], clearNotification }) => {
  const [activeNotifications, setActiveNotifications] = useState([])
  const [userInputs, setUserInputs] = useState({})

  useEffect(() => {
    setActiveNotifications(notifications)
  }, [notifications])

  const handleAction = (notificationId, response, userInput = '') => {
    const notification = activeNotifications.find(n => n.id === notificationId)
    if (!notification) return

    onUserAction({
      notificationId,
      type: notification.type,
      action: notification.action,
      userResponse: response,
      userInput: userInput,
      context: notification.context
    })

    if (clearNotification) {
      clearNotification(notificationId)
    }

    // Clear user input for this notification
    setUserInputs(prev => ({ ...prev, [notificationId]: '' }))
  }

  const setUserInput = (notificationId, value) => {
    setUserInputs(prev => ({ ...prev, [notificationId]: value }))
  }

  if (activeNotifications.length === 0) {
    return null
  }

  return (
    <div style={{
      position: 'fixed',
      top: '20px',
      right: '20px',
      width: '420px',
      maxHeight: '85vh',
      overflowY: 'auto',
      zIndex: 1000,
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      backdropFilter: 'blur(10px)',
      border: '1px solid rgba(229, 231, 235, 0.5)',
      borderRadius: '16px',
      boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
      padding: '24px'
    }}>
      {/* SmartUI Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '20px',
        paddingBottom: '16px',
        borderBottom: '2px solid rgba(229, 231, 235, 0.3)'
      }}>
        <div>
          <h3 style={{ 
            margin: 0, 
            fontSize: '18px', 
            fontWeight: '800',
            background: 'linear-gradient(135deg, #3b82f6, #1e40af)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            🤝 Human-in-the-Loop
          </h3>
          <p style={{ 
            margin: '4px 0 0 0', 
            fontSize: '13px', 
            color: '#6b7280',
            fontWeight: '500'
          }}>
            AG-UI + SmartUI 智能交互
          </p>
        </div>
        <div style={{
          fontSize: '12px',
          color: '#ffffff',
          background: 'linear-gradient(135deg, #f59e0b, #d97706)',
          padding: '6px 12px',
          borderRadius: '16px',
          fontWeight: '600',
          boxShadow: '0 2px 8px rgba(245, 158, 11, 0.3)'
        }}>
          {activeNotifications.length} 項智能提醒
        </div>
      </div>

      {/* AG-UI Generated Notification Cards */}
      {activeNotifications.map((notification) => (
        <AGUINotificationCard
          key={notification.id}
          notification={notification}
          onAction={handleAction}
          userInput={userInputs[notification.id] || ''}
          setUserInput={(value) => setUserInput(notification.id, value)}
        />
      ))}

      {/* SmartUI Footer */}
      <div style={{
        marginTop: '16px',
        paddingTop: '16px',
        borderTop: '1px solid rgba(229, 231, 235, 0.3)',
        textAlign: 'center'
      }}>
        <p style={{
          margin: 0,
          fontSize: '11px',
          color: '#9ca3af',
          fontStyle: 'italic'
        }}>
          🤖 Powered by AG-UI + SmartUI • PowerAutomation v4.6.9.1
        </p>
      </div>
    </div>
  )
}

export default HITLManager