import React, { useState, useCallback, useEffect } from 'react';
import { 
  Edit3, Save, Download, Copy, FileText, Code, 
  Maximize2, Minimize2, Search, Replace, Settings,
  CheckCircle, AlertCircle, Lightbulb, Zap
} from 'lucide-react';

const LocalProcessor = ({ input, processingOptions, onSaveResult, onBackToClaudeCode }) => {
  const [content, setContent] = useState(input?.content || '');
  const [isEditing, setIsEditing] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [replaceTerm, setReplaceTerm] = useState('');
  const [processingStatus, setProcessingStatus] = useState('ready');
  const [localAnalysis, setLocalAnalysis] = useState(null);

  // 自動分析輸入內容
  useEffect(() => {
    if (input?.content) {
      analyzeContent(input.content);
    }
  }, [input]);

  // 本地內容分析
  const analyzeContent = useCallback((text) => {
    const analysis = {
      wordCount: text.split(/\s+/).length,
      charCount: text.length,
      lineCount: text.split('\n').length,
      language: detectLanguage(text),
      contentType: detectContentType(text),
      complexity: calculateComplexity(text),
      suggestions: generateSuggestions(text),
      extractedInfo: extractKeyInformation(text)
    };

    setLocalAnalysis(analysis);
  }, []);

  // 語言檢測
  const detectLanguage = (text) => {
    const chineseChars = text.match(/[\u4e00-\u9fff]/g) || [];
    const totalChars = text.replace(/\s/g, '').length;
    
    if (totalChars === 0) return 'unknown';
    
    const chineseRatio = chineseChars.length / totalChars;
    
    if (chineseRatio > 0.3) return 'chinese';
    if (text.match(/[\u3040-\u309f\u30a0-\u30ff]/)) return 'japanese';
    if (text.match(/[\uac00-\ud7af]/)) return 'korean';
    
    return 'english';
  };

  // 內容類型檢測
  const detectContentType = (text) => {
    if (text.match(/```[\s\S]*```/)) return 'code_with_markdown';
    if (text.match(/function\s+\w+|class\s+\w+|import\s+\w+/)) return 'code';
    if (text.match(/^#\s+|^\*\s+|^\d+\.\s+/m)) return 'structured_document';
    if (text.match(/https?:\/\/\S+/)) return 'document_with_links';
    if (text.length > 1000) return 'long_document';
    
    return 'plain_text';
  };

  // 複雜度計算
  const calculateComplexity = (text) => {
    let score = 0;
    
    // 長度因子
    if (text.length > 5000) score += 3;
    else if (text.length > 1000) score += 2;
    else if (text.length > 500) score += 1;
    
    // 結構因子
    if (text.match(/```[\s\S]*```/)) score += 2;
    if (text.match(/^#{1,6}\s+/m)) score += 1;
    if (text.match(/https?:\/\/\S+/g)?.length > 5) score += 2;
    
    // 技術內容因子
    if (text.match(/function|class|import|const|let|var/g)?.length > 10) score += 3;
    
    if (score >= 7) return 'high';
    if (score >= 4) return 'medium';
    return 'low';
  };

  // 生成建議
  const generateSuggestions = (text) => {
    const suggestions = [];
    
    if (text.length > 2000) {
      suggestions.push({
        type: 'split',
        title: '建議分割內容',
        description: '內容較長，建議分割為多個較小的部分進行處理',
        action: 'split_content'
      });
    }
    
    if (text.match(/```[\s\S]*```/)) {
      suggestions.push({
        type: 'code',
        title: '代碼格式化',
        description: '檢測到代碼塊，可以進行語法高亮和格式化',
        action: 'format_code'
      });
    }
    
    if (text.match(/https?:\/\/\S+/g)?.length > 3) {
      suggestions.push({
        type: 'links',
        title: '鏈接提取',
        description: '檢測到多個鏈接，可以提取並整理',
        action: 'extract_links'
      });
    }
    
    if (text.match(/^#{1,6}\s+/gm)?.length > 3) {
      suggestions.push({
        type: 'outline',
        title: '生成目錄',
        description: '檢測到標題結構，可以生成文檔目錄',
        action: 'generate_outline'
      });
    }
    
    return suggestions;
  };

  // 提取關鍵信息
  const extractKeyInformation = (text) => {
    const info = {};
    
    // 提取鏈接
    const links = text.match(/https?:\/\/\S+/g) || [];
    if (links.length > 0) {
      info.links = [...new Set(links)].slice(0, 10);
    }
    
    // 提取標題
    const headings = text.match(/^#{1,6}\s+.+$/gm) || [];
    if (headings.length > 0) {
      info.headings = headings.map(h => h.replace(/^#+\s*/, '')).slice(0, 10);
    }
    
    // 提取代碼塊
    const codeBlocks = text.match(/```[\s\S]*?```/g) || [];
    if (codeBlocks.length > 0) {
      info.codeBlocks = codeBlocks.length;
    }
    
    // 提取關鍵詞（簡化版）
    const words = text.toLowerCase().match(/\b\w{4,}\b/g) || [];
    const wordCount = {};
    words.forEach(word => {
      wordCount[word] = (wordCount[word] || 0) + 1;
    });
    
    const keywords = Object.entries(wordCount)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([word, count]) => ({ word, count }));
    
    if (keywords.length > 0) {
      info.keywords = keywords;
    }
    
    return info;
  };

  // 執行本地處理操作
  const executeLocalAction = useCallback((action) => {
    setProcessingStatus('processing');
    
    setTimeout(() => {
      switch (action) {
        case 'split_content':
          handleSplitContent();
          break;
        case 'format_code':
          handleFormatCode();
          break;
        case 'extract_links':
          handleExtractLinks();
          break;
        case 'generate_outline':
          handleGenerateOutline();
          break;
        default:
          break;
      }
      setProcessingStatus('completed');
    }, 1000);
  }, [content]);

  // 分割內容
  const handleSplitContent = () => {
    const sections = content.split(/\n\s*\n/).filter(section => section.trim());
    const maxSectionLength = 1000;
    
    const splitSections = [];
    sections.forEach(section => {
      if (section.length <= maxSectionLength) {
        splitSections.push(section);
      } else {
        const words = section.split(' ');
        let currentSection = '';
        
        words.forEach(word => {
          if ((currentSection + ' ' + word).length <= maxSectionLength) {
            currentSection += (currentSection ? ' ' : '') + word;
          } else {
            if (currentSection) {
              splitSections.push(currentSection);
            }
            currentSection = word;
          }
        });
        
        if (currentSection) {
          splitSections.push(currentSection);
        }
      }
    });
    
    const newContent = splitSections.map((section, index) => 
      `## 部分 ${index + 1}\n\n${section}`
    ).join('\n\n---\n\n');
    
    setContent(newContent);
  };

  // 格式化代碼
  const handleFormatCode = () => {
    const formattedContent = content.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
      const lines = code.split('\n');
      const indentedLines = lines.map(line => {
        if (line.trim()) {
          return '  ' + line.trim();
        }
        return line;
      });
      
      return `\`\`\`${lang || 'text'}\n${indentedLines.join('\n')}\`\`\``;
    });
    
    setContent(formattedContent);
  };

  // 提取鏈接
  const handleExtractLinks = () => {
    const links = content.match(/https?:\/\/\S+/g) || [];
    const uniqueLinks = [...new Set(links)];
    
    const linkSection = '\n\n## 提取的鏈接\n\n' + 
      uniqueLinks.map((link, index) => `${index + 1}. ${link}`).join('\n');
    
    setContent(content + linkSection);
  };

  // 生成目錄
  const handleGenerateOutline = () => {
    const headings = content.match(/^(#{1,6})\s+(.+)$/gm) || [];
    
    if (headings.length > 0) {
      const outline = '\n\n## 文檔目錄\n\n' + 
        headings.map(heading => {
          const level = heading.match(/^#+/)[0].length;
          const title = heading.replace(/^#+\s*/, '');
          const indent = '  '.repeat(level - 1);
          return `${indent}- ${title}`;
        }).join('\n');
      
      setContent(outline + '\n\n---\n\n' + content);
    }
  };

  // 搜索和替換
  const handleSearchReplace = () => {
    if (searchTerm && replaceTerm) {
      const newContent = content.replaceAll(searchTerm, replaceTerm);
      setContent(newContent);
      setSearchTerm('');
      setReplaceTerm('');
    }
  };

  // 保存結果
  const handleSave = () => {
    const result = {
      processedContent: content,
      originalInput: input,
      processingInfo: {
        method: 'local_processing',
        timestamp: new Date().toISOString(),
        analysis: localAnalysis,
        reason: processingOptions?.reason
      }
    };
    
    onSaveResult(result);
  };

  // 複製內容
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      alert('內容已複製到剪貼板');
    } catch (err) {
      console.error('複製失敗:', err);
    }
  };

  // 下載文件
  const handleDownload = () => {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `processed_content_${Date.now()}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className={`local-processor ${isFullscreen ? 'fixed inset-0 z-50 bg-white' : 'p-6 bg-white border border-gray-200 rounded-lg shadow-sm'}`}>
      {/* 標題欄 */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">
          ClaudeEditor 本地處理
        </h3>
        
        <div className="flex items-center space-x-2">
          {/* 處理狀態 */}
          {processingStatus === 'processing' && (
            <div className="flex items-center text-blue-600">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
              <span className="text-sm">處理中...</span>
            </div>
          )}
          
          {processingStatus === 'completed' && (
            <div className="flex items-center text-green-600">
              <CheckCircle className="h-4 w-4 mr-2" />
              <span className="text-sm">處理完成</span>
            </div>
          )}
          
          {/* 工具欄 */}
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-2 text-gray-500 hover:text-gray-700 rounded"
          >
            {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {/* 處理原因顯示 */}
      {processingOptions?.reason && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-start">
            <AlertCircle className="h-5 w-5 text-yellow-600 mr-2 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-yellow-800 mb-1">
                <strong>本地處理原因:</strong> {getReasonText(processingOptions.reason)}
              </p>
              
              {processingOptions.incompatibilityReasons && (
                <ul className="text-xs text-yellow-700 list-disc list-inside">
                  {processingOptions.incompatibilityReasons.map((reason, index) => (
                    <li key={index}>{reason}</li>
                  ))}
                </ul>
              )}
              
              {processingOptions.suggestedActions && (
                <div className="mt-2">
                  <p className="text-xs text-yellow-700 font-medium">建議操作:</p>
                  <ul className="text-xs text-yellow-700 list-disc list-inside">
                    {processingOptions.suggestedActions.map((action, index) => (
                      <li key={index}>{action}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 主編輯區域 */}
        <div className="lg:col-span-2">
          {/* 搜索替換工具 */}
          <div className="mb-4 p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <Search className="h-4 w-4 text-gray-500" />
              <input
                type="text"
                placeholder="搜索..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded"
              />
            </div>
            <div className="flex items-center space-x-2">
              <Replace className="h-4 w-4 text-gray-500" />
              <input
                type="text"
                placeholder="替換為..."
                value={replaceTerm}
                onChange={(e) => setReplaceTerm(e.target.value)}
                className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded"
              />
              <button
                onClick={handleSearchReplace}
                disabled={!searchTerm || !replaceTerm}
                className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:bg-gray-400"
              >
                替換
              </button>
            </div>
          </div>

          {/* 內容編輯器 */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-gray-700">
                內容編輯器
              </label>
              <button
                onClick={() => setIsEditing(!isEditing)}
                className="flex items-center px-2 py-1 text-sm text-blue-600 hover:text-blue-800"
              >
                <Edit3 className="h-3 w-3 mr-1" />
                {isEditing ? '預覽' : '編輯'}
              </button>
            </div>
            
            {isEditing ? (
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="w-full h-96 p-3 border border-gray-300 rounded-lg font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="在此編輯內容..."
              />
            ) : (
              <div className="w-full h-96 p-3 border border-gray-300 rounded-lg bg-gray-50 overflow-auto">
                <pre className="whitespace-pre-wrap text-sm text-gray-800">
                  {content}
                </pre>
              </div>
            )}
          </div>

          {/* 操作按鈕 */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={handleSave}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              <Save className="h-4 w-4 mr-2" />
              保存結果
            </button>
            
            <button
              onClick={handleCopy}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Copy className="h-4 w-4 mr-2" />
              複製
            </button>
            
            <button
              onClick={handleDownload}
              className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              <Download className="h-4 w-4 mr-2" />
              下載
            </button>
            
            {onBackToClaudeCode && (
              <button
                onClick={() => onBackToClaudeCode(content)}
                className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
              >
                <Code className="h-4 w-4 mr-2" />
                重試 Claude Code
              </button>
            )}
          </div>
        </div>

        {/* 側邊欄 - 分析和建議 */}
        <div className="space-y-4">
          {/* 內容分析 */}
          {localAnalysis && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h4 className="text-sm font-medium text-blue-800 mb-3 flex items-center">
                <FileText className="h-4 w-4 mr-2" />
                內容分析
              </h4>
              
              <div className="space-y-2 text-xs text-blue-700">
                <div className="flex justify-between">
                  <span>字數:</span>
                  <span>{localAnalysis.wordCount}</span>
                </div>
                <div className="flex justify-between">
                  <span>字符數:</span>
                  <span>{localAnalysis.charCount}</span>
                </div>
                <div className="flex justify-between">
                  <span>行數:</span>
                  <span>{localAnalysis.lineCount}</span>
                </div>
                <div className="flex justify-between">
                  <span>語言:</span>
                  <span>{localAnalysis.language}</span>
                </div>
                <div className="flex justify-between">
                  <span>類型:</span>
                  <span>{localAnalysis.contentType}</span>
                </div>
                <div className="flex justify-between">
                  <span>複雜度:</span>
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    localAnalysis.complexity === 'high' ? 'bg-red-100 text-red-800' :
                    localAnalysis.complexity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {localAnalysis.complexity}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* 智能建議 */}
          {localAnalysis?.suggestions && localAnalysis.suggestions.length > 0 && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <h4 className="text-sm font-medium text-green-800 mb-3 flex items-center">
                <Lightbulb className="h-4 w-4 mr-2" />
                智能建議
              </h4>
              
              <div className="space-y-2">
                {localAnalysis.suggestions.map((suggestion, index) => (
                  <div key={index} className="p-2 bg-white rounded border border-green-200">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-green-800">
                        {suggestion.title}
                      </span>
                      <button
                        onClick={() => executeLocalAction(suggestion.action)}
                        className="px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700"
                      >
                        <Zap className="h-3 w-3" />
                      </button>
                    </div>
                    <p className="text-xs text-green-700">
                      {suggestion.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 提取的信息 */}
          {localAnalysis?.extractedInfo && Object.keys(localAnalysis.extractedInfo).length > 0 && (
            <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
              <h4 className="text-sm font-medium text-purple-800 mb-3">
                提取信息
              </h4>
              
              <div className="space-y-3 text-xs">
                {localAnalysis.extractedInfo.links && (
                  <div>
                    <span className="font-medium text-purple-800">鏈接 ({localAnalysis.extractedInfo.links.length}):</span>
                    <ul className="list-disc list-inside text-purple-700 mt-1">
                      {localAnalysis.extractedInfo.links.slice(0, 3).map((link, index) => (
                        <li key={index} className="truncate">{link}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {localAnalysis.extractedInfo.headings && (
                  <div>
                    <span className="font-medium text-purple-800">標題:</span>
                    <ul className="list-disc list-inside text-purple-700 mt-1">
                      {localAnalysis.extractedInfo.headings.slice(0, 3).map((heading, index) => (
                        <li key={index} className="truncate">{heading}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {localAnalysis.extractedInfo.codeBlocks && (
                  <div>
                    <span className="font-medium text-purple-800">
                      代碼塊: {localAnalysis.extractedInfo.codeBlocks} 個
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// 獲取處理原因的文本描述
const getReasonText = (reason) => {
  switch (reason) {
    case 'claude_code_unavailable':
      return 'Claude Code 服務暫時不可用';
    case 'input_not_compatible':
      return '輸入內容與 Claude Code 不兼容';
    case 'user_choice':
      return '用戶選擇在本地處理';
    case 'size_too_large':
      return '內容大小超出 Claude Code 限制';
    case 'contains_unsupported_elements':
      return '包含 Claude Code 不支持的元素';
    default:
      return reason || '未知原因';
  }
};

export default LocalProcessor;