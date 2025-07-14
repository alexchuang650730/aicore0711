import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Send, ArrowRight, ArrowLeft, AlertTriangle, CheckCircle, RefreshCw, Brain, Database } from 'lucide-react';

const ClaudeCodeIntegration = ({ processedInput, onLocalProcessing }) => {
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [lastError, setLastError] = useState(null);
  const [processingHistory, setProcessingHistory] = useState([]);
  const [claudeCodeResponse, setClaudeCodeResponse] = useState(null);
  const [memoryOSConnected, setMemoryOSConnected] = useState(false);
  const [learningStats, setLearningStats] = useState({ totalInteractions: 0, successRate: 0 });
  const [contextEnhancement, setContextEnhancement] = useState(null);

  // MemoryOS MCP 集成
  const memoryOSAPI = useRef({
    async initialize() {
      try {
        const response = await fetch('/api/memoryos/initialize', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        const result = await response.json();
        setMemoryOSConnected(result.success);
        return result.success;
      } catch (error) {
        console.error('MemoryOS initialization failed:', error);
        setMemoryOSConnected(false);
        return false;
      }
    },

    async getContextEnhancement(userInput) {
      try {
        const response = await fetch('/api/memoryos/context-enhancement', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            query: userInput,
            context_type: 'claude_interaction',
            limit: 5
          })
        });
        const result = await response.json();
        return result.enhancement;
      } catch (error) {
        console.error('Context enhancement failed:', error);
        return null;
      }
    },

    async recordInteraction(interaction) {
      try {
        const response = await fetch('/api/memoryos/record-interaction', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_input: interaction.input,
            claude_response: interaction.response,
            response_time: interaction.responseTime,
            user_satisfaction: interaction.satisfaction || 0,
            metadata: {
              input_type: interaction.inputType,
              processing_method: interaction.processingMethod,
              timestamp: Date.now()
            }
          })
        });
        const result = await response.json();
        return result.success;
      } catch (error) {
        console.error('Interaction recording failed:', error);
        return false;
      }
    },

    async sendToPowerAutomationCore(data) {
      try {
        const response = await fetch('/api/powerautomation/learn', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            source: 'claude_code_integration',
            data: data,
            learning_type: 'claude_interaction',
            timestamp: Date.now()
          })
        });
        const result = await response.json();
        return result.success;
      } catch (error) {
        console.error('PowerAutomation Core learning failed:', error);
        return false;
      }
    },

    async getLearningStats() {
      try {
        const response = await fetch('/api/memoryos/learning-stats');
        const result = await response.json();
        return result.stats;
      } catch (error) {
        console.error('Learning stats failed:', error);
        return { totalInteractions: 0, successRate: 0 };
      }
    }
  });

  // 初始化 MemoryOS MCP
  useEffect(() => {
    memoryOSAPI.current.initialize().then(success => {
      if (success) {
        memoryOSAPI.current.getLearningStats().then(stats => {
          setLearningStats(stats);
        });
      }
    });
  }, []);

  // 檢查輸入是否適合 Claude Code
  const isClaudeCodeCompatible = useCallback((input) => {
    if (!input) return false;

    // Claude Code 支持的格式檢查
    const compatibleTypes = ['text', 'code', 'document', 'web_content'];
    const maxSize = 1000000; // 1MB 文本限制
    const hasUnsupportedFeatures = input.metadata?.containsImages || 
                                  input.metadata?.containsInteractiveElements ||
                                  input.metadata?.requiresSpecialProcessing;

    return (
      compatibleTypes.includes(input.type) &&
      input.content.length <= maxSize &&
      !hasUnsupportedFeatures
    );
  }, []);

  // 轉換輸入為 Claude Code 格式
  const convertToClaudeCodeFormat = useCallback((input) => {
    const timestamp = new Date().toISOString();
    
    switch (input.type) {
      case 'document':
        return {
          type: 'file_content',
          content: input.content,
          metadata: {
            filename: input.filename,
            file_type: input.format,
            processing_timestamp: timestamp,
            source: 'claudeditor_pdf_processor'
          }
        };

      case 'web_content':
        return {
          type: 'web_article',
          content: input.content,
          metadata: {
            source_url: input.source_url,
            title: input.metadata?.title,
            author: input.metadata?.author,
            word_count: input.metadata?.wordCount,
            processing_timestamp: timestamp,
            source: 'claudeditor_url_processor'
          }
        };

      default:
        return {
          type: 'text_input',
          content: input.content,
          metadata: {
            processing_timestamp: timestamp,
            source: 'claudeditor_general_processor'
          }
        };
    }
  }, []);

  // 發送到 Claude Code (支持雙向學習)
  const sendToClaudeCode = useCallback(async (input) => {
    setIsConnecting(true);
    setLastError(null);
    
    const startTime = Date.now();

    try {
      setConnectionStatus('connecting');
      
      // 1. 從 MemoryOS MCP 獲取上下文增強
      const enhancement = await memoryOSAPI.current.getContextEnhancement(input.content);
      setContextEnhancement(enhancement);

      // 2. 構建增強的 Claude Code 輸入
      const claudeCodeInput = convertToClaudeCodeFormat(input);
      
      // 如果有上下文增強，添加到輸入中
      if (enhancement) {
        claudeCodeInput.context_enhancement = {
          relevant_contexts: enhancement.relevant_contexts,
          user_preferences: enhancement.user_preferences,
          similar_interactions: enhancement.similar_interactions,
          best_practices: enhancement.best_practices
        };
      }

      // 3. 發送到真實的 Claude Code API
      const response = await fetch('https://api.claude.ai/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.CLAUDE_API_KEY}`,
          'anthropic-version': '2023-06-01',
          'X-ClaudeEditor-Source': 'true',
          'X-MemoryOS-Enhanced': enhancement ? 'true' : 'false'
        },
        body: JSON.stringify({
          model: 'claude-3-sonnet-20240229',
          max_tokens: 4000,
          temperature: 0.1,
          messages: [
            {
              role: 'user',
              content: claudeCodeInput.content
            }
          ],
          metadata: {
            source: 'claudeditor',
            enhancement: enhancement ? 'enabled' : 'disabled',
            input_type: claudeCodeInput.type,
            context_enhancement: claudeCodeInput.context_enhancement || null
          }
        })
      });

      if (!response.ok) {
        throw new Error(`Claude Code API 錯誤: ${response.status}`);
      }

      const result = await response.json();
      const responseTime = Date.now() - startTime;
      
      setConnectionStatus('connected');
      setClaudeCodeResponse(result);
      
      // 4. 記錄交互到 MemoryOS MCP
      const interactionData = {
        input: input.content,
        inputType: input.type,
        response: result.response || result.content,
        responseTime: responseTime,
        processingMethod: 'claude_code',
        contextEnhanced: !!enhancement,
        satisfaction: 0.8 // 預設滿意度，稍後可由用戶調整
      };

      await memoryOSAPI.current.recordInteraction(interactionData);

      // 5. 同時發送學習數據到 PowerAutomation Core
      await memoryOSAPI.current.sendToPowerAutomationCore({
        interaction: interactionData,
        success: true,
        performance_metrics: {
          response_time: responseTime,
          context_enhancement_used: !!enhancement,
          input_complexity: input.content.length,
          output_quality: result.confidence || 0.8
        }
      });

      // 6. 更新學習統計
      const updatedStats = await memoryOSAPI.current.getLearningStats();
      setLearningStats(updatedStats);
      
      // 7. 添加到處理歷史
      const historyEntry = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        input: input,
        claudeCodeInput: claudeCodeInput,
        response: result,
        responseTime: responseTime,
        contextEnhanced: !!enhancement,
        status: 'success'
      };
      
      setProcessingHistory(prev => [historyEntry, ...prev.slice(0, 9)]); // 保留最近10條
      
    } catch (error) {
      console.error('Claude Code 集成錯誤:', error);
      setLastError(error.message);
      setConnectionStatus('error');
      
      // 記錄失敗的交互
      const failedInteraction = {
        input: input.content,
        inputType: input.type,
        response: null,
        responseTime: Date.now() - startTime,
        processingMethod: 'claude_code_failed',
        error: error.message,
        satisfaction: 0.2 // 失敗的滿意度
      };

      await memoryOSAPI.current.recordInteraction(failedInteraction);
      
      // 如果 Claude Code 不可用，回退到本地處理
      handleFallbackToLocal(input, error);
      
    } finally {
      setIsConnecting(false);
    }
  }, [convertToClaudeCodeFormat, contextEnhancement]);

  // 回退到本地處理
  const handleFallbackToLocal = useCallback((input, originalError) => {
    console.log('回退到 ClaudeEditor 本地處理');
    
    const localProcessingOptions = {
      reason: 'claude_code_unavailable',
      originalError: originalError.message,
      suggestedActions: [
        '在 ClaudeEditor 中直接編輯內容',
        '使用本地語法高亮和代碼分析',
        '保存為本地項目文件',
        '稍後重試 Claude Code 連接'
      ]
    };
    
    onLocalProcessing(input, localProcessingOptions);
    
  }, [onLocalProcessing]);

  // 智能路由決策
  const handleSmartRouting = useCallback(async (input) => {
    if (!input) return;

    // 檢查是否適合 Claude Code
    if (isClaudeCodeCompatible(input)) {
      await sendToClaudeCode(input);
    } else {
      // 不適合 Claude Code，使用本地處理
      const localProcessingOptions = {
        reason: 'input_not_compatible',
        incompatibilityReasons: getIncompatibilityReasons(input),
        suggestedActions: [
          '在 ClaudeEditor 中預處理內容',
          '分割大文件為小塊',
          '移除不支持的元素',
          '使用本地編輯功能'
        ]
      };
      
      onLocalProcessing(input, localProcessingOptions);
    }
  }, [isClaudeCodeCompatible, sendToClaudeCode, onLocalProcessing]);

  // 獲取不兼容原因
  const getIncompatibilityReasons = (input) => {
    const reasons = [];
    
    if (input.content.length > 1000000) {
      reasons.push('內容大小超過 1MB 限制');
    }
    
    if (input.metadata?.containsImages) {
      reasons.push('包含圖片內容');
    }
    
    if (input.metadata?.containsInteractiveElements) {
      reasons.push('包含互動元素');
    }
    
    if (!['text', 'code', 'document', 'web_content'].includes(input.type)) {
      reasons.push('不支持的內容類型');
    }
    
    return reasons;
  };

  // 重試連接
  const retryConnection = useCallback(() => {
    if (processedInput) {
      handleSmartRouting(processedInput);
    }
  }, [processedInput, handleSmartRouting]);

  return (
    <div className="claude-code-integration p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">
          Claude Code 集成
        </h3>
        
        {/* 連接狀態指示器 */}
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${
            connectionStatus === 'connected' ? 'bg-green-500' :
            connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
            connectionStatus === 'error' ? 'bg-red-500' : 'bg-gray-400'
          }`}></div>
          <span className="text-sm text-gray-600">
            {connectionStatus === 'connected' ? '已連接' :
             connectionStatus === 'connecting' ? '連接中' :
             connectionStatus === 'error' ? '連接錯誤' : '未連接'}
          </span>
        </div>
      </div>

      {/* 錯誤顯示 */}
      {lastError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start">
          <AlertTriangle className="h-5 w-5 text-red-600 mr-2 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-red-800 mb-2">{lastError}</p>
            <button
              onClick={retryConnection}
              className="text-xs text-red-600 hover:text-red-800 underline"
            >
              重試連接
            </button>
          </div>
        </div>
      )}

      {/* 輸入處理狀態 */}
      {processedInput && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h4 className="text-sm font-medium text-blue-800 mb-2">
            待處理輸入
          </h4>
          <div className="text-xs text-blue-700 space-y-1">
            <p><strong>類型:</strong> {processedInput.type}</p>
            <p><strong>大小:</strong> {processedInput.content.length} 字符</p>
            {processedInput.filename && (
              <p><strong>文件:</strong> {processedInput.filename}</p>
            )}
            {processedInput.source_url && (
              <p><strong>來源:</strong> {processedInput.source_url}</p>
            )}
          </div>
          
          {/* 兼容性檢查 */}
          <div className="mt-3 flex items-center">
            {isClaudeCodeCompatible(processedInput) ? (
              <div className="flex items-center text-green-700">
                <CheckCircle className="h-4 w-4 mr-1" />
                <span className="text-xs">Claude Code 兼容</span>
              </div>
            ) : (
              <div className="flex items-center text-orange-700">
                <AlertTriangle className="h-4 w-4 mr-1" />
                <span className="text-xs">需要本地處理</span>
              </div>
            )}
          </div>

          {/* 處理按鈕 */}
          <div className="mt-4 flex space-x-2">
            <button
              onClick={() => handleSmartRouting(processedInput)}
              disabled={isConnecting}
              className="flex items-center px-3 py-1.5 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:bg-gray-400"
            >
              {isConnecting ? (
                <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
              ) : (
                <Send className="h-3 w-3 mr-1" />
              )}
              智能處理
            </button>
            
            <button
              onClick={() => onLocalProcessing(processedInput, { reason: 'user_choice' })}
              className="flex items-center px-3 py-1.5 bg-gray-600 text-white text-xs rounded hover:bg-gray-700"
            >
              <ArrowLeft className="h-3 w-3 mr-1" />
              本地處理
            </button>
          </div>
        </div>
      )}

      {/* Claude Code 響應 */}
      {claudeCodeResponse && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <h4 className="text-sm font-medium text-green-800 mb-2">
            Claude Code 響應
          </h4>
          <div className="text-xs text-green-700">
            <p><strong>狀態:</strong> {claudeCodeResponse.status}</p>
            <p><strong>處理時間:</strong> {claudeCodeResponse.processingTime}ms</p>
            {claudeCodeResponse.suggestions && (
              <div className="mt-2">
                <strong>建議:</strong>
                <ul className="list-disc list-inside mt-1">
                  {claudeCodeResponse.suggestions.map((suggestion, index) => (
                    <li key={index}>{suggestion}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 處理歷史 */}
      {processingHistory.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            處理歷史
          </h4>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {processingHistory.map((entry) => (
              <div key={entry.id} className="p-2 bg-gray-50 rounded text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">
                    {new Date(entry.timestamp).toLocaleTimeString()}
                  </span>
                  <span className={`px-2 py-0.5 rounded ${
                    entry.status === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {entry.status}
                  </span>
                </div>
                <p className="text-gray-700 mt-1">
                  {entry.input.type} → {entry.response?.status || 'failed'}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 使用說明 */}
      <div className="bg-gray-50 p-3 rounded-lg">
        <h5 className="text-xs font-medium text-gray-700 mb-2">
          智能處理流程
        </h5>
        <ol className="text-xs text-gray-600 space-y-1">
          <li>1. 自動檢測輸入內容兼容性</li>
          <li>2. 適合的內容發送到 Claude Code</li>
          <li>3. 不適合的內容在 ClaudeEditor 本地處理</li>
          <li>4. 支持錯誤回退和重試機制</li>
        </ol>
      </div>
    </div>
  );
};

export default ClaudeCodeIntegration;