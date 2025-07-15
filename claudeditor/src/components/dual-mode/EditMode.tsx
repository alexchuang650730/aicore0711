import React, { useEffect, useRef, useState, useCallback } from 'react';
import MonacoEditor from '../../editor/MonacoEditor';
import { 
  FileText, 
  FolderOpen, 
  Terminal, 
  Search, 
  GitBranch, 
  Bug, 
  Settings,
  Save,
  Undo,
  Redo,
  Copy,
  Cut,
  Paste
} from 'lucide-react';

interface EditState {
  openFiles: string[];
  activeFile: string;
  cursorPosition: { line: number; column: number };
  selections: Array<{ start: { line: number; column: number }; end: { line: number; column: number } }>;
  fileContents: Record<string, string>;
  theme: 'light' | 'dark';
  fontSize: number;
  wordWrap: boolean;
  minimap: boolean;
}

interface EditModeProps {
  isActive: boolean;
  state: EditState;
  onStateChange: (state: EditState) => void;
}

export const EditMode: React.FC<EditModeProps> = ({
  isActive,
  state,
  onStateChange
}) => {
  const [sidebarWidth, setSidebarWidth] = useState(250);
  const [terminalHeight, setTerminalHeight] = useState(200);
  const [showTerminal, setShowTerminal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentFile, setCurrentFile] = useState(null);
  const [fileContent, setFileContent] = useState('');

  // 文件树数据（模拟）
  const [fileTree] = useState([
    {
      name: 'src',
      type: 'folder',
      children: [
        { name: 'main.tsx', type: 'file', path: '/src/main.tsx', language: 'typescript' },
        { name: 'App.tsx', type: 'file', path: '/src/App.tsx', language: 'typescript' },
        { name: 'components', type: 'folder', children: [
          { name: 'Header.tsx', type: 'file', path: '/src/components/Header.tsx', language: 'typescript' },
          { name: 'Sidebar.tsx', type: 'file', path: '/src/components/Sidebar.tsx', language: 'typescript' }
        ]}
      ]
    },
    { name: 'package.json', type: 'file', path: '/package.json', language: 'json' },
    { name: 'README.md', type: 'file', path: '/README.md', language: 'markdown' }
  ]);

  // 更新文件内容
  const updateFileContent = useCallback((filePath: string, content: string) => {
    const newState = {
      ...state,
      fileContents: {
        ...state.fileContents,
        [filePath]: content
      }
    };
    onStateChange(newState);
  }, [state, onStateChange]);

  // 保存文件
  const handleSaveFile = useCallback(() => {
    if (currentFile && fileContent) {
      updateFileContent(currentFile.path, fileContent);
      console.log('保存文件:', currentFile.path, fileContent);
    }
  }, [currentFile, fileContent, updateFileContent]);

  // 打开文件
  const handleOpenFile = useCallback((filePath: string, fileName: string, language: string) => {
    const newOpenFiles = state.openFiles.includes(filePath) 
      ? state.openFiles 
      : [...state.openFiles, filePath];
    
    const newState = {
      ...state,
      openFiles: newOpenFiles,
      activeFile: filePath
    };
    onStateChange(newState);

    // 设置当前文件信息给 MonacoEditor
    setCurrentFile({
      name: fileName,
      path: filePath,
      language: language
    });

    // 设置文件内容
    const content = state.fileContents[filePath] || getDefaultContent(language);
    setFileContent(content);
  }, [state, onStateChange]);

  // 关闭文件
  const handleCloseFile = useCallback((filePath: string) => {
    const newOpenFiles = state.openFiles.filter(f => f !== filePath);
    const newActiveFile = newOpenFiles.length > 0 
      ? (state.activeFile === filePath ? newOpenFiles[0] : state.activeFile)
      : '';
    
    const newState = {
      ...state,
      openFiles: newOpenFiles,
      activeFile: newActiveFile
    };
    onStateChange(newState);

    // 如果关闭的是当前文件，切换到其他文件或清空
    if (currentFile?.path === filePath) {
      if (newOpenFiles.length > 0) {
        // 切换到第一个打开的文件
        const firstFile = findFileByPath(newOpenFiles[0]);
        if (firstFile) {
          setCurrentFile({
            name: firstFile.name,
            path: firstFile.path,
            language: firstFile.language
          });
          setFileContent(state.fileContents[firstFile.path] || getDefaultContent(firstFile.language));
        }
      } else {
        setCurrentFile(null);
        setFileContent('');
      }
    }
  }, [state, onStateChange, currentFile]);

  // 根据路径查找文件
  const findFileByPath = (path: string) => {
    const findInTree = (items: any[]): any => {
      for (const item of items) {
        if (item.path === path) return item;
        if (item.children) {
          const found = findInTree(item.children);
          if (found) return found;
        }
      }
      return null;
    };
    return findInTree(fileTree);
  };

  // 获取默认文件内容
  const getDefaultContent = (language: string): string => {
    switch (language) {
      case 'typescript':
        return `// TypeScript 文件
export interface Example {
  name: string;
  value: number;
}

const example: Example = {
  name: "ClaudeEditor",
  value: 42
};

console.log(example);
`;
      case 'javascript':
        return `// JavaScript 文件
function hello() {
  console.log("Hello from ClaudeEditor!");
}

hello();
`;
      case 'json':
        return `{
  "name": "claudeditor-project",
  "version": "1.0.0",
  "description": "AI-powered code editor"
}`;
      case 'markdown':
        return `# ClaudeEditor 项目

这是一个 AI 驱动的代码编辑器项目。

## 特性

- 智能代码补全
- 实时协作
- 双模式编辑/演示
`;
      default:
        return '// 开始编写代码...\n';
    }
  };

  // 处理文件内容变化
  const handleFileContentChange = useCallback((newContent: string) => {
    setFileContent(newContent);
    if (currentFile) {
      updateFileContent(currentFile.path, newContent);
    }
  }, [currentFile, updateFileContent]);

  // 渲染文件树
  const renderFileTree = (items: any[], level = 0) => {
    return items.map((item, index) => (
      <div key={index} style={{ paddingLeft: `${level * 16}px` }}>
        <div 
          className={`flex items-center gap-2 px-2 py-1 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer rounded ${
            item.path === state.activeFile ? 'bg-blue-100 dark:bg-blue-900' : ''
          }`}
          onClick={() => item.type === 'file' && handleOpenFile(item.path, item.name, item.language)}
        >
          {item.type === 'folder' ? (
            <FolderOpen className="w-4 h-4 text-yellow-600" />
          ) : (
            <FileText className="w-4 h-4 text-blue-600" />
          )}
          <span className="text-sm text-gray-700 dark:text-gray-300">{item.name}</span>
        </div>
        {item.children && renderFileTree(item.children, level + 1)}
      </div>
    ));
  };

  return (
    <div className="edit-mode flex h-full bg-white dark:bg-gray-900">
      {/* 侧边栏 */}
      <div 
        className="flex-shrink-0 bg-gray-50 dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700"
        style={{ width: `${sidebarWidth}px` }}
      >
        {/* 侧边栏标签 */}
        <div className="flex border-b border-gray-200 dark:border-gray-700">
          <button className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-blue-600 border-b-2 border-blue-600">
            <FolderOpen className="w-4 h-4" />
            文件
          </button>
          <button className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200">
            <Search className="w-4 h-4" />
            搜索
          </button>
          <button className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200">
            <GitBranch className="w-4 h-4" />
            Git
          </button>
        </div>

        {/* 文件树 */}
        <div className="p-2 overflow-y-auto" style={{ height: 'calc(100% - 40px)' }}>
          {renderFileTree(fileTree)}
        </div>
      </div>

      {/* 主编辑区域 */}
      <div className="flex-1 flex flex-col">
        {/* 文件标签栏 */}
        <div className="flex items-center bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
          {state.openFiles.map((filePath) => {
            const file = findFileByPath(filePath);
            return (
              <div
                key={filePath}
                className={`flex items-center gap-2 px-3 py-2 border-r border-gray-200 dark:border-gray-700 cursor-pointer ${
                  filePath === state.activeFile 
                    ? 'bg-white dark:bg-gray-900 text-blue-600' 
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
                onClick={() => file && handleOpenFile(filePath, file.name, file.language)}
              >
                <FileText className="w-4 h-4" />
                <span className="text-sm">{file?.name || filePath.split('/').pop()}</span>
                <button
                  className="ml-1 p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCloseFile(filePath);
                  }}
                >
                  ×
                </button>
              </div>
            );
          })}
        </div>

        {/* 编辑器工具栏 */}
        <div className="flex items-center justify-between px-4 py-2 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <button 
              className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded" 
              title="保存 (Ctrl+S)"
              onClick={handleSaveFile}
            >
              <Save className="w-4 h-4" />
            </button>
            <button className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded" title="撤销 (Ctrl+Z)">
              <Undo className="w-4 h-4" />
            </button>
            <button className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded" title="重做 (Ctrl+Y)">
              <Redo className="w-4 h-4" />
            </button>
            <div className="w-px h-4 bg-gray-300 dark:bg-gray-600 mx-2" />
            <button className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded" title="复制 (Ctrl+C)">
              <Copy className="w-4 h-4" />
            </button>
            <button className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded" title="剪切 (Ctrl+X)">
              <Cut className="w-4 h-4" />
            </button>
            <button className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded" title="粘贴 (Ctrl+V)">
              <Paste className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button 
              className="flex items-center gap-1 px-2 py-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded text-sm"
              onClick={() => setShowTerminal(!showTerminal)}
            >
              <Terminal className="w-4 h-4" />
              终端
            </button>
            <button className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded">
              <Bug className="w-4 h-4" />
            </button>
            <button className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded">
              <Settings className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* 使用现有的 MonacoEditor 组件 */}
        <div className="flex-1 relative">
          {currentFile ? (
            <MonacoEditor 
              currentFile={currentFile}
              fileContent={fileContent}
              onFileContentChange={handleFileContentChange}
            />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
              <div className="text-center">
                <FileText className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p className="text-lg mb-2">欢迎使用 ClaudeEditor</p>
                <p className="text-sm">选择一个文件开始编辑</p>
              </div>
            </div>
          )}
        </div>

        {/* 终端面板 */}
        {showTerminal && (
          <div 
            className="border-t border-gray-200 dark:border-gray-700 bg-black text-green-400 font-mono text-sm"
            style={{ height: `${terminalHeight}px` }}
          >
            <div className="flex items-center justify-between px-4 py-2 bg-gray-800 text-white">
              <span>终端</span>
              <button 
                onClick={() => setShowTerminal(false)}
                className="hover:bg-gray-700 px-2 py-1 rounded"
              >
                ×
              </button>
            </div>
            <div className="p-4 h-full overflow-y-auto">
              <div>$ npm run dev</div>
              <div className="text-blue-400">启动开发服务器...</div>
              <div className="text-green-400">✓ 服务器运行在 http://localhost:5175</div>
              <div className="flex items-center">
                <span>$ </span>
                <input 
                  type="text" 
                  className="bg-transparent border-none outline-none flex-1 ml-1"
                  placeholder="输入命令..."
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

