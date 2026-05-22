# Python 环境与代理

---

## 1. 双 Python 问题

Windows + Git Bash (MSYS2) 的经典坑：存在两个 Python。

```bash
# MSYS2 ucrt64 Python（git-bash 默认）
$ which python3
/c/msys64/ucrt64/bin/python3
# 没有 pip 安装的包

# 系统 CPython（我们需要的）
$ /c/Users/dairch/AppData/Local/Programs/Python/Python314/python.exe
# 有 ccxt, numpy, pandas, requests, skyfield...
```

### 解决方案：永远用完整路径

```bash
# 正确
/c/Users/dairch/AppData/Local/Programs/Python/Python314/python.exe -B script.py

# 错误
python3 script.py  # → ModuleNotFoundError
```

`-B` flag 跳过 `.pyc` 缓存，确保代码修改后立即生效。

### Pip 也用系统 Python

```bash
/c/Users/dairch/AppData/Local/Programs/Python/Python314/python.exe -m pip install <package>
```

---

## 2. 代理传透

### 问题

Windows 上 `HTTP_PROXY` / `HTTPS_PROXY` 环境变量不一定被 Python libraries 自动使用。`curl -x` 能用不等于 Python `requests` 能用。

### 解决方案：显式传 proxies

```python
import requests

# 错误 — 依赖环境变量（可能不生效）
resp = requests.get('https://api.binance.com')

# 正确 — 显式传入
proxies = {
    'http': 'http://127.0.0.1:1081',
    'https': 'http://127.0.0.1:1081',
}
resp = requests.get('https://api.binance.com', proxies=proxies)
```

### CCXT 的代理配置

```python
import ccxt

exchange = ccxt.binance({
    'apiKey': '...',
    'secret': '...',
    'proxies': {
        'http': 'http://127.0.0.1:1081',
        'https': 'http://127.0.0.1:1081',
    },
})
```

### 从配置读代理（不硬编码）

```python
import json

with open('config.json') as f:
    config = json.load(f)

proxies = config['proxy']  # {'http': '...', 'https': '...'}
```

---

## 3. 代理出口 IP

```bash
# 查代理出口 IP（用于 API 白名单）
curl -x http://127.0.0.1:1081 -s https://api.ipify.org
# 或
curl -x http://127.0.0.1:1081 -s https://icanhazip.com
```

**我的代理出口 IP**: `172.235.214.193`（已在 Binance 白名单）

> ipinfo.io 和 ifconfig.me 在 GFW 下可能超时，用 api.ipify.org 更可靠。

---

## 4. 依赖管理清单

| 用途 | 依赖 |
|------|------|
| 交易 | ccxt · numpy · pandas · ta |
| 数据 | requests |
| 玄学 | skyfield（可选，无则用近似算法） |
| 消息 | aiohttp-socks |

---

## 5. execute_code vs terminal

Hermes 的 `execute_code` 在沙箱中运行，有自己的 Python 环境：

| | terminal() | execute_code |
|-|-----------|-------------|
| Python | git-bash 默认（MSYS2） | 沙箱环境 |
| 安装包 | 需手动 pip install | 内置 |
| 网络 | 需要代理 | 沙箱内直连 |

---

### 回到总览

→ [README.md](README.md)
