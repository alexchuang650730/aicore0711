"""
Mirror Status Indicator - Mirror狀態指示器
顯示Mirror Code系統的實時狀態信息
"""

import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  LinearProgress, 
  Chip, 
  IconButton,
  Tooltip,
  Card,
  CardContent
} from '@mui/material';
import { 
  CloudSync,
  CloudDone,
  CloudOff,
  Error,
  Refresh,
  Info
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

const StatusCard = styled(Card)(({ theme }) => ({
  minWidth: 300,
  marginBottom: theme.spacing(1),
  border: `1px solid ${theme.palette.divider}`,
}));

const StatusHeader = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  marginBottom: theme.spacing(1),
}));

const StatusIcon = styled(Box)(({ theme, status }) => ({
  display: 'flex',
  alignItems: 'center',
  color: 
    status === 'syncing' ? theme.palette.warning.main :
    status === 'synced' ? theme.palette.success.main :
    status === 'error' ? theme.palette.error.main :
    theme.palette.grey[500],
}));

const MetricsGrid = styled(Box)(({ theme }) => ({
  display: 'grid',
  gridTemplateColumns: 'repeat(3, 1fr)',
  gap: theme.spacing(1),
  marginTop: theme.spacing(1),
}));

const MetricItem = styled(Box)(({ theme }) => ({
  textAlign: 'center',
  padding: theme.spacing(0.5),
  backgroundColor: theme.palette.background.default,
  borderRadius: theme.shape.borderRadius,
}));

interface MirrorStatusIndicatorProps {
  status: 'idle' | 'syncing' | 'synced' | 'error' | 'offline';
  syncProgress: number;
  lastSyncTime: string | null;
  syncCount: number;
  errorCount: number;
  activeTasks: number;
  onRefresh: () => void;
  onShowDetails: () => void;
}

const MirrorStatusIndicator: React.FC<MirrorStatusIndicatorProps> = ({
  status,
  syncProgress,
  lastSyncTime,
  syncCount,
  errorCount,
  activeTasks,
  onRefresh,
  onShowDetails
}) => {
  const [refreshing, setRefreshing] = useState(false);

  const getStatusIcon = () => {
    switch (status) {
      case 'syncing':
        return <CloudSync />;
      case 'synced':
        return <CloudDone />;
      case 'error':
        return <Error />;
      case 'offline':
        return <CloudOff />;
      default:
        return <CloudSync />;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'syncing':
        return '同步中';
      case 'synced':
        return '已同步';
      case 'error':
        return '錯誤';
      case 'offline':
        return '離線';
      default:
        return '閒置';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'syncing':
        return 'warning';
      case 'synced':
        return 'success';
      case 'error':
        return 'error';
      case 'offline':
        return 'default';
      default:
        return 'default';
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setRefreshing(false);
    }
  };

  const formatTime = (timeString: string | null) => {
    if (!timeString) return '從未';
    
    const time = new Date(timeString);
    const now = new Date();
    const diffMs = now.getTime() - time.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return '剛才';
    if (diffMins < 60) return `${diffMins}分鐘前`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}小時前`;
    return time.toLocaleDateString();
  };

  return (
    <StatusCard>
      <CardContent>
        {/* 狀態標題 */}
        <StatusHeader>
          <Box display="flex" alignItems="center" gap={1}>
            <StatusIcon status={status}>
              {getStatusIcon()}
            </StatusIcon>
            <Typography variant="h6" component="div">
              Mirror Code
            </Typography>
            <Chip 
              label={getStatusText()} 
              color={getStatusColor()}
              size="small"
            />
          </Box>
          
          <Box>
            <Tooltip title="刷新狀態">
              <IconButton 
                size="small" 
                onClick={handleRefresh}
                disabled={refreshing}
              >
                <Refresh />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="查看詳情">
              <IconButton size="small" onClick={onShowDetails}>
                <Info />
              </IconButton>
            </Tooltip>
          </Box>
        </StatusHeader>

        {/* 同步進度 */}
        {status === 'syncing' && (
          <Box mb={2}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
              <Typography variant="body2" color="text.secondary">
                同步進度
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {Math.round(syncProgress)}%
              </Typography>
            </Box>
            <LinearProgress 
              variant="determinate" 
              value={syncProgress}
              color="warning"
            />
          </Box>
        )}

        {/* 狀態信息 */}
        <Box mb={2}>
          <Typography variant="body2" color="text.secondary">
            最後同步: {formatTime(lastSyncTime)}
          </Typography>
          
          {activeTasks > 0 && (
            <Typography variant="body2" color="text.secondary">
              活躍任務: {activeTasks}個
            </Typography>
          )}
        </Box>

        {/* 統計指標 */}
        <MetricsGrid>
          <MetricItem>
            <Typography variant="h6" color="primary">
              {syncCount}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              同步次數
            </Typography>
          </MetricItem>
          
          <MetricItem>
            <Typography variant="h6" color={errorCount > 0 ? 'error' : 'text.secondary'}>
              {errorCount}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              錯誤次數
            </Typography>
          </MetricItem>
          
          <MetricItem>
            <Typography variant="h6" color="info">
              {activeTasks}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              活躍任務
            </Typography>
          </MetricItem>
        </MetricsGrid>

        {/* 錯誤狀態提示 */}
        {status === 'error' && (
          <Box mt={2} p={1} bgcolor="error.light" borderRadius={1}>
            <Typography variant="body2" color="error.contrastText">
              Mirror同步遇到問題，請檢查網絡連接或重新啟動服務
            </Typography>
          </Box>
        )}

        {/* 離線狀態提示 */}
        {status === 'offline' && (
          <Box mt={2} p={1} bgcolor="grey.200" borderRadius={1}>
            <Typography variant="body2" color="text.secondary">
              Mirror服務離線，正在嘗試重新連接...
            </Typography>
          </Box>
        )}
      </CardContent>
    </StatusCard>
  );
};

export default MirrorStatusIndicator;

// Python兼容性導出
export const MirrorStatusIndicatorConfig = {
  name: 'MirrorStatusIndicator',
  description: 'Mirror Code狀態指示器組件',
  props: {
    status: { 
      type: 'enum', 
      values: ['idle', 'syncing', 'synced', 'error', 'offline'],
      required: true 
    },
    syncProgress: { type: 'number', min: 0, max: 100, required: true },
    lastSyncTime: { type: 'string', required: false },
    syncCount: { type: 'number', required: true },
    errorCount: { type: 'number', required: true },
    activeTasks: { type: 'number', required: true },
    onRefresh: { type: 'function', required: true },
    onShowDetails: { type: 'function', required: true }
  },
  events: ['refresh', 'showDetails'],
  styling: {
    card: 'StatusCard',
    header: 'StatusHeader',
    icon: 'StatusIcon',
    metrics: 'MetricsGrid'
  }
};

/*
Python使用示例:

from ui.mirror_code.components.mirror_status_indicator import MirrorStatusIndicatorConfig

# 組件配置
status_indicator_props = {
    "status": "syncing",
    "syncProgress": 75.5,
    "lastSyncTime": "2025-07-11T12:30:00Z",
    "syncCount": 25,
    "errorCount": 2,
    "activeTasks": 3,
    "onRefresh": lambda: handle_status_refresh(),
    "onShowDetails": lambda: show_mirror_details()
}

# 渲染組件
render_component("MirrorStatusIndicator", status_indicator_props)
*/