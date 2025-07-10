import React from 'react'
import MonacoEditor from './editor/MonacoEditor'
import AIAssistant from './ai-assistant/AIAssistant'
import ToolManager from './components/ToolManager'
import './App.css'

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>ClaudEditor</h1>
        <p>AI-Powered Code Editor with PowerAutomation</p>
      </header>
      
      <div className="app-content">
        <div className="editor-section">
          <MonacoEditor />
        </div>
        
        <div className="sidebar">
          <AIAssistant />
          <ToolManager />
        </div>
      </div>
    </div>
  )
}

export default App

