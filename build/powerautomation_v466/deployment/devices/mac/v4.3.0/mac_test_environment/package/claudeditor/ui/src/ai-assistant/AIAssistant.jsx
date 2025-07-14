import React, { useState, useRef, useEffect } from 'react'

const AIAssistant = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'assistant',
      content: '👋 Hello! I\'m Claude, your AI coding assistant. I can help you with:\n\n• Code generation and completion\n• Bug detection and fixing\n• Code optimization\n• Documentation\n• Explaining complex concepts\n\nHow can I assist you today?',
      timestamp: new Date().toLocaleTimeString()
    }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toLocaleTimeString()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    // Simulate AI response
    setTimeout(() => {
      const aiResponse = {
        id: Date.now() + 1,
        type: 'assistant',
        content: generateAIResponse(inputMessage),
        timestamp: new Date().toLocaleTimeString()
      }
      setMessages(prev => [...prev, aiResponse])
      setIsLoading(false)
    }, 1500)
  }

  const generateAIResponse = (userInput) => {
    const input = userInput.toLowerCase()
    
    if (input.includes('hello') || input.includes('hi')) {
      return '👋 Hello! I\'m ready to help you with your coding tasks. What would you like to work on?'
    }
    
    if (input.includes('bug') || input.includes('error')) {
      return '🐛 I can help you debug your code! Please share the error message or problematic code, and I\'ll analyze it for you.'
    }
    
    if (input.includes('optimize') || input.includes('performance')) {
      return '⚡ I\'d be happy to help optimize your code! Share the code you\'d like me to review for performance improvements.'
    }
    
    if (input.includes('function') || input.includes('method')) {
      return '🔧 I can help you create functions! What functionality do you need? Please describe what the function should do.'
    }
    
    if (input.includes('react') || input.includes('component')) {
      return '⚛️ I can help with React components! Are you looking to create a new component or improve an existing one?'
    }
    
    if (input.includes('api') || input.includes('fetch')) {
      return '🌐 I can assist with API integration! Are you working with REST APIs, GraphQL, or need help with data fetching?'
    }
    
    return `🤖 I understand you're asking about: "${userInput}"\n\nI'm here to help! Could you provide more details about what you're trying to accomplish? The more context you give me, the better I can assist you.`
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const quickActions = [
    { label: '🐛 Debug Code', action: 'Help me debug this code' },
    { label: '⚡ Optimize', action: 'How can I optimize this code?' },
    { label: '📝 Document', action: 'Generate documentation for this code' },
    { label: '🧪 Test', action: 'Create unit tests for this function' }
  ]

  return (
    <div style={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      backgroundColor: '#f8f9fa'
    }}>
      {/* Header */}
      <div style={{ 
        padding: '15px', 
        backgroundColor: '#1e3a8a', 
        color: 'white',
        borderBottom: '1px solid #e9ecef'
      }}>
        <h3 style={{ margin: 0, fontSize: '16px' }}>🤖 AI Assistant (Claude)</h3>
        <p style={{ margin: '4px 0 0 0', fontSize: '12px', opacity: 0.9 }}>
          PowerAutomation AI Integration
        </p>
      </div>

      {/* Quick Actions */}
      <div style={{ 
        padding: '10px',
        backgroundColor: 'white',
        borderBottom: '1px solid #e9ecef'
      }}>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: '1fr 1fr',
          gap: '5px'
        }}>
          {quickActions.map((action, index) => (
            <button
              key={index}
              onClick={() => setInputMessage(action.action)}
              style={{
                padding: '6px 8px',
                fontSize: '11px',
                backgroundColor: '#f1f3f4',
                border: '1px solid #dadce0',
                borderRadius: '4px',
                cursor: 'pointer',
                textAlign: 'left'
              }}
            >
              {action.label}
            </button>
          ))}
        </div>
      </div>

      {/* Messages */}
      <div style={{ 
        flex: 1, 
        overflowY: 'auto', 
        padding: '10px',
        backgroundColor: 'white'
      }}>
        {messages.map((message) => (
          <div
            key={message.id}
            style={{
              marginBottom: '15px',
              padding: '10px',
              borderRadius: '8px',
              backgroundColor: message.type === 'user' ? '#e3f2fd' : '#f5f5f5',
              border: `1px solid ${message.type === 'user' ? '#bbdefb' : '#e0e0e0'}`
            }}
          >
            <div style={{ 
              fontSize: '12px', 
              color: '#666',
              marginBottom: '5px',
              fontWeight: 'bold'
            }}>
              {message.type === 'user' ? '👤 You' : '🤖 Claude'} • {message.timestamp}
            </div>
            <div style={{ 
              fontSize: '14px',
              lineHeight: '1.4',
              whiteSpace: 'pre-wrap'
            }}>
              {message.content}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div style={{
            padding: '10px',
            borderRadius: '8px',
            backgroundColor: '#f5f5f5',
            border: '1px solid #e0e0e0',
            textAlign: 'center',
            color: '#666'
          }}>
            🤖 Claude is thinking...
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={{ 
        padding: '10px',
        backgroundColor: 'white',
        borderTop: '1px solid #e9ecef'
      }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask Claude anything about your code..."
            style={{
              flex: 1,
              padding: '8px',
              border: '1px solid #dadce0',
              borderRadius: '4px',
              resize: 'none',
              fontSize: '14px',
              minHeight: '36px',
              maxHeight: '100px'
            }}
            rows={1}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            style={{
              padding: '8px 16px',
              backgroundColor: isLoading ? '#ccc' : '#1e3a8a',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              fontSize: '14px'
            }}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}

export default AIAssistant

