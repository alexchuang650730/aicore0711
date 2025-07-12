#!/usr/bin/env python3
"""
PowerAutomation v4.6.9 版本配額管理系統
Version Quota Management System

支持個人版、專業版、團隊版、企業版四個版本層級
Supports Personal, Professional, Team, and Enterprise edition tiers
"""

import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class EditionType(Enum):
    """版本類型"""
    PERSONAL = "personal"       # 個人版
    PROFESSIONAL = "professional"   # 專業版  
    TEAM = "team"              # 團隊版
    ENTERPRISE = "enterprise"   # 企業版

@dataclass
class QuotaLimits:
    """配額限制"""
    concurrent_projects: int     # 並發項目數
    daily_ai_requests: int      # 每日AI請求
    collaboration_users: int    # 協作用戶數
    storage_limit_mb: int      # 存儲限制(MB)
    
    # 附加功能限制
    advanced_workflows: bool = False      # 高級工作流
    priority_support: bool = False        # 優先支持
    custom_integrations: bool = False     # 自定義集成
    api_access: bool = False             # API訪問
    white_labeling: bool = False         # 白標籤
    sla_guarantee: bool = False          # SLA保證

@dataclass
class UsageStats:
    """使用統計"""
    current_projects: int = 0
    daily_requests_used: int = 0
    active_users: int = 0
    storage_used_mb: int = 0
    last_reset_date: str = ""

class VersionQuotaManager:
    """版本配額管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.edition_configs = self._define_edition_configs()
        self.user_usage = {}
        
    def _define_edition_configs(self) -> Dict[EditionType, QuotaLimits]:
        """定義版本配額配置"""
        return {
            EditionType.PERSONAL: QuotaLimits(
                concurrent_projects=3,
                daily_ai_requests=100,
                collaboration_users=0,
                storage_limit_mb=1024,
                advanced_workflows=False,
                priority_support=False,
                custom_integrations=False,
                api_access=False,
                white_labeling=False,
                sla_guarantee=False
            ),
            
            EditionType.PROFESSIONAL: QuotaLimits(
                concurrent_projects=10,
                daily_ai_requests=1000,
                collaboration_users=3,
                storage_limit_mb=10240,
                advanced_workflows=True,
                priority_support=True,
                custom_integrations=False,
                api_access=True,
                white_labeling=False,
                sla_guarantee=False
            ),
            
            EditionType.TEAM: QuotaLimits(
                concurrent_projects=50,
                daily_ai_requests=5000,
                collaboration_users=15,
                storage_limit_mb=51200,
                advanced_workflows=True,
                priority_support=True,
                custom_integrations=True,
                api_access=True,
                white_labeling=False,
                sla_guarantee=True
            ),
            
            EditionType.ENTERPRISE: QuotaLimits(
                concurrent_projects=-1,  # 無限制
                daily_ai_requests=-1,    # 無限制  
                collaboration_users=-1,  # 無限制
                storage_limit_mb=-1,     # 無限制
                advanced_workflows=True,
                priority_support=True,
                custom_integrations=True,
                api_access=True,
                white_labeling=True,
                sla_guarantee=True
            )
        }
    
    def get_edition_limits(self, edition: EditionType) -> QuotaLimits:
        """獲取版本限制"""
        return self.edition_configs.get(edition, self.edition_configs[EditionType.PERSONAL])
    
    def check_quota_availability(self, user_id: str, edition: EditionType, 
                                resource_type: str, requested_amount: int = 1) -> Dict[str, Any]:
        """檢查配額可用性"""
        limits = self.get_edition_limits(edition)
        usage = self.user_usage.get(user_id, UsageStats())
        
        # 重置每日使用量（如果需要）
        if self._should_reset_daily_usage(usage):
            usage.daily_requests_used = 0
            usage.last_reset_date = datetime.now().date().isoformat()
        
        result = {
            "allowed": False,
            "reason": "",
            "current_usage": 0,
            "limit": 0,
            "remaining": 0
        }
        
        if resource_type == "concurrent_projects":
            limit = limits.concurrent_projects
            current = usage.current_projects
            result["limit"] = limit
            result["current_usage"] = current
            
            if limit == -1:  # 無限制
                result["allowed"] = True
                result["remaining"] = -1
            elif current + requested_amount <= limit:
                result["allowed"] = True
                result["remaining"] = limit - current
            else:
                result["reason"] = f"超過並發項目限制 ({limit}個)"
                result["remaining"] = limit - current
                
        elif resource_type == "daily_ai_requests":
            limit = limits.daily_ai_requests
            current = usage.daily_requests_used
            result["limit"] = limit
            result["current_usage"] = current
            
            if limit == -1:  # 無限制
                result["allowed"] = True
                result["remaining"] = -1
            elif current + requested_amount <= limit:
                result["allowed"] = True
                result["remaining"] = limit - current
            else:
                result["reason"] = f"超過每日AI請求限制 ({limit}次)"
                result["remaining"] = limit - current
                
        elif resource_type == "collaboration_users":
            limit = limits.collaboration_users
            current = usage.active_users
            result["limit"] = limit
            result["current_usage"] = current
            
            if limit == -1:  # 無限制
                result["allowed"] = True
                result["remaining"] = -1
            elif current + requested_amount <= limit:
                result["allowed"] = True
                result["remaining"] = limit - current
            else:
                result["reason"] = f"超過協作用戶限制 ({limit}個)"
                result["remaining"] = limit - current
                
        elif resource_type == "storage":
            limit = limits.storage_limit_mb
            current = usage.storage_used_mb
            result["limit"] = limit
            result["current_usage"] = current
            
            if limit == -1:  # 無限制
                result["allowed"] = True
                result["remaining"] = -1
            elif current + requested_amount <= limit:
                result["allowed"] = True
                result["remaining"] = limit - current
            else:
                result["reason"] = f"超過存儲限制 ({limit}MB)"
                result["remaining"] = limit - current
        
        return result
    
    def consume_quota(self, user_id: str, edition: EditionType, 
                     resource_type: str, amount: int = 1) -> bool:
        """消耗配額"""
        check_result = self.check_quota_availability(user_id, edition, resource_type, amount)
        
        if not check_result["allowed"]:
            self.logger.warning(f"配額不足: {user_id} - {resource_type} - {check_result['reason']}")
            return False
        
        # 更新使用統計
        if user_id not in self.user_usage:
            self.user_usage[user_id] = UsageStats()
        
        usage = self.user_usage[user_id]
        
        if resource_type == "concurrent_projects":
            usage.current_projects += amount
        elif resource_type == "daily_ai_requests":
            usage.daily_requests_used += amount
        elif resource_type == "collaboration_users":
            usage.active_users += amount
        elif resource_type == "storage":
            usage.storage_used_mb += amount
        
        self.logger.info(f"配額消耗成功: {user_id} - {resource_type} - {amount}")
        return True
    
    def release_quota(self, user_id: str, resource_type: str, amount: int = 1) -> bool:
        """釋放配額"""
        if user_id not in self.user_usage:
            return False
        
        usage = self.user_usage[user_id]
        
        if resource_type == "concurrent_projects":
            usage.current_projects = max(0, usage.current_projects - amount)
        elif resource_type == "collaboration_users":
            usage.active_users = max(0, usage.active_users - amount)
        elif resource_type == "storage":
            usage.storage_used_mb = max(0, usage.storage_used_mb - amount)
        
        self.logger.info(f"配額釋放成功: {user_id} - {resource_type} - {amount}")
        return True
    
    def get_user_usage_summary(self, user_id: str, edition: EditionType) -> Dict[str, Any]:
        """獲取用戶使用摘要"""
        limits = self.get_edition_limits(edition)
        usage = self.user_usage.get(user_id, UsageStats())
        
        def format_limit(value):
            return "無限制" if value == -1 else str(value)
        
        def calculate_percentage(used, limit):
            if limit == -1:
                return 0
            return min(100, (used / limit) * 100) if limit > 0 else 0
        
        return {
            "user_id": user_id,
            "edition": edition.value,
            "usage_summary": {
                "concurrent_projects": {
                    "used": usage.current_projects,
                    "limit": format_limit(limits.concurrent_projects),
                    "remaining": "無限制" if limits.concurrent_projects == -1 else 
                               max(0, limits.concurrent_projects - usage.current_projects),
                    "percentage": calculate_percentage(usage.current_projects, limits.concurrent_projects)
                },
                "daily_ai_requests": {
                    "used": usage.daily_requests_used,
                    "limit": format_limit(limits.daily_ai_requests),
                    "remaining": "無限制" if limits.daily_ai_requests == -1 else 
                               max(0, limits.daily_ai_requests - usage.daily_requests_used),
                    "percentage": calculate_percentage(usage.daily_requests_used, limits.daily_ai_requests)
                },
                "collaboration_users": {
                    "used": usage.active_users,
                    "limit": format_limit(limits.collaboration_users),
                    "remaining": "無限制" if limits.collaboration_users == -1 else 
                               max(0, limits.collaboration_users - usage.active_users),
                    "percentage": calculate_percentage(usage.active_users, limits.collaboration_users)
                },
                "storage": {
                    "used_mb": usage.storage_used_mb,
                    "limit_mb": format_limit(limits.storage_limit_mb),
                    "remaining_mb": "無限制" if limits.storage_limit_mb == -1 else 
                                  max(0, limits.storage_limit_mb - usage.storage_used_mb),
                    "percentage": calculate_percentage(usage.storage_used_mb, limits.storage_limit_mb)
                }
            },
            "features": {
                "advanced_workflows": limits.advanced_workflows,
                "priority_support": limits.priority_support,
                "custom_integrations": limits.custom_integrations,
                "api_access": limits.api_access,
                "white_labeling": limits.white_labeling,
                "sla_guarantee": limits.sla_guarantee
            },
            "last_updated": datetime.now().isoformat()
        }
    
    def get_edition_comparison_table(self) -> Dict[str, Any]:
        """獲取版本比較表"""
        comparison = {
            "title": "PowerAutomation v4.6.9 版本配額對比",
            "editions": {},
            "generated_at": datetime.now().isoformat()
        }
        
        for edition_type in EditionType:
            limits = self.get_edition_limits(edition_type)
            comparison["editions"][edition_type.value] = {
                "name": self._get_edition_name(edition_type),
                "concurrent_projects": "無限制" if limits.concurrent_projects == -1 else limits.concurrent_projects,
                "daily_ai_requests": "無限制" if limits.daily_ai_requests == -1 else limits.daily_ai_requests,
                "collaboration_users": "無限制" if limits.collaboration_users == -1 else limits.collaboration_users,
                "storage_limit_mb": "無限制" if limits.storage_limit_mb == -1 else limits.storage_limit_mb,
                "advanced_workflows": "✅" if limits.advanced_workflows else "❌",
                "priority_support": "✅" if limits.priority_support else "❌",
                "custom_integrations": "✅" if limits.custom_integrations else "❌",
                "api_access": "✅" if limits.api_access else "❌",
                "white_labeling": "✅" if limits.white_labeling else "❌",
                "sla_guarantee": "✅" if limits.sla_guarantee else "❌"
            }
        
        return comparison
    
    def _get_edition_name(self, edition: EditionType) -> str:
        """獲取版本中文名稱"""
        names = {
            EditionType.PERSONAL: "個人版",
            EditionType.PROFESSIONAL: "專業版",
            EditionType.TEAM: "團隊版",
            EditionType.ENTERPRISE: "企業版"
        }
        return names.get(edition, "未知版本")
    
    def _should_reset_daily_usage(self, usage: UsageStats) -> bool:
        """檢查是否需要重置每日使用量"""
        if not usage.last_reset_date:
            return True
        
        try:
            last_reset = datetime.fromisoformat(usage.last_reset_date).date()
            today = datetime.now().date()
            return today > last_reset
        except:
            return True
    
    def save_quota_data(self, file_path: str = "quota_data.json"):
        """保存配額數據"""
        data = {
            "user_usage": {
                user_id: asdict(usage) for user_id, usage in self.user_usage.items()
            },
            "last_saved": datetime.now().isoformat()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"配額數據已保存到: {file_path}")
    
    def load_quota_data(self, file_path: str = "quota_data.json"):
        """加載配額數據"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.user_usage = {
                user_id: UsageStats(**usage_data) 
                for user_id, usage_data in data.get("user_usage", {}).items()
            }
            
            self.logger.info(f"配額數據已從 {file_path} 加載")
        except FileNotFoundError:
            self.logger.info("配額數據文件不存在，使用默認配置")
        except Exception as e:
            self.logger.error(f"加載配額數據失敗: {e}")

# 單例實例
quota_manager = VersionQuotaManager()

def main():
    """演示配額管理系統"""
    print("🎯 PowerAutomation v4.6.9 版本配額管理系統")
    print("=" * 60)
    
    # 顯示版本比較表
    comparison = quota_manager.get_edition_comparison_table()
    print(f"\n📊 {comparison['title']}")
    print("-" * 60)
    print(f"{'配額項目':<15} {'個人版':<8} {'專業版':<8} {'團隊版':<8} {'企業版':<8}")
    print("-" * 60)
    
    editions = comparison["editions"]
    
    print(f"{'並發項目數':<13} {editions['personal']['concurrent_projects']:<8} "
          f"{editions['professional']['concurrent_projects']:<8} "
          f"{editions['team']['concurrent_projects']:<8} "
          f"{editions['enterprise']['concurrent_projects']:<8}")
    
    print(f"{'每日AI請求':<13} {editions['personal']['daily_ai_requests']:<8} "
          f"{editions['professional']['daily_ai_requests']:<8} "
          f"{editions['team']['daily_ai_requests']:<8} "
          f"{editions['enterprise']['daily_ai_requests']:<8}")
    
    print(f"{'協作用戶數':<13} {editions['personal']['collaboration_users']:<8} "
          f"{editions['professional']['collaboration_users']:<8} "
          f"{editions['team']['collaboration_users']:<8} "
          f"{editions['enterprise']['collaboration_users']:<8}")
    
    print(f"{'存儲限制(MB)':<12} {editions['personal']['storage_limit_mb']:<8} "
          f"{editions['professional']['storage_limit_mb']:<8} "
          f"{editions['team']['storage_limit_mb']:<8} "
          f"{editions['enterprise']['storage_limit_mb']:<8}")
    
    print("-" * 60)
    print("附加功能:")
    print(f"{'高級工作流':<13} {editions['personal']['advanced_workflows']:<8} "
          f"{editions['professional']['advanced_workflows']:<8} "
          f"{editions['team']['advanced_workflows']:<8} "
          f"{editions['enterprise']['advanced_workflows']:<8}")
    
    print(f"{'優先支持':<14} {editions['personal']['priority_support']:<8} "
          f"{editions['professional']['priority_support']:<8} "
          f"{editions['team']['priority_support']:<8} "
          f"{editions['enterprise']['priority_support']:<8}")
    
    print(f"{'API訪問':<15} {editions['personal']['api_access']:<8} "
          f"{editions['professional']['api_access']:<8} "
          f"{editions['team']['api_access']:<8} "
          f"{editions['enterprise']['api_access']:<8}")
    
    print(f"{'SLA保證':<15} {editions['personal']['sla_guarantee']:<8} "
          f"{editions['professional']['sla_guarantee']:<8} "
          f"{editions['team']['sla_guarantee']:<8} "
          f"{editions['enterprise']['sla_guarantee']:<8}")
    
    # 演示用戶使用
    print(f"\n🧪 配額使用演示:")
    test_user = "user_demo_001"
    edition = EditionType.PROFESSIONAL
    
    # 消耗一些配額
    quota_manager.consume_quota(test_user, edition, "concurrent_projects", 3)
    quota_manager.consume_quota(test_user, edition, "daily_ai_requests", 150)
    quota_manager.consume_quota(test_user, edition, "collaboration_users", 2)
    quota_manager.consume_quota(test_user, edition, "storage", 2048)
    
    # 顯示使用摘要
    summary = quota_manager.get_user_usage_summary(test_user, edition)
    print(f"\n👤 用戶: {test_user} ({quota_manager._get_edition_name(edition)})")
    print("-" * 40)
    
    for resource, stats in summary["usage_summary"].items():
        percentage = stats["percentage"]
        status = "🔴" if percentage > 80 else "🟡" if percentage > 60 else "🟢"
        print(f"{resource}: {stats['used']}/{stats['limit']} ({percentage:.1f}%) {status}")
    
    # 保存配額數據
    quota_manager.save_quota_data("demo_quota_data.json")
    print(f"\n💾 演示配額數據已保存")

if __name__ == "__main__":
    main()