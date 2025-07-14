"""
Trae Client - Interface for Trae Agent Communication

This module provides the client interface for communicating with Trae Agent,
handling all low-level communication, configuration, and task execution.
"""

import asyncio
import json
import logging
import subprocess
import tempfile
import os
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TraeConfig:
    """Configuration for Trae Agent"""
    model: str = "claude-3-sonnet"
    temperature: float = 0.1
    max_tokens: int = 4000
    tools: List[str] = None
    working_directory: str = None
    timeout: int = 300
    debug: bool = False


@dataclass
class TraeTask:
    """Task representation for Trae Agent"""
    instruction: str
    context: Dict[str, Any]
    files: List[str]
    tools: List[str]
    model_preferences: Dict[str, Any]
    timeout: int = 300
    metadata: Dict[str, Any] = None


@dataclass
class TraeResult:
    """Result from Trae Agent execution"""
    success: bool
    output: str
    files_modified: List[str]
    tools_used: List[str]
    model_used: str
    execution_time: float
    trajectory: List[Dict[str, Any]]
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


class TraeClient:
    """
    Trae Agent Client
    
    Provides interface for communicating with Trae Agent, handling task execution,
    configuration management, and result processing.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Trae Client
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Trae Agent configuration
        self.trae_executable = self.config.get('trae_executable', 'trae')
        self.working_directory = self.config.get('working_directory', tempfile.mkdtemp())
        self.default_model = self.config.get('default_model', 'claude-3-sonnet')
        self.default_timeout = self.config.get('default_timeout', 300)
        
        # Client state
        self.is_initialized = False
        self.current_config = None
        self.session_id = None
        
        # Performance tracking
        self.execution_count = 0
        self.total_execution_time = 0.0
        
        self.logger.info("TraeClient initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize the Trae Client
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Initializing Trae Client...")
            
            # Check if Trae Agent is available
            if not await self._check_trae_availability():
                raise Exception("Trae Agent not available or not installed")
            
            # Create working directory if it doesn't exist
            os.makedirs(self.working_directory, exist_ok=True)
            
            # Initialize session
            self.session_id = f"trae_session_{int(time.time())}"
            
            # Test basic functionality
            test_result = await self._test_basic_functionality()
            if not test_result:
                raise Exception("Trae Agent basic functionality test failed")
            
            self.is_initialized = True
            self.logger.info("Trae Client initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Trae Client: {str(e)}")
            self.is_initialized = False
            return False
    
    async def configure(self, config: TraeConfig) -> bool:
        """
        Configure Trae Agent for task execution
        
        Args:
            config: Trae Agent configuration
            
        Returns:
            bool: True if configuration successful, False otherwise
        """
        try:
            self.logger.info(f"Configuring Trae Agent with model: {config.model}")
            
            # Validate configuration
            if not await self._validate_config(config):
                raise Exception("Invalid Trae Agent configuration")
            
            # Store current configuration
            self.current_config = config
            
            self.logger.info("Trae Agent configured successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to configure Trae Agent: {str(e)}")
            return False
    
    async def execute_task(self, task: TraeTask) -> TraeResult:
        """
        Execute a task using Trae Agent
        
        Args:
            task: Task to execute
            
        Returns:
            TraeResult: Execution result
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Executing task with Trae Agent")
            
            # Validate client state
            if not self.is_initialized:
                raise Exception("Trae Client not initialized")
            
            if not self.current_config:
                raise Exception("Trae Agent not configured")
            
            # Prepare task execution environment
            task_dir = await self._prepare_task_environment(task)
            
            # Build Trae Agent command
            command = await self._build_trae_command(task, task_dir)
            
            # Execute Trae Agent
            execution_result = await self._execute_trae_command(command, task_dir, task.timeout)
            
            # Process execution result
            result = await self._process_execution_result(
                execution_result, task, task_dir, start_time
            )
            
            # Update performance tracking
            execution_time = time.time() - start_time
            self.execution_count += 1
            self.total_execution_time += execution_time
            
            self.logger.info(f"Task executed successfully in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Task execution failed: {str(e)}")
            
            return TraeResult(
                success=False,
                output="",
                files_modified=[],
                tools_used=[],
                model_used=self.current_config.model if self.current_config else "unknown",
                execution_time=execution_time,
                trajectory=[],
                error_message=str(e),
                metadata={'error_type': type(e).__name__}
            )
    
    async def _check_trae_availability(self) -> bool:
        """
        Check if Trae Agent is available and accessible
        
        Returns:
            bool: True if Trae Agent is available, False otherwise
        """
        try:
            # Try to run Trae Agent with version command
            process = await asyncio.create_subprocess_exec(
                self.trae_executable, '--version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
            
            if process.returncode == 0:
                version_info = stdout.decode().strip()
                self.logger.info(f"Trae Agent available: {version_info}")
                return True
            else:
                self.logger.error(f"Trae Agent version check failed: {stderr.decode()}")
                return False
                
        except asyncio.TimeoutError:
            self.logger.error("Trae Agent version check timed out")
            return False
        except FileNotFoundError:
            self.logger.error(f"Trae Agent executable not found: {self.trae_executable}")
            return False
        except Exception as e:
            self.logger.error(f"Error checking Trae Agent availability: {str(e)}")
            return False
    
    async def _test_basic_functionality(self) -> bool:
        """
        Test basic Trae Agent functionality
        
        Returns:
            bool: True if basic functionality works, False otherwise
        """
        try:
            # Create a simple test task
            test_instruction = "Echo 'Hello from Trae Agent' to test basic functionality"
            
            # Create test command
            command = [
                self.trae_executable,
                '--model', self.default_model,
                '--instruction', test_instruction,
                '--timeout', str(30)
            ]
            
            # Execute test command
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_directory
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
            
            if process.returncode == 0:
                self.logger.info("Trae Agent basic functionality test passed")
                return True
            else:
                self.logger.error(f"Trae Agent test failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            self.logger.error(f"Trae Agent basic functionality test error: {str(e)}")
            return False
    
    async def _validate_config(self, config: TraeConfig) -> bool:
        """
        Validate Trae Agent configuration
        
        Args:
            config: Configuration to validate
            
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        # Check required fields
        if not config.model:
            self.logger.error("Model not specified in configuration")
            return False
        
        # Validate temperature range
        if not 0.0 <= config.temperature <= 2.0:
            self.logger.error(f"Invalid temperature: {config.temperature}")
            return False
        
        # Validate max_tokens
        if config.max_tokens <= 0:
            self.logger.error(f"Invalid max_tokens: {config.max_tokens}")
            return False
        
        # Validate timeout
        if config.timeout <= 0:
            self.logger.error(f"Invalid timeout: {config.timeout}")
            return False
        
        # Validate working directory
        if config.working_directory and not os.path.exists(config.working_directory):
            try:
                os.makedirs(config.working_directory, exist_ok=True)
            except Exception as e:
                self.logger.error(f"Cannot create working directory: {str(e)}")
                return False
        
        return True
    
    async def _prepare_task_environment(self, task: TraeTask) -> str:
        """
        Prepare execution environment for the task
        
        Args:
            task: Task to prepare environment for
            
        Returns:
            str: Path to task directory
        """
        # Create task-specific directory
        task_id = task.metadata.get('original_task_id', f"task_{int(time.time())}")
        task_dir = os.path.join(self.working_directory, f"task_{task_id}")
        os.makedirs(task_dir, exist_ok=True)
        
        # Copy task files to task directory
        if task.files:
            for file_path in task.files:
                if os.path.exists(file_path):
                    dest_path = os.path.join(task_dir, os.path.basename(file_path))
                    with open(file_path, 'r', encoding='utf-8') as src:
                        with open(dest_path, 'w', encoding='utf-8') as dst:
                            dst.write(src.read())
        
        # Create task context file
        context_file = os.path.join(task_dir, 'task_context.json')
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(task.context, f, indent=2)
        
        return task_dir
    
    async def _build_trae_command(self, task: TraeTask, task_dir: str) -> List[str]:
        """
        Build Trae Agent command for task execution
        
        Args:
            task: Task to execute
            task_dir: Task directory path
            
        Returns:
            List[str]: Command arguments
        """
        command = [self.trae_executable]
        
        # Add model configuration
        command.extend(['--model', self.current_config.model])
        command.extend(['--temperature', str(self.current_config.temperature)])
        command.extend(['--max-tokens', str(self.current_config.max_tokens)])
        
        # Add instruction
        command.extend(['--instruction', task.instruction])
        
        # Add tools
        if task.tools:
            command.extend(['--tools', ','.join(task.tools)])
        
        # Add timeout
        command.extend(['--timeout', str(task.timeout)])
        
        # Add working directory
        command.extend(['--working-dir', task_dir])
        
        # Add debug flag if enabled
        if self.current_config.debug:
            command.append('--debug')
        
        # Add output format
        command.extend(['--output-format', 'json'])
        
        return command
    
    async def _execute_trae_command(self, command: List[str], task_dir: str, timeout: int) -> Dict[str, Any]:
        """
        Execute Trae Agent command
        
        Args:
            command: Command to execute
            task_dir: Task directory
            timeout: Execution timeout
            
        Returns:
            Dict: Execution result
        """
        try:
            self.logger.info(f"Executing Trae command: {' '.join(command)}")
            
            # Execute command
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=task_dir
            )
            
            # Wait for completion with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            # Parse result
            result = {
                'returncode': process.returncode,
                'stdout': stdout.decode('utf-8'),
                'stderr': stderr.decode('utf-8'),
                'success': process.returncode == 0
            }
            
            return result
            
        except asyncio.TimeoutError:
            self.logger.error(f"Trae Agent execution timed out after {timeout}s")
            # Kill the process if it's still running
            if process.returncode is None:
                process.kill()
                await process.wait()
            
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': f'Execution timed out after {timeout} seconds',
                'success': False
            }
        
        except Exception as e:
            self.logger.error(f"Error executing Trae command: {str(e)}")
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'success': False
            }
    
    async def _process_execution_result(
        self, 
        execution_result: Dict[str, Any], 
        task: TraeTask, 
        task_dir: str, 
        start_time: float
    ) -> TraeResult:
        """
        Process Trae Agent execution result
        
        Args:
            execution_result: Raw execution result
            task: Original task
            task_dir: Task directory
            start_time: Execution start time
            
        Returns:
            TraeResult: Processed result
        """
        execution_time = time.time() - start_time
        
        if not execution_result['success']:
            return TraeResult(
                success=False,
                output=execution_result['stderr'],
                files_modified=[],
                tools_used=[],
                model_used=self.current_config.model,
                execution_time=execution_time,
                trajectory=[],
                error_message=execution_result['stderr'],
                metadata={'returncode': execution_result['returncode']}
            )
        
        try:
            # Parse JSON output if available
            output_data = {}
            if execution_result['stdout']:
                try:
                    output_data = json.loads(execution_result['stdout'])
                except json.JSONDecodeError:
                    output_data = {'raw_output': execution_result['stdout']}
            
            # Find modified files
            files_modified = await self._find_modified_files(task_dir, task.files)
            
            # Extract trajectory if available
            trajectory = output_data.get('trajectory', [])
            
            # Extract tools used
            tools_used = output_data.get('tools_used', task.tools or [])
            
            return TraeResult(
                success=True,
                output=output_data.get('output', execution_result['stdout']),
                files_modified=files_modified,
                tools_used=tools_used,
                model_used=output_data.get('model_used', self.current_config.model),
                execution_time=execution_time,
                trajectory=trajectory,
                metadata={
                    'returncode': execution_result['returncode'],
                    'task_dir': task_dir,
                    'raw_output': output_data
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error processing execution result: {str(e)}")
            return TraeResult(
                success=False,
                output=execution_result['stdout'],
                files_modified=[],
                tools_used=[],
                model_used=self.current_config.model,
                execution_time=execution_time,
                trajectory=[],
                error_message=f"Result processing error: {str(e)}",
                metadata={'processing_error': str(e)}
            )
    
    async def _find_modified_files(self, task_dir: str, original_files: List[str]) -> List[str]:
        """
        Find files that were modified during task execution
        
        Args:
            task_dir: Task directory
            original_files: List of original files
            
        Returns:
            List[str]: List of modified files
        """
        modified_files = []
        
        try:
            # Check all files in task directory
            for root, dirs, files in os.walk(task_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Skip system files
                    if file.startswith('.') or file == 'task_context.json':
                        continue
                    
                    # Check if file was modified or is new
                    relative_path = os.path.relpath(file_path, task_dir)
                    modified_files.append(relative_path)
            
            return modified_files
            
        except Exception as e:
            self.logger.error(f"Error finding modified files: {str(e)}")
            return []
    
    async def health_check(self) -> bool:
        """
        Perform health check on Trae Client
        
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            # Check if initialized
            if not self.is_initialized:
                return False
            
            # Check Trae Agent availability
            if not await self._check_trae_availability():
                return False
            
            # Check working directory
            if not os.path.exists(self.working_directory):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics
        
        Returns:
            Dict: Performance statistics
        """
        avg_execution_time = (
            self.total_execution_time / self.execution_count 
            if self.execution_count > 0 else 0.0
        )
        
        return {
            'execution_count': self.execution_count,
            'total_execution_time': self.total_execution_time,
            'average_execution_time': avg_execution_time,
            'is_initialized': self.is_initialized,
            'working_directory': self.working_directory,
            'current_model': self.current_config.model if self.current_config else None
        }
    
    async def shutdown(self):
        """
        Gracefully shutdown the client
        """
        try:
            self.logger.info("Shutting down Trae Client...")
            
            # Clean up temporary files if needed
            # (Implementation depends on cleanup requirements)
            
            self.is_initialized = False
            self.current_config = None
            self.session_id = None
            
            self.logger.info("Trae Client shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during Trae Client shutdown: {str(e)}")

