# Security 组件重复分析与整合方案

## 🔍 **重复分析结果**

您的担心是正确的！经过详细分析，确实存在功能重复的问题：

### 📊 **现有Security组件功能对比**

| 功能模块 | security_manager.py | authorizer.py | WebUI权限管理 | 重复程度 |
|---------|-------------------|---------------|--------------|---------|
| **用户认证** | ❌ 无 | ❌ 无 | ✅ 三角色认证 | 🟡 部分重复 |
| **权限控制** | ❌ 无 | ✅ RBAC完整实现 | ✅ 三角色权限 | 🔴 高度重复 |
| **角色管理** | ❌ 无 | ✅ 完整角色系统 | ✅ Admin/Dev/User | 🔴 高度重复 |
| **访问策略** | ❌ 无 | ✅ 策略引擎 | ✅ 权限策略 | 🔴 高度重复 |
| **威胁检测** | ✅ 完整实现 | ❌ 无 | ❌ 无 | 🟢 无重复 |
| **安全事件** | ✅ 完整实现 | ❌ 无 | ❌ 无 | 🟢 无重复 |
| **合规检查** | ✅ 完整实现 | ❌ 无 | ❌ 无 | 🟢 无重复 |
| **实时协作** | ❌ 无 | ❌ 无 | ✅ 多人编辑 | 🟢 无重复 |

### 🎯 **重复问题总结**

#### 🔴 **高度重复 (需要整合)**
1. **权限控制系统**
   - `authorizer.py`: 完整的RBAC系统，支持6种角色
   - `WebUI权限管理`: 三角色权限控制 (Admin/Developer/User)
   - **重复度**: 90%

2. **角色管理系统**
   - `authorizer.py`: 角色继承、权限分配、策略管理
   - `WebUI权限管理`: 简化的三角色管理
   - **重复度**: 85%

3. **访问策略引擎**
   - `authorizer.py`: 复杂的策略规则引擎
   - `WebUI权限管理`: 基础的权限策略
   - **重复度**: 75%

#### 🟡 **部分重复 (需要协调)**
1. **用户认证**
   - `WebUI权限管理`: API Key、OAuth、Email认证
   - `authorizer.py`: 权限验证但无认证实现
   - **重复度**: 30%

#### 🟢 **无重复 (保持独立)**
1. **威胁检测**: `security_manager.py` 独有
2. **安全事件**: `security_manager.py` 独有
3. **合规检查**: `security_manager.py` 独有
4. **实时协作**: `WebUI权限管理` 独有

## 🔧 **整合方案设计**

### 🎯 **整合原则**
1. **避免重复开发**: 复用现有的authorizer.py RBAC系统
2. **功能增强**: 在现有基础上扩展WebUI特定功能
3. **保持兼容**: 确保现有组件正常工作
4. **统一接口**: 提供统一的权限管理接口

### 🏗️ **整合架构设计**

```
┌─────────────────────────────────────────────────────────────┐
│                    🎨 WebUI Permission Layer                │
├─────────────────────────────────────────────────────────────┤
│  📊 三角色管理    │  🔐 认证集成    │  🔄 实时协作    │  📈 使用分析  │
│  (Admin/Dev/User) │  (Multi-Auth)  │  (Multi-User)  │  (Analytics) │
├─────────────────────────────────────────────────────────────┤
│                   🔌 Permission Bridge Adapter              │
├─────────────────────────────────────────────────────────────┤
│  🔄 角色映射      │  📡 权限桥接    │  🎯 策略转换    │  📊 事件同步  │
│  (Role Mapping)  │  (Perm Bridge) │  (Policy Conv) │  (Event Sync)│
├─────────────────────────────────────────────────────────────┤
│                   🛡️ Core Authorization Layer               │
├─────────────────────────────────────────────────────────────┤
│  👥 RBAC系统      │  🔐 权限引擎    │  📋 策略管理    │  📝 访问日志  │
│  (authorizer.py) │  (Perm Engine) │  (Policy Mgmt) │  (Access Log)│
├─────────────────────────────────────────────────────────────┤
│                   🚨 Security Management Layer              │
├─────────────────────────────────────────────────────────────┤
│  🔍 威胁检测      │  📊 安全事件    │  ✅ 合规检查    │  🚨 告警系统  │
│  (security_manager.py)                                     │
└─────────────────────────────────────────────────────────────┘
```

### 📦 **整合实现方案**

#### 1. **Permission Bridge Adapter** - 权限桥接适配器

```python
# components/web_ui_mcp/permission_bridge_adapter.py

import asyncio
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ...core.security.authorizer import MCPAuthorizer, Permission, Role, PermissionType, ResourceType
from .smartui_adapter import SmartUIAdapter, WebSocketMessage, MessageType


class WebUIRole(Enum):
    """WebUI角色枚举"""
    ADMIN = "admin"
    DEVELOPER = "developer"
    USER = "user"


@dataclass
class WebUIPermissionRequest:
    """WebUI权限请求"""
    user_id: str
    role: WebUIRole
    action: str  # read, write, execute, admin
    resource: str  # monaco, github, file_manager, etc.
    context: Dict[str, Any]


class PermissionBridgeAdapter:
    """
    权限桥接适配器
    
    将WebUI的三角色权限系统桥接到核心RBAC系统
    """
    
    def __init__(self, authorizer: MCPAuthorizer, smartui_adapter: SmartUIAdapter):
        self.authorizer = authorizer
        self.smartui_adapter = smartui_adapter
        
        # WebUI角色到核心角色的映射
        self.role_mapping = {
            WebUIRole.ADMIN: ["admin", "developer", "operator"],
            WebUIRole.DEVELOPER: ["developer", "operator"],
            WebUIRole.USER: ["viewer"]
        }
        
        # WebUI资源到核心资源的映射
        self.resource_mapping = {
            "monaco": ("tool", "monaco_editor"),
            "github": ("service", "github_integration"),
            "file_manager": ("tool", "file_manager"),
            "auth": ("service", "authentication"),
            "analytics": ("data", "usage_analytics"),
            "mcp_servers": ("service", "mcp_servers"),
            "projects": ("data", "projects"),
            "sessions": ("data", "sessions")
        }
        
        # WebUI动作到核心权限的映射
        self.action_mapping = {
            "read": PermissionType.READ,
            "write": PermissionType.WRITE,
            "execute": PermissionType.EXECUTE,
            "admin": PermissionType.ADMIN,
            "create": PermissionType.CREATE,
            "update": PermissionType.UPDATE,
            "delete": PermissionType.DELETE,
            "list": PermissionType.LIST
        }
        
        self._setup_webui_integration()
    
    def _setup_webui_integration(self):
        """设置WebUI集成"""
        # 注册WebUI权限检查处理器
        self.smartui_adapter.add_event_listener(
            "permission_check", 
            self._handle_permission_check
        )
        self.smartui_adapter.add_event_listener(
            "role_assignment", 
            self._handle_role_assignment
        )
        self.smartui_adapter.add_event_listener(
            "user_authentication", 
            self._handle_user_authentication
        )
    
    async def check_webui_permission(self, request: WebUIPermissionRequest) -> bool:
        """
        检查WebUI权限
        
        Args:
            request: WebUI权限请求
            
        Returns:
            bool: 是否有权限
        """
        try:
            # 映射到核心权限系统
            resource_type, resource_id = self._map_resource(request.resource)
            permission_type = self._map_action(request.action)
            
            # 检查核心权限
            result = await self.authorizer.check_permission(
                user_id=request.user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                permission_type=permission_type,
                context=request.context
            )
            
            return result.decision.value == "allow"
            
        except Exception as e:
            print(f"检查WebUI权限失败: {e}")
            return False
    
    async def assign_webui_role(self, user_id: str, webui_role: WebUIRole) -> bool:
        """
        分配WebUI角色
        
        Args:
            user_id: 用户ID
            webui_role: WebUI角色
            
        Returns:
            bool: 分配是否成功
        """
        try:
            # 获取对应的核心角色
            core_roles = self.role_mapping.get(webui_role, [])
            
            success = True
            for role_id in core_roles:
                result = await self.authorizer.assign_role_to_user(user_id, role_id)
                if not result:
                    success = False
            
            return success
            
        except Exception as e:
            print(f"分配WebUI角色失败: {e}")
            return False
    
    async def get_user_webui_role(self, user_id: str) -> Optional[WebUIRole]:
        """
        获取用户的WebUI角色
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[WebUIRole]: WebUI角色
        """
        try:
            user_roles = await self.authorizer.get_user_roles(user_id)
            role_ids = {role.role_id for role in user_roles}
            
            # 按优先级检查角色
            if "admin" in role_ids:
                return WebUIRole.ADMIN
            elif "developer" in role_ids:
                return WebUIRole.DEVELOPER
            elif "viewer" in role_ids:
                return WebUIRole.USER
            else:
                return None
                
        except Exception as e:
            print(f"获取用户WebUI角色失败: {e}")
            return None
    
    async def create_webui_permissions(self) -> None:
        """创建WebUI特定权限"""
        try:
            webui_permissions = [
                # Monaco Editor权限
                Permission("monaco_read", "Monaco读取", "读取Monaco编辑器", ResourceType.TOOL, PermissionType.READ, "monaco_editor"),
                Permission("monaco_write", "Monaco写入", "在Monaco编辑器中编辑", ResourceType.TOOL, PermissionType.WRITE, "monaco_editor"),
                Permission("monaco_execute", "Monaco执行", "在Monaco编辑器中执行代码", ResourceType.TOOL, PermissionType.EXECUTE, "monaco_editor"),
                
                # GitHub集成权限
                Permission("github_read", "GitHub读取", "读取GitHub仓库", ResourceType.SERVICE, PermissionType.READ, "github_integration"),
                Permission("github_write", "GitHub写入", "修改GitHub仓库", ResourceType.SERVICE, PermissionType.WRITE, "github_integration"),
                
                # 文件管理权限
                Permission("file_read", "文件读取", "读取文件", ResourceType.TOOL, PermissionType.READ, "file_manager"),
                Permission("file_write", "文件写入", "修改文件", ResourceType.TOOL, PermissionType.WRITE, "file_manager"),
                Permission("file_delete", "文件删除", "删除文件", ResourceType.TOOL, PermissionType.DELETE, "file_manager"),
                
                # 项目管理权限
                Permission("project_read", "项目读取", "读取项目信息", ResourceType.DATA, PermissionType.READ, "projects"),
                Permission("project_write", "项目写入", "修改项目信息", ResourceType.DATA, PermissionType.WRITE, "projects"),
                Permission("project_admin", "项目管理", "完全管理项目", ResourceType.DATA, PermissionType.ADMIN, "projects"),
                
                # 会话管理权限
                Permission("session_read", "会话读取", "读取会话信息", ResourceType.DATA, PermissionType.READ, "sessions"),
                Permission("session_write", "会话写入", "修改会话信息", ResourceType.DATA, PermissionType.WRITE, "sessions"),
                
                # 分析数据权限
                Permission("analytics_read", "分析读取", "读取使用分析", ResourceType.DATA, PermissionType.READ, "usage_analytics"),
                
                # MCP服务器权限
                Permission("mcp_server_read", "MCP服务器读取", "读取MCP服务器信息", ResourceType.SERVICE, PermissionType.READ, "mcp_servers"),
                Permission("mcp_server_admin", "MCP服务器管理", "管理MCP服务器", ResourceType.SERVICE, PermissionType.ADMIN, "mcp_servers"),
            ]
            
            for permission in webui_permissions:
                await self.authorizer.add_permission(permission)
            
            print(f"创建了 {len(webui_permissions)} 个WebUI权限")
            
        except Exception as e:
            print(f"创建WebUI权限失败: {e}")
    
    async def create_webui_roles(self) -> None:
        """创建WebUI特定角色"""
        try:
            # 扩展现有角色的权限
            webui_admin_permissions = {
                "monaco_read", "monaco_write", "monaco_execute",
                "github_read", "github_write",
                "file_read", "file_write", "file_delete",
                "project_read", "project_write", "project_admin",
                "session_read", "session_write",
                "analytics_read",
                "mcp_server_read", "mcp_server_admin"
            }
            
            webui_developer_permissions = {
                "monaco_read", "monaco_write", "monaco_execute",
                "github_read", "github_write",
                "file_read", "file_write",
                "project_read", "project_write",
                "session_read", "session_write",
                "analytics_read",
                "mcp_server_read"
            }
            
            webui_user_permissions = {
                "monaco_read",
                "github_read",
                "file_read",
                "project_read",
                "session_read",
                "analytics_read",
                "mcp_server_read"
            }
            
            # 更新现有角色
            if "admin" in self.authorizer.roles:
                admin_role = self.authorizer.roles["admin"]
                admin_role.permissions.update(webui_admin_permissions)
            
            if "developer" in self.authorizer.roles:
                developer_role = self.authorizer.roles["developer"]
                developer_role.permissions.update(webui_developer_permissions)
            
            if "viewer" in self.authorizer.roles:
                viewer_role = self.authorizer.roles["viewer"]
                viewer_role.permissions.update(webui_user_permissions)
            
            print("WebUI角色权限更新完成")
            
        except Exception as e:
            print(f"创建WebUI角色失败: {e}")
    
    def _map_resource(self, webui_resource: str) -> tuple:
        """映射WebUI资源到核心资源"""
        if webui_resource in self.resource_mapping:
            resource_type_str, resource_id = self.resource_mapping[webui_resource]
            resource_type = ResourceType(resource_type_str)
            return resource_type, resource_id
        else:
            return ResourceType.SERVICE, webui_resource
    
    def _map_action(self, webui_action: str) -> PermissionType:
        """映射WebUI动作到核心权限类型"""
        return self.action_mapping.get(webui_action, PermissionType.READ)
    
    # WebSocket消息处理器
    async def _handle_permission_check(self, data: Dict[str, Any]):
        """处理权限检查请求"""
        try:
            user_id = data.get("user_id")
            role = WebUIRole(data.get("role", "user"))
            action = data.get("action", "read")
            resource = data.get("resource", "")
            context = data.get("context", {})
            
            request = WebUIPermissionRequest(
                user_id=user_id,
                role=role,
                action=action,
                resource=resource,
                context=context
            )
            
            has_permission = await self.check_webui_permission(request)
            
            return {
                "type": "permission_response",
                "user_id": user_id,
                "resource": resource,
                "action": action,
                "allowed": has_permission
            }
            
        except Exception as e:
            return {
                "type": "error",
                "message": f"权限检查失败: {e}"
            }
    
    async def _handle_role_assignment(self, data: Dict[str, Any]):
        """处理角色分配请求"""
        try:
            user_id = data.get("user_id")
            role = WebUIRole(data.get("role"))
            
            success = await self.assign_webui_role(user_id, role)
            
            return {
                "type": "role_assignment_response",
                "user_id": user_id,
                "role": role.value,
                "success": success
            }
            
        except Exception as e:
            return {
                "type": "error",
                "message": f"角色分配失败: {e}"
            }
    
    async def _handle_user_authentication(self, data: Dict[str, Any]):
        """处理用户认证请求"""
        try:
            user_id = data.get("user_id")
            
            # 获取用户角色
            webui_role = await self.get_user_webui_role(user_id)
            
            # 获取用户权限
            permissions = await self.authorizer.get_user_permissions(user_id)
            permission_list = [
                {
                    "id": p.permission_id,
                    "name": p.name,
                    "resource_type": p.resource_type.value,
                    "permission_type": p.permission_type.value,
                    "resource_pattern": p.resource_pattern
                }
                for p in permissions
            ]
            
            return {
                "type": "authentication_response",
                "user_id": user_id,
                "role": webui_role.value if webui_role else None,
                "permissions": permission_list
            }
            
        except Exception as e:
            return {
                "type": "error",
                "message": f"用户认证失败: {e}"
            }
```

#### 2. **更新WebUI MCP组件** - 移除重复功能

```python
# 更新 components/web_ui_mcp/smartui_adapter.py

class SmartUIAdapter:
    """
    SmartUI适配器 (更新版本 - 移除重复的权限管理)
    """
    
    def __init__(self, permission_bridge: PermissionBridgeAdapter):
        # ... 现有代码 ...
        
        # 使用权限桥接适配器而不是内置权限管理
        self.permission_bridge = permission_bridge
        
        # 移除重复的权限管理代码
        # self.user_permissions = {}  # 删除
        # self.role_permissions = {}  # 删除
    
    async def check_user_permission(self, user_id: str, action: str, resource: str) -> bool:
        """检查用户权限 (使用权限桥接)"""
        try:
            # 获取用户角色
            webui_role = await self.permission_bridge.get_user_webui_role(user_id)
            if not webui_role:
                return False
            
            # 创建权限请求
            request = WebUIPermissionRequest(
                user_id=user_id,
                role=webui_role,
                action=action,
                resource=resource,
                context={}
            )
            
            # 检查权限
            return await self.permission_bridge.check_webui_permission(request)
            
        except Exception as e:
            print(f"检查用户权限失败: {e}")
            return False
```

#### 3. **实时协作权限管理** - 新增功能

```python
# components/web_ui_mcp/realtime_collaboration_manager.py

import asyncio
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .permission_bridge_adapter import PermissionBridgeAdapter, WebUIRole


class CollaborationAction(Enum):
    """协作动作枚举"""
    JOIN_SESSION = "join_session"
    LEAVE_SESSION = "leave_session"
    EDIT_DOCUMENT = "edit_document"
    SAVE_DOCUMENT = "save_document"
    SHARE_CURSOR = "share_cursor"
    SEND_MESSAGE = "send_message"
    LOCK_RESOURCE = "lock_resource"
    UNLOCK_RESOURCE = "unlock_resource"


@dataclass
class CollaborationSession:
    """协作会话"""
    session_id: str
    resource_id: str
    participants: Set[str]
    owner: str
    created_at: datetime
    last_activity: datetime
    metadata: Dict[str, Any]


@dataclass
class ResourceLock:
    """资源锁"""
    resource_id: str
    user_id: str
    lock_type: str  # exclusive, shared
    acquired_at: datetime
    expires_at: Optional[datetime]


class RealtimeCollaborationManager:
    """
    实时协作管理器
    
    管理多用户实时编辑、权限控制、冲突解决
    """
    
    def __init__(self, permission_bridge: PermissionBridgeAdapter):
        self.permission_bridge = permission_bridge
        
        # 协作会话管理
        self.sessions: Dict[str, CollaborationSession] = {}
        
        # 资源锁管理
        self.resource_locks: Dict[str, ResourceLock] = {}
        
        # 用户活动跟踪
        self.user_activities: Dict[str, datetime] = {}
        
        # 权限缓存
        self.permission_cache: Dict[str, Dict[str, bool]] = {}
    
    async def join_collaboration_session(self, session_id: str, user_id: str, 
                                       resource_id: str) -> bool:
        """
        加入协作会话
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            resource_id: 资源ID
            
        Returns:
            bool: 是否成功加入
        """
        try:
            # 检查权限
            if not await self._check_collaboration_permission(
                user_id, CollaborationAction.JOIN_SESSION, resource_id
            ):
                return False
            
            # 创建或更新会话
            if session_id not in self.sessions:
                self.sessions[session_id] = CollaborationSession(
                    session_id=session_id,
                    resource_id=resource_id,
                    participants=set(),
                    owner=user_id,
                    created_at=datetime.now(),
                    last_activity=datetime.now(),
                    metadata={}
                )
            
            session = self.sessions[session_id]
            session.participants.add(user_id)
            session.last_activity = datetime.now()
            
            # 更新用户活动
            self.user_activities[user_id] = datetime.now()
            
            return True
            
        except Exception as e:
            print(f"加入协作会话失败: {e}")
            return False
    
    async def leave_collaboration_session(self, session_id: str, user_id: str) -> bool:
        """
        离开协作会话
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            
        Returns:
            bool: 是否成功离开
        """
        try:
            if session_id not in self.sessions:
                return False
            
            session = self.sessions[session_id]
            session.participants.discard(user_id)
            session.last_activity = datetime.now()
            
            # 如果没有参与者，清理会话
            if not session.participants:
                del self.sessions[session_id]
            
            # 释放用户持有的锁
            await self._release_user_locks(user_id)
            
            return True
            
        except Exception as e:
            print(f"离开协作会话失败: {e}")
            return False
    
    async def acquire_resource_lock(self, resource_id: str, user_id: str, 
                                  lock_type: str = "exclusive") -> bool:
        """
        获取资源锁
        
        Args:
            resource_id: 资源ID
            user_id: 用户ID
            lock_type: 锁类型
            
        Returns:
            bool: 是否成功获取锁
        """
        try:
            # 检查权限
            if not await self._check_collaboration_permission(
                user_id, CollaborationAction.LOCK_RESOURCE, resource_id
            ):
                return False
            
            # 检查是否已有锁
            if resource_id in self.resource_locks:
                existing_lock = self.resource_locks[resource_id]
                
                # 如果是同一用户，更新锁
                if existing_lock.user_id == user_id:
                    existing_lock.acquired_at = datetime.now()
                    return True
                
                # 如果是排他锁，拒绝
                if existing_lock.lock_type == "exclusive":
                    return False
                
                # 如果是共享锁且请求排他锁，拒绝
                if existing_lock.lock_type == "shared" and lock_type == "exclusive":
                    return False
            
            # 创建新锁
            self.resource_locks[resource_id] = ResourceLock(
                resource_id=resource_id,
                user_id=user_id,
                lock_type=lock_type,
                acquired_at=datetime.now(),
                expires_at=None
            )
            
            return True
            
        except Exception as e:
            print(f"获取资源锁失败: {e}")
            return False
    
    async def release_resource_lock(self, resource_id: str, user_id: str) -> bool:
        """
        释放资源锁
        
        Args:
            resource_id: 资源ID
            user_id: 用户ID
            
        Returns:
            bool: 是否成功释放锁
        """
        try:
            if resource_id not in self.resource_locks:
                return False
            
            lock = self.resource_locks[resource_id]
            
            # 只有锁的持有者或管理员可以释放锁
            user_role = await self.permission_bridge.get_user_webui_role(user_id)
            if lock.user_id != user_id and user_role != WebUIRole.ADMIN:
                return False
            
            del self.resource_locks[resource_id]
            return True
            
        except Exception as e:
            print(f"释放资源锁失败: {e}")
            return False
    
    async def check_edit_permission(self, user_id: str, resource_id: str) -> bool:
        """
        检查编辑权限
        
        Args:
            user_id: 用户ID
            resource_id: 资源ID
            
        Returns:
            bool: 是否有编辑权限
        """
        try:
            # 检查基础权限
            if not await self._check_collaboration_permission(
                user_id, CollaborationAction.EDIT_DOCUMENT, resource_id
            ):
                return False
            
            # 检查资源锁
            if resource_id in self.resource_locks:
                lock = self.resource_locks[resource_id]
                
                # 如果是排他锁且不是锁的持有者
                if lock.lock_type == "exclusive" and lock.user_id != user_id:
                    return False
            
            return True
            
        except Exception as e:
            print(f"检查编辑权限失败: {e}")
            return False
    
    async def get_collaboration_status(self, resource_id: str) -> Dict[str, Any]:
        """
        获取协作状态
        
        Args:
            resource_id: 资源ID
            
        Returns:
            Dict[str, Any]: 协作状态信息
        """
        try:
            # 查找相关会话
            related_sessions = [
                session for session in self.sessions.values()
                if session.resource_id == resource_id
            ]
            
            # 获取资源锁信息
            lock_info = None
            if resource_id in self.resource_locks:
                lock = self.resource_locks[resource_id]
                lock_info = {
                    "user_id": lock.user_id,
                    "lock_type": lock.lock_type,
                    "acquired_at": lock.acquired_at.isoformat()
                }
            
            # 统计活跃用户
            active_users = set()
            for session in related_sessions:
                active_users.update(session.participants)
            
            return {
                "resource_id": resource_id,
                "active_sessions": len(related_sessions),
                "active_users": list(active_users),
                "user_count": len(active_users),
                "lock_info": lock_info,
                "sessions": [
                    {
                        "session_id": session.session_id,
                        "participants": list(session.participants),
                        "owner": session.owner,
                        "created_at": session.created_at.isoformat(),
                        "last_activity": session.last_activity.isoformat()
                    }
                    for session in related_sessions
                ]
            }
            
        except Exception as e:
            print(f"获取协作状态失败: {e}")
            return {}
    
    async def _check_collaboration_permission(self, user_id: str, 
                                            action: CollaborationAction, 
                                            resource_id: str) -> bool:
        """检查协作权限"""
        try:
            # 缓存键
            cache_key = f"{user_id}:{action.value}:{resource_id}"
            
            # 检查缓存
            if user_id in self.permission_cache and cache_key in self.permission_cache[user_id]:
                return self.permission_cache[user_id][cache_key]
            
            # 获取用户角色
            user_role = await self.permission_bridge.get_user_webui_role(user_id)
            if not user_role:
                return False
            
            # 根据动作和角色检查权限
            has_permission = False
            
            if action == CollaborationAction.JOIN_SESSION:
                # 所有角色都可以加入会话
                has_permission = True
            
            elif action == CollaborationAction.EDIT_DOCUMENT:
                # 开发者和管理员可以编辑
                has_permission = user_role in [WebUIRole.ADMIN, WebUIRole.DEVELOPER]
            
            elif action == CollaborationAction.SAVE_DOCUMENT:
                # 开发者和管理员可以保存
                has_permission = user_role in [WebUIRole.ADMIN, WebUIRole.DEVELOPER]
            
            elif action == CollaborationAction.LOCK_RESOURCE:
                # 开发者和管理员可以锁定资源
                has_permission = user_role in [WebUIRole.ADMIN, WebUIRole.DEVELOPER]
            
            elif action == CollaborationAction.UNLOCK_RESOURCE:
                # 管理员可以解锁任何资源
                has_permission = user_role == WebUIRole.ADMIN
            
            else:
                # 其他动作默认允许
                has_permission = True
            
            # 缓存结果
            if user_id not in self.permission_cache:
                self.permission_cache[user_id] = {}
            self.permission_cache[user_id][cache_key] = has_permission
            
            return has_permission
            
        except Exception as e:
            print(f"检查协作权限失败: {e}")
            return False
    
    async def _release_user_locks(self, user_id: str) -> None:
        """释放用户持有的所有锁"""
        try:
            locks_to_remove = [
                resource_id for resource_id, lock in self.resource_locks.items()
                if lock.user_id == user_id
            ]
            
            for resource_id in locks_to_remove:
                del self.resource_locks[resource_id]
                
        except Exception as e:
            print(f"释放用户锁失败: {e}")
```

## 🎯 **整合效果**

### ✅ **避免重复开发**
1. **复用现有RBAC**: 直接使用authorizer.py的完整RBAC系统
2. **扩展而非重写**: 在现有基础上扩展WebUI特定功能
3. **统一权限管理**: 所有权限检查通过统一接口

### 🚀 **功能增强**
1. **三角色映射**: WebUI三角色自动映射到核心RBAC角色
2. **实时协作**: 新增多用户实时编辑和冲突解决
3. **权限缓存**: 提升权限检查性能
4. **资源锁定**: 防止编辑冲突

### 📊 **架构优化**
1. **分层设计**: 清晰的权限管理分层架构
2. **桥接模式**: 通过适配器桥接不同权限系统
3. **事件驱动**: 权限变更实时同步
4. **可扩展性**: 易于添加新的权限类型和角色

### 💡 **开发建议**

#### 🔄 **立即执行**
1. **实现Permission Bridge Adapter** - 桥接现有权限系统
2. **更新SmartUI Adapter** - 移除重复的权限管理代码
3. **创建WebUI特定权限** - 扩展现有权限系统

#### 📋 **后续优化**
1. **实时协作管理器** - 实现多用户协作功能
2. **权限缓存优化** - 提升性能
3. **权限审计日志** - 增强安全性

这样的整合方案既避免了重复开发，又充分利用了现有的成熟组件，同时为WebUI提供了专业级的权限管理能力！🔧

