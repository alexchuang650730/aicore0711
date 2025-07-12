#!/usr/bin/env python3
"""
Test Intelligent Monitoring and Reporting System
"""

import asyncio
import sys
import os
sys.path.append('.')

from core.monitoring.intelligent_monitoring import (
    intelligent_monitoring_system, 
    MonitoringScope,
    AlertSeverity
)

async def test_intelligent_monitoring_system():
    print('📊 Testing Intelligent Monitoring and Reporting System...')
    
    try:
        # 初始化智能監控系統
        await intelligent_monitoring_system.initialize()
        print('✅ Intelligent Monitoring System initialization successful')
        
        # 測試狀態
        status = intelligent_monitoring_system.get_status()
        print(f'📊 Monitoring System Status:')
        print(f'  🔧 Component: {status["component"]}')
        print(f'  📦 Version: {status["version"]}')
        print(f'  📋 Supported Scopes: {len(status["supported_scopes"])}')
        print(f'  📄 Report Types: {len(status["supported_report_types"])}')
        print(f'  🎯 Dashboard Widgets: {status["dashboard_widgets"]}')
        
        # 顯示支持的監控範圍
        print(f'\n📊 Supported Monitoring Scopes:')
        for scope in status["supported_scopes"]:
            print(f'  📋 {scope}')
        
        # 顯示支持的報告類型
        print(f'\n📄 Supported Report Types:')
        for report_type in status["supported_report_types"]:
            print(f'  📄 {report_type}')
        
        # 顯示系統能力
        print(f'\n🎯 System Capabilities:')
        for capability in status["capabilities"]:
            print(f'  ✅ {capability}')
        
        # 開始監控
        print(f'\n🔄 Starting monitoring...')
        await intelligent_monitoring_system.start_monitoring()
        
        # 等待收集一些指標
        print(f'⏳ Collecting metrics for 10 seconds...')
        await asyncio.sleep(10)
        
        # 檢查指標收集狀態
        updated_status = intelligent_monitoring_system.get_status()
        print(f'📊 Metrics collected: {updated_status["total_metrics_collected"]}')
        print(f'🚨 Active alerts: {updated_status["active_alerts"]}')
        print(f'🔄 Monitoring active: {updated_status["monitoring_active"]}')
        
        # 測試系統指標摘要
        print(f'\n📈 Testing System Metrics Summary:')
        metrics_summary = intelligent_monitoring_system.get_system_metrics_summary()
        
        for metric_name, metric_data in metrics_summary.items():
            print(f'  📊 {metric_name}:')
            print(f'    Current: {metric_data["current"]:.2f}')
            print(f'    Average: {metric_data["average"]:.2f}')
            print(f'    Max: {metric_data["max"]:.2f}')
            print(f'    Min: {metric_data["min"]:.2f}')
            print(f'    Count: {metric_data["count"]}')
        
        # 測試儀表板數據
        print(f'\n📊 Testing Dashboard Data:')
        dashboard_data = intelligent_monitoring_system.get_dashboard_data()
        print(f'  🎯 Total Widgets: {len(dashboard_data["widgets"])}')
        print(f'  📅 Last Updated: {dashboard_data["last_updated"]}')
        
        for widget in dashboard_data["widgets"]:
            print(f'  📊 Widget: {widget["title"]} ({widget["type"]})')
            if "series" in widget["data"]:
                print(f'    📈 Series: {len(widget["data"]["series"])} metrics')
            elif "gauges" in widget["data"]:
                print(f'    📊 Gauges: {len(widget["data"]["gauges"])} metrics')
            elif "alerts" in widget["data"]:
                print(f'    🚨 Alerts: {len(widget["data"]["alerts"])} active')
        
        # 測試報告生成
        print(f'\n📄 Testing Report Generation:')
        
        # 生成系統健康報告
        system_report = await intelligent_monitoring_system.generate_monitoring_report(
            "system_health", 
            MonitoringScope.SYSTEM, 
            period_hours=1
        )
        
        print(f'✅ System Health Report Generated:')
        print(f'  📊 Report ID: {system_report.id[:8]}...')
        print(f'  📅 Period: {system_report.period_start} to {system_report.period_end}')
        print(f'  📋 Metrics: {len(system_report.metrics)} collected')
        print(f'  🚨 Alerts: {len(system_report.alerts)} triggered')
        print(f'  💡 Insights: {len(system_report.insights)} generated')
        print(f'  📝 Recommendations: {len(system_report.recommendations)} provided')
        
        # 顯示報告摘要
        print(f'\n📊 System Health Summary:')
        for key, value in system_report.summary.items():
            if isinstance(value, float):
                print(f'  {key}: {value:.2f}')
            else:
                print(f'  {key}: {value}')
        
        # 顯示洞察
        if system_report.insights:
            print(f'\n💡 Key Insights:')
            for insight in system_report.insights:
                print(f'  • {insight}')
        
        # 顯示建議
        if system_report.recommendations:
            print(f'\n📝 Recommendations:')
            for recommendation in system_report.recommendations:
                print(f'  • {recommendation}')
        
        # 生成性能報告
        performance_report = await intelligent_monitoring_system.generate_monitoring_report(
            "performance",
            MonitoringScope.APPLICATION,
            period_hours=1
        )
        
        print(f'\n🚀 Performance Report Generated:')
        print(f'  📊 Report ID: {performance_report.id[:8]}...')
        print(f'  📈 Performance Summary:')
        for key, value in performance_report.summary.items():
            if isinstance(value, float):
                print(f'    {key}: {value:.2f}')
            else:
                print(f'    {key}: {value}')
        
        # 生成安全報告
        security_report = await intelligent_monitoring_system.generate_monitoring_report(
            "security",
            MonitoringScope.SECURITY,
            period_hours=1
        )
        
        print(f'\n🔒 Security Report Generated:')
        print(f'  📊 Report ID: {security_report.id[:8]}...')
        print(f'  🛡️ Security Summary:')
        for key, value in security_report.summary.items():
            print(f'    {key}: {value}')
        
        # 生成業務報告
        business_report = await intelligent_monitoring_system.generate_monitoring_report(
            "business",
            MonitoringScope.BUSINESS,
            period_hours=1
        )
        
        print(f'\n💼 Business Report Generated:')
        print(f'  📊 Report ID: {business_report.id[:8]}...')
        print(f'  📈 Business Summary:')
        for key, value in business_report.summary.items():
            if isinstance(value, float):
                print(f'    {key}: {value:.2f}')
            else:
                print(f'    {key}: {value}')
        
        # 生成週總結報告
        weekly_report = await intelligent_monitoring_system.generate_monitoring_report(
            "weekly_summary",
            MonitoringScope.SYSTEM,
            period_hours=168  # 一週
        )
        
        print(f'\n📅 Weekly Summary Report Generated:')
        print(f'  📊 Report ID: {weekly_report.id[:8]}...')
        print(f'  📊 Weekly Summary:')
        for key, value in weekly_report.summary.items():
            if key == "top_issues":
                print(f'    {key}: {", ".join(value) if value else "None"}')
            elif key == "improvement_areas":
                print(f'    {key}: {", ".join(value) if value else "None"}')
            elif isinstance(value, float):
                print(f'    {key}: {value:.2f}')
            else:
                print(f'    {key}: {value}')
        
        # 測試告警功能
        print(f'\n🚨 Testing Alert System:')
        final_status = intelligent_monitoring_system.get_status()
        if final_status["active_alerts"] > 0:
            print(f'  🚨 Active Alerts: {final_status["active_alerts"]}')
        else:
            print(f'  ✅ No active alerts')
        
        # 停止監控
        print(f'\n⏹️ Stopping monitoring...')
        intelligent_monitoring_system.stop_monitoring()
        
        print(f'\n🎉 All Intelligent Monitoring System tests passed!')
        
    except Exception as e:
        print(f'❌ Test failed with error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_intelligent_monitoring_system())