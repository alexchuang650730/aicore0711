"""
Claude Code Router MCP - 工具函數
路由器系統的通用工具函數
"""

import json
import hashlib
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)


class RouterUtils:
    """路由器工具類"""
    
    @staticmethod
    def generate_request_id() -> str:
        """生成唯一請求ID"""
        timestamp = str(int(time.time() * 1000))
        random_part = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        return f"req_{timestamp}_{random_part}"
    
    @staticmethod
    def calculate_token_count(text: str, model_type: str = "gpt") -> int:
        """估算token數量"""
        if model_type in ["gpt", "claude"]:
            # 粗略估算：英文約4字符=1token，中文約1.5字符=1token
            chinese_chars = sum(1 for c in text if ord(c) > 127)
            english_chars = len(text) - chinese_chars
            return int(english_chars / 4 + chinese_chars / 1.5)
        else:
            # 其他模型使用通用估算
            return len(text.split())
    
    @staticmethod
    def format_response_time(seconds: float) -> str:
        """格式化響應時間"""
        if seconds < 1:
            return f"{seconds * 1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.2f}s"
        else:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}m{remaining_seconds:.0f}s"
    
    @staticmethod
    def format_cost(cost: float) -> str:
        """格式化成本"""
        if cost < 0.01:
            return f"${cost:.4f}"
        elif cost < 1:
            return f"${cost:.3f}"
        else:
            return f"${cost:.2f}"
    
    @staticmethod
    def sanitize_model_name(model_name: str) -> str:
        """清理模型名稱"""
        # 移除特殊字符，只保留字母、數字、連字符和點
        import re
        return re.sub(r'[^a-zA-Z0-9\-\.]', '', model_name)
    
    @staticmethod
    def parse_model_capabilities(model_id: str) -> Dict[str, bool]:
        """解析模型能力"""
        capabilities = {
            "supports_vision": False,
            "supports_function_calling": False,
            "supports_streaming": True,
            "supports_json_mode": False
        }
        
        # 基於模型ID判斷能力
        if "vision" in model_id.lower() or "gpt-4" in model_id or "claude-3" in model_id:
            capabilities["supports_vision"] = True
        
        if "gpt-4" in model_id or "claude-3" in model_id or "gemini" in model_id:
            capabilities["supports_function_calling"] = True
        
        if "gpt" in model_id or "claude" in model_id:
            capabilities["supports_json_mode"] = True
        
        return capabilities
    
    @staticmethod
    def validate_request_format(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證請求格式"""
        errors = []
        warnings = []
        
        # 檢查必需字段
        required_fields = ["model", "messages"]
        for field in required_fields:
            if field not in request_data:
                errors.append(f"缺少必需字段: {field}")
        
        # 檢查消息格式
        if "messages" in request_data:
            messages = request_data["messages"]
            if not isinstance(messages, list):
                errors.append("messages必須是數組")
            else:
                for i, msg in enumerate(messages):
                    if not isinstance(msg, dict):
                        errors.append(f"消息{i}必須是對象")
                        continue
                    
                    if "role" not in msg:
                        errors.append(f"消息{i}缺少role字段")
                    elif msg["role"] not in ["user", "assistant", "system"]:
                        errors.append(f"消息{i}的role值無效: {msg['role']}")
                    
                    if "content" not in msg:
                        errors.append(f"消息{i}缺少content字段")
        
        # 檢查參數範圍
        if "temperature" in request_data:
            temp = request_data["temperature"]
            if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                errors.append("temperature必須在0-2之間")
        
        if "max_tokens" in request_data:
            max_tokens = request_data["max_tokens"]
            if not isinstance(max_tokens, int) or max_tokens < 1:
                errors.append("max_tokens必須是大於0的整數")
        
        if "top_p" in request_data:
            top_p = request_data["top_p"]
            if not isinstance(top_p, (int, float)) or top_p < 0 or top_p > 1:
                errors.append("top_p必須在0-1之間")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    @staticmethod
    def convert_message_format(messages: List[Dict[str, Any]], 
                             from_format: str, to_format: str) -> List[Dict[str, Any]]:
        """轉換消息格式"""
        if from_format == to_format:
            return messages
        
        converted = []
        
        for msg in messages:
            if from_format == "openai" and to_format == "anthropic":
                # OpenAI -> Anthropic
                if msg["role"] == "system":
                    # Anthropic將system消息轉為user消息
                    converted.append({
                        "role": "user",
                        "content": f"[System: {msg['content']}]"
                    })
                else:
                    converted.append(msg)
            
            elif from_format == "anthropic" and to_format == "openai":
                # Anthropic -> OpenAI
                converted.append(msg)
            
            elif from_format == "google" and to_format == "openai":
                # Google -> OpenAI
                if msg["role"] == "model":
                    converted.append({
                        "role": "assistant",
                        "content": msg["content"]
                    })
                else:
                    converted.append(msg)
            
            else:
                # 默認保持原格式
                converted.append(msg)
        
        return converted
    
    @staticmethod
    def calculate_priority_score(model_config: Dict[str, Any], 
                               request_context: Dict[str, Any]) -> float:
        """計算模型優先級分數"""
        score = 100.0
        
        # 基礎優先級
        score -= model_config.get("priority", 1) * 10
        
        # 成功率加分
        success_rate = model_config.get("success_rate", 100)
        score += success_rate * 0.5
        
        # 響應時間扣分
        avg_response_time = model_config.get("avg_response_time", 1.0)
        score -= avg_response_time * 10
        
        # 成本因素
        cost_per_1k = model_config.get("cost_per_1k_tokens", 0.01)
        if request_context.get("cost_sensitive", False):
            score -= cost_per_1k * 1000
        
        # 功能匹配
        if request_context.get("requires_vision", False):
            if model_config.get("supports_vision", False):
                score += 20
            else:
                score -= 50
        
        if request_context.get("requires_function_calling", False):
            if model_config.get("supports_function_calling", False):
                score += 20
            else:
                score -= 50
        
        # 上下文長度匹配
        context_length = request_context.get("context_length", 0)
        model_context_window = model_config.get("context_window", 4000)
        if context_length > model_context_window:
            score -= 100  # 不能處理的請求
        
        return max(0, score)
    
    @staticmethod
    def detect_language(text: str) -> str:
        """檢測文本語言"""
        # 簡單的語言檢測
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        total_chars = len(text)
        
        if total_chars == 0:
            return "unknown"
        
        if chinese_chars / total_chars > 0.3:
            return "chinese"
        elif any(ord(c) > 127 for c in text):
            return "other"
        else:
            return "english"
    
    @staticmethod
    def estimate_processing_time(request_data: Dict[str, Any], 
                               model_config: Dict[str, Any]) -> float:
        """估算處理時間"""
        # 基礎時間（秒）
        base_time = 1.0
        
        # 根據消息長度調整
        total_text = ""
        for msg in request_data.get("messages", []):
            total_text += str(msg.get("content", ""))
        
        text_length = len(total_text)
        time_per_char = 0.001  # 每字符處理時間
        
        # 根據最大token數調整
        max_tokens = request_data.get("max_tokens", 1000)
        time_per_token = 0.01  # 每token生成時間
        
        # 根據模型性能調整
        model_speed_factor = model_config.get("speed_factor", 1.0)
        
        estimated_time = (base_time + text_length * time_per_char + 
                         max_tokens * time_per_token) * model_speed_factor
        
        return estimated_time
    
    @staticmethod
    def create_error_response(error_message: str, error_code: str = "INTERNAL_ERROR") -> Dict[str, Any]:
        """創建錯誤響應"""
        return {
            "error": {
                "message": error_message,
                "code": error_code,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    @staticmethod
    def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """遮蔽敏感數據"""
        sensitive_keys = ["api_key", "token", "password", "secret", "key"]
        
        def mask_value(value):
            if isinstance(value, str) and len(value) > 8:
                return f"{value[:4]}****{value[-4:]}"
            return "****"
        
        def mask_dict(d):
            if not isinstance(d, dict):
                return d
            
            masked = {}
            for k, v in d.items():
                if any(sensitive_key in k.lower() for sensitive_key in sensitive_keys):
                    masked[k] = mask_value(v)
                elif isinstance(v, dict):
                    masked[k] = mask_dict(v)
                elif isinstance(v, list):
                    masked[k] = [mask_dict(item) if isinstance(item, dict) else item for item in v]
                else:
                    masked[k] = v
            return masked
        
        return mask_dict(data)
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """計算文本相似度"""
        # 簡單的相似度計算
        if not text1 or not text2:
            return 0.0
        
        # 轉換為小寫並分詞
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # 計算Jaccard相似度
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    @staticmethod
    async def with_timeout(coro, timeout: float):
        """為協程添加超時"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise Exception(f"操作超時 ({timeout}s)")
    
    @staticmethod
    def format_model_info(model_config: Dict[str, Any]) -> str:
        """格式化模型信息"""
        info = f"🤖 {model_config.get('model_id', 'Unknown')}\n"
        info += f"📊 提供商: {model_config.get('provider', 'Unknown')}\n"
        info += f"💰 成本: {RouterUtils.format_cost(model_config.get('cost_per_1k_tokens', 0))}/1k tokens\n"
        info += f"⚡ 平均響應時間: {RouterUtils.format_response_time(model_config.get('avg_response_time', 0))}\n"
        info += f"✅ 成功率: {model_config.get('success_rate', 0):.1f}%\n"
        info += f"📝 上下文窗口: {model_config.get('context_window', 0):,} tokens\n"
        
        capabilities = []
        if model_config.get('supports_vision', False):
            capabilities.append("🖼️ 圖像識別")
        if model_config.get('supports_function_calling', False):
            capabilities.append("🔧 函數調用")
        if model_config.get('supports_streaming', True):
            capabilities.append("📡 流式輸出")
        
        if capabilities:
            info += f"🎯 支持功能: {', '.join(capabilities)}\n"
        
        return info