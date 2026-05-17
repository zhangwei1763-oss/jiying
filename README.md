# 极影AI

Windows 桌面版 AI 视频生成工具，支持视频解析、文案改写、图片生成、素材库、批量任务和卡密验证。

## 运行

```powershell
python main.py
```

## 卡密后台

卡密服务端在 `tools/license_server.py`。

```powershell
python tools\license_server.py create-card TEST-KEY-001 2099-12-31
python tools\license_server.py serve --host 0.0.0.0 --port 8765
```

客户端卡密服务器地址在 `main.py` 的 `DEFAULT_LICENSE_SERVER_URL` 中配置。
