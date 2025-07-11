# ClaudEditor 4.3 完整UI设计规范

## 🎯 设计目标

基于VS Code等现代编辑器的UI模式，为ClaudEditor 4.3设计完整的编辑器界面，包含：
- 侧边栏导航和文件管理
- Git集成和版本控制
- 项目管理和工作区
- AI助手集成
- 终端和调试面板
- 扩展和设置管理

## 🏗️ 整体UI架构

```
ClaudEditor 4.3 UI Layout
├── Title Bar (标题栏)
│   ├── Menu Bar (菜单栏)
│   ├── Window Controls (窗口控制)
│   └── Activity Indicators (活动指示器)
├── Activity Bar (活动栏) - 左侧
│   ├── Explorer (文件浏览器)
│   ├── Search (搜索)
│   ├── Source Control (Git)
│   ├── Run & Debug (运行调试)
│   ├── Extensions (扩展)
│   ├── AI Assistant (AI助手) ⭐ 新增
│   └── Settings (设置)
├── Side Bar (侧边栏) - 可切换内容
│   ├── File Explorer Panel
│   ├── Git Panel
│   ├── AI Assistant Panel ⭐ 新增
│   └── Other Panels
├── Editor Group (编辑器组) - 中央区域
│   ├── Tab Bar (标签栏)
│   ├── Editor Panes (编辑器面板)
│   ├── Monaco Editor (代码编辑器)
│   └── AI Code Completion ⭐ 集成
├── Panel (面板) - 底部
│   ├── Terminal (终端)
│   ├── Problems (问题)
│   ├── Output (输出)
│   ├── Debug Console (调试控制台)
│   └── AI Chat (AI对话) ⭐ 新增
└── Status Bar (状态栏) - 底部
    ├── Git Branch Info
    ├── Language Mode
    ├── Encoding
    ├── Line/Column
    ├── AI Status ⭐ 新增
    └── Notifications
```

## 🎨 设计系统

### 颜色主题
```css
/* ClaudEditor Dark Theme */
:root {
  /* 主色调 */
  --primary-bg: #1e1e1e;
  --secondary-bg: #252526;
  --tertiary-bg: #2d2d30;
  
  /* 文本颜色 */
  --text-primary: #cccccc;
  --text-secondary: #969696;
  --text-muted: #6a6a6a;
  
  /* 强调色 */
  --accent-blue: #007acc;
  --accent-green: #4ec9b0;
  --accent-orange: #ce9178;
  --accent-red: #f44747;
  
  /* AI主题色 ⭐ */
  --ai-primary: #8b5cf6;
  --ai-secondary: #a78bfa;
  --ai-accent: #c4b5fd;
  
  /* 边框和分割线 */
  --border-color: #3e3e42;
  --divider-color: #454545;
  
  /* 交互状态 */
  --hover-bg: #2a2d2e;
  --active-bg: #37373d;
  --focus-border: #007fd4;
}
```

### 字体系统
```css
/* 字体定义 */
.font-system {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.font-mono {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', monospace;
}

/* 字体大小 */
.text-xs { font-size: 11px; }
.text-sm { font-size: 12px; }
.text-base { font-size: 13px; }
.text-lg { font-size: 14px; }
.text-xl { font-size: 16px; }
```

## 📱 组件设计规范

### 1. Activity Bar (活动栏)
```typescript
interface ActivityBarItem {
  id: string;
  icon: string;
  title: string;
  badge?: number;
  active?: boolean;
  onClick: () => void;
}

const activityBarItems: ActivityBarItem[] = [
  { id: 'explorer', icon: 'files', title: '文件浏览器' },
  { id: 'search', icon: 'search', title: '搜索' },
  { id: 'scm', icon: 'source-control', title: 'Git' },
  { id: 'debug', icon: 'debug', title: '运行调试' },
  { id: 'extensions', icon: 'extensions', title: '扩展' },
  { id: 'ai-assistant', icon: 'robot', title: 'AI助手' }, // ⭐ 新增
  { id: 'settings', icon: 'settings', title: '设置' }
];
```

### 2. File Explorer (文件浏览器)
```typescript
interface FileTreeNode {
  id: string;
  name: string;
  type: 'file' | 'folder';
  path: string;
  children?: FileTreeNode[];
  expanded?: boolean;
  modified?: boolean;
  gitStatus?: 'modified' | 'added' | 'deleted' | 'untracked';
}

interface FileExplorerProps {
  workspaceRoot: string;
  files: FileTreeNode[];
  onFileSelect: (file: FileTreeNode) => void;
  onFileCreate: (parentPath: string, type: 'file' | 'folder') => void;
  onFileDelete: (file: FileTreeNode) => void;
  onFileRename: (file: FileTreeNode, newName: string) => void;
}
```

### 3. Git Integration (Git集成)
```typescript
interface GitStatus {
  branch: string;
  ahead: number;
  behind: number;
  modified: FileChange[];
  staged: FileChange[];
  untracked: FileChange[];
}

interface FileChange {
  path: string;
  status: 'M' | 'A' | 'D' | 'R' | 'U';
  staged: boolean;
}

interface GitPanelProps {
  status: GitStatus;
  onStage: (files: string[]) => void;
  onUnstage: (files: string[]) => void;
  onCommit: (message: string) => void;
  onPush: () => void;
  onPull: () => void;
  onBranchSwitch: (branch: string) => void;
}
```

### 4. AI Assistant Panel (AI助手面板) ⭐
```typescript
interface AIAssistantProps {
  conversations: AIConversation[];
  currentConversation?: string;
  onSendMessage: (message: string) => void;
  onNewConversation: () => void;
  onSelectConversation: (id: string) => void;
  aiStatus: 'connected' | 'disconnected' | 'thinking';
  availableModels: AIModel[];
  selectedModel: string;
  onModelChange: (model: string) => void;
}

interface AIConversation {
  id: string;
  title: string;
  messages: AIMessage[];
  createdAt: Date;
  updatedAt: Date;
}

interface AIMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  codeBlocks?: CodeBlock[];
  attachments?: Attachment[];
}
```

### 5. Monaco Editor Integration (Monaco编辑器集成)
```typescript
interface MonacoEditorProps {
  value: string;
  language: string;
  theme: 'vs-dark' | 'vs-light';
  onChange: (value: string) => void;
  onSave: () => void;
  
  // AI功能集成 ⭐
  aiCompletionEnabled: boolean;
  aiHoverEnabled: boolean;
  aiDiagnosticsEnabled: boolean;
  onAICompletion: (position: Position) => Promise<CompletionItem[]>;
  onAIHover: (position: Position) => Promise<HoverInfo>;
  onAIAction: (action: string, selection: Selection) => void;
}

interface CompletionItem {
  label: string;
  kind: CompletionItemKind;
  detail?: string;
  documentation?: string;
  insertText: string;
  range: Range;
  aiGenerated?: boolean; // ⭐ AI生成标识
}
```

## 🔧 技术实现规范

### 1. React组件架构
```typescript
// 主应用组件
const ClaudEditor: React.FC = () => {
  const [activeView, setActiveView] = useState('explorer');
  const [openFiles, setOpenFiles] = useState<OpenFile[]>([]);
  const [activeFile, setActiveFile] = useState<string | null>(null);
  const [aiAssistant, setAIAssistant] = useState<AIAssistantState>();
  
  return (
    <div className="claudeditor-container">
      <TitleBar />
      <div className="claudeditor-body">
        <ActivityBar 
          activeView={activeView}
          onViewChange={setActiveView}
        />
        <SideBar 
          activeView={activeView}
          onFileSelect={handleFileSelect}
        />
        <EditorGroup 
          openFiles={openFiles}
          activeFile={activeFile}
          onFileChange={handleFileChange}
        />
        <Panel />
      </div>
      <StatusBar />
    </div>
  );
};
```

### 2. 状态管理
```typescript
// 使用Zustand进行状态管理
interface EditorStore {
  // 文件系统状态
  workspaceRoot: string;
  fileTree: FileTreeNode[];
  openFiles: OpenFile[];
  activeFile: string | null;
  
  // Git状态
  gitStatus: GitStatus;
  
  // AI助手状态
  aiAssistant: {
    connected: boolean;
    currentModel: string;
    conversations: AIConversation[];
    activeConversation: string | null;
  };
  
  // UI状态
  activeView: string;
  sidebarVisible: boolean;
  panelVisible: boolean;
  theme: 'dark' | 'light';
  
  // Actions
  setActiveView: (view: string) => void;
  openFile: (file: FileTreeNode) => void;
  closeFile: (fileId: string) => void;
  updateFileContent: (fileId: string, content: string) => void;
  sendAIMessage: (message: string) => void;
}
```

### 3. AI集成接口
```typescript
// AI服务接口
interface AIService {
  // 代码补全
  getCompletions(
    document: TextDocument,
    position: Position,
    context: CompletionContext
  ): Promise<CompletionItem[]>;
  
  // 代码解释
  explainCode(
    code: string,
    language: string
  ): Promise<string>;
  
  // 代码重构
  refactorCode(
    code: string,
    refactorType: RefactorType,
    options?: RefactorOptions
  ): Promise<RefactorResult>;
  
  // 聊天对话
  sendChatMessage(
    message: string,
    context?: ChatContext
  ): Promise<ChatResponse>;
  
  // 代码生成
  generateCode(
    prompt: string,
    language: string,
    context?: CodeContext
  ): Promise<GeneratedCode>;
}
```

## 🎯 关键功能特性

### 1. 智能文件浏览器
- 📁 树形文件结构显示
- 🔍 文件快速搜索和过滤
- 📝 文件创建、删除、重命名
- 🏷️ Git状态显示（修改、新增、删除）
- 📋 右键上下文菜单
- 🎨 文件图标和语法高亮

### 2. Git集成
- 🌿 分支管理和切换
- 📊 文件变更状态显示
- ✅ 暂存和提交操作
- 🔄 推送和拉取操作
- 📈 提交历史查看
- 🔀 合并冲突解决

### 3. AI助手集成 ⭐
- 💬 智能对话界面
- 🤖 多模型支持（Claude, Gemini等）
- 💡 代码补全和建议
- 🔍 代码解释和分析
- 🛠️ 自动重构和优化
- 📚 文档生成

### 4. 高级编辑功能
- 📑 多标签页编辑
- 🔍 全局搜索和替换
- 🎯 智能跳转和导航
- 🐛 调试集成
- 🔧 扩展系统
- ⚙️ 自定义设置

## 📱 响应式设计

### 桌面端 (>1200px)
- 完整的三栏布局
- 侧边栏默认展开
- 面板区域可调整高度

### 平板端 (768px - 1200px)
- 侧边栏可折叠
- 面板区域自适应
- 触摸友好的交互

### 移动端 (<768px)
- 单栏布局
- 抽屉式侧边栏
- 简化的工具栏

## 🎨 主题系统

### 内置主题
1. **ClaudEditor Dark** (默认)
2. **ClaudEditor Light**
3. **High Contrast**
4. **AI Purple** ⭐ (AI主题)

### 自定义主题支持
- CSS变量系统
- 主题配置文件
- 实时主题切换
- 主题导入导出

## 🔧 扩展系统

### 扩展API
```typescript
interface ClaudEditorExtension {
  id: string;
  name: string;
  version: string;
  description: string;
  
  // 生命周期
  activate(context: ExtensionContext): void;
  deactivate(): void;
  
  // 贡献点
  contributes?: {
    commands?: Command[];
    menus?: Menu[];
    keybindings?: Keybinding[];
    languages?: Language[];
    themes?: Theme[];
    aiProviders?: AIProvider[]; // ⭐ AI扩展
  };
}
```

### 内置扩展
- Git集成扩展
- AI助手扩展 ⭐
- 语言支持扩展
- 主题扩展
- 调试扩展

## 📊 性能优化

### 虚拟化
- 文件树虚拟滚动
- 大文件分块加载
- 智能缓存策略

### 懒加载
- 组件按需加载
- 扩展延迟激活
- AI模型按需初始化

### 内存管理
- 文件内容缓存策略
- 未使用标签页回收
- AI对话历史清理

这个设计规范为ClaudEditor 4.3提供了完整的现代编辑器UI架构，集成了AI功能，确保用户体验与VS Code等主流编辑器相当。

