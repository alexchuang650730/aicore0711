import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Play, 
  Pause, 
  Square, 
  SkipBack, 
  SkipForward, 
  Volume2, 
  VolumeX,
  Maximize,
  Code,
  Image,
  Video,
  FileText,
  BarChart3,
  Layers,
  Zap,
  Timer,
  Users
} from 'lucide-react';

interface Slide {
  id: string;
  title: string;
  type: 'code' | 'text' | 'image' | 'video' | 'chart' | 'interactive';
  content: any;
  duration?: number;
  transition?: 'fade' | 'slide' | 'zoom' | 'flip';
  notes?: string;
}

interface PresentationState {
  currentSlide: number;
  slides: Slide[];
  isPlaying: boolean;
  settings: {
    autoAdvance: boolean;
    slideInterval: number;
    showNotes: boolean;
    theme: 'light' | 'dark' | 'custom';
    transition: 'fade' | 'slide' | 'zoom' | 'flip';
  };
  playbackHistory: number[];
}

interface PresentationModeProps {
  isActive: boolean;
  state: PresentationState;
  onStateChange: (state: PresentationState) => void;
  isFullscreen?: boolean;
}

export const PresentationMode: React.FC<PresentationModeProps> = ({
  isActive,
  state,
  onStateChange,
  isFullscreen = false
}) => {
  const [showControls, setShowControls] = useState(true);
  const [showNotes, setShowNotes] = useState(state.settings.showNotes);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const slideRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const [slideStartTime, setSlideStartTime] = useState(Date.now());
  const [totalPresentationTime, setTotalPresentationTime] = useState(0);

  // 示例幻灯片数据
  const defaultSlides: Slide[] = [
    {
      id: 'slide-1',
      title: '欢迎使用 ClaudeEditor',
      type: 'text',
      content: {
        title: 'ClaudeEditor',
        subtitle: 'AI 驱动的跨平台代码编辑器',
        bullets: [
          '智能代码补全和建议',
          '实时协作编辑',
          '内置 AI 助手',
          '跨平台支持'
        ]
      },
      transition: 'fade',
      notes: '介绍 ClaudeEditor 的主要特性和优势'
    },
    {
      id: 'slide-2',
      title: '代码演示',
      type: 'code',
      content: {
        language: 'typescript',
        code: `// ClaudeEditor AI 助手示例
import { AIAssistant } from '@claudeditor/ai';

class SmartCodeEditor {
  private assistant: AIAssistant;
  
  constructor() {
    this.assistant = new AIAssistant({
      model: 'claude-3-sonnet',
      features: ['completion', 'refactoring', 'debugging']
    });
  }
  
  async generateCode(prompt: string): Promise<string> {
    const result = await this.assistant.complete({
      prompt,
      context: this.getCurrentContext(),
      language: this.getActiveLanguage()
    });
    
    return result.code;
  }
  
  async refactorCode(selection: string): Promise<string> {
    return await this.assistant.refactor(selection, {
      style: 'modern',
      performance: 'optimized',
      readability: 'high'
    });
  }
}`,
        highlights: [
          { line: 8, type: 'info', message: 'AI 助手初始化' },
          { line: 15, type: 'success', message: '智能代码生成' },
          { line: 23, type: 'warning', message: '代码重构功能' }
        ]
      },
      transition: 'slide',
      notes: '展示 ClaudeEditor 的 AI 代码生成和重构功能'
    },
    {
      id: 'slide-3',
      title: '功能特性',
      type: 'interactive',
      content: {
        features: [
          {
            icon: 'Code',
            title: '智能编码',
            description: 'AI 驱动的代码补全、生成和优化',
            demo: 'code-completion'
          },
          {
            icon: 'Users',
            title: '实时协作',
            description: '多人同时编辑，实时同步更改',
            demo: 'collaboration'
          },
          {
            icon: 'Zap',
            title: '快速部署',
            description: '一键部署到云平台，支持多种环境',
            demo: 'deployment'
          },
          {
            icon: 'BarChart3',
            title: '性能分析',
            description: '代码性能监控和优化建议',
            demo: 'analytics'
          }
        ]
      },
      transition: 'zoom',
      notes: '交互式展示主要功能特性'
    }
  ];

  // 初始化幻灯片
  useEffect(() => {
    if (state.slides.length === 0) {
      const newState = {
        ...state,
        slides: defaultSlides
      };
      onStateChange(newState);
    }
  }, [state, onStateChange]);

  // 自动播放控制
  useEffect(() => {
    if (state.isPlaying && state.settings.autoAdvance) {
      timerRef.current = setTimeout(() => {
        nextSlide();
      }, state.settings.slideInterval * 1000);
    } else if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [state.isPlaying, state.currentSlide, state.settings.autoAdvance, state.settings.slideInterval]);

  // 键盘控制
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!isActive) return;

      switch (event.key) {
        case 'ArrowRight':
        case ' ':
          event.preventDefault();
          nextSlide();
          break;
        case 'ArrowLeft':
          event.preventDefault();
          previousSlide();
          break;
        case 'Home':
          event.preventDefault();
          goToSlide(0);
          break;
        case 'End':
          event.preventDefault();
          goToSlide(state.slides.length - 1);
          break;
        case 'p':
        case 'P':
          event.preventDefault();
          togglePlayback();
          break;
        case 'n':
        case 'N':
          event.preventDefault();
          setShowNotes(!showNotes);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isActive, state.currentSlide, state.slides.length, showNotes]);

  // 鼠标控制显示
  useEffect(() => {
    let hideTimer: NodeJS.Timeout;

    const handleMouseMove = () => {
      setShowControls(true);
      clearTimeout(hideTimer);
      hideTimer = setTimeout(() => {
        if (state.isPlaying) {
          setShowControls(false);
        }
      }, 3000);
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      clearTimeout(hideTimer);
    };
  }, [state.isPlaying]);

  // 幻灯片导航
  const nextSlide = useCallback(() => {
    if (state.currentSlide < state.slides.length - 1) {
      const newState = {
        ...state,
        currentSlide: state.currentSlide + 1,
        playbackHistory: [...state.playbackHistory, state.currentSlide]
      };
      onStateChange(newState);
      setSlideStartTime(Date.now());
    }
  }, [state, onStateChange]);

  const previousSlide = useCallback(() => {
    if (state.currentSlide > 0) {
      const newState = {
        ...state,
        currentSlide: state.currentSlide - 1
      };
      onStateChange(newState);
      setSlideStartTime(Date.now());
    }
  }, [state, onStateChange]);

  const goToSlide = useCallback((slideIndex: number) => {
    if (slideIndex >= 0 && slideIndex < state.slides.length) {
      const newState = {
        ...state,
        currentSlide: slideIndex
      };
      onStateChange(newState);
      setSlideStartTime(Date.now());
    }
  }, [state, onStateChange]);

  const togglePlayback = useCallback(() => {
    const newState = {
      ...state,
      isPlaying: !state.isPlaying
    };
    onStateChange(newState);
  }, [state, onStateChange]);

  // 渲染幻灯片内容
  const renderSlideContent = (slide: Slide) => {
    switch (slide.type) {
      case 'text':
        return (
          <div className="text-center space-y-8">
            <h1 className="text-6xl font-bold text-gray-800 dark:text-white mb-4">
              {slide.content.title}
            </h1>
            {slide.content.subtitle && (
              <h2 className="text-3xl text-gray-600 dark:text-gray-300 mb-8">
                {slide.content.subtitle}
              </h2>
            )}
            {slide.content.bullets && (
              <ul className="text-2xl space-y-4 text-left max-w-4xl mx-auto">
                {slide.content.bullets.map((bullet: string, index: number) => (
                  <li key={index} className="flex items-center space-x-4">
                    <div className="w-3 h-3 bg-blue-600 rounded-full flex-shrink-0" />
                    <span className="text-gray-700 dark:text-gray-300">{bullet}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        );

      case 'code':
        return (
          <div className="space-y-6">
            <h2 className="text-4xl font-bold text-center text-gray-800 dark:text-white mb-8">
              {slide.title}
            </h2>
            <div className="bg-gray-900 rounded-lg p-6 text-green-400 font-mono text-lg overflow-auto max-h-96">
              <pre className="whitespace-pre-wrap">{slide.content.code}</pre>
            </div>
            {slide.content.highlights && (
              <div className="space-y-2">
                {slide.content.highlights.map((highlight: any, index: number) => (
                  <div key={index} className={`p-3 rounded-lg ${
                    highlight.type === 'info' ? 'bg-blue-100 text-blue-800' :
                    highlight.type === 'success' ? 'bg-green-100 text-green-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    <span className="font-semibold">第 {highlight.line} 行:</span> {highlight.message}
                  </div>
                ))}
              </div>
            )}
          </div>
        );

      case 'interactive':
        return (
          <div className="space-y-8">
            <h2 className="text-4xl font-bold text-center text-gray-800 dark:text-white mb-8">
              {slide.title}
            </h2>
            <div className="grid grid-cols-2 gap-8">
              {slide.content.features.map((feature: any, index: number) => (
                <div 
                  key={index}
                  className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg hover:shadow-xl transition-shadow cursor-pointer"
                >
                  <div className="flex items-center space-x-4 mb-4">
                    {React.createElement(
                      feature.icon === 'Code' ? Code :
                      feature.icon === 'Users' ? Users :
                      feature.icon === 'Zap' ? Zap :
                      BarChart3,
                      { className: "w-8 h-8 text-blue-600" }
                    )}
                    <h3 className="text-2xl font-semibold text-gray-800 dark:text-white">
                      {feature.title}
                    </h3>
                  </div>
                  <p className="text-gray-600 dark:text-gray-300 text-lg">
                    {feature.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        );

      default:
        return (
          <div className="text-center">
            <h2 className="text-4xl font-bold text-gray-800 dark:text-white">
              {slide.title}
            </h2>
          </div>
        );
    }
  };

  const currentSlide = state.slides[state.currentSlide];

  return (
    <div className={`presentation-mode relative w-full h-full ${
      state.settings.theme === 'dark' ? 'bg-gray-900' : 'bg-white'
    } ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}>
      
      {/* 主幻灯片区域 */}
      <div 
        ref={slideRef}
        className="flex items-center justify-center h-full p-8"
        onClick={() => nextSlide()}
      >
        {currentSlide && (
          <div className={`w-full max-w-6xl transition-all duration-500 ${
            state.settings.transition === 'fade' ? 'animate-fade-in' :
            state.settings.transition === 'slide' ? 'animate-slide-in' :
            state.settings.transition === 'zoom' ? 'animate-zoom-in' :
            'animate-flip-in'
          }`}>
            {renderSlideContent(currentSlide)}
          </div>
        )}
      </div>

      {/* 控制栏 */}
      <div className={`absolute bottom-0 left-0 right-0 bg-black bg-opacity-75 text-white p-4 transition-opacity duration-300 ${
        showControls ? 'opacity-100' : 'opacity-0'
      }`}>
        <div className="flex items-center justify-between">
          {/* 播放控制 */}
          <div className="flex items-center space-x-4">
            <button
              onClick={togglePlayback}
              className="p-2 hover:bg-white hover:bg-opacity-20 rounded"
            >
              {state.isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6" />}
            </button>
            
            <button
              onClick={() => goToSlide(0)}
              className="p-2 hover:bg-white hover:bg-opacity-20 rounded"
            >
              <SkipBack className="w-6 h-6" />
            </button>
            
            <button
              onClick={previousSlide}
              disabled={state.currentSlide === 0}
              className="p-2 hover:bg-white hover:bg-opacity-20 rounded disabled:opacity-50"
            >
              <SkipBack className="w-5 h-5" />
            </button>
            
            <button
              onClick={nextSlide}
              disabled={state.currentSlide === state.slides.length - 1}
              className="p-2 hover:bg-white hover:bg-opacity-20 rounded disabled:opacity-50"
            >
              <SkipForward className="w-5 h-5" />
            </button>
          </div>

          {/* 幻灯片信息 */}
          <div className="flex items-center space-x-6">
            <span className="text-sm">
              {state.currentSlide + 1} / {state.slides.length}
            </span>
            
            <div className="flex items-center space-x-2">
              <Timer className="w-4 h-4" />
              <span className="text-sm">
                {Math.floor((Date.now() - slideStartTime) / 1000)}s
              </span>
            </div>
          </div>

          {/* 设置控制 */}
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setShowNotes(!showNotes)}
              className={`p-2 hover:bg-white hover:bg-opacity-20 rounded ${
                showNotes ? 'bg-white bg-opacity-20' : ''
              }`}
            >
              <FileText className="w-5 h-5" />
            </button>
            
            <button
              onClick={() => setIsMuted(!isMuted)}
              className="p-2 hover:bg-white hover:bg-opacity-20 rounded"
            >
              {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
            </button>
            
            <button className="p-2 hover:bg-white hover:bg-opacity-20 rounded">
              <Maximize className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* 进度条 */}
        <div className="mt-4">
          <div className="w-full bg-gray-600 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${((state.currentSlide + 1) / state.slides.length) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* 演讲者备注 */}
      {showNotes && currentSlide?.notes && (
        <div className="absolute top-4 right-4 w-80 bg-yellow-100 dark:bg-yellow-900 p-4 rounded-lg shadow-lg">
          <h4 className="font-semibold text-yellow-800 dark:text-yellow-200 mb-2">演讲者备注</h4>
          <p className="text-sm text-yellow-700 dark:text-yellow-300">{currentSlide.notes}</p>
        </div>
      )}

      {/* 幻灯片缩略图导航 */}
      <div className="absolute left-4 top-1/2 transform -translate-y-1/2 space-y-2">
        {state.slides.map((slide, index) => (
          <button
            key={slide.id}
            onClick={() => goToSlide(index)}
            className={`w-16 h-12 rounded border-2 transition-all ${
              index === state.currentSlide 
                ? 'border-blue-600 bg-blue-100' 
                : 'border-gray-300 bg-gray-100 hover:border-gray-400'
            }`}
            title={slide.title}
          >
            <div className="text-xs p-1 truncate">{index + 1}</div>
          </button>
        ))}
      </div>

      {/* 快捷键提示 */}
      <div className="absolute top-4 left-4 text-xs text-gray-500 bg-white bg-opacity-90 p-2 rounded">
        <div>→/Space: 下一张</div>
        <div>←: 上一张</div>
        <div>P: 播放/暂停</div>
        <div>N: 显示/隐藏备注</div>
      </div>
    </div>
  );
};

