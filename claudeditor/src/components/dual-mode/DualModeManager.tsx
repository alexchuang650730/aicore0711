import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Monitor, Edit3, Play, Pause, RotateCcw, Settings, Maximize2, Minimize2 } from 'lucide-react';
import { useEditorStore } from '../../stores/editorStore';
import { EditMode } from './EditMode';
import { PresentationMode } from './PresentationMode';
import { ModeTransition } from './ModeTransition';

export type EditorMode = 'edit' | 'presentation';

interface DualModeManagerProps {
  className?: string;
  onModeChange?: (mode: EditorMode) => void;
}

export const DualModeManager: React.FC<DualModeManagerProps> = ({
  className = '',
  onModeChange
}) => {
  const {
    mode,
    switchMode,
    editState,
    presentationState,
    saveEditState,
    savePresentationState,
    restoreEditState,
    restorePresentationState
  } = useEditorStore();

  const [isTransitioning, setIsTransitioning] = useState(false);
  const [transitionProgress, setTransitionProgress] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // 模式切换处理
  const handleModeSwitch = useCallback(async (newMode: EditorMode) => {
    if (mode === newMode || isTransitioning) return;

    setIsTransitioning(true);
    setTransitionProgress(0);

    try {
      // 保存当前模式状态
      if (mode === 'edit') {
        await saveEditState();
      } else {
        await savePresentationState();
      }

      // 执行渐进式转换动画
      const transitionDuration = 500; // 500ms
      const steps = 20;
      const stepDuration = transitionDuration / steps;

      for (let i = 0; i <= steps; i++) {
        setTransitionProgress(i / steps);
        await new Promise(resolve => setTimeout(resolve, stepDuration));
      }

      // 切换模式
      switchMode(newMode);

      // 恢复新模式状态
      if (newMode === 'edit') {
        await restoreEditState();
      } else {
        await restorePresentationState();
      }

      // 通知父组件
      onModeChange?.(newMode);

    } catch (error) {
      console.error('模式切换失败:', error);
    } finally {
      setIsTransitioning(false);
      setTransitionProgress(0);
    }
  }, [mode, isTransitioning, switchMode, saveEditState, savePresentationState, restoreEditState, restorePresentationState, onModeChange]);

  // 快捷键处理
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ctrl/Cmd + Shift + M: 切换模式
      if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'M') {
        event.preventDefault();
        const newMode = mode === 'edit' ? 'presentation' : 'edit';
        handleModeSwitch(newMode);
      }

      // F11: 全屏切换
      if (event.key === 'F11') {
        event.preventDefault();
        toggleFullscreen();
      }

      // Esc: 退出演示模式
      if (event.key === 'Escape' && mode === 'presentation') {
        handleModeSwitch('edit');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [mode, handleModeSwitch]);

  // 全屏切换
  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  }, []);

  // 监听全屏状态变化
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  return (
    <div 
      ref={containerRef}
      className={`dual-mode-manager relative w-full h-full bg-gray-50 dark:bg-gray-900 ${className}`}
    >
      {/* 模式切换工具栏 */}
      <div className="absolute top-4 right-4 z-50 flex items-center gap-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-2">
        {/* 模式指示器 */}
        <div className="flex items-center gap-2 px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-md">
          {mode === 'edit' ? (
            <Edit3 className="w-4 h-4 text-blue-600" />
          ) : (
            <Monitor className="w-4 h-4 text-green-600" />
          )}
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {mode === 'edit' ? '编辑模式' : '演示模式'}
          </span>
        </div>

        {/* 模式切换按钮 */}
        <button
          onClick={() => handleModeSwitch(mode === 'edit' ? 'presentation' : 'edit')}
          disabled={isTransitioning}
          className="flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-md transition-colors"
          title={`切换到${mode === 'edit' ? '演示' : '编辑'}模式 (Ctrl+Shift+M)`}
        >
          {mode === 'edit' ? (
            <>
              <Play className="w-4 h-4" />
              <span className="text-sm">演示</span>
            </>
          ) : (
            <>
              <Edit3 className="w-4 h-4" />
              <span className="text-sm">编辑</span>
            </>
          )}
        </button>

        {/* 全屏按钮 */}
        <button
          onClick={toggleFullscreen}
          className="p-2 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
          title="全屏 (F11)"
        >
          {isFullscreen ? (
            <Minimize2 className="w-4 h-4" />
          ) : (
            <Maximize2 className="w-4 h-4" />
          )}
        </button>

        {/* 设置按钮 */}
        <button
          className="p-2 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
          title="设置"
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>

      {/* 转换动画覆盖层 */}
      {isTransitioning && (
        <ModeTransition
          progress={transitionProgress}
          fromMode={mode}
          toMode={mode === 'edit' ? 'presentation' : 'edit'}
        />
      )}

      {/* 主要内容区域 */}
      <div className="w-full h-full">
        {mode === 'edit' ? (
          <EditMode
            isActive={!isTransitioning}
            state={editState}
            onStateChange={saveEditState}
          />
        ) : (
          <PresentationMode
            isActive={!isTransitioning}
            state={presentationState}
            onStateChange={savePresentationState}
            isFullscreen={isFullscreen}
          />
        )}
      </div>

      {/* 状态指示器 */}
      {isTransitioning && (
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 flex items-center gap-3">
            <div className="animate-spin">
              <RotateCcw className="w-5 h-5 text-blue-600" />
            </div>
            <span className="text-sm text-gray-700 dark:text-gray-300">
              正在切换到{mode === 'edit' ? '演示' : '编辑'}模式...
            </span>
            <div className="w-32 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div 
                className="h-full bg-blue-600 transition-all duration-100"
                style={{ width: `${transitionProgress * 100}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* 快捷键提示 */}
      <div className="absolute bottom-4 right-4 z-40 text-xs text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-800 rounded-md p-2 shadow-sm">
        <div>Ctrl+Shift+M: 切换模式</div>
        <div>F11: 全屏</div>
        <div>Esc: 退出演示</div>
      </div>
    </div>
  );
};

