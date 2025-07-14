"""
MCP Coordinator Integration - Central MCP Communication Hub

This module provides the central coordination hub for all MCP communications
in PowerAutomation 4.0, specifically integrating Trae Agent MCP with the
existing PowerAutomation ecosystem through the MCPCoordinator.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path


class MCPMessageType(Enum):
    """MCP message types for coordination"""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    STATUS_UPDATE = "status_update"
    HEALTH_CHECK = "health_check"
    REGISTRATION = "registration"
    DEREGISTRATION = "deregistration"
    ROUTING_REQUEST = "routing_request"
    ROUTING_RESPONSE = "routing_response"
    ERROR_NOTIFICATION = "error_notification"
    PERFORMANCE_METRICS = "performance_metrics"


class MCPStatus(Enum):
    """MCP status states"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


@dataclass
class MCPMessage:
    """Standard MCP message format"""
    message_id: str
    message_type: MCPMessageType
    source_mcp: str
    target_mcp: str
    timestamp: float
    payload: Dict[str, Any]
    correlation_id: Optional[str] = None
    priority: int = 5  # 1-10, 1 is highest priority
    ttl: Optional[float] = None  # Time to live in seconds


@dataclass
class MCPRegistration:
    """MCP registration information"""
    mcp_id: str
    mcp_name: str
    mcp_type: str
    capabilities: List[str]
    endpoints: Dict[str, str]
    status: MCPStatus
    health_check_interval: float
    last_heartbeat: float
    metadata: Dict[str, Any]


@dataclass
class TaskExecution:
    """Task execution tracking"""
    task_id: str
    original_task: Any
    assigned_mcp: str
    routing_decision: Dict[str, Any]
    start_time: float
    status: str
    progress: float
    estimated_completion: Optional[float]
    result: Optional[Dict[str, Any]]
    error: Optional[str]


class MCPCoordinatorIntegration:
    """
    MCP Coordinator Integration
    
    Central coordination hub for all MCP communications in PowerAutomation 4.0.
    Manages Trae Agent MCP integration with existing PowerAutomation ecosystem.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize MCP Coordinator Integration
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Coordinator configuration
        self.coordinator_id = self.config.get('coordinator_id', 'mcp_coordinator_main')
        self.enable_load_balancing = self.config.get('enable_load_balancing', True)
        self.enable_failover = self.config.get('enable_failover', True)
        self.enable_monitoring = self.config.get('enable_monitoring', True)
        
        # MCP registry
        self.registered_mcps = {}
        self.mcp_capabilities = {}
        self.mcp_performance = {}
        
        # Task management
        self.active_tasks = {}
        self.task_queue = asyncio.Queue()
        self.completed_tasks = {}
        
        # Message routing
        self.message_handlers = {}
        self.message_queue = asyncio.Queue()
        self.pending_responses = {}
        
        # Performance tracking
        self.coordination_stats = {
            'total_tasks_coordinated': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'average_coordination_time': 0.0,
            'messages_processed': 0,
            'active_mcps': 0
        }
        
        # Health monitoring
        self.health_check_interval = 30.0  # seconds
        self.health_check_task = None
        
        # Initialize message handlers
        self._initialize_message_handlers()
        
        self.logger.info("MCPCoordinatorIntegration initialized")
    
    async def start_coordinator(self) -> bool:
        """
        Start the MCP coordinator
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            self.logger.info("Starting MCP Coordinator...")
            
            # Start message processing
            asyncio.create_task(self._process_messages())
            
            # Start task processing
            asyncio.create_task(self._process_tasks())
            
            # Start health monitoring
            if self.enable_monitoring:
                self.health_check_task = asyncio.create_task(self._health_monitor())
            
            # Register core MCPs
            await self._register_core_mcps()
            
            self.logger.info("MCP Coordinator started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start MCP Coordinator: {str(e)}")
            return False
    
    async def register_mcp(self, registration: MCPRegistration) -> bool:
        """
        Register an MCP with the coordinator
        
        Args:
            registration: MCP registration information
            
        Returns:
            bool: True if registration successful, False otherwise
        """
        try:
            self.logger.info(f"Registering MCP: {registration.mcp_id}")
            
            # Validate registration
            if not await self._validate_mcp_registration(registration):
                raise ValueError("Invalid MCP registration")
            
            # Store registration
            self.registered_mcps[registration.mcp_id] = registration
            self.mcp_capabilities[registration.mcp_id] = registration.capabilities
            
            # Initialize performance tracking
            self.mcp_performance[registration.mcp_id] = {
                'tasks_completed': 0,
                'tasks_failed': 0,
                'average_execution_time': 0.0,
                'last_activity': time.time(),
                'health_score': 1.0
            }
            
            # Update statistics
            self.coordination_stats['active_mcps'] = len(self.registered_mcps)
            
            # Send registration confirmation
            await self._send_registration_confirmation(registration.mcp_id)
            
            self.logger.info(f"MCP {registration.mcp_id} registered successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register MCP {registration.mcp_id}: {str(e)}")
            return False
    
    async def coordinate_task(self, task: Any, routing_preference: Optional[str] = None) -> Dict[str, Any]:
        """
        Coordinate task execution across MCPs
        
        Args:
            task: Task to coordinate
            routing_preference: Optional routing preference
            
        Returns:
            Dict: Coordination result
        """
        start_time = time.time()
        task_id = getattr(task, 'id', f"task_{uuid.uuid4().hex[:8]}")
        
        try:
            self.logger.info(f"Coordinating task: {task_id}")
            
            # Create task execution record
            task_execution = TaskExecution(
                task_id=task_id,
                original_task=task,
                assigned_mcp="",
                routing_decision={},
                start_time=start_time,
                status="routing",
                progress=0.0,
                estimated_completion=None,
                result=None,
                error=None
            )
            
            self.active_tasks[task_id] = task_execution
            
            # Route task to appropriate MCP
            routing_result = await self._route_task(task, routing_preference)
            task_execution.routing_decision = routing_result
            task_execution.assigned_mcp = routing_result.get('assigned_mcp', '')
            
            # Validate MCP availability
            if not await self._validate_mcp_availability(task_execution.assigned_mcp):
                raise Exception(f"Assigned MCP {task_execution.assigned_mcp} is not available")
            
            # Send task to assigned MCP
            task_execution.status = "executing"
            execution_result = await self._execute_task_on_mcp(task, task_execution.assigned_mcp, routing_result)
            
            # Process execution result
            coordination_result = await self._process_task_result(task_execution, execution_result)
            
            # Update statistics
            coordination_time = time.time() - start_time
            await self._update_coordination_stats(task_execution, coordination_time, True)
            
            self.logger.info(f"Task {task_id} coordinated successfully in {coordination_time:.2f}s")
            return coordination_result
            
        except Exception as e:
            coordination_time = time.time() - start_time
            await self._update_coordination_stats(task_execution, coordination_time, False)
            
            self.logger.error(f"Task coordination failed for {task_id}: {str(e)}")
            
            # Try fallback coordination
            fallback_result = await self._attempt_fallback_coordination(task, str(e))
            return fallback_result
    
    async def _route_task(self, task: Any, routing_preference: Optional[str] = None) -> Dict[str, Any]:
        """
        Route task to appropriate MCP
        
        Args:
            task: Task to route
            routing_preference: Optional routing preference
            
        Returns:
            Dict: Routing result
        """
        # Import and use the intelligent task router
        from .intelligent_task_router import IntelligentTaskRouter
        
        router = IntelligentTaskRouter(self.config.get('router_config', {}))
        routing_result = await router.route_task(task)
        
        # Map routing decision to MCP assignment
        mcp_assignment = await self._map_routing_to_mcp(routing_result, routing_preference)
        
        return {
            'routing_decision': routing_result.decision.value,
            'primary_engine': routing_result.primary_engine.value,
            'assigned_mcp': mcp_assignment['mcp_id'],
            'confidence_score': routing_result.confidence_score,
            'reasoning': routing_result.reasoning,
            'fallback_mcp': mcp_assignment.get('fallback_mcp'),
            'routing_metadata': routing_result.routing_metadata
        }
    
    async def _map_routing_to_mcp(self, routing_result: Any, routing_preference: Optional[str] = None) -> Dict[str, Any]:
        """
        Map routing decision to specific MCP assignment
        
        Args:
            routing_result: Routing result from intelligent router
            routing_preference: Optional routing preference
            
        Returns:
            Dict: MCP assignment
        """
        primary_engine = routing_result.primary_engine.value
        
        # Map engine types to MCP IDs
        engine_to_mcp_mapping = {
            'trae_agent': 'trae_agent_mcp',
            'powerautomation_native': 'powerautomation_native_mcp',
            'hybrid': 'hybrid_coordination_mcp'
        }
        
        assigned_mcp = engine_to_mcp_mapping.get(primary_engine, 'powerautomation_native_mcp')
        
        # Check if preferred MCP is available
        if routing_preference and routing_preference in self.registered_mcps:
            if await self._validate_mcp_availability(routing_preference):
                assigned_mcp = routing_preference
        
        # Determine fallback MCP
        fallback_mcp = None
        if routing_result.secondary_engine:
            fallback_mcp = engine_to_mcp_mapping.get(routing_result.secondary_engine.value)
        
        # Load balancing for multiple instances
        if self.enable_load_balancing:
            assigned_mcp = await self._apply_load_balancing(assigned_mcp)
        
        return {
            'mcp_id': assigned_mcp,
            'fallback_mcp': fallback_mcp,
            'load_balanced': self.enable_load_balancing
        }
    
    async def _apply_load_balancing(self, base_mcp_id: str) -> str:
        """
        Apply load balancing to select optimal MCP instance
        
        Args:
            base_mcp_id: Base MCP ID
            
        Returns:
            str: Selected MCP ID
        """
        # Find all instances of the MCP type
        mcp_instances = [
            mcp_id for mcp_id in self.registered_mcps.keys()
            if mcp_id.startswith(base_mcp_id)
        ]
        
        if not mcp_instances:
            return base_mcp_id
        
        # Select instance with lowest load
        best_instance = base_mcp_id
        lowest_load = float('inf')
        
        for instance_id in mcp_instances:
            if instance_id in self.mcp_performance:
                # Calculate load score (active tasks + recent failures)
                active_tasks = sum(1 for task in self.active_tasks.values() if task.assigned_mcp == instance_id)
                recent_failures = self.mcp_performance[instance_id].get('tasks_failed', 0)
                health_score = self.mcp_performance[instance_id].get('health_score', 1.0)
                
                load_score = active_tasks + (recent_failures * 0.1) + (1.0 - health_score)
                
                if load_score < lowest_load:
                    lowest_load = load_score
                    best_instance = instance_id
        
        return best_instance
    
    async def _validate_mcp_availability(self, mcp_id: str) -> bool:
        """
        Validate MCP availability
        
        Args:
            mcp_id: MCP ID to validate
            
        Returns:
            bool: True if available, False otherwise
        """
        if mcp_id not in self.registered_mcps:
            return False
        
        mcp_registration = self.registered_mcps[mcp_id]
        
        # Check status
        if mcp_registration.status not in [MCPStatus.READY, MCPStatus.BUSY]:
            return False
        
        # Check last heartbeat
        time_since_heartbeat = time.time() - mcp_registration.last_heartbeat
        if time_since_heartbeat > mcp_registration.health_check_interval * 2:
            return False
        
        return True
    
    async def _execute_task_on_mcp(self, task: Any, mcp_id: str, routing_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute task on assigned MCP
        
        Args:
            task: Task to execute
            mcp_id: Target MCP ID
            routing_result: Routing result
            
        Returns:
            Dict: Execution result
        """
        # Create task request message
        task_message = MCPMessage(
            message_id=f"task_{uuid.uuid4().hex[:8]}",
            message_type=MCPMessageType.TASK_REQUEST,
            source_mcp=self.coordinator_id,
            target_mcp=mcp_id,
            timestamp=time.time(),
            payload={
                'task': self._serialize_task(task),
                'routing_context': routing_result,
                'execution_config': await self._get_execution_config(mcp_id, routing_result)
            }
        )
        
        # Send message and wait for response
        response = await self._send_message_and_wait(task_message, timeout=300.0)
        
        if not response:
            raise Exception(f"No response from MCP {mcp_id}")
        
        if response.message_type != MCPMessageType.TASK_RESPONSE:
            raise Exception(f"Unexpected response type: {response.message_type}")
        
        return response.payload
    
    async def _get_execution_config(self, mcp_id: str, routing_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get execution configuration for MCP
        
        Args:
            mcp_id: MCP ID
            routing_result: Routing result
            
        Returns:
            Dict: Execution configuration
        """
        base_config = {
            'timeout': 300.0,
            'priority': 5,
            'retry_count': 3,
            'enable_monitoring': True
        }
        
        # MCP-specific configuration
        if mcp_id == 'trae_agent_mcp':
            base_config.update({
                'model_config': routing_result.get('routing_metadata', {}).get('optimal_model'),
                'tools_config': routing_result.get('routing_metadata', {}).get('optimal_tools'),
                'performance_mode': 'accuracy' if routing_result.get('confidence_score', 0) > 0.8 else 'balanced'
            })
        elif mcp_id == 'powerautomation_native_mcp':
            base_config.update({
                'execution_mode': 'fast',
                'resource_limit': 'medium',
                'enable_caching': True
            })
        elif mcp_id == 'hybrid_coordination_mcp':
            base_config.update({
                'coordination_strategy': 'parallel',
                'result_aggregation': 'best_of_both',
                'timeout': 600.0  # Longer timeout for hybrid
            })
        
        return base_config
    
    async def _send_message_and_wait(self, message: MCPMessage, timeout: float = 30.0) -> Optional[MCPMessage]:
        """
        Send message and wait for response
        
        Args:
            message: Message to send
            timeout: Response timeout
            
        Returns:
            Optional[MCPMessage]: Response message or None
        """
        # Store pending response
        response_future = asyncio.Future()
        self.pending_responses[message.message_id] = response_future
        
        try:
            # Send message
            await self._send_message(message)
            
            # Wait for response
            response = await asyncio.wait_for(response_future, timeout=timeout)
            return response
            
        except asyncio.TimeoutError:
            self.logger.error(f"Message {message.message_id} timed out")
            return None
        finally:
            # Clean up pending response
            self.pending_responses.pop(message.message_id, None)
    
    async def _send_message(self, message: MCPMessage):
        """
        Send message to target MCP
        
        Args:
            message: Message to send
        """
        # Add to message queue for processing
        await self.message_queue.put(message)
        
        # Update statistics
        self.coordination_stats['messages_processed'] += 1
    
    async def _process_messages(self):
        """Process messages from the message queue"""
        while True:
            try:
                # Get message from queue
                message = await self.message_queue.get()
                
                # Route message to appropriate handler
                await self._route_message(message)
                
                # Mark task as done
                self.message_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Error processing message: {str(e)}")
    
    async def _route_message(self, message: MCPMessage):
        """
        Route message to appropriate handler
        
        Args:
            message: Message to route
        """
        message_type = message.message_type
        
        if message_type in self.message_handlers:
            handler = self.message_handlers[message_type]
            await handler(message)
        else:
            self.logger.warning(f"No handler for message type: {message_type}")
    
    async def _process_tasks(self):
        """Process tasks from the task queue"""
        while True:
            try:
                # Get task from queue
                task_data = await self.task_queue.get()
                
                # Process task
                await self._process_single_task(task_data)
                
                # Mark task as done
                self.task_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Error processing task: {str(e)}")
    
    async def _process_single_task(self, task_data: Dict[str, Any]):
        """
        Process a single task
        
        Args:
            task_data: Task data to process
        """
        # Implementation would depend on task type
        # For now, just log the task processing
        self.logger.info(f"Processing task: {task_data.get('task_id', 'unknown')}")
    
    async def _health_monitor(self):
        """Monitor health of registered MCPs"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                # Check health of all registered MCPs
                for mcp_id in list(self.registered_mcps.keys()):
                    await self._check_mcp_health(mcp_id)
                
            except Exception as e:
                self.logger.error(f"Error in health monitor: {str(e)}")
    
    async def _check_mcp_health(self, mcp_id: str):
        """
        Check health of specific MCP
        
        Args:
            mcp_id: MCP ID to check
        """
        try:
            # Send health check message
            health_message = MCPMessage(
                message_id=f"health_{uuid.uuid4().hex[:8]}",
                message_type=MCPMessageType.HEALTH_CHECK,
                source_mcp=self.coordinator_id,
                target_mcp=mcp_id,
                timestamp=time.time(),
                payload={'check_type': 'routine'}
            )
            
            # Send and wait for response
            response = await self._send_message_and_wait(health_message, timeout=10.0)
            
            if response:
                # Update MCP status based on response
                await self._update_mcp_health_status(mcp_id, response.payload)
            else:
                # No response - mark as potentially unhealthy
                await self._handle_mcp_health_failure(mcp_id)
                
        except Exception as e:
            self.logger.error(f"Health check failed for MCP {mcp_id}: {str(e)}")
            await self._handle_mcp_health_failure(mcp_id)
    
    async def _update_mcp_health_status(self, mcp_id: str, health_data: Dict[str, Any]):
        """
        Update MCP health status
        
        Args:
            mcp_id: MCP ID
            health_data: Health data from MCP
        """
        if mcp_id in self.registered_mcps:
            registration = self.registered_mcps[mcp_id]
            registration.last_heartbeat = time.time()
            
            # Update health score
            if mcp_id in self.mcp_performance:
                health_score = health_data.get('health_score', 1.0)
                self.mcp_performance[mcp_id]['health_score'] = health_score
                
                # Update status based on health
                if health_score > 0.8:
                    registration.status = MCPStatus.READY
                elif health_score > 0.5:
                    registration.status = MCPStatus.BUSY
                else:
                    registration.status = MCPStatus.ERROR
    
    async def _handle_mcp_health_failure(self, mcp_id: str):
        """
        Handle MCP health check failure
        
        Args:
            mcp_id: MCP ID that failed health check
        """
        if mcp_id in self.registered_mcps:
            registration = self.registered_mcps[mcp_id]
            registration.status = MCPStatus.ERROR
            
            # Update performance metrics
            if mcp_id in self.mcp_performance:
                self.mcp_performance[mcp_id]['health_score'] = 0.0
            
            self.logger.warning(f"MCP {mcp_id} marked as unhealthy")
    
    def _initialize_message_handlers(self):
        """Initialize message handlers"""
        self.message_handlers = {
            MCPMessageType.TASK_RESPONSE: self._handle_task_response,
            MCPMessageType.STATUS_UPDATE: self._handle_status_update,
            MCPMessageType.HEALTH_CHECK: self._handle_health_check_response,
            MCPMessageType.ERROR_NOTIFICATION: self._handle_error_notification,
            MCPMessageType.PERFORMANCE_METRICS: self._handle_performance_metrics
        }
    
    async def _handle_task_response(self, message: MCPMessage):
        """Handle task response message"""
        # Find pending response and resolve it
        if message.correlation_id in self.pending_responses:
            future = self.pending_responses[message.correlation_id]
            if not future.done():
                future.set_result(message)
    
    async def _handle_status_update(self, message: MCPMessage):
        """Handle status update message"""
        mcp_id = message.source_mcp
        status_data = message.payload
        
        if mcp_id in self.registered_mcps:
            # Update MCP status
            new_status = MCPStatus(status_data.get('status', 'ready'))
            self.registered_mcps[mcp_id].status = new_status
            
            self.logger.info(f"MCP {mcp_id} status updated to {new_status.value}")
    
    async def _handle_health_check_response(self, message: MCPMessage):
        """Handle health check response message"""
        await self._update_mcp_health_status(message.source_mcp, message.payload)
    
    async def _handle_error_notification(self, message: MCPMessage):
        """Handle error notification message"""
        mcp_id = message.source_mcp
        error_data = message.payload
        
        self.logger.error(f"Error notification from MCP {mcp_id}: {error_data}")
        
        # Update MCP status if severe error
        if error_data.get('severity') == 'critical':
            if mcp_id in self.registered_mcps:
                self.registered_mcps[mcp_id].status = MCPStatus.ERROR
    
    async def _handle_performance_metrics(self, message: MCPMessage):
        """Handle performance metrics message"""
        mcp_id = message.source_mcp
        metrics_data = message.payload
        
        if mcp_id in self.mcp_performance:
            # Update performance metrics
            performance = self.mcp_performance[mcp_id]
            performance.update(metrics_data)
            performance['last_activity'] = time.time()
    
    async def _register_core_mcps(self):
        """Register core MCPs with the coordinator"""
        # Register Trae Agent MCP
        trae_registration = MCPRegistration(
            mcp_id="trae_agent_mcp",
            mcp_name="Trae Agent MCP",
            mcp_type="software_engineering",
            capabilities=["code_analysis", "debugging", "refactoring", "architecture_design"],
            endpoints={"task_execution": "/trae/execute", "health": "/trae/health"},
            status=MCPStatus.READY,
            health_check_interval=30.0,
            last_heartbeat=time.time(),
            metadata={"version": "1.0.0", "engine_type": "trae_agent"}
        )
        
        await self.register_mcp(trae_registration)
        
        # Register PowerAutomation Native MCP
        native_registration = MCPRegistration(
            mcp_id="powerautomation_native_mcp",
            mcp_name="PowerAutomation Native MCP",
            mcp_type="automation",
            capabilities=["automation", "system_management", "data_processing"],
            endpoints={"task_execution": "/native/execute", "health": "/native/health"},
            status=MCPStatus.READY,
            health_check_interval=30.0,
            last_heartbeat=time.time(),
            metadata={"version": "4.0.0", "engine_type": "powerautomation_native"}
        )
        
        await self.register_mcp(native_registration)
    
    async def _validate_mcp_registration(self, registration: MCPRegistration) -> bool:
        """Validate MCP registration"""
        # Check required fields
        if not all([registration.mcp_id, registration.mcp_name, registration.mcp_type]):
            return False
        
        # Check for duplicate registration
        if registration.mcp_id in self.registered_mcps:
            return False
        
        # Validate capabilities
        if not registration.capabilities:
            return False
        
        return True
    
    async def _send_registration_confirmation(self, mcp_id: str):
        """Send registration confirmation to MCP"""
        confirmation_message = MCPMessage(
            message_id=f"reg_confirm_{uuid.uuid4().hex[:8]}",
            message_type=MCPMessageType.REGISTRATION,
            source_mcp=self.coordinator_id,
            target_mcp=mcp_id,
            timestamp=time.time(),
            payload={
                'status': 'confirmed',
                'coordinator_id': self.coordinator_id,
                'registration_time': time.time()
            }
        )
        
        await self._send_message(confirmation_message)
    
    def _serialize_task(self, task: Any) -> Dict[str, Any]:
        """Serialize task for transmission"""
        return {
            'id': getattr(task, 'id', 'unknown'),
            'description': getattr(task, 'description', ''),
            'files': getattr(task, 'files', []),
            'context': getattr(task, 'context', {}),
            'priority': getattr(task, 'priority', 'normal'),
            'metadata': getattr(task, 'metadata', {})
        }
    
    async def _process_task_result(self, task_execution: TaskExecution, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Process task execution result"""
        task_execution.result = execution_result
        task_execution.status = "completed" if execution_result.get('success', False) else "failed"
        task_execution.progress = 1.0
        
        # Move to completed tasks
        self.completed_tasks[task_execution.task_id] = task_execution
        self.active_tasks.pop(task_execution.task_id, None)
        
        return {
            'task_id': task_execution.task_id,
            'success': execution_result.get('success', False),
            'result': execution_result,
            'coordination_metadata': {
                'assigned_mcp': task_execution.assigned_mcp,
                'routing_decision': task_execution.routing_decision,
                'execution_time': time.time() - task_execution.start_time
            }
        }
    
    async def _attempt_fallback_coordination(self, task: Any, error_message: str) -> Dict[str, Any]:
        """Attempt fallback coordination when primary coordination fails"""
        return {
            'task_id': getattr(task, 'id', 'unknown'),
            'success': False,
            'error': error_message,
            'fallback_attempted': True,
            'coordination_metadata': {
                'fallback_reason': error_message,
                'fallback_timestamp': time.time()
            }
        }
    
    async def _update_coordination_stats(self, task_execution: TaskExecution, coordination_time: float, success: bool):
        """Update coordination statistics"""
        self.coordination_stats['total_tasks_coordinated'] += 1
        
        if success:
            self.coordination_stats['successful_tasks'] += 1
        else:
            self.coordination_stats['failed_tasks'] += 1
        
        # Update average coordination time
        total_tasks = self.coordination_stats['total_tasks_coordinated']
        current_avg = self.coordination_stats['average_coordination_time']
        self.coordination_stats['average_coordination_time'] = (
            (current_avg * (total_tasks - 1) + coordination_time) / total_tasks
        )
        
        # Update MCP performance if task was assigned
        if task_execution.assigned_mcp and task_execution.assigned_mcp in self.mcp_performance:
            mcp_perf = self.mcp_performance[task_execution.assigned_mcp]
            if success:
                mcp_perf['tasks_completed'] += 1
            else:
                mcp_perf['tasks_failed'] += 1
            
            # Update average execution time
            total_mcp_tasks = mcp_perf['tasks_completed'] + mcp_perf['tasks_failed']
            current_mcp_avg = mcp_perf['average_execution_time']
            mcp_perf['average_execution_time'] = (
                (current_mcp_avg * (total_mcp_tasks - 1) + coordination_time) / total_mcp_tasks
            )
    
    async def get_coordination_stats(self) -> Dict[str, Any]:
        """Get coordination statistics"""
        stats = self.coordination_stats.copy()
        
        # Add success rate
        total_tasks = stats['total_tasks_coordinated']
        if total_tasks > 0:
            stats['success_rate'] = stats['successful_tasks'] / total_tasks
        else:
            stats['success_rate'] = 0.0
        
        # Add MCP performance summary
        stats['mcp_performance'] = self.mcp_performance.copy()
        
        # Add active task count
        stats['active_tasks_count'] = len(self.active_tasks)
        
        return stats
    
    async def get_registered_mcps(self) -> Dict[str, Dict[str, Any]]:
        """Get information about registered MCPs"""
        return {
            mcp_id: {
                'name': reg.mcp_name,
                'type': reg.mcp_type,
                'status': reg.status.value,
                'capabilities': reg.capabilities,
                'last_heartbeat': reg.last_heartbeat,
                'performance': self.mcp_performance.get(mcp_id, {})
            }
            for mcp_id, reg in self.registered_mcps.items()
        }
    
    async def shutdown(self):
        """Gracefully shutdown the coordinator"""
        try:
            self.logger.info("Shutting down MCP Coordinator...")
            
            # Cancel health check task
            if self.health_check_task:
                self.health_check_task.cancel()
            
            # Notify all MCPs of shutdown
            for mcp_id in self.registered_mcps.keys():
                shutdown_message = MCPMessage(
                    message_id=f"shutdown_{uuid.uuid4().hex[:8]}",
                    message_type=MCPMessageType.DEREGISTRATION,
                    source_mcp=self.coordinator_id,
                    target_mcp=mcp_id,
                    timestamp=time.time(),
                    payload={'reason': 'coordinator_shutdown'}
                )
                await self._send_message(shutdown_message)
            
            # Wait for pending tasks to complete (with timeout)
            try:
                await asyncio.wait_for(self.task_queue.join(), timeout=30.0)
                await asyncio.wait_for(self.message_queue.join(), timeout=30.0)
            except asyncio.TimeoutError:
                self.logger.warning("Timeout waiting for queues to empty during shutdown")
            
            self.logger.info("MCP Coordinator shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during coordinator shutdown: {str(e)}")

