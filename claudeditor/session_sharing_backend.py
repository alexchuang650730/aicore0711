"""
會話分享和回放系統 - ClaudEditor的協作競爭優勢
提供比Manus更強大的團隊協作和會話管理能力
"""

import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging

logger = logging.getLogger(__name__)

@dataclass
class SessionMessage:
    """會話消息結構"""
    id: str
    session_id: str
    user_id: str
    user_name: str
    message_type: str  # 'user', 'assistant', 'system', 'task_plan', 'progress'
    content: str
    timestamp: str
    metadata: Dict[str, Any]

@dataclass
class SessionInfo:
    """會話信息結構"""
    session_id: str
    title: str
    creator_id: str
    creator_name: str
    created_at: str
    last_active: str
    participants: List[Dict[str, str]]
    message_count: int
    is_public: bool
    tags: List[str]
    project_context: Optional[Dict[str, Any]]

@dataclass
class ReplayEvent:
    """回放事件結構"""
    event_id: str
    session_id: str
    event_type: str  # 'message', 'task_start', 'task_progress', 'task_complete', 'user_join', 'user_leave'
    timestamp: str
    data: Dict[str, Any]
    duration: float  # 事件持續時間（秒）

class SessionManager:
    """
    會話管理器
    提供超越Manus的協作能力
    """
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_messages: Dict[str, List[SessionMessage]] = {}
        self.session_info: Dict[str, SessionInfo] = {}
        self.replay_events: Dict[str, List[ReplayEvent]] = {}
        self.websocket_connections: Dict[str, List[WebSocket]] = {}
        
    async def create_session(self, creator_id: str, creator_name: str, title: str = None, is_public: bool = False) -> str:
        """創建新的協作會話"""
        session_id = str(uuid.uuid4())
        current_time = datetime.now().isoformat()
        
        if not title:
            title = f"{creator_name}的編程會話 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        session_info = SessionInfo(
            session_id=session_id,
            title=title,
            creator_id=creator_id,
            creator_name=creator_name,
            created_at=current_time,
            last_active=current_time,
            participants=[{"user_id": creator_id, "user_name": creator_name, "joined_at": current_time}],
            message_count=0,
            is_public=is_public,
            tags=[],
            project_context=None
        )
        
        self.session_info[session_id] = session_info
        self.session_messages[session_id] = []
        self.replay_events[session_id] = []
        self.websocket_connections[session_id] = []
        
        # 添加會話創建事件
        await self._add_replay_event(session_id, 'session_created', {
            'creator': creator_name,
            'title': title,
            'is_public': is_public
        })
        
        logger.info(f"🎬 創建協作會話: {session_id} by {creator_name}")
        return session_id
    
    async def join_session(self, session_id: str, user_id: str, user_name: str, websocket: WebSocket = None) -> bool:
        """加入協作會話"""
        if session_id not in self.session_info:
            return False
        
        session = self.session_info[session_id]
        current_time = datetime.now().isoformat()
        
        # 檢查用戶是否已經在會話中
        existing_participant = next((p for p in session.participants if p["user_id"] == user_id), None)
        
        if not existing_participant:
            # 添加新參與者
            session.participants.append({
                "user_id": user_id,
                "user_name": user_name,
                "joined_at": current_time
            })
            
            # 添加系統消息
            join_message = SessionMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                user_id="system",
                user_name="系統",
                message_type="system",
                content=f"🎉 {user_name} 加入了會話",
                timestamp=current_time,
                metadata={"event_type": "user_join"}
            )
            
            await self._add_message(join_message)
            
            # 添加回放事件
            await self._add_replay_event(session_id, 'user_join', {
                'user_name': user_name,
                'user_id': user_id
            })
        
        # 添加WebSocket連接
        if websocket and session_id in self.websocket_connections:
            self.websocket_connections[session_id].append(websocket)
        
        session.last_active = current_time
        logger.info(f"👥 用戶 {user_name} 加入會話: {session_id}")
        return True
    
    async def add_message(self, session_id: str, user_id: str, user_name: str, 
                         message_type: str, content: str, metadata: Dict[str, Any] = None) -> str:
        """添加消息到會話"""
        if session_id not in self.session_info:
            raise ValueError(f"會話不存在: {session_id}")
        
        message_id = str(uuid.uuid4())
        current_time = datetime.now().isoformat()
        
        message = SessionMessage(
            id=message_id,
            session_id=session_id,
            user_id=user_id,
            user_name=user_name,
            message_type=message_type,
            content=content,
            timestamp=current_time,
            metadata=metadata or {}
        )
        
        await self._add_message(message)
        
        # 更新會話活躍時間
        self.session_info[session_id].last_active = current_time
        
        # 廣播消息給所有連接的客戶端
        await self._broadcast_to_session(session_id, {
            "type": "new_message",
            "message": asdict(message)
        })
        
        # 添加回放事件
        await self._add_replay_event(session_id, 'message', asdict(message))
        
        return message_id
    
    async def _add_message(self, message: SessionMessage):
        """內部方法：添加消息"""
        if message.session_id not in self.session_messages:
            self.session_messages[message.session_id] = []
        
        self.session_messages[message.session_id].append(message)
        self.session_info[message.session_id].message_count += 1
    
    async def get_session_messages(self, session_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """獲取會話消息"""
        if session_id not in self.session_messages:
            return []
        
        messages = self.session_messages[session_id]
        start_idx = max(0, len(messages) - offset - limit)
        end_idx = len(messages) - offset if offset > 0 else len(messages)
        
        return [asdict(msg) for msg in messages[start_idx:end_idx]]
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """獲取會話信息"""
        if session_id not in self.session_info:
            return None
        
        return asdict(self.session_info[session_id])
    
    async def get_public_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """獲取公開會話列表"""
        public_sessions = [
            asdict(session) for session in self.session_info.values()
            if session.is_public
        ]
        
        # 按最後活躍時間排序
        public_sessions.sort(key=lambda x: x['last_active'], reverse=True)
        
        return public_sessions[:limit]
    
    async def generate_share_link(self, session_id: str, expire_days: int = 7) -> str:
        """生成會話分享鏈接"""
        if session_id not in self.session_info:
            raise ValueError(f"會話不存在: {session_id}")
        
        # 生成分享令牌
        share_token = str(uuid.uuid4())
        expire_time = datetime.now() + timedelta(days=expire_days)
        
        # 這裡應該存儲分享令牌到數據庫
        # 暫時返回模擬鏈接
        share_link = f"http://localhost:8080/share/{share_token}"
        
        logger.info(f"🔗 生成分享鏈接: {session_id} -> {share_link}")
        return share_link
    
    async def start_session_replay(self, session_id: str, speed: float = 1.0) -> Dict[str, Any]:
        """開始會話回放"""
        if session_id not in self.replay_events:
            raise ValueError(f"會話回放數據不存在: {session_id}")
        
        events = self.replay_events[session_id]
        session_info = self.session_info[session_id]
        
        replay_info = {
            "session_id": session_id,
            "title": f"回放: {session_info.title}",
            "total_events": len(events),
            "total_duration": sum(event.duration for event in events),
            "replay_speed": speed,
            "created_at": session_info.created_at,
            "participants": session_info.participants
        }
        
        logger.info(f"▶️ 開始會話回放: {session_id} (速度: {speed}x)")
        return replay_info
    
    async def get_replay_events(self, session_id: str, start_time: str = None, end_time: str = None) -> List[Dict[str, Any]]:
        """獲取回放事件"""
        if session_id not in self.replay_events:
            return []
        
        events = self.replay_events[session_id]
        
        # 時間過濾（如果提供）
        if start_time or end_time:
            filtered_events = []
            for event in events:
                event_time = datetime.fromisoformat(event.timestamp)
                
                if start_time and event_time < datetime.fromisoformat(start_time):
                    continue
                if end_time and event_time > datetime.fromisoformat(end_time):
                    continue
                
                filtered_events.append(event)
            
            events = filtered_events
        
        return [asdict(event) for event in events]
    
    async def _add_replay_event(self, session_id: str, event_type: str, data: Dict[str, Any], duration: float = 0.1):
        """添加回放事件"""
        if session_id not in self.replay_events:
            self.replay_events[session_id] = []
        
        event = ReplayEvent(
            event_id=str(uuid.uuid4()),
            session_id=session_id,
            event_type=event_type,
            timestamp=datetime.now().isoformat(),
            data=data,
            duration=duration
        )
        
        self.replay_events[session_id].append(event)
    
    async def _broadcast_to_session(self, session_id: str, message: Dict[str, Any]):
        """向會話中的所有連接廣播消息"""
        if session_id not in self.websocket_connections:
            return
        
        # 清理無效連接
        active_connections = []
        for websocket in self.websocket_connections[session_id]:
            try:
                await websocket.send_json(message)
                active_connections.append(websocket)
            except:
                # 連接已斷開，忽略
                pass
        
        self.websocket_connections[session_id] = active_connections
    
    async def export_session(self, session_id: str, format: str = 'json') -> Dict[str, Any]:
        """導出會話數據"""
        if session_id not in self.session_info:
            raise ValueError(f"會話不存在: {session_id}")
        
        session_data = {
            "session_info": asdict(self.session_info[session_id]),
            "messages": [asdict(msg) for msg in self.session_messages.get(session_id, [])],
            "replay_events": [asdict(event) for event in self.replay_events.get(session_id, [])],
            "export_timestamp": datetime.now().isoformat(),
            "format_version": "1.0"
        }
        
        logger.info(f"📤 導出會話數據: {session_id} (格式: {format})")
        return session_data

# 創建全局會話管理器實例
session_manager = SessionManager()

# FastAPI應用集成
app = FastAPI(title="ClaudEditor Session Sharing API", version="4.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/sessions/create")
async def create_session_api(request: Dict[str, Any]):
    """創建會話API"""
    try:
        session_id = await session_manager.create_session(
            creator_id=request.get("creator_id", "anonymous"),
            creator_name=request.get("creator_name", "匿名用戶"),
            title=request.get("title"),
            is_public=request.get("is_public", False)
        )
        
        return {
            "status": "success",
            "session_id": session_id,
            "message": "會話創建成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sessions/{session_id}/join")
async def join_session_api(session_id: str, request: Dict[str, Any]):
    """加入會話API"""
    try:
        success = await session_manager.join_session(
            session_id=session_id,
            user_id=request.get("user_id", "anonymous"),
            user_name=request.get("user_name", "匿名用戶")
        )
        
        if success:
            return {"status": "success", "message": "成功加入會話"}
        else:
            raise HTTPException(status_code=404, detail="會話不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sessions/{session_id}/messages")
async def add_message_api(session_id: str, request: Dict[str, Any]):
    """添加消息API"""
    try:
        message_id = await session_manager.add_message(
            session_id=session_id,
            user_id=request.get("user_id", "anonymous"),
            user_name=request.get("user_name", "匿名用戶"),
            message_type=request.get("message_type", "user"),
            content=request.get("content", ""),
            metadata=request.get("metadata", {})
        )
        
        return {
            "status": "success",
            "message_id": message_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/{session_id}/messages")
async def get_messages_api(session_id: str, limit: int = 100, offset: int = 0):
    """獲取會話消息API"""
    try:
        messages = await session_manager.get_session_messages(session_id, limit, offset)
        return {
            "status": "success",
            "messages": messages,
            "total": len(messages)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/{session_id}/share")
async def generate_share_link_api(session_id: str, expire_days: int = 7):
    """生成分享鏈接API"""
    try:
        share_link = await session_manager.generate_share_link(session_id, expire_days)
        return {
            "status": "success",
            "share_link": share_link,
            "expire_days": expire_days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/{session_id}/replay")
async def get_replay_info_api(session_id: str, speed: float = 1.0):
    """獲取會話回放信息API"""
    try:
        replay_info = await session_manager.start_session_replay(session_id, speed)
        return {
            "status": "success",
            "replay_info": replay_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/{session_id}/events")
async def get_replay_events_api(session_id: str, start_time: str = None, end_time: str = None):
    """獲取回放事件API"""
    try:
        events = await session_manager.get_replay_events(session_id, start_time, end_time)
        return {
            "status": "success",
            "events": events,
            "total": len(events)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/public")
async def get_public_sessions_api(limit: int = 20):
    """獲取公開會話列表API"""
    try:
        sessions = await session_manager.get_public_sessions(limit)
        return {
            "status": "success",
            "sessions": sessions,
            "total": len(sessions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/sessions/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket連接端點"""
    await websocket.accept()
    
    # 將連接添加到會話
    if session_id not in session_manager.websocket_connections:
        session_manager.websocket_connections[session_id] = []
    
    session_manager.websocket_connections[session_id].append(websocket)
    
    try:
        while True:
            # 接收客戶端消息
            data = await websocket.receive_json()
            
            # 處理不同類型的消息
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "message":
                # 廣播消息給其他用戶
                await session_manager._broadcast_to_session(session_id, data)
            
    except WebSocketDisconnect:
        # 移除斷開的連接
        if websocket in session_manager.websocket_connections[session_id]:
            session_manager.websocket_connections[session_id].remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083, log_level="info")