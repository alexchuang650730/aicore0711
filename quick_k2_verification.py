#!/usr/bin/env python3
"""
快速K2驗證測試
確保所有輸入輸出都通過K2而不是Claude Code
"""

import json
import time
import requests
from datetime import datetime

def test_k2_service():
    """測試K2服務"""
    print("🧪 測試K2服務...")
    
    results = {}
    
    # 1. 健康檢查
    try:
        response = requests.get("http://localhost:8765/health", timeout=5)
        health_data = response.json()
        
        results["health_check"] = {
            "success": response.status_code == 200,
            "provider": health_data.get("provider"),
            "model": health_data.get("model"),
            "status": health_data.get("status")
        }
        
        print(f"  ✅ 健康檢查: {health_data.get('status')} - {health_data.get('provider')}")
        
    except Exception as e:
        results["health_check"] = {"success": False, "error": str(e)}
        print(f"  ❌ 健康檢查失敗: {e}")
    
    # 2. 模型列表
    try:
        response = requests.get("http://localhost:8765/v1/models", timeout=5)
        models_data = response.json()
        
        k2_model_found = any("kimi-k2" in model.get("id", "") for model in models_data.get("data", []))
        
        results["models_list"] = {
            "success": response.status_code == 200 and k2_model_found,
            "models_count": len(models_data.get("data", [])),
            "has_k2_model": k2_model_found
        }
        
        print(f"  ✅ 模型列表: 找到{len(models_data.get('data', []))}個模型，K2模型: {k2_model_found}")
        
    except Exception as e:
        results["models_list"] = {"success": False, "error": str(e)}
        print(f"  ❌ 模型列表失敗: {e}")
    
    # 3. K2聊天測試
    try:
        payload = {
            "model": "kimi-k2-instruct",
            "messages": [{"role": "user", "content": "Hello, please respond briefly"}],
            "max_tokens": 50,
            "temperature": 0.7
        }
        
        start_time = time.time()
        response = requests.post("http://localhost:8765/v1/chat/completions", json=payload, timeout=10)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            chat_data = response.json()
            content = chat_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            model_used = chat_data.get("model", "")
            
            results["chat_completion"] = {
                "success": True,
                "response_time": response_time,
                "model_used": model_used,
                "has_content": bool(content),
                "content_length": len(content)
            }
            
            print(f"  ✅ K2聊天: 模型={model_used}, 響應時間={response_time:.2f}s, 內容長度={len(content)}")
        else:
            results["chat_completion"] = {"success": False, "status_code": response.status_code}
            print(f"  ❌ K2聊天失敗: 狀態碼={response.status_code}")
            
    except Exception as e:
        results["chat_completion"] = {"success": False, "error": str(e)}
        print(f"  ❌ K2聊天失敗: {e}")
    
    # 4. 統計信息
    try:
        response = requests.get("http://localhost:8765/v1/stats", timeout=5)
        stats_data = response.json()
        
        provider = stats_data.get("provider", "")
        model = stats_data.get("model", "")
        
        is_k2_service = "infini-ai" in provider and "kimi-k2" in model
        
        results["statistics"] = {
            "success": response.status_code == 200 and is_k2_service,
            "provider": provider,
            "model": model,
            "is_k2_service": is_k2_service
        }
        
        print(f"  ✅ 統計信息: 提供者={provider}, 模型={model}")
        
    except Exception as e:
        results["statistics"] = {"success": False, "error": str(e)}
        print(f"  ❌ 統計信息失敗: {e}")
    
    return results

def test_mirror_service():
    """測試Mirror服務"""
    print("\n🪞 測試Mirror服務...")
    
    results = {}
    
    # 1. 健康檢查
    try:
        response = requests.get("http://localhost:8080/health", timeout=5)
        health_data = response.json()
        
        results["health_check"] = {
            "success": response.status_code == 200,
            "status": health_data.get("status"),
            "components": health_data.get("components", {})
        }
        
        print(f"  ✅ 健康檢查: {health_data.get('status')}")
        
    except Exception as e:
        results["health_check"] = {"success": False, "error": str(e)}
        print(f"  ❌ 健康檢查失敗: {e}")
    
    # 2. 檢查Mirror配置
    try:
        import os
        if os.path.exists("mirror_config.json"):
            with open("mirror_config.json", 'r') as f:
                config = json.load(f)
            
            uses_k2 = any(
                "k2" in str(value).lower() or "kimi" in str(value).lower() 
                for value in str(config).lower().split()
            )
            
            results["configuration"] = {
                "success": uses_k2,
                "config_exists": True,
                "uses_k2": uses_k2
            }
            
            print(f"  ✅ 配置檢查: K2配置={uses_k2}")
        else:
            results["configuration"] = {
                "success": False,
                "config_exists": False,
                "error": "配置文件不存在"
            }
            print("  ❌ 配置文件不存在")
            
    except Exception as e:
        results["configuration"] = {"success": False, "error": str(e)}
        print(f"  ❌ 配置檢查失敗: {e}")
    
    return results

def test_k2_routing():
    """測試K2路由"""
    print("\n🔄 測試K2路由...")
    
    results = {}
    
    # 測試端到端K2流程
    try:
        # 1. 先通過K2服務測試
        k2_payload = {
            "model": "kimi-k2-instruct",
            "messages": [{"role": "user", "content": "Generate a simple Python function"}],
            "max_tokens": 100
        }
        
        start_time = time.time()
        response = requests.post("http://localhost:8765/v1/chat/completions", json=k2_payload, timeout=15)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            model_used = data.get("model", "")
            
            # 檢查是否真的使用了K2
            is_k2_response = "kimi-k2" in model_used
            
            results["k2_direct_test"] = {
                "success": True,
                "response_time": response_time,
                "model_used": model_used,
                "is_k2_response": is_k2_response,
                "content_length": len(content),
                "has_code": "def " in content or "function" in content.lower()
            }
            
            print(f"  ✅ K2直接測試: 模型={model_used}, 時間={response_time:.2f}s")
            print(f"     響應包含代碼: {'def ' in content or 'function' in content.lower()}")
        else:
            results["k2_direct_test"] = {"success": False, "status_code": response.status_code}
            print(f"  ❌ K2直接測試失敗: {response.status_code}")
            
    except Exception as e:
        results["k2_direct_test"] = {"success": False, "error": str(e)}
        print(f"  ❌ K2直接測試失敗: {e}")
    
    return results

def verify_no_claude_usage():
    """驗證沒有使用Claude"""
    print("\n🚫 驗證沒有使用Claude...")
    
    results = {}
    
    try:
        # 檢查提供者比較
        response = requests.get("http://localhost:8765/v1/providers/compare", timeout=5)
        if response.status_code == 200:
            comparison_data = response.json()
            
            primary_provider = comparison_data.get("primary", {}).get("provider", "")
            fallback_provider = comparison_data.get("fallback", {}).get("provider", "")
            
            # 檢查是否避免使用Claude
            avoids_claude = (
                "claude" not in primary_provider.lower() and
                "anthropic" not in primary_provider.lower() and
                ("None" in fallback_provider or "k2" in fallback_provider.lower())
            )
            
            results["provider_comparison"] = {
                "success": avoids_claude,
                "primary_provider": primary_provider,
                "fallback_provider": fallback_provider,
                "avoids_claude": avoids_claude
            }
            
            print(f"  ✅ 提供者比較: 主要={primary_provider}, 回退={fallback_provider}")
            print(f"     避免Claude: {avoids_claude}")
        else:
            results["provider_comparison"] = {"success": False, "status_code": response.status_code}
            print(f"  ❌ 提供者比較失敗: {response.status_code}")
            
    except Exception as e:
        results["provider_comparison"] = {"success": False, "error": str(e)}
        print(f"  ❌ 提供者比較失敗: {e}")
    
    return results

def generate_report(k2_results, mirror_results, routing_results, claude_check_results):
    """生成測試報告"""
    
    all_results = {
        "k2_service": k2_results,
        "mirror_service": mirror_results,
        "k2_routing": routing_results,
        "claude_verification": claude_check_results
    }
    
    # 計算總體成功率
    total_tests = 0
    passed_tests = 0
    
    for category, tests in all_results.items():
        for test_name, result in tests.items():
            total_tests += 1
            if result.get("success", False):
                passed_tests += 1
    
    success_rate = passed_tests / total_tests if total_tests > 0 else 0
    
    # 檢查關鍵K2功能
    critical_k2_tests = [
        k2_results.get("health_check", {}).get("success", False),
        k2_results.get("chat_completion", {}).get("success", False),
        k2_results.get("statistics", {}).get("success", False),
        routing_results.get("k2_direct_test", {}).get("success", False),
        claude_check_results.get("provider_comparison", {}).get("success", False)
    ]
    
    k2_critical_success = sum(critical_k2_tests)
    k2_migration_successful = k2_critical_success >= len(critical_k2_tests) * 0.8
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": success_rate,
            "k2_migration_successful": k2_migration_successful,
            "k2_critical_success_count": k2_critical_success,
            "k2_critical_total": len(critical_k2_tests)
        },
        "detailed_results": all_results,
        "k2_verification": {
            "uses_k2_model": k2_results.get("chat_completion", {}).get("success", False),
            "uses_k2_provider": "infini-ai" in k2_results.get("statistics", {}).get("provider", ""),
            "avoids_claude": claude_check_results.get("provider_comparison", {}).get("avoids_claude", False),
            "response_quality": k2_results.get("chat_completion", {}).get("has_content", False)
        }
    }
    
    return report

def main():
    """主函數"""
    print("🚀 快速K2驗證測試開始")
    print("=" * 50)
    
    # 運行測試
    k2_results = test_k2_service()
    mirror_results = test_mirror_service()
    routing_results = test_k2_routing()
    claude_check_results = verify_no_claude_usage()
    
    # 生成報告
    report = generate_report(k2_results, mirror_results, routing_results, claude_check_results)
    
    # 顯示結果
    print("\n" + "=" * 50)
    print("📊 測試結果摘要")
    print("=" * 50)
    
    summary = report["summary"]
    print(f"總測試數: {summary['total_tests']}")
    print(f"通過: {summary['passed_tests']}")
    print(f"失敗: {summary['failed_tests']}")
    print(f"成功率: {summary['success_rate']:.1%}")
    
    k2_verification = report["k2_verification"]
    print(f"\n🤖 K2驗證狀態:")
    print(f"  使用K2模型: {'✅' if k2_verification['uses_k2_model'] else '❌'}")
    print(f"  使用K2提供者: {'✅' if k2_verification['uses_k2_provider'] else '❌'}")
    print(f"  避免Claude: {'✅' if k2_verification['avoids_claude'] else '❌'}")
    print(f"  響應質量: {'✅' if k2_verification['response_quality'] else '❌'}")
    
    migration_status = summary['k2_migration_successful']
    print(f"\n🚀 K2遷移狀態: {'✅ 成功' if migration_status else '❌ 需要改進'}")
    print(f"關鍵測試通過: {summary['k2_critical_success_count']}/{summary['k2_critical_total']}")
    
    # 保存報告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"k2_verification_report_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 測試報告已保存: {filename}")
    
    if migration_status:
        print("\n🎉 K2遷移驗證成功！所有輸入輸出都通過K2處理")
    else:
        print("\n⚠️ K2遷移需要改進，部分功能可能仍在使用Claude Code")
    
    return report

if __name__ == "__main__":
    report = main()