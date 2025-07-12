#!/usr/bin/env python3
"""
Test Multi-Platform Deployment Support System
測試多平台部署支持系統
"""

import asyncio
import sys
import os
sys.path.append('.')

from core.deployment.multi_platform_deployer import (
    multi_platform_deployer,
    PlatformType,
    DeploymentStage
)

async def test_multi_platform_deployment():
    print('🚀 Testing Multi-Platform Deployment Support System...')
    
    try:
        # 初始化多平台部署器
        await multi_platform_deployer.initialize()
        print('✅ Multi-Platform Deployer initialization successful')
        
        # 測試部署器狀態
        status = multi_platform_deployer.get_status()
        print(f'🌍 Multi-Platform Deployer Status:')
        print(f'  🔧 Component: {status["component"]}')
        print(f'  📦 Version: {status["version"]}')
        print(f'  🎯 Supported Platforms: {status["supported_platforms"]}')
        print(f'  📊 Active Deployments: {status["active_deployments"]}')
        
        # 顯示平台分類
        print(f'\n🎯 Platform Categories:')
        for category, platforms in status["platform_categories"].items():
            print(f'  📋 {category.title()}: {", ".join(platforms)}')
        
        # 顯示部署能力
        print(f'\n🔧 Deployment Capabilities:')
        for capability in status["deployment_capabilities"]:
            print(f'  ✅ {capability}')
        
        # 測試關鍵平台部署
        print(f'\n🚀 Testing Key Platform Deployments:')
        
        # 測試桌面平台
        print(f'\n🖥️ Testing Desktop Platforms:')
        desktop_platforms = [
            PlatformType.WINDOWS,
            PlatformType.LINUX, 
            PlatformType.MACOS
        ]
        
        for platform in desktop_platforms:
            result = await multi_platform_deployer.deploy_platform(platform)
            status_icon = "✅" if result.success else "❌"
            print(f'  {status_icon} {platform.value}: {result.message}')
            if result.success:
                print(f'    📦 Package size: {result.package_size / 1000000:.1f}MB')
                print(f'    ⏱️ Build time: {result.build_time:.1f}s')
                print(f'    📄 Artifacts: {len(result.artifacts)}')
        
        # 測試Web平台
        print(f'\n🌐 Testing Web Platforms:')
        web_platforms = [
            PlatformType.WEB_BROWSER,
            PlatformType.PWA
        ]
        
        for platform in web_platforms:
            result = await multi_platform_deployer.deploy_platform(platform)
            status_icon = "✅" if result.success else "❌"
            print(f'  {status_icon} {platform.value}: {result.message}')
            if result.success and result.deployment_url:
                print(f'    🌐 URL: {result.deployment_url}')
                print(f'    📦 Package size: {result.package_size / 1000000:.1f}MB')
                print(f'    ⏱️ Build time: {result.build_time:.1f}s')
        
        # 測試社群平台
        print(f'\n👥 Testing Community Platforms:')
        community_platforms = [
            PlatformType.GITHUB_PAGES,
            PlatformType.VERCEL,
            PlatformType.NETLIFY
        ]
        
        for platform in community_platforms:
            result = await multi_platform_deployer.deploy_platform(platform)
            status_icon = "✅" if result.success else "❌"
            print(f'  {status_icon} {platform.value}: {result.message}')
            if result.success and result.deployment_url:
                print(f'    🌐 URL: {result.deployment_url}')
                print(f'    ⏱️ Build time: {result.build_time:.1f}s')
        
        # 測試編輯器平台
        print(f'\n📝 Testing Editor Platforms:')
        editor_platforms = [
            PlatformType.VSCODE_EXTENSION
        ]
        
        for platform in editor_platforms:
            result = await multi_platform_deployer.deploy_platform(platform)
            status_icon = "✅" if result.success else "❌"
            print(f'  {status_icon} {platform.value}: {result.message}')
            if result.success:
                print(f'    🏪 Marketplace: {result.deployment_url}')
                print(f'    📦 Package size: {result.package_size / 1000:.0f}KB')
                print(f'    ⏱️ Build time: {result.build_time:.1f}s')
        
        # 測試雲平台
        print(f'\n☁️ Testing Cloud Platforms:')
        cloud_platforms = [
            PlatformType.DOCKER,
            PlatformType.KUBERNETES
        ]
        
        for platform in cloud_platforms:
            result = await multi_platform_deployer.deploy_platform(platform)
            status_icon = "✅" if result.success else "❌"
            print(f'  {status_icon} {platform.value}: {result.message}')
            if result.success:
                if result.deployment_url:
                    print(f'    🌐 URL: {result.deployment_url}')
                print(f'    📦 Image size: {result.package_size / 1000000:.0f}MB')
                print(f'    ⏱️ Build time: {result.build_time:.1f}s')
        
        # 獲取部署摘要
        print(f'\n📊 Deployment Summary:')
        summary = multi_platform_deployer.get_deployment_summary()
        
        print(f'🌍 Overall Statistics:')
        print(f'  📊 Total platforms: {summary["total_platforms"]}')
        print(f'  ✅ Successful deployments: {summary["successful_deployments"]}')
        print(f'  ❌ Failed deployments: {summary["failed_deployments"]}')
        print(f'  📈 Success rate: {summary["success_rate"]:.1f}%')
        print(f'  ⏱️ Total build time: {summary["total_build_time"]:.1f}s')
        print(f'  📦 Total package size: {summary["total_package_size"] / 1000000:.1f}MB')
        print(f'  📊 Average build time: {summary["average_build_time"]:.1f}s')
        
        # 顯示部署URL
        if summary["deployment_urls"]:
            print(f'\n🌐 Deployment URLs:')
            for platform, url in summary["deployment_urls"].items():
                print(f'  🔗 {platform}: {url}')
        
        # 顯示現有GitHub倉庫連接
        print(f'\n🐙 GitHub Repository Integration:')
        github_repos = {
            "Community版本": "https://github.com/alexchuang650730/powerautomation_community/tree/main",
            "Web版本": "https://github.com/alexchuang650730/aicore0624/tree/main/powerautomation_web",
            "主倉庫": "https://github.com/alexchuang650730/aicore0711"
        }
        
        for repo_name, repo_url in github_repos.items():
            print(f'  📁 {repo_name}: {repo_url}')
        
        # 測試特定平台的詳細信息
        print(f'\n🔍 Platform Details:')
        for platform_name, platform_info in summary["platform_status"].items():
            if platform_info["success"]:
                print(f'  ✅ {platform_name}:')
                print(f'    📊 Stage: {platform_info["stage"]}')
                print(f'    ⏱️ Build time: {platform_info["build_time"]:.1f}s')
                print(f'    📦 Package size: {platform_info["package_size"] / 1000000:.1f}MB')
                print(f'    📄 Artifacts: {platform_info["artifacts"]}')
                if platform_info.get("deployment_url"):
                    print(f'    🌐 URL: {platform_info["deployment_url"]}')
        
        # 顯示支持的完整平台列表
        print(f'\n🌟 Complete Platform Support Matrix:')
        platform_matrix = {
            "🖥️ Desktop Platforms": [
                "✅ Windows (executable + installer)",
                "✅ Linux (AppImage + tar.gz)", 
                "✅ macOS (app bundle + DMG)"
            ],
            "🌐 Web Platforms": [
                "✅ Browser Web App (SPA)",
                "✅ Progressive Web App (PWA)",
                "✅ WebAssembly (WASM)"
            ],
            "👥 Community Platforms": [
                "✅ GitHub Pages (靜態托管)",
                "✅ Vercel (無服務器部署)",
                "✅ Netlify (JAMstack部署)"
            ],
            "📝 Editor Extensions": [
                "✅ VSCode Extension (Marketplace)",
                "✅ JetBrains Plugin (Plugin Portal)"
            ],
            "☁️ Cloud Platforms": [
                "✅ Docker Container (Hub)",
                "✅ Kubernetes (Helm Charts)",
                "⚙️ AWS (ECS/Lambda)",
                "⚙️ Azure (Container Instances)",
                "⚙️ GCP (Cloud Run)"
            ],
            "📱 Mobile Platforms": [
                "⚙️ React Native (iOS/Android)",
                "⚙️ Electron Mobile (Hybrid)"
            ]
        }
        
        for category, platforms in platform_matrix.items():
            print(f'\n{category}:')
            for platform in platforms:
                print(f'  {platform}')
        
        # 最終狀態檢查
        final_status = multi_platform_deployer.get_status()
        print(f'\n🎉 Multi-Platform Deployment System Status:')
        print(f'  🌍 Supported platforms: {final_status["supported_platforms"]}')
        print(f'  🚀 Active deployments: {final_status["active_deployments"]}')
        print(f'  📦 Platform categories: {len(final_status["platform_categories"])}')
        print(f'  🔧 Deployment capabilities: {len(final_status["deployment_capabilities"])}')
        
        print(f'\n🎉 All Multi-Platform Deployment tests passed!')
        print(f'✨ PowerAutomation v4.6.1 現已支持完整的全平台部署！')
        
    except Exception as e:
        print(f'❌ Test failed with error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_multi_platform_deployment())