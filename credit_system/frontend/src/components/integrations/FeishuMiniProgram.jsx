/**
 * 飛書小程序集成組件
 * 提供飛書內購買入口和流程
 */

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  SmartContainer, 
  SmartCard, 
  SmartButton, 
  SmartModal,
  SmartLoader,
  useSmartUI 
} from '@/components/ui/smart-ui'
import { 
  MessageSquare, 
  Users, 
  Crown, 
  Building, 
  CreditCard, 
  Check,
  ArrowRight,
  ExternalLink,
  Zap,
  Shield,
  Sparkles
} from 'lucide-react'

const FeishuMiniProgram = () => {
  const { isMobile } = useSmartUI()
  const [showPurchaseModal, setShowPurchaseModal] = useState(false)
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [loading, setLoading] = useState(false)
  const [feishuSupported, setFeishuSupported] = useState(false)

  // 檢測飛書環境
  useEffect(() => {
    const checkFeishuEnvironment = () => {
      // 檢查是否在飛書環境中
      const isFeishu = window.h5sdk || window.tt || navigator.userAgent.includes('Feishu')
      setFeishuSupported(isFeishu)
    }

    checkFeishuEnvironment()
  }, [])

  // 飛書購買方案
  const feishuPlans = [
    {
      id: 'personal',
      name: '個人版',
      price: 100,
      currency: 'credits',
      originalPrice: 120,
      icon: <Crown className="w-6 h-6" />,
      color: 'bg-blue-500',
      features: [
        '完整AI功能',
        '高級編輯器',
        '無限K2調用',
        '優先支持',
        '移動端優化',
        '飛書深度集成'
      ],
      popular: true,
      feishuBenefits: [
        '飛書日曆智能提醒',
        '飛書文檔同步編輯',
        '飛書會議記錄自動化',
        '飛書通訊錄集成'
      ]
    },
    {
      id: 'team',
      name: '團隊版',
      price: 300,
      currency: 'credits',
      originalPrice: 400,
      icon: <Users className="w-6 h-6" />,
      color: 'bg-green-500',
      features: [
        '個人版全部功能',
        '團隊協作工具',
        '項目管理',
        '代碼審查',
        '版本控制',
        '團隊分析'
      ],
      teamSize: '最多10人',
      feishuBenefits: [
        '飛書群組智能管理',
        '飛書審批流程自動化',
        '飛書OKR追蹤',
        '飛書BI報表集成'
      ]
    },
    {
      id: 'enterprise',
      name: '企業版',
      price: 800,
      currency: 'credits',
      originalPrice: 1200,
      icon: <Building className="w-6 h-6" />,
      color: 'bg-purple-500',
      features: [
        '團隊版全部功能',
        '企業級支持',
        '自定義集成',
        '專屬服務器',
        'SLA保障',
        '技術培訓'
      ],
      teamSize: '無限人數',
      feishuBenefits: [
        '飛書企業級SSO',
        '飛書多維表格集成',
        '飛書自定義機器人',
        '飛書開放平台API'
      ]
    }
  ]

  // 打開飛書購買鏈接
  const openFeishuPurchaseLink = () => {
    const feishuLink = 'https://applink.feishu.cn/client/message/link/open?token=AmfoKtFagQATaHK7JJIAQAI%3D'
    
    if (feishuSupported) {
      // 在飛書環境中打開
      window.location.href = feishuLink
    } else {
      // 在外部瀏覽器中打開
      window.open(feishuLink, '_blank')
    }
  }

  // 處理購買
  const handlePurchase = async (plan) => {
    setLoading(true)
    setSelectedPlan(plan)
    
    try {
      // 模擬購買API調用
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      // 在飛書環境中，調用飛書支付API
      if (feishuSupported) {
        // 飛書支付邏輯
        await handleFeishuPayment(plan)
      } else {
        // 普通購買流程
        setShowPurchaseModal(true)
      }
    } catch (error) {
      console.error('Purchase failed:', error)
    } finally {
      setLoading(false)
    }
  }

  // 飛書支付處理
  const handleFeishuPayment = async (plan) => {
    try {
      // 調用飛書支付API
      const paymentData = {
        app_id: 'your-feishu-app-id',
        user_id: 'current-user-id',
        order_id: `feishu-${Date.now()}`,
        amount: plan.price,
        currency: plan.currency,
        product_name: `PowerAutomation ${plan.name}`,
        product_description: `PowerAutomation ${plan.name} - 飛書專屬版本`,
        callback_url: `${window.location.origin}/api/payments/feishu/callback`
      }

      // 這裡會調用實際的飛書支付API
      console.log('Feishu payment data:', paymentData)
      
      // 跳轉到飛書支付頁面
      openFeishuPurchaseLink()
    } catch (error) {
      console.error('Feishu payment failed:', error)
    }
  }

  return (
    <SmartContainer className="py-12">
      {/* 飛書集成標題 */}
      <motion.div 
        className="text-center mb-12"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div className="flex items-center justify-center gap-3 mb-4">
          <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <MessageSquare className="w-6 h-6 text-white" />
          </div>
          <div className="text-left">
            <h1 className="text-3xl font-bold text-gray-900">飛書專屬版本</h1>
            <p className="text-gray-600">深度集成飛書生態，提升團隊協作效率</p>
          </div>
        </div>
        
        {feishuSupported && (
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-50 border border-green-200 rounded-lg text-green-700">
            <Check className="w-4 h-4" />
            <span className="text-sm font-medium">已檢測到飛書環境</span>
          </div>
        )}
      </motion.div>

      {/* 飛書特色功能 */}
      <motion.div 
        className="mb-12"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        <SmartCard className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">🚀 飛書深度集成特性</h2>
            <p className="text-gray-600">專為飛書用戶打造的增強功能</p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              {
                icon: <Zap className="w-6 h-6 text-yellow-500" />,
                title: '一鍵啟動',
                description: '從飛書直接啟動PowerAutomation'
              },
              {
                icon: <Users className="w-6 h-6 text-blue-500" />,
                title: '團隊協作',
                description: '與飛書群組無縫協作'
              },
              {
                icon: <Shield className="w-6 h-6 text-green-500" />,
                title: '企業安全',
                description: '符合企業級安全標準'
              },
              {
                icon: <Sparkles className="w-6 h-6 text-purple-500" />,
                title: 'AI增強',
                description: '飛書智能助手深度集成'
              }
            ].map((feature, index) => (
              <div key={index} className="text-center p-4 bg-white rounded-lg shadow-sm">
                <div className="flex justify-center mb-3">
                  {feature.icon}
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-sm text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </SmartCard>
      </motion.div>

      {/* 飛書購買方案 */}
      <motion.div 
        className="mb-12"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
      >
        <h2 className="text-2xl font-bold text-center mb-8">選擇適合的飛書版本</h2>
        
        <div className="grid md:grid-cols-3 gap-6">
          {feishuPlans.map((plan, index) => (
            <motion.div
              key={plan.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 * index }}
            >
              <SmartCard className={`relative ${plan.popular ? 'ring-2 ring-blue-500' : ''}`}>
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <span className="bg-blue-500 text-white px-3 py-1 rounded-full text-sm font-medium">
                      最受歡迎
                    </span>
                  </div>
                )}
                
                <div className="text-center mb-6">
                  <div className={`inline-flex items-center justify-center w-12 h-12 rounded-lg ${plan.color} mb-4`}>
                    {React.cloneElement(plan.icon, { className: "w-6 h-6 text-white" })}
                  </div>
                  
                  <h3 className="text-xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                  
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <span className="text-3xl font-bold text-gray-900">{plan.price}</span>
                    <span className="text-gray-600">積分</span>
                    {plan.originalPrice && (
                      <span className="text-sm text-gray-500 line-through ml-2">
                        {plan.originalPrice}積分
                      </span>
                    )}
                  </div>
                  
                  {plan.teamSize && (
                    <p className="text-sm text-gray-600">{plan.teamSize}</p>
                  )}
                </div>
                
                {/* 基礎功能 */}
                <div className="mb-6">
                  <h4 className="font-semibold text-gray-900 mb-3">基礎功能</h4>
                  <ul className="space-y-2">
                    {plan.features.map((feature, featureIndex) => (
                      <li key={featureIndex} className="flex items-center gap-2">
                        <Check className="w-4 h-4 text-green-500 flex-shrink-0" />
                        <span className="text-sm text-gray-600">{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                
                {/* 飛書專屬功能 */}
                <div className="mb-6">
                  <h4 className="font-semibold text-gray-900 mb-3">飛書專屬功能</h4>
                  <ul className="space-y-2">
                    {plan.feishuBenefits.map((benefit, benefitIndex) => (
                      <li key={benefitIndex} className="flex items-center gap-2">
                        <MessageSquare className="w-4 h-4 text-blue-500 flex-shrink-0" />
                        <span className="text-sm text-gray-600">{benefit}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                
                <SmartButton
                  className="w-full"
                  variant={plan.popular ? "primary" : "outline"}
                  onClick={() => handlePurchase(plan)}
                  loading={loading && selectedPlan?.id === plan.id}
                >
                  {feishuSupported ? '飛書內購買' : '立即購買'}
                  <ArrowRight className="w-4 h-4 ml-2" />
                </SmartButton>
              </SmartCard>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* 飛書快速入口 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.6 }}
      >
        <SmartCard className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-4">🎯 飛書專屬入口</h2>
            <p className="text-blue-100 mb-6">
              通過飛書官方鏈接，享受更便捷的購買體驗
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <SmartButton
                variant="secondary"
                onClick={openFeishuPurchaseLink}
                className="bg-white text-blue-600 hover:bg-blue-50"
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                打開飛書購買鏈接
              </SmartButton>
              
              <SmartButton
                variant="outline"
                className="border-white text-white hover:bg-white hover:text-blue-600"
                onClick={() => setShowPurchaseModal(true)}
              >
                <CreditCard className="w-4 h-4 mr-2" />
                其他支付方式
              </SmartButton>
            </div>
          </div>
        </SmartCard>
      </motion.div>

      {/* 購買模態框 */}
      <SmartModal
        open={showPurchaseModal}
        onClose={() => setShowPurchaseModal(false)}
        title="完成購買"
        size="lg"
      >
        <div className="space-y-6">
          {selectedPlan && (
            <div className="text-center">
              <h3 className="text-lg font-semibold mb-2">
                {selectedPlan.name} - {selectedPlan.price}積分
              </h3>
              <p className="text-gray-600">
                {feishuSupported ? '飛書專屬版本' : '標準版本'}
              </p>
            </div>
          )}
          
          <div className="grid grid-cols-2 gap-4">
            <SmartButton variant="outline" onClick={() => setShowPurchaseModal(false)}>
              取消
            </SmartButton>
            <SmartButton onClick={() => {
              // 處理實際購買邏輯
              setShowPurchaseModal(false)
            }}>
              確認購買
            </SmartButton>
          </div>
        </div>
      </SmartModal>
    </SmartContainer>
  )
}

export default FeishuMiniProgram