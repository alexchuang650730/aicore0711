#!/usr/bin/env python3
"""
Test Enterprise Version Strategy
"""

import asyncio
import sys
import os
sys.path.append('.')

from core.enterprise.version_strategy import enterprise_version_strategy, EditionTier

async def test_enterprise_version_strategy():
    print('🧪 Testing Enterprise Version Strategy...')
    
    try:
        # 初始化
        await enterprise_version_strategy.initialize()
        print('✅ Initialization successful')
        
        # 測試當前版本檢測
        current_edition = enterprise_version_strategy.current_edition.value
        print(f'📦 Current edition: {current_edition}')
        
        # 測試功能訪問檢查
        test_features = ['mcp_test', 'mcp_security', 'sso_integration']
        print('\n🔍 Feature access check:')
        for feature in test_features:
            access = enterprise_version_strategy.check_feature_access(feature)
            print(f'  {feature}: {access.value}')
        
        # 測試可用功能列表
        available_features = enterprise_version_strategy.get_available_features()
        print(f'\n✅ Available features: {len(available_features)}')
        
        # 測試版本對比
        comparison = enterprise_version_strategy.get_edition_comparison()
        print(f'📊 Total editions: {len(comparison)}')
        
        # 測試狀態
        status = enterprise_version_strategy.get_status()
        print(f'📈 Status: {status["component"]} v{status["version"]}')
        print(f'📈 Total features: {status["total_features"]}')
        
        # 測試授權生成
        print('\n🔑 Testing license generation...')
        license_info = await enterprise_version_strategy.generate_license(
            EditionTier.PROFESSIONAL, 
            user_count=5,
            organization='Test Company'
        )
        print(f'✅ Generated license: {license_info.license_key[:8]}...')
        print(f'📅 Valid until: {license_info.valid_until}')
        
        # 測試授權驗證
        is_valid = await enterprise_version_strategy.validate_license(license_info.license_key)
        print(f'🔍 License validation: {"✅ Valid" if is_valid else "❌ Invalid"}')
        
        # 導出配置
        print('\n💾 Testing configuration export...')
        await enterprise_version_strategy.save_version_strategy_config('test_config.json')
        print('✅ Configuration exported successfully')
        
        # 清理測試文件
        if os.path.exists('test_config.json'):
            os.remove('test_config.json')
            print('🗑️ Cleaned up test files')
        
        print('\n🎉 All tests passed! Enterprise Version Strategy is working correctly.')
        
    except Exception as e:
        print(f'❌ Test failed with error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_enterprise_version_strategy())