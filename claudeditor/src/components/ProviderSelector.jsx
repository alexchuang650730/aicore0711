/**
 * ProviderSelector.jsx
 * ClaudeEditor中的AI Provider智能選擇器
 * 支持Kimi K2雙Provider切換和優化選擇
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Zap, 
  DollarSign, 
  Shield, 
  Activity, 
  TrendingUp, 
  AlertCircle,
  CheckCircle,
  Settings,
  BarChart3,
  RefreshCw
} from 'lucide-react';

const ProviderSelector = ({ onProviderChange, currentProvider = 'moonshot-official' }) => {
  const [selectedProvider, setSelectedProvider] = useState(currentProvider);
  const [autoOptimize, setAutoOptimize] = useState(true);
  const [providerStats, setProviderStats] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [optimization, setOptimization] = useState('balanced'); // 'cost', 'speed', 'stability', 'balanced'

  // Provider配置
  const providers = {
    'moonshot-official': {
      id: 'moonshot-v1-8k',
      name: 'Moonshot Official',
      description: '官方API - 穩定性最高',
      apiBase: 'https://api.moonshot.cn/v1',
      type: 'official',
      features: {
        stability: 95,
        speed: 80,
        cost: 70,
        qps: 60,
        reliability: 98
      },
      pros: [
        '官方支持，穩定性最高',
        '完整的SLA保障',
        '第一時間獲得新功能',
        '官方文檔支持'
      ],
      cons: [
        '成本相對較高',
        'QPS限制較嚴格',
        '可能有地域限制'
      ],
      pricing: {
        costPer1k: 0.0012,
        currency: 'USD',
        rateLimit: 60
      }
    },
    'infini-ai-cloud': {
      id: 'kimi-k2-instruct-infini',
      name: 'Infini-AI Cloud',
      description: '高QPS代理 - 成本優化',
      apiBase: 'https://cloud.infini-ai.com/maas/v1',
      type: 'proxy',
      features: {
        stability: 85,
        speed: 92,
        cost: 95,
        qps: 98,
        reliability: 88
      },
      pros: [
        '成本優勢明顯（便宜60%）',
        '高QPS支持（500/分鐘）',
        '可能有CDN優化',
        '響應速度更快'
      ],
      cons: [
        '第三方服務，穩定性依賴代理商',
        '新功能可能有延遲',
        '技術支持可能不如官方'
      ],
      pricing: {
        costPer1k: 0.0005,
        currency: 'USD',
        rateLimit: 500
      }
    }
  };

  const optimizationStrategies = {
    cost: {
      name: '成本優先',
      icon: DollarSign,
      description: '選擇最具成本效益的Provider',
      weight: { cost: 0.6, speed: 0.1, stability: 0.2, qps: 0.1 }
    },
    speed: {
      name: '速度優先',
      icon: Zap,
      description: '選擇響應最快的Provider',
      weight: { cost: 0.1, speed: 0.5, stability: 0.2, qps: 0.2 }
    },
    stability: {
      name: '穩定性優先',
      icon: Shield,
      description: '選擇最穩定可靠的Provider',
      weight: { cost: 0.1, speed: 0.1, stability: 0.6, qps: 0.2 }
    },
    qps: {
      name: 'QPS優先',
      icon: Activity,
      description: '選擇高并發能力的Provider',
      weight: { cost: 0.1, speed: 0.2, stability: 0.2, qps: 0.5 }
    },
    balanced: {
      name: '均衡模式',
      icon: BarChart3,
      description: '綜合考慮各項指標',
      weight: { cost: 0.25, speed: 0.25, stability: 0.25, qps: 0.25 }
    }
  };

  // 計算推薦Provider
  const getRecommendedProvider = () => {
    const strategy = optimizationStrategies[optimization];
    const scores = {};
    
    Object.entries(providers).forEach(([key, provider]) => {
      const features = provider.features;
      const score = 
        features.cost * strategy.weight.cost +
        features.speed * strategy.weight.speed +
        features.stability * strategy.weight.stability +
        features.qps * strategy.weight.qps;
      
      scores[key] = {
        ...provider,
        score: score.toFixed(1),
        isRecommended: false
      };
    });
    
    // 找出最高分
    const maxScore = Math.max(...Object.values(scores).map(s => parseFloat(s.score)));
    Object.keys(scores).forEach(key => {
      if (parseFloat(scores[key].score) === maxScore) {
        scores[key].isRecommended = true;
      }
    });
    
    return scores;
  };

  const recommendedProviders = getRecommendedProvider();

  // 處理Provider切換
  const handleProviderChange = (providerId) => {
    setIsLoading(true);
    setSelectedProvider(providerId);
    
    // 調用父組件的回調
    onProviderChange?.(providerId);
    
    // 模擬API調用
    setTimeout(() => {
      setIsLoading(false);
    }, 1000);
  };

  // 自動優化切換
  useEffect(() => {
    if (autoOptimize) {
      const recommended = Object.keys(recommendedProviders).find(
        key => recommendedProviders[key].isRecommended
      );
      if (recommended && recommended !== selectedProvider) {
        handleProviderChange(recommended);
      }
    }
  }, [optimization, autoOptimize]);

  // 渲染性能指標
  const renderPerformanceMetrics = (provider) => {
    const features = provider.features;
    return (
      <div className=\"grid grid-cols-2 gap-2 mt-3\">
        <div className=\"flex items-center gap-2 text-sm\">
          <Shield className=\"w-4 h-4 text-blue-500\" />
          <span>穩定性: {features.stability}%</span>
        </div>
        <div className=\"flex items-center gap-2 text-sm\">
          <Zap className=\"w-4 h-4 text-yellow-500\" />
          <span>速度: {features.speed}%</span>
        </div>
        <div className=\"flex items-center gap-2 text-sm\">
          <DollarSign className=\"w-4 h-4 text-green-500\" />
          <span>成本: {features.cost}%</span>
        </div>
        <div className=\"flex items-center gap-2 text-sm\">
          <Activity className=\"w-4 h-4 text-purple-500\" />
          <span>QPS: {features.qps}%</span>
        </div>
      </div>
    );
  };

  // 渲染Provider卡片
  const renderProviderCard = (key, provider) => {
    const isSelected = selectedProvider === key;
    const isRecommended = provider.isRecommended;
    
    return (
      <Card 
        key={key}
        className={`cursor-pointer transition-all duration-200 ${
          isSelected ? 'ring-2 ring-blue-500 bg-blue-50' : 'hover:shadow-md'
        }`}
        onClick={() => handleProviderChange(key)}
      >
        <CardHeader className=\"pb-3\">
          <div className=\"flex items-center justify-between\">
            <div className=\"flex items-center gap-2\">
              <CardTitle className=\"text-lg\">{provider.name}</CardTitle>
              {isRecommended && (
                <Badge variant=\"secondary\" className=\"bg-green-100 text-green-700\">
                  推薦
                </Badge>
              )}
              {isSelected && (
                <Badge variant=\"default\" className=\"bg-blue-100 text-blue-700\">
                  當前
                </Badge>
              )}
            </div>
            <div className=\"flex items-center gap-1\">
              {isSelected ? (
                <CheckCircle className=\"w-5 h-5 text-green-500\" />
              ) : (
                <div className=\"w-5 h-5 rounded-full border-2 border-gray-300\" />
              )}
            </div>
          </div>
          <p className=\"text-sm text-gray-600\">{provider.description}</p>
        </CardHeader>
        
        <CardContent>
          {/* 性能指標 */}
          {renderPerformanceMetrics(provider)}
          
          {/* 價格信息 */}
          <div className=\"mt-3 p-2 bg-gray-50 rounded-lg\">
            <div className=\"flex items-center justify-between text-sm\">
              <span>價格/1K tokens:</span>
              <span className=\"font-semibold\">${provider.pricing.costPer1k}</span>
            </div>
            <div className=\"flex items-center justify-between text-sm mt-1\">
              <span>速率限制:</span>
              <span className=\"font-semibold\">{provider.pricing.rateLimit}/分鐘</span>
            </div>
          </div>
          
          {/* 優缺點 */}
          <div className=\"mt-3 space-y-2\">
            <div>
              <h4 className=\"text-sm font-semibold text-green-700 mb-1\">優勢:</h4>
              <ul className=\"text-xs text-gray-600 space-y-1\">
                {provider.pros.slice(0, 2).map((pro, index) => (
                  <li key={index} className=\"flex items-start gap-1\">
                    <CheckCircle className=\"w-3 h-3 text-green-500 mt-0.5 flex-shrink-0\" />
                    <span>{pro}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          
          {/* 綜合評分 */}
          <div className=\"mt-3 pt-2 border-t\">
            <div className=\"flex items-center justify-between\">
              <span className=\"text-sm font-medium\">綜合評分:</span>
              <div className=\"flex items-center gap-2\">
                <div className=\"w-16 h-2 bg-gray-200 rounded-full overflow-hidden\">
                  <div 
                    className=\"h-full bg-blue-500 transition-all duration-300\"
                    style={{ width: `${provider.score}%` }}
                  />
                </div>
                <span className=\"text-sm font-semibold\">{provider.score}</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className=\"w-full max-w-4xl mx-auto p-4 space-y-6\">
      {/* 標題和控制 */}
      <div className=\"flex items-center justify-between\">
        <div>
          <h2 className=\"text-2xl font-bold text-gray-900\">AI Provider 智能選擇器</h2>
          <p className=\"text-gray-600 mt-1\">為您的Kimi K2使用場景選擇最佳Provider</p>
        </div>
        <div className=\"flex items-center gap-4\">
          <div className=\"flex items-center gap-2\">
            <span className=\"text-sm font-medium\">自動優化:</span>
            <Switch 
              checked={autoOptimize} 
              onCheckedChange={setAutoOptimize}
            />
          </div>
          <Button 
            variant=\"outline\" 
            size=\"sm\"
            onClick={() => window.location.reload()}
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            刷新
          </Button>
        </div>
      </div>

      <Tabs defaultValue=\"providers\" className=\"w-full\">
        <TabsList className=\"grid w-full grid-cols-3\">
          <TabsTrigger value=\"providers\">Provider選擇</TabsTrigger>
          <TabsTrigger value=\"optimization\">優化策略</TabsTrigger>
          <TabsTrigger value=\"comparison\">性能對比</TabsTrigger>
        </TabsList>

        {/* Provider選擇標籤 */}
        <TabsContent value=\"providers\" className=\"space-y-4\">
          <div className=\"grid md:grid-cols-2 gap-4\">
            {Object.entries(recommendedProviders).map(([key, provider]) => 
              renderProviderCard(key, provider)
            )}
          </div>
        </TabsContent>

        {/* 優化策略標籤 */}
        <TabsContent value=\"optimization\" className=\"space-y-4\">
          <Card>
            <CardHeader>
              <CardTitle>選擇優化策略</CardTitle>
              <p className=\"text-sm text-gray-600\">
                根據您的使用場景選擇最適合的優化策略
              </p>
            </CardHeader>
            <CardContent>
              <div className=\"grid md:grid-cols-2 lg:grid-cols-3 gap-4\">
                {Object.entries(optimizationStrategies).map(([key, strategy]) => {
                  const Icon = strategy.icon;
                  return (
                    <Card 
                      key={key}
                      className={`cursor-pointer transition-all duration-200 ${
                        optimization === key ? 'ring-2 ring-blue-500 bg-blue-50' : 'hover:shadow-md'
                      }`}
                      onClick={() => setOptimization(key)}
                    >
                      <CardContent className=\"p-4\">
                        <div className=\"flex items-center gap-3 mb-2\">
                          <Icon className=\"w-5 h-5 text-blue-500\" />
                          <h3 className=\"font-semibold\">{strategy.name}</h3>
                          {optimization === key && (
                            <CheckCircle className=\"w-4 h-4 text-green-500\" />
                          )}
                        </div>
                        <p className=\"text-sm text-gray-600\">{strategy.description}</p>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 性能對比標籤 */}
        <TabsContent value=\"comparison\" className=\"space-y-4\">
          <Card>
            <CardHeader>
              <CardTitle>Provider性能對比</CardTitle>
              <p className=\"text-sm text-gray-600\">
                詳細的性能指標和成本分析
              </p>
            </CardHeader>
            <CardContent>
              <div className=\"overflow-x-auto\">
                <table className=\"w-full border-collapse\">
                  <thead>
                    <tr className=\"border-b\">
                      <th className=\"text-left p-2\">Provider</th>
                      <th className=\"text-center p-2\">穩定性</th>
                      <th className=\"text-center p-2\">速度</th>
                      <th className=\"text-center p-2\">成本</th>
                      <th className=\"text-center p-2\">QPS</th>
                      <th className=\"text-center p-2\">價格</th>
                      <th className=\"text-center p-2\">推薦度</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(providers).map(([key, provider]) => (
                      <tr key={key} className=\"border-b\">
                        <td className=\"p-2\">
                          <div className=\"flex items-center gap-2\">
                            <span className=\"font-semibold\">{provider.name}</span>
                            {key === selectedProvider && (
                              <Badge variant=\"secondary\" size=\"sm\">當前</Badge>
                            )}
                          </div>
                        </td>
                        <td className=\"text-center p-2\">{provider.features.stability}%</td>
                        <td className=\"text-center p-2\">{provider.features.speed}%</td>
                        <td className=\"text-center p-2\">{provider.features.cost}%</td>
                        <td className=\"text-center p-2\">{provider.features.qps}%</td>
                        <td className=\"text-center p-2\">${provider.pricing.costPer1k}</td>
                        <td className=\"text-center p-2\">
                          <div className=\"flex items-center justify-center gap-1\">
                            <span>{recommendedProviders[key]?.score}</span>
                            {recommendedProviders[key]?.isRecommended && (
                              <TrendingUp className=\"w-4 h-4 text-green-500\" />
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* 當前選擇狀態 */}
      <Card>
        <CardContent className=\"p-4\">
          <div className=\"flex items-center justify-between\">
            <div className=\"flex items-center gap-3\">
              <div className=\"w-3 h-3 rounded-full bg-green-500\"></div>
              <span className=\"font-semibold\">
                當前Provider: {providers[selectedProvider]?.name}
              </span>
              <Badge variant=\"outline\" className=\"text-xs\">
                {providers[selectedProvider]?.type === 'official' ? '官方' : '代理'}
              </Badge>
            </div>
            <div className=\"flex items-center gap-2 text-sm text-gray-600\">
              <DollarSign className=\"w-4 h-4\" />
              <span>成本: ${providers[selectedProvider]?.pricing.costPer1k}/1K tokens</span>
              <Activity className=\"w-4 h-4 ml-2\" />
              <span>QPS: {providers[selectedProvider]?.pricing.rateLimit}/分鐘</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ProviderSelector;