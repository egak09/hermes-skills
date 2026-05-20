# 代理配置诊断记录

> 2026-05-20 · Paradigme 环境

## 代理信息

- **类型**: HTTP (非 SOCKS5)
- **地址**: `127.0.0.1:1081`
- **出口 IP**: `172.235.214.193`（3 个独立 IP 检测服务交叉验证）

## 发现过程

1. 初始用 `curl -s https://api.ipify.org`（无代理）得到 `111.44.232.56` → **这是直连 IP，非代理出口 IP**
2. 用 `curl -x http://127.0.0.1:1081` 通过代理测试三个 IP 检测服务：
   - `api.ipify.org` → `172.235.214.193`
   - `icanhazip.com` → `172.235.214.193`
   - `myip.biturl.top` → `172.235.214.193`
3. Binance 公开 API 通过代理正常响应（BTC/ETH 价格可拉）
4. 私密 API 返回 `-2015 Invalid API-key, IP, or permissions` → IP 白名单不匹配

## CCXT 代理配置

⚠️ CCXT **不会**自动使用 `HTTP_PROXY`/`HTTPS_PROXY` 环境变量。必须在 exchange 构造函数中显式传入 `proxies`：

```python
exchange = ccxt.binance({
    'apiKey': '...',
    'secret': '...',
    'proxies': {
        'http': 'http://127.0.0.1:1081',
        'https': 'http://127.0.0.1:1081',
    },
    'timeout': 15000,  # 15s，代理下建议加长
})
```

## IP 检测命令（备忘）

```bash
# 通过代理检测出口 IP
curl -x http://127.0.0.1:1081 -s --max-time 5 https://api.ipify.org
curl -x http://127.0.0.1:1081 -s --max-time 5 https://icanhazip.com

# 直连 IP
curl -s --max-time 5 https://api.ipify.org
```
