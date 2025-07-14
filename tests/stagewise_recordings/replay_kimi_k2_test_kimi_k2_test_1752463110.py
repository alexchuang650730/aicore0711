#!/usr/bin/env python3
'''
Kimi K2 集成測試回放腳本
自動生成於: 2025-07-14T11:18:30.848360
測試會話: kimi_k2_test_1752463110
'''

import requests
import time
import json

def replay_kimi_k2_tests():
    base_url = "http://localhost:8001"
    api_base = f"{base_url}/api"
    
    print("🔄 開始回放Kimi K2集成測試...")
    

    # 階段 1: 環境檢查
    print(f"📋 執行階段 1: 環境檢查")
    
    response = requests.get(f"{api_base}/status")
    assert response.status_code == 200, "狀態檢查失敗"
    print("✅ 服務器狀態正常")
    time.sleep(1)  # 測試間隔

    # 階段 2: 模型列表驗證
    print(f"📋 執行階段 2: 模型列表驗證")
    
    response = requests.get(f"{api_base}/models")
    assert response.status_code == 200, "模型列表獲取失敗"
    data = response.json()
    models = [m['id'] for m in data['models']]
    assert 'kimi_k2' in models and 'claude' in models, "模型列表不完整"
    print("✅ 模型列表驗證通過")
    time.sleep(1)  # 測試間隔

    # 階段 3: Kimi K2聊天測試
    print(f"📋 執行階段 3: Kimi K2聊天測試")
    
    chat_request = {
    "model": "kimi_k2",
    "message": "\u4f60\u597d\uff0c\u8acb\u4ecb\u7d39\u4e00\u4e0bKimi K2\u6a21\u578b",
    "max_tokens": 500
}
    response = requests.post(f"{api_base}/ai/chat", json=chat_request)
    assert response.status_code == 200, "聊天API調用失敗"
    data = response.json()
    print(f"✅ {stage['stage_name']}回應: {data['response'][:50]}...")
    time.sleep(1)  # 測試間隔

    # 階段 4: Claude聊天測試
    print(f"📋 執行階段 4: Claude聊天測試")
    
    chat_request = {
    "model": "claude",
    "message": "\u8acb\u4ecb\u7d39\u4e00\u4e0bClaude\u6a21\u578b",
    "max_tokens": 500
}
    response = requests.post(f"{api_base}/ai/chat", json=chat_request)
    assert response.status_code == 200, "聊天API調用失敗"
    data = response.json()
    print(f"✅ {stage['stage_name']}回應: {data['response'][:50]}...")
    time.sleep(1)  # 測試間隔

    # 階段 5: 模型對比測試
    print(f"📋 執行階段 5: 模型對比測試")
    
    time.sleep(1)  # 測試間隔

    # 階段 6: UI交互測試
    print(f"📋 執行階段 6: UI交互測試")
    
    time.sleep(1)  # 測試間隔

    # 階段 7: 集成驗證
    print(f"📋 執行階段 7: 集成驗證")
    
    time.sleep(1)  # 測試間隔

    print("🎉 Kimi K2集成測試回放完成！")

if __name__ == "__main__":
    replay_kimi_k2_tests()
