# PowerAutomation v4.6.6 雲端到邊緣部署配置指南

## 🌍 網絡架構說明

### 問題分析
你說得很對！**EC2在AWS雲端，你的macOS在本地網絡，它們不在同一個局域網**。

```
AWS雲端               本地網絡
┌─────────────┐      ┌──────────────┐
│   EC2實例   │ ···> │  你的macOS   │
│ (構建服務器) │      │ (部署目標)   │
└─────────────┘      └──────────────┘
   公網IP              內網IP/公網IP
```

## 🔧 解決方案選項

### 方案A: 公網IP部署 (推薦)
**適用場景**: 你的macOS有公網IP或可以配置端口轉發

```bash
# 1. 獲取你的公網IP
curl ifconfig.me

# 2. 配置路由器端口轉發
# 路由器設定: 外部端口2222 → 內部設備端口22

# 3. 配置部署目標
{
  "host": "你的公網IP",
  "username": "你的用戶名", 
  "ssh_port": 2222,
  "ssh_key_path": "~/.ssh/id_rsa"
}
```

### 方案B: VPN隧道部署
**適用場景**: 建立EC2到本地的VPN連接

```bash
# 1. 在EC2上配置VPN客戶端
# 2. 連接到你的本地網絡VPN
# 3. 通過VPN使用內網IP部署
```

### 方案C: 反向隧道部署
**適用場景**: 從本地主動連接到EC2

```bash
# 1. 本地設備建立反向SSH隧道到EC2
ssh -R 2222:localhost:22 ec2-user@EC2_PUBLIC_IP

# 2. EC2通過隧道連接本地設備
ssh -p 2222 localhost
```

### 方案D: 本地構建 + 遠程推送 (最簡單)
**適用場景**: 在本地構建，推送到本地設備

```bash
# 1. 本地構建DMG
python deployment/build_local.py

# 2. 本地部署到同網段設備
python deployment/local_deployment.py
```

## 🎯 推薦配置流程

### 步驟1: 檢測你的網絡環境
```bash
# 運行網絡檢測工具
python check_network_setup.py
```

### 步驟2: 選擇部署方案
- **個人使用**: 選擇方案D (本地構建)
- **團隊使用**: 選擇方案A (公網IP)
- **企業環境**: 選擇方案B (VPN)

### 步驟3: 配置部署目標
```json
{
  "deployment_targets": [
    {
      "name": "your_mac",
      "host": "你的IP地址",
      "username": "你的用戶名",
      "ssh_port": 22,
      "connection_type": "public_ip|vpn|tunnel|local"
    }
  ]
}
```

## 💡 我來為你創建正確的配置工具