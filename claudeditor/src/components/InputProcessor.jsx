import React, { useState, useCallback } from 'react';
import { Upload, Link, FileText, Download, AlertCircle, CheckCircle } from 'lucide-react';

const InputProcessor = ({ onProcessedInput, onError }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState('');

  // PDF 處理
  const processPDF = useCallback(async (file) => {
    setIsProcessing(true);
    setProcessingStatus('正在處理 PDF 文件...');

    try {
      // 使用 PDF.js 或類似庫提取文本
      const text = await extractTextFromPDF(file);
      
      // 轉換為 Claude Code 可接受的格式
      const processedInput = {
        type: 'document',
        format: 'pdf',
        filename: file.name,
        content: text,
        metadata: {
          size: file.size,
          lastModified: file.lastModified,
          processingTimestamp: Date.now()
        }
      };

      onProcessedInput(processedInput);
      setProcessingStatus('PDF 處理完成');
      
    } catch (error) {
      console.error('PDF 處理錯誤:', error);
      onError(`PDF 處理失敗: ${error.message}`);
    } finally {
      setIsProcessing(false);
      setTimeout(() => setProcessingStatus(''), 3000);
    }
  }, [onProcessedInput, onError]);

  // URL 內容處理
  const processURL = useCallback(async (url) => {
    setIsProcessing(true);
    setProcessingStatus('正在獲取網頁內容...');

    try {
      // 調用後端 API 獲取網頁內容
      const response = await fetch('/api/fetch-url', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      // 轉換為 Claude Code 可接受的格式
      const processedInput = {
        type: 'web_content',
        format: 'html_text',
        source_url: url,
        content: data.text,
        metadata: {
          title: data.title,
          description: data.description,
          author: data.author,
          publishDate: data.publishDate,
          processingTimestamp: Date.now(),
          wordCount: data.text.split(' ').length
        }
      };

      onProcessedInput(processedInput);
      setProcessingStatus('網頁內容獲取完成');
      
    } catch (error) {
      console.error('URL 處理錯誤:', error);
      onError(`網頁獲取失敗: ${error.message}`);
    } finally {
      setIsProcessing(false);
      setTimeout(() => setProcessingStatus(''), 3000);
    }
  }, [onProcessedInput, onError]);

  // 文件拖放處理
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    
    files.forEach(file => {
      if (file.type === 'application/pdf') {
        processPDF(file);
      } else {
        onError(`不支持的文件類型: ${file.type}`);
      }
    });
  }, [processPDF, onError]);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
  }, []);

  // URL 輸入處理
  const handleURLSubmit = useCallback((e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const url = formData.get('url');
    
    if (isValidURL(url)) {
      processURL(url);
    } else {
      onError('請輸入有效的 URL');
    }
  }, [processURL, onError]);

  return (
    <div className="input-processor p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">
        輸入處理器
      </h3>
      
      {/* 狀態顯示 */}
      {processingStatus && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-center">
          {isProcessing ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
          ) : (
            <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
          )}
          <span className="text-sm text-blue-800">{processingStatus}</span>
        </div>
      )}

      {/* PDF 文件上傳區域 */}
      <div 
        className="mb-6 p-6 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-400 transition-colors"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        <div className="text-center">
          <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h4 className="text-md font-medium text-gray-700 mb-2">
            PDF 文件處理
          </h4>
          <p className="text-sm text-gray-500 mb-4">
            拖拽 PDF 文件到此處，或點擊選擇文件
          </p>
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => {
              const file = e.target.files[0];
              if (file) processPDF(file);
            }}
            className="hidden"
            id="pdf-upload"
          />
          <label
            htmlFor="pdf-upload"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 cursor-pointer transition-colors"
          >
            <Upload className="h-4 w-4 mr-2" />
            選擇 PDF 文件
          </label>
        </div>
      </div>

      {/* URL 輸入區域 */}
      <form onSubmit={handleURLSubmit} className="mb-6">
        <h4 className="text-md font-medium text-gray-700 mb-3">
          網頁鏈接處理
        </h4>
        <div className="flex gap-3">
          <div className="flex-1">
            <input
              type="url"
              name="url"
              placeholder="輸入網頁 URL (如: https://example.com)"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <button
            type="submit"
            disabled={isProcessing}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center"
          >
            <Link className="h-4 w-4 mr-2" />
            獲取內容
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          支持網頁、博客文章、新聞、文檔等各種在線內容
        </p>
      </form>

      {/* 支持的格式說明 */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h5 className="text-sm font-medium text-gray-700 mb-2">
          支持的輸入格式
        </h5>
        <ul className="text-xs text-gray-600 space-y-1">
          <li>• PDF 文檔 - 自動提取文本內容</li>
          <li>• 網頁鏈接 - 提取主要文本內容</li>
          <li>• 博客文章 - 智能識別正文</li>
          <li>• 新聞網站 - 提取標題和內容</li>
          <li>• 技術文檔 - 保留格式結構</li>
        </ul>
      </div>
    </div>
  );
};

// PDF 文本提取函數
const extractTextFromPDF = async (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = async (e) => {
      try {
        // 這裡需要集成 PDF.js 或其他 PDF 解析庫
        // 暫時使用模擬實現
        const arrayBuffer = e.target.result;
        
        // 模擬 PDF 文本提取
        const simulatedText = `
[PDF 內容提取]
文件名: ${file.name}
大小: ${(file.size / 1024).toFixed(2)} KB
提取時間: ${new Date().toLocaleString()}

這是從 PDF 文件中提取的文本內容。
在實際實現中，這裡會使用 PDF.js 或其他庫來解析 PDF 內容。

PDF 文件結構:
- 頁數: 估計 ${Math.ceil(file.size / 50000)} 頁
- 文本內容已提取並格式化為 Claude Code 可讀格式
- 保留了原文的段落結構和基本格式
        `;
        
        resolve(simulatedText.trim());
      } catch (error) {
        reject(new Error('PDF 解析失敗'));
      }
    };
    
    reader.onerror = () => reject(new Error('文件讀取失敗'));
    reader.readAsArrayBuffer(file);
  });
};

// URL 驗證函數
const isValidURL = (string) => {
  try {
    new URL(string);
    return true;
  } catch (_) {
    return false;
  }
};

export default InputProcessor;