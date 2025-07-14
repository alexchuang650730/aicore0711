#!/usr/bin/env python3
"""
ClaudEditor UI测试执行脚本
快速启动和管理UI自动化测试

使用方法:
    python run_ui_tests.py                    # 运行所有测试
    python run_ui_tests.py --smoke            # 只运行冒烟测试
    python run_ui_tests.py --high-priority    # 只运行高优先级测试
    python run_ui_tests.py --stage setup      # 只运行特定阶段测试
    python run_ui_tests.py --record-only      # 只录制，不执行验证
    python run_ui_tests.py --replay <id>      # 回放指定录制

作者: PowerAutomation Team
版本: 4.1
日期: 2025-01-07
"""

import asyncio
import argparse
import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from core.components.test_mcp.templates.claudeditor_ui_test_template import ClaudEditorUITestTemplate

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'ui_test_{datetime.now().strftime("%Y%m%d")}.log')
    ]
)
logger = logging.getLogger(__name__)

class UITestRunner:
    """UI测试运行器"""
    
    def __init__(self):
        self.test_template = None
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """加载测试配置"""
        config_path = Path(__file__).parent / "test_config.json"
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 创建默认配置
            default_config = {
                "base_url": "http://localhost:3000",
                "api_base_url": "http://localhost:5000", 
                "output_directory": "./test_results",
                "screenshot_on_failure": True,
                "video_recording": True,
                "max_retry_attempts": 3,
                "default_timeout": 30,
                "browser_options": {
                    "headless": False,
                    "window_size": [1920, 1080],
                    "user_agent": "ClaudEditor-UITest/4.1"
                },
                "test_environments": {
                    "local": {
                        "base_url": "http://localhost:3000",
                        "api_base_url": "http://localhost:5000"
                    },
                    "staging": {
                        "base_url": "https://staging.claudeditor.com",
                        "api_base_url": "https://api-staging.claudeditor.com"
                    },
                    "production": {
                        "base_url": "https://claudeditor.com",
                        "api_base_url": "https://api.claudeditor.com"
                    }
                }
            }
            
            # 保存默认配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            return default_config
    
    async def run_tests(self, args):
        """运行测试"""
        logger.info("🚀 启动ClaudEditor UI自动化测试")
        
        # 选择测试环境
        env_config = self.config['test_environments'].get(args.environment, 
                                                         self.config['test_environments']['local'])
        
        # 更新配置
        test_config = self.config.copy()
        test_config.update(env_config)
        
        if args.headless:
            test_config['browser_options']['headless'] = True
        
        # 创建测试模板
        self.test_template = ClaudEditorUITestTemplate(test_config)
        
        # 构建测试过滤器
        test_filter = self._build_test_filter(args)
        
        logger.info(f"测试环境: {args.environment}")
        logger.info(f"测试过滤器: {test_filter}")
        
        try:
            # 运行测试套件
            report = await self.test_template.run_test_suite(test_filter)
            
            # 显示结果
            self._display_results(report)
            
            # 如果有失败的测试，返回非零退出码
            if report['summary']['failed'] > 0 or report['summary']['errors'] > 0:
                sys.exit(1)
                
        except Exception as e:
            logger.error(f"测试执行失败: {e}")
            sys.exit(1)
    
    def _build_test_filter(self, args) -> dict:
        """构建测试过滤器"""
        test_filter = {}
        
        if args.smoke:
            test_filter['tags'] = ['smoke']
        elif args.core:
            test_filter['tags'] = ['core']
        elif args.integration:
            test_filter['tags'] = ['integration', 'e2e']
        elif args.tags:
            test_filter['tags'] = args.tags.split(',')
        
        if args.high_priority:
            test_filter['priority'] = 'high'
        elif args.medium_priority:
            test_filter['priority'] = 'medium'
        elif args.low_priority:
            test_filter['priority'] = 'low'
        
        if args.stage:
            test_filter['stage'] = args.stage
        
        return test_filter
    
    def _display_results(self, report):
        """显示测试结果"""
        summary = report['summary']
        
        print("\n" + "="*60)
        print("🎯 ClaudEditor UI测试结果")
        print("="*60)
        print(f"📊 总测试数: {summary['total_tests']}")
        print(f"✅ 通过: {summary['passed']}")
        print(f"❌ 失败: {summary['failed']}")
        print(f"💥 错误: {summary['errors']}")
        print(f"📈 成功率: {summary['success_rate']:.1f}%")
        print(f"⏱️  总耗时: {summary['total_execution_time']:.2f}秒")
        print("="*60)
        
        # 显示失败的测试
        failed_tests = [r for r in report['test_results'] if r['status'] in ['failed', 'error']]
        if failed_tests:
            print("\n❌ 失败的测试:")
            for test in failed_tests:
                print(f"  - {test['test_case_id']}: {test['error_message']}")
        
        # 显示录制文件
        recordings = [r['recording_path'] for r in report['test_results'] 
                     if r.get('recording_path')]
        if recordings:
            print(f"\n🎬 录制文件 ({len(recordings)}个):")
            for recording in recordings[:5]:  # 只显示前5个
                print(f"  - {recording}")
            if len(recordings) > 5:
                print(f"  ... 还有 {len(recordings) - 5} 个录制文件")
        
        print("\n" + "="*60)
    
    async def replay_recording(self, recording_id: str):
        """回放录制"""
        logger.info(f"🔄 回放录制: {recording_id}")
        
        self.test_template = ClaudEditorUITestTemplate(self.config)
        
        try:
            result = await self.test_template.recorder_integration.replay_recording(recording_id)
            logger.info(f"回放完成: {result}")
        except Exception as e:
            logger.error(f"回放失败: {e}")
            sys.exit(1)
    
    async def list_recordings(self):
        """列出所有录制"""
        logger.info("📋 列出所有录制")
        
        recordings_dir = Path(self.config['output_directory']) / "recordings"
        if not recordings_dir.exists():
            print("没有找到录制文件")
            return
        
        recordings = list(recordings_dir.glob("*.json"))
        if not recordings:
            print("没有找到录制文件")
            return
        
        print(f"\n📁 找到 {len(recordings)} 个录制文件:")
        for recording in sorted(recordings, key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                with open(recording, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"  - {recording.stem}: {data.get('name', 'Unknown')} "
                          f"({data.get('duration', 0):.1f}s)")
            except Exception as e:
                print(f"  - {recording.stem}: (无法读取: {e})")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='ClaudEditor UI自动化测试')
    
    # 测试选择
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument('--smoke', action='store_true', help='只运行冒烟测试')
    test_group.add_argument('--core', action='store_true', help='只运行核心功能测试')
    test_group.add_argument('--integration', action='store_true', help='只运行集成测试')
    test_group.add_argument('--tags', type=str, help='按标签过滤测试 (逗号分隔)')
    
    # 优先级选择
    priority_group = parser.add_mutually_exclusive_group()
    priority_group.add_argument('--high-priority', action='store_true', help='只运行高优先级测试')
    priority_group.add_argument('--medium-priority', action='store_true', help='只运行中优先级测试')
    priority_group.add_argument('--low-priority', action='store_true', help='只运行低优先级测试')
    
    # 阶段选择
    parser.add_argument('--stage', type=str, 
                       choices=['setup', 'ui_load', 'user_interaction', 'api_testing', 
                               'integration', 'performance', 'cleanup'],
                       help='只运行特定阶段的测试')
    
    # 环境选择
    parser.add_argument('--environment', type=str, default='local',
                       choices=['local', 'staging', 'production'],
                       help='选择测试环境')
    
    # 浏览器选项
    parser.add_argument('--headless', action='store_true', help='无头模式运行')
    
    # 录制相关
    parser.add_argument('--record-only', action='store_true', help='只录制，不执行验证')
    parser.add_argument('--replay', type=str, help='回放指定录制ID')
    parser.add_argument('--list-recordings', action='store_true', help='列出所有录制')
    
    # 其他选项
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    parser.add_argument('--config', type=str, help='指定配置文件路径')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建测试运行器
    runner = UITestRunner()
    
    # 执行相应的操作
    if args.replay:
        asyncio.run(runner.replay_recording(args.replay))
    elif args.list_recordings:
        asyncio.run(runner.list_recordings())
    else:
        asyncio.run(runner.run_tests(args))

if __name__ == "__main__":
    main()

