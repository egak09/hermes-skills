# Web3 基础概念手册

> 面向测试网交易、合约调用、钱包确认和链上验证的理解前置。
> 覆盖 11 个核心概念：从账户到区块链浏览器。

---

## 目录

1. [Account（账户）](#1-account账户)
2. [Address（地址）](#2-address地址)
3. [Wallet（钱包）](#3-wallet钱包)
4. [Seed Phrase（助记词）](#4-seed-phrase助记词)
5. [Private Key（私钥）](#5-private-key私钥)
6. [Signature（签名）](#6-signature签名)
7. [Transaction（交易）](#7-transaction交易)
8. [Gas（燃料费）](#8-gas燃料费)
9. [Smart Contract（智能合约）](#9-smart-contract智能合约)
10. [Testnet（测试网）](#10-testnet测试网)
11. [Block Explorer（区块链浏览器）](#11-block-explorer区块链浏览器)
12. [⚠️ 私钥、助记词、签名和授权：为什么需要特别谨慎](#️-私钥助记词签名和授权为什么需要特别谨慎)

---

## 1. Account（账户）

### 一句话解释

区块链上的"用户身份"——控制资金和发起交易的主体，分为 EOA、Smart Account 和 Multisig 三种类型。

### 三种账户类型

| 类型 | 谁控制 | 有私钥？ | 典型用途 |
|------|--------|----------|---------|
| **EOA**（Externally Owned Account） | 私钥持有者 | ✅ 有 | 个人钱包、MetaMask 默认账户 |
| **Smart Account**（合约账户） | 合约代码逻辑 | ❌ 无 | DeFi 金库、DEX 池、NFT 合约 |
| **Multisig**（多签账户） | 多个私钥持有者（M-of-N） | ✅ 有（多个） | DAO 国库、团队共管资金 |

### 具体例子

- **EOA**：你在 MetaMask 创建的钱包，本质就是一个 EOA。`0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1` 这样的地址背后是一把私钥。
- **Smart Account**：Uniswap V3 的流动性池合约地址 `0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8`，它没有私钥，行为由合约代码定义。
- **Multisig**：Safe 钱包（3/5 多签）——5 个人中有 3 人签名才能动钱，常用于 DAO 国库管理。

### ⚠️ 常见误区

> "合约地址和普通地址一样，我也能给它转 ETH"  
> ✅ 可以转 ETH，但**合约不一定能退还**。许多合约没有 `withdraw` 函数，转进去的币永久锁死。

---

## 2. Address（地址）

### 一句话解释

区块链上的"账号号码"——账户的唯一公开标识符，别人给你转账就打到这个地址。

### 具体例子

```
以太坊地址：0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1
Solana 地址：7EcDhSYGxXyscszYEp35KHN8vvw3svAuLKTzXwCFLtV
比特币地址：1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
```

不同链的地址格式不同，但功能相同：**收/发资产的公开标识**。

### ⚠️ 安全提醒

> 地址是**公开的**，可以放心分享。  
> 但分享地址后，任何人都能查到你的链上交易历史（通过区块链浏览器）。

---

## 3. Wallet（钱包）

### 一句话解释

管理私钥和签名的工具——它本身不"存放"你的资产，资产始终在链上。

### 具体例子

| 钱包类型 | 代表产品 | 特点 |
|---------|---------|------|
| 浏览器插件 | MetaMask、Rabby | 与 DApp 交互最方便 |
| 移动端 | Trust Wallet、imToken | 手机扫码签名 |
| 硬件钱包 | Ledger、Trezor | 私钥离线，最安全 |
| 命令行 | cast（Foundry） | 开发者用，脚本化操作 |

### ⚠️ 常见误区

> "我的 ETH 存在 MetaMask 里"  
> ❌ 错误。MetaMask 只是**钥匙**，ETH 始终在链上。就像你的银行卡只是钥匙，钱不在卡里而在银行系统中。

---

## 4. Seed Phrase（助记词）

### 一句话解释

私钥的"人类可读版本"——12 或 24 个英文单词，拥有它 = 拥有钱包的完全控制权。

### 具体例子

```
助记词（示例，勿用于真实钱包）：
abandon ability able about above absent absorb abstract absurd abuse access accident
```

这 12 个单词通过 BIP39 标准可以**推导出所有子私钥和地址**。

### ⚠️ 安全提醒

> **助记词 ≠ 密码**。密码丢了可以重置，助记词丢了 = 永久失去资产。  
> - 绝对不要截图/拍照存储  
> - 绝对不要输入任何网站  
> - 手写在纸上，物理保存  
> - 任何让你"验证助记词"的弹窗都是钓鱼

---

## 5. Private Key（私钥）

### 一句话解释

区块链账户的"终极密码"——一把 64 位十六进制字符串，持有它就能签名任何交易、转移任何资产。

### 具体例子

```
私钥格式：
0x4c0883a69102937d6231471b5dbb6204fe5129617082792ae468d01a3f362318
```

只有你能用这把私钥生成签名，别人无法伪造——这就是"你确实是地址主人"的数学证明。

### ⚠️ 安全提醒

> **私钥泄露 = 资产全丢，且不可逆。**  
> 区块链没有"客服"、没有"冻结账户"、没有"撤销交易"。

---

## 6. Signature（签名）

### 一句话解释

用私钥对一段数据加密生成的"数字指纹"——证明"我同意"而不暴露私钥本身。

### 具体例子

最常见的签名场景：

1. **交易签名**：你要转 1 ETH 给 Alice，钱包用你的私钥对交易数据签名，矿工验证签名后执行
2. **消息签名**：DApp 让你 "Sign a message to log in"，你签名后 DApp 验证地址匹配
3. **授权签名**：在 Uniswap 上"Approve USDC"，你用私钥签名授权合约调用你的 USDC

```javascript
// MetaMask 调用签名
const signature = await ethereum.request({
  method: 'personal_sign',
  params: ['Hello, Web3!', userAddress]
});
// 返回: 0x... (签名字符串，不包含私钥)
```

### ⚠️ 常见误区

> "签名只是登录，又不花钱，随便签"  
> ❌ **危险。** `eth_sign` 类型的签名可以授权任意交易。不要对看不懂的内容签名。

---

## 7. Transaction（交易）

### 一句话解释

区块链上一切状态变更的载体——转账、部署合约、调用合约函数，都通过交易完成。

### 具体例子

一笔典型的 ETH 转账交易：

```
From:  0xAlice...
To:    0xBob...
Value: 0.5 ETH
Gas:   21000 gas × 20 gwei = 0.00042 ETH
Nonce: 15
Data:  (空 — 纯转账无需 data)

→ 签名 → 广播 → 矿工/验证者打包 → 确认
```

### 交易生命周期

```
发起 → 签名 → 广播到 mempool → 矿工打包 → 区块确认 → 最终确定
```

### ⚠️ 安全提醒

> 交易一旦上链就**不可撤销**。  
> 没有"管理员帮你回滚"，没有"7天无条件退款"。转账前务必核对地址和金额。

---

## 8. Gas（燃料费）

### 一句话解释

执行交易或合约所需的计算资源费用——类似汽车的"油费"，由网络供需决定价格。

### 具体例子

```
Gas 费 = Gas Limit × Gas Price

- Gas Limit: 操作复杂度上限
  - 纯 ETH 转账: 21,000
  - ERC20 转账: ~65,000
  - Uniswap swap: ~150,000-300,000
  - 复杂合约部署: 数百万

- Gas Price: 每单位 Gas 的价格（以 gwei 计）
  - 1 gwei = 0.000000001 ETH
  - 网络拥堵时可能飙升到 100+ gwei

计算示例：
  Uniswap swap: 200,000 gas × 50 gwei = 0.01 ETH（约 $25）
```

### ⚠️ 常见误区

> "Gas Limit 设得越大交易越快"  
> ❌ 交易速度由 **Gas Price** 决定，不是 Gas Limit。  
> Gas Limit 太小 → 交易失败（且不退 Gas）。  
> Gas Limit 太大 → 用不完的会退还，但先预扣的保证金可能很高。

---

## 9. Smart Contract（智能合约）

### 一句话解释

运行在区块链上的自动化程序——一旦部署，代码公开且不可篡改，触发条件后自动执行。

### 具体例子

一个最简单的 ERC20 代币合约：

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract MyToken {
    mapping(address => uint256) public balanceOf;
    
    function transfer(address to, uint256 amount) external {
        require(balanceOf[msg.sender] >= amount, "Insufficient");
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
    }
}
```

部署后，任何人都能调用 `transfer()` 转账，逻辑锁死在链上，无法修改。

### ⚠️ 安全提醒

> 开源 ≠ 安全。任何人都能看合约代码，但看懂不等于没漏洞。  
> 常见风险：重入攻击（Reentrancy）、闪电贷攻击、逻辑漏洞、后门。

---

## 10. Testnet（测试网）

### 一句话解释

区块链的"沙盒环境"——和主网功能完全相同，但代币免费、零价值，用来测试代码而不冒真金白银的风险。

### 具体例子

| 测试网 | 链 | 水龙头（领测试币） |
|--------|-----|-------------------|
| Sepolia | Ethereum | sepoliafaucet.com |
| Goerli | Ethereum | ⚠️ 已弃用 |
| Mumbai | Polygon | faucet.polygon.technology |
| Fuji | Avalanche | faucet.avax.network |
| BSC Testnet | BNB Chain | testnet.bnbchain.org/faucet |

### 典型测试流程

```
领测试 ETH（水龙头）→ 部署合约到 Sepolia → 调用合约 → 
检查浏览器 → 确认无误 → 部署到主网
```

### ⚠️ 常见误区

> "测试网测过了，主网肯定没问题"  
> ⚠️ 测试网**不能模拟**：主网的高并发、MEV 攻击、高昂 Gas 费、任意合约交互的未知风险。测试通过只是第一步。

---

## 11. Block Explorer（区块链浏览器）

### 一句话解释

区块链的"搜索引擎"——输入地址、交易哈希或区块号，就能查看链上一切公开数据。

### 具体例子

| 浏览器 | 链 | 网址 |
|--------|-----|------|
| Etherscan | Ethereum | etherscan.io |
| Solscan | Solana | solscan.io |
| Polygonscan | Polygon | polygonscan.com |
| BscScan | BNB Chain | bscscan.com |

### 你能查到什么

```
地址页：余额、所有交易历史、持有的代币/NFT
交易页：From/To/Value/Gas/状态（Success/Fail）
合约页：源码（已认证的）、ABI、Read/Write Contract
```

### ⚠️ 安全提醒

> 如果有人说"官方客服帮你恢复资产"，马上去浏览器查你的地址——  
> **如果币已经被转走，那就是被转走了**，不存在"锁定""冻结""追回"，100% 是骗子。

---

## ⚠️ 私钥、助记词、签名和授权：为什么需要特别谨慎

这四项是 Web3 安全的核心，理解它们之间的关系可以避免 90% 的安全事故。

### 权限层级

```
助记词（最高）
  └─ 可推导出 → 所有私钥（主私钥 + 子私钥）
      └─ 可生成 → 签名（不暴露私钥本身）
          └─ 可执行 → 交易（转账）/ 授权（Approve）→ 资产转移
```

### 四者的安全性对比

| | 泄露后果 | 可撤销？ | 防护方式 |
|------|---------|---------|---------|
| **助记词** | 所有地址所有资产永久丢失 | ❌ 不可逆 | 物理保管，永不联网 |
| **私钥** | 该地址所有资产永久丢失 | ❌ 不可逆 | 硬件钱包 / 加密文件 |
| **签名** | 单次操作授权 | ⚠️ 取决于签名内容 | 看懂再签，不签盲签 |
| **Approve 授权** | 授权额度内的代币可被转走 | ✅ **可以 revoke** | 只授权所需额度，用完撤销 |

### 为什么签名和授权比你想的更危险

**签名**：不是"只是登录"。

```javascript
// 这是登录签名 — 相对安全
personal_sign("Login to DApp")

// 这是致命签名 — 可以授权转移你所有资产
eth_sign(hash)  // 对任意哈希签名 = 给攻击者空白支票
```

**授权（Approve）**：DeFi 最被忽视的风险。

- 你在 Uniswap 上"Approve USDC"时，通常授权了 **无限额度**
- 即使你只用了一次，合约仍有权限从你地址转走 USDC
- 如果那个合约后来被发现漏洞，你的 USDC 在劫难逃

### 实操守则

1. 🔐 助记词：手写纸上 + 防火保险箱 + 分片存储（3-2-1 备份策略）
2. 🔑 私钥：硬件钱包（Ledger/Trezor）> 加密文件 > 明文文件 >>>>>> 截图
3. ✍️ 签名：看懂内容再签，对于 `eth_sign` 类型的签名直接拒绝
4. 🛡️ 授权：用 [revoke.cash](https://revoke.cash) 定期清理不用的授权，只批准所需额度而不是 "无限"

---

> ⚠️ 本文档所有示例私钥和助记词均为演示用，不承载任何真实资产。
> 永远不要共享你的私钥、助记词或 API 私密信息。
