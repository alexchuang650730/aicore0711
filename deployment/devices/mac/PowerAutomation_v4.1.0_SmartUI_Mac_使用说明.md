# 🍎 PowerAutomation v4.1.0 SmartUI - macOS 使用说明

## 📋 **系统要求**

### **最低要求**
- **macOS**: 10.15 Catalina 或更高版本
- **内存**: 8GB RAM
- **存储**: 20GB 可用空间
- **处理器**: Intel x64 或 Apple Silicon (M1/M2/M3)
- **网络**: 稳定的互联网连接

### **推荐配置**
- **macOS**: 12.0 Monterey 或更高版本
- **内存**: 16GB RAM
- **存储**: 50GB 可用空间
- **处理器**: Apple Silicon M2 或更高

### **必需软件**
- **Xcode Command Line Tools**: 自动安装
- **Homebrew**: 自动安装 (如果未安装)
- **Python 3.11+**: 自动安装
- **Node.js 20.x+**: 自动安装

---

## 🚀 **安装步骤**

### **1. 下载安装包**
```bash
# 使用curl下载
curl -L -o PowerAutomation_v4.1.0_SmartUI_Mac.tar.gz \
  https://github.com/alexchuang650730/aicore0707/releases/download/v4.1.0/PowerAutomation_v4.1.0_SmartUI_Mac.tar.gz

# 或使用wget下载
wget https://github.com/alexchuang650730/aicore0707/releases/download/v4.1.0/PowerAutomation_v4.1.0_SmartUI_Mac.tar.gz
```

### **2. 验证下载完整性**
```bash
# 验证SHA256校验和
shasum -a 256 PowerAutomation_v4.1.0_SmartUI_Mac.tar.gz
# 应该输出: [校验和将在发布时提供]
```

### **3. 解压安装包**
```bash
tar -xzf PowerAutomation_v4.1.0_SmartUI_Mac.tar.gz
cd PowerAutomation_v4.1.0_SmartUI_Mac
```

### **4. 运行安装脚本**
```bash
# 赋予执行权限
chmod +x install_mac.sh

# 运行安装 (需要管理员权限)
sudo ./install_mac.sh
```

### **5. 验证安装**
```bash
# 检查安装状态
powerautomation --version

# 启动SmartUI MCP服务
powerautomation smartui start

# 验证核心功能
powerautomation test p0
```

---

## 🎨 **SmartUI功能使用**

### **1. 启动SmartUI服务**
```bash
# 启动服务
powerautomation smartui start

# 检查服务状态
powerautomation smartui status

# 查看服务日志
powerautomation smartui logs
```

### **2. 生成UI组件**
```bash
# 生成基础按钮组件
powerautomation smartui generate button MyButton \
  --variant primary \
  --size large \
  --theme default

# 生成表单输入组件
powerautomation smartui generate input EmailInput \
  --type email \
  --label "邮箱地址" \
  --required true

# 生成复杂表单
powerautomation smartui generate form UserForm \
  --fields "name,email,password" \
  --validation true \
  --theme dark
```

### **3. 主题管理**
```bash
# 列出可用主题
powerautomation smartui themes list

# 应用主题
powerautomation smartui themes apply dark

# 创建自定义主题
powerautomation smartui themes create MyTheme \
  --primary "#007AFF" \
  --secondary "#5856D6" \
  --background "#000000"
```

### **4. 组件预览**
```bash
# 启动预览服务器
powerautomation smartui preview start

# 在浏览器中打开预览
open http://localhost:3000/preview

# 实时预览组件
powerautomation smartui preview component MyButton
```

---

## 🎬 **录制即测试功能**

### **1. 启动录制**
```bash
# 启动录制会话
powerautomation record start "我的测试场景"

# 指定浏览器
powerautomation record start "登录测试" --browser chrome

# 录制移动端视图
powerautomation record start "移动端测试" --device mobile
```

### **2. 录制过程**
1. **打开目标网页**: 录制器会自动打开浏览器
2. **执行操作**: 正常使用网页，所有操作都会被记录
3. **添加断言**: 使用快捷键 `Cmd+Shift+A` 添加验证点
4. **停止录制**: 使用快捷键 `Cmd+Shift+S` 或关闭浏览器

### **3. 生成测试代码**
```bash
# 生成测试代码
powerautomation record generate "我的测试场景" \
  --format pytest \
  --output tests/

# 优化测试代码
powerautomation record optimize "我的测试场景" \
  --ai-enhance true

# 运行生成的测试
powerautomation test run tests/my_test_scenario.py
```

---

## 🧪 **测试系统使用**

### **1. 运行测试**
```bash
# 运行P0核心测试
powerautomation test p0

# 运行UI测试
powerautomation test ui --browser chrome

# 运行所有测试
powerautomation test all --report html

# 运行特定测试套件
powerautomation test suite login_workflow
```

### **2. 测试报告**
```bash
# 生成HTML报告
powerautomation test report --format html --output reports/

# 生成JSON报告
powerautomation test report --format json --output reports/

# 查看最新报告
open reports/latest_report.html
```

### **3. 测试配置**
```bash
# 查看测试配置
powerautomation test config show

# 更新测试配置
powerautomation test config set browser chrome
powerautomation test config set timeout 30
powerautomation test config set parallel true
```

---

## 🔧 **ClaudEditor集成**

### **1. 启动ClaudEditor**
```bash
# 启动ClaudEditor with SmartUI
powerautomation claudeditor start --with-smartui

# 启动测试平台
powerautomation claudeditor start --with-testing

# 启动完整功能
powerautomation claudeditor start --full
```

### **2. 在ClaudEditor中使用SmartUI**
1. **打开SmartUI面板**: 在ClaudEditor中按 `Cmd+Shift+U`
2. **选择组件类型**: 从组件库中选择需要的组件
3. **配置参数**: 设置组件属性和样式
4. **生成代码**: 点击"生成"按钮自动生成代码
5. **插入项目**: 将生成的代码插入到当前项目中

### **3. 测试集成**
1. **打开测试面板**: 在ClaudEditor中按 `Cmd+Shift+T`
2. **录制测试**: 点击"开始录制"按钮
3. **执行操作**: 在预览窗口中执行测试操作
4. **生成测试**: 录制完成后自动生成测试代码
5. **运行测试**: 在测试面板中运行生成的测试

---

## 🛠️ **故障排除**

### **常见问题**

#### **1. 安装失败**
```bash
# 检查系统权限
sudo -v

# 清理之前的安装
sudo rm -rf /usr/local/powerautomation

# 重新安装
sudo ./install_mac.sh --clean-install
```

#### **2. 服务启动失败**
```bash
# 检查端口占用
lsof -i :8080

# 杀死占用进程
sudo kill -9 [PID]

# 重启服务
powerautomation smartui restart
```

#### **3. 浏览器兼容性问题**
```bash
# 更新浏览器驱动
powerautomation drivers update

# 指定浏览器版本
powerautomation record start --browser chrome --version 120

# 使用无头模式
powerautomation test ui --headless
```

#### **4. 权限问题**
```bash
# 修复权限
sudo chown -R $(whoami) /usr/local/powerautomation

# 重新设置环境变量
echo 'export PATH="/usr/local/powerautomation/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### **性能优化**

#### **1. 内存优化**
```bash
# 设置内存限制
powerautomation config set memory_limit 8GB

# 启用内存监控
powerautomation monitor memory --alert 80%
```

#### **2. 生成速度优化**
```bash
# 启用缓存
powerautomation config set cache_enabled true

# 设置并行生成
powerautomation config set parallel_generation 4

# 预热缓存
powerautomation smartui cache warm
```

---

## 📚 **高级功能**

### **1. 自定义模板**
```bash
# 创建自定义模板
powerautomation smartui template create MyTemplate \
  --base button \
  --custom-props "icon,tooltip"

# 使用自定义模板
powerautomation smartui generate MyTemplate IconButton \
  --icon "star" \
  --tooltip "收藏"
```

### **2. 批量生成**
```bash
# 从配置文件批量生成
powerautomation smartui batch generate \
  --config components_config.json

# 批量应用主题
powerautomation smartui batch theme apply \
  --theme dark \
  --components "Button,Input,Form"
```

### **3. API集成**
```bash
# 启动API服务
powerautomation api start --port 8080

# 测试API
curl http://localhost:8080/api/v1/smartui/generate \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"type":"button","name":"TestButton","props":{"variant":"primary"}}'
```

---

## 🔄 **升级和维护**

### **从v4.0.x升级**
```bash
# 备份当前配置
powerautomation backup create v4.0.x-backup

# 下载升级包
curl -L -o upgrade_v4.1.0.tar.gz \
  https://github.com/alexchuang650730/aicore0707/releases/download/v4.1.0/upgrade_v4.1.0.tar.gz

# 运行升级
tar -xzf upgrade_v4.1.0.tar.gz
sudo ./upgrade_to_v4.1.0.sh

# 验证升级
powerautomation --version
powerautomation test p0
```

### **定期维护**
```bash
# 清理缓存
powerautomation cache clean

# 更新依赖
powerautomation update dependencies

# 检查系统健康
powerautomation health check

# 备份配置
powerautomation backup create daily-backup
```

---

## 📞 **技术支持**

### **获取帮助**
- **命令行帮助**: `powerautomation --help`
- **在线文档**: https://docs.powerautomation.ai
- **GitHub Issues**: https://github.com/alexchuang650730/aicore0707/issues

### **日志和诊断**
```bash
# 查看系统日志
powerautomation logs system

# 查看错误日志
powerautomation logs error

# 生成诊断报告
powerautomation diagnose --output diagnostic_report.zip
```

### **社区支持**
- **官方论坛**: https://forum.powerautomation.ai
- **Discord社区**: https://discord.gg/powerautomation
- **微信群**: 扫描二维码加入技术交流群

---

**🚀 享受PowerAutomation v4.1.0 SmartUI带来的革命性AI开发体验！**

*最后更新: 2025年7月9日*

