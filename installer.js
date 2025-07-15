#!/usr/bin/env node

/**
 * PowerAutomation v4.6.9.7 一鍵安裝工具
 * 集成K2 AI、支付儲值積分系統和PC/Mobile支持
 * 
 * 使用方法:
 * npm install -g powerautomation-installer
 * powerautomation install
 * 
 * 或者:
 * curl -fsSL https://raw.githubusercontent.com/alexchuang650730/aicore0711/main/installer.js | node
 */

const fs = require('fs');
const path = require('path');
const { execSync, spawn } = require('child_process');
const https = require('https');
const { program } = require('commander');
const chalk = require('chalk');
const inquirer = require('inquirer');
const ora = require('ora');

// 版本信息
const VERSION = '4.6.9.7';
const PRODUCT_NAME = 'PowerAutomation';

// 支付系統配置
const PAYMENT_CONFIG = {
    apiBase: 'https://api.powerauto.aiweb.com',
    webUrl: 'https://powerauto.aiweb.com',
    creditsRequired: {
        community: 0,
        personal: 100,
        enterprise: 500
    }
};

// 平台檢測
const PLATFORM = process.platform;
const ARCH = process.arch;

// 安裝腳本URLs
const INSTALL_SCRIPTS = {
    darwin: 'https://raw.githubusercontent.com/alexchuang650730/aicore0711/main/install-script-macos-v4.6.9.7.sh',
    linux: 'https://raw.githubusercontent.com/alexchuang650730/aicore0711/main/install-script-linux-v4.6.9.7.sh',
    win32: 'https://raw.githubusercontent.com/alexchuang650730/aicore0711/main/install-script-windows-v4.6.9.7.ps1'
};

// 日誌函數
const log = {
    info: (msg) => console.log(chalk.blue(`ℹ ${msg}`)),
    success: (msg) => console.log(chalk.green(`✓ ${msg}`)),
    warning: (msg) => console.log(chalk.yellow(`⚠ ${msg}`)),
    error: (msg) => console.log(chalk.red(`✗ ${msg}`)),
    title: (msg) => console.log(chalk.bold.cyan(msg))
};

// 顯示歡迎信息
function showWelcome() {
    console.clear();
    console.log(chalk.cyan(`
╔══════════════════════════════════════════════════════════════════════════╗
║                     ${PRODUCT_NAME} v${VERSION}                              ║
║                        Node.js 一鍵安裝工具                               ║
║                                                                          ║
║  🚀 特色功能:                                                             ║
║   • K2 AI模型集成 (60%成本節省)                                           ║
║   • ClaudeEditor桌面版                                                   ║
║   • Mirror Code實時同步                                                  ║
║   • 支付儲值積分系統                                                      ║
║   • PC/Mobile響應式界面                                                  ║
║   • 企業級工作流管理                                                      ║
║                                                                          ║
║  💰 版本選擇:                                                             ║
║   • Community版 (免費) - 基礎功能                                         ║
║   • Personal版 (${PAYMENT_CONFIG.creditsRequired.personal}積分) - 個人增強功能                                      ║
║   • Enterprise版 (${PAYMENT_CONFIG.creditsRequired.enterprise}積分) - 完整功能集                                     ║
║                                                                          ║
║  🌐 支付系統: ${PAYMENT_CONFIG.webUrl}                          ║
╚══════════════════════════════════════════════════════════════════════════╝
    `));
}

// 檢查系統要求
function checkSystemRequirements() {
    const spinner = ora('檢查系統要求...').start();
    
    try {
        // 檢查Node.js版本
        const nodeVersion = process.version;
        const majorVersion = parseInt(nodeVersion.split('.')[0].substring(1));
        
        if (majorVersion < 16) {
            throw new Error(`需要Node.js 16或更高版本，當前版本: ${nodeVersion}`);
        }
        
        // 檢查平台支持
        if (!INSTALL_SCRIPTS[PLATFORM]) {
            throw new Error(`不支持的平台: ${PLATFORM}`);
        }
        
        // 檢查必要命令
        const requiredCommands = {
            darwin: ['curl', 'git'],
            linux: ['curl', 'git'],
            win32: ['powershell', 'git']
        };
        
        const commands = requiredCommands[PLATFORM] || [];
        for (const cmd of commands) {
            try {
                execSync(`which ${cmd}`, { stdio: 'ignore' });
            } catch (error) {
                throw new Error(`缺少必要命令: ${cmd}`);
            }
        }
        
        spinner.succeed('系統要求檢查完成');
        return true;
    } catch (error) {
        spinner.fail(`系統要求檢查失敗: ${error.message}`);
        return false;
    }
}

// 選擇安裝版本
async function selectVersion() {
    const { version } = await inquirer.prompt([
        {
            type: 'list',
            name: 'version',
            message: '請選擇要安裝的版本:',
            choices: [
                {
                    name: 'Community版 (免費) - 基礎功能',
                    value: 'community',
                    short: 'Community'
                },
                {
                    name: `Personal版 (${PAYMENT_CONFIG.creditsRequired.personal}積分) - 個人增強功能`,
                    value: 'personal',
                    short: 'Personal'
                },
                {
                    name: `Enterprise版 (${PAYMENT_CONFIG.creditsRequired.enterprise}積分) - 完整功能集`,
                    value: 'enterprise',
                    short: 'Enterprise'
                }
            ]
        }
    ]);
    
    return version;
}

// 檢查積分系統
async function checkCreditsSystem(version) {
    const creditsRequired = PAYMENT_CONFIG.creditsRequired[version];
    
    if (creditsRequired === 0) {
        return true; // Community版本不需要積分
    }
    
    const spinner = ora('檢查積分系統...').start();
    
    try {
        // 檢查用戶token
        const tokenPath = path.join(process.env.HOME || process.env.USERPROFILE, '.powerauto_token');
        let userToken;
        
        if (fs.existsSync(tokenPath)) {
            userToken = fs.readFileSync(tokenPath, 'utf8').trim();
            spinner.text = '找到用戶token';
        } else {
            spinner.stop();
            
            log.warning('首次使用需要註冊積分賬戶');
            log.info(`請訪問: ${PAYMENT_CONFIG.webUrl}/register`);
            
            const { token } = await inquirer.prompt([
                {
                    type: 'input',
                    name: 'token',
                    message: '請輸入您的用戶token:',
                    validate: (input) => input.trim().length > 0 || '請輸入有效的token'
                }
            ]);
            
            userToken = token.trim();
            fs.writeFileSync(tokenPath, userToken, { mode: 0o600 });
            
            spinner.start('檢查積分餘額...');
        }
        
        // 檢查積分餘額
        const creditsBalance = await checkCreditsBalance(userToken);
        
        if (creditsBalance < creditsRequired) {
            spinner.fail(`積分不足! 需要: ${creditsRequired}, 當前: ${creditsBalance}`);
            
            log.warning(`請訪問以下網址充值積分: ${PAYMENT_CONFIG.webUrl}/recharge`);
            
            const { recharged } = await inquirer.prompt([
                {
                    type: 'confirm',
                    name: 'recharged',
                    message: '充值完成後繼續?',
                    default: false
                }
            ]);
            
            if (!recharged) {
                return false;
            }
            
            // 重新檢查積分
            const newBalance = await checkCreditsBalance(userToken);
            if (newBalance < creditsRequired) {
                log.error('積分仍然不足，安裝終止');
                return false;
            }
        }
        
        spinner.succeed(`積分檢查通過 (餘額: ${creditsBalance})`);
        
        // 扣除積分
        await deductCredits(userToken, creditsRequired, version);
        
        return true;
    } catch (error) {
        spinner.fail(`積分系統檢查失敗: ${error.message}`);
        return false;
    }
}

// 檢查積分餘額
async function checkCreditsBalance(token) {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: 'api.powerauto.aiweb.com',
            port: 443,
            path: '/v1/credits/balance',
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        };
        
        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => {
                try {
                    const response = JSON.parse(data);
                    resolve(response.balance || 0);
                } catch (error) {
                    resolve(0);
                }
            });
        });
        
        req.on('error', () => resolve(0));
        req.setTimeout(10000, () => resolve(0));
        req.end();
    });
}

// 扣除積分
async function deductCredits(token, amount, version) {
    return new Promise((resolve, reject) => {
        const postData = JSON.stringify({
            amount: amount,
            reason: `PowerAutomation ${version} v${VERSION} installation`
        });
        
        const options = {
            hostname: 'api.powerauto.aiweb.com',
            port: 443,
            path: '/v1/credits/deduct',
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(postData)
            }
        };
        
        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => {
                try {
                    const response = JSON.parse(data);
                    if (response.success) {
                        resolve(true);
                    } else {
                        reject(new Error('積分扣除失敗'));
                    }
                } catch (error) {
                    reject(error);
                }
            });
        });
        
        req.on('error', reject);
        req.setTimeout(10000, () => reject(new Error('請求超時')));
        req.write(postData);
        req.end();
    });
}

// 下載安裝腳本
async function downloadInstallScript(platform) {
    const spinner = ora('下載安裝腳本...').start();
    
    return new Promise((resolve, reject) => {
        const scriptUrl = INSTALL_SCRIPTS[platform];
        const scriptName = `install-script-${platform}-v${VERSION}.${platform === 'win32' ? 'ps1' : 'sh'}`;
        const scriptPath = path.join(process.cwd(), scriptName);
        
        const file = fs.createWriteStream(scriptPath);
        
        https.get(scriptUrl, (response) => {
            if (response.statusCode !== 200) {
                reject(new Error(`下載失敗: HTTP ${response.statusCode}`));
                return;
            }
            
            response.pipe(file);
            
            file.on('finish', () => {
                file.close();
                
                // 設置執行權限 (Unix系統)
                if (platform !== 'win32') {
                    try {
                        execSync(`chmod +x ${scriptPath}`);
                    } catch (error) {
                        // 忽略權限設置錯誤
                    }
                }
                
                spinner.succeed('安裝腳本下載完成');
                resolve(scriptPath);
            });
        }).on('error', (error) => {
            fs.unlink(scriptPath, () => {}); // 清理失敗的文件
            reject(error);
        });
    });
}

// 執行安裝腳本
async function executeInstallScript(scriptPath, version) {
    const spinner = ora('執行安裝腳本...').start();
    
    return new Promise((resolve, reject) => {
        let command, args;
        
        if (PLATFORM === 'win32') {
            command = 'powershell';
            args = ['-ExecutionPolicy', 'Bypass', '-File', scriptPath];
        } else {
            command = 'bash';
            args = [scriptPath];
        }
        
        // 設置環境變量
        const env = {
            ...process.env,
            POWERAUTO_VERSION: version,
            POWERAUTO_SKIP_PROMPTS: 'true'
        };
        
        const child = spawn(command, args, {
            stdio: 'inherit',
            env: env
        });
        
        child.on('close', (code) => {
            if (code === 0) {
                spinner.succeed('安裝腳本執行完成');
                resolve();
            } else {
                spinner.fail(`安裝腳本執行失敗 (退出碼: ${code})`);
                reject(new Error(`安裝失敗，退出碼: ${code}`));
            }
        });
        
        child.on('error', (error) => {
            spinner.fail(`安裝腳本執行錯誤: ${error.message}`);
            reject(error);
        });
    });
}

// 顯示完成信息
function showCompletion(version) {
    console.log(chalk.green(`
╔══════════════════════════════════════════════════════════════════════════╗
║                     🎉 安裝完成！                                        ║
║                                                                          ║
║  ${PRODUCT_NAME} v${VERSION} 已成功安裝                                      ║
║  版本: ${version}                                                         ║
║                                                                          ║
║  🌐 服務地址:                                                             ║
║    • K2服務: http://localhost:8765                                       ║
║    • Mirror服務: http://localhost:8080                                   ║
║    • ClaudeEditor: http://localhost:3000                                ║
║    • 支付系統: http://localhost:3001                                     ║
║                                                                          ║
║  📱 移動端支持:                                                           ║
║    • 響應式設計支持PC/Mobile                                              ║
║    • 觸控優化界面                                                         ║
║    • 離線功能支持                                                         ║
║                                                                          ║
║  💰 積分系統:                                                             ║
║    • 儲值: ${PAYMENT_CONFIG.webUrl}/recharge                          ║
║    • 歷史: ${PAYMENT_CONFIG.webUrl}/history                           ║
║    • 管理: ${PAYMENT_CONFIG.webUrl}/dashboard                         ║
║                                                                          ║
║  🔧 需要幫助?                                                             ║
║    • 文檔: ${PAYMENT_CONFIG.webUrl}/docs                              ║
║    • 支持: ${PAYMENT_CONFIG.webUrl}/support                           ║
║    • GitHub: https://github.com/alexchuang650730/aicore0711              ║
╚══════════════════════════════════════════════════════════════════════════╝
    `));
    
    if (version !== 'community') {
        log.info(`感謝您購買 ${version} 版本！`);
        log.info(`剩餘積分請查看: ${PAYMENT_CONFIG.webUrl}/dashboard`);
    }
}

// 主安裝函數
async function install() {
    try {
        showWelcome();
        
        // 檢查系統要求
        if (!checkSystemRequirements()) {
            process.exit(1);
        }
        
        // 選擇版本
        const version = await selectVersion();
        
        // 檢查積分系統
        if (!await checkCreditsSystem(version)) {
            process.exit(1);
        }
        
        // 確認安裝
        const { confirm } = await inquirer.prompt([
            {
                type: 'confirm',
                name: 'confirm',
                message: `確認安裝 ${PRODUCT_NAME} v${VERSION} (${version} 版本)?`,
                default: true
            }
        ]);
        
        if (!confirm) {
            log.info('安裝已取消');
            process.exit(0);
        }
        
        // 下載安裝腳本
        const scriptPath = await downloadInstallScript(PLATFORM);
        
        // 執行安裝腳本
        await executeInstallScript(scriptPath, version);
        
        // 清理安裝腳本
        try {
            fs.unlinkSync(scriptPath);
        } catch (error) {
            // 忽略清理錯誤
        }
        
        // 顯示完成信息
        showCompletion(version);
        
        // 詢問是否立即啟動
        const { startNow } = await inquirer.prompt([
            {
                type: 'confirm',
                name: 'startNow',
                message: '是否立即啟動 PowerAutomation?',
                default: false
            }
        ]);
        
        if (startNow) {
            log.info('正在啟動 PowerAutomation...');
            // 這裡可以添加啟動邏輯
        }
        
    } catch (error) {
        log.error(`安裝失敗: ${error.message}`);
        process.exit(1);
    }
}

// 命令行界面
program
    .name('powerautomation')
    .description('PowerAutomation v4.6.9.7 一鍵安裝工具')
    .version(VERSION);

program
    .command('install')
    .description('安裝 PowerAutomation')
    .action(install);

program
    .command('info')
    .description('顯示版本和系統信息')
    .action(() => {
        console.log(`${PRODUCT_NAME} v${VERSION}`);
        console.log(`平台: ${PLATFORM} (${ARCH})`);
        console.log(`Node.js: ${process.version}`);
        console.log(`支付系統: ${PAYMENT_CONFIG.webUrl}`);
    });

// 如果沒有參數，顯示幫助
if (process.argv.length === 2) {
    program.help();
} else {
    program.parse();
}

// 導出模組 (用於測試)
module.exports = {
    install,
    checkSystemRequirements,
    selectVersion,
    checkCreditsSystem
};