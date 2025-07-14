import React, { useState } from 'react'

const ToolManager = () => {
  const [activeTab, setActiveTab] = useState('mcp')
  const [selectedTool, setSelectedTool] = useState(null)

  const mcpTools = [
    { 
      id: 'zen-mcp', 
      name: 'Zen MCP', 
      status: 'active',
      description: '智能工具协作网络',
      capabilities: ['工具发现', '智能路由', '性能优化']
    },
    { 
      id: 'ag-ui-mcp', 
      name: 'AG-UI MCP', 
      status: 'active',
      description: 'UI自动化测试工具',
      capabilities: ['UI测试', '组件生成', '事件处理']
    },
    { 
      id: 'agent-zero', 
      name: 'Agent Zero', 
      status: 'connected',
      description: '智能代理协调器',
      capabilities: ['任务分解', '代理协调', '结果聚合']
    }
  ]

  const automationTools = [
    {
      id: 'code-gen',
      name: 'Code Generator',
      status: 'ready',
      description: 'AI驱动的代码生成',
      action: 'Generate'
    },
    {
      id: 'test-gen',
      name: 'Test Generator', 
      status: 'ready',
      description: '自动化测试生成',
      action: 'Create Tests'
    },
    {
      id: 'doc-gen',
      name: 'Doc Generator',
      status: 'ready', 
      description: '文档自动生成',
      action: 'Generate Docs'
    },
    {
      id: 'refactor',
      name: 'Code Refactor',
      status: 'ready',
      description: '智能代码重构',
      action: 'Refactor'
    }
  ]

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return '#16a34a'
      case 'connected': return '#2563eb'
      case 'ready': return '#ea580c'
      default: return '#6b7280'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return '🟢'
      case 'connected': return '🔵'
      case 'ready': return '🟠'
      default: return '⚪'
    }
  }

  const handleToolAction = (tool) => {
    setSelectedTool(tool)
    console.log(`Executing ${tool.name}...`)
    // 这里可以集成实际的工具调用逻辑
  }

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
        backgroundColor: '#059669', 
        color: 'white',
        borderBottom: '1px solid #e9ecef'
      }}>
        <h3 style={{ margin: 0, fontSize: '16px' }}>🛠️ Tool Manager</h3>
        <p style={{ margin: '4px 0 0 0', fontSize: '12px', opacity: 0.9 }}>
          PowerAutomation Tool Ecosystem
        </p>
      </div>

      {/* Tabs */}
      <div style={{ 
        display: 'flex',
        backgroundColor: 'white',
        borderBottom: '1px solid #e9ecef'
      }}>
        <button
          onClick={() => setActiveTab('mcp')}
          style={{
            flex: 1,
            padding: '10px',
            border: 'none',
            backgroundColor: activeTab === 'mcp' ? '#059669' : 'transparent',
            color: activeTab === 'mcp' ? 'white' : '#374151',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: activeTab === 'mcp' ? 'bold' : 'normal'
          }}
        >
          MCP Tools
        </button>
        <button
          onClick={() => setActiveTab('automation')}
          style={{
            flex: 1,
            padding: '10px',
            border: 'none',
            backgroundColor: activeTab === 'automation' ? '#059669' : 'transparent',
            color: activeTab === 'automation' ? 'white' : '#374151',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: activeTab === 'automation' ? 'bold' : 'normal'
          }}
        >
          Automation
        </button>
      </div>

      {/* Content */}
      <div style={{ 
        flex: 1, 
        overflowY: 'auto', 
        padding: '10px',
        backgroundColor: 'white'
      }}>
        {activeTab === 'mcp' && (
          <div>
            <h4 style={{ margin: '0 0 15px 0', fontSize: '14px', color: '#374151' }}>
              MCP Protocol Tools
            </h4>
            {mcpTools.map((tool) => (
              <div
                key={tool.id}
                style={{
                  marginBottom: '12px',
                  padding: '12px',
                  border: '1px solid #e5e7eb',
                  borderRadius: '6px',
                  backgroundColor: selectedTool?.id === tool.id ? '#f0fdf4' : '#fafafa',
                  cursor: 'pointer'
                }}
                onClick={() => setSelectedTool(tool)}
              >
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '6px'
                }}>
                  <span style={{ 
                    fontWeight: 'bold', 
                    fontSize: '13px',
                    color: '#111827'
                  }}>
                    {tool.name}
                  </span>
                  <span style={{ 
                    fontSize: '12px',
                    color: getStatusColor(tool.status),
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}>
                    {getStatusIcon(tool.status)} {tool.status}
                  </span>
                </div>
                <p style={{ 
                  margin: '0 0 8px 0', 
                  fontSize: '12px',
                  color: '#6b7280',
                  lineHeight: '1.4'
                }}>
                  {tool.description}
                </p>
                <div style={{ 
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '4px'
                }}>
                  {tool.capabilities.map((cap, index) => (
                    <span
                      key={index}
                      style={{
                        fontSize: '10px',
                        padding: '2px 6px',
                        backgroundColor: '#e0f2fe',
                        color: '#0369a1',
                        borderRadius: '10px'
                      }}
                    >
                      {cap}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'automation' && (
          <div>
            <h4 style={{ margin: '0 0 15px 0', fontSize: '14px', color: '#374151' }}>
              Automation Tools
            </h4>
            {automationTools.map((tool) => (
              <div
                key={tool.id}
                style={{
                  marginBottom: '12px',
                  padding: '12px',
                  border: '1px solid #e5e7eb',
                  borderRadius: '6px',
                  backgroundColor: '#fafafa'
                }}
              >
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '6px'
                }}>
                  <span style={{ 
                    fontWeight: 'bold', 
                    fontSize: '13px',
                    color: '#111827'
                  }}>
                    {tool.name}
                  </span>
                  <span style={{ 
                    fontSize: '12px',
                    color: getStatusColor(tool.status),
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}>
                    {getStatusIcon(tool.status)} {tool.status}
                  </span>
                </div>
                <p style={{ 
                  margin: '0 0 10px 0', 
                  fontSize: '12px',
                  color: '#6b7280',
                  lineHeight: '1.4'
                }}>
                  {tool.description}
                </p>
                <button
                  onClick={() => handleToolAction(tool)}
                  style={{
                    width: '100%',
                    padding: '6px 12px',
                    backgroundColor: '#059669',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '12px',
                    fontWeight: 'bold'
                  }}
                >
                  {tool.action}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Selected Tool Details */}
      {selectedTool && activeTab === 'mcp' && (
        <div style={{ 
          padding: '10px',
          backgroundColor: '#f0fdf4',
          borderTop: '1px solid #e9ecef'
        }}>
          <h5 style={{ margin: '0 0 8px 0', fontSize: '13px', color: '#059669' }}>
            {selectedTool.name} - Details
          </h5>
          <p style={{ margin: '0', fontSize: '11px', color: '#374151' }}>
            Status: {selectedTool.status} | Capabilities: {selectedTool.capabilities.join(', ')}
          </p>
        </div>
      )}
    </div>
  )
}

export default ToolManager

