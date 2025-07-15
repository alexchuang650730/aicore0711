/**
 * SmartUI 組件庫
 * 基於 AI-UI 的自適應智能組件系統
 */

import React, { useState, useEffect, createContext, useContext } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useMediaQuery } from 'react-responsive'
import { cn } from '@/lib/utils'

// SmartUI 上下文
const SmartUIContext = createContext({
  isMobile: false,
  isTablet: false,
  isDesktop: false,
  theme: 'light',
  adaptiveMode: 'auto',
})

// SmartUI Provider
export const SmartUIProvider = ({ children }) => {
  const isMobile = useMediaQuery({ maxWidth: 767 })
  const isTablet = useMediaQuery({ minWidth: 768, maxWidth: 1023 })
  const isDesktop = useMediaQuery({ minWidth: 1024 })
  const [theme, setTheme] = useState('light')
  const [adaptiveMode, setAdaptiveMode] = useState('auto')

  // 自動主題切換
  useEffect(() => {
    const hour = new Date().getHours()
    if (adaptiveMode === 'auto') {
      setTheme(hour >= 18 || hour <= 6 ? 'dark' : 'light')
    }
  }, [adaptiveMode])

  const value = {
    isMobile,
    isTablet,
    isDesktop,
    theme,
    setTheme,
    adaptiveMode,
    setAdaptiveMode,
  }

  return (
    <SmartUIContext.Provider value={value}>
      <div className={cn('smart-ui-root', theme)}>
        {children}
      </div>
    </SmartUIContext.Provider>
  )
}

// 使用 SmartUI 鉤子
export const useSmartUI = () => {
  const context = useContext(SmartUIContext)
  if (!context) {
    throw new Error('useSmartUI must be used within SmartUIProvider')
  }
  return context
}

// 智能容器組件
export const SmartContainer = ({ children, className, ...props }) => {
  const { isMobile, isTablet, isDesktop } = useSmartUI()
  
  return (
    <div 
      className={cn(
        'smart-container',
        {
          'px-4': isMobile,
          'px-6': isTablet,
          'px-8': isDesktop,
        },
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

// 智能卡片組件
export const SmartCard = ({ children, className, hover = true, ...props }) => {
  const { isMobile, theme } = useSmartUI()
  
  return (
    <motion.div
      className={cn(
        'smart-card',
        'bg-white rounded-lg shadow-sm border border-gray-200 p-4',
        {
          'p-3': isMobile,
          'p-6': !isMobile,
          'bg-gray-800 border-gray-700': theme === 'dark',
          'hover:shadow-md hover:scale-105 transition-all duration-200': hover,
        },
        className
      )}
      whileHover={hover ? { y: -2 } : {}}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      {...props}
    >
      {children}
    </motion.div>
  )
}

// 智能按鈕組件
export const SmartButton = ({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  loading = false,
  disabled = false,
  className,
  onClick,
  ...props 
}) => {
  const { isMobile, theme } = useSmartUI()
  
  const variants = {
    primary: 'bg-brand-600 hover:bg-brand-700 text-white',
    secondary: 'bg-gray-100 hover:bg-gray-200 text-gray-900',
    outline: 'border border-brand-600 text-brand-600 hover:bg-brand-50',
    ghost: 'text-brand-600 hover:bg-brand-50',
    danger: 'bg-red-600 hover:bg-red-700 text-white',
  }
  
  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  }
  
  const mobileSize = isMobile ? 'sm' : size
  
  return (
    <motion.button
      className={cn(
        'smart-button',
        'rounded-lg font-medium transition-all duration-200',
        'focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variants[variant],
        sizes[mobileSize],
        {
          'w-full': isMobile,
          'cursor-not-allowed': disabled || loading,
        },
        className
      )}
      disabled={disabled || loading}
      onClick={onClick}
      whileHover={!disabled && !loading ? { scale: 1.02 } : {}}
      whileTap={!disabled && !loading ? { scale: 0.98 } : {}}
      {...props}
    >
      {loading && (
        <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2 inline-block" />
      )}
      {children}
    </motion.button>
  )
}

// 智能輸入框組件
export const SmartInput = ({ 
  label, 
  error, 
  helper, 
  className,
  ...props 
}) => {
  const { isMobile, theme } = useSmartUI()
  
  return (
    <div className="smart-input-group">
      {label && (
        <label className={cn(
          'block text-sm font-medium mb-1',
          theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
        )}>
          {label}
        </label>
      )}
      <input
        className={cn(
          'smart-input',
          'w-full px-3 py-2 border border-gray-300 rounded-lg',
          'focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent',
          'transition-all duration-200',
          {
            'px-4 py-3': isMobile,
            'border-red-500 focus:ring-red-500': error,
            'bg-gray-800 border-gray-600 text-white': theme === 'dark',
          },
          className
        )}
        {...props}
      />
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
      {helper && !error && (
        <p className="mt-1 text-sm text-gray-500">{helper}</p>
      )}
    </div>
  )
}

// 智能網格組件
export const SmartGrid = ({ children, columns = 'auto', gap = 4, className, ...props }) => {
  const { isMobile, isTablet, isDesktop } = useSmartUI()
  
  const getColumns = () => {
    if (columns === 'auto') {
      if (isMobile) return 1
      if (isTablet) return 2
      return 3
    }
    return columns
  }
  
  return (
    <div
      className={cn(
        'smart-grid',
        `grid grid-cols-${getColumns()} gap-${gap}`,
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

// 智能模態框組件
export const SmartModal = ({ 
  open, 
  onClose, 
  title, 
  children, 
  footer,
  size = 'md',
  className 
}) => {
  const { isMobile } = useSmartUI()
  
  const sizes = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    full: 'max-w-full',
  }
  
  const modalSize = isMobile ? 'full' : size
  
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          {/* 背景遮罩 */}
          <motion.div
            className="absolute inset-0 bg-black bg-opacity-50 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          
          {/* 模態框內容 */}
          <motion.div
            className={cn(
              'smart-modal',
              'relative bg-white rounded-lg shadow-xl',
              'w-full max-h-[90vh] overflow-auto',
              {
                'h-full rounded-none': isMobile,
                'max-h-[80vh]': !isMobile,
              },
              sizes[modalSize],
              className
            )}
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          >
            {/* 標題 */}
            {title && (
              <div className="flex items-center justify-between p-6 border-b">
                <h2 className="text-xl font-semibold">{title}</h2>
                <button
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            )}
            
            {/* 內容 */}
            <div className="p-6">
              {children}
            </div>
            
            {/* 底部 */}
            {footer && (
              <div className="flex justify-end gap-3 p-6 border-t bg-gray-50">
                {footer}
              </div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

// 智能加載組件
export const SmartLoader = ({ size = 'md', className }) => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  }
  
  return (
    <div className={cn('smart-loader flex items-center justify-center', className)}>
      <div className={cn(
        'border-2 border-brand-200 border-t-brand-600 rounded-full animate-spin',
        sizes[size]
      )} />
    </div>
  )
}

// 智能通知組件
export const SmartToast = ({ 
  message, 
  type = 'info', 
  duration = 3000,
  onClose 
}) => {
  const [visible, setVisible] = useState(true)
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false)
      onClose?.()
    }, duration)
    
    return () => clearTimeout(timer)
  }, [duration, onClose])
  
  const types = {
    info: 'bg-blue-50 border-blue-200 text-blue-800',
    success: 'bg-green-50 border-green-200 text-green-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    error: 'bg-red-50 border-red-200 text-red-800',
  }
  
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          className={cn(
            'smart-toast',
            'fixed top-4 right-4 z-50 p-4 rounded-lg border shadow-lg',
            types[type]
          )}
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -50 }}
        >
          <p className="font-medium">{message}</p>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

// 智能導航組件
export const SmartNavigation = ({ items, className }) => {
  const { isMobile } = useSmartUI()
  const [activeItem, setActiveItem] = useState(items[0]?.id)
  
  if (isMobile) {
    return (
      <div className={cn('smart-navigation-mobile', 'fixed bottom-0 left-0 right-0 bg-white border-t', className)}>
        <div className="flex justify-around py-2">
          {items.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveItem(item.id)}
              className={cn(
                'flex flex-col items-center p-2 rounded-lg transition-colors',
                activeItem === item.id
                  ? 'text-brand-600 bg-brand-50'
                  : 'text-gray-600 hover:text-gray-800'
              )}
            >
              {item.icon}
              <span className="text-xs mt-1">{item.label}</span>
            </button>
          ))}
        </div>
      </div>
    )
  }
  
  return (
    <nav className={cn('smart-navigation', 'space-y-2', className)}>
      {items.map((item) => (
        <button
          key={item.id}
          onClick={() => setActiveItem(item.id)}
          className={cn(
            'w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
            activeItem === item.id
              ? 'bg-brand-50 text-brand-600 border-r-2 border-brand-600'
              : 'text-gray-600 hover:bg-gray-50'
          )}
        >
          {item.icon}
          <span className="font-medium">{item.label}</span>
        </button>
      ))}
    </nav>
  )
}

// 智能響應式圖片組件
export const SmartImage = ({ src, alt, aspectRatio = '16/9', className, ...props }) => {
  const { isMobile } = useSmartUI()
  
  return (
    <div 
      className={cn(
        'smart-image',
        'relative overflow-hidden rounded-lg',
        {
          'aspect-square': isMobile,
          [`aspect-[${aspectRatio}]`]: !isMobile,
        },
        className
      )}
    >
      <img
        src={src}
        alt={alt}
        className="absolute inset-0 w-full h-full object-cover"
        {...props}
      />
    </div>
  )
}

// 智能分頁組件
export const SmartPagination = ({ 
  currentPage, 
  totalPages, 
  onPageChange,
  className 
}) => {
  const { isMobile } = useSmartUI()
  
  if (isMobile) {
    return (
      <div className={cn('smart-pagination-mobile', 'flex justify-between items-center', className)}>
        <SmartButton
          variant="outline"
          size="sm"
          disabled={currentPage === 1}
          onClick={() => onPageChange(currentPage - 1)}
        >
          上一頁
        </SmartButton>
        <span className="text-sm text-gray-600">
          {currentPage} / {totalPages}
        </span>
        <SmartButton
          variant="outline"
          size="sm"
          disabled={currentPage === totalPages}
          onClick={() => onPageChange(currentPage + 1)}
        >
          下一頁
        </SmartButton>
      </div>
    )
  }
  
  const getPageNumbers = () => {
    const delta = 2
    const range = []
    const rangeWithDots = []
    
    for (let i = Math.max(2, currentPage - delta); i <= Math.min(totalPages - 1, currentPage + delta); i++) {
      range.push(i)
    }
    
    if (currentPage - delta > 2) {
      rangeWithDots.push(1, '...')
    } else {
      rangeWithDots.push(1)
    }
    
    rangeWithDots.push(...range)
    
    if (currentPage + delta < totalPages - 1) {
      rangeWithDots.push('...', totalPages)
    } else {
      rangeWithDots.push(totalPages)
    }
    
    return rangeWithDots
  }
  
  return (
    <div className={cn('smart-pagination', 'flex items-center justify-center gap-2', className)}>
      {getPageNumbers().map((page, index) => (
        <button
          key={index}
          onClick={() => typeof page === 'number' && onPageChange(page)}
          disabled={page === '...'}
          className={cn(
            'w-10 h-10 rounded-lg transition-colors',
            page === currentPage
              ? 'bg-brand-600 text-white'
              : 'text-gray-600 hover:bg-gray-100',
            page === '...' && 'cursor-default'
          )}
        >
          {page}
        </button>
      ))}
    </div>
  )
}