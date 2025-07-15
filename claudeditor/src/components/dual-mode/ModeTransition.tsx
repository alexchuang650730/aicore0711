import React from 'react';
import { Edit3, Monitor } from 'lucide-react';

interface ModeTransitionProps {
  progress: number; // 0 to 1
  fromMode: 'edit' | 'presentation';
  toMode: 'edit' | 'presentation';
}

export const ModeTransition: React.FC<ModeTransitionProps> = ({
  progress,
  fromMode,
  toMode
}) => {
  const isEditToPresentation = fromMode === 'edit' && toMode === 'presentation';
  
  return (
    <div className="absolute inset-0 z-40 pointer-events-none">
      {/* 背景渐变覆盖层 */}
      <div 
        className="absolute inset-0 transition-all duration-500"
        style={{
          background: isEditToPresentation 
            ? `linear-gradient(45deg, 
                rgba(59, 130, 246, ${progress * 0.3}) 0%, 
                rgba(16, 185, 129, ${progress * 0.3}) 100%)`
            : `linear-gradient(45deg, 
                rgba(16, 185, 129, ${progress * 0.3}) 0%, 
                rgba(59, 130, 246, ${progress * 0.3}) 100%)`
        }}
      />

      {/* 中央转换动画 */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="relative">
          {/* 从模式图标 */}
          <div 
            className="absolute transition-all duration-500"
            style={{
              transform: `translateX(${-progress * 100}px) scale(${1 - progress * 0.5})`,
              opacity: 1 - progress
            }}
          >
            <div className="flex flex-col items-center space-y-4">
              {fromMode === 'edit' ? (
                <Edit3 className="w-16 h-16 text-blue-600" />
              ) : (
                <Monitor className="w-16 h-16 text-green-600" />
              )}
              <span className="text-lg font-medium text-gray-700">
                {fromMode === 'edit' ? '编辑模式' : '演示模式'}
              </span>
            </div>
          </div>

          {/* 到模式图标 */}
          <div 
            className="absolute transition-all duration-500"
            style={{
              transform: `translateX(${(1 - progress) * 100}px) scale(${0.5 + progress * 0.5})`,
              opacity: progress
            }}
          >
            <div className="flex flex-col items-center space-y-4">
              {toMode === 'edit' ? (
                <Edit3 className="w-16 h-16 text-blue-600" />
              ) : (
                <Monitor className="w-16 h-16 text-green-600" />
              )}
              <span className="text-lg font-medium text-gray-700">
                {toMode === 'edit' ? '编辑模式' : '演示模式'}
              </span>
            </div>
          </div>

          {/* 连接线动画 */}
          <div className="absolute top-8 left-1/2 transform -translate-x-1/2">
            <div 
              className="h-0.5 bg-gradient-to-r from-blue-600 to-green-600 transition-all duration-500"
              style={{
                width: `${progress * 200}px`,
                transform: 'translateX(-50%)'
              }}
            />
          </div>
        </div>
      </div>

      {/* 粒子效果 */}
      <div className="absolute inset-0 overflow-hidden">
        {Array.from({ length: 20 }).map((_, i) => (
          <div
            key={i}
            className="absolute w-2 h-2 bg-blue-400 rounded-full opacity-60"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              transform: `scale(${progress}) rotate(${progress * 360}deg)`,
              transition: 'all 0.5s ease-out',
              animationDelay: `${i * 0.1}s`
            }}
          />
        ))}
      </div>

      {/* 波纹效果 */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div 
          className="border-2 border-blue-400 rounded-full transition-all duration-500"
          style={{
            width: `${progress * 400}px`,
            height: `${progress * 400}px`,
            opacity: 1 - progress
          }}
        />
        <div 
          className="absolute border-2 border-green-400 rounded-full transition-all duration-500"
          style={{
            width: `${progress * 600}px`,
            height: `${progress * 600}px`,
            opacity: (1 - progress) * 0.5
          }}
        />
      </div>

      {/* 进度指示器 */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2">
        <div className="bg-white bg-opacity-90 rounded-full px-6 py-3 shadow-lg">
          <div className="flex items-center space-x-3">
            <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-blue-600 to-green-600 transition-all duration-100"
                style={{ width: `${progress * 100}%` }}
              />
            </div>
            <span className="text-sm font-medium text-gray-700">
              {Math.round(progress * 100)}%
            </span>
          </div>
        </div>
      </div>

      {/* 文字提示 */}
      <div className="absolute top-1/4 left-1/2 transform -translate-x-1/2">
        <div 
          className="text-center transition-all duration-500"
          style={{
            opacity: progress > 0.5 ? 1 : 0,
            transform: `translateY(${(1 - progress) * 20}px)`
          }}
        >
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            正在切换到{toMode === 'edit' ? '编辑' : '演示'}模式
          </h2>
          <p className="text-gray-600">
            {toMode === 'edit' 
              ? '准备代码编辑环境...' 
              : '准备演示界面...'}
          </p>
        </div>
      </div>
    </div>
  );
};

