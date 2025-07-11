"""
Mirror Settings Panel - Mirror設置面板
提供Mirror Code系統的詳細配置和管理界面
"""

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Switch,
  TextField,
  Button,
  Divider,
  FormControl,
  FormLabel,
  FormGroup,
  FormControlLabel,
  Select,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  ExpandMore,
  Settings,
  Sync,
  CloudSync,
  Delete,
  Add,
  Edit,
  Save,
  Cancel
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

const SettingsCard = styled(Card)(({ theme }) => ({
  maxWidth: 800,
  margin: 'auto',
}));

const SettingSection = styled(Box)(({ theme }) => ({
  marginBottom: theme.spacing(3),
}));

const SyncRuleItem = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: theme.spacing(1),
  backgroundColor: theme.palette.background.default,
  borderRadius: theme.shape.borderRadius,
  marginBottom: theme.spacing(1),
}));

interface MirrorConfig {
  enabled: boolean;
  autoSync: boolean;
  syncInterval: number;
  debugMode: boolean;
  claudeIntegration: boolean;
  websocketPort: number;
  localAdapters: string[];
  remoteEndpoints: RemoteEndpoint[];
}

interface RemoteEndpoint {
  id: string;
  name: string;
  type: string;
  host: string;
  port: number;
  enabled: boolean;
}

interface SyncRule {
  id: string;
  pattern: string;
  direction: string;
  strategy: string;
  enabled: boolean;
}

interface MirrorSettingsPanelProps {
  config: MirrorConfig;
  syncRules: SyncRule[];
  onConfigChange: (config: MirrorConfig) => void;
  onSyncRuleAdd: (rule: Omit<SyncRule, 'id'>) => void;
  onSyncRuleUpdate: (id: string, rule: Partial<SyncRule>) => void;
  onSyncRuleDelete: (id: string) => void;
  onTestConnection: (endpoint: RemoteEndpoint) => Promise<boolean>;
  onSaveSettings: () => Promise<boolean>;
  onResetSettings: () => void;
}

const MirrorSettingsPanel: React.FC<MirrorSettingsPanelProps> = ({
  config,
  syncRules,
  onConfigChange,
  onSyncRuleAdd,
  onSyncRuleUpdate,
  onSyncRuleDelete,
  onTestConnection,
  onSaveSettings,
  onResetSettings
}) => {
  const [localConfig, setLocalConfig] = useState<MirrorConfig>(config);
  const [newRuleDialog, setNewRuleDialog] = useState(false);
  const [newRule, setNewRule] = useState<Omit<SyncRule, 'id'>>({
    pattern: '*',
    direction: 'bidirectional',
    strategy: 'real_time',
    enabled: true
  });
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    setLocalConfig(config);
  }, [config]);

  const handleConfigChange = (field: keyof MirrorConfig, value: any) => {
    const updatedConfig = { ...localConfig, [field]: value };
    setLocalConfig(updatedConfig);
    onConfigChange(updatedConfig);
  };

  const handleSaveSettings = async () => {
    setSaving(true);
    try {
      const success = await onSaveSettings();
      setSaveMessage(success ? '設置保存成功' : '設置保存失敗');
      setTimeout(() => setSaveMessage(null), 3000);
    } finally {
      setSaving(false);
    }
  };

  const handleAddSyncRule = () => {
    onSyncRuleAdd(newRule);
    setNewRule({
      pattern: '*',
      direction: 'bidirectional',
      strategy: 'real_time',
      enabled: true
    });
    setNewRuleDialog(false);
  };

  const handleTestEndpoint = async (endpoint: RemoteEndpoint) => {
    try {
      const success = await onTestConnection(endpoint);
      setSaveMessage(success ? `${endpoint.name} 連接成功` : `${endpoint.name} 連接失敗`);
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (error) {
      setSaveMessage(`連接測試失敗: ${error}`);
      setTimeout(() => setSaveMessage(null), 3000);
    }
  };

  return (
    <SettingsCard>
      <CardHeader
        title="Mirror Code 設置"
        subheader="配置Mirror Code系統的同步和集成選項"
        action={
          <IconButton onClick={handleSaveSettings} disabled={saving}>
            <Save />
          </IconButton>
        }
      />
      
      <CardContent>
        {/* 保存狀態消息 */}
        {saveMessage && (
          <Alert 
            severity={saveMessage.includes('成功') ? 'success' : 'error'}
            sx={{ mb: 2 }}
          >
            {saveMessage}
          </Alert>
        )}

        {/* 基本設置 */}
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Typography variant="h6">基本設置</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <SettingSection>
              <FormGroup>
                <FormControlLabel
                  control={
                    <Switch
                      checked={localConfig.enabled}
                      onChange={(e) => handleConfigChange('enabled', e.target.checked)}
                    />
                  }
                  label="啟用Mirror Code"
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={localConfig.autoSync}
                      onChange={(e) => handleConfigChange('autoSync', e.target.checked)}
                    />
                  }
                  label="自動同步"
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={localConfig.debugMode}
                      onChange={(e) => handleConfigChange('debugMode', e.target.checked)}
                    />
                  }
                  label="調試模式"
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={localConfig.claudeIntegration}
                      onChange={(e) => handleConfigChange('claudeIntegration', e.target.checked)}
                    />
                  }
                  label="Claude集成"
                />
              </FormGroup>
            </SettingSection>

            <SettingSection>
              <TextField
                label="同步間隔 (秒)"
                type="number"
                value={localConfig.syncInterval}
                onChange={(e) => handleConfigChange('syncInterval', parseInt(e.target.value))}
                InputProps={{ inputProps: { min: 1, max: 3600 } }}
                fullWidth
                margin="normal"
              />
              
              <TextField
                label="WebSocket端口"
                type="number"
                value={localConfig.websocketPort}
                onChange={(e) => handleConfigChange('websocketPort', parseInt(e.target.value))}
                InputProps={{ inputProps: { min: 1024, max: 65535 } }}
                fullWidth
                margin="normal"
              />
            </SettingSection>
          </AccordionDetails>
        </Accordion>

        {/* 同步規則 */}
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Typography variant="h6">同步規則</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <SettingSection>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="subtitle1">同步規則列表</Typography>
                <Button
                  startIcon={<Add />}
                  variant="outlined"
                  size="small"
                  onClick={() => setNewRuleDialog(true)}
                >
                  添加規則
                </Button>
              </Box>

              {syncRules.map((rule) => (
                <SyncRuleItem key={rule.id}>
                  <Box>
                    <Typography variant="body2" fontWeight="medium">
                      {rule.pattern}
                    </Typography>
                    <Box display="flex" gap={1} mt={0.5}>
                      <Chip label={rule.direction} size="small" />
                      <Chip label={rule.strategy} size="small" />
                      <Chip 
                        label={rule.enabled ? '啟用' : '停用'} 
                        size="small"
                        color={rule.enabled ? 'success' : 'default'}
                      />
                    </Box>
                  </Box>
                  
                  <Box>
                    <IconButton
                      size="small"
                      onClick={() => onSyncRuleUpdate(rule.id, { enabled: !rule.enabled })}
                    >
                      <Edit />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => onSyncRuleDelete(rule.id)}
                      color="error"
                    >
                      <Delete />
                    </IconButton>
                  </Box>
                </SyncRuleItem>
              ))}
            </SettingSection>
          </AccordionDetails>
        </Accordion>

        {/* 遠端端點 */}
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Typography variant="h6">遠端端點</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <SettingSection>
              {localConfig.remoteEndpoints.map((endpoint) => (
                <SyncRuleItem key={endpoint.id}>
                  <Box>
                    <Typography variant="body2" fontWeight="medium">
                      {endpoint.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {endpoint.type} - {endpoint.host}:{endpoint.port}
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Button
                      size="small"
                      startIcon={<CloudSync />}
                      onClick={() => handleTestEndpoint(endpoint)}
                    >
                      測試連接
                    </Button>
                    <Switch
                      checked={endpoint.enabled}
                      onChange={(e) => {
                        const updatedEndpoints = localConfig.remoteEndpoints.map(ep =>
                          ep.id === endpoint.id ? { ...ep, enabled: e.target.checked } : ep
                        );
                        handleConfigChange('remoteEndpoints', updatedEndpoints);
                      }}
                      size="small"
                    />
                  </Box>
                </SyncRuleItem>
              ))}
            </SettingSection>
          </AccordionDetails>
        </Accordion>

        {/* 操作按鈕 */}
        <Box display="flex" justifyContent="space-between" mt={3}>
          <Button
            variant="outlined"
            color="secondary"
            onClick={onResetSettings}
          >
            重置設置
          </Button>
          
          <Box display="flex" gap={2}>
            <Button
              variant="contained"
              color="primary"
              onClick={handleSaveSettings}
              disabled={saving}
              startIcon={<Save />}
            >
              {saving ? '保存中...' : '保存設置'}
            </Button>
          </Box>
        </Box>
      </CardContent>

      {/* 新增同步規則對話框 */}
      <Dialog open={newRuleDialog} onClose={() => setNewRuleDialog(false)}>
        <DialogTitle>新增同步規則</DialogTitle>
        <DialogContent>
          <TextField
            label="匹配模式"
            value={newRule.pattern}
            onChange={(e) => setNewRule({ ...newRule, pattern: e.target.value })}
            fullWidth
            margin="normal"
            placeholder="例如: *.py, src/**, *.json"
          />
          
          <FormControl fullWidth margin="normal">
            <FormLabel>同步方向</FormLabel>
            <Select
              value={newRule.direction}
              onChange={(e) => setNewRule({ ...newRule, direction: e.target.value })}
            >
              <MenuItem value="local_to_remote">本地到遠端</MenuItem>
              <MenuItem value="remote_to_local">遠端到本地</MenuItem>
              <MenuItem value="bidirectional">雙向同步</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl fullWidth margin="normal">
            <FormLabel>同步策略</FormLabel>
            <Select
              value={newRule.strategy}
              onChange={(e) => setNewRule({ ...newRule, strategy: e.target.value })}
            >
              <MenuItem value="real_time">實時同步</MenuItem>
              <MenuItem value="batch">批量同步</MenuItem>
              <MenuItem value="on_demand">按需同步</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewRuleDialog(false)}>
            取消
          </Button>
          <Button onClick={handleAddSyncRule} variant="contained">
            添加
          </Button>
        </DialogActions>
      </Dialog>
    </SettingsCard>
  );
};

export default MirrorSettingsPanel;

// Python兼容性導出
export const MirrorSettingsPanelConfig = {
  name: 'MirrorSettingsPanel',
  description: 'Mirror Code設置面板組件',
  props: {
    config: { type: 'object', required: true },
    syncRules: { type: 'array', required: true },
    onConfigChange: { type: 'function', required: true },
    onSyncRuleAdd: { type: 'function', required: true },
    onSyncRuleUpdate: { type: 'function', required: true },
    onSyncRuleDelete: { type: 'function', required: true },
    onTestConnection: { type: 'function', required: true },
    onSaveSettings: { type: 'function', required: true },
    onResetSettings: { type: 'function', required: true }
  },
  events: ['configChange', 'syncRuleAdd', 'syncRuleUpdate', 'syncRuleDelete', 'testConnection', 'saveSettings', 'resetSettings'],
  styling: {
    card: 'SettingsCard',
    section: 'SettingSection',
    ruleItem: 'SyncRuleItem'
  }
};

/*
Python使用示例:

from ui.mirror_code.panels.mirror_settings_panel import MirrorSettingsPanelConfig

# 設置面板配置
settings_panel_props = {
    "config": {
        "enabled": True,
        "autoSync": True,
        "syncInterval": 30,
        "debugMode": False,
        "claudeIntegration": True,
        "websocketPort": 8765,
        "localAdapters": ["macos", "linux"],
        "remoteEndpoints": []
    },
    "syncRules": [
        {
            "id": "rule1",
            "pattern": "*.py",
            "direction": "bidirectional",
            "strategy": "real_time",
            "enabled": True
        }
    ],
    "onConfigChange": lambda config: handle_config_change(config),
    "onSyncRuleAdd": lambda rule: add_sync_rule(rule),
    "onSyncRuleUpdate": lambda id, rule: update_sync_rule(id, rule),
    "onSyncRuleDelete": lambda id: delete_sync_rule(id),
    "onTestConnection": lambda endpoint: test_endpoint_connection(endpoint),
    "onSaveSettings": lambda: save_mirror_settings(),
    "onResetSettings": lambda: reset_mirror_settings()
}

# 渲染組件
render_component("MirrorSettingsPanel", settings_panel_props)
*/