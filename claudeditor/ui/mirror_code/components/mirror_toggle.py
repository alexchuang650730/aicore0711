"""
Mirror Toggle Component - Mirror開關組件
提供Mirror Code功能的開關控制界面
"""

import React, { useState, useEffect } from 'react';
import { Switch, Box, Typography, CircularProgress, Chip } from '@mui/material';
import { styled } from '@mui/material/styles';

const MirrorToggleContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(2),
  padding: theme.spacing(1),
  borderRadius: theme.shape.borderRadius,
  backgroundColor: theme.palette.background.paper,
  border: `1px solid ${theme.palette.divider}`,
}));

const StatusChip = styled(Chip)(({ theme, status }) => ({
  fontSize: '0.75rem',
  height: '20px',
  color: theme.palette.getContrastText(
    status === 'enabled' ? theme.palette.success.main :
    status === 'syncing' ? theme.palette.warning.main :
    status === 'error' ? theme.palette.error.main :
    theme.palette.grey[500]
  ),
  backgroundColor:
    status === 'enabled' ? theme.palette.success.main :
    status === 'syncing' ? theme.palette.warning.main :
    status === 'error' ? theme.palette.error.main :
    theme.palette.grey[500],
}));

interface MirrorToggleProps {
  enabled: boolean;
  syncing: boolean;
  status: 'disabled' | 'enabled' | 'syncing' | 'error' | 'offline';
  syncCount: number;
  lastSync: string | null;
  onToggle: (enabled: boolean) => void;
  onSync: () => void;
}

const MirrorToggle: React.FC<MirrorToggleProps> = ({
  enabled,
  syncing,
  status,
  syncCount,
  lastSync,
  onToggle,
  onSync
}) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleToggle = async (event: React.ChangeEvent<HTMLInputElement>) => {
    setIsLoading(true);
    try {
      await onToggle(event.target.checked);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSync = async () => {
    if (!enabled || syncing) return;
    
    setIsLoading(true);
    try {
      await onSync();
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'enabled':
        return '已啟用';
      case 'syncing':
        return '同步中';
      case 'error':
        return '錯誤';
      case 'offline':
        return '離線';
      default:
        return '已停用';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'enabled':
        return 'success';
      case 'syncing':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <MirrorToggleContainer>
      {/* Mirror開關 */}
      <Box display="flex" alignItems="center" gap={1}>
        <Switch
          checked={enabled}
          onChange={handleToggle}
          disabled={isLoading || syncing}
          color="primary"
          size="small"
        />
        <Typography variant="body2" fontWeight="medium">
          Mirror Code
        </Typography>
      </Box>

      {/* 狀態指示 */}
      <StatusChip
        label={getStatusText()}
        status={status}
        size="small"
      />

      {/* 同步狀態 */}
      {enabled && (
        <Box display="flex" alignItems="center" gap={1}>
          {syncing && (
            <CircularProgress size={16} thickness={4} />
          )}
          
          <Typography variant="caption" color="text.secondary">
            {syncCount > 0 ? `同步: ${syncCount}次` : '未同步'}
          </Typography>
          
          {!syncing && enabled && (
            <Typography
              variant="caption"
              color="primary"
              sx={{ 
                cursor: 'pointer',
                '&:hover': { textDecoration: 'underline' }
              }}
              onClick={handleSync}
            >
              立即同步
            </Typography>
          )}
        </Box>
      )}

      {/* 最後同步時間 */}
      {lastSync && (
        <Typography variant="caption" color="text.secondary">
          {new Date(lastSync).toLocaleTimeString()}
        </Typography>
      )}

      {/* 載入指示 */}
      {isLoading && !syncing && (
        <CircularProgress size={16} thickness={4} />
      )}
    </MirrorToggleContainer>
  );
};

export default MirrorToggle;

// Python兼容性導出
export const MirrorToggleConfig = {
  name: 'MirrorToggle',
  description: 'Mirror Code開關控制組件',
  props: {
    enabled: { type: 'boolean', required: true },
    syncing: { type: 'boolean', required: true },
    status: { 
      type: 'enum', 
      values: ['disabled', 'enabled', 'syncing', 'error', 'offline'],
      required: true 
    },
    syncCount: { type: 'number', required: true },
    lastSync: { type: 'string', required: false },
    onToggle: { type: 'function', required: true },
    onSync: { type: 'function', required: true }
  },
  events: ['toggle', 'sync'],
  styling: {
    container: 'MirrorToggleContainer',
    statusChip: 'StatusChip'
  }
};

/*
Python使用示例:

from ui.mirror_code.components.mirror_toggle import MirrorToggleConfig

# 組件配置
mirror_toggle_props = {
    "enabled": True,
    "syncing": False,
    "status": "enabled",
    "syncCount": 5,
    "lastSync": "2025-07-11T12:30:00Z",
    "onToggle": lambda enabled: handle_mirror_toggle(enabled),
    "onSync": lambda: handle_mirror_sync()
}

# 渲染組件
render_component("MirrorToggle", mirror_toggle_props)
*/