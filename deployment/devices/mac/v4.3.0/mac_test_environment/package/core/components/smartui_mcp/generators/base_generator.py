#!/usr/bin/env python3
"""
基础生成器类

提供所有生成器的基础功能和接口定义
"""

import json
import yaml
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class GeneratorType(Enum):
    """生成器类型枚举"""
    COMPONENT = "component"
    LAYOUT = "layout"
    PAGE = "page"
    THEME = "theme"
    STYLE = "style"
    SCRIPT = "script"

@dataclass
class GenerationConfig:
    """生成配置"""
    template_name: str
    output_path: str
    context: Dict[str, Any]
    theme: Optional[str] = None
    minify: bool = False
    source_maps: bool = False
    hot_reload: bool = False

@dataclass
class GenerationResult:
    """生成结果"""
    success: bool
    output_files: List[str]
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]

class BaseGenerator(ABC):
    """基础生成器抽象类"""
    
    def __init__(
        self,
        template_dirs: Optional[List[str]] = None,
        output_dir: Optional[str] = None,
        theme_dirs: Optional[List[str]] = None
    ):
        self.template_dirs = template_dirs or ["ui/templates"]
        self.output_dir = output_dir or "ui/components/generated"
        self.theme_dirs = theme_dirs or ["ui/themes"]
        
        # 缓存
        self.template_cache: Dict[str, Dict[str, Any]] = {}
        self.theme_cache: Dict[str, Dict[str, Any]] = {}
        
        # 配置
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载生成器配置"""
        config_path = Path("ui/config/generator.json")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _find_template(self, template_name: str, category: str = None) -> Optional[Path]:
        """查找模板文件"""
        for template_dir in self.template_dirs:
            template_dir_path = Path(template_dir)
            
            # 尝试不同的路径组合
            possible_paths = [
                template_dir_path / f"{template_name}.json",
                template_dir_path / f"{template_name}.yaml",
                template_dir_path / f"{template_name}.yml"
            ]
            
            if category:
                possible_paths.extend([
                    template_dir_path / category / f"{template_name}.json",
                    template_dir_path / category / f"{template_name}.yaml",
                    template_dir_path / category / f"{template_name}.yml"
                ])
            
            for path in possible_paths:
                if path.exists():
                    return path
        
        return None
    
    def _load_template(self, template_path: Path) -> Dict[str, Any]:
        """加载模板文件"""
        cache_key = str(template_path)
        
        if cache_key in self.template_cache:
            return self.template_cache[cache_key]
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                if template_path.suffix == '.json':
                    template = json.load(f)
                else:  # yaml/yml
                    template = yaml.safe_load(f)
            
            self.template_cache[cache_key] = template
            return template
            
        except Exception as e:
            logger.error(f"Failed to load template {template_path}: {e}")
            raise
    
    def _validate_template(self, template: Dict[str, Any]) -> List[str]:
        """验证模板格式"""
        errors = []
        
        # 检查必需字段
        required_fields = ['meta', 'schema', 'template']
        for field in required_fields:
            if field not in template:
                errors.append(f"Missing required field: {field}")
        
        # 检查meta字段
        if 'meta' in template:
            meta = template['meta']
            meta_required = ['name', 'version', 'description']
            for field in meta_required:
                if field not in meta:
                    errors.append(f"Missing required meta field: {field}")
        
        return errors
    
    def _resolve_dependencies(self, template: Dict[str, Any]) -> List[str]:
        """解析模板依赖"""
        dependencies = []
        
        if 'dependencies' in template:
            deps = template['dependencies']
            
            # 组件依赖
            if 'components' in deps:
                dependencies.extend(deps['components'])
            
            # 主题依赖
            if 'themes' in deps:
                dependencies.extend(deps['themes'])
        
        return dependencies
    
    def _create_output_dir(self, output_path: str) -> None:
        """创建输出目录"""
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
    
    def _write_output_file(
        self, 
        content: str, 
        output_path: str,
        minify: bool = False
    ) -> None:
        """写入输出文件"""
        self._create_output_dir(output_path)
        
        if minify:
            content = self._minify_content(content, output_path)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _minify_content(self, content: str, file_path: str) -> str:
        """压缩内容"""
        # 简单的压缩实现，可以根据文件类型进行优化
        if file_path.endswith('.css'):
            # CSS压缩
            import re
            content = re.sub(r'\s+', ' ', content)
            content = re.sub(r';\s*}', '}', content)
            content = re.sub(r'{\s*', '{', content)
            content = re.sub(r'}\s*', '}', content)
        elif file_path.endswith('.js'):
            # JavaScript压缩（简单版本）
            import re
            content = re.sub(r'\s+', ' ', content)
            content = re.sub(r';\s*', ';', content)
        
        return content.strip()
    
    @abstractmethod
    async def generate(self, config: GenerationConfig) -> GenerationResult:
        """生成内容 - 子类必须实现"""
        pass
    
    @abstractmethod
    def get_supported_templates(self) -> List[str]:
        """获取支持的模板列表 - 子类必须实现"""
        pass
    
    def validate_config(self, config: GenerationConfig) -> List[str]:
        """验证生成配置"""
        errors = []
        
        if not config.template_name:
            errors.append("Template name is required")
        
        if not config.output_path:
            errors.append("Output path is required")
        
        return errors
    
    async def generate_multiple(
        self, 
        configs: List[GenerationConfig]
    ) -> List[GenerationResult]:
        """批量生成"""
        results = []
        
        for config in configs:
            try:
                result = await self.generate(config)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to generate {config.template_name}: {e}")
                results.append(GenerationResult(
                    success=False,
                    output_files=[],
                    errors=[str(e)],
                    warnings=[],
                    metadata={}
                ))
        
        return results
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self.template_cache.clear()
        self.theme_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计"""
        return {
            "template_cache_size": len(self.template_cache),
            "theme_cache_size": len(self.theme_cache)
        }

