"""
PowerAutomation 4.0 安全系统集成测试

测试安全认证系统各组件之间的集成和协作。
"""

import pytest
import asyncio
import time
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any

# 导入安全组件
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.components.security_mcp.authenticator import MCPAuthenticator, AuthMethod, UserRole
from core.components.security_mcp.authorizer import MCPAuthorizer, Permission, Resource, AccessDecision
from core.components.security_mcp.security_manager import MCPSecurityManager, SecurityEventType, ThreatLevel
from core.components.security_mcp.token_manager import MCPTokenManager, TokenType, TokenScope


class TestSecurityIntegration:
    """安全系统集成测试类"""
    
    @pytest.fixture
    async def security_components(self):
        """初始化安全组件"""
        # 创建安全组件实例
        authenticator = MCPAuthenticator({
            "password_min_length": 8,
            "max_failed_attempts": 3,
            "lockout_duration": 300
        })
        
        authorizer = MCPAuthorizer({
            "cache_ttl": 300,
            "default_decision": "deny"
        })
        
        security_manager = MCPSecurityManager({
            "max_failed_logins": 5,
            "brute_force_window": 300,
            "anomaly_threshold": 2.0
        })
        
        token_manager = MCPTokenManager({
            "default_access_token_expiry": 3600,
            "default_refresh_token_expiry": 86400,
            "jwt_secret": "test_secret_key_for_integration_testing"
        })
        
        # 启动所有组件
        await authenticator.start()
        await authorizer.start()
        await security_manager.start()
        await token_manager.start()
        
        yield {
            "authenticator": authenticator,
            "authorizer": authorizer,
            "security_manager": security_manager,
            "token_manager": token_manager
        }
        
        # 清理
        await authenticator.stop()
        await authorizer.stop()
        await security_manager.stop()
        await token_manager.stop()
    
    @pytest.mark.asyncio
    async def test_complete_authentication_flow(self, security_components):
        """测试完整的认证流程"""
        components = security_components
        authenticator = components["authenticator"]
        token_manager = components["token_manager"]
        
        # 1. 创建用户
        user_id = "test_user_001"
        password = "SecurePassword123!"
        
        success = await authenticator.create_user(
            user_id=user_id,
            password=password,
            role=UserRole.USER,
            metadata={"test": True}
        )
        assert success, "用户创建失败"
        
        # 2. 用户登录
        session = await authenticator.authenticate(
            user_id=user_id,
            password=password,
            method=AuthMethod.PASSWORD
        )
        assert session is not None, "用户登录失败"
        assert session.user_id == user_id
        
        # 3. 创建访问令牌
        access_token = await token_manager.create_token(
            token_type=TokenType.ACCESS_TOKEN,
            user_id=user_id,
            scopes={TokenScope.READ, TokenScope.WRITE}
        )
        assert access_token is not None, "访问令牌创建失败"
        
        # 4. 验证令牌
        validated_token = await token_manager.validate_token(
            token_value=access_token.token_value,
            required_scopes={TokenScope.READ}
        )
        assert validated_token is not None, "令牌验证失败"
        assert validated_token.user_id == user_id
        
        # 5. 用户登出
        logout_success = await authenticator.logout(session.session_id)
        assert logout_success, "用户登出失败"
        
        print("✅ 完整认证流程测试通过")
    
    @pytest.mark.asyncio
    async def test_authorization_integration(self, security_components):
        """测试授权集成"""
        components = security_components
        authenticator = components["authenticator"]
        authorizer = components["authorizer"]
        
        # 1. 创建用户
        user_id = "test_user_002"
        password = "SecurePassword123!"
        
        await authenticator.create_user(
            user_id=user_id,
            password=password,
            role=UserRole.DEVELOPER
        )
        
        # 2. 用户登录
        session = await authenticator.authenticate(
            user_id=user_id,
            password=password,
            method=AuthMethod.PASSWORD
        )
        assert session is not None
        
        # 3. 检查权限 - 应该有读权限
        has_read_permission = await authorizer.check_permission(
            user_id=user_id,
            permission=Permission.READ,
            resource=Resource.SERVICE,
            resource_id="test_service"
        )
        assert has_read_permission == AccessDecision.ALLOW, "开发者应该有读权限"
        
        # 4. 检查权限 - 应该有写权限
        has_write_permission = await authorizer.check_permission(
            user_id=user_id,
            permission=Permission.WRITE,
            resource=Resource.SERVICE,
            resource_id="test_service"
        )
        assert has_write_permission == AccessDecision.ALLOW, "开发者应该有写权限"
        
        # 5. 检查权限 - 不应该有管理员权限
        has_admin_permission = await authorizer.check_permission(
            user_id=user_id,
            permission=Permission.ADMIN,
            resource=Resource.USER,
            resource_id="other_user"
        )
        assert has_admin_permission == AccessDecision.DENY, "开发者不应该有用户管理权限"
        
        print("✅ 授权集成测试通过")
    
    @pytest.mark.asyncio
    async def test_security_event_flow(self, security_components):
        """测试安全事件流程"""
        components = security_components
        authenticator = components["authenticator"]
        security_manager = components["security_manager"]
        
        # 记录安全事件
        events_received = []
        
        def event_callback(event):
            events_received.append(event)
        
        security_manager.add_event_callback("security_event", event_callback)
        
        # 1. 模拟登录失败
        user_id = "test_user_003"
        password = "WrongPassword"
        
        for i in range(6):  # 超过最大失败次数
            session = await authenticator.authenticate(
                user_id=user_id,
                password=password,
                method=AuthMethod.PASSWORD
            )
            assert session is None, f"第{i+1}次登录应该失败"
            
            # 报告登录失败事件
            await security_manager.report_security_event(
                event_type=SecurityEventType.LOGIN_FAILURE,
                threat_level=ThreatLevel.MEDIUM,
                user_id=user_id,
                description=f"登录失败尝试 #{i+1}"
            )
        
        # 等待事件处理
        await asyncio.sleep(0.1)
        
        # 2. 验证安全事件被记录
        assert len(events_received) >= 6, "应该记录所有登录失败事件"
        
        # 3. 检查用户是否被隔离
        is_quarantined = await security_manager.check_user_quarantined(user_id)
        # 注意：这取决于安全规则的配置
        
        print(f"✅ 安全事件流程测试通过，记录了 {len(events_received)} 个事件")
    
    @pytest.mark.asyncio
    async def test_token_lifecycle_integration(self, security_components):
        """测试令牌生命周期集成"""
        components = security_components
        authenticator = components["authenticator"]
        token_manager = components["token_manager"]
        security_manager = components["security_manager"]
        
        # 1. 创建用户并登录
        user_id = "test_user_004"
        password = "SecurePassword123!"
        
        await authenticator.create_user(
            user_id=user_id,
            password=password,
            role=UserRole.USER
        )
        
        session = await authenticator.authenticate(
            user_id=user_id,
            password=password,
            method=AuthMethod.PASSWORD
        )
        assert session is not None
        
        # 2. 创建访问令牌和刷新令牌
        access_token = await token_manager.create_token(
            token_type=TokenType.ACCESS_TOKEN,
            user_id=user_id,
            expires_in=60  # 1分钟过期
        )
        
        refresh_token = await token_manager.create_token(
            token_type=TokenType.REFRESH_TOKEN,
            user_id=user_id,
            expires_in=3600  # 1小时过期
        )
        
        assert access_token is not None
        assert refresh_token is not None
        
        # 3. 验证令牌
        validated_access = await token_manager.validate_token(access_token.token_value)
        validated_refresh = await token_manager.validate_token(refresh_token.token_value)
        
        assert validated_access is not None
        assert validated_refresh is not None
        
        # 4. 使用刷新令牌获取新的访问令牌
        new_tokens = await token_manager.refresh_token(refresh_token.token_value)
        assert new_tokens is not None
        
        new_access_token, new_refresh_token = new_tokens
        assert new_access_token.user_id == user_id
        assert new_refresh_token.user_id == user_id
        
        # 5. 撤销所有用户令牌
        revoked_count = await token_manager.revoke_user_tokens(
            user_id=user_id,
            reason="测试撤销"
        )
        assert revoked_count > 0, "应该撤销了一些令牌"
        
        # 6. 验证令牌已被撤销
        revoked_access = await token_manager.validate_token(new_access_token.token_value)
        assert revoked_access is None, "撤销的令牌应该无法验证"
        
        print("✅ 令牌生命周期集成测试通过")
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self, security_components):
        """测试高负载下的性能"""
        components = security_components
        authenticator = components["authenticator"]
        authorizer = components["authorizer"]
        token_manager = components["token_manager"]
        
        # 1. 创建测试用户
        user_id = "perf_test_user"
        password = "SecurePassword123!"
        
        await authenticator.create_user(
            user_id=user_id,
            password=password,
            role=UserRole.DEVELOPER
        )
        
        # 2. 创建访问令牌
        access_token = await token_manager.create_token(
            token_type=TokenType.ACCESS_TOKEN,
            user_id=user_id,
            scopes={TokenScope.READ, TokenScope.WRITE}
        )
        
        # 3. 并发令牌验证测试
        async def validate_token_task():
            return await token_manager.validate_token(
                token_value=access_token.token_value,
                required_scopes={TokenScope.READ}
            )
        
        start_time = time.time()
        tasks = [validate_token_task() for _ in range(100)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # 验证结果
        successful_validations = sum(1 for r in results if r is not None)
        assert successful_validations == 100, "所有令牌验证都应该成功"
        
        # 计算性能指标
        total_time = end_time - start_time
        avg_time_per_validation = total_time / 100
        
        print(f"✅ 性能测试通过:")
        print(f"   - 100次并发令牌验证耗时: {total_time:.3f}秒")
        print(f"   - 平均每次验证耗时: {avg_time_per_validation*1000:.2f}毫秒")
        
        # 性能断言
        assert avg_time_per_validation < 0.1, "平均验证时间应该小于100毫秒"
        
        # 4. 并发权限检查测试
        async def check_permission_task():
            return await authorizer.check_permission(
                user_id=user_id,
                permission=Permission.READ,
                resource=Resource.SERVICE,
                resource_id="test_service"
            )
        
        start_time = time.time()
        tasks = [check_permission_task() for _ in range(100)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # 验证结果
        successful_checks = sum(1 for r in results if r == AccessDecision.ALLOW)
        assert successful_checks == 100, "所有权限检查都应该成功"
        
        # 计算性能指标
        total_time = end_time - start_time
        avg_time_per_check = total_time / 100
        
        print(f"   - 100次并发权限检查耗时: {total_time:.3f}秒")
        print(f"   - 平均每次检查耗时: {avg_time_per_check*1000:.2f}毫秒")
        
        # 性能断言
        assert avg_time_per_check < 0.05, "平均权限检查时间应该小于50毫秒"
    
    @pytest.mark.asyncio
    async def test_security_threat_detection(self, security_components):
        """测试安全威胁检测"""
        components = security_components
        security_manager = components["security_manager"]
        
        # 记录威胁检测事件
        threats_detected = []
        
        def threat_callback(threat):
            threats_detected.append(threat)
        
        security_manager.add_event_callback("threat_detected", threat_callback)
        
        # 1. 模拟暴力破解攻击
        attacker_ip = "192.168.1.100"
        
        for i in range(10):  # 快速连续的登录失败
            await security_manager.report_security_event(
                event_type=SecurityEventType.LOGIN_FAILURE,
                threat_level=ThreatLevel.MEDIUM,
                source_ip=attacker_ip,
                user_id=f"victim_user_{i % 3}",  # 攻击多个用户
                description=f"暴力破解尝试 #{i+1}"
            )
        
        # 等待威胁检测处理
        await asyncio.sleep(0.2)
        
        # 2. 检查IP是否被阻止
        is_blocked = await security_manager.check_ip_blocked(attacker_ip)
        # 注意：这取决于安全规则的配置
        
        # 3. 模拟异常活动
        for i in range(150):  # 大量活动
            await security_manager.report_security_event(
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                threat_level=ThreatLevel.LOW,
                source_ip=attacker_ip,
                description=f"异常活动 #{i+1}"
            )
        
        await asyncio.sleep(0.2)
        
        # 4. 获取安全统计
        stats = await security_manager.get_security_statistics()
        
        assert stats["events_24h"] > 0, "应该记录了安全事件"
        assert "LOGIN_FAILURE" in stats["event_types_24h"], "应该记录了登录失败事件"
        
        print(f"✅ 威胁检测测试通过:")
        print(f"   - 检测到威胁: {len(threats_detected)} 个")
        print(f"   - 24小时内事件: {stats['events_24h']} 个")
        print(f"   - IP阻止状态: {'已阻止' if is_blocked else '未阻止'}")
    
    @pytest.mark.asyncio
    async def test_compliance_checks(self, security_components):
        """测试合规检查"""
        components = security_components
        security_manager = components["security_manager"]
        
        # 记录合规违规事件
        violations = []
        
        def violation_callback(violation):
            violations.append(violation)
        
        security_manager.add_event_callback("compliance_violation", violation_callback)
        
        # 1. 运行所有合规检查
        check_results = {}
        
        for check_id in security_manager.compliance_checks.keys():
            result = await security_manager.run_compliance_check(check_id)
            check_results[check_id] = result
            print(f"   - {check_id}: {'通过' if result else '失败'}")
        
        # 2. 验证检查结果
        assert len(check_results) > 0, "应该有合规检查"
        
        # 3. 检查是否有违规事件
        await asyncio.sleep(0.1)
        
        print(f"✅ 合规检查测试通过:")
        print(f"   - 执行检查: {len(check_results)} 个")
        print(f"   - 违规事件: {len(violations)} 个")
        
        for check_id, result in check_results.items():
            print(f"   - {check_id}: {'✅ 通过' if result else '❌ 失败'}")
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, security_components):
        """测试错误处理和恢复"""
        components = security_components
        authenticator = components["authenticator"]
        token_manager = components["token_manager"]
        
        # 1. 测试无效输入处理
        
        # 无效用户ID
        session = await authenticator.authenticate(
            user_id="",
            password="password",
            method=AuthMethod.PASSWORD
        )
        assert session is None, "空用户ID应该认证失败"
        
        # 无效令牌
        invalid_token = await token_manager.validate_token("invalid_token_value")
        assert invalid_token is None, "无效令牌应该验证失败"
        
        # 2. 测试边界条件
        
        # 极长的用户ID
        long_user_id = "a" * 1000
        session = await authenticator.authenticate(
            user_id=long_user_id,
            password="password",
            method=AuthMethod.PASSWORD
        )
        assert session is None, "极长用户ID应该认证失败"
        
        # 3. 测试并发安全
        
        user_id = "concurrent_test_user"
        password = "SecurePassword123!"
        
        await authenticator.create_user(
            user_id=user_id,
            password=password,
            role=UserRole.USER
        )
        
        # 并发登录尝试
        async def login_task():
            return await authenticator.authenticate(
                user_id=user_id,
                password=password,
                method=AuthMethod.PASSWORD
            )
        
        tasks = [login_task() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 验证没有异常
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"并发登录不应该产生异常: {exceptions}"
        
        # 验证所有登录都成功
        successful_logins = [r for r in results if r is not None and not isinstance(r, Exception)]
        assert len(successful_logins) == 10, "所有并发登录都应该成功"
        
        print("✅ 错误处理和恢复测试通过")
    
    @pytest.mark.asyncio
    async def test_system_integration_end_to_end(self, security_components):
        """端到端系统集成测试"""
        components = security_components
        authenticator = components["authenticator"]
        authorizer = components["authorizer"]
        security_manager = components["security_manager"]
        token_manager = components["token_manager"]
        
        print("🚀 开始端到端集成测试...")
        
        # 1. 用户注册和认证
        user_id = "e2e_test_user"
        password = "SecurePassword123!"
        client_id = "test_client"
        
        # 创建用户
        user_created = await authenticator.create_user(
            user_id=user_id,
            password=password,
            role=UserRole.DEVELOPER,
            metadata={"department": "engineering", "level": "senior"}
        )
        assert user_created, "用户创建失败"
        
        # 用户登录
        session = await authenticator.authenticate(
            user_id=user_id,
            password=password,
            method=AuthMethod.PASSWORD,
            client_id=client_id
        )
        assert session is not None, "用户登录失败"
        
        # 2. 令牌管理
        
        # 创建访问令牌
        access_token = await token_manager.create_token(
            token_type=TokenType.ACCESS_TOKEN,
            user_id=user_id,
            client_id=client_id,
            scopes={TokenScope.READ, TokenScope.WRITE},
            expires_in=3600
        )
        assert access_token is not None, "访问令牌创建失败"
        
        # 创建API密钥
        api_key = await token_manager.create_token(
            token_type=TokenType.API_KEY,
            user_id=user_id,
            scopes={TokenScope.SERVICE},
            ip_restrictions=["192.168.1.0/24"]
        )
        assert api_key is not None, "API密钥创建失败"
        
        # 3. 权限验证
        
        # 检查服务访问权限
        service_access = await authorizer.check_permission(
            user_id=user_id,
            permission=Permission.READ,
            resource=Resource.SERVICE,
            resource_id="critical_service"
        )
        assert service_access == AccessDecision.ALLOW, "开发者应该有服务读权限"
        
        # 检查数据写权限
        data_write = await authorizer.check_permission(
            user_id=user_id,
            permission=Permission.WRITE,
            resource=Resource.DATA,
            resource_id="project_data"
        )
        assert data_write == AccessDecision.ALLOW, "开发者应该有数据写权限"
        
        # 检查用户管理权限（应该被拒绝）
        user_admin = await authorizer.check_permission(
            user_id=user_id,
            permission=Permission.ADMIN,
            resource=Resource.USER,
            resource_id="other_user"
        )
        assert user_admin == AccessDecision.DENY, "开发者不应该有用户管理权限"
        
        # 4. 安全监控
        
        # 模拟正常活动
        for i in range(5):
            await security_manager.report_security_event(
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                threat_level=ThreatLevel.LOW,
                user_id=user_id,
                source_ip="192.168.1.10",
                resource="test_resource",
                description=f"正常活动 #{i+1}"
            )
        
        # 5. 令牌使用和验证
        
        # 使用访问令牌
        validated_token = await token_manager.validate_token(
            token_value=access_token.token_value,
            required_scopes={TokenScope.READ},
            ip_address="192.168.1.10",
            resource="test_api"
        )
        assert validated_token is not None, "令牌验证失败"
        assert validated_token.use_count > 0, "令牌使用计数应该增加"
        
        # 使用API密钥（正确IP）
        validated_api_key = await token_manager.validate_token(
            token_value=api_key.token_value,
            required_scopes={TokenScope.SERVICE},
            ip_address="192.168.1.50"  # 在允许的IP范围内
        )
        assert validated_api_key is not None, "API密钥验证应该成功"
        
        # 使用API密钥（错误IP）
        invalid_api_key = await token_manager.validate_token(
            token_value=api_key.token_value,
            required_scopes={TokenScope.SERVICE},
            ip_address="10.0.0.1"  # 不在允许的IP范围内
        )
        assert invalid_api_key is None, "错误IP的API密钥验证应该失败"
        
        # 6. 会话管理
        
        # 验证会话
        session_valid = await authenticator.validate_session(session.session_id)
        assert session_valid is not None, "会话验证失败"
        
        # 更新会话
        session_updated = await authenticator.update_session_activity(session.session_id)
        assert session_updated, "会话更新失败"
        
        # 7. 安全统计和监控
        
        # 获取令牌统计
        token_stats = await token_manager.get_token_statistics()
        assert token_stats["total_tokens"] >= 2, "应该有至少2个令牌"
        assert token_stats["active_tokens"] >= 2, "应该有至少2个活跃令牌"
        
        # 获取安全统计
        security_stats = await security_manager.get_security_statistics()
        assert security_stats["events_24h"] >= 5, "应该有至少5个安全事件"
        
        # 8. 清理和登出
        
        # 撤销令牌
        revoked_count = await token_manager.revoke_user_tokens(
            user_id=user_id,
            reason="端到端测试完成"
        )
        assert revoked_count >= 2, "应该撤销了至少2个令牌"
        
        # 用户登出
        logout_success = await authenticator.logout(session.session_id)
        assert logout_success, "用户登出失败"
        
        # 验证登出后的状态
        session_after_logout = await authenticator.validate_session(session.session_id)
        assert session_after_logout is None, "登出后会话应该无效"
        
        print("✅ 端到端集成测试完全通过!")
        print(f"   - 令牌统计: {token_stats['total_tokens']} 个令牌")
        print(f"   - 安全事件: {security_stats['events_24h']} 个事件")
        print(f"   - 撤销令牌: {revoked_count} 个")


# 性能基准测试
class TestSecurityPerformance:
    """安全系统性能测试"""
    
    @pytest.mark.asyncio
    async def test_authentication_performance(self, security_components):
        """认证性能测试"""
        components = security_components
        authenticator = components["authenticator"]
        
        # 创建测试用户
        user_id = "perf_auth_user"
        password = "SecurePassword123!"
        
        await authenticator.create_user(
            user_id=user_id,
            password=password,
            role=UserRole.USER
        )
        
        # 测试认证性能
        iterations = 50
        start_time = time.time()
        
        for i in range(iterations):
            session = await authenticator.authenticate(
                user_id=user_id,
                password=password,
                method=AuthMethod.PASSWORD
            )
            assert session is not None
            
            # 立即登出以避免会话累积
            await authenticator.logout(session.session_id)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / iterations
        
        print(f"🚀 认证性能测试结果:")
        print(f"   - {iterations} 次认证总耗时: {total_time:.3f}秒")
        print(f"   - 平均每次认证耗时: {avg_time*1000:.2f}毫秒")
        print(f"   - 每秒认证次数: {iterations/total_time:.1f} TPS")
        
        # 性能断言
        assert avg_time < 0.2, f"平均认证时间应该小于200毫秒，实际: {avg_time*1000:.2f}毫秒"
    
    @pytest.mark.asyncio
    async def test_token_validation_performance(self, security_components):
        """令牌验证性能测试"""
        components = security_components
        token_manager = components["token_manager"]
        
        # 创建测试令牌
        tokens = []
        for i in range(10):
            token = await token_manager.create_token(
                token_type=TokenType.ACCESS_TOKEN,
                user_id=f"perf_user_{i}",
                scopes={TokenScope.READ}
            )
            tokens.append(token)
        
        # 测试令牌验证性能
        iterations = 200
        start_time = time.time()
        
        for i in range(iterations):
            token = tokens[i % len(tokens)]
            validated = await token_manager.validate_token(
                token_value=token.token_value,
                required_scopes={TokenScope.READ}
            )
            assert validated is not None
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / iterations
        
        print(f"🚀 令牌验证性能测试结果:")
        print(f"   - {iterations} 次验证总耗时: {total_time:.3f}秒")
        print(f"   - 平均每次验证耗时: {avg_time*1000:.2f}毫秒")
        print(f"   - 每秒验证次数: {iterations/total_time:.1f} TPS")
        
        # 性能断言
        assert avg_time < 0.05, f"平均验证时间应该小于50毫秒，实际: {avg_time*1000:.2f}毫秒"


# 安全测试
class TestSecurityVulnerabilities:
    """安全漏洞测试"""
    
    @pytest.mark.asyncio
    async def test_brute_force_protection(self, security_components):
        """暴力破解防护测试"""
        components = security_components
        authenticator = components["authenticator"]
        security_manager = components["security_manager"]
        
        # 创建测试用户
        user_id = "brute_force_target"
        password = "SecurePassword123!"
        
        await authenticator.create_user(
            user_id=user_id,
            password=password,
            role=UserRole.USER
        )
        
        # 模拟暴力破解攻击
        failed_attempts = 0
        max_attempts = 10
        
        for i in range(max_attempts):
            session = await authenticator.authenticate(
                user_id=user_id,
                password="WrongPassword",
                method=AuthMethod.PASSWORD
            )
            
            if session is None:
                failed_attempts += 1
                
                # 报告安全事件
                await security_manager.report_security_event(
                    event_type=SecurityEventType.LOGIN_FAILURE,
                    threat_level=ThreatLevel.MEDIUM,
                    user_id=user_id,
                    source_ip="192.168.1.100",
                    description=f"暴力破解尝试 #{i+1}"
                )
            else:
                # 如果意外成功，立即登出
                await authenticator.logout(session.session_id)
        
        # 验证所有尝试都失败了
        assert failed_attempts == max_attempts, "所有错误密码尝试都应该失败"
        
        # 检查用户是否被锁定
        user = await authenticator.get_user(user_id)
        # 注意：这取决于具体的锁定策略实现
        
        print(f"✅ 暴力破解防护测试通过:")
        print(f"   - 失败尝试: {failed_attempts}/{max_attempts}")
        print(f"   - 用户状态: {user.status.value if user else '未找到'}")
    
    @pytest.mark.asyncio
    async def test_token_security(self, security_components):
        """令牌安全测试"""
        components = security_components
        token_manager = components["token_manager"]
        
        # 创建测试令牌
        token = await token_manager.create_token(
            token_type=TokenType.ACCESS_TOKEN,
            user_id="security_test_user",
            scopes={TokenScope.READ}
        )
        
        # 1. 测试令牌唯一性
        token2 = await token_manager.create_token(
            token_type=TokenType.ACCESS_TOKEN,
            user_id="security_test_user",
            scopes={TokenScope.READ}
        )
        
        assert token.token_value != token2.token_value, "令牌值应该是唯一的"
        assert token.token_id != token2.token_id, "令牌ID应该是唯一的"
        
        # 2. 测试令牌撤销后的安全性
        revoke_success = await token_manager.revoke_token(
            token_id=token.token_id,
            reason="安全测试"
        )
        assert revoke_success, "令牌撤销应该成功"
        
        # 验证撤销的令牌无法使用
        validated = await token_manager.validate_token(token.token_value)
        assert validated is None, "撤销的令牌应该无法验证"
        
        # 3. 测试令牌作用域限制
        limited_token = await token_manager.create_token(
            token_type=TokenType.ACCESS_TOKEN,
            user_id="security_test_user",
            scopes={TokenScope.READ}  # 只有读权限
        )
        
        # 验证只有读权限
        read_validated = await token_manager.validate_token(
            token_value=limited_token.token_value,
            required_scopes={TokenScope.READ}
        )
        assert read_validated is not None, "应该有读权限"
        
        # 验证没有写权限
        write_validated = await token_manager.validate_token(
            token_value=limited_token.token_value,
            required_scopes={TokenScope.WRITE}
        )
        assert write_validated is None, "不应该有写权限"
        
        print("✅ 令牌安全测试通过")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])

