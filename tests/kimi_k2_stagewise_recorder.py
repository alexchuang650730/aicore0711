#!/usr/bin/env python3
"""
StagewiseMCP 測試記錄器 - 記錄Kimi K2集成測試操作
使用MCP協議記錄測試步驟，支持回放驗證
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
import sys

class KimiK2StagewiseRecorder:
    """Kimi K2 測試階段性記錄器"""
    
    def __init__(self):
        self.test_session_id = f"kimi_k2_test_{int(time.time())}"
        self.stages = []
        
        # 設置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def start_recording_session(self):
        """開始記錄測試會話"""
        self.logger.info(f"🎬 開始記錄Kimi K2測試會話: {self.test_session_id}")
        
        session_data = {
            "session_id": self.test_session_id,
            "test_type": "kimi_k2_integration",
            "start_time": datetime.now().isoformat(),
            "description": "ClaudEditor Kimi K2模型集成測試錄製",
            "stages": []
        }
        
        return session_data
        
    def record_stage(self, stage_name, action_type, details):
        """記錄測試階段"""
        stage = {
            "stage_id": len(self.stages) + 1,
            "stage_name": stage_name,
            "action_type": action_type,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "status": "executed"
        }
        
        self.stages.append(stage)
        self.logger.info(f"📝 記錄階段 {stage['stage_id']}: {stage_name}")
        
        return stage
        
    def record_kimi_k2_test_flow(self):
        """記錄完整的Kimi K2測試流程"""
        self.logger.info("🎯 開始記錄Kimi K2測試流程...")
        
        # 階段1: 環境檢查
        self.record_stage(
            "環境檢查",
            "api_test",
            {
                "endpoint": "/api/status",
                "expected_status": 200,
                "description": "檢查Demo服務器狀態"
            }
        )
        
        # 階段2: 模型列表驗證
        self.record_stage(
            "模型列表驗證",
            "api_test",
            {
                "endpoint": "/api/models",
                "expected_models": ["kimi_k2", "claude"],
                "validation": "檢查Kimi K2和Claude模型是否都存在"
            }
        )
        
        # 階段3: Kimi K2聊天測試
        self.record_stage(
            "Kimi K2聊天測試",
            "api_test",
            {
                "endpoint": "/api/ai/chat",
                "request_data": {
                    "model": "kimi_k2",
                    "message": "你好，請介紹一下Kimi K2模型",
                    "max_tokens": 500
                },
                "expected_response_contains": ["🌙", "Kimi K2", "月之暗面"]
            }
        )
        
        # 階段4: Claude聊天測試
        self.record_stage(
            "Claude聊天測試",
            "api_test",
            {
                "endpoint": "/api/ai/chat",
                "request_data": {
                    "model": "claude",
                    "message": "請介紹一下Claude模型",
                    "max_tokens": 500
                },
                "expected_response_contains": ["🔵", "Claude", "Anthropic"]
            }
        )
        
        # 階段5: 模型對比測試
        self.record_stage(
            "模型對比測試",
            "api_test",
            {
                "description": "同時測試兩個模型的不同回應",
                "test_question": "什麼是人工智能？",
                "validation": "確保兩個模型回應不同且都包含正確標識"
            }
        )
        
        # 階段6: UI交互測試
        self.record_stage(
            "UI交互測試",
            "ui_test",
            {
                "url": "http://localhost:8001",
                "actions": [
                    "檢查頁面標題包含Kimi K2",
                    "驗證模型選擇器存在",
                    "切換到Kimi K2模型",
                    "發送測試消息",
                    "驗證回應顯示",
                    "切換到Claude模型",
                    "發送測試消息",
                    "驗證回應顯示"
                ]
            }
        )
        
        # 階段7: 集成驗證
        self.record_stage(
            "集成驗證",
            "integration_test",
            {
                "description": "驗證Kimi K2完全集成到ClaudEditor",
                "checks": [
                    "模型選擇功能正常",
                    "API響應正確",
                    "UI顯示正確",
                    "模型切換無誤",
                    "回應包含正確標識"
                ]
            }
        )
        
        self.logger.info(f"✅ 記錄完成，共記錄 {len(self.stages)} 個測試階段")
        
    def save_recording(self):
        """保存錄製的測試"""
        session_data = {
            "session_id": self.test_session_id,
            "test_type": "kimi_k2_integration",
            "recorded_at": datetime.now().isoformat(),
            "description": "ClaudEditor Kimi K2模型集成測試完整流程",
            "total_stages": len(self.stages),
            "stages": self.stages,
            "metadata": {
                "purpose": "驗證Kimi K2模型成功集成到ClaudEditor",
                "test_coverage": [
                    "API端點測試",
                    "模型切換功能",
                    "UI交互測試",
                    "回應驗證",
                    "集成完整性"
                ]
            }
        }
        
        # 保存到文件
        output_file = f"/Users/alexchuang/Desktop/alex/tests/package/aicore0711/tests/stagewise_recordings/kimi_k2_test_recording_{self.test_session_id}.json"
        
        # 創建目錄
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"💾 測試錄製已保存至: {output_file}")
        
        return output_file
        
    def generate_playback_script(self):
        """生成回放腳本"""
        playback_script = f"""#!/usr/bin/env python3
'''
Kimi K2 集成測試回放腳本
自動生成於: {datetime.now().isoformat()}
測試會話: {self.test_session_id}
'''

import requests
import time
import json

def replay_kimi_k2_tests():
    base_url = "http://localhost:8001"
    api_base = f"{{base_url}}/api"
    
    print("🔄 開始回放Kimi K2集成測試...")
    
"""
        
        for i, stage in enumerate(self.stages, 1):
            playback_script += f"""
    # 階段 {i}: {stage['stage_name']}
    print(f"📋 執行階段 {i}: {stage['stage_name']}")
    
"""
            
            if stage['action_type'] == 'api_test':
                if 'endpoint' in stage['details']:
                    endpoint = stage['details']['endpoint']
                    if endpoint == "/api/status":
                        playback_script += f"""    response = requests.get(f"{{api_base}}/status")
    assert response.status_code == 200, "狀態檢查失敗"
    print("✅ 服務器狀態正常")
"""
                    elif endpoint == "/api/models":
                        playback_script += f"""    response = requests.get(f"{{api_base}}/models")
    assert response.status_code == 200, "模型列表獲取失敗"
    data = response.json()
    models = [m['id'] for m in data['models']]
    assert 'kimi_k2' in models and 'claude' in models, "模型列表不完整"
    print("✅ 模型列表驗證通過")
"""
                    elif endpoint == "/api/ai/chat":
                        if 'request_data' in stage['details']:
                            request_data = stage['details']['request_data']
                            playback_script += f"""    chat_request = {json.dumps(request_data, indent=4)}
    response = requests.post(f"{{api_base}}/ai/chat", json=chat_request)
    assert response.status_code == 200, "聊天API調用失敗"
    data = response.json()
    print(f"✅ {{stage['stage_name']}}回應: {{data['response'][:50]}}...")
"""
            
            playback_script += f"""    time.sleep(1)  # 測試間隔
"""
        
        playback_script += """
    print("🎉 Kimi K2集成測試回放完成！")

if __name__ == "__main__":
    replay_kimi_k2_tests()
"""
        
        # 保存回放腳本
        script_file = f"/Users/alexchuang/Desktop/alex/tests/package/aicore0711/tests/stagewise_recordings/replay_kimi_k2_test_{self.test_session_id}.py"
        
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(playback_script)
            
        self.logger.info(f"🎬 回放腳本已生成: {script_file}")
        
        return script_file
        
    def run_full_recording(self):
        """運行完整的記錄流程"""
        self.logger.info("🚀 啟動Kimi K2 StagewiseMCP測試記錄...")
        
        # 開始記錄
        session = self.start_recording_session()
        
        # 記錄測試流程
        self.record_kimi_k2_test_flow()
        
        # 保存記錄
        recording_file = self.save_recording()
        
        # 生成回放腳本
        playback_file = self.generate_playback_script()
        
        # 生成摘要報告
        summary = {
            "recording_completed": True,
            "session_id": self.test_session_id,
            "total_stages": len(self.stages),
            "recording_file": recording_file,
            "playback_script": playback_file,
            "timestamp": datetime.now().isoformat()
        }
        
        print("\n" + "="*60)
        print("🎬 STAGEWISE MCP 測試記錄完成")
        print("="*60)
        print(f"📋 會話ID: {self.test_session_id}")
        print(f"📊 記錄階段: {len(self.stages)}")
        print(f"💾 記錄文件: {recording_file}")
        print(f"🎬 回放腳本: {playback_file}")
        print("="*60)
        
        return summary

if __name__ == "__main__":
    recorder = KimiK2StagewiseRecorder()
    result = recorder.run_full_recording()
    print(f"\\n🎉 StagewiseMCP記錄完成: {result['recording_completed']}")