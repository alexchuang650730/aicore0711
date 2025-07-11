"""
PowerAutomation v4.6.1 性能基準測試系統
企業級性能監控和基準測試框架

核心功能：
- 系統性能基準測試
- 應用程序性能監控
- 負載測試和壓力測試
- 性能回歸檢測
- 實時性能分析
- 性能報告生成
"""

import asyncio
import logging
import time
import statistics
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import psutil
import aiohttp
import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)


class BenchmarkType(Enum):
    """基準測試類型"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK_IO = "disk_io"
    NETWORK = "network"
    APPLICATION = "application"
    DATABASE = "database"
    API_RESPONSE = "api_response"
    UI_RENDERING = "ui_rendering"
    LOAD_TESTING = "load_testing"


class PerformanceMetric(Enum):
    """性能指標"""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    NETWORK_LATENCY = "network_latency"
    ERROR_RATE = "error_rate"
    AVAILABILITY = "availability"


@dataclass
class PerformanceThreshold:
    """性能閾值"""
    metric: PerformanceMetric
    warning_threshold: float
    critical_threshold: float
    unit: str
    description: str


@dataclass
class BenchmarkResult:
    """基準測試結果"""
    benchmark_id: str
    benchmark_type: BenchmarkType
    metric: PerformanceMetric
    value: float
    unit: str
    timestamp: str
    duration: float
    environment: str
    platform: str
    additional_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_data is None:
            self.additional_data = {}


@dataclass
class LoadTestConfiguration:
    """負載測試配置"""
    target_url: str
    concurrent_users: int
    duration_seconds: int
    ramp_up_time: int
    request_rate: int
    headers: Dict[str, str] = None
    payload: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
        if self.payload is None:
            self.payload = {}


class SystemPerformanceMonitor:
    """系統性能監控器"""
    
    def __init__(self, sampling_interval: float = 1.0):
        self.sampling_interval = sampling_interval
        self.monitoring = False
        self.performance_data = []
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def start_monitoring(self):
        """開始性能監控"""
        self.monitoring = True
        self.performance_data = []
        
        while self.monitoring:
            try:
                # 收集系統指標
                cpu_percent = psutil.cpu_percent(interval=None)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                network = psutil.net_io_counters()
                
                # 收集進程指標
                process = psutil.Process()
                process_memory = process.memory_info()
                process_cpu = process.cpu_percent()
                
                data_point = {
                    "timestamp": datetime.now().isoformat(),
                    "system": {
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                        "memory_used_gb": memory.used / (1024**3),
                        "memory_available_gb": memory.available / (1024**3),
                        "disk_used_percent": (disk.used / disk.total) * 100,
                        "disk_free_gb": disk.free / (1024**3)
                    },
                    "process": {
                        "cpu_percent": process_cpu,
                        "memory_rss_mb": process_memory.rss / (1024**2),
                        "memory_vms_mb": process_memory.vms / (1024**2)
                    },
                    "network": {
                        "bytes_sent": network.bytes_sent,
                        "bytes_recv": network.bytes_recv,
                        "packets_sent": network.packets_sent,
                        "packets_recv": network.packets_recv
                    }
                }
                
                self.performance_data.append(data_point)
                
                await asyncio.sleep(self.sampling_interval)
                
            except Exception as e:
                self.logger.error(f"性能監控錯誤: {e}")
                await asyncio.sleep(self.sampling_interval)
    
    def stop_monitoring(self) -> List[Dict[str, Any]]:
        """停止監控並返回數據"""
        self.monitoring = False
        return self.performance_data.copy()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """獲取性能摘要"""
        if not self.performance_data:
            return {}
        
        # 提取數值數據
        cpu_values = [d["system"]["cpu_percent"] for d in self.performance_data]
        memory_values = [d["system"]["memory_percent"] for d in self.performance_data]
        process_cpu_values = [d["process"]["cpu_percent"] for d in self.performance_data]
        process_memory_values = [d["process"]["memory_rss_mb"] for d in self.performance_data]
        
        return {
            "duration_seconds": len(self.performance_data) * self.sampling_interval,
            "sample_count": len(self.performance_data),
            "system_cpu": {
                "average": statistics.mean(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values),
                "std_dev": statistics.stdev(cpu_values) if len(cpu_values) > 1 else 0
            },
            "system_memory": {
                "average": statistics.mean(memory_values),
                "max": max(memory_values),
                "min": min(memory_values),
                "std_dev": statistics.stdev(memory_values) if len(memory_values) > 1 else 0
            },
            "process_cpu": {
                "average": statistics.mean(process_cpu_values),
                "max": max(process_cpu_values),
                "min": min(process_cpu_values)
            },
            "process_memory": {
                "average": statistics.mean(process_memory_values),
                "max": max(process_memory_values),
                "min": min(process_memory_values)
            }
        }


class LoadTestRunner:
    """負載測試執行器"""
    
    def __init__(self, config: LoadTestConfiguration):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.results = []
        self.running = False
    
    async def run_load_test(self) -> Dict[str, Any]:
        """執行負載測試"""
        self.logger.info(f"開始負載測試: {self.config.target_url}")
        self.logger.info(f"並發用戶: {self.config.concurrent_users}, 持續時間: {self.config.duration_seconds}秒")
        
        self.running = True
        self.results = []
        start_time = time.time()
        
        # 創建並發任務
        tasks = []
        for user_id in range(self.config.concurrent_users):
            task = asyncio.create_task(self._simulate_user(user_id, start_time))
            tasks.append(task)
            
            # 逐步增加用戶（ramp-up）
            if self.config.ramp_up_time > 0:
                await asyncio.sleep(self.config.ramp_up_time / self.config.concurrent_users)
        
        # 等待測試完成
        await asyncio.sleep(self.config.duration_seconds)
        self.running = False
        
        # 等待所有任務完成
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # 分析結果
        return self._analyze_results()
    
    async def _simulate_user(self, user_id: int, start_time: float):
        """模擬用戶行為"""
        async with aiohttp.ClientSession() as session:
            while self.running and (time.time() - start_time) < self.config.duration_seconds:
                try:
                    request_start = time.time()
                    
                    async with session.get(
                        self.config.target_url,
                        headers=self.config.headers
                    ) as response:
                        await response.read()
                        request_end = time.time()
                        
                        result = {
                            "user_id": user_id,
                            "timestamp": datetime.now().isoformat(),
                            "response_time": request_end - request_start,
                            "status_code": response.status,
                            "success": 200 <= response.status < 400
                        }
                        
                        self.results.append(result)
                
                except Exception as e:
                    result = {
                        "user_id": user_id,
                        "timestamp": datetime.now().isoformat(),
                        "response_time": -1,
                        "status_code": -1,
                        "success": False,
                        "error": str(e)
                    }
                    self.results.append(result)
                
                # 控制請求頻率
                if self.config.request_rate > 0:
                    await asyncio.sleep(1.0 / self.config.request_rate)
    
    def _analyze_results(self) -> Dict[str, Any]:
        """分析負載測試結果"""
        if not self.results:
            return {}
        
        successful_requests = [r for r in self.results if r["success"]]
        failed_requests = [r for r in self.results if not r["success"]]
        
        response_times = [r["response_time"] for r in successful_requests if r["response_time"] > 0]
        
        total_requests = len(self.results)
        success_rate = len(successful_requests) / total_requests * 100 if total_requests > 0 else 0
        
        analysis = {
            "summary": {
                "total_requests": total_requests,
                "successful_requests": len(successful_requests),
                "failed_requests": len(failed_requests),
                "success_rate_percent": success_rate,
                "throughput_rps": total_requests / self.config.duration_seconds
            },
            "response_times": {},
            "errors": {}
        }
        
        if response_times:
            analysis["response_times"] = {
                "average_ms": statistics.mean(response_times) * 1000,
                "median_ms": statistics.median(response_times) * 1000,
                "min_ms": min(response_times) * 1000,
                "max_ms": max(response_times) * 1000,
                "p90_ms": np.percentile(response_times, 90) * 1000,
                "p95_ms": np.percentile(response_times, 95) * 1000,
                "p99_ms": np.percentile(response_times, 99) * 1000,
                "std_dev_ms": statistics.stdev(response_times) * 1000 if len(response_times) > 1 else 0
            }
        
        # 錯誤分析
        error_types = {}
        for result in failed_requests:
            error = result.get("error", "Unknown error")
            error_types[error] = error_types.get(error, 0) + 1
        
        analysis["errors"] = error_types
        
        return analysis


class PerformanceBenchmarkSuite:
    """性能基準測試套件"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.benchmarks = {}
        self.thresholds = self._load_default_thresholds()
        self.monitor = SystemPerformanceMonitor()
    
    def _load_default_thresholds(self) -> Dict[PerformanceMetric, PerformanceThreshold]:
        """載入默認性能閾值"""
        return {
            PerformanceMetric.RESPONSE_TIME: PerformanceThreshold(
                metric=PerformanceMetric.RESPONSE_TIME,
                warning_threshold=200.0,
                critical_threshold=500.0,
                unit="ms",
                description="API響應時間"
            ),
            PerformanceMetric.CPU_USAGE: PerformanceThreshold(
                metric=PerformanceMetric.CPU_USAGE,
                warning_threshold=70.0,
                critical_threshold=90.0,
                unit="%",
                description="CPU使用率"
            ),
            PerformanceMetric.MEMORY_USAGE: PerformanceThreshold(
                metric=PerformanceMetric.MEMORY_USAGE,
                warning_threshold=80.0,
                critical_threshold=95.0,
                unit="%",
                description="內存使用率"
            ),
            PerformanceMetric.THROUGHPUT: PerformanceThreshold(
                metric=PerformanceMetric.THROUGHPUT,
                warning_threshold=100.0,
                critical_threshold=50.0,
                unit="rps",
                description="每秒請求數"
            )
        }
    
    async def run_cpu_benchmark(self) -> BenchmarkResult:
        """CPU基準測試"""
        self.logger.info("執行CPU基準測試...")
        
        start_time = time.time()
        
        # CPU密集型任務
        def cpu_intensive_task():
            # 計算質數
            def is_prime(n):
                if n < 2:
                    return False
                for i in range(2, int(n ** 0.5) + 1):
                    if n % i == 0:
                        return False
                return True
            
            count = 0
            for i in range(100000):
                if is_prime(i):
                    count += 1
            return count
        
        # 監控CPU使用率
        monitor_task = asyncio.create_task(self.monitor.start_monitoring())
        
        # 執行CPU測試
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=psutil.cpu_count()) as executor:
            tasks = [loop.run_in_executor(executor, cpu_intensive_task) for _ in range(psutil.cpu_count())]
            await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 停止監控
        performance_data = self.monitor.stop_monitoring()
        summary = self.monitor.get_performance_summary()
        
        return BenchmarkResult(
            benchmark_id=f"cpu_benchmark_{int(start_time)}",
            benchmark_type=BenchmarkType.CPU,
            metric=PerformanceMetric.CPU_USAGE,
            value=summary.get("system_cpu", {}).get("average", 0),
            unit="%",
            timestamp=datetime.now().isoformat(),
            duration=duration,
            environment="local",
            platform=f"{psutil.cpu_count()} cores",
            additional_data={
                "performance_summary": summary,
                "cpu_cores": psutil.cpu_count(),
                "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {}
            }
        )
    
    async def run_memory_benchmark(self) -> BenchmarkResult:
        """內存基準測試"""
        self.logger.info("執行內存基準測試...")
        
        start_time = time.time()
        
        # 內存密集型任務
        def memory_intensive_task():
            # 創建大型數據結構
            data = []
            for i in range(1000000):
                data.append(f"test_string_{i}" * 100)
            return len(data)
        
        monitor_task = asyncio.create_task(self.monitor.start_monitoring())
        
        # 執行內存測試
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=4) as executor:
            tasks = [loop.run_in_executor(executor, memory_intensive_task) for _ in range(4)]
            results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        performance_data = self.monitor.stop_monitoring()
        summary = self.monitor.get_performance_summary()
        
        return BenchmarkResult(
            benchmark_id=f"memory_benchmark_{int(start_time)}",
            benchmark_type=BenchmarkType.MEMORY,
            metric=PerformanceMetric.MEMORY_USAGE,
            value=summary.get("system_memory", {}).get("average", 0),
            unit="%",
            timestamp=datetime.now().isoformat(),
            duration=duration,
            environment="local",
            platform=f"{psutil.virtual_memory().total // (1024**3)}GB RAM",
            additional_data={
                "performance_summary": summary,
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "objects_created": sum(results)
            }
        )
    
    async def run_api_benchmark(self, url: str, requests_count: int = 100) -> BenchmarkResult:
        """API響應時間基準測試"""
        self.logger.info(f"執行API基準測試: {url}")
        
        start_time = time.time()
        response_times = []
        
        async with aiohttp.ClientSession() as session:
            for i in range(requests_count):
                request_start = time.time()
                try:
                    async with session.get(url) as response:
                        await response.read()
                        request_end = time.time()
                        response_times.append((request_end - request_start) * 1000)  # 轉換為毫秒
                except Exception as e:
                    self.logger.warning(f"API請求失敗: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        avg_response_time = statistics.mean(response_times) if response_times else 0
        
        return BenchmarkResult(
            benchmark_id=f"api_benchmark_{int(start_time)}",
            benchmark_type=BenchmarkType.API_RESPONSE,
            metric=PerformanceMetric.RESPONSE_TIME,
            value=avg_response_time,
            unit="ms",
            timestamp=datetime.now().isoformat(),
            duration=duration,
            environment="local",
            platform="network",
            additional_data={
                "url": url,
                "requests_count": requests_count,
                "successful_requests": len(response_times),
                "min_response_time": min(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0,
                "median_response_time": statistics.median(response_times) if response_times else 0
            }
        )
    
    async def run_load_test_benchmark(self, config: LoadTestConfiguration) -> BenchmarkResult:
        """負載測試基準測試"""
        self.logger.info("執行負載測試基準測試...")
        
        start_time = time.time()
        
        # 運行負載測試
        load_runner = LoadTestRunner(config)
        load_results = await load_runner.run_load_test()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 提取關鍵指標
        throughput = load_results.get("summary", {}).get("throughput_rps", 0)
        avg_response_time = load_results.get("response_times", {}).get("average_ms", 0)
        success_rate = load_results.get("summary", {}).get("success_rate_percent", 0)
        
        return BenchmarkResult(
            benchmark_id=f"load_test_benchmark_{int(start_time)}",
            benchmark_type=BenchmarkType.LOAD_TESTING,
            metric=PerformanceMetric.THROUGHPUT,
            value=throughput,
            unit="rps",
            timestamp=datetime.now().isoformat(),
            duration=duration,
            environment="local",
            platform=f"{config.concurrent_users} users",
            additional_data={
                "load_test_config": asdict(config),
                "load_test_results": load_results,
                "average_response_time_ms": avg_response_time,
                "success_rate_percent": success_rate
            }
        )
    
    async def run_full_benchmark_suite(self) -> List[BenchmarkResult]:
        """運行完整基準測試套件"""
        self.logger.info("開始運行完整性能基準測試套件...")
        
        results = []
        
        try:
            # CPU基準測試
            cpu_result = await self.run_cpu_benchmark()
            results.append(cpu_result)
            
            # 內存基準測試
            memory_result = await self.run_memory_benchmark()
            results.append(memory_result)
            
            # API基準測試（如果有可用的API端點）
            try:
                api_result = await self.run_api_benchmark("http://localhost:8080/api/health")
                results.append(api_result)
            except Exception as e:
                self.logger.warning(f"API基準測試跳過: {e}")
            
            # 生成基準測試報告
            await self._generate_benchmark_report(results)
            
        except Exception as e:
            self.logger.error(f"基準測試執行失敗: {e}")
        
        return results
    
    async def _generate_benchmark_report(self, results: List[BenchmarkResult]):
        """生成基準測試報告"""
        report = {
            "report_info": {
                "generated_at": datetime.now().isoformat(),
                "total_benchmarks": len(results),
                "platform": {
                    "system": platform.system(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "cpu_count": psutil.cpu_count(),
                    "memory_gb": psutil.virtual_memory().total / (1024**3)
                }
            },
            "benchmark_results": [asdict(r) for r in results],
            "performance_analysis": self._analyze_benchmark_results(results)
        }
        
        # 保存報告
        report_dir = Path("performance_reports")
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = report_dir / f"performance_benchmark_report_{timestamp}.json"
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"基準測試報告已生成: {report_path}")
        
        # 生成性能圖表
        await self._generate_performance_charts(results, report_dir / f"charts_{timestamp}")
    
    def _analyze_benchmark_results(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """分析基準測試結果"""
        analysis = {
            "performance_score": 0,
            "threshold_violations": [],
            "recommendations": []
        }
        
        total_score = 0
        max_score = 0
        
        for result in results:
            threshold = self.thresholds.get(result.metric)
            if threshold:
                max_score += 100
                
                if result.value <= threshold.warning_threshold:
                    score = 100
                elif result.value <= threshold.critical_threshold:
                    score = 50
                else:
                    score = 0
                    analysis["threshold_violations"].append({
                        "benchmark": result.benchmark_id,
                        "metric": result.metric.value,
                        "value": result.value,
                        "threshold": threshold.critical_threshold,
                        "unit": result.unit
                    })
                
                total_score += score
        
        analysis["performance_score"] = (total_score / max_score * 100) if max_score > 0 else 0
        
        # 生成建議
        if analysis["performance_score"] < 70:
            analysis["recommendations"].append("系統性能需要優化")
        if analysis["threshold_violations"]:
            analysis["recommendations"].append("有性能指標超出閾值，需要立即關注")
        
        return analysis
    
    async def _generate_performance_charts(self, results: List[BenchmarkResult], charts_dir: Path):
        """生成性能圖表"""
        charts_dir.mkdir(exist_ok=True)
        
        try:
            # 創建性能指標圖表
            metrics = [r.metric.value for r in results]
            values = [r.value for r in results]
            
            plt.figure(figsize=(12, 8))
            plt.bar(metrics, values)
            plt.title("Performance Benchmark Results")
            plt.xlabel("Metrics")
            plt.ylabel("Values")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(charts_dir / "benchmark_results.png")
            plt.close()
            
            self.logger.info(f"性能圖表已生成: {charts_dir}")
            
        except Exception as e:
            self.logger.warning(f"圖表生成失敗: {e}")


# 單例實例
performance_benchmark_suite = PerformanceBenchmarkSuite()