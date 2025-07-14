import React, { useState, useRef } from 'react'
import Editor from '@monaco-editor/react'

const MonacoEditor = ({ currentFile, fileContent, onFileContentChange }) => {
  const [code, setCode] = useState(fileContent || `// Welcome to ClaudEditor
// AI-Powered Code Editor with PowerAutomation

function hello() {
  console.log("Hello, ClaudEditor!");
  return "PowerAutomation + ClaudEditor is running!";
}

// Test the function
const result = hello();
console.log(result);

// Example: AI-assisted coding
class PowerAutomationAgent {
  constructor(name) {
    this.name = name;
    this.capabilities = [
      'Code Generation',
      'Bug Detection', 
      'Performance Optimization',
      'Documentation',
      'Testing'
    ];
  }
  
  assist(task) {
    console.log(\`\${this.name} is helping with: \${task}\`);
    return \`AI assistance for \${task} completed!\`;
  }
}

// Initialize AI agent
const aiAgent = new PowerAutomationAgent('Claude');
aiAgent.assist('Code Review');`)

  const [language, setLanguage] = useState(currentFile?.language || 'javascript')
  const [theme, setTheme] = useState('vs-dark')
  const [openTabs, setOpenTabs] = useState([])
  const [activeTab, setActiveTab] = useState(null)
  const editorRef = useRef(null)

  // 當文件改變時更新內容
  React.useEffect(() => {
    if (fileContent !== undefined) {
      setCode(fileContent)
    }
    if (currentFile?.language) {
      setLanguage(currentFile.language)
    }
  }, [fileContent, currentFile])

  // 添加新標籤頁
  React.useEffect(() => {
    if (currentFile && !openTabs.find(tab => tab.path === currentFile.path)) {
      const newTab = {
        name: currentFile.name,
        path: currentFile.path,
        language: currentFile.language,
        content: fileContent
      }
      setOpenTabs(prev => [...prev, newTab])
      setActiveTab(currentFile.path)
    }
  }, [currentFile, fileContent])

  const handleEditorDidMount = (editor, monaco) => {
    editorRef.current = editor
    
    // Configure Monaco editor
    monaco.editor.defineTheme('claudeditor-dark', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'comment', foreground: '6A9955' },
        { token: 'keyword', foreground: '569CD6' },
        { token: 'string', foreground: 'CE9178' },
        { token: 'number', foreground: 'B5CEA8' },
      ],
      colors: {
        'editor.background': '#1e1e1e',
        'editor.foreground': '#d4d4d4',
        'editorLineNumber.foreground': '#858585',
        'editor.selectionBackground': '#264f78',
        'editor.inactiveSelectionBackground': '#3a3d41',
      }
    })
    
    monaco.editor.setTheme('claudeditor-dark')
  }

  const handleEditorChange = (value) => {
    setCode(value || '')
    if (onFileContentChange) {
      onFileContentChange(value || '')
    }
  }

  const closeTab = (tabPath) => {
    setOpenTabs(prev => prev.filter(tab => tab.path !== tabPath))
    if (activeTab === tabPath) {
      const remainingTabs = openTabs.filter(tab => tab.path !== tabPath)
      setActiveTab(remainingTabs.length > 0 ? remainingTabs[0].path : null)
    }
  }

  const switchTab = (tabPath) => {
    setActiveTab(tabPath)
    const tab = openTabs.find(t => t.path === tabPath)
    if (tab) {
      setCode(tab.content)
      setLanguage(tab.language)
    }
  }

  const formatCode = () => {
    if (editorRef.current) {
      editorRef.current.getAction('editor.action.formatDocument').run()
    }
  }

  const runCode = () => {
    try {
      // Simple code execution simulation
      console.log('Executing code...')
      console.log(code)
      alert('Code executed! Check console for output.')
    } catch (error) {
      console.error('Error executing code:', error)
      alert('Error executing code: ' + error.message)
    }
  }

  const getFileIcon = (language) => {
    switch (language) {
      case 'javascript': return '🟨'
      case 'typescript': return '🔷'
      case 'python': return '🐍'
      case 'json': return '⚙️'
      case 'markdown': return '📝'
      case 'html': return '🌐'
      case 'css': return '🎨'
      default: return '📄'
    }
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 標籤頁 */}
      {openTabs.length > 0 && (
        <div style={{ 
          display: 'flex', 
          backgroundColor: '#2d3748',
          borderBottom: '1px solid #4a5568',
          overflowX: 'auto'
        }}>
          {openTabs.map(tab => (
            <div
              key={tab.path}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '8px 12px',
                backgroundColor: activeTab === tab.path ? '#1e3a8a' : '#4a5568',
                color: 'white',
                borderRight: '1px solid #2d3748',
                cursor: 'pointer',
                minWidth: '120px',
                position: 'relative'
              }}
              onClick={() => switchTab(tab.path)}
            >
              <span style={{ fontSize: '12px', marginRight: '8px' }}>
                {getFileIcon(tab.language)}
              </span>
              <span style={{ fontSize: '13px', flexGrow: 1 }}>{tab.name}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  closeTab(tab.path)
                }}
                style={{
                  backgroundColor: 'transparent',
                  border: 'none',
                  color: 'white',
                  cursor: 'pointer',
                  padding: '2px',
                  marginLeft: '4px',
                  fontSize: '12px'
                }}
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      {/* 統一工具欄 */}
      <div style={{ 
        padding: '10px', 
        backgroundColor: '#2d2d30', 
        borderBottom: '1px solid #3e3e42',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        color: '#cccccc'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontWeight: 'bold', color: '#569CD6' }}>
            📝 ClaudEditor
          </span>
          {currentFile && (
            <span style={{ fontSize: '12px', color: '#6c757d' }}>
              {currentFile.name} - {currentFile.path}
            </span>
          )}
        </div>
        
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <select 
            value={language} 
            onChange={(e) => setLanguage(e.target.value)}
            style={{ 
              backgroundColor: '#3c3c3c', 
              color: '#cccccc', 
              border: '1px solid #464647',
              padding: '4px 8px',
              borderRadius: '3px',
              fontSize: '12px'
            }}
          >
            <option value="javascript">JavaScript</option>
            <option value="typescript">TypeScript</option>
            <option value="python">Python</option>
            <option value="html">HTML</option>
            <option value="css">CSS</option>
            <option value="json">JSON</option>
            <option value="markdown">Markdown</option>
          </select>

          <select 
            value={theme} 
            onChange={(e) => setTheme(e.target.value)}
            style={{ 
              backgroundColor: '#3c3c3c', 
              color: '#cccccc', 
              border: '1px solid #464647',
              padding: '4px 8px',
              borderRadius: '3px',
              fontSize: '12px'
            }}
          >
            <option value="vs-dark">Dark</option>
            <option value="light">Light</option>
            <option value="hc-black">High Contrast</option>
          </select>

          <button 
            onClick={formatCode}
            style={{ 
              backgroundColor: '#0e639c', 
              color: 'white', 
              border: 'none',
              padding: '4px 12px',
              borderRadius: '3px',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            🎨 格式化
          </button>

          <button 
            onClick={runCode}
            style={{ 
              backgroundColor: '#16825d', 
              color: 'white', 
              border: 'none',
              padding: '4px 12px',
              borderRadius: '3px',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            ▶️ 運行
          </button>
        </div>
      </div>

      {/* Monaco Editor */}
      <div style={{ flex: 1 }}>
        <Editor
          height="100%"
          language={language}
          theme={theme}
          value={code}
          onChange={handleEditorChange}
          onMount={handleEditorDidMount}
          options={{
            selectOnLineNumbers: true,
            roundedSelection: false,
            readOnly: false,
            cursorStyle: 'line',
            automaticLayout: true,
            minimap: { enabled: true },
            scrollBeyondLastLine: false,
            fontSize: 14,
            lineHeight: 21,
            fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
            wordWrap: 'on',
            lineNumbers: 'on',
            glyphMargin: true,
            folding: true,
            lineDecorationsWidth: 20,
            lineNumbersMinChars: 3,
            renderLineHighlight: 'all',
            contextmenu: true,
            mouseWheelZoom: true,
            smoothScrolling: true,
            cursorBlinking: 'blink',
            cursorSmoothCaretAnimation: true,
            renderWhitespace: 'selection',
            renderControlCharacters: false,
            fontLigatures: true,
            fixedOverflowWidgets: true,
          }}
        />
      </div>
    </div>
  )
}

export default MonacoEditor

