"""
PowerAutomation 4.0 配置验证器

负责验证配置的正确性、完整性和安全性，支持自定义验证规则和模式验证。
"""

import re
import logging
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import jsonschema
from jsonschema import validate, ValidationError


class ValidationType(Enum):
    """验证类型枚举"""
    REQUIRED = "required"
    TYPE = "type"
    RANGE = "range"
    PATTERN = "pattern"
    ENUM = "enum"
    CUSTOM = "custom"


@dataclass
class ValidationRule:
    """验证规则"""
    rule_id: str
    config_path: str
    validation_type: ValidationType
    rule_data: Any
    error_message: str = ""
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validated_paths: List[str] = field(default_factory=list)


class ConfigValidator:
    """
    PowerAutomation 4.0 配置验证器
    
    功能：
    1. 配置结构验证
    2. 数据类型验证
    3. 值范围验证
    4. 模式匹配验证
    5. 自定义验证规则
    """
    
    def __init__(self):
        """初始化配置验证器"""
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        
        # 验证规则
        self.validation_rules: Dict[str, ValidationRule] = {}
        
        # JSON Schema
        self.json_schema: Optional[Dict[str, Any]] = None
        
        # 自定义验证器
        self.custom_validators: Dict[str, Callable] = {}
        
        self.logger.info("配置验证器初始化完成")
    
    async def start(self) -> None:
        """启动配置验证器"""
        if self.is_running:
            return
        
        try:
            self.logger.info("启动配置验证器...")
            
            # 加载默认验证规则
            await self._load_default_rules()
            
            # 加载JSON Schema
            await self._load_json_schema()
            
            # 注册默认自定义验证器
            await self._register_default_validators()
            
            self.is_running = True
            self.logger.info("配置验证器启动成功")
            
        except Exception as e:
            self.logger.error(f"配置验证器启动失败: {e}")
            raise
    
    async def stop(self) -> None:
        """停止配置验证器"""
        if not self.is_running:
            return
        
        try:
            self.logger.info("停止配置验证器...")
            
            self.is_running = False
            
            # 清理资源
            self.validation_rules.clear()
            self.custom_validators.clear()
            
            self.logger.info("配置验证器已停止")
            
        except Exception as e:
            self.logger.error(f"配置验证器停止时出错: {e}")
    
    async def validate(self, config_data: Dict[str, Any]) -> bool:
        """
        验证配置
        
        Args:
            config_data: 配置数据
            
        Returns:
            bool: 验证是否通过
        """
        try:
            result = await self.validate_detailed(config_data)
            return result.is_valid
            
        except Exception as e:
            self.logger.error(f"配置验证失败: {e}")
            return False
    
    async def validate_detailed(self, config_data: Dict[str, Any]) -> ValidationResult:
        """
        详细验证配置
        
        Args:
            config_data: 配置数据
            
        Returns:
            ValidationResult: 详细验证结果
        """
        try:
            result = ValidationResult(is_valid=True)
            
            # JSON Schema验证
            if self.json_schema:
                schema_result = await self._validate_with_schema(config_data)
                result.errors.extend(schema_result.errors)
                result.warnings.extend(schema_result.warnings)
                if not schema_result.is_valid:
                    result.is_valid = False
            
            # 规则验证
            rules_result = await self._validate_with_rules(config_data)
            result.errors.extend(rules_result.errors)
            result.warnings.extend(rules_result.warnings)
            result.validated_paths.extend(rules_result.validated_paths)
            if not rules_result.is_valid:
                result.is_valid = False
            
            # 记录验证结果
            if result.is_valid:
                self.logger.info("配置验证通过")
            else:
                self.logger.error(f"配置验证失败: {len(result.errors)} 个错误")
                for error in result.errors:
                    self.logger.error(f"  - {error}")
            
            if result.warnings:
                self.logger.warning(f"配置验证警告: {len(result.warnings)} 个警告")
                for warning in result.warnings:
                    self.logger.warning(f"  - {warning}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"详细配置验证失败: {e}")
            return ValidationResult(is_valid=False, errors=[str(e)])
    
    async def add_validation_rule(self, rule: ValidationRule) -> bool:
        """
        添加验证规则
        
        Args:
            rule: 验证规则
            
        Returns:
            bool: 添加是否成功
        """
        try:
            self.validation_rules[rule.rule_id] = rule
            self.logger.info(f"添加验证规则: {rule.rule_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加验证规则失败: {e}")
            return False
    
    async def remove_validation_rule(self, rule_id: str) -> bool:
        """
        移除验证规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            bool: 移除是否成功
        """
        try:
            if rule_id in self.validation_rules:
                del self.validation_rules[rule_id]
                self.logger.info(f"移除验证规则: {rule_id}")
                return True
            else:
                self.logger.warning(f"验证规则不存在: {rule_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"移除验证规则失败: {e}")
            return False
    
    async def set_json_schema(self, schema: Dict[str, Any]) -> bool:
        """
        设置JSON Schema
        
        Args:
            schema: JSON Schema
            
        Returns:
            bool: 设置是否成功
        """
        try:
            # 验证schema本身的有效性
            jsonschema.Draft7Validator.check_schema(schema)
            
            self.json_schema = schema
            self.logger.info("设置JSON Schema成功")
            return True
            
        except Exception as e:
            self.logger.error(f"设置JSON Schema失败: {e}")
            return False
    
    def register_custom_validator(self, name: str, validator: Callable) -> bool:
        """
        注册自定义验证器
        
        Args:
            name: 验证器名称
            validator: 验证器函数
            
        Returns:
            bool: 注册是否成功
        """
        try:
            self.custom_validators[name] = validator
            self.logger.info(f"注册自定义验证器: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"注册自定义验证器失败: {e}")
            return False
    
    def get_validation_rules(self) -> List[ValidationRule]:
        """获取所有验证规则"""
        return list(self.validation_rules.values())
    
    async def _validate_with_schema(self, config_data: Dict[str, Any]) -> ValidationResult:
        """使用JSON Schema验证"""
        try:
            validate(instance=config_data, schema=self.json_schema)
            return ValidationResult(is_valid=True)
            
        except ValidationError as e:
            error_msg = f"Schema验证失败: {e.message}"
            if e.absolute_path:
                error_msg += f" (路径: {'.'.join(str(p) for p in e.absolute_path)})"
            
            return ValidationResult(is_valid=False, errors=[error_msg])
            
        except Exception as e:
            return ValidationResult(is_valid=False, errors=[f"Schema验证异常: {e}"])
    
    async def _validate_with_rules(self, config_data: Dict[str, Any]) -> ValidationResult:
        """使用验证规则验证"""
        result = ValidationResult(is_valid=True)
        
        try:
            for rule in self.validation_rules.values():
                if not rule.enabled:
                    continue
                
                rule_result = await self._validate_single_rule(config_data, rule)
                
                if not rule_result.is_valid:
                    result.is_valid = False
                    result.errors.extend(rule_result.errors)
                
                result.warnings.extend(rule_result.warnings)
                result.validated_paths.append(rule.config_path)
            
            return result
            
        except Exception as e:
            return ValidationResult(is_valid=False, errors=[f"规则验证异常: {e}"])
    
    async def _validate_single_rule(self, config_data: Dict[str, Any], 
                                   rule: ValidationRule) -> ValidationResult:
        """验证单个规则"""
        try:
            # 获取配置值
            value = self._get_config_value(config_data, rule.config_path)
            
            # 根据验证类型执行验证
            if rule.validation_type == ValidationType.REQUIRED:
                return await self._validate_required(value, rule)
            elif rule.validation_type == ValidationType.TYPE:
                return await self._validate_type(value, rule)
            elif rule.validation_type == ValidationType.RANGE:
                return await self._validate_range(value, rule)
            elif rule.validation_type == ValidationType.PATTERN:
                return await self._validate_pattern(value, rule)
            elif rule.validation_type == ValidationType.ENUM:
                return await self._validate_enum(value, rule)
            elif rule.validation_type == ValidationType.CUSTOM:
                return await self._validate_custom(value, rule)
            else:
                return ValidationResult(is_valid=False, errors=[f"未知验证类型: {rule.validation_type}"])
                
        except Exception as e:
            error_msg = rule.error_message or f"规则验证失败: {e}"
            return ValidationResult(is_valid=False, errors=[error_msg])
    
    async def _validate_required(self, value: Any, rule: ValidationRule) -> ValidationResult:
        """验证必需字段"""
        if value is None:
            error_msg = rule.error_message or f"必需字段缺失: {rule.config_path}"
            return ValidationResult(is_valid=False, errors=[error_msg])
        
        return ValidationResult(is_valid=True)
    
    async def _validate_type(self, value: Any, rule: ValidationRule) -> ValidationResult:
        """验证数据类型"""
        if value is None:
            return ValidationResult(is_valid=True)  # None值跳过类型检查
        
        expected_type = rule.rule_data
        
        # 处理类型名称字符串
        if isinstance(expected_type, str):
            type_map = {
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict
            }
            expected_type = type_map.get(expected_type, str)
        
        if not isinstance(value, expected_type):
            error_msg = rule.error_message or f"类型错误: {rule.config_path} 期望 {expected_type.__name__}, 实际 {type(value).__name__}"
            return ValidationResult(is_valid=False, errors=[error_msg])
        
        return ValidationResult(is_valid=True)
    
    async def _validate_range(self, value: Any, rule: ValidationRule) -> ValidationResult:
        """验证值范围"""
        if value is None:
            return ValidationResult(is_valid=True)
        
        range_data = rule.rule_data
        min_val = range_data.get("min")
        max_val = range_data.get("max")
        
        try:
            if min_val is not None and value < min_val:
                error_msg = rule.error_message or f"值过小: {rule.config_path} = {value}, 最小值 {min_val}"
                return ValidationResult(is_valid=False, errors=[error_msg])
            
            if max_val is not None and value > max_val:
                error_msg = rule.error_message or f"值过大: {rule.config_path} = {value}, 最大值 {max_val}"
                return ValidationResult(is_valid=False, errors=[error_msg])
            
            return ValidationResult(is_valid=True)
            
        except TypeError:
            error_msg = rule.error_message or f"范围验证失败: {rule.config_path} 值不支持比较"
            return ValidationResult(is_valid=False, errors=[error_msg])
    
    async def _validate_pattern(self, value: Any, rule: ValidationRule) -> ValidationResult:
        """验证模式匹配"""
        if value is None:
            return ValidationResult(is_valid=True)
        
        if not isinstance(value, str):
            error_msg = rule.error_message or f"模式验证失败: {rule.config_path} 不是字符串"
            return ValidationResult(is_valid=False, errors=[error_msg])
        
        pattern = rule.rule_data
        
        try:
            if not re.match(pattern, value):
                error_msg = rule.error_message or f"模式不匹配: {rule.config_path} = '{value}' 不匹配模式 '{pattern}'"
                return ValidationResult(is_valid=False, errors=[error_msg])
            
            return ValidationResult(is_valid=True)
            
        except re.error as e:
            error_msg = rule.error_message or f"正则表达式错误: {e}"
            return ValidationResult(is_valid=False, errors=[error_msg])
    
    async def _validate_enum(self, value: Any, rule: ValidationRule) -> ValidationResult:
        """验证枚举值"""
        if value is None:
            return ValidationResult(is_valid=True)
        
        allowed_values = rule.rule_data
        
        if value not in allowed_values:
            error_msg = rule.error_message or f"值不在允许范围内: {rule.config_path} = {value}, 允许值 {allowed_values}"
            return ValidationResult(is_valid=False, errors=[error_msg])
        
        return ValidationResult(is_valid=True)
    
    async def _validate_custom(self, value: Any, rule: ValidationRule) -> ValidationResult:
        """验证自定义规则"""
        validator_name = rule.rule_data
        
        if validator_name not in self.custom_validators:
            error_msg = f"自定义验证器不存在: {validator_name}"
            return ValidationResult(is_valid=False, errors=[error_msg])
        
        try:
            validator = self.custom_validators[validator_name]
            is_valid = await validator(value, rule) if asyncio.iscoroutinefunction(validator) else validator(value, rule)
            
            if not is_valid:
                error_msg = rule.error_message or f"自定义验证失败: {rule.config_path}"
                return ValidationResult(is_valid=False, errors=[error_msg])
            
            return ValidationResult(is_valid=True)
            
        except Exception as e:
            error_msg = rule.error_message or f"自定义验证异常: {e}"
            return ValidationResult(is_valid=False, errors=[error_msg])
    
    def _get_config_value(self, config_data: Dict[str, Any], path: str) -> Any:
        """获取配置值"""
        keys = path.split('.')
        current = config_data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    async def _load_default_rules(self) -> None:
        """加载默认验证规则"""
        try:
            # MCP协调器相关规则
            rules = [
                ValidationRule(
                    rule_id="mcp_coordinator_host_required",
                    config_path="mcp.coordinator.host",
                    validation_type=ValidationType.REQUIRED,
                    rule_data=True,
                    error_message="MCP协调器主机地址是必需的"
                ),
                ValidationRule(
                    rule_id="mcp_coordinator_port_type",
                    config_path="mcp.coordinator.port",
                    validation_type=ValidationType.TYPE,
                    rule_data=int,
                    error_message="MCP协调器端口必须是整数"
                ),
                ValidationRule(
                    rule_id="mcp_coordinator_port_range",
                    config_path="mcp.coordinator.port",
                    validation_type=ValidationType.RANGE,
                    rule_data={"min": 1024, "max": 65535},
                    error_message="MCP协调器端口必须在1024-65535范围内"
                ),
                
                # 日志级别规则
                ValidationRule(
                    rule_id="log_level_enum",
                    config_path="logging.level",
                    validation_type=ValidationType.ENUM,
                    rule_data=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                    error_message="日志级别必须是有效值"
                ),
                
                # 数据库连接规则
                ValidationRule(
                    rule_id="database_url_pattern",
                    config_path="database.url",
                    validation_type=ValidationType.PATTERN,
                    rule_data=r"^(sqlite|postgresql|mysql)://.*",
                    error_message="数据库URL格式不正确"
                ),
                
                # Redis连接规则
                ValidationRule(
                    rule_id="redis_host_required",
                    config_path="redis.host",
                    validation_type=ValidationType.REQUIRED,
                    rule_data=True,
                    error_message="Redis主机地址是必需的"
                ),
                ValidationRule(
                    rule_id="redis_port_range",
                    config_path="redis.port",
                    validation_type=ValidationType.RANGE,
                    rule_data={"min": 1, "max": 65535},
                    error_message="Redis端口必须在1-65535范围内"
                )
            ]
            
            for rule in rules:
                await self.add_validation_rule(rule)
            
            self.logger.info(f"加载了 {len(rules)} 个默认验证规则")
            
        except Exception as e:
            self.logger.error(f"加载默认验证规则失败: {e}")
    
    async def _load_json_schema(self) -> None:
        """加载JSON Schema"""
        try:
            # PowerAutomation 4.0 配置的JSON Schema
            schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "PowerAutomation 4.0 Configuration",
                "type": "object",
                "properties": {
                    "mcp": {
                        "type": "object",
                        "properties": {
                            "coordinator": {
                                "type": "object",
                                "properties": {
                                    "host": {"type": "string"},
                                    "port": {"type": "integer", "minimum": 1024, "maximum": 65535},
                                    "max_connections": {"type": "integer", "minimum": 1}
                                },
                                "required": ["host", "port"]
                            }
                        }
                    },
                    "logging": {
                        "type": "object",
                        "properties": {
                            "level": {
                                "type": "string",
                                "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                            },
                            "format": {"type": "string"},
                            "file": {"type": "string"}
                        }
                    },
                    "database": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string"},
                            "pool_size": {"type": "integer", "minimum": 1},
                            "timeout": {"type": "number", "minimum": 0}
                        }
                    },
                    "redis": {
                        "type": "object",
                        "properties": {
                            "host": {"type": "string"},
                            "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                            "password": {"type": "string"},
                            "db": {"type": "integer", "minimum": 0}
                        }
                    }
                }
            }
            
            await self.set_json_schema(schema)
            
        except Exception as e:
            self.logger.error(f"加载JSON Schema失败: {e}")
    
    async def _register_default_validators(self) -> None:
        """注册默认自定义验证器"""
        try:
            # URL验证器
            def validate_url(value: Any, rule: ValidationRule) -> bool:
                if not isinstance(value, str):
                    return False
                
                import urllib.parse
                try:
                    result = urllib.parse.urlparse(value)
                    return all([result.scheme, result.netloc])
                except:
                    return False
            
            # 邮箱验证器
            def validate_email(value: Any, rule: ValidationRule) -> bool:
                if not isinstance(value, str):
                    return False
                
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                return re.match(email_pattern, value) is not None
            
            # IP地址验证器
            def validate_ip(value: Any, rule: ValidationRule) -> bool:
                if not isinstance(value, str):
                    return False
                
                import ipaddress
                try:
                    ipaddress.ip_address(value)
                    return True
                except:
                    return False
            
            # 注册验证器
            self.register_custom_validator("url", validate_url)
            self.register_custom_validator("email", validate_email)
            self.register_custom_validator("ip", validate_ip)
            
            self.logger.info("注册默认自定义验证器完成")
            
        except Exception as e:
            self.logger.error(f"注册默认自定义验证器失败: {e}")


# 导入asyncio用于异步操作
import asyncio

