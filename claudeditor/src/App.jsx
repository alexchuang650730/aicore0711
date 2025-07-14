import React, { useState } from 'react'
import MonacoEditor from './editor/MonacoEditor'
import FileExplorer from './components/FileExplorer'
import AIAssistant from './ai-assistant/AIAssistant'
import ToolManager from './components/ToolManager'
import './App.css'

function App() {
  const [currentFile, setCurrentFile] = useState(null)
  const [fileContent, setFileContent] = useState('')

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

  return (
    <div className="app">
      <header className="app-header">
        <h1>ClaudEditor</h1>
        <p>AI-Powered Code Editor with PowerAutomation</p>
      </header>
      
      <div className="app-content">
        <div className="file-explorer-section">
          <FileExplorer 
            onFileSelect={handleFileSelect}
            onProjectOpen={handleProjectOpen}
          />
        </div>
        
        <div className="editor-section">
          <MonacoEditor 
            currentFile={currentFile}
            fileContent={fileContent}
            onFileContentChange={handleFileContentChange}
          />
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

