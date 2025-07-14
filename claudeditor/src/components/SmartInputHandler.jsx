import React, { useState, useCallback } from 'react';
import { ArrowRight, RefreshCw, CheckCircle, AlertTriangle, Info } from 'lucide-react';
import InputProcessor from './InputProcessor';
import ClaudeCodeIntegration from './ClaudeCodeIntegration';
import LocalProcessor from './LocalProcessor';

const SmartInputHandler = () => {
  const [currentStep, setCurrentStep] = useState('input'); // 'input', 'routing', 'local', 'success'
  const [processedInput, setProcessedInput] = useState(null);
  const [processingOptions, setProcessingOptions] = useState(null);
  const [finalResult, setFinalResult] = useState(null);
  const [errors, setErrors] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // 處理輸入成功
  const handleProcessedInput = useCallback((input) => {
    setProcessedInput(input);
    setCurrentStep('routing');
    setErrors([]);
    
    console.log('處理輸入成功:', input);
  }, []);

  // 處理輸入錯誤
  const handleInputError = useCallback((error) => {
    setErrors(prev => [...prev, {
      id: Date.now(),
      type: 'input_error',
      message: error,
      timestamp: new Date().toISOString()
    }]);
  }, []);

  // 本地處理回調
  const handleLocalProcessing = useCallback((input, options) => {
    setProcessingOptions(options);
    setCurrentStep('local');
    
    console.log('轉到本地處理:', { input, options });
  }, []);

  // 保存本地處理結果
  const handleSaveLocalResult = useCallback((result) => {
    setFinalResult(result);
    setCurrentStep('success');
    
    console.log('本地處理完成:', result);
  }, []);

  // 重新嘗試 Claude Code
  const handleRetryClaudeCode = useCallback((content) => {
    // 創建新的輸入對象
    const newInput = {
      ...processedInput,
      content: content,
      metadata: {
        ...processedInput.metadata,
        retryAttempt: true,
        lastModified: Date.now()
      }
    };
    
    setProcessedInput(newInput);
    setCurrentStep('routing');
    
    console.log('重試 Claude Code:', newInput);
  }, [processedInput]);

  // 重新開始
  const handleRestart = useCallback(() => {
    setCurrentStep('input');
    setProcessedInput(null);
    setProcessingOptions(null);
    setFinalResult(null);
    setErrors([]);
    setIsProcessing(false);
  }, []);

  // 清除錯誤
  const handleClearErrors = useCallback(() => {
    setErrors([]);
  }, []);

  return (
    <div className="smart-input-handler max-w-7xl mx-auto p-6">
      {/* 頁面標題 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          ClaudeEditor 智能輸入處理系統
        </h1>
        <p className="text-gray-600">
          支持 PDF、網頁鏈接等多種輸入格式，智能選擇最佳處理方式
        </p>
      </div>

      {/* 進度指示器 */}
      <div className="mb-8">
        <div className="flex items-center space-x-4">
          <StepIndicator 
            step="input" 
            currentStep={currentStep} 
            label="輸入處理" 
            icon="📁"
          />
          <ArrowRight className="h-4 w-4 text-gray-400" />
          <StepIndicator 
            step="routing" 
            currentStep={currentStep} 
            label="智能路由" 
            icon="🧠"
          />
          <ArrowRight className="h-4 w-4 text-gray-400" />
          <StepIndicator 
            step="local" 
            currentStep={currentStep} 
            label="本地處理" 
            icon="💻"
            optional={true}
          />
          <ArrowRight className="h-4 w-4 text-gray-400" />
          <StepIndicator 
            step="success" 
            currentStep={currentStep} 
            label="完成" 
            icon="✅"
          />
        </div>
      </div>

      {/* 錯誤顯示 */}
      {errors.length > 0 && (
        <div className="mb-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-red-800">
                處理錯誤 ({errors.length})
              </h3>
              <button
                onClick={handleClearErrors}
                className="text-xs text-red-600 hover:text-red-800 underline"
              >
                清除
              </button>
            </div>
            <div className="space-y-1">
              {errors.map(error => (
                <div key={error.id} className="text-sm text-red-700">
                  <span className="font-medium">{error.type}:</span> {error.message}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 主要內容區域 */}
      <div className="space-y-6">
        {/* 步驟 1: 輸入處理 */}
        {currentStep === 'input' && (
          <div className="transition-all duration-300">
            <InputProcessor
              onProcessedInput={handleProcessedInput}
              onError={handleInputError}
            />
            
            {/* 使用說明 */}
            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h3 className="text-sm font-medium text-blue-800 mb-2 flex items-center">
                <Info className="h-4 w-4 mr-2" />
                使用說明
              </h3>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• 支持拖拽或選擇 PDF 文件進行文本提取</li>
                <li>• 輸入任何網頁 URL 自動獲取主要內容</li>
                <li>• 系統會智能分析內容並選擇最佳處理方式</li>
                <li>• 不兼容 Claude Code 的內容會自動轉到本地處理</li>
              </ul>
            </div>
          </div>
        )}

        {/* 步驟 2: 智能路由 */}
        {currentStep === 'routing' && processedInput && (
          <div className="transition-all duration-300">
            <ClaudeCodeIntegration
              processedInput={processedInput}
              onLocalProcessing={handleLocalProcessing}
            />
            
            {/* 重新開始按鈕 */}
            <div className="mt-4 flex justify-center">
              <button
                onClick={handleRestart}
                className="flex items-center px-4 py-2 text-gray-600 hover:text-gray-800 text-sm"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                重新開始
              </button>
            </div>
          </div>
        )}

        {/* 步驟 3: 本地處理 */}
        {currentStep === 'local' && processedInput && processingOptions && (
          <div className="transition-all duration-300">
            <LocalProcessor
              input={processedInput}
              processingOptions={processingOptions}
              onSaveResult={handleSaveLocalResult}
              onBackToClaudeCode={handleRetryClaudeCode}
            />
          </div>
        )}

        {/* 步驟 4: 完成 */}
        {currentStep === 'success' && finalResult && (
          <div className="transition-all duration-300">
            <div className="p-6 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center mb-4">
                <CheckCircle className="h-6 w-6 text-green-600 mr-3" />
                <h2 className="text-lg font-semibold text-green-800">
                  處理完成！
                </h2>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div className="bg-white p-4 rounded border border-green-200">
                  <h3 className="text-sm font-medium text-green-800 mb-2">
                    處理信息
                  </h3>
                  <div className="text-sm text-green-700 space-y-1">
                    <p><strong>方法:</strong> {finalResult.processingInfo.method}</p>
                    <p><strong>時間:</strong> {new Date(finalResult.processingInfo.timestamp).toLocaleString()}</p>
                    <p><strong>原因:</strong> {finalResult.processingInfo.reason}</p>
                  </div>
                </div>
                
                <div className="bg-white p-4 rounded border border-green-200">
                  <h3 className="text-sm font-medium text-green-800 mb-2">
                    內容統計
                  </h3>
                  <div className="text-sm text-green-700 space-y-1">
                    <p><strong>原始長度:</strong> {finalResult.originalInput.content.length} 字符</p>
                    <p><strong>處理後長度:</strong> {finalResult.processedContent.length} 字符</p>
                    <p><strong>類型:</strong> {finalResult.originalInput.type}</p>
                  </div>
                </div>
              </div>
              
              {/* 最終結果預覽 */}
              <div className="mb-6">
                <h3 className="text-sm font-medium text-green-800 mb-2">
                  處理結果預覽
                </h3>
                <div className="max-h-40 overflow-y-auto p-3 bg-white border border-green-200 rounded">
                  <pre className="whitespace-pre-wrap text-sm text-gray-700">
                    {finalResult.processedContent.substring(0, 500)}
                    {finalResult.processedContent.length > 500 && '...'}
                  </pre>
                </div>
              </div>
              
              {/* 操作按鈕 */}
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(finalResult.processedContent);
                    alert('結果已複製到剪貼板');
                  }}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  複製結果
                </button>
                
                <button
                  onClick={() => {
                    const blob = new Blob([finalResult.processedContent], { type: 'text/plain' });
                    const url = URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = `claudeditor_result_${Date.now()}.txt`;
                    link.click();
                    URL.revokeObjectURL(url);
                  }}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  下載結果
                </button>
                
                <button
                  onClick={handleRestart}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  處理新內容
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 系統狀態欄 */}
      <div className="mt-8 p-4 bg-gray-50 border border-gray-200 rounded-lg">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div className="flex items-center space-x-4">
            <span>狀態: {getStepLabel(currentStep)}</span>
            {processedInput && (
              <span>輸入類型: {processedInput.type}</span>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span>系統正常</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// 步驟指示器組件
const StepIndicator = ({ step, currentStep, label, icon, optional = false }) => {
  const isActive = currentStep === step;
  const isCompleted = getStepIndex(currentStep) > getStepIndex(step);
  
  return (
    <div className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
      isActive ? 'bg-blue-100 text-blue-800' :
      isCompleted ? 'bg-green-100 text-green-800' :
      'bg-gray-100 text-gray-600'
    }`}>
      <span className="text-sm">{icon}</span>
      <span className="text-sm font-medium">
        {label}
        {optional && <span className="text-xs ml-1">(可選)</span>}
      </span>
      {isCompleted && <CheckCircle className="h-4 w-4" />}
    </div>
  );
};

// 獲取步驟索引
const getStepIndex = (step) => {
  const steps = ['input', 'routing', 'local', 'success'];
  return steps.indexOf(step);
};

// 獲取步驟標籤
const getStepLabel = (step) => {
  const labels = {
    'input': '等待輸入',
    'routing': '智能路由中',
    'local': '本地處理中',
    'success': '處理完成'
  };
  return labels[step] || '未知狀態';
};

export default SmartInputHandler;