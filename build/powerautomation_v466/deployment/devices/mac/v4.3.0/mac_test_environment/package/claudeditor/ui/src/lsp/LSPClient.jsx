import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Zap, 
  AlertTriangle, 
  CheckCircle, 
  Info, 
  Lightbulb,
  Code,
  Search,
  RefreshCw,
  Settings,
  Bug,
  FileText,
  Layers
} from 'lucide-react';

// LSP消息类型
const LSP_MESSAGE_TYPES = {
  INITIALIZE: 'initialize',
  INITIALIZED: 'initialized',
  SHUTDOWN: 'shutdown',
  EXIT: 'exit',
  TEXT_DOCUMENT_DID_OPEN: 'textDocument/didOpen',
  TEXT_DOCUMENT_DID_CHANGE: 'textDocument/didChange',
  TEXT_DOCUMENT_DID_SAVE: 'textDocument/didSave',
  TEXT_DOCUMENT_DID_CLOSE: 'textDocument/didClose',
  TEXT_DOCUMENT_COMPLETION: 'textDocument/completion',
  TEXT_DOCUMENT_HOVER: 'textDocument/hover',
  TEXT_DOCUMENT_SIGNATURE_HELP: 'textDocument/signatureHelp',
  TEXT_DOCUMENT_DEFINITION: 'textDocument/definition',
  TEXT_DOCUMENT_REFERENCES: 'textDocument/references',
  TEXT_DOCUMENT_DOCUMENT_HIGHLIGHT: 'textDocument/documentHighlight',
  TEXT_DOCUMENT_DOCUMENT_SYMBOL: 'textDocument/documentSymbol',
  TEXT_DOCUMENT_CODE_ACTION: 'textDocument/codeAction',
  TEXT_DOCUMENT_CODE_LENS: 'textDocument/codeLens',
  TEXT_DOCUMENT_FORMATTING: 'textDocument/formatting',
  TEXT_DOCUMENT_RANGE_FORMATTING: 'textDocument/rangeFormatting',
  TEXT_DOCUMENT_ON_TYPE_FORMATTING: 'textDocument/onTypeFormatting',
  TEXT_DOCUMENT_RENAME: 'textDocument/rename',
  TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS: 'textDocument/publishDiagnostics',
  WORKSPACE_SYMBOL: 'workspace/symbol',
  WORKSPACE_EXECUTE_COMMAND: 'workspace/executeCommand'
};

// 诊断严重性
const DIAGNOSTIC_SEVERITY = {
  ERROR: 1,
  WARNING: 2,
  INFORMATION: 3,
  HINT: 4
};

// 完成项类型
const COMPLETION_ITEM_KIND = {
  TEXT: 1,
  METHOD: 2,
  FUNCTION: 3,
  CONSTRUCTOR: 4,
  FIELD: 5,
  VARIABLE: 6,
  CLASS: 7,
  INTERFACE: 8,
  MODULE: 9,
  PROPERTY: 10,
  UNIT: 11,
  VALUE: 12,
  ENUM: 13,
  KEYWORD: 14,
  SNIPPET: 15,
  COLOR: 16,
  FILE: 17,
  REFERENCE: 18,
  FOLDER: 19,
  ENUM_MEMBER: 20,
  CONSTANT: 21,
  STRUCT: 22,
  EVENT: 23,
  OPERATOR: 24,
  TYPE_PARAMETER: 25
};

// 支持的语言服务器
const LANGUAGE_SERVERS = {
  typescript: {
    name: 'TypeScript Language Server',
    command: 'typescript-language-server',
    args: ['--stdio'],
    filetypes: ['typescript', 'javascript', 'typescriptreact', 'javascriptreact'],
    capabilities: {
      completionProvider: true,
      hoverProvider: true,
      signatureHelpProvider: true,
      definitionProvider: true,
      referencesProvider: true,
      documentHighlightProvider: true,
      documentSymbolProvider: true,
      workspaceSymbolProvider: true,
      codeActionProvider: true,
      codeLensProvider: true,
      documentFormattingProvider: true,
      documentRangeFormattingProvider: true,
      renameProvider: true,
      foldingRangeProvider: true,
      executeCommandProvider: true,
      declarationProvider: true,
      implementationProvider: true,
      typeDefinitionProvider: true,
      colorProvider: true,
      documentLinkProvider: true
    }
  },
  python: {
    name: 'Pylsp (Python LSP Server)',
    command: 'pylsp',
    args: [],
    filetypes: ['python'],
    capabilities: {
      completionProvider: true,
      hoverProvider: true,
      signatureHelpProvider: true,
      definitionProvider: true,
      referencesProvider: true,
      documentHighlightProvider: true,
      documentSymbolProvider: true,
      workspaceSymbolProvider: true,
      codeActionProvider: true,
      documentFormattingProvider: true,
      documentRangeFormattingProvider: true,
      renameProvider: true,
      foldingRangeProvider: true
    }
  },
  rust: {
    name: 'Rust Analyzer',
    command: 'rust-analyzer',
    args: [],
    filetypes: ['rust'],
    capabilities: {
      completionProvider: true,
      hoverProvider: true,
      signatureHelpProvider: true,
      definitionProvider: true,
      referencesProvider: true,
      documentHighlightProvider: true,
      documentSymbolProvider: true,
      workspaceSymbolProvider: true,
      codeActionProvider: true,
      codeLensProvider: true,
      documentFormattingProvider: true,
      renameProvider: true,
      foldingRangeProvider: true,
      executeCommandProvider: true,
      declarationProvider: true,
      implementationProvider: true,
      typeDefinitionProvider: true
    }
  },
  go: {
    name: 'gopls',
    command: 'gopls',
    args: [],
    filetypes: ['go'],
    capabilities: {
      completionProvider: true,
      hoverProvider: true,
      signatureHelpProvider: true,
      definitionProvider: true,
      referencesProvider: true,
      documentHighlightProvider: true,
      documentSymbolProvider: true,
      workspaceSymbolProvider: true,
      codeActionProvider: true,
      codeLensProvider: true,
      documentFormattingProvider: true,
      documentRangeFormattingProvider: true,
      renameProvider: true,
      foldingRangeProvider: true,
      executeCommandProvider: true,
      declarationProvider: true,
      implementationProvider: true,
      typeDefinitionProvider: true
    }
  }
};

const LSPClient = ({ 
  editorRef,
  language,
  documentUri,
  onDiagnostics,
  onCompletion,
  onHover,
  onSignatureHelp,
  className = ''
}) => {
  // LSP连接状态
  const [isConnected, setIsConnected] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const [serverCapabilities, setServerCapabilities] = useState({});

  // 诊断信息
  const [diagnostics, setDiagnostics] = useState([]);
  const [diagnosticsVisible, setDiagnosticsVisible] = useState(true);

  // 完成建议
  const [completionItems, setCompletionItems] = useState([]);
  const [completionVisible, setCompletionVisible] = useState(false);
  const [completionPosition, setCompletionPosition] = useState(null);

  // 悬停信息
  const [hoverInfo, setHoverInfo] = useState(null);
  const [hoverPosition, setHoverPosition] = useState(null);

  // 符号信息
  const [documentSymbols, setDocumentSymbols] = useState([]);
  const [workspaceSymbols, setWorkspaceSymbols] = useState([]);

  // LSP客户端引用
  const lspClientRef = useRef(null);
  const messageIdRef = useRef(1);
  const pendingRequestsRef = useRef(new Map());

  // 初始化LSP客户端
  useEffect(() => {
    if (language && LANGUAGE_SERVERS[language]) {
      initializeLSP();
    }

    return () => {
      shutdownLSP();
    };
  }, [language]);

  // 文档变化时通知LSP
  useEffect(() => {
    if (isInitialized && editorRef.current) {
      const editor = editorRef.current;
      const model = editor.getModel();

      if (model) {
        // 监听文档变化
        const disposable = model.onDidChangeContent((e) => {
          notifyDocumentChange(e);
        });

        // 监听光标位置变化
        const cursorDisposable = editor.onDidChangeCursorPosition((e) => {
          handleCursorPositionChange(e);
        });

        return () => {
          disposable.dispose();
          cursorDisposable.dispose();
        };
      }
    }
  }, [isInitialized, editorRef]);

  // 初始化LSP服务器
  const initializeLSP = useCallback(async () => {
    const serverConfig = LANGUAGE_SERVERS[language];
    if (!serverConfig) {
      setConnectionError(`No LSP server configured for ${language}`);
      return;
    }

    try {
      // 模拟LSP服务器连接
      // 在实际实现中，这里应该启动真实的LSP服务器进程
      const mockLSPClient = {
        send: (message) => {
          console.log('LSP Send:', message);
          // 模拟服务器响应
          setTimeout(() => {
            handleMockLSPResponse(message);
          }, 100);
        },
        close: () => {
          setIsConnected(false);
          setIsInitialized(false);
        }
      };

      lspClientRef.current = mockLSPClient;
      setIsConnected(true);
      setConnectionError(null);

      // 发送初始化请求
      const initializeParams = {
        processId: null,
        clientInfo: {
          name: 'ClaudEditor',
          version: '2.0.0'
        },
        rootUri: null,
        capabilities: {
          textDocument: {
            synchronization: {
              dynamicRegistration: false,
              willSave: false,
              willSaveWaitUntil: false,
              didSave: false
            },
            completion: {
              dynamicRegistration: false,
              completionItem: {
                snippetSupport: true,
                commitCharactersSupport: true,
                documentationFormat: ['markdown', 'plaintext'],
                deprecatedSupport: true,
                preselectSupport: true
              },
              contextSupport: true
            },
            hover: {
              dynamicRegistration: false,
              contentFormat: ['markdown', 'plaintext']
            },
            signatureHelp: {
              dynamicRegistration: false,
              signatureInformation: {
                documentationFormat: ['markdown', 'plaintext']
              }
            },
            definition: {
              dynamicRegistration: false,
              linkSupport: true
            },
            references: {
              dynamicRegistration: false
            },
            documentHighlight: {
              dynamicRegistration: false
            },
            documentSymbol: {
              dynamicRegistration: false,
              symbolKind: {
                valueSet: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]
              },
              hierarchicalDocumentSymbolSupport: true
            },
            codeAction: {
              dynamicRegistration: false,
              codeActionLiteralSupport: {
                codeActionKind: {
                  valueSet: ['quickfix', 'refactor', 'refactor.extract', 'refactor.inline', 'refactor.rewrite', 'source', 'source.organizeImports']
                }
              }
            },
            formatting: {
              dynamicRegistration: false
            },
            rangeFormatting: {
              dynamicRegistration: false
            },
            rename: {
              dynamicRegistration: false,
              prepareSupport: true
            },
            publishDiagnostics: {
              relatedInformation: true,
              versionSupport: false,
              tagSupport: {
                valueSet: [1, 2]
              }
            }
          },
          workspace: {
            applyEdit: true,
            workspaceEdit: {
              documentChanges: true,
              resourceOperations: ['create', 'rename', 'delete'],
              failureHandling: 'textOnlyTransactional'
            },
            didChangeConfiguration: {
              dynamicRegistration: false
            },
            didChangeWatchedFiles: {
              dynamicRegistration: false
            },
            symbol: {
              dynamicRegistration: false,
              symbolKind: {
                valueSet: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]
              }
            },
            executeCommand: {
              dynamicRegistration: false
            }
          }
        },
        trace: 'off',
        workspaceFolders: null
      };

      sendRequest(LSP_MESSAGE_TYPES.INITIALIZE, initializeParams);

    } catch (error) {
      console.error('Failed to initialize LSP:', error);
      setConnectionError(error.message);
    }
  }, [language]);

  // 模拟LSP服务器响应
  const handleMockLSPResponse = (request) => {
    switch (request.method) {
      case LSP_MESSAGE_TYPES.INITIALIZE:
        // 模拟初始化响应
        const capabilities = LANGUAGE_SERVERS[language]?.capabilities || {};
        setServerCapabilities(capabilities);
        setIsInitialized(true);
        
        // 发送initialized通知
        sendNotification(LSP_MESSAGE_TYPES.INITIALIZED, {});
        
        // 模拟诊断信息
        setTimeout(() => {
          const mockDiagnostics = [
            {
              range: {
                start: { line: 0, character: 0 },
                end: { line: 0, character: 10 }
              },
              severity: DIAGNOSTIC_SEVERITY.WARNING,
              message: 'Unused variable detected',
              source: 'eslint'
            },
            {
              range: {
                start: { line: 5, character: 15 },
                end: { line: 5, character: 25 }
              },
              severity: DIAGNOSTIC_SEVERITY.ERROR,
              message: 'Type error: Cannot assign string to number',
              source: 'typescript'
            }
          ];
          
          setDiagnostics(mockDiagnostics);
          onDiagnostics?.(mockDiagnostics);
        }, 1000);
        break;

      case LSP_MESSAGE_TYPES.TEXT_DOCUMENT_COMPLETION:
        // 模拟代码完成
        const mockCompletions = [
          {
            label: 'console.log',
            kind: COMPLETION_ITEM_KIND.FUNCTION,
            detail: 'console.log(message?: any, ...optionalParams: any[]): void',
            documentation: 'Prints to stdout with newline',
            insertText: 'console.log($1)',
            insertTextFormat: 2 // Snippet
          },
          {
            label: 'function',
            kind: COMPLETION_ITEM_KIND.KEYWORD,
            detail: 'function declaration',
            insertText: 'function ${1:name}(${2:params}) {\n\t$0\n}',
            insertTextFormat: 2
          },
          {
            label: 'const',
            kind: COMPLETION_ITEM_KIND.KEYWORD,
            detail: 'const declaration',
            insertText: 'const ${1:name} = $0',
            insertTextFormat: 2
          }
        ];
        
        setCompletionItems(mockCompletions);
        setCompletionVisible(true);
        onCompletion?.(mockCompletions);
        break;

      case LSP_MESSAGE_TYPES.TEXT_DOCUMENT_HOVER:
        // 模拟悬停信息
        const mockHover = {
          contents: {
            kind: 'markdown',
            value: '```typescript\nfunction console.log(message?: any, ...optionalParams: any[]): void\n```\n\nPrints to stdout with newline. Multiple arguments can be passed, with the first used as the primary message and all additional used as substitution values similar to printf(3).'
          },
          range: {
            start: { line: request.params.position.line, character: 0 },
            end: { line: request.params.position.line, character: 10 }
          }
        };
        
        setHoverInfo(mockHover);
        setHoverPosition(request.params.position);
        onHover?.(mockHover);
        break;

      case LSP_MESSAGE_TYPES.TEXT_DOCUMENT_DOCUMENT_SYMBOL:
        // 模拟文档符号
        const mockSymbols = [
          {
            name: 'MyClass',
            kind: 7, // Class
            range: {
              start: { line: 0, character: 0 },
              end: { line: 20, character: 0 }
            },
            selectionRange: {
              start: { line: 0, character: 6 },
              end: { line: 0, character: 13 }
            },
            children: [
              {
                name: 'constructor',
                kind: 4, // Constructor
                range: {
                  start: { line: 1, character: 2 },
                  end: { line: 5, character: 3 }
                },
                selectionRange: {
                  start: { line: 1, character: 2 },
                  end: { line: 1, character: 13 }
                }
              },
              {
                name: 'myMethod',
                kind: 2, // Method
                range: {
                  start: { line: 7, character: 2 },
                  end: { line: 15, character: 3 }
                },
                selectionRange: {
                  start: { line: 7, character: 2 },
                  end: { line: 7, character: 10 }
                }
              }
            ]
          }
        ];
        
        setDocumentSymbols(mockSymbols);
        break;
    }
  };

  // 关闭LSP服务器
  const shutdownLSP = useCallback(() => {
    if (lspClientRef.current && isInitialized) {
      sendRequest(LSP_MESSAGE_TYPES.SHUTDOWN, {});
      sendNotification(LSP_MESSAGE_TYPES.EXIT, {});
      lspClientRef.current.close();
      lspClientRef.current = null;
    }
    
    setIsConnected(false);
    setIsInitialized(false);
    setDiagnostics([]);
    setCompletionItems([]);
    setHoverInfo(null);
    setDocumentSymbols([]);
  }, [isInitialized]);

  // 发送LSP请求
  const sendRequest = useCallback((method, params) => {
    if (!lspClientRef.current) return null;

    const id = messageIdRef.current++;
    const message = {
      jsonrpc: '2.0',
      id,
      method,
      params
    };

    lspClientRef.current.send(message);
    
    return new Promise((resolve, reject) => {
      pendingRequestsRef.current.set(id, { resolve, reject });
      
      // 设置超时
      setTimeout(() => {
        if (pendingRequestsRef.current.has(id)) {
          pendingRequestsRef.current.delete(id);
          reject(new Error('Request timeout'));
        }
      }, 10000);
    });
  }, []);

  // 发送LSP通知
  const sendNotification = useCallback((method, params) => {
    if (!lspClientRef.current) return;

    const message = {
      jsonrpc: '2.0',
      method,
      params
    };

    lspClientRef.current.send(message);
  }, []);

  // 通知文档变化
  const notifyDocumentChange = useCallback((changeEvent) => {
    if (!isInitialized || !documentUri) return;

    const changes = changeEvent.changes.map(change => ({
      range: {
        start: {
          line: change.range.startLineNumber - 1,
          character: change.range.startColumn - 1
        },
        end: {
          line: change.range.endLineNumber - 1,
          character: change.range.endColumn - 1
        }
      },
      rangeLength: change.rangeLength,
      text: change.text
    }));

    sendNotification(LSP_MESSAGE_TYPES.TEXT_DOCUMENT_DID_CHANGE, {
      textDocument: {
        uri: documentUri,
        version: changeEvent.versionId
      },
      contentChanges: changes
    });
  }, [isInitialized, documentUri]);

  // 处理光标位置变化
  const handleCursorPositionChange = useCallback((e) => {
    // 隐藏完成建议
    setCompletionVisible(false);
    setHoverInfo(null);
    
    // 可以在这里触发悬停信息请求
    const position = {
      line: e.position.lineNumber - 1,
      character: e.position.column - 1
    };
    
    // 延迟触发悬停
    setTimeout(() => {
      if (isInitialized && serverCapabilities.hoverProvider) {
        sendRequest(LSP_MESSAGE_TYPES.TEXT_DOCUMENT_HOVER, {
          textDocument: { uri: documentUri },
          position
        });
      }
    }, 500);
  }, [isInitialized, serverCapabilities, documentUri]);

  // 请求代码完成
  const requestCompletion = useCallback((position) => {
    if (!isInitialized || !serverCapabilities.completionProvider) return;

    sendRequest(LSP_MESSAGE_TYPES.TEXT_DOCUMENT_COMPLETION, {
      textDocument: { uri: documentUri },
      position: {
        line: position.lineNumber - 1,
        character: position.column - 1
      },
      context: {
        triggerKind: 1 // Invoked
      }
    });
  }, [isInitialized, serverCapabilities, documentUri]);

  // 请求文档符号
  const requestDocumentSymbols = useCallback(() => {
    if (!isInitialized || !serverCapabilities.documentSymbolProvider) return;

    sendRequest(LSP_MESSAGE_TYPES.TEXT_DOCUMENT_DOCUMENT_SYMBOL, {
      textDocument: { uri: documentUri }
    });
  }, [isInitialized, serverCapabilities, documentUri]);

  // 获取诊断图标
  const getDiagnosticIcon = (severity) => {
    switch (severity) {
      case DIAGNOSTIC_SEVERITY.ERROR:
        return <AlertTriangle className="text-red-500" size={16} />;
      case DIAGNOSTIC_SEVERITY.WARNING:
        return <AlertTriangle className="text-yellow-500" size={16} />;
      case DIAGNOSTIC_SEVERITY.INFORMATION:
        return <Info className="text-blue-500" size={16} />;
      case DIAGNOSTIC_SEVERITY.HINT:
        return <Lightbulb className="text-gray-500" size={16} />;
      default:
        return <Info className="text-gray-500" size={16} />;
    }
  };

  // 获取完成项图标
  const getCompletionIcon = (kind) => {
    switch (kind) {
      case COMPLETION_ITEM_KIND.FUNCTION:
      case COMPLETION_ITEM_KIND.METHOD:
        return '🔧';
      case COMPLETION_ITEM_KIND.CLASS:
        return '📦';
      case COMPLETION_ITEM_KIND.VARIABLE:
        return '📊';
      case COMPLETION_ITEM_KIND.KEYWORD:
        return '🔑';
      case COMPLETION_ITEM_KIND.SNIPPET:
        return '📝';
      default:
        return '📄';
    }
  };

  return (
    <div className={`lsp-client ${className}`}>
      {/* LSP状态栏 */}
      <div className="lsp-status bg-gray-800 border-b border-gray-700 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {/* 连接状态 */}
          <div className="flex items-center space-x-2">
            {isConnected ? (
              <CheckCircle className="text-green-500" size={16} />
            ) : (
              <AlertTriangle className="text-red-500" size={16} />
            )}
            <span className="text-sm text-gray-300">
              {isInitialized ? `LSP: ${LANGUAGE_SERVERS[language]?.name || language}` : 
               isConnected ? 'Initializing...' : 
               connectionError ? 'Connection Error' : 'Disconnected'}
            </span>
          </div>

          {/* 诊断统计 */}
          {diagnostics.length > 0 && (
            <div className="flex items-center space-x-2 text-sm">
              <span className="text-red-500">
                {diagnostics.filter(d => d.severity === DIAGNOSTIC_SEVERITY.ERROR).length} errors
              </span>
              <span className="text-yellow-500">
                {diagnostics.filter(d => d.severity === DIAGNOSTIC_SEVERITY.WARNING).length} warnings
              </span>
            </div>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {/* 刷新按钮 */}
          <button
            onClick={() => requestDocumentSymbols()}
            className="p-1 text-gray-400 hover:text-white transition-colors"
            title="Refresh Symbols"
            disabled={!isInitialized}
          >
            <RefreshCw size={14} />
          </button>

          {/* 设置按钮 */}
          <button
            className="p-1 text-gray-400 hover:text-white transition-colors"
            title="LSP Settings"
          >
            <Settings size={14} />
          </button>
        </div>
      </div>

      {/* 诊断面板 */}
      {diagnosticsVisible && diagnostics.length > 0 && (
        <div className="diagnostics-panel bg-gray-900 border-b border-gray-700 max-h-48 overflow-y-auto">
          <div className="p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-white">Problems</h3>
              <button
                onClick={() => setDiagnosticsVisible(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-2">
              {diagnostics.map((diagnostic, index) => (
                <div key={index} className="flex items-start space-x-3 p-2 bg-gray-800 rounded">
                  {getDiagnosticIcon(diagnostic.severity)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white">{diagnostic.message}</p>
                    <p className="text-xs text-gray-400">
                      Line {diagnostic.range.start.line + 1}, Column {diagnostic.range.start.character + 1}
                      {diagnostic.source && ` • ${diagnostic.source}`}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 完成建议弹窗 */}
      {completionVisible && completionItems.length > 0 && (
        <div className="completion-popup fixed bg-gray-800 border border-gray-600 rounded-lg shadow-lg z-50 max-w-md">
          <div className="max-h-64 overflow-y-auto">
            {completionItems.map((item, index) => (
              <div
                key={index}
                className="flex items-center space-x-3 p-3 hover:bg-gray-700 cursor-pointer border-b border-gray-700 last:border-b-0"
              >
                <span className="text-lg">{getCompletionIcon(item.kind)}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-white">{item.label}</span>
                    {item.detail && (
                      <span className="text-xs text-gray-400 truncate">{item.detail}</span>
                    )}
                  </div>
                  {item.documentation && (
                    <p className="text-xs text-gray-300 mt-1 line-clamp-2">
                      {typeof item.documentation === 'string' ? 
                        item.documentation : 
                        item.documentation.value}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 悬停信息弹窗 */}
      {hoverInfo && (
        <div className="hover-popup fixed bg-gray-800 border border-gray-600 rounded-lg shadow-lg z-50 max-w-lg p-4">
          <div className="text-sm text-white">
            {typeof hoverInfo.contents === 'string' ? (
              <p>{hoverInfo.contents}</p>
            ) : hoverInfo.contents.kind === 'markdown' ? (
              <div dangerouslySetInnerHTML={{ __html: hoverInfo.contents.value }} />
            ) : (
              <p>{hoverInfo.contents.value}</p>
            )}
          </div>
        </div>
      )}

      {/* 连接错误提示 */}
      {connectionError && (
        <div className="error-banner bg-red-900 border-b border-red-700 px-4 py-2">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="text-red-400" size={16} />
            <span className="text-sm text-red-200">{connectionError}</span>
            <button
              onClick={initializeLSP}
              className="ml-auto text-xs text-red-200 hover:text-white underline"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* 样式 */}
      <style jsx>{`
        .lsp-client {
          background: #1f2937;
        }
        
        .diagnostics-panel::-webkit-scrollbar,
        .completion-popup::-webkit-scrollbar {
          width: 6px;
        }
        
        .diagnostics-panel::-webkit-scrollbar-track,
        .completion-popup::-webkit-scrollbar-track {
          background: #374151;
        }
        
        .diagnostics-panel::-webkit-scrollbar-thumb,
        .completion-popup::-webkit-scrollbar-thumb {
          background: #6b7280;
          border-radius: 3px;
        }
        
        .line-clamp-2 {
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
        
        .completion-popup {
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
        }
        
        .hover-popup {
          top: 30%;
          left: 50%;
          transform: translate(-50%, -50%);
        }
      `}</style>
    </div>
  );
};

export default LSPClient;

