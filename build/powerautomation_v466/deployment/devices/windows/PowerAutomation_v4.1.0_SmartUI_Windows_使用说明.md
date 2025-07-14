# 🪟 PowerAutomation v4.1.0 SmartUI - Windows 使用说明

## 📋 **系统要求**

### **最低要求**
- **Windows**: 10 版本 1903 或更高版本
- **内存**: 8GB RAM
- **存储**: 20GB 可用空间
- **处理器**: x64 架构处理器
- **网络**: 稳定的互联网连接
- **.NET Framework**: 4.8 或更高版本

### **推荐配置**
- **Windows**: 11 或 Windows 10 版本 21H2
- **内存**: 16GB RAM
- **存储**: 50GB 可用空间
- **处理器**: Intel Core i5 或 AMD Ryzen 5 或更高

### **必需软件**
- **Visual Studio Build Tools**: 自动安装
- **Git for Windows**: 自动安装 (如果未安装)
- **Python 3.11+**: 自动安装
- **Node.js 20.x+**: 自动安装

---

## 🚀 **安装步骤**

### **1. 下载安装包**

#### **使用PowerShell下载**
```powershell
# 使用Invoke-WebRequest下载
Invoke-WebRequest -Uri "https://github.com/alexchuang650730/aicore0707/releases/download/v4.1.0/PowerAutomation_v4.1.0_SmartUI_Windows.zip" -OutFile "PowerAutomation_v4.1.0_SmartUI_Windows.zip"
```

#### **使用浏览器下载**
访问: https://github.com/alexchuang650730/aicore0707/releases/download/v4.1.0/PowerAutomation_v4.1.0_SmartUI_Windows.zip

### **2. 验证下载完整性**
```powershell
# 验证SHA256校验和
Get-FileHash PowerAutomation_v4.1.0_SmartUI_Windows.zip -Algorithm SHA256
# 应该输出: [校验和将在发布时提供]
```

### **3. 解压安装包**
```powershell
# 解压到当前目录
Expand-Archive PowerAutomation_v4.1.0_SmartUI_Windows.zip -DestinationPath .
cd PowerAutomation_v4.1.0_SmartUI_Windows
```

### **4. 以管理员身份运行安装**
```powershell
# 右键点击PowerShell，选择"以管理员身份运行"
# 然后执行安装脚本
.\install_windows.bat
```

### **5. 验证安装**
```cmd
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
```cmd
# 启动服务
powerautomation smartui start

# 检查服务状态
powerautomation smartui status

# 查看服务日志
powerautomation smartui logs
```

### **2. 生成UI组件**
```cmd
# 生成基础按钮组件
powerautomation smartui generate button MyButton ^
  --variant primary ^
  --size large ^
  --theme default

# 生成表单输入组件
powerautomation smartui generate input EmailInput ^
  --type email ^
  --label "邮箱地址" ^
  --required true

# 生成复杂表单
powerautomation smartui generate form UserForm ^
  --fields "name,email,password" ^
  --validation true ^
  --theme dark
```

### **3. 主题管理**
```cmd
# 列出可用主题
powerautomation smartui themes list

# 应用主题
powerautomation smartui themes apply dark

# 创建自定义主题
powerautomation smartui themes create MyTheme ^
  --primary "#007AFF" ^
  --secondary "#5856D6" ^
  --background "#000000"
```

### **4. 组件预览**
```cmd
# 启动预览服务器
powerautomation smartui preview start

# 在浏览器中打开预览
start http://localhost:3000/preview

# 实时预览组件
powerautomation smartui preview component MyButton
```

---

## 🎬 **录制即测试功能**

### **1. 启动录制**
```cmd
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
3. **添加断言**: 使用快捷键 `Ctrl+Shift+A` 添加验证点
4. **停止录制**: 使用快捷键 `Ctrl+Shift+S` 或关闭浏览器

### **3. 生成测试代码**
```cmd
# 生成测试代码
powerautomation record generate "我的测试场景" ^
  --format pytest ^
  --output tests\

# 优化测试代码
powerautomation record optimize "我的测试场景" ^
  --ai-enhance true

# 运行生成的测试
powerautomation test run tests\my_test_scenario.py
```

---

## 🧪 **测试系统使用**

### **1. 运行测试**
```cmd
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
```cmd
# 生成HTML报告
powerautomation test report --format html --output reports\

# 生成JSON报告
powerautomation test report --format json --output reports\

# 查看最新报告
start reports\latest_report.html
```

### **3. 测试配置**
```cmd
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
```cmd
# 启动ClaudEditor with SmartUI
powerautomation claudeditor start --with-smartui

# 启动测试平台
powerautomation claudeditor start --with-testing

# 启动完整功能
powerautomation claudeditor start --full
```

### **2. 在ClaudEditor中使用SmartUI**
1. **打开SmartUI面板**: 在ClaudEditor中按 `Ctrl+Shift+U`
2. **选择组件类型**: 从组件库中选择需要的组件
3. **配置参数**: 设置组件属性和样式
4. **生成代码**: 点击"生成"按钮自动生成代码
5. **插入项目**: 将生成的代码插入到当前项目中

### **3. 测试集成**
1. **打开测试面板**: 在ClaudEditor中按 `Ctrl+Shift+T`
2. **录制测试**: 点击"开始录制"按钮
3. **执行操作**: 在预览窗口中执行测试操作
4. **生成测试**: 录制完成后自动生成测试代码
5. **运行测试**: 在测试面板中运行生成的测试

---

## 🛠️ **故障排除**

### **常见问题**

#### **1. 安装失败**
```cmd
# 检查管理员权限
net session >nul 2>&1
if %errorLevel% == 0 (
    echo 具有管理员权限
) else (
    echo 需要管理员权限，请以管理员身份运行
)

# 清理之前的安装
rmdir /s /q "C:\Program Files\PowerAutomation"

# 重新安装
.\install_windows.bat --clean-install
```

#### **2. 服务启动失败**
```cmd
# 检查端口占用
netstat -ano | findstr :8080

# 杀死占用进程
taskkill /PID [PID] /F

# 重启服务
powerautomation smartui restart
```

#### **3. 浏览器兼容性问题**
```cmd
# 更新浏览器驱动
powerautomation drivers update

# 指定浏览器版本
powerautomation record start --browser chrome --version 120

# 使用无头模式
powerautomation test ui --headless
```

#### **4. 权限问题**
```cmd
# 修复权限 (以管理员身份运行)
icacls "C:\Program Files\PowerAutomation" /grant Users:F /T

# 重新设置环境变量
setx PATH "%PATH%;C:\Program Files\PowerAutomation\bin" /M
```

#### **5. Windows Defender问题**
```powershell
# 添加PowerAutomation到Windows Defender排除列表
Add-MpPreference -ExclusionPath "C:\Program Files\PowerAutomation"
Add-MpPreference -ExclusionProcess "powerautomation.exe"
```

### **性能优化**

#### **1. 内存优化**
```cmd
# 设置内存限制
powerautomation config set memory_limit 8GB

# 启用内存监控
powerautomation monitor memory --alert 80%
```

#### **2. 生成速度优化**
```cmd
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
```cmd
# 创建自定义模板
powerautomation smartui template create MyTemplate ^
  --base button ^
  --custom-props "icon,tooltip"

# 使用自定义模板
powerautomation smartui generate MyTemplate IconButton ^
  --icon "star" ^
  --tooltip "收藏"
```

### **2. 批量生成**
```cmd
# 从配置文件批量生成
powerautomation smartui batch generate ^
  --config components_config.json

# 批量应用主题
powerautomation smartui batch theme apply ^
  --theme dark ^
  --components "Button,Input,Form"
```

### **3. API集成**
```cmd
# 启动API服务
powerautomation api start --port 8080

# 测试API (使用curl for Windows)
curl http://localhost:8080/api/v1/smartui/generate ^
  -X POST ^
  -H "Content-Type: application/json" ^
  -d "{\"type\":\"button\",\"name\":\"TestButton\",\"props\":{\"variant\":\"primary\"}}"
```

---

## 🔄 **升级和维护**

### **从v4.0.x升级**
```cmd
# 备份当前配置
powerautomation backup create v4.0.x-backup

# 下载升级包
Invoke-WebRequest -Uri "https://github.com/alexchuang650730/aicore0707/releases/download/v4.1.0/upgrade_v4.1.0_windows.zip" -OutFile "upgrade_v4.1.0_windows.zip"

# 运行升级 (以管理员身份)
Expand-Archive upgrade_v4.1.0_windows.zip
.\upgrade_v4.1.0_windows\upgrade_to_v4.1.0.bat

# 验证升级
powerautomation --version
powerautomation test p0
```

### **定期维护**
```cmd
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

## 🔧 **Windows特定配置**

### **1. 防火墙配置**
```cmd
# 添加防火墙规则 (以管理员身份运行)
netsh advfirewall firewall add rule name="PowerAutomation" dir=in action=allow program="C:\Program Files\PowerAutomation\bin\powerautomation.exe"
netsh advfirewall firewall add rule name="PowerAutomation API" dir=in action=allow protocol=TCP localport=8080
```

### **2. 任务计划程序**
```cmd
# 创建开机自启动任务
schtasks /create /tn "PowerAutomation Service" /tr "C:\Program Files\PowerAutomation\bin\powerautomation.exe service start" /sc onstart /ru SYSTEM
```

### **3. 环境变量**
```cmd
# 查看环境变量
echo %POWERAUTOMATION_HOME%
echo %PATH%

# 手动设置环境变量 (如果自动设置失败)
setx POWERAUTOMATION_HOME "C:\Program Files\PowerAutomation" /M
setx PATH "%PATH%;C:\Program Files\PowerAutomation\bin" /M
```

---

## 📞 **技术支持**

### **获取帮助**
- **命令行帮助**: `powerautomation --help`
- **在线文档**: https://docs.powerautomation.ai
- **GitHub Issues**: https://github.com/alexchuang650730/aicore0707/issues

### **日志和诊断**
```cmd
# 查看系统日志
powerautomation logs system

# 查看错误日志
powerautomation logs error

# 生成诊断报告
powerautomation diagnose --output diagnostic_report.zip
```

### **Windows事件日志**
```cmd
# 查看PowerAutomation事件日志
eventvwr.msc
# 导航到: Windows日志 > 应用程序 > 筛选器 > PowerAutomation
```

### **社区支持**
- **官方论坛**: https://forum.powerautomation.ai
- **Discord社区**: https://discord.gg/powerautomation
- **QQ群**: 123456789 (PowerAutomation技术交流)

---

## 🔒 **安全注意事项**

### **1. 用户账户控制 (UAC)**
- 某些功能需要管理员权限
- 建议在安装后以标准用户身份运行
- 录制功能可能需要提升权限

### **2. 网络安全**
- 确保防火墙规则正确配置
- API服务默认只监听本地地址
- 生产环境请配置HTTPS

### **3. 数据保护**
- 录制的测试数据存储在本地
- 定期备份重要配置和数据
- 敏感信息不会上传到云端

---

**🚀 享受PowerAutomation v4.1.0 SmartUI带来的革命性AI开发体验！**

*最后更新: 2025年7月9日*

