import React, { useState, useEffect } from 'react'

const FileExplorer = ({ onFileSelect, onProjectOpen }) => {
  const [currentPath, setCurrentPath] = useState('/')
  const [files, setFiles] = useState([])
  const [repositories, setRepositories] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [activeRepository, setActiveRepository] = useState(null)
  const [showRepoDialog, setShowRepoDialog] = useState(false)
  const [showEC2Dialog, setShowEC2Dialog] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState('disconnected')
  const [ec2Connections, setEC2Connections] = useState([])

  // AG-UI SmartUI 智能倉庫管理
  const [smartRepoManager] = useState({
    recentRepos: [
      {
        id: 'repo-1',
        name: 'powerautomation-v4.5',
        type: 'local',
        path: '/Users/alexchuang/Desktop/alex/tests/package/aicore0711',
        lastAccessed: '2025-01-14',
        branch: 'main',
        status: 'active'
      },
      {
        id: 'repo-2', 
        name: 'claudeditor-desktop',
        type: 'github',
        url: 'https://github.com/alexchuang650730/claudeditor-desktop.git',
        lastAccessed: '2025-01-13',
        branch: 'develop',
        status: 'synced'
      }
    ],
    ec2Instances: [
      {
        id: 'ec2-1',
        name: 'PowerAutomation-Prod',
        host: 'ec2-13-125-123-45.ap-northeast-1.compute.amazonaws.com',
        user: 'ubuntu',
        status: 'running',
        lastConnected: '2025-01-14'
      },
      {
        id: 'ec2-2',
        name: 'ClaudEditor-Dev',
        host: 'ec2-54-248-67-89.ap-northeast-1.compute.amazonaws.com', 
        user: 'ec2-user',
        status: 'stopped',
        lastConnected: '2025-01-12'
      }
    ]
  })

  // 模擬文件系統結構 (增強版)
  const mockFileSystem = {
    '/': {
      type: 'directory',
      children: {
        'Local Projects': { 
          type: 'directory', 
          children: {
            'powerautomation-v4.5': {
              type: 'repository',
              branch: 'main',
              children: {
                'claudeditor': {
                  type: 'directory',
                  children: {
                    'src': {
                      type: 'directory',
                      children: {
                        'App.jsx': { type: 'file', language: 'javascript' },
                        'components': {
                          type: 'directory',
                          children: {
                            'FileExplorer.jsx': { type: 'file', language: 'javascript' },
                            'ToolManager.jsx': { type: 'file', language: 'javascript' }
                          }
                        }
                      }
                    },
                    'package.json': { type: 'file', language: 'json' },
                    'README.md': { type: 'file', language: 'markdown' }
                  }
                }
              }
            },
            'my-react-app': {
              type: 'repository',
              branch: 'develop',
              children: {
                'src': {
                  type: 'directory',
                  children: {
                    'App.js': { type: 'file', language: 'javascript' },
                    'index.js': { type: 'file', language: 'javascript' }
                  }
                }
              }
            }
          }
        },
        'Remote Repositories': { 
          type: 'directory', 
          children: {
            'github-repos': {
              type: 'directory',
              children: {}
            }
          }
        },
        'EC2 Remote Files': { 
          type: 'directory', 
          children: {
            'PowerAutomation-Prod': {
              type: 'remote',
              host: 'ec2-13-125-123-45',
              children: {
                'home': {
                  type: 'directory',
                  children: {
                    'ubuntu': {
                      type: 'directory',
                      children: {
                        'projects': {
                          type: 'directory',
                          children: {
                            'app.py': { type: 'file', language: 'python' },
                            'config.json': { type: 'file', language: 'json' }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }

  const getCurrentDirectory = () => {
    const parts = currentPath.split('/').filter(p => p)
    let current = mockFileSystem['/']
    
    for (const part of parts) {
      if (current.children && current.children[part]) {
        current = current.children[part]
      }
    }
    
    return current
  }

  const loadFiles = () => {
    const current = getCurrentDirectory()
    if (current && current.children) {
      const fileList = Object.entries(current.children).map(([name, item]) => ({
        name,
        type: item.type,
        language: item.language || null,
        branch: item.branch || null,
        host: item.host || null,
        path: `${currentPath}${currentPath.endsWith('/') ? '' : '/'}${name}`
      }))
      setFiles(fileList)
    }
  }

  useEffect(() => {
    loadFiles()
    setRepositories(smartRepoManager.recentRepos)
    setEC2Connections(smartRepoManager.ec2Instances)
  }, [currentPath])

  const handleFileClick = (file) => {
    if (file.type === 'directory' || file.type === 'repository' || file.type === 'remote') {
      setCurrentPath(file.path)
      if (file.type === 'repository') {
        setActiveRepository(file)
      }
    } else {
      setSelectedFile(file)
      if (onFileSelect) {
        const mockContent = generateMockContent(file)
        onFileSelect(file, mockContent)
      }
    }
  }

  const generateMockContent = (file) => {
    switch (file.language) {
      case 'javascript':
        return `// ${file.name} - AG-UI SmartUI Enhanced
import React from 'react';
import { AgUIComponent } from '@ag-ui/core';

const ${file.name.replace('.jsx', '').replace('.js', '')} = () => {
  return (
    <AgUIComponent smartUI={{
      autoLayout: true,
      responsiveDesign: true,
      accessibilityCompliant: true
    }}>
      <div className="smart-container">
        <h1>Hello from ${file.name}</h1>
        <p>Powered by AG-UI + SmartUI</p>
      </div>
    </AgUIComponent>
  );
};

export default ${file.name.replace('.jsx', '').replace('.js', '')};`
      case 'python':
        return `# ${file.name} - AG-UI Backend Integration
from ag_ui_mcp import SmartUIEngine
from smart_ui import AutoLayoutManager

class ${file.name.replace('.py', '').title()}:
    def __init__(self):
        self.smart_ui = SmartUIEngine()
        self.layout_manager = AutoLayoutManager()
    
    def process_request(self):
        """處理來自 AG-UI 的智能請求"""
        print(f"Processing in {file.name}")
        return self.smart_ui.generate_response()
    
if __name__ == "__main__":
    app = ${file.name.replace('.py', '').title()}()
    app.process_request()`
      case 'json':
        return `{
  "name": "ag-ui-smartui-project",
  "version": "4.5.0",
  "description": "AG-UI + SmartUI 智能代碼編輯器",
  "main": "index.js",
  "dependencies": {
    "@ag-ui/core": "^2.1.0",
    "@ag-ui/react": "^2.1.0",
    "smart-ui-engine": "^1.5.0",
    "react": "^18.0.0"
  },
  "agui": {
    "smartLayout": true,
    "autoGeneration": true,
    "intelligentRouting": true
  }
}`
      default:
        return `# ${file.name} - AG-UI SmartUI Documentation

## 智能界面生成

這個文件展示了 AG-UI 與 SmartUI 的集成功能：

### 特性
- 🤖 智能代碼生成
- 🎨 自適應界面布局  
- 🔄 實時協作編輯
- 📱 響應式設計

### AG-UI 組件
- AgUIComponent: 核心智能組件
- SmartLayout: 自動布局管理
- AutoGenerator: 代碼自動生成

通過 AG-UI MCP 協議實現無縫集成。`
    }
  }

  const goBack = () => {
    const parts = currentPath.split('/').filter(p => p)
    if (parts.length > 0) {
      parts.pop()
      setCurrentPath('/' + parts.join('/'))
    }
  }

  const cloneGitRepository = async () => {
    const repoUrl = prompt('請輸入 GitHub 倉庫 URL:')
    if (repoUrl) {
      try {
        // 模擬 AG-UI Git 克隆過程
        setConnectionStatus('cloning')
        
        // 模擬進度
        setTimeout(() => {
          const repoName = repoUrl.split('/').pop().replace('.git', '')
          const newRepo = {
            id: `repo-${Date.now()}`,
            name: repoName,
            type: 'github',
            url: repoUrl,
            lastAccessed: new Date().toISOString().split('T')[0],
            branch: 'main',
            status: 'cloned'
          }
          
          setRepositories(prev => [...prev, newRepo])
          setConnectionStatus('connected')
          alert(`✅ 成功克隆倉庫: ${repoName}\n🔧 使用 AG-UI SmartUI 自動分析代碼結構`)
          
          // 自動切換到新克隆的倉庫
          setCurrentPath(`/Remote Repositories/github-repos/${repoName}`)
        }, 2000)
        
      } catch (error) {
        setConnectionStatus('error')
        alert('❌ 克隆失敗: ' + error.message)
      }
    }
  }

  const connectToEC2 = async (instance) => {
    try {
      setConnectionStatus('connecting')
      
      // 模擬 AG-UI EC2 連接過程
      setTimeout(() => {
        setConnectionStatus('connected')
        setEC2Connections(prev => 
          prev.map(conn => 
            conn.id === instance.id 
              ? { ...conn, status: 'connected', lastConnected: new Date().toISOString().split('T')[0] }
              : conn
          )
        )
        
        alert(`🌐 已連接到 EC2: ${instance.name}\n📡 使用 AG-UI 智能文件同步`)
        setCurrentPath(`/EC2 Remote Files/${instance.name}`)
        setShowEC2Dialog(false)
      }, 1500)
      
    } catch (error) {
      setConnectionStatus('error')
      alert('❌ EC2 連接失敗: ' + error.message)
    }
  }

  const getFileIcon = (type, language) => {
    if (type === 'repository') return '📚'
    if (type === 'remote') return '🌐'
    if (type === 'directory') return '📁'
    
    switch (language) {
      case 'javascript': return '🟨'
      case 'python': return '🐍'
      case 'json': return '⚙️'
      case 'markdown': return '📝'
      case 'html': return '🌐'
      case 'css': return '🎨'
      default: return '📄'
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': case 'connected': case 'running': return '#16a34a'
      case 'synced': case 'cloned': return '#2563eb'
      case 'stopped': return '#dc2626'
      case 'connecting': case 'cloning': return '#ea580c'
      default: return '#6b7280'
    }
  }

  return (
    <div style={{ 
      width: '300px', 
      height: '100%', 
      backgroundColor: '#f8f9fa', 
      borderRight: '1px solid #dee2e6',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* AG-UI SmartUI 智能頭部 */}
      <div style={{ 
        padding: '10px', 
        backgroundColor: '#1e3a8a', 
        color: 'white',
        borderBottom: '1px solid #dee2e6'
      }}>
        <h4 style={{ margin: 0, fontSize: '14px', display: 'flex', alignItems: 'center' }}>
          🤖 AG-UI SmartExplorer
        </h4>
        <p style={{ margin: '4px 0 0 0', fontSize: '11px', opacity: 0.9 }}>
          智能代碼倉庫管理 + EC2 遠程連接
        </p>
      </div>

      {/* 當前倉庫狀態 */}
      {activeRepository && (
        <div style={{
          padding: '8px',
          backgroundColor: '#e3f2fd',
          borderBottom: '1px solid #bbdefb',
          fontSize: '12px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontWeight: 'bold' }}>📚 {activeRepository.name}</span>
            <span style={{ 
              backgroundColor: getStatusColor(activeRepository.status),
              color: 'white',
              padding: '2px 6px',
              borderRadius: '10px',
              fontSize: '10px'
            }}>
              {activeRepository.branch}
            </span>
          </div>
        </div>
      )}

      {/* 工具列 - AG-UI 增強版 */}
      <div style={{ 
        padding: '8px', 
        backgroundColor: '#e9ecef', 
        borderBottom: '1px solid #dee2e6',
        display: 'flex',
        gap: '4px',
        flexWrap: 'wrap'
      }}>
        <button
          onClick={() => setShowRepoDialog(true)}
          style={{
            padding: '4px 8px',
            fontSize: '11px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '3px',
            cursor: 'pointer',
            flex: '1'
          }}
          title="切換倉庫"
        >
          📚 倉庫
        </button>
        <button
          onClick={cloneGitRepository}
          style={{
            padding: '4px 8px',
            fontSize: '11px',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '3px',
            cursor: 'pointer',
            flex: '1'
          }}
          title="克隆 Git 倉庫"
        >
          📥 克隆
        </button>
        <button
          onClick={() => setShowEC2Dialog(true)}
          style={{
            padding: '4px 8px',
            fontSize: '11px',
            backgroundColor: '#17a2b8',
            color: 'white',
            border: 'none',
            borderRadius: '3px',
            cursor: 'pointer',
            flex: '1'
          }}
          title="連接 EC2"
        >
          🌐 EC2
        </button>
      </div>

      {/* 連接狀態指示器 */}
      {connectionStatus !== 'disconnected' && (
        <div style={{
          padding: '6px 8px',
          backgroundColor: connectionStatus === 'connected' ? '#d4edda' : 
                          connectionStatus === 'connecting' || connectionStatus === 'cloning' ? '#fff3cd' : '#f8d7da',
          borderBottom: '1px solid #dee2e6',
          fontSize: '11px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}>
          <span>
            {connectionStatus === 'connected' ? '🟢' : 
             connectionStatus === 'connecting' ? '🟡' :
             connectionStatus === 'cloning' ? '🔄' : '🔴'}
          </span>
          <span>
            {connectionStatus === 'connected' ? 'AG-UI 智能連接已建立' :
             connectionStatus === 'connecting' ? '正在連接 EC2...' :
             connectionStatus === 'cloning' ? '正在克隆倉庫...' : '連接錯誤'}
          </span>
        </div>
      )}

      {/* 路徑導航 */}
      <div style={{ 
        padding: '8px', 
        fontSize: '12px', 
        backgroundColor: '#fff',
        borderBottom: '1px solid #dee2e6',
        display: 'flex',
        alignItems: 'center'
      }}>
        <button
          onClick={goBack}
          disabled={currentPath === '/'}
          style={{
            padding: '2px 6px',
            fontSize: '12px',
            backgroundColor: currentPath === '/' ? '#ccc' : '#6c757d',
            color: 'white',
            border: 'none',
            borderRadius: '3px',
            marginRight: '8px',
            cursor: currentPath === '/' ? 'not-allowed' : 'pointer'
          }}
        >
          ⬅️
        </button>
        <span style={{ 
          fontFamily: 'monospace', 
          fontSize: '10px',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap'
        }}>
          {currentPath}
        </span>
      </div>

      {/* 智能文件列表 */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {files.map((file, index) => (
          <div
            key={index}
            onClick={() => handleFileClick(file)}
            style={{
              padding: '8px 12px',
              cursor: 'pointer',
              borderBottom: '1px solid #f1f3f4',
              backgroundColor: selectedFile?.path === file.path ? '#e3f2fd' : 'transparent',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}
            onMouseEnter={(e) => e.target.style.backgroundColor = '#f8f9fa'}
            onMouseLeave={(e) => e.target.style.backgroundColor = 
              selectedFile?.path === file.path ? '#e3f2fd' : 'transparent'}
          >
            <div style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
              <span style={{ marginRight: '8px', fontSize: '16px' }}>
                {getFileIcon(file.type, file.language)}
              </span>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '13px', fontWeight: file.type === 'repository' ? 'bold' : 'normal' }}>
                  {file.name}
                </span>
                {file.branch && (
                  <span style={{ fontSize: '10px', color: '#6c757d' }}>
                    {file.branch} branch
                  </span>
                )}
                {file.host && (
                  <span style={{ fontSize: '10px', color: '#17a2b8' }}>
                    {file.host}
                  </span>
                )}
              </div>
            </div>
            {file.type === 'repository' && (
              <span style={{
                fontSize: '10px',
                padding: '1px 4px',
                backgroundColor: '#28a745',
                color: 'white',
                borderRadius: '8px'
              }}>
                Git
              </span>
            )}
            {file.type === 'remote' && (
              <span style={{
                fontSize: '10px',
                padding: '1px 4px',
                backgroundColor: '#17a2b8',
                color: 'white',
                borderRadius: '8px'
              }}>
                SSH
              </span>
            )}
          </div>
        ))}
      </div>

      {/* 倉庫選擇對話框 */}
      {showRepoDialog && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            width: '500px',
            maxHeight: '400px',
            overflow: 'auto'
          }}>
            <h3 style={{ margin: '0 0 15px 0' }}>🤖 AG-UI 智能倉庫管理</h3>
            <div style={{ marginBottom: '15px' }}>
              {repositories.map(repo => (
                <div key={repo.id} style={{
                  padding: '12px',
                  marginBottom: '8px',
                  backgroundColor: '#f8f9fa',
                  border: '1px solid #dee2e6',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }} onClick={() => {
                  setCurrentPath(`/Local Projects/${repo.name}`)
                  setActiveRepository(repo)
                  setShowRepoDialog(false)
                }}>
                  <div>
                    <div style={{ fontWeight: 'bold', fontSize: '14px' }}>
                      📚 {repo.name}
                    </div>
                    <div style={{ fontSize: '12px', color: '#6c757d' }}>
                      {repo.type === 'local' ? '本地倉庫' : 'GitHub 倉庫'} • {repo.branch} • {repo.lastAccessed}
                    </div>
                  </div>
                  <span style={{
                    fontSize: '10px',
                    padding: '2px 6px',
                    backgroundColor: getStatusColor(repo.status),
                    color: 'white',
                    borderRadius: '10px'
                  }}>
                    {repo.status}
                  </span>
                </div>
              ))}
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <button
                onClick={cloneGitRepository}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#28a745',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                📥 克隆新倉庫
              </button>
              <button
                onClick={() => setShowRepoDialog(false)}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}

      {/* EC2 連接對話框 */}
      {showEC2Dialog && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            width: '500px',
            maxHeight: '400px',
            overflow: 'auto'
          }}>
            <h3 style={{ margin: '0 0 15px 0' }}>🌐 AG-UI EC2 智能連接</h3>
            <div style={{ marginBottom: '15px' }}>
              {ec2Connections.map(instance => (
                <div key={instance.id} style={{
                  padding: '12px',
                  marginBottom: '8px',
                  backgroundColor: '#f8f9fa',
                  border: '1px solid #dee2e6',
                  borderRadius: '4px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <div style={{ fontWeight: 'bold', fontSize: '14px' }}>
                      🖥️ {instance.name}
                    </div>
                    <div style={{ fontSize: '11px', color: '#6c757d', marginTop: '2px' }}>
                      {instance.user}@{instance.host}
                    </div>
                    <div style={{ fontSize: '10px', color: '#6c757d' }}>
                      最後連接: {instance.lastConnected}
                    </div>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
                    <span style={{
                      fontSize: '10px',
                      padding: '2px 6px',
                      backgroundColor: getStatusColor(instance.status),
                      color: 'white',
                      borderRadius: '10px'
                    }}>
                      {instance.status}
                    </span>
                    <button
                      onClick={() => connectToEC2(instance)}
                      disabled={instance.status === 'stopped'}
                      style={{
                        padding: '4px 8px',
                        fontSize: '10px',
                        backgroundColor: instance.status === 'stopped' ? '#ccc' : '#17a2b8',
                        color: 'white',
                        border: 'none',
                        borderRadius: '3px',
                        cursor: instance.status === 'stopped' ? 'not-allowed' : 'pointer'
                      }}
                    >
                      {instance.status === 'connected' ? '已連接' : '連接'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowEC2Dialog(false)}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                關閉
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

const getFileIcon = (language) => {
  switch (language) {
    case 'javascript': return '🟨'
    case 'python': return '🐍'
    case 'json': return '⚙️'
    case 'markdown': return '📝'
    case 'html': return '🌐'
    case 'css': return '🎨'
    default: return '📄'
  }
}

export default FileExplorer