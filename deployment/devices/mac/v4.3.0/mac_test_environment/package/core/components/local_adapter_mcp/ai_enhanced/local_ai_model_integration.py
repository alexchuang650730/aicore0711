"""
Local AI Model Integration - 本地AI模型集成
集成OCRFlux多模态OCR工具，提供强大的PDF到Markdown转换能力

功能：
- PDF到Markdown转换
- 复杂布局处理和表格解析
- 跨页内容合并
- 图像OCR识别
- 多语言支持（中英文）
- 批量文档处理
"""

import asyncio
import json
import logging
import os
import tempfile
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import subprocess
import shutil

@dataclass
class OCRResult:
    """OCR识别结果"""
    file_path: str
    markdown_content: str
    processing_time: float
    page_count: int
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class OCRConfig:
    """OCR配置"""
    model_path: str = "OCRFlux-3B"
    device: str = "cuda"
    batch_size: int = 1
    max_pages: int = 100
    output_format: str = "markdown"
    language: str = "auto"  # auto, en, zh
    enable_cross_page_merge: bool = True
    enable_table_parsing: bool = True
    quality_threshold: float = 0.8

class LocalAIModelIntegration:
    """本地AI模型集成 - OCRFlux"""
    
    def __init__(self, config: OCRConfig = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or OCRConfig()
        
        # 模型状态
        self.model_loaded = False
        self.model_path = None
        self.conda_env = "ocrflux"
        
        # 处理统计
        self.total_processed = 0
        self.total_pages = 0
        self.total_processing_time = 0.0
        self.success_count = 0
        self.error_count = 0
        
        # 缓存
        self.result_cache: Dict[str, OCRResult] = {}
        self.cache_max_size = 100
        
        self.logger.info("OCRFlux本地AI模型集成初始化完成")
    
    async def initialize_model(self) -> bool:
        """
        初始化OCRFlux模型
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.logger.info("开始初始化OCRFlux模型...")
            
            # 检查conda环境
            if not await self._check_conda_environment():
                self.logger.error("OCRFlux conda环境未找到")
                return False
            
            # 检查模型文件
            if not await self._check_model_files():
                self.logger.error("OCRFlux模型文件未找到")
                return False
            
            # 测试模型加载
            if not await self._test_model_loading():
                self.logger.error("OCRFlux模型加载测试失败")
                return False
            
            self.model_loaded = True
            self.logger.info("OCRFlux模型初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"初始化OCRFlux模型失败: {e}")
            return False
    
    async def _check_conda_environment(self) -> bool:
        """检查conda环境"""
        try:
            # 检查conda是否安装
            result = await self._run_command("conda --version")
            if result.returncode != 0:
                self.logger.error("Conda未安装")
                return False
            
            # 检查ocrflux环境是否存在
            result = await self._run_command("conda env list")
            if self.conda_env not in result.stdout:
                self.logger.warning(f"Conda环境 {self.conda_env} 不存在，尝试创建...")
                return await self._create_conda_environment()
            
            return True
            
        except Exception as e:
            self.logger.error(f"检查conda环境失败: {e}")
            return False
    
    async def _create_conda_environment(self) -> bool:
        """创建conda环境"""
        try:
            self.logger.info("创建OCRFlux conda环境...")
            
            # 创建环境
            create_cmd = f"conda create -n {self.conda_env} python=3.11 -y"
            result = await self._run_command(create_cmd)
            if result.returncode != 0:
                self.logger.error(f"创建conda环境失败: {result.stderr}")
                return False
            
            # 安装依赖
            install_cmd = f"conda run -n {self.conda_env} pip install torch torchvision transformers accelerate"
            result = await self._run_command(install_cmd)
            if result.returncode != 0:
                self.logger.error(f"安装基础依赖失败: {result.stderr}")
                return False
            
            self.logger.info("OCRFlux conda环境创建成功")
            return True
            
        except Exception as e:
            self.logger.error(f"创建conda环境失败: {e}")
            return False
    
    async def _check_model_files(self) -> bool:
        """检查模型文件"""
        try:
            # 检查OCRFlux是否已安装
            check_cmd = f"conda run -n {self.conda_env} python -c 'import ocrflux; print(ocrflux.__version__)'"
            result = await self._run_command(check_cmd)
            
            if result.returncode != 0:
                self.logger.warning("OCRFlux未安装，尝试安装...")
                return await self._install_ocrflux()
            
            self.logger.info("OCRFlux已安装")
            return True
            
        except Exception as e:
            self.logger.error(f"检查模型文件失败: {e}")
            return False
    
    async def _install_ocrflux(self) -> bool:
        """安装OCRFlux"""
        try:
            self.logger.info("开始安装OCRFlux...")
            
            # 克隆仓库
            clone_cmd = "git clone https://github.com/chatdoc-com/OCRFlux.git /tmp/OCRFlux"
            result = await self._run_command(clone_cmd)
            if result.returncode != 0:
                self.logger.error(f"克隆OCRFlux仓库失败: {result.stderr}")
                return False
            
            # 安装OCRFlux
            install_cmd = f"cd /tmp/OCRFlux && conda run -n {self.conda_env} pip install -e . --find-links https://flashinfer.ai/whl/cu124/torch2.5/flashinfer/"
            result = await self._run_command(install_cmd)
            if result.returncode != 0:
                self.logger.error(f"安装OCRFlux失败: {result.stderr}")
                return False
            
            # 清理临时文件
            shutil.rmtree("/tmp/OCRFlux", ignore_errors=True)
            
            self.logger.info("OCRFlux安装成功")
            return True
            
        except Exception as e:
            self.logger.error(f"安装OCRFlux失败: {e}")
            return False
    
    async def _test_model_loading(self) -> bool:
        """测试模型加载"""
        try:
            test_script = '''
import sys
try:
    from ocrflux import OCRFlux
    model = OCRFlux()
    print("Model loaded successfully")
    sys.exit(0)
except Exception as e:
    print(f"Model loading failed: {e}")
    sys.exit(1)
'''
            
            # 创建临时测试脚本
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(test_script)
                test_file = f.name
            
            try:
                # 运行测试
                test_cmd = f"conda run -n {self.conda_env} python {test_file}"
                result = await self._run_command(test_cmd, timeout=60)
                
                if result.returncode == 0:
                    self.logger.info("模型加载测试成功")
                    return True
                else:
                    self.logger.error(f"模型加载测试失败: {result.stderr}")
                    return False
                    
            finally:
                os.unlink(test_file)
                
        except Exception as e:
            self.logger.error(f"测试模型加载失败: {e}")
            return False
    
    async def process_pdf(self, pdf_path: str, output_path: str = None) -> OCRResult:
        """
        处理PDF文件
        
        Args:
            pdf_path: PDF文件路径
            output_path: 输出文件路径（可选）
            
        Returns:
            OCRResult: 处理结果
        """
        start_time = time.time()
        
        try:
            # 检查文件是否存在
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
            
            # 检查缓存
            cache_key = f"{pdf_path}_{os.path.getmtime(pdf_path)}"
            if cache_key in self.result_cache:
                self.logger.debug(f"使用缓存结果: {pdf_path}")
                return self.result_cache[cache_key]
            
            # 确保模型已加载
            if not self.model_loaded:
                if not await self.initialize_model():
                    raise RuntimeError("模型初始化失败")
            
            # 创建处理脚本
            processing_script = self._create_processing_script(pdf_path, output_path)
            
            # 执行OCR处理
            result = await self._execute_ocr_processing(processing_script)
            
            # 读取结果
            markdown_content = ""
            if result.returncode == 0 and output_path and os.path.exists(output_path):
                with open(output_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
            
            # 计算页数
            page_count = await self._count_pdf_pages(pdf_path)
            
            # 创建结果对象
            processing_time = time.time() - start_time
            ocr_result = OCRResult(
                file_path=pdf_path,
                markdown_content=markdown_content,
                processing_time=processing_time,
                page_count=page_count,
                success=result.returncode == 0,
                error_message=result.stderr if result.returncode != 0 else None,
                metadata={
                    "model": "OCRFlux-3B",
                    "config": asdict(self.config),
                    "file_size": os.path.getsize(pdf_path)
                }
            )
            
            # 更新统计
            self._update_statistics(ocr_result)
            
            # 缓存结果
            self._cache_result(cache_key, ocr_result)
            
            return ocr_result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_result = OCRResult(
                file_path=pdf_path,
                markdown_content="",
                processing_time=processing_time,
                page_count=0,
                success=False,
                error_message=str(e)
            )
            
            self._update_statistics(error_result)
            self.logger.error(f"处理PDF失败: {e}")
            return error_result
    
    def _create_processing_script(self, pdf_path: str, output_path: str = None) -> str:
        """创建处理脚本"""
        if output_path is None:
            output_path = pdf_path.replace('.pdf', '_ocr.md')
        
        script = f'''
import sys
import os
from ocrflux import OCRFlux

try:
    # 初始化模型
    model = OCRFlux(
        device="{self.config.device}",
        batch_size={self.config.batch_size}
    )
    
    # 处理PDF
    result = model.process_pdf(
        pdf_path="{pdf_path}",
        output_path="{output_path}",
        enable_cross_page_merge={self.config.enable_cross_page_merge},
        enable_table_parsing={self.config.enable_table_parsing},
        language="{self.config.language}",
        max_pages={self.config.max_pages}
    )
    
    print(f"Processing completed: {{result}}")
    sys.exit(0)
    
except Exception as e:
    print(f"Processing failed: {{e}}")
    sys.exit(1)
'''
        
        return script
    
    async def _execute_ocr_processing(self, script: str) -> subprocess.CompletedProcess:
        """执行OCR处理"""
        # 创建临时脚本文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script)
            script_file = f.name
        
        try:
            # 执行脚本
            cmd = f"conda run -n {self.conda_env} python {script_file}"
            result = await self._run_command(cmd, timeout=300)  # 5分钟超时
            return result
            
        finally:
            os.unlink(script_file)
    
    async def _count_pdf_pages(self, pdf_path: str) -> int:
        """计算PDF页数"""
        try:
            # 使用poppler-utils的pdfinfo
            cmd = f"pdfinfo '{pdf_path}' | grep Pages | awk '{{print $2}}'"
            result = await self._run_command(cmd)
            
            if result.returncode == 0:
                return int(result.stdout.strip())
            else:
                return 0
                
        except Exception as e:
            self.logger.warning(f"计算PDF页数失败: {e}")
            return 0
    
    async def process_image(self, image_path: str, output_path: str = None) -> OCRResult:
        """
        处理图像文件
        
        Args:
            image_path: 图像文件路径
            output_path: 输出文件路径（可选）
            
        Returns:
            OCRResult: 处理结果
        """
        start_time = time.time()
        
        try:
            # 检查文件是否存在
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"图像文件不存在: {image_path}")
            
            # 确保模型已加载
            if not self.model_loaded:
                if not await self.initialize_model():
                    raise RuntimeError("模型初始化失败")
            
            # 创建处理脚本
            if output_path is None:
                output_path = image_path.replace(Path(image_path).suffix, '_ocr.md')
            
            script = f'''
import sys
from ocrflux import OCRFlux

try:
    model = OCRFlux(device="{self.config.device}")
    result = model.process_image(
        image_path="{image_path}",
        output_path="{output_path}",
        language="{self.config.language}"
    )
    print(f"Image processing completed: {{result}}")
    sys.exit(0)
except Exception as e:
    print(f"Image processing failed: {{e}}")
    sys.exit(1)
'''
            
            # 执行处理
            result = await self._execute_ocr_processing(script)
            
            # 读取结果
            markdown_content = ""
            if result.returncode == 0 and os.path.exists(output_path):
                with open(output_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
            
            # 创建结果对象
            processing_time = time.time() - start_time
            ocr_result = OCRResult(
                file_path=image_path,
                markdown_content=markdown_content,
                processing_time=processing_time,
                page_count=1,
                success=result.returncode == 0,
                error_message=result.stderr if result.returncode != 0 else None,
                metadata={
                    "model": "OCRFlux-3B",
                    "type": "image",
                    "file_size": os.path.getsize(image_path)
                }
            )
            
            self._update_statistics(ocr_result)
            return ocr_result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_result = OCRResult(
                file_path=image_path,
                markdown_content="",
                processing_time=processing_time,
                page_count=0,
                success=False,
                error_message=str(e)
            )
            
            self._update_statistics(error_result)
            self.logger.error(f"处理图像失败: {e}")
            return error_result
    
    async def batch_process(self, file_paths: List[str], 
                          output_dir: str = None) -> List[OCRResult]:
        """
        批量处理文件
        
        Args:
            file_paths: 文件路径列表
            output_dir: 输出目录（可选）
            
        Returns:
            List[OCRResult]: 处理结果列表
        """
        try:
            results = []
            
            # 创建输出目录
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # 并发处理文件
            semaphore = asyncio.Semaphore(self.config.batch_size)
            
            async def process_single_file(file_path: str) -> OCRResult:
                async with semaphore:
                    if output_dir:
                        filename = Path(file_path).stem
                        output_path = os.path.join(output_dir, f"{filename}_ocr.md")
                    else:
                        output_path = None
                    
                    if file_path.lower().endswith('.pdf'):
                        return await self.process_pdf(file_path, output_path)
                    else:
                        return await self.process_image(file_path, output_path)
            
            # 创建任务
            tasks = [process_single_file(file_path) for file_path in file_paths]
            
            # 执行任务
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理异常
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    error_result = OCRResult(
                        file_path=file_paths[i],
                        markdown_content="",
                        processing_time=0.0,
                        page_count=0,
                        success=False,
                        error_message=str(result)
                    )
                    processed_results.append(error_result)
                else:
                    processed_results.append(result)
            
            self.logger.info(f"批量处理完成: {len(processed_results)} 个文件")
            return processed_results
            
        except Exception as e:
            self.logger.error(f"批量处理失败: {e}")
            return []
    
    async def _run_command(self, command: str, timeout: int = 30) -> subprocess.CompletedProcess:
        """运行命令"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            return subprocess.CompletedProcess(
                args=command,
                returncode=process.returncode,
                stdout=stdout.decode('utf-8'),
                stderr=stderr.decode('utf-8')
            )
            
        except asyncio.TimeoutError:
            self.logger.error(f"命令执行超时: {command}")
            return subprocess.CompletedProcess(
                args=command,
                returncode=1,
                stdout="",
                stderr="Command timeout"
            )
        except Exception as e:
            self.logger.error(f"命令执行失败: {e}")
            return subprocess.CompletedProcess(
                args=command,
                returncode=1,
                stdout="",
                stderr=str(e)
            )
    
    def _update_statistics(self, result: OCRResult) -> None:
        """更新统计信息"""
        self.total_processed += 1
        self.total_pages += result.page_count
        self.total_processing_time += result.processing_time
        
        if result.success:
            self.success_count += 1
        else:
            self.error_count += 1
    
    def _cache_result(self, cache_key: str, result: OCRResult) -> None:
        """缓存结果"""
        if len(self.result_cache) >= self.cache_max_size:
            # 移除最旧的缓存项
            oldest_key = next(iter(self.result_cache))
            del self.result_cache[oldest_key]
        
        self.result_cache[cache_key] = result
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        avg_processing_time = (
            self.total_processing_time / self.total_processed 
            if self.total_processed > 0 else 0
        )
        
        avg_pages_per_file = (
            self.total_pages / self.total_processed 
            if self.total_processed > 0 else 0
        )
        
        success_rate = (
            self.success_count / self.total_processed 
            if self.total_processed > 0 else 0
        )
        
        return {
            "model_loaded": self.model_loaded,
            "total_processed": self.total_processed,
            "total_pages": self.total_pages,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": success_rate,
            "average_processing_time": avg_processing_time,
            "average_pages_per_file": avg_pages_per_file,
            "cache_size": len(self.result_cache),
            "config": asdict(self.config)
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态信息"""
        return {
            "status": "ready" if self.model_loaded else "not_initialized",
            "model": "OCRFlux-3B",
            "conda_env": self.conda_env,
            "device": self.config.device,
            "capabilities": [
                "pdf_to_markdown",
                "image_ocr",
                "cross_page_merge",
                "table_parsing",
                "multi_language",
                "batch_processing"
            ],
            "supported_formats": [
                "pdf", "png", "jpg", "jpeg", "tiff", "bmp"
            ],
            "languages": ["auto", "en", "zh"],
            "statistics": self.get_statistics()
        }
    
    async def cleanup(self) -> None:
        """清理资源"""
        try:
            # 清理缓存
            self.result_cache.clear()
            
            # 重置统计
            self.total_processed = 0
            self.total_pages = 0
            self.total_processing_time = 0.0
            self.success_count = 0
            self.error_count = 0
            
            self.logger.info("OCRFlux资源清理完成")
            
        except Exception as e:
            self.logger.error(f"清理资源失败: {e}")

