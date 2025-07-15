import React, { useState } from 'react'
import MonacoEditor from './editor/MonacoEditor'
import FileExplorer from './components/FileExplorer'
import TaskList from './components/TaskList'
import AIAssistant from './ai-assistant/AIAssistant'
import ToolManager from './components/ToolManager'
import './App.css'

function App() {
  const [currentFile, setCurrentFile] = useState(null)
  const [fileContent, setFileContent] = useState('')
  const [selectedTask, setSelectedTask] = useState(null)
  const [activeLeftPanel, setActiveLeftPanel] = useState('tasks') // 'tasks', 'files'

  const handleFileSelect = (file, content) => {
    setCurrentFile(file)
    setFileContent(content)
  }

  const handleFileContentChange = (newContent) => {
    setFileContent(newContent)
  }

  const handleProjectOpen = (projectPath) => {
    console.log('Opening project:', projectPath)
    // 可以在這裡添加項目打開邏輯
  }

  const handleTaskSelect = (task) => {
    setSelectedTask(task)
    console.log('Selected task:', task)
    
    // 处理不同类型的任务选择
    if (task && task.type) {
      switch (task.type) {
        case 'open_file':
          // 打开文件请求
          console.log('Opening file from task:', task.filePath)
          // 这里可以触发文件打开逻辑
          break;
        
        case 'edit_code':
          // 代码编辑请求
          console.log('Edit code request:', task.changes)
          // 这里可以应用代码更改
          break;
        
        case 'show_diff':
          // 显示差异请求
          console.log('Show diff request:', task.before, task.after)
          // 这里可以显示差异视图
          break;
        
        default:
          // 普通任务选择
          break;
      }
    }
  }

  const handleAgentAssign = (taskId, agentId) => {
    console.log('Agent assigned:', { taskId, agentId })
    // 这里可以处理智能体分配逻辑
  }

  return (
    <div className="app">
      <header className="app-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ margin: 0, fontSize: '20px' }}>ClaudeEditor</h1>
            <p style={{ margin: '2px 0 0 0', fontSize: '12px', opacity: 0.8 }}>
              AI-Powered Code Editor with PowerAutomation v4.6.9.5
            </p>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={() => setActiveLeftPanel('tasks')}
              style={{
                padding: '6px 12px',
                backgroundColor: activeLeftPanel === 'tasks' ? '#1e3a8a' : 'transparent',
                color: activeLeftPanel === 'tasks' ? 'white' : '#1e3a8a',
                border: '1px solid #1e3a8a',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              🎯 任务管理
            </button>
            <button
              onClick={() => setActiveLeftPanel('files')}
              style={{
                padding: '6px 12px',
                backgroundColor: activeLeftPanel === 'files' ? '#1e3a8a' : 'transparent',
                color: activeLeftPanel === 'files' ? 'white' : '#1e3a8a',
                border: '1px solid #1e3a8a',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              📁 文件浏览
            </button>
          </div>
        </div>
      </header>
      
      <div className="app-content" style={{ display: 'flex', height: 'calc(100vh - 80px)' }}>
        {/* Left Panel */}
        <div style={{ display: 'flex' }}>
          {activeLeftPanel === 'tasks' && (
            <TaskList 
              onTaskSelect={handleTaskSelect}
              onAgentAssign={handleAgentAssign}
            />
          )}
          {activeLeftPanel === 'files' && (
            <div style={{ width: '350px' }}>
              <FileExplorer 
                onFileSelect={handleFileSelect}
                onProjectOpen={handleProjectOpen}
              />
            </div>
          )}
        </div>
        
        {/* Main Editor Area */}
        <div style={{ 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column',
          minWidth: 0 // 防止 flex 子元素溢出
        }}>
          {/* Task Info Bar */}
          {selectedTask && (
            <div style={{
              padding: '8px 15px',
              backgroundColor: '#e3f2fd',
              borderBottom: '1px solid #e9ecef',
              fontSize: '12px',
              color: '#1976d2'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>
                  🎯 当前任务: <strong>{selectedTask.title}</strong>
                  {selectedTask.assignedAgent && (
                    <span style={{ marginLeft: '10px', opacity: 0.8 }}>
                      分配给: {selectedTask.assignedAgent}
                    </span>
                  )}
                </span>
                <button
                  onClick={() => setSelectedTask(null)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#1976d2',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                >
                  ✕
                </button>
              </div>
              {selectedTask.description && (
                <div style={{ marginTop: '4px', opacity: 0.8 }}>
                  {selectedTask.description}
                </div>
              )}
            </div>
          )}
          
          {/* Monaco Editor */}
          <div style={{ flex: 1 }}>
            <MonacoEditor 
              currentFile={currentFile}
              fileContent={fileContent}
              onFileContentChange={handleFileContentChange}
              selectedTask={selectedTask} // 传递选中的任务给编辑器
            />
          </div>
        </div>
        
        {/* Right Sidebar */}
        <div style={{ 
          width: '300px', 
          backgroundColor: '#f8f9fa',
          borderLeft: '1px solid #e9ecef',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <div style={{ flex: 1 }}>
            <AIAssistant selectedTask={selectedTask} />
          </div>
          <div style={{ 
            borderTop: '1px solid #e9ecef',
            maxHeight: '200px',
            overflowY: 'auto'
          }}>
            <ToolManager />
          </div>
        </div>
      </div>
    </div>
  )
}

export default App

