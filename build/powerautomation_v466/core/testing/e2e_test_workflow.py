#!/usr/bin/env python3
"""
PowerAutomation End-to-End Test Workflow System
端到端測試工作流系統

功能：
- 完整的E2E測試編排和執行
- 跨平台測試環境管理
- 自動化測試數據準備
- 測試結果收集和分析
- 與CI/CD管道深度集成
- 測試報告和可視化

Author: PowerAutomation Team
Version: 1.0.0
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess
import tempfile
import shutil

import pytest
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
import requests
import docker
import yaml


class TestEnvironment(Enum):
    """測試環境枚舉"""
    LOCAL = "local"
    DOCKER = "docker"
    STAGING = "staging"
    PRODUCTION = "production"
    CLOUD = "cloud"


class TestType(Enum):
    """測試類型枚舉"""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"
    COMPATIBILITY = "compatibility"


class TestStatus(Enum):
    """測試狀態枚舉"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestCase:
    """測試用例數據類"""
    id: str
    name: str
    description: str
    test_type: TestType
    environment: TestEnvironment
    tags: List[str]
    priority: int  # 1-5, 5 為最高優先級
    estimated_duration: int  # 預估執行時間(秒)
    dependencies: List[str]
    preconditions: List[str]
    steps: List[Dict[str, Any]]
    expected_results: List[str]
    test_data: Dict[str, Any]
    status: TestStatus
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    error_message: Optional[str]
    screenshots: List[str]
    logs: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            **asdict(self),
            'test_type': self.test_type.value,
            'environment': self.environment.value,
            'status': self.status.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None
        }


@dataclass
class TestSuite:
    """測試套件數據類"""
    id: str
    name: str
    description: str
    test_cases: List[TestCase]
    environment: TestEnvironment
    parallel_execution: bool
    max_workers: int
    timeout: int  # 套件總超時時間(秒)
    setup_scripts: List[str]
    teardown_scripts: List[str]
    status: TestStatus
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    passed_count: int
    failed_count: int
    skipped_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'test_cases': [tc.to_dict() for tc in self.test_cases],
            'environment': self.environment.value,
            'parallel_execution': self.parallel_execution,
            'max_workers': self.max_workers,
            'timeout': self.timeout,
            'setup_scripts': self.setup_scripts,
            'teardown_scripts': self.teardown_scripts,
            'status': self.status.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'passed_count': self.passed_count,
            'failed_count': self.failed_count,
            'skipped_count': self.skipped_count
        }


class EnvironmentManager:
    """測試環境管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.docker_client = docker.from_env() if self._is_docker_available() else None
        self.active_containers = {}
        
    def _is_docker_available(self) -> bool:
        """檢查Docker是否可用"""
        try:
            docker.from_env().ping()
            return True
        except:
            return False
    
    async def setup_environment(self, environment: TestEnvironment, config: Dict[str, Any]) -> Dict[str, Any]:
        """設置測試環境"""
        self.logger.info(f"正在設置測試環境: {environment.value}")
        
        if environment == TestEnvironment.LOCAL:
            return await self._setup_local_environment(config)
        elif environment == TestEnvironment.DOCKER:
            return await self._setup_docker_environment(config)
        elif environment == TestEnvironment.STAGING:
            return await self._setup_staging_environment(config)
        elif environment == TestEnvironment.CLOUD:
            return await self._setup_cloud_environment(config)
        else:
            raise ValueError(f"不支持的環境類型: {environment}")
    
    async def _setup_local_environment(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """設置本地測試環境"""
        env_info = {
            'type': 'local',
            'base_url': config.get('base_url', 'http://localhost:3000'),
            'api_url': config.get('api_url', 'http://localhost:8000'),
            'database_url': config.get('database_url', 'sqlite:///test.db'),
            'browser': config.get('browser', 'chrome')
        }
        
        # 啟動本地服務
        services = config.get('services', [])
        for service in services:
            await self._start_local_service(service)
        
        # 等待服務就緒
        await self._wait_for_services(env_info)
        
        return env_info
    
    async def _setup_docker_environment(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """設置Docker測試環境"""
        if not self.docker_client:
            raise RuntimeError("Docker不可用")
        
        compose_file = config.get('compose_file', 'docker-compose.test.yml')
        network_name = f"test_network_{uuid.uuid4().hex[:8]}"
        
        # 創建測試網絡
        network = self.docker_client.networks.create(network_name)
        
        # 啟動容器
        containers = []
        for service_config in config.get('services', []):
            container = await self._start_docker_container(service_config, network_name)
            containers.append(container)
            self.active_containers[container.id] = container
        
        # 獲取服務端點
        env_info = {
            'type': 'docker',
            'network': network_name,
            'containers': [c.id for c in containers],
            'base_url': await self._get_service_url('web', containers),
            'api_url': await self._get_service_url('api', containers),
            'database_url': await self._get_service_url('database', containers)
        }
        
        # 等待服務就緒
        await self._wait_for_services(env_info)
        
        return env_info
    
    async def _start_docker_container(self, service_config: Dict[str, Any], network_name: str):
        """啟動Docker容器"""
        container = self.docker_client.containers.run(
            image=service_config['image'],
            name=f"{service_config['name']}_{uuid.uuid4().hex[:8]}",
            environment=service_config.get('environment', {}),
            ports=service_config.get('ports', {}),
            volumes=service_config.get('volumes', {}),
            network=network_name,
            detach=True,
            remove=True
        )
        
        self.logger.info(f"啟動容器: {container.name}")
        return container
    
    async def _wait_for_services(self, env_info: Dict[str, Any]):
        """等待服務就緒"""
        max_retries = 30
        retry_interval = 2
        
        for i in range(max_retries):
            try:
                # 檢查Web服務
                if 'base_url' in env_info:
                    response = requests.get(f"{env_info['base_url']}/health", timeout=5)
                    if response.status_code != 200:
                        raise requests.RequestException()
                
                # 檢查API服務
                if 'api_url' in env_info:
                    response = requests.get(f"{env_info['api_url']}/health", timeout=5)
                    if response.status_code != 200:
                        raise requests.RequestException()
                
                self.logger.info("所有服務已就緒")
                return
                
            except Exception as e:
                if i == max_retries - 1:
                    raise RuntimeError(f"服務啟動超時: {e}")
                
                await asyncio.sleep(retry_interval)
    
    async def cleanup_environment(self, env_info: Dict[str, Any]):
        """清理測試環境"""
        env_type = env_info.get('type')
        
        if env_type == 'docker':
            # 清理Docker容器和網絡
            for container_id in env_info.get('containers', []):
                try:
                    container = self.docker_client.containers.get(container_id)
                    container.stop(timeout=10)
                    container.remove()
                    self.logger.info(f"清理容器: {container_id}")
                except Exception as e:
                    self.logger.warning(f"清理容器失敗: {e}")
            
            # 清理網絡
            if 'network' in env_info:
                try:
                    network = self.docker_client.networks.get(env_info['network'])
                    network.remove()
                    self.logger.info(f"清理網絡: {env_info['network']}")
                except Exception as e:
                    self.logger.warning(f"清理網絡失敗: {e}")


class WebDriverManager:
    """WebDriver管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.drivers = {}
        self.logger = logging.getLogger(__name__)
    
    def get_driver(self, browser: str = "chrome", headless: bool = True) -> webdriver.Remote:
        """獲取WebDriver實例"""
        driver_key = f"{browser}_{headless}"
        
        if driver_key in self.drivers:
            return self.drivers[driver_key]
        
        if browser.lower() == "chrome":
            options = webdriver.ChromeOptions()
            if headless:
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            
            driver = webdriver.Chrome(options=options)
            
        elif browser.lower() == "firefox":
            options = webdriver.FirefoxOptions()
            if headless:
                options.add_argument("--headless")
            
            driver = webdriver.Firefox(options=options)
            
        else:
            raise ValueError(f"不支持的瀏覽器: {browser}")
        
        # 設置隱式等待
        driver.implicitly_wait(10)
        
        self.drivers[driver_key] = driver
        return driver
    
    def cleanup_drivers(self):
        """清理所有WebDriver"""
        for driver_key, driver in self.drivers.items():
            try:
                driver.quit()
                self.logger.info(f"清理WebDriver: {driver_key}")
            except Exception as e:
                self.logger.warning(f"清理WebDriver失敗: {e}")
        
        self.drivers.clear()


class TestDataManager:
    """測試數據管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.test_data_dir = Path(config.get('test_data_dir', 'test_data'))
        self.test_data_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def load_test_data(self, test_case_id: str) -> Dict[str, Any]:
        """加載測試數據"""
        data_file = self.test_data_dir / f"{test_case_id}.json"
        
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 生成默認測試數據
        return self._generate_default_data(test_case_id)
    
    def _generate_default_data(self, test_case_id: str) -> Dict[str, Any]:
        """生成默認測試數據"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return {
            'user': {
                'username': f'test_user_{timestamp}',
                'email': f'test_{timestamp}@example.com',
                'password': 'Test123!@#',
                'name': f'Test User {timestamp}'
            },
            'project': {
                'name': f'Test Project {timestamp}',
                'description': f'Automated test project created at {timestamp}',
                'type': 'web_application'
            },
            'file': {
                'name': f'test_file_{timestamp}.txt',
                'content': f'Test content generated at {timestamp}',
                'size': 1024
            }
        }
    
    def save_test_data(self, test_case_id: str, data: Dict[str, Any]):
        """保存測試數據"""
        data_file = self.test_data_dir / f"{test_case_id}.json"
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class E2ETestExecutor:
    """端到端測試執行器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = self._setup_logging()
        self.env_manager = EnvironmentManager(config)
        self.driver_manager = WebDriverManager(config)
        self.data_manager = TestDataManager(config)
        self.results_dir = Path(config.get('results_dir', 'test_results'))
        self.results_dir.mkdir(exist_ok=True)
        self.screenshots_dir = self.results_dir / 'screenshots'
        self.screenshots_dir.mkdir(exist_ok=True)
    
    def _setup_logging(self) -> logging.Logger:
        """設置日志系統"""
        logger = logging.getLogger('e2e_test_executor')
        logger.setLevel(logging.INFO)
        
        # 文件處理器
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(
            log_dir / f'e2e_tests_{datetime.now().strftime("%Y%m%d")}.log',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # 控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    async def execute_test_suite(self, test_suite: TestSuite) -> TestSuite:
        """執行測試套件"""
        self.logger.info(f"開始執行測試套件: {test_suite.name}")
        test_suite.start_time = datetime.now()
        test_suite.status = TestStatus.RUNNING
        
        try:
            # 設置測試環境
            env_info = await self.env_manager.setup_environment(
                test_suite.environment,
                self.config.get('environments', {}).get(test_suite.environment.value, {})
            )
            
            # 執行設置腳本
            await self._run_setup_scripts(test_suite.setup_scripts, env_info)
            
            # 執行測試用例
            if test_suite.parallel_execution:
                await self._execute_tests_parallel(test_suite, env_info)
            else:
                await self._execute_tests_sequential(test_suite, env_info)
            
            # 執行清理腳本
            await self._run_teardown_scripts(test_suite.teardown_scripts, env_info)
            
            # 更新套件狀態
            test_suite.passed_count = sum(1 for tc in test_suite.test_cases if tc.status == TestStatus.PASSED)
            test_suite.failed_count = sum(1 for tc in test_suite.test_cases if tc.status == TestStatus.FAILED)
            test_suite.skipped_count = sum(1 for tc in test_suite.test_cases if tc.status == TestStatus.SKIPPED)
            
            if test_suite.failed_count > 0:
                test_suite.status = TestStatus.FAILED
            else:
                test_suite.status = TestStatus.PASSED
            
        except Exception as e:
            self.logger.error(f"測試套件執行失敗: {e}")
            test_suite.status = TestStatus.ERROR
            
        finally:
            test_suite.end_time = datetime.now()
            
            # 清理環境
            try:
                await self.env_manager.cleanup_environment(env_info)
            except Exception as e:
                self.logger.warning(f"環境清理失敗: {e}")
        
        self.logger.info(f"測試套件執行完成: {test_suite.name}")
        return test_suite
    
    async def _execute_tests_sequential(self, test_suite: TestSuite, env_info: Dict[str, Any]):
        """順序執行測試用例"""
        for test_case in test_suite.test_cases:
            if self._should_skip_test(test_case, test_suite):
                test_case.status = TestStatus.SKIPPED
                continue
            
            await self._execute_test_case(test_case, env_info)
    
    async def _execute_tests_parallel(self, test_suite: TestSuite, env_info: Dict[str, Any]):
        """並行執行測試用例"""
        # 根據依賴關係分組測試用例
        test_groups = self._group_tests_by_dependencies(test_suite.test_cases)
        
        for group in test_groups:
            # 每組內並行執行
            semaphore = asyncio.Semaphore(test_suite.max_workers)
            tasks = []
            
            for test_case in group:
                if not self._should_skip_test(test_case, test_suite):
                    task = self._execute_test_case_with_semaphore(test_case, env_info, semaphore)
                    tasks.append(task)
                else:
                    test_case.status = TestStatus.SKIPPED
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_test_case_with_semaphore(self, test_case: TestCase, env_info: Dict[str, Any], semaphore: asyncio.Semaphore):
        """帶信號量的測試用例執行"""
        async with semaphore:
            await self._execute_test_case(test_case, env_info)
    
    async def _execute_test_case(self, test_case: TestCase, env_info: Dict[str, Any]):
        """執行單個測試用例"""
        self.logger.info(f"執行測試用例: {test_case.name}")
        test_case.start_time = datetime.now()
        test_case.status = TestStatus.RUNNING
        
        try:
            # 加載測試數據
            test_data = self.data_manager.load_test_data(test_case.id)
            test_case.test_data.update(test_data)
            
            # 檢查前置條件
            if not await self._check_preconditions(test_case, env_info):
                test_case.status = TestStatus.SKIPPED
                test_case.error_message = "前置條件不滿足"
                return
            
            # 執行測試步驟
            driver = None
            if test_case.test_type in [TestType.E2E, TestType.INTEGRATION]:
                browser = env_info.get('browser', 'chrome')
                driver = self.driver_manager.get_driver(browser, headless=True)
            
            for i, step in enumerate(test_case.steps):
                await self._execute_test_step(step, test_case, env_info, driver, i)
            
            # 驗證測試結果
            await self._verify_test_results(test_case, env_info, driver)
            
            test_case.status = TestStatus.PASSED
            
        except Exception as e:
            self.logger.error(f"測試用例執行失敗: {test_case.name}, 錯誤: {e}")
            test_case.status = TestStatus.FAILED
            test_case.error_message = str(e)
            
            # 截圖保存錯誤場景
            if driver:
                screenshot_path = await self._take_screenshot(driver, test_case.id, "error")
                if screenshot_path:
                    test_case.screenshots.append(screenshot_path)
        
        finally:
            test_case.end_time = datetime.now()
    
    async def _execute_test_step(self, step: Dict[str, Any], test_case: TestCase, env_info: Dict[str, Any], driver, step_index: int):
        """執行測試步驟"""
        action = step.get('action')
        params = step.get('params', {})
        
        self.logger.debug(f"執行步驟 {step_index + 1}: {action}")
        
        if action == 'navigate':
            url = params['url'].format(**test_case.test_data, **env_info)
            driver.get(url)
            
        elif action == 'click':
            locator = params['locator']
            element = self._find_element(driver, locator)
            element.click()
            
        elif action == 'input':
            locator = params['locator']
            value = params['value'].format(**test_case.test_data)
            element = self._find_element(driver, locator)
            element.clear()
            element.send_keys(value)
            
        elif action == 'wait':
            wait_time = params.get('time', 1)
            await asyncio.sleep(wait_time)
            
        elif action == 'wait_for_element':
            locator = params['locator']
            timeout = params.get('timeout', 10)
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located(self._parse_locator(locator))
            )
            
        elif action == 'screenshot':
            screenshot_path = await self._take_screenshot(driver, test_case.id, f"step_{step_index + 1}")
            if screenshot_path:
                test_case.screenshots.append(screenshot_path)
        
        elif action == 'api_call':
            await self._make_api_call(params, test_case, env_info)
            
        elif action == 'validate':
            await self._validate_condition(params, test_case, driver, env_info)
        
        else:
            raise ValueError(f"不支持的操作: {action}")
    
    def _find_element(self, driver, locator: str):
        """查找頁面元素"""
        by, value = self._parse_locator(locator)
        return driver.find_element(by, value)
    
    def _parse_locator(self, locator: str) -> Tuple[str, str]:
        """解析定位器"""
        if locator.startswith('id='):
            return By.ID, locator[3:]
        elif locator.startswith('class='):
            return By.CLASS_NAME, locator[6:]
        elif locator.startswith('css='):
            return By.CSS_SELECTOR, locator[4:]
        elif locator.startswith('xpath='):
            return By.XPATH, locator[6:]
        elif locator.startswith('name='):
            return By.NAME, locator[5:]
        else:
            # 默認使用CSS選擇器
            return By.CSS_SELECTOR, locator
    
    async def _take_screenshot(self, driver, test_case_id: str, suffix: str = "") -> Optional[str]:
        """截圖"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{test_case_id}_{suffix}_{timestamp}.png"
            filepath = self.screenshots_dir / filename
            
            driver.save_screenshot(str(filepath))
            return str(filepath)
            
        except Exception as e:
            self.logger.warning(f"截圖失敗: {e}")
            return None
    
    async def _make_api_call(self, params: Dict[str, Any], test_case: TestCase, env_info: Dict[str, Any]):
        """進行API調用"""
        method = params['method'].upper()
        url = params['url'].format(**test_case.test_data, **env_info)
        headers = params.get('headers', {})
        data = params.get('data', {})
        
        # 格式化請求數據
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    data[key] = value.format(**test_case.test_data)
        
        response = requests.request(method, url, headers=headers, json=data, timeout=30)
        
        # 保存響應到測試數據
        test_case.test_data['last_api_response'] = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'json': response.json() if response.headers.get('content-type', '').startswith('application/json') else None,
            'text': response.text
        }
        
        # 檢查響應狀態
        expected_status = params.get('expected_status', 200)
        if response.status_code != expected_status:
            raise AssertionError(f"API調用失敗: 期望狀態碼 {expected_status}, 實際 {response.status_code}")
    
    async def _validate_condition(self, params: Dict[str, Any], test_case: TestCase, driver, env_info: Dict[str, Any]):
        """驗證條件"""
        condition_type = params['type']
        
        if condition_type == 'element_text':
            locator = params['locator']
            expected_text = params['expected'].format(**test_case.test_data)
            element = self._find_element(driver, locator)
            actual_text = element.text
            
            if actual_text != expected_text:
                raise AssertionError(f"文本驗證失敗: 期望 '{expected_text}', 實際 '{actual_text}'")
        
        elif condition_type == 'element_exists':
            locator = params['locator']
            try:
                self._find_element(driver, locator)
            except:
                raise AssertionError(f"元素不存在: {locator}")
        
        elif condition_type == 'api_response':
            field_path = params['field']
            expected_value = params['expected']
            
            response_data = test_case.test_data.get('last_api_response', {})
            actual_value = self._get_nested_value(response_data, field_path)
            
            if actual_value != expected_value:
                raise AssertionError(f"API響應驗證失敗: 期望 {expected_value}, 實際 {actual_value}")
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """獲取嵌套字典值"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _should_skip_test(self, test_case: TestCase, test_suite: TestSuite) -> bool:
        """判斷是否應該跳過測試"""
        # 檢查依賴的測試是否已完成
        for dep_id in test_case.dependencies:
            dep_test = next((tc for tc in test_suite.test_cases if tc.id == dep_id), None)
            if dep_test and dep_test.status != TestStatus.PASSED:
                return True
        
        return False
    
    def _group_tests_by_dependencies(self, test_cases: List[TestCase]) -> List[List[TestCase]]:
        """根據依賴關係對測試用例分組"""
        groups = []
        remaining = test_cases.copy()
        processed = set()
        
        while remaining:
            current_group = []
            
            # 找到沒有未處理依賴的測試用例
            for test_case in remaining.copy():
                deps_satisfied = all(dep_id in processed for dep_id in test_case.dependencies)
                if deps_satisfied:
                    current_group.append(test_case)
                    remaining.remove(test_case)
                    processed.add(test_case.id)
            
            if not current_group:
                # 如果沒有找到可執行的測試用例，可能存在循環依賴
                # 將剩餘的測試用例強制加入當前組
                current_group = remaining.copy()
                remaining.clear()
                for tc in current_group:
                    processed.add(tc.id)
            
            groups.append(current_group)
        
        return groups
    
    async def _check_preconditions(self, test_case: TestCase, env_info: Dict[str, Any]) -> bool:
        """檢查前置條件"""
        for condition in test_case.preconditions:
            if condition.startswith('service_available:'):
                service_url = condition.split(':', 1)[1].format(**env_info)
                try:
                    response = requests.get(service_url, timeout=5)
                    if response.status_code != 200:
                        return False
                except:
                    return False
            
            elif condition.startswith('file_exists:'):
                file_path = condition.split(':', 1)[1]
                if not Path(file_path).exists():
                    return False
        
        return True
    
    async def _verify_test_results(self, test_case: TestCase, env_info: Dict[str, Any], driver):
        """驗證測試結果"""
        for expected_result in test_case.expected_results:
            # 根據期望結果類型進行驗證
            if expected_result.startswith('page_title:'):
                expected_title = expected_result.split(':', 1)[1]
                actual_title = driver.title
                if actual_title != expected_title:
                    raise AssertionError(f"頁面標題驗證失敗: 期望 '{expected_title}', 實際 '{actual_title}'")
            
            elif expected_result.startswith('url_contains:'):
                expected_url_part = expected_result.split(':', 1)[1]
                current_url = driver.current_url
                if expected_url_part not in current_url:
                    raise AssertionError(f"URL驗證失敗: '{expected_url_part}' 不在 '{current_url}' 中")
    
    async def _run_setup_scripts(self, scripts: List[str], env_info: Dict[str, Any]):
        """運行設置腳本"""
        for script in scripts:
            self.logger.info(f"運行設置腳本: {script}")
            try:
                result = subprocess.run(script, shell=True, capture_output=True, text=True, timeout=300)
                if result.returncode != 0:
                    raise RuntimeError(f"設置腳本失敗: {result.stderr}")
            except subprocess.TimeoutExpired:
                raise RuntimeError(f"設置腳本超時: {script}")
    
    async def _run_teardown_scripts(self, scripts: List[str], env_info: Dict[str, Any]):
        """運行清理腳本"""
        for script in scripts:
            self.logger.info(f"運行清理腳本: {script}")
            try:
                result = subprocess.run(script, shell=True, capture_output=True, text=True, timeout=300)
                if result.returncode != 0:
                    self.logger.warning(f"清理腳本失敗: {result.stderr}")
            except subprocess.TimeoutExpired:
                self.logger.warning(f"清理腳本超時: {script}")


class E2ETestWorkflow:
    """端到端測試工作流主類"""
    
    def __init__(self, config_path: str = "e2e_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.executor = E2ETestExecutor(self.config)
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self) -> Dict[str, Any]:
        """加載配置文件"""
        if not self.config_path.exists():
            # 創建默認配置
            default_config = {
                'environments': {
                    'local': {
                        'base_url': 'http://localhost:3000',
                        'api_url': 'http://localhost:8000',
                        'browser': 'chrome',
                        'services': []
                    },
                    'docker': {
                        'compose_file': 'docker-compose.test.yml',
                        'services': [
                            {
                                'name': 'web',
                                'image': 'powerautomation:latest',
                                'ports': {'3000/tcp': 3000},
                                'environment': {'NODE_ENV': 'test'}
                            }
                        ]
                    }
                },
                'test_data_dir': 'test_data',
                'results_dir': 'test_results',
                'parallel_execution': True,
                'max_workers': 4,
                'default_timeout': 300
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
            
            return default_config
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def create_default_test_suite(self) -> TestSuite:
        """創建默認測試套件"""
        
        # PowerAutomation 核心功能測試用例
        test_cases = [
            TestCase(
                id="pa_login_test",
                name="用戶登錄測試",
                description="測試PowerAutomation用戶登錄功能",
                test_type=TestType.E2E,
                environment=TestEnvironment.LOCAL,
                tags=["auth", "critical"],
                priority=5,
                estimated_duration=30,
                dependencies=[],
                preconditions=["service_available:{base_url}/health"],
                steps=[
                    {
                        "action": "navigate",
                        "params": {"url": "{base_url}/login"}
                    },
                    {
                        "action": "input",
                        "params": {
                            "locator": "id=username",
                            "value": "{user[username]}"
                        }
                    },
                    {
                        "action": "input",
                        "params": {
                            "locator": "id=password",
                            "value": "{user[password]}"
                        }
                    },
                    {
                        "action": "click",
                        "params": {"locator": "id=login-button"}
                    },
                    {
                        "action": "wait_for_element",
                        "params": {
                            "locator": "class=dashboard",
                            "timeout": 10
                        }
                    },
                    {
                        "action": "screenshot",
                        "params": {}
                    }
                ],
                expected_results=[
                    "url_contains:/dashboard",
                    "page_title:PowerAutomation Dashboard"
                ],
                test_data={},
                status=TestStatus.PENDING,
                start_time=None,
                end_time=None,
                error_message=None,
                screenshots=[],
                logs=[]
            ),
            
            TestCase(
                id="pa_project_creation_test",
                name="項目創建測試",
                description="測試PowerAutomation項目創建功能",
                test_type=TestType.E2E,
                environment=TestEnvironment.LOCAL,
                tags=["project", "core"],
                priority=4,
                estimated_duration=60,
                dependencies=["pa_login_test"],
                preconditions=[],
                steps=[
                    {
                        "action": "click",
                        "params": {"locator": "id=new-project-btn"}
                    },
                    {
                        "action": "input",
                        "params": {
                            "locator": "id=project-name",
                            "value": "{project[name]}"
                        }
                    },
                    {
                        "action": "input",
                        "params": {
                            "locator": "id=project-description",
                            "value": "{project[description]}"
                        }
                    },
                    {
                        "action": "click",
                        "params": {"locator": "id=create-project-btn"}
                    },
                    {
                        "action": "wait_for_element",
                        "params": {
                            "locator": "class=project-created-message",
                            "timeout": 15
                        }
                    },
                    {
                        "action": "validate",
                        "params": {
                            "type": "element_text",
                            "locator": "id=project-title",
                            "expected": "{project[name]}"
                        }
                    }
                ],
                expected_results=[
                    "url_contains:/project/",
                    "page_title:PowerAutomation - {project[name]}"
                ],
                test_data={},
                status=TestStatus.PENDING,
                start_time=None,
                end_time=None,
                error_message=None,
                screenshots=[],
                logs=[]
            ),
            
            TestCase(
                id="pa_ai_assistant_test",
                name="AI助手功能測試",
                description="測試PowerAutomation AI助手的對話和代碼生成功能",
                test_type=TestType.E2E,
                environment=TestEnvironment.LOCAL,
                tags=["ai", "assistant", "core"],
                priority=4,
                estimated_duration=90,
                dependencies=["pa_project_creation_test"],
                preconditions=[],
                steps=[
                    {
                        "action": "click",
                        "params": {"locator": "id=ai-assistant-tab"}
                    },
                    {
                        "action": "input",
                        "params": {
                            "locator": "id=ai-chat-input",
                            "value": "請幫我生成一個React組件"
                        }
                    },
                    {
                        "action": "click",
                        "params": {"locator": "id=send-message-btn"}
                    },
                    {
                        "action": "wait_for_element",
                        "params": {
                            "locator": "class=ai-response",
                            "timeout": 30
                        }
                    },
                    {
                        "action": "validate",
                        "params": {
                            "type": "element_exists",
                            "locator": "class=code-block"
                        }
                    },
                    {
                        "action": "screenshot",
                        "params": {}
                    }
                ],
                expected_results=[],
                test_data={},
                status=TestStatus.PENDING,
                start_time=None,
                end_time=None,
                error_message=None,
                screenshots=[],
                logs=[]
            ),
            
            TestCase(
                id="pa_api_integration_test",
                name="API集成測試",
                description="測試PowerAutomation API端點的正常功能",
                test_type=TestType.INTEGRATION,
                environment=TestEnvironment.LOCAL,
                tags=["api", "integration"],
                priority=3,
                estimated_duration=45,
                dependencies=[],
                preconditions=["service_available:{api_url}/health"],
                steps=[
                    {
                        "action": "api_call",
                        "params": {
                            "method": "POST",
                            "url": "{api_url}/auth/login",
                            "data": {
                                "username": "{user[username]}",
                                "password": "{user[password]}"
                            },
                            "expected_status": 200
                        }
                    },
                    {
                        "action": "validate",
                        "params": {
                            "type": "api_response",
                            "field": "json.token",
                            "expected": "not_null"
                        }
                    },
                    {
                        "action": "api_call",
                        "params": {
                            "method": "GET",
                            "url": "{api_url}/projects",
                            "headers": {
                                "Authorization": "Bearer {last_api_response[json][token]}"
                            },
                            "expected_status": 200
                        }
                    }
                ],
                expected_results=[],
                test_data={},
                status=TestStatus.PENDING,
                start_time=None,
                end_time=None,
                error_message=None,
                screenshots=[],
                logs=[]
            )
        ]
        
        return TestSuite(
            id="powerautomation_e2e_suite",
            name="PowerAutomation 端到端測試套件",
            description="完整的PowerAutomation平台功能測試",
            test_cases=test_cases,
            environment=TestEnvironment.LOCAL,
            parallel_execution=self.config.get('parallel_execution', True),
            max_workers=self.config.get('max_workers', 4),
            timeout=self.config.get('default_timeout', 300),
            setup_scripts=[],
            teardown_scripts=[],
            status=TestStatus.PENDING,
            start_time=None,
            end_time=None,
            passed_count=0,
            failed_count=0,
            skipped_count=0
        )
    
    async def run_test_workflow(self, test_suite: TestSuite = None) -> TestSuite:
        """運行測試工作流"""
        if test_suite is None:
            test_suite = self.create_default_test_suite()
        
        self.logger.info("開始執行端到端測試工作流")
        
        try:
            # 執行測試套件
            result_suite = await self.executor.execute_test_suite(test_suite)
            
            # 生成測試報告
            await self._generate_test_report(result_suite)
            
            # 保存測試結果
            await self._save_test_results(result_suite)
            
            return result_suite
            
        except Exception as e:
            self.logger.error(f"測試工作流執行失敗: {e}")
            raise
        
        finally:
            # 清理資源
            self.executor.driver_manager.cleanup_drivers()
    
    async def _generate_test_report(self, test_suite: TestSuite):
        """生成測試報告"""
        report_lines = [
            "# PowerAutomation 端到端測試報告",
            f"**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 📊 測試總覽",
            f"**測試套件**: {test_suite.name}",
            f"**測試環境**: {test_suite.environment.value}",
            f"**執行狀態**: {test_suite.status.value}",
            f"**開始時間**: {test_suite.start_time.strftime('%Y-%m-%d %H:%M:%S') if test_suite.start_time else 'N/A'}",
            f"**結束時間**: {test_suite.end_time.strftime('%Y-%m-%d %H:%M:%S') if test_suite.end_time else 'N/A'}",
            "",
            "## 📈 測試統計",
            f"- **總測試數**: {len(test_suite.test_cases)}",
            f"- **通過**: {test_suite.passed_count} ✅",
            f"- **失敗**: {test_suite.failed_count} ❌",
            f"- **跳過**: {test_suite.skipped_count} ⏭️",
            f"- **成功率**: {(test_suite.passed_count / len(test_suite.test_cases) * 100):.1f}%" if test_suite.test_cases else "0%",
            "",
            "## 📋 測試用例詳情",
            ""
        ]
        
        for test_case in test_suite.test_cases:
            status_emoji = {
                TestStatus.PASSED: "✅",
                TestStatus.FAILED: "❌",
                TestStatus.SKIPPED: "⏭️",
                TestStatus.ERROR: "💥"
            }.get(test_case.status, "❓")
            
            duration = ""
            if test_case.start_time and test_case.end_time:
                duration = f" ({(test_case.end_time - test_case.start_time).total_seconds():.1f}s)"
            
            report_lines.extend([
                f"### {status_emoji} {test_case.name}{duration}",
                f"**ID**: {test_case.id}",
                f"**描述**: {test_case.description}",
                f"**類型**: {test_case.test_type.value}",
                f"**標籤**: {', '.join(test_case.tags)}",
                f"**狀態**: {test_case.status.value}",
            ])
            
            if test_case.error_message:
                report_lines.append(f"**錯誤信息**: {test_case.error_message}")
            
            if test_case.screenshots:
                report_lines.append("**截圖**:")
                for screenshot in test_case.screenshots:
                    report_lines.append(f"  - ![Screenshot]({screenshot})")
            
            report_lines.append("")
        
        # 保存報告
        report_path = self.executor.results_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))
        
        self.logger.info(f"測試報告已生成: {report_path}")
    
    async def _save_test_results(self, test_suite: TestSuite):
        """保存測試結果"""
        results_path = self.executor.results_dir / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(test_suite.to_dict(), f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"測試結果已保存: {results_path}")


async def main():
    """主函數"""
    workflow = E2ETestWorkflow()
    
    # 創建並運行默認測試套件
    test_suite = workflow.create_default_test_suite()
    result = await workflow.run_test_workflow(test_suite)
    
    print(f"\n🎯 測試執行完成!")
    print(f"總測試數: {len(result.test_cases)}")
    print(f"通過: {result.passed_count}")
    print(f"失敗: {result.failed_count}")
    print(f"跳過: {result.skipped_count}")
    print(f"成功率: {(result.passed_count / len(result.test_cases) * 100):.1f}%")


if __name__ == "__main__":
    asyncio.run(main())