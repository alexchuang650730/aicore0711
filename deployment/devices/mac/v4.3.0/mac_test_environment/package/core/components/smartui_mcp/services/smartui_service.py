#!/usr/bin/env python3
"""
SmartUI MCP 核心服务

PowerAutomation 4.1 SmartUI MCP的主要服务类
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class SmartUIServiceConfig:
    """SmartUI服务配置"""
    service_name: str = "SmartUI MCP"
    version: str = "4.1.0"
    ai_optimization_enabled: bool = True
    agui_integration_enabled: bool = True
    theme_management_enabled: bool = True
    component_registry_enabled: bool = True
    performance_monitoring_enabled: bool = True
    cache_enabled: bool = True
    cache_ttl: int = 3600

class SmartUIService:
    """SmartUI MCP核心服务"""
    
    def __init__(self, config: Optional[SmartUIServiceConfig] = None):
        self.config = config or SmartUIServiceConfig()
        self.service_id = f"smartui_mcp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 服务状态
        self.is_running = False
        self.start_time = None
        
        # 服务组件
        self.ai_service = None
        self.theme_service = None
        self.registry_service = None
        
        # 缓存
        self.cache = {} if self.config.cache_enabled else None
        
        # 统计信息
        self.stats = {
            "requests_processed": 0,
            "components_generated": 0,
            "ai_optimizations": 0,
            "theme_applications": 0,
            "errors": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        logger.info(f"SmartUI MCP Service initialized: {self.service_id}")
    
    async def start(self) -> bool:
        """启动SmartUI服务"""
        try:
            if self.is_running:
                logger.warning("SmartUI service is already running")
                return True
            
            logger.info("Starting SmartUI MCP Service...")
            
            # 初始化子服务
            await self._initialize_services()
            
            # 加载配置
            await self._load_configuration()
            
            # 验证环境
            await self._validate_environment()
            
            self.is_running = True
            self.start_time = datetime.now()
            
            logger.info(f"SmartUI MCP Service started successfully: {self.service_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start SmartUI service: {e}")
            return False
    
    async def stop(self) -> bool:
        """停止SmartUI服务"""
        try:
            if not self.is_running:
                logger.warning("SmartUI service is not running")
                return True
            
            logger.info("Stopping SmartUI MCP Service...")
            
            # 停止子服务
            await self._shutdown_services()
            
            # 清理资源
            await self._cleanup_resources()
            
            self.is_running = False
            
            logger.info("SmartUI MCP Service stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop SmartUI service: {e}")
            return False
    
    async def _initialize_services(self):
        """初始化子服务"""
        if self.config.ai_optimization_enabled:
            from .ai_optimization_service import AIOptimizationService
            self.ai_service = AIOptimizationService()
            await self.ai_service.initialize()
        
        if self.config.theme_management_enabled:
            from .theme_service import ThemeService
            self.theme_service = ThemeService()
            await self.theme_service.initialize()
        
        if self.config.component_registry_enabled:
            from .component_registry_service import ComponentRegistryService
            self.registry_service = ComponentRegistryService()
            await self.registry_service.initialize()
    
    async def _load_configuration(self):
        """加载配置"""
        config_path = Path("core/components/smartui_mcp/config/smartui_config.json")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                # 更新配置
                for key, value in config_data.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
    
    async def _validate_environment(self):
        """验证环境"""
        # 检查必要的目录
        required_dirs = [
            "core/components/smartui_mcp/templates",
            "core/components/smartui_mcp/generated",
            "core/components/smartui_mcp/config"
        ]
        
        for dir_path in required_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    async def _shutdown_services(self):
        """关闭子服务"""
        if self.ai_service:
            await self.ai_service.shutdown()
        
        if self.theme_service:
            await self.theme_service.shutdown()
        
        if self.registry_service:
            await self.registry_service.shutdown()
    
    async def _cleanup_resources(self):
        """清理资源"""
        if self.cache:
            self.cache.clear()
    
    async def optimize_component_context(
        self, 
        context: Dict[str, Any], 
        template: str, 
        framework: str = "react"
    ) -> Dict[str, Any]:
        """AI优化组件上下文"""
        try:
            self.stats["requests_processed"] += 1
            
            # 检查缓存
            cache_key = f"optimize_{template}_{framework}_{hash(str(context))}"
            if self.cache and cache_key in self.cache:
                self.stats["cache_hits"] += 1
                return self.cache[cache_key]
            
            self.stats["cache_misses"] += 1
            
            # AI优化
            if self.ai_service:
                optimized_context = await self.ai_service.optimize_context(
                    context, template, framework
                )
                self.stats["ai_optimizations"] += 1
            else:
                optimized_context = context.copy()
            
            # 缓存结果
            if self.cache:
                self.cache[cache_key] = optimized_context
            
            return optimized_context
            
        except Exception as e:
            logger.error(f"Context optimization failed: {e}")
            self.stats["errors"] += 1
            return context
    
    async def apply_theme(
        self, 
        component_data: Dict[str, Any], 
        theme_name: str
    ) -> Dict[str, Any]:
        """应用主题"""
        try:
            if self.theme_service:
                themed_data = await self.theme_service.apply_theme(
                    component_data, theme_name
                )
                self.stats["theme_applications"] += 1
                return themed_data
            else:
                return component_data
                
        except Exception as e:
            logger.error(f"Theme application failed: {e}")
            self.stats["errors"] += 1
            return component_data
    
    async def register_component(
        self, 
        component_name: str, 
        component_data: Dict[str, Any]
    ) -> bool:
        """注册组件"""
        try:
            if self.registry_service:
                success = await self.registry_service.register_component(
                    component_name, component_data
                )
                if success:
                    self.stats["components_generated"] += 1
                return success
            else:
                return False
                
        except Exception as e:
            logger.error(f"Component registration failed: {e}")
            self.stats["errors"] += 1
            return False
    
    async def get_component_templates(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取组件模板列表"""
        try:
            templates = []
            templates_dir = Path("core/components/smartui_mcp/templates/components")
            
            if category:
                category_dir = templates_dir / category
                if category_dir.exists():
                    for template_file in category_dir.glob("*.json"):
                        with open(template_file, 'r', encoding='utf-8') as f:
                            template_data = json.load(f)
                            template_data["file_path"] = str(template_file)
                            templates.append(template_data)
            else:
                # 获取所有模板
                for category_dir in templates_dir.iterdir():
                    if category_dir.is_dir():
                        for template_file in category_dir.glob("*.json"):
                            with open(template_file, 'r', encoding='utf-8') as f:
                                template_data = json.load(f)
                                template_data["file_path"] = str(template_file)
                                template_data["category"] = category_dir.name
                                templates.append(template_data)
            
            return templates
            
        except Exception as e:
            logger.error(f"Failed to get component templates: {e}")
            return []
    
    async def get_available_themes(self) -> List[Dict[str, Any]]:
        """获取可用主题列表"""
        try:
            if self.theme_service:
                return await self.theme_service.get_available_themes()
            else:
                return []
                
        except Exception as e:
            logger.error(f"Failed to get available themes: {e}")
            return []
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "service_id": self.service_id,
            "version": self.config.version,
            "is_running": self.is_running,
            "uptime_seconds": uptime,
            "config": asdict(self.config),
            "stats": self.stats.copy(),
            "services": {
                "ai_optimization": self.ai_service is not None,
                "theme_management": self.theme_service is not None,
                "component_registry": self.registry_service is not None
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        for key in self.stats:
            self.stats[key] = 0
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = {
            "status": "healthy" if self.is_running else "stopped",
            "service_id": self.service_id,
            "version": self.config.version,
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        # 检查子服务
        if self.ai_service:
            health_status["checks"]["ai_service"] = await self.ai_service.health_check()
        
        if self.theme_service:
            health_status["checks"]["theme_service"] = await self.theme_service.health_check()
        
        if self.registry_service:
            health_status["checks"]["registry_service"] = await self.registry_service.health_check()
        
        # 检查文件系统
        try:
            templates_dir = Path("core/components/smartui_mcp/templates")
            health_status["checks"]["templates_directory"] = {
                "exists": templates_dir.exists(),
                "readable": templates_dir.is_dir() if templates_dir.exists() else False
            }
        except Exception as e:
            health_status["checks"]["templates_directory"] = {
                "exists": False,
                "error": str(e)
            }
        
        return health_status

# 全局服务实例
_smartui_service_instance = None

async def get_smartui_service() -> SmartUIService:
    """获取SmartUI服务实例（单例模式）"""
    global _smartui_service_instance
    
    if _smartui_service_instance is None:
        _smartui_service_instance = SmartUIService()
        await _smartui_service_instance.start()
    
    return _smartui_service_instance

async def shutdown_smartui_service():
    """关闭SmartUI服务"""
    global _smartui_service_instance
    
    if _smartui_service_instance:
        await _smartui_service_instance.stop()
        _smartui_service_instance = None

