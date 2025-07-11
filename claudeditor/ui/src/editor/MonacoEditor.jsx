import React, { useState, useRef } from 'react'
import Editor from '@monaco-editor/react'

const MonacoEditor = () => {
  const [code, setCode] = useState(`// Welcome to ClaudEditor
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

  const [language, setLanguage] = useState('javascript')
  const [theme, setTheme] = useState('vs-dark')
  const editorRef = useRef(null)

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

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Editor Toolbar */}
      <div style={{ 
        padding: '10px', 
        backgroundColor: '#2d2d30', 
        borderBottom: '1px solid #3e3e42',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        color: '#cccccc'
      }}>
        <span style={{ fontWeight: 'bold', color: '#569CD6' }}>
          📝 ClaudEditor - Monaco Editor
        </span>
        
        <select 
          value={language} 
          onChange={(e) => setLanguage(e.target.value)}
          style={{ 
            backgroundColor: '#3c3c3c', 
            color: '#cccccc', 
            border: '1px solid #464647',
            padding: '4px 8px',
            borderRadius: '3px'
          }}
        >
          <option value="javascript">JavaScript</option>
          <option value="typescript">TypeScript</option>
          <option value="python">Python</option>
          <option value="html">HTML</option>
          <option value="css">CSS</option>
          <option value="json">JSON</option>
        </select>

        <select 
          value={theme} 
          onChange={(e) => setTheme(e.target.value)}
          style={{ 
            backgroundColor: '#3c3c3c', 
            color: '#cccccc', 
            border: '1px solid #464647',
            padding: '4px 8px',
            borderRadius: '3px'
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
            cursor: 'pointer'
          }}
        >
          Format
        </button>

        <button 
          onClick={runCode}
          style={{ 
            backgroundColor: '#16825d', 
            color: 'white', 
            border: 'none',
            padding: '4px 12px',
            borderRadius: '3px',
            cursor: 'pointer'
          }}
        >
          Run
        </button>
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

