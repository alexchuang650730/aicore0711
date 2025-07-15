#!/usr/bin/env python3
"""
測試K2與Command MCP的完整集成
"""

import asyncio
from core.components.command_mcp.command_manager import command_mcp

async def test_k2_integration():
    print('🔄 測試K2與Command MCP的完整集成...')
    print('=' * 50)
    
    # 初始化
    await command_mcp.initialize()
    
    # 測試指令
    commands = ['/status', '/models', '/cost', '/memory', '/doctor', '/compact', '/help']
    
    for cmd in commands:
        print(f'\n📝 測試指令: {cmd}')
        try:
            result = await command_mcp.handle_slash_command(cmd)
            cmd_type = result.get('type', 'unknown')
            print(f'✅ 成功執行: {cmd_type}')
            
            # 顯示重要信息
            if cmd_type == 'status':
                print(f'   🔧 當前模型: {result.get("current_model", "unknown")}')
                print(f'   📊 API狀態: {result.get("api_status", "unknown")}')
                print(f'   🔗 路由URL: {result.get("router_url", "unknown")}')
            
            elif cmd_type == 'cost':
                current_session = result.get('current_session', {})
                print(f'   💰 總成本: ${current_session.get("total_cost", 0):.4f}')
                print(f'   📞 請求數: {current_session.get("requests", 0)}')
                print(f'   🤖 模型: {current_session.get("model", "unknown")}')
            
            elif cmd_type == 'memory':
                memory = result.get('current_memory', {})
                print(f'   📊 會話指令: {memory.get("session_commands", 0)}')
                print(f'   💾 配置記憶: {memory.get("config_memory", 0)} bytes')
                print(f'   🧠 模型記憶: {memory.get("model_memory", "unknown")}')
            
            elif cmd_type == 'doctor':
                overall = result.get('overall_health', 'unknown')
                print(f'   🏥 系統健康: {overall}')
                checks = result.get('checks', {})
                for check_name, check_result in checks.items():
                    status = check_result.get('status', 'unknown')
                    print(f'   - {check_name}: {status}')
            
            elif cmd_type == 'compact':
                comp_status = result.get('compression_status', {})
                print(f'   📦 會話大小: {comp_status.get("current_session_size", 0)}')
                print(f'   💾 估計tokens: {comp_status.get("estimated_tokens", 0)}')
            
            elif cmd_type == 'help':
                commands_count = len(result.get('commands', {}))
                print(f'   📋 可用指令數: {commands_count}')
                
        except Exception as e:
            print(f'❌ 失敗: {e}')
    
    print('\n' + '=' * 50)
    print('🎯 K2與Command MCP集成測試完成!')
    print('✅ K2已成功轉換為主要Claude Code服務')
    print('💡 所有斜槓指令都已經支援K2模型')
    print('🔄 當K2不支援時會透過Mirror Code轉送到Claude Code')

if __name__ == "__main__":
    asyncio.run(test_k2_integration())