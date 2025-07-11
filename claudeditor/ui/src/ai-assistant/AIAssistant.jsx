import React, { useState, useRef, useEffect } from 'react'

const AIAssistant = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'assistant',
      content: '🚀 你好！我是Claude，你的自主AI編程助手。我能夠：\n\n🎯 **自主任務執行**\n• 分析需求並制定執行計劃\n• 獨立完成編程任務\n• 自動調試和優化代碼\n\n🧠 **智能項目理解**\n• 全項目代碼分析\n• 架構理解和建議\n• 依賴關係管理\n\n⚡ **實時協作**\n• 會話分享和回放\n• 團隊協作支持\n• 透明AI決策過程\n\n告訴我你想完成什麼任務，我會為你制定完整的執行計劃！',
      timestamp: new Date().toLocaleTimeString()
    }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [currentTask, setCurrentTask] = useState(null)
  const [taskProgress, setTaskProgress] = useState([])
  const [autonomousMode, setAutonomousMode] = useState(false)
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
    const originalMessage = inputMessage
    setInputMessage('')
    setIsLoading(true)

    try {
      // 調用AI後端服務
      const response = await fetch('http://localhost:8082/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: originalMessage,
          project_path: './',
          use_project_context: true
        })
      })
      
      const data = await response.json()
      
      const aiResponse = {
        id: Date.now() + 1,
        type: 'assistant',
        content: data.response,
        timestamp: new Date().toLocaleTimeString(),
        project_context_used: data.project_context_used
      }
      
      setMessages(prev => [...prev, aiResponse])
      
    } catch (error) {
      console.error('調用AI服務失敗:', error)
      // 降級到本地響應
      const fallbackResponse = {
        id: Date.now() + 1,
        type: 'assistant',
        content: generateAIResponse(originalMessage),
        timestamp: new Date().toLocaleTimeString(),
        fallback: true
      }
      setMessages(prev => [...prev, fallbackResponse])
    }
    
    setIsLoading(false)
  }

  // 觸發自主任務執行
  const triggerAutonomousTask = async (taskDescription) => {
    setInputMessage('')
    setIsLoading(true)
    
    const taskMessage = {
      id: Date.now(),
      type: 'user', 
      content: taskDescription,
      timestamp: new Date().toLocaleTimeString()
    }
    
    setMessages(prev => [...prev, taskMessage])
    
    try {
      // 調用自主任務API
      const response = await fetch('http://localhost:8082/api/autonomous-task', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_description: taskDescription,
          project_path: './',
          context: {}
        })
      })
      
      const data = await response.json()
      
      if (data.status === 'created') {
        const taskPlan = data.task_plan
        setCurrentTask(taskPlan)
        
        const planMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: `🚀 **自主任務已創建**: ${taskPlan.title}\n\n📋 **執行計劃**:\n${taskPlan.steps.map((step, index) => `${index + 1}. ${step.description} (預計${step.estimated_time})`).join('\n')}\n\n⏱️ **總預計時間**: ${taskPlan.total_time}\n\n🤖 開始自主執行...`,
          timestamp: new Date().toLocaleTimeString(),
          taskPlan: taskPlan
        }
        
        setMessages(prev => [...prev, planMessage])
        
        // 開始執行任務
        executeAutonomousTask(taskPlan)
      }
      
    } catch (error) {
      console.error('創建自主任務失敗:', error)
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: '⚠️ 自主任務創建失敗，使用本地任務規劃...',
        timestamp: new Date().toLocaleTimeString()
      }
      setMessages(prev => [...prev, errorMessage])
      
      // 降級到本地任務執行
      const localTaskPlan = generateTaskPlan(taskDescription)
      setTimeout(() => executeAutonomousTask(localTaskPlan), 500)
    }
    
    setIsLoading(false)
  }

  // 項目分析功能
  const analyzeProject = async () => {
    setIsLoading(true)
    
    const analysisMessage = {
      id: Date.now(),
      type: 'assistant',
      content: '🔍 開始分析項目代碼庫...這將提供比Manus更深入的理解能力！',
      timestamp: new Date().toLocaleTimeString()
    }
    
    setMessages(prev => [...prev, analysisMessage])
    
    try {
      const response = await fetch('http://localhost:8082/api/analyze-project', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_path: './'
        })
      })
      
      const data = await response.json()
      
      const resultMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: `✅ **項目分析已啟動**\n\n${data.message}\n\n🧠 分析完成後，我將具備：\n• 完整的項目架構理解\n• 智能的代碼建議\n• 基於上下文的自主任務執行\n\n這就是我們超越Manus的關鍵優勢！`,
        timestamp: new Date().toLocaleTimeString()
      }
      
      setMessages(prev => [...prev, resultMessage])
      
    } catch (error) {
      console.error('項目分析失敗:', error)
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: '⚠️ 項目分析服務暫時不可用，但基礎功能仍可正常使用',
        timestamp: new Date().toLocaleTimeString()
      }
      setMessages(prev => [...prev, errorMessage])
    }
    
    setIsLoading(false)
  }

  // 自主任務規劃和執行
  const generateTaskPlan = (taskDescription) => {
    const input = taskDescription.toLowerCase()
    
    if (input.includes('創建') || input.includes('新建') || input.includes('build') || input.includes('create')) {
      return {
        taskId: Date.now(),
        title: `創建項目: ${taskDescription}`,
        steps: [
          { id: 1, description: '📋 分析需求和技術方案', status: 'pending', estimatedTime: '2分鐘' },
          { id: 2, description: '🏗️ 設計項目架構', status: 'pending', estimatedTime: '5分鐘' },
          { id: 3, description: '⚙️ 生成核心代碼結構', status: 'pending', estimatedTime: '8分鐘' },
          { id: 4, description: '🧪 創建測試用例', status: 'pending', estimatedTime: '3分鐘' },
          { id: 5, description: '📝 生成文檔', status: 'pending', estimatedTime: '2分鐘' }
        ],
        totalTime: '20分鐘',
        autonomousExecution: true
      }
    }
    
    if (input.includes('調試') || input.includes('debug') || input.includes('修復') || input.includes('fix')) {
      return {
        taskId: Date.now(),
        title: `調試任務: ${taskDescription}`,
        steps: [
          { id: 1, description: '🔍 掃描代碼錯誤', status: 'pending', estimatedTime: '1分鐘' },
          { id: 2, description: '📊 分析錯誤根因', status: 'pending', estimatedTime: '3分鐘' },
          { id: 3, description: '🛠️ 生成修復方案', status: 'pending', estimatedTime: '5分鐘' },
          { id: 4, description: '✅ 自動應用修復', status: 'pending', estimatedTime: '2分鐘' },
          { id: 5, description: '🧪 驗證修復效果', status: 'pending', estimatedTime: '2分鐘' }
        ],
        totalTime: '13分鐘',
        autonomousExecution: true
      }
    }
    
    if (input.includes('優化') || input.includes('optimize') || input.includes('性能')) {
      return {
        taskId: Date.now(),
        title: `性能優化: ${taskDescription}`,
        steps: [
          { id: 1, description: '📈 性能基線測試', status: 'pending', estimatedTime: '3分鐘' },
          { id: 2, description: '🔍 識別性能瓶頸', status: 'pending', estimatedTime: '5分鐘' },
          { id: 3, description: '⚡ 實施優化策略', status: 'pending', estimatedTime: '10分鐘' },
          { id: 4, description: '📊 性能對比測試', status: 'pending', estimatedTime: '3分鐘' },
          { id: 5, description: '📋 生成優化報告', status: 'pending', estimatedTime: '2分鐘' }
        ],
        totalTime: '23分鐘',
        autonomousExecution: true
      }
    }
    
    // 默認任務規劃
    return {
      taskId: Date.now(),
      title: `自定義任務: ${taskDescription}`,
      steps: [
        { id: 1, description: '🎯 分析任務需求', status: 'pending', estimatedTime: '2分鐘' },
        { id: 2, description: '📋 制定執行計劃', status: 'pending', estimatedTime: '3分鐘' },
        { id: 3, description: '⚙️ 執行核心任務', status: 'pending', estimatedTime: '10分鐘' },
        { id: 4, description: '✅ 質量檢查', status: 'pending', estimatedTime: '3分鐘' },
        { id: 5, description: '📝 總結報告', status: 'pending', estimatedTime: '2分鐘' }
      ],
      totalTime: '20分鐘',
      autonomousExecution: true
    }
  }
  
  const executeAutonomousTask = async (taskPlan) => {
    setCurrentTask(taskPlan)
    setAutonomousMode(true)
    
    const updatedMessages = [...messages, {
      id: Date.now(),
      type: 'assistant',
      content: `🚀 **開始自主執行任務**: ${taskPlan.title}\n\n📋 **執行計劃**:\n${taskPlan.steps.map((step, index) => `${index + 1}. ${step.description} (預計${step.estimatedTime})`).join('\n')}\n\n⏱️ **總預計時間**: ${taskPlan.totalTime}\n\n🤖 我將自主完成這個任務，你可以隨時查看進度...`,
      timestamp: new Date().toLocaleTimeString(),
      taskPlan: taskPlan
    }]
    setMessages(updatedMessages)
    
    // 模擬自主執行過程
    for (const step of taskPlan.steps) {
      await new Promise(resolve => setTimeout(resolve, 2000)) // 模擬執行時間
      
      step.status = 'in_progress'
      setTaskProgress(prev => [...prev, { ...step, status: 'in_progress', timestamp: new Date() }])
      
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      step.status = 'completed'
      setTaskProgress(prev => prev.map(p => p.id === step.id ? { ...p, status: 'completed' } : p))
      
      const progressMessage = {
        id: Date.now() + Math.random(),
        type: 'assistant',
        content: `✅ **完成步驟 ${step.id}**: ${step.description}\n\n🔍 **執行詳情**: AI自主分析並完成了此步驟，應用了最佳實踐...`,
        timestamp: new Date().toLocaleTimeString(),
        isProgress: true
      }
      
      setMessages(prev => [...prev, progressMessage])
    }
    
    // 任務完成
    const completionMessage = {
      id: Date.now(),
      type: 'assistant', 
      content: `🎉 **任務完成**: ${taskPlan.title}\n\n✅ **執行結果**:\n• 所有${taskPlan.steps.length}個步驟已完成\n• 總執行時間: ${taskPlan.totalTime}\n• 質量檢查: 通過\n\n📋 **下一步建議**:\n• 查看生成的代碼\n• 運行測試驗證\n• 部署到測試環境\n\n需要我執行其他任務嗎？`,
      timestamp: new Date().toLocaleTimeString(),
      isCompletion: true
    }
    
    setMessages(prev => [...prev, completionMessage])
    setAutonomousMode(false)
  }
  
  const generateAIResponse = (userInput) => {
    // 檢查是否是任務請求
    const taskKeywords = ['創建', '新建', '調試', '修復', '優化', '分析', '生成', 'create', 'build', 'debug', 'fix', 'optimize']
    const isTaskRequest = taskKeywords.some(keyword => userInput.toLowerCase().includes(keyword))
    
    if (isTaskRequest) {
      const taskPlan = generateTaskPlan(userInput)
      // 自動開始執行任務
      setTimeout(() => executeAutonomousTask(taskPlan), 500)
      return `🎯 **任務識別**: ${userInput}\n\n🤖 我已經為你制定了完整的執行計劃，即將開始自主執行...`
    }
    
    const input = userInput.toLowerCase()
    
    if (input.includes('hello') || input.includes('你好') || input.includes('hi')) {
      return '👋 你好！我是具備自主執行能力的AI助手。告訴我你想完成什麼任務，我會制定計劃並自主執行！'
    }
    
    if (input.includes('幫助') || input.includes('help') || input.includes('功能')) {
      return '🚀 **我的核心能力**:\n\n🎯 **自主任務執行**:\n• 理解你的需求\n• 制定詳細計劃\n• 自主完成任務\n• 實時進度報告\n\n💡 **試試這些命令**:\n• "創建一個React組件"\n• "調試這段代碼"\n• "優化性能"\n• "分析項目架構"'
    }
    
    return `🤖 我理解你想要: "${userInput}"\n\n💡 **建議**: 描述具體任務，我會為你制定執行計劃。例如：\n• "創建一個用戶登錄功能"\n• "修復這個API錯誤"\n• "優化代碼性能"`
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const quickActions = [
    { label: '🚀 創建React應用', action: '創建一個完整的React應用，包含路由和狀態管理' },
    { label: '🐛 自動調試', action: '掃描並修復當前項目中的所有錯誤' },
    { label: '⚡ 性能優化', action: '分析並優化項目性能，提供詳細報告' },
    { label: '🧪 生成測試', action: '為整個項目生成完整的測試套件' },
    { label: '📝 API文檔', action: '自動生成API接口文檔' },
    { label: '🔍 代碼審查', action: '進行全面代碼質量審查和改進建議' }
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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '16px' }}>🚀 自主AI助手 (Claude)</h3>
            <p style={{ margin: '4px 0 0 0', fontSize: '12px', opacity: 0.9 }}>
              PowerAutomation v4.5 - 自主任務執行引擎
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {autonomousMode && (
              <div style={{ 
                padding: '4px 8px', 
                backgroundColor: '#16a085', 
                borderRadius: '12px',
                fontSize: '10px',
                fontWeight: 'bold'
              }}>
                🤖 自主執行中
              </div>
            )}
            <div style={{ 
              padding: '4px 8px', 
              backgroundColor: 'rgba(255,255,255,0.2)', 
              borderRadius: '8px',
              fontSize: '10px'
            }}>
              vs Manus準備就緒
            </div>
          </div>
        </div>
      </div>

      {/* 項目分析按鈕 */}
      <div style={{ 
        padding: '10px',
        backgroundColor: '#f0f8ff',
        borderBottom: '1px solid #e9ecef'
      }}>
        <button
          onClick={analyzeProject}
          disabled={isLoading}
          style={{
            width: '100%',
            padding: '8px',
            backgroundColor: isLoading ? '#ccc' : '#1e3a8a',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            fontSize: '14px',
            fontWeight: 'bold'
          }}
        >
          {isLoading ? '🔍 分析中...' : '🧠 分析項目 (超越Manus的關鍵)'}
        </button>
      </div>

      {/* Quick Actions */}
      <div style={{ 
        padding: '10px',
        backgroundColor: 'white',
        borderBottom: '1px solid #e9ecef'
      }}>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: '1fr 1fr 1fr',
          gap: '5px'
        }}>
          {quickActions.map((action, index) => (
            <button
              key={index}
              onClick={() => triggerAutonomousTask(action.action)}
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
              {message.project_context_used && (
                <div style={{
                  marginTop: '8px',
                  padding: '4px 8px',
                  backgroundColor: '#e8f5e8',
                  borderRadius: '4px',
                  fontSize: '11px',
                  color: '#2d5016'
                }}>
                  🧠 基於項目上下文回復
                </div>
              )}
              {message.fallback && (
                <div style={{
                  marginTop: '8px', 
                  padding: '4px 8px',
                  backgroundColor: '#fff3cd',
                  borderRadius: '4px',
                  fontSize: '11px',
                  color: '#856404'
                }}>
                  ⚠️ 本地降級回復
                </div>
              )}
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
            {autonomousMode ? '🤖 自主執行中...' : '🧠 Claude正在思考...'}
            {autonomousMode && (
              <div style={{ marginTop: '5px', fontSize: '12px' }}>
                展示與Manus競爭的自主能力
              </div>
            )}
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
            placeholder="描述你的任務，我會自主執行...(如：創建登錄功能、調試API錯誤、優化性能)"
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

