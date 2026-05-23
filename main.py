import base64
import csv
import ctypes
import hashlib
import http.client
import json
import mimetypes
import os
import platform
import queue
import re
import shutil
import site
import socket
import subprocess
import sys
import traceback
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, X, Y, Button, Canvas, Entry, Frame, Label, LabelFrame, Listbox, Toplevel
from tkinter import Menu, PhotoImage, StringVar, Text, Tk, filedialog, messagebox, ttk


if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
else:
    APP_DIR = Path(__file__).resolve().parent
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
DATA_DIR = APP_DIR / "data"
MATERIAL_DIR = APP_DIR / "materials"
OUTPUT_DIR = APP_DIR / "outputs"
THUMB_DIR = DATA_DIR / "thumbs"
GENERATED_IMAGE_DIR = OUTPUT_DIR / "generated_images"
SETTINGS_FILE = DATA_DIR / "settings.json"
LICENSE_FILE = DATA_DIR / "license.json"
IMAGE_PROMPT_TEMPLATES_FILE = DATA_DIR / "image_prompt_templates.json"
REWRITE_PROMPT_TEMPLATES_FILE = DATA_DIR / "rewrite_prompt_templates.json"
REWRITE_HISTORY_FILE = DATA_DIR / "rewrite_history.json"
MATERIALS_FILE = DATA_DIR / "materials.json"
TASKS_FILE = DATA_DIR / "tasks.json"
PARSED_VIDEOS_FILE = DATA_DIR / "parsed_videos.json"
IMAGE_TASKS_FILE = DATA_DIR / "image_tasks.json"
GROUPS_FILE = DATA_DIR / "material_groups.json"
AGENT_CONVERSATIONS_FILE = DATA_DIR / "agent_conversations.json"
API_BASE = "https://api.x.ai/v1"
MODEL_NAME = "grok-imagine-video"
TEXT_MODEL_NAME = "gpt-5.5"
IMAGE_MODEL_NAME = "gpt-image-2"
AUDIO_MODEL_NAME = "gpt-4o-transcribe"
LOCAL_WHISPER_MODEL_NAME = "small"
IMAGE_SUBMIT_TIMEOUT = 90
IMAGE_POLL_TIMEOUT = 180
IMAGE_POLL_INTERVAL = 60
DEFAULT_IMAGE_POLL_PATH = "/images/jobs/{id}"
DEFAULT_PARSER_ENDPOINT = "https://jxs.72ke.vip/DXTQMCIO"
DEFAULT_PARSER_KEY = "54ddc3b065e8f015add36f100ee775b8"
DEFAULT_PARSER_SIGN = "L5-YK9BCDD14F758D37F6881B24F3013FED3D"
MAX_REFERENCE_IMAGES = 7
APP_NAME = "极影AI"
APP_VERSION = "1.0"
DEFAULT_LICENSE_SERVER_URL = "http://64.83.47.98:8765"
APP_ICON_FILE = RESOURCE_DIR / "assets" / "app_icon.ico"
COLOR_BG = "#070b12"
COLOR_NAV = "#0b1220"
COLOR_PANEL = "#101827"
COLOR_PANEL_2 = "#151f31"
COLOR_CARD = "#182234"
COLOR_BORDER = "#2a3446"
COLOR_TEXT = "#e8edf5"
COLOR_MUTED = "#9aa7ba"
COLOR_ACCENT = "#38bdf8"
COLOR_ACCENT_DARK = "#075985"
COLOR_SUCCESS = "#22c55e"
COLOR_INPUT = "#0c1422"
FONT_BODY = ("Microsoft YaHei UI", 10)
FONT_SMALL = ("Microsoft YaHei UI", 9)
FONT_TITLE = ("Microsoft YaHei UI", 16, "bold")
FONT_SECTION = ("Microsoft YaHei UI", 11, "bold")
STATUS_LABELS = {
    "queued": "待提交",
    "submitting": "提交中",
    "submitted": "已提交",
    "processing": "生成中",
    "done": "已完成",
    "failed": "失败",
    "paused": "已暂停",
    "ended": "已结束",
}
LOCAL_WHISPER_CACHE = {}
DEFAULT_MATERIAL_GROUPS = ["产品", "人物", "场景", "视频封面", "AI生成", "其他"]
REWRITE_PROMPT_TEMPLATE = """现在我给你一段同行爆款带货对标文案，请严格按照我的专属视频规则深度改写、原创洗稿、定制分镜，适配 Grok 写实真人视频生成。

一、文案改写规则
1. 百分百保留原视频核心钩子、痛点、产品卖点、成交逻辑、爆款节奏，流量结构完全不变。
2. 全深度原创改写，换语序、换话术、换句式、规避平台查重，纯口语短句，适配抖音、快手中老年下沉市场。
3. 文案语速适配3/6/8/10 秒单镜头，短句拆分均匀，无超长台词，适配分段生成拼接。

二、专属分镜硬性规则（最重要、必须严格执行）
4. 所有分镜单镜头时长：3 秒 / 6 秒 / 8 秒 / 10 秒四选一，禁止低于3秒、禁止高于10秒。
5. 严格适配我的工作流：单段生成 10 秒成片，多段镜头无缝拼接成 30 秒完整视频。
6. 分镜逻辑连贯、人设统一、场景衔接自然，每一段 10 秒独立成片、又能组合成完整视频。
7. 标注清楚：每一段镜头【时长 + 画面内容 + 运镜 + 对口播台词】，分段清晰，方便我分 2-3 次生成视频、后期拼接。
8. 全程适配 Grok 模型：写实真人、无崩脸、无跳帧、时序连贯、生活化自然动作。

三、最终输出格式
1、原创改写成品口播文案（适配 30 秒完整视频）
2、分段式精准分镜表（每段仅限3/6/8/10秒，不低于3秒、不超10秒，可独立生成、可拼接）
3、适配 Grok 直接出片的单段画面提示词

原视频文案：
{source}
"""

DEFAULT_IMAGE_PROMPT_TEMPLATES = [
    {
        "name": "默认图片提示词",
        "template": "{prompt}",
    }
]
DEFAULT_REWRITE_PROMPT_TEMPLATES = [
    {
        "name": "Grok分镜改写",
        "template": REWRITE_PROMPT_TEMPLATE,
    }
]
IMAGE_QUALITY_OPTIONS = ("auto", "high", "medium", "low")
IMAGE_QUALITY_LABELS = {
    "auto": "自动",
    "high": "高",
    "medium": "中",
    "low": "低",
}
IMAGE_ASPECT_PRESETS = [
    ("1:1", "2048", "2048"),
    ("3:2", "2048", "1365"),
    ("2:3", "1365", "2048"),
    ("4:3", "2048", "1536"),
    ("3:4", "1536", "2048"),
    ("9:16", "1088", "1920"),
    ("1:1(2k)", "2048", "2048"),
    ("16:9(2k)", "1920", "1088"),
    ("9:16(2k)", "1088", "1920"),
    ("16:9(4k)", "3840", "2160"),
    ("9:16(4k)", "2160", "3840"),
    ("auto", "2048", "2048"),
]


def ensure_dirs():
    DATA_DIR.mkdir(exist_ok=True)
    MATERIAL_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    GENERATED_IMAGE_DIR.mkdir(exist_ok=True)
    THUMB_DIR.mkdir(exist_ok=True)


def add_nvidia_dll_directories():
    if os.name != "nt":
        return
    candidates = []
    bundled_cuda = APP_DIR / "cuda_runtime"
    candidates.extend((
        bundled_cuda,
        bundled_cuda / "cublas" / "bin",
        bundled_cuda / "cudnn" / "bin",
        bundled_cuda / "cuda_nvrtc" / "bin",
        bundled_cuda / "cuda_runtime" / "bin",
    ))
    for root in site.getsitepackages():
        base = Path(root) / "nvidia"
        candidates.extend((
            base / "cublas" / "bin",
            base / "cudnn" / "bin",
            base / "cuda_nvrtc" / "bin",
            base / "cuda_runtime" / "bin",
        ))
    for path in candidates:
        if path.exists():
            os.environ["PATH"] = str(path) + os.pathsep + os.environ.get("PATH", "")
            try:
                os.add_dll_directory(str(path))
            except (AttributeError, OSError):
                pass
    for dll_name in ("cublas64_12.dll", "cublasLt64_12.dll", "cudart64_12.dll", "cudnn64_9.dll", "nvrtc64_120_0.dll"):
        for path in candidates:
            dll_path = path / dll_name
            if dll_path.exists():
                try:
                    ctypes.CDLL(str(dll_path))
                except OSError:
                    pass
                break


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_name(value):
    value = re.sub(r"[\\/:*?\"<>|]+", "_", value.strip())
    value = re.sub(r"\s+", "_", value)
    return value[:80] or "video"


def safe_alias(value, fallback="image"):
    value = re.sub(r"\.[A-Za-z0-9]{2,5}$", "", str(value).strip())
    value = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    if not value or len(value) > 40:
        value = fallback
    return value


def normalize_base_url(value):
    value = (value or API_BASE).strip().rstrip("/")
    if not value:
        return API_BASE
    if not value.startswith(("http://", "https://")):
        if value.lower().startswith(("www.wuxianai.top", "wuxianai.top")):
            value = "http://" + value
        else:
            value = "https://" + value
    if not value.endswith("/v1"):
        value = value + "/v1"
    return value


def read_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


JSON_LOCKS = {}
JSON_LOCKS_GUARD = threading.Lock()


def json_lock_for(path):
    key = str(Path(path).resolve())
    with JSON_LOCKS_GUARD:
        lock = JSON_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            JSON_LOCKS[key] = lock
        return lock


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex[:8]}.tmp")
    lock = json_lock_for(path)
    with lock:
        try:
            tmp.write_text(payload, encoding="utf-8")
            tmp.replace(path)
        finally:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass


def repair_prompt_templates(items, defaults):
    if not isinstance(items, list):
        items = []
    templates = []
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        name = text_value(item.get("name")).strip()
        template = text_value(item.get("template")).strip()
        if not name or not template or name in seen:
            continue
        templates.append({"name": name, "template": template})
        seen.add(name)
    for item in defaults:
        name = item["name"]
        if name not in seen:
            templates.append({"name": name, "template": item["template"]})
            seen.add(name)
    return templates


def apply_prompt_template(template, key, content):
    template = text_value(template).strip()
    content = text_value(content).strip()
    placeholder = "{" + key + "}"
    if not template:
        return content
    if placeholder in template:
        return template.replace(placeholder, content)
    return f"{template}\n\n{content}".strip()


def unique_alias(base, existing_aliases, fallback="image"):
    alias = safe_alias(base, fallback)
    existing = {text_value(item).lower() for item in existing_aliases}
    if alias.lower() not in existing:
        return alias
    root = alias
    index = 2
    while True:
        candidate = safe_alias(f"{root}_{index}", f"{fallback}_{index}")
        if candidate.lower() not in existing:
            return candidate
        index += 1


def machine_fingerprint():
    machine_guid = ""
    if os.name == "nt":
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as key:
                machine_guid = winreg.QueryValueEx(key, "MachineGuid")[0]
        except Exception:
            machine_guid = ""
    parts = [
        machine_guid,
        platform.node(),
        platform.system(),
        platform.machine(),
        str(uuid.getnode()),
        os.environ.get("COMPUTERNAME", ""),
    ]
    raw = "|".join(part.strip().lower() for part in parts if part)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def machine_display_name():
    name = platform.node() or os.environ.get("COMPUTERNAME") or "unknown"
    system = f"{platform.system()} {platform.release()}".strip()
    return f"{name} ({system})"


def post_json(url, payload, timeout=20):
    body = json.dumps(payload or {}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            text = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(text)
            message = data.get("message") or data.get("error") or text
        except json.JSONDecodeError:
            message = text or str(exc)
        raise RuntimeError(message) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"无法连接卡密服务器：{exc.reason}") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"卡密服务器返回了无效 JSON：{text[:200]}") from exc


def data_uri_for_file(path):
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        mime = "image/jpeg"
    raw = Path(path).read_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def is_image_file(path):
    mime, _ = mimetypes.guess_type(path)
    return bool(mime and mime.startswith("image/"))


def read_text_attachment(path, max_chars=12000):
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in {".txt", ".md", ".csv", ".json", ".xml", ".html", ".htm", ".srt", ".py", ".js", ".ts", ".css", ".log"}:
        return ""
    for encoding in ("utf-8", "utf-8-sig", "gbk", "latin-1"):
        try:
            text = path.read_text(encoding=encoding, errors="replace")
            break
        except OSError:
            return ""
    text = text.strip()
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[文件内容过长，已截断]"
    return text


def video_size_for_aspect(aspect_ratio):
    return {
        "16:9": "1280x720",
        "9:16": "720x1280",
        "1:1": "1024x1024",
        "4:7": "1024x1792",
        "7:4": "1792x1024",
        "4:3": "1280x720",
        "3:4": "720x1280",
        "3:2": "1280x720",
        "2:3": "720x1280",
    }.get(str(aspect_ratio).strip(), "1280x720")


def supported_video_seconds(duration):
    allowed = [6, 10, 12, 16, 20]
    try:
        value = int(duration)
    except (TypeError, ValueError):
        value = 6
    return next((item for item in allowed if item >= value), allowed[-1])


def ps_single_quote(value):
    return str(value).replace("'", "''")


def thumbnail_path_for(material):
    return THUMB_DIR / f"{material.id}.png"


def repair_material(item):
    if not isinstance(item, dict):
        item = {}
    refs = item.get("references") or []
    if not isinstance(refs, list):
        refs = []
    item = {key: item.get(key) for key in ("id", "alias", "path", "added_at", "tags", "prompt", "references") if key in item}
    item.setdefault("id", uuid.uuid4().hex[:12])
    item.setdefault("alias", "image")
    item.setdefault("path", "")
    item.setdefault("added_at", now_text())
    item.setdefault("tags", "")
    item.setdefault("prompt", "")
    item["references"] = [text_value(ref) for ref in refs]
    material = Material(**item)
    material.alias = safe_alias(material.alias, f"image_{material.id[:6]}")
    path = Path(material.path)
    if path.exists():
        return material

    candidates = []
    if path.name:
        candidates.append(MATERIAL_DIR / path.name)
    candidates.extend(MATERIAL_DIR.glob(f"{material.id}_*"))
    candidates.extend(MATERIAL_DIR.glob(f"*{material.id}*"))
    for candidate in candidates:
        if candidate.exists():
            material.path = str(candidate)
            return material
    return material


def repair_groups(items):
    groups = []
    if isinstance(items, list):
        for item in items:
            name = text_value(item).strip()
            if name and name not in groups:
                groups.append(name)
    for name in DEFAULT_MATERIAL_GROUPS:
        if name not in groups:
            groups.append(name)
    return groups


def text_value(value, default=""):
    if value is None:
        return default
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except TypeError:
        return str(value)


def compact_text(value, limit=120):
    value = re.sub(r"\s+", " ", text_value(value)).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def extract_first_url(value):
    match = re.search(r"https?://[^\s，。！？、；；,]+", text_value(value))
    if not match:
        return ""
    return match.group(0).rstrip("。？！.,，；;")


def mask_secret(value):
    value = text_value(value).strip()
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def parser_settings(settings):
    return {
        "endpoint": text_value(settings.get("parser_endpoint"), DEFAULT_PARSER_ENDPOINT),
        "key": text_value(settings.get("parser_key"), DEFAULT_PARSER_KEY),
        "sign": text_value(settings.get("parser_sign"), DEFAULT_PARSER_SIGN),
    }


def task_error_text(task):
    error = text_value(task.error).strip()
    if error:
        return error
    if task.status == "failed":
        return "任务失败，但接口没有返回具体错误信息。"
    return ""


def task_error_hint(error_text):
    lower = error_text.lower()
    if not error_text:
        return ""
    if "timed out" in lower or "timeout" in lower or "请求超时" in error_text:
        return "网络请求超时：本机到接口服务长时间无响应。建议检查网络/API 地址，降低并发，稍后重试。"
    if "remote end closed" in lower or "closed connection" in lower or "connection reset" in lower:
        return "连接被服务端或代理中断：通常是接口服务不稳定、代理断连或网络波动。建议降低并发后重试。"
    if "video_generation_failed" in lower or "no final video url" in lower:
        return "服务端生成失败：接口已接收任务，但最终没有产出视频链接。常见原因是参考图/提示词不适合、生成服务拥堵或服务端内部失败。建议减少参考图、缩短提示词、换一版描述后重试。"
    if "http 400" in lower:
        return "请求参数错误：检查提示词、比例、时长、参考图数量和图片格式。"
    if "http 401" in lower or "http 403" in lower:
        return "认证失败：检查 API Key 是否正确、是否过期、是否有权限。"
    if "http 429" in lower:
        return "请求过多或额度限制：降低并发、拉长轮询间隔，稍后再试。"
    if "http 5" in lower:
        return "接口服务端错误：不是本地参数问题，建议稍后重试或更换 API 地址。"
    if "用户已结束任务" in error_text:
        return "任务被用户手动结束，本地不会继续提交或轮询。"
    return "未识别的错误：请查看完整错误信息，优先检查 API 地址、Key、网络、提示词和参考图。"


def task_error_summary(task):
    error_text = task_error_text(task)
    if not error_text:
        return ""
    hint = task_error_hint(error_text)
    return compact_text(hint or error_text, 120)


def task_error_detail(task):
    error_text = task_error_text(task)
    hint = task_error_hint(error_text)
    parts = [
        f"任务ID：{task.id}",
        f"状态：{STATUS_LABELS.get(task.status, task.status)}",
        f"Request ID：{task.request_id or '无'}",
        f"参数：{task.aspect_ratio} / {task.duration}s / {task.resolution}",
        f"参考图数量：{len(task.references)}",
        "",
        "问题判断：",
        hint or "暂无明确判断。",
        "",
        "原始错误：",
        error_text or "无",
    ]
    return "\n".join(parts)


def repair_task(item):
    if not isinstance(item, dict):
        item = {}
    refs = item.get("references") or []
    if not isinstance(refs, list):
        refs = []
    try:
        duration = int(item.get("duration") or 6)
    except (TypeError, ValueError):
        duration = 6
    return Task(
        id=text_value(item.get("id"), uuid.uuid4().hex[:12]),
        prompt=text_value(item.get("prompt")),
        aspect_ratio=text_value(item.get("aspect_ratio"), "16:9"),
        duration=duration,
        resolution=text_value(item.get("resolution"), "720p"),
        references=[text_value(ref) for ref in refs],
        status=text_value(item.get("status"), "queued"),
        request_id=text_value(item.get("request_id")),
        output_path=text_value(item.get("output_path")),
        error=text_value(item.get("error")),
        created_at=text_value(item.get("created_at"), now_text()),
        updated_at=text_value(item.get("updated_at"), now_text()),
    )


def create_thumbnail(material, size=96):
    source = Path(material.path)
    target = thumbnail_path_for(material)
    if not source.exists():
        return ""
    if target.exists() and target.stat().st_mtime >= source.stat().st_mtime:
        return str(target)

    script = f"""
Add-Type -AssemblyName System.Drawing
$src = '{ps_single_quote(source)}'
$dst = '{ps_single_quote(target)}'
$size = {int(size)}
$img = [System.Drawing.Image]::FromFile($src)
try {{
  $ratio = [Math]::Min($size / $img.Width, $size / $img.Height)
  $w = [Math]::Max(1, [int]($img.Width * $ratio))
  $h = [Math]::Max(1, [int]($img.Height * $ratio))
  $bmp = New-Object System.Drawing.Bitmap $size, $size
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  try {{
    $g.Clear([System.Drawing.Color]::FromArgb(245, 245, 245))
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $x = [int](($size - $w) / 2)
    $y = [int](($size - $h) / 2)
    $g.DrawImage($img, $x, $y, $w, $h)
    $bmp.Save($dst, [System.Drawing.Imaging.ImageFormat]::Png)
  }} finally {{
    $g.Dispose()
    $bmp.Dispose()
  }}
}} finally {{
    $img.Dispose()
}}
"""
    try:
        run_kwargs = {
            "check": True,
            "capture_output": True,
            "timeout": 20,
        }
        if os.name == "nt":
            run_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            **run_kwargs,
        )
        return str(target) if target.exists() else ""
    except (subprocess.SubprocessError, OSError):
        return ""


def http_json(method, url, api_key, payload=None, timeout=180, retries=0):
    body = None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "GrokVideoStudio/1.0",
        "Connection": "close",
    }
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                text = resp.read().decode("utf-8")
                return json.loads(text) if text else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            if attempt < retries:
                time.sleep(1.2 * (attempt + 1))
                continue
            raise RuntimeError(str(exc.reason)) from exc
        except http.client.RemoteDisconnected as exc:
            if attempt < retries:
                time.sleep(1.2 * (attempt + 1))
                continue
            raise RuntimeError("接口服务器主动断开连接，可能是模型服务繁忙、请求内容过长或当前模型不支持该请求。") from exc
        except (ConnectionResetError, ConnectionAbortedError, TimeoutError, socket.timeout) as exc:
            if attempt < retries:
                time.sleep(1.2 * (attempt + 1))
                continue
            if isinstance(exc, (TimeoutError, socket.timeout)):
                raise RuntimeError(f"请求超时：{timeout} 秒内接口没有响应") from exc
            raise RuntimeError(f"接口连接被中断：{exc}") from exc
    raise RuntimeError("接口请求失败")


def friendly_image_error(error):
    message = text_value(error)
    if "HTTP 502" in message and "Upstream request failed" in message:
        return "图片生成失败：上游模型服务异常或临时繁忙（HTTP 502 Upstream request failed），请稍后重试；如果连续失败，请检查图片模型是否可用或更换模型。"
    if "HTTP 502" in message:
        return "图片生成失败：接口上游服务返回 502，通常是模型服务临时不可用，请稍后重试。"
    return f"图片生成失败：{message}"


def test_models_endpoint(base_url, api_key):
    if not api_key:
        raise RuntimeError("缺少 API Key")
    base_url = (base_url or "https://api.openai.com/v1").strip().rstrip("/")
    result = http_json("GET", f"{base_url}/models", api_key, timeout=30)
    if not isinstance(result, dict):
        raise RuntimeError("接口返回格式异常")
    return True


def append_image_generation_log(message):
    try:
        with open(APP_DIR / "image_generation_trace.log", "a", encoding="utf-8") as file:
            file.write(f"[{now_text()}] {message}\n")
    except OSError:
        pass


def append_transcribe_log(message):
    try:
        with open(APP_DIR / "transcribe_error.log", "a", encoding="utf-8") as file:
            file.write(f"[{now_text()}] {message}\n")
    except OSError:
        pass


def compact_log_data(value):
    if isinstance(value, dict):
        compact = {}
        for key, item in value.items():
            if key == "b64_json" and isinstance(item, str):
                compact[key] = f"<base64 {len(item)} chars>"
            else:
                compact[key] = compact_log_data(item)
        return compact
    if isinstance(value, list):
        return [compact_log_data(item) for item in value]
    if isinstance(value, str) and len(value) > 500:
        return value[:500] + f"... <{len(value)} chars>"
    return value


def download_file(url, api_key, destination):
    destination = Path(destination)
    part = destination.with_suffix(destination.suffix + ".part")
    expected_total = None
    last_error = None

    for attempt in range(1, 7):
        existing = part.stat().st_size if part.exists() else 0
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        if existing:
            headers["Range"] = f"bytes={existing}-"

        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                status = getattr(resp, "status", 200)
                if existing and status != 206:
                    existing = 0
                    part.unlink(missing_ok=True)

                total_header = resp.headers.get("Content-Range") or resp.headers.get("Content-Length")
                if total_header:
                    match = re.search(r"/(\d+)$", total_header)
                    if match:
                        expected_total = int(match.group(1))
                    elif not existing:
                        expected_total = int(total_header)

                mode = "ab" if existing else "wb"
                with open(part, mode) as file:
                    shutil.copyfileobj(resp, file)

            if expected_total is None:
                part.replace(destination)
                return
            if part.stat().st_size >= expected_total:
                part.replace(destination)
                return
            last_error = RuntimeError(
                f"下载不完整：{part.stat().st_size}/{expected_total} bytes"
            )
            time.sleep(min(10, attempt * 2))
        except Exception as exc:
            last_error = exc
            time.sleep(min(10, attempt * 2))

    raise RuntimeError(f"视频下载失败：{last_error}")


def multipart_form_data(fields, files):
    boundary = f"----GrokVideoStudio{uuid.uuid4().hex}"
    chunks = []
    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        chunks.append(str(value).encode("utf-8"))
        chunks.append(b"\r\n")
    if isinstance(files, dict):
        file_items = list(files.items())
    else:
        file_items = list(files)
    for item in file_items:
        if len(item) == 2:
            name, path = item
            filename = Path(path).name
        else:
            name, path, filename = item[:3]
        path = Path(path)
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode("utf-8")
        )
        chunks.append(f"Content-Type: {mime}\r\n\r\n".encode("utf-8"))
        chunks.append(path.read_bytes())
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return boundary, b"".join(chunks)


def http_multipart_json(url, api_key, fields, files, timeout=180, retries=0):
    boundary, body = multipart_form_data(fields, files)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Accept": "application/json",
        "User-Agent": "GrokVideoStudio/1.0",
        "Connection": "close",
    }
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                text = resp.read().decode("utf-8", errors="replace")
                return json.loads(text) if text else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            if attempt < retries:
                time.sleep(1.2 * (attempt + 1))
                continue
            raise RuntimeError(str(exc.reason)) from exc
        except http.client.RemoteDisconnected as exc:
            if attempt < retries:
                time.sleep(1.2 * (attempt + 1))
                continue
            raise RuntimeError("接口服务器主动断开连接，可能是模型服务繁忙或当前模型不支持该请求。") from exc
        except (ConnectionResetError, ConnectionAbortedError, TimeoutError, socket.timeout) as exc:
            if attempt < retries:
                time.sleep(1.2 * (attempt + 1))
                continue
            if isinstance(exc, (TimeoutError, socket.timeout)):
                raise RuntimeError(f"请求超时：{timeout} 秒内接口没有响应") from exc
            raise RuntimeError(f"接口连接被中断：{exc}") from exc
    raise RuntimeError("接口请求失败")


def transcribe_audio_file(path, api_key, base_url, model):
    if not api_key:
        raise RuntimeError("缺少音频转文案 API Key")
    base_url = (base_url or "https://api.openai.com/v1").strip().rstrip("/")
    url = f"{base_url}/audio/transcriptions"
    boundary, body = multipart_form_data(
        {
            "model": model or AUDIO_MODEL_NAME,
            "response_format": "json",
            "language": "zh",
        },
        {"file": path},
    )
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            text = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"音频转文案接口 HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"音频转文案接口请求失败：{exc.reason}") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return text.strip()
    return text_value(data.get("text") or data.get("transcript") or data.get("content")).strip()


def transcribe_audio_file_local_gpu(path, settings, status_callback=None):
    if status_callback:
        status_callback("检查本地 GPU 转写依赖")
    try:
        import ctranslate2
        from faster_whisper import BatchedInferencePipeline, WhisperModel
    except ImportError as exc:
        raise RuntimeError("未安装本地 GPU 文案提取依赖，请先运行 dependencies\\faster-whisper-gpu\\install_gpu_deps.bat") from exc
    try:
        cuda_count = int(ctranslate2.get_cuda_device_count()) if hasattr(ctranslate2, "get_cuda_device_count") else 0
    except Exception:
        cuda_count = 0
    if cuda_count <= 0:
        raise RuntimeError("未检测到可用 CUDA 设备，请检查 NVIDIA 显卡驱动，或切换到 API 转写。")
    if status_callback:
        status_callback(f"检测到 {cuda_count} 个 CUDA 设备")

    model_name = text_value(settings.get("local_whisper_model"), LOCAL_WHISPER_MODEL_NAME).strip() or LOCAL_WHISPER_MODEL_NAME
    model_dir = text_value(settings.get("local_whisper_model_dir")).strip()
    compute_type = text_value(settings.get("local_whisper_compute_type"), "float16").strip() or "float16"
    try:
        batch_size = max(1, int(settings.get("local_whisper_batch_size") or 4))
    except (TypeError, ValueError):
        batch_size = 4
    try:
        beam_size = max(1, int(settings.get("local_whisper_beam_size") or 3))
    except (TypeError, ValueError):
        beam_size = 3

    cache_key = (model_name, model_dir, compute_type)
    model = LOCAL_WHISPER_CACHE.get(cache_key)
    if model is None:
        if status_callback:
            status_callback(f"加载本地 GPU 模型：{model_name}")
        kwargs = {"device": "cuda", "compute_type": compute_type}
        if model_dir:
            if not Path(model_dir).exists():
                raise RuntimeError(f"模型目录不存在：{model_dir}")
            kwargs["download_root"] = model_dir
        try:
            model = WhisperModel(model_name, **kwargs)
        except Exception as exc:
            raise RuntimeError(f"本地 GPU 模型加载失败：{exc}") from exc
        LOCAL_WHISPER_CACHE.clear()
        LOCAL_WHISPER_CACHE[cache_key] = model
        if status_callback:
            status_callback(f"本地 GPU 模型加载完成：{model_name}")

    if status_callback:
        status_callback(f"本地 GPU 文案提取中：batch={batch_size}, beam={beam_size}")
    try:
        if batch_size > 1:
            batched_model = BatchedInferencePipeline(model=model)
            segments, _info = batched_model.transcribe(
                str(path),
                language="zh",
                vad_filter=True,
                beam_size=beam_size,
                batch_size=batch_size,
            )
        else:
            segments, _info = model.transcribe(
                str(path),
                language="zh",
                vad_filter=True,
                beam_size=beam_size,
            )
        parts = []
        for index, segment in enumerate(segments, 1):
            parts.append(segment.text)
            if status_callback and index % 10 == 0:
                status_callback(f"本地 GPU 文案提取中：已识别 {index} 段")
        if status_callback:
            status_callback(f"本地 GPU 文案提取完成：共 {len(parts)} 段")
        return "".join(parts).strip()
    except Exception as exc:
        raise RuntimeError(f"本地 GPU 文案提取失败：{exc}") from exc


def validate_local_gpu_transcription(settings):
    try:
        import ctranslate2
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("未安装本地 GPU 文案提取依赖，请先运行 dependencies\\faster-whisper-gpu\\install_gpu_deps.bat") from exc

    cuda_count = 0
    if hasattr(ctranslate2, "get_cuda_device_count"):
        cuda_count = int(ctranslate2.get_cuda_device_count())
    if cuda_count <= 0:
        raise RuntimeError("未检测到可用 CUDA 设备，请检查 NVIDIA 显卡驱动。")

    model_name = text_value(settings.get("local_whisper_model"), LOCAL_WHISPER_MODEL_NAME).strip() or LOCAL_WHISPER_MODEL_NAME
    model_dir = text_value(settings.get("local_whisper_model_dir")).strip()
    compute_type = text_value(settings.get("local_whisper_compute_type"), "int8_float16").strip() or "int8_float16"
    kwargs = {"device": "cuda", "compute_type": compute_type}
    if model_dir:
        if not Path(model_dir).exists():
            raise RuntimeError(f"模型目录不存在：{model_dir}")
        kwargs["download_root"] = model_dir
    cache_key = (model_name, model_dir, compute_type)
    if cache_key not in LOCAL_WHISPER_CACHE:
        model = WhisperModel(model_name, **kwargs)
        LOCAL_WHISPER_CACHE.clear()
        LOCAL_WHISPER_CACHE[cache_key] = model
    return f"CUDA 可用，检测到 {cuda_count} 个 CUDA 设备；模型 {model_name} 已成功加载，计算精度 {compute_type}。"


def detect_nvidia_gpu_info():
    command = [
        "nvidia-smi",
        "--query-gpu=name,memory.total,memory.free,driver_version",
        "--format=csv,noheader,nounits",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=12, check=True)
    except FileNotFoundError as exc:
        raise RuntimeError("未找到 nvidia-smi，请确认已安装 NVIDIA 显卡驱动。") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("检测 GPU 超时，请稍后重试。") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise RuntimeError(f"nvidia-smi 执行失败：{detail or exc}") from exc

    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("未检测到 NVIDIA GPU。")

    summaries = []
    for index, line in enumerate(lines, start=1):
        parts = [part.strip() for part in line.split(",")]
        name = parts[0] if len(parts) > 0 else "未知型号"
        total_mb = int(float(parts[1])) if len(parts) > 1 and parts[1] else 0
        free_mb = int(float(parts[2])) if len(parts) > 2 and parts[2] else 0
        driver = parts[3] if len(parts) > 3 else "未知"
        total_gb = total_mb / 1024 if total_mb else 0
        free_gb = free_mb / 1024 if free_mb else 0
        if total_gb >= 12:
            advice = "可选 medium，显存充足时可尝试 large-v3 / distil-large-v3，batch 4-8。"
        elif total_gb >= 8:
            advice = "建议 small 或 medium，计算精度 int8_float16，batch 2-4。"
        else:
            advice = "建议 small，计算精度 int8_float16 或 int8，batch 1。"
        summaries.append(
            f"GPU {index}: {name}\n"
            f"显存：总计 {total_gb:.1f} GB，可用 {free_gb:.1f} GB\n"
            f"驱动版本：{driver}\n"
            f"推荐：{advice}"
        )
    return "\n\n".join(summaries)


def chat_completion_text(prompt, api_key, base_url, model):
    if not api_key:
        raise RuntimeError("缺少文本模型 API Key")
    base_url = (base_url or "https://api.openai.com/v1").strip().rstrip("/")
    payload = {
        "model": model or TEXT_MODEL_NAME,
        "messages": [
            {"role": "system", "content": "你是短视频文案改写助手。保持事实一致，输出适合直接用于视频生成或发布的中文文案。"},
            {"role": "user", "content": prompt},
        ],
    }
    result = http_json("POST", f"{base_url}/chat/completions", api_key, payload, timeout=300, retries=2)
    choices = result.get("choices") or []
    if choices:
        message = choices[0].get("message") or {}
        content = message.get("content")
        if content:
            return text_value(content).strip()
    return text_value(result.get("output_text") or result.get("text")).strip()


def chat_completion_messages(messages, api_key, base_url, model):
    if not api_key:
        raise RuntimeError("缺少文本模型 API Key")
    base_url = (base_url or "https://api.openai.com/v1").strip().rstrip("/")
    payload = {
        "model": model or TEXT_MODEL_NAME,
        "messages": messages,
    }
    result = http_json("POST", f"{base_url}/chat/completions", api_key, payload, timeout=300, retries=2)
    choices = result.get("choices") or []
    if choices:
        message = choices[0].get("message") or {}
        content = message.get("content")
        if content:
            return text_value(content).strip()
    return text_value(result.get("output_text") or result.get("text")).strip()


def chat_completion_messages_stream(messages, api_key, base_url, model, on_delta):
    if not api_key:
        raise RuntimeError("缺少文本模型 API Key")
    base_url = (base_url or "https://api.openai.com/v1").strip().rstrip("/")
    payload = {
        "model": model or TEXT_MODEL_NAME,
        "messages": messages,
        "stream": True,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "User-Agent": "GrokVideoStudio/1.0",
        "Connection": "close",
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(f"{base_url}/chat/completions", data=body, headers=headers, method="POST")
    chunks = []
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            while True:
                raw = resp.readline()
                if not raw:
                    break
                line = raw.decode("utf-8", errors="replace").strip()
                if not line or not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    event = json.loads(data)
                except json.JSONDecodeError:
                    continue
                choices = event.get("choices") or []
                if not choices:
                    continue
                choice = choices[0]
                delta = choice.get("delta") or {}
                content = delta.get("content")
                if content is None:
                    message = choice.get("message") or {}
                    content = message.get("content")
                content = text_value(content)
                if content:
                    chunks.append(content)
                    on_delta(content)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(str(exc.reason)) from exc
    except http.client.RemoteDisconnected as exc:
        raise RuntimeError("接口服务器主动断开连接，可能是模型服务繁忙、请求内容过长或当前模型不支持流式回复。") from exc
    except (ConnectionResetError, ConnectionAbortedError, TimeoutError, socket.timeout) as exc:
        if isinstance(exc, (TimeoutError, socket.timeout)):
            raise RuntimeError("请求超时：300 秒内接口没有响应") from exc
        raise RuntimeError(f"接口连接被中断：{exc}") from exc
    return "".join(chunks).strip()


def save_image_from_result(result, prompt):
    data = result.get("data") or []
    first = data[0] if isinstance(data, list) and data else result
    if not isinstance(first, dict):
        return ""
    GENERATED_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    destination = GENERATED_IMAGE_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_name(prompt[:24])}.png"
    if first.get("b64_json"):
        destination.write_bytes(base64.b64decode(first["b64_json"]))
        return str(destination)
    image_url = first.get("url") or first.get("image_url") or first.get("output_url")
    if image_url:
        download_file(image_url, "", destination)
        return str(destination)
    nested = first.get("image")
    if isinstance(nested, dict):
        return save_image_from_result({"data": [nested]}, prompt)
    nested_result = first.get("result")
    if isinstance(nested_result, dict):
        return save_image_from_result(nested_result, prompt)
    return ""


def image_request_id(result):
    if not isinstance(result, dict):
        return ""
    object_type = text_value(result.get("object")).strip()
    job_id = text_value(result.get("id")).strip()
    if object_type == "image_generation.job" and job_id:
        return job_id
    if job_id.startswith("imgjob_"):
        return job_id
    for key in ("task_id", "job_id", "id", "generation_id", "request_id"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    data = result.get("data")
    if isinstance(data, dict):
        return image_request_id(data)
    if isinstance(data, list) and data:
        return image_request_id(data[0])
    return ""


def image_poll_url(base_url, poll_path, request_id, submit_result):
    for key in ("poll_url", "status_url", "result_url"):
        value = submit_result.get(key) if isinstance(submit_result, dict) else ""
        if isinstance(value, str) and value.strip():
            return value.strip()
    base_url = base_url.rstrip("/")
    poll_path = (poll_path or DEFAULT_IMAGE_POLL_PATH).strip()
    if poll_path.startswith(("http://", "https://")):
        return poll_path.replace("{id}", urllib.parse.quote(request_id))
    if "{id}" in poll_path:
        path = poll_path.replace("{id}", urllib.parse.quote(request_id))
    else:
        path = poll_path.rstrip("/") + "/" + urllib.parse.quote(request_id)
    if not path.startswith("/"):
        path = "/" + path
    return base_url + path


def image_result_state(result):
    if not isinstance(result, dict):
        return ""
    state = result.get("status") or result.get("state") or result.get("task_status") or ""
    return text_value(state).strip().lower()


def image_poll_attempts():
    return max(1, (IMAGE_POLL_TIMEOUT + IMAGE_POLL_INTERVAL - 1) // IMAGE_POLL_INTERVAL)


def generate_image_file(prompt, api_key, base_url, model, size="1024x1024", poll_path=DEFAULT_IMAGE_POLL_PATH, status_callback=None, reference_paths=None, quality="auto"):
    if not api_key:
        raise RuntimeError("缺少文生图 API Key")
    base_url = (base_url or "https://api.openai.com/v1").strip().rstrip("/")
    resolved_references = []
    for path in (reference_paths or [])[:MAX_REFERENCE_IMAGES]:
        ref_path = Path(path)
        if ref_path.exists():
            resolved_references.append(ref_path)
    if resolved_references:
        fields = {
            "model": model or IMAGE_MODEL_NAME,
            "prompt": prompt,
            "size": size,
            "n": 1,
            "background": "auto",
        }
        if quality:
            fields["quality"] = quality
        files = [("image", path, path.name) for path in resolved_references]
        append_image_generation_log(
            f"submit_endpoint={base_url}/images/edits reference_count={len(files)} "
            f"reference_files={[path.name for path in resolved_references]}"
        )
        submit_result = http_multipart_json(
            f"{base_url}/images/edits",
            api_key,
            fields,
            files,
            timeout=IMAGE_SUBMIT_TIMEOUT,
        )
    else:
        payload = {
            "model": model or IMAGE_MODEL_NAME,
            "prompt": prompt,
            "size": size,
            "n": 1,
            "background": "auto",
        }
        if quality:
            payload["quality"] = quality
        append_image_generation_log(f"submit_endpoint={base_url}/images/generations reference_count=0")
        submit_result = http_json("POST", f"{base_url}/images/generations", api_key, payload, timeout=IMAGE_SUBMIT_TIMEOUT)
    append_image_generation_log(f"submit_result={json.dumps(compact_log_data(submit_result), ensure_ascii=False)}")
    direct_path = save_image_from_result(submit_result, prompt)
    if direct_path:
        return Path(direct_path)

    request_id = image_request_id(submit_result)
    if not request_id:
        raise RuntimeError(f"文生图接口未返回图片或任务 ID：{submit_result}")
    if status_callback:
        status_callback(f"已提交：{request_id}")

    poll_url = image_poll_url(base_url, poll_path, request_id, submit_result)
    append_image_generation_log(f"request_id={request_id} poll_url={poll_url}")
    for _attempt in range(image_poll_attempts()):
        time.sleep(IMAGE_POLL_INTERVAL)
        try:
            result = http_json("GET", poll_url, api_key, timeout=60)
        except Exception as exc:
            error_text = str(exc)
            append_image_generation_log(f"poll_error request_id={request_id} error={error_text}")
            if "HTTP 404" in error_text and "job not found" in error_text.lower():
                if status_callback:
                    status_callback(f"等待任务可查询：{request_id}")
                continue
            transient_markers = (
                "remote end closed connection without response",
                "closed connection without response",
                "connection reset",
                "timed out",
                "请求超时",
            )
            if any(marker in error_text.lower() for marker in transient_markers):
                if status_callback:
                    status_callback(f"轮询连接中断，继续重试：{request_id}")
                continue
            raise
        append_image_generation_log(f"poll_result={json.dumps(compact_log_data(result), ensure_ascii=False)}")
        path = save_image_from_result(result, prompt)
        if path:
            return Path(path)
        state = image_result_state(result)
        if state in ("failed", "error", "expired", "canceled", "cancelled"):
            raise RuntimeError(f"图片生成任务失败：{result}")
        if status_callback:
            status_callback(f"生成中：{state or request_id}")

    raise RuntimeError(f"图片生成轮询超时：{request_id}")


def poll_image_job_file(prompt, api_key, base_url, request_id, poll_path=DEFAULT_IMAGE_POLL_PATH, status_callback=None):
    if not api_key:
        raise RuntimeError("缺少文生图 API Key")
    if not request_id:
        raise RuntimeError("缺少图片任务 ID")
    base_url = (base_url or "https://api.openai.com/v1").strip().rstrip("/")
    poll_url = image_poll_url(base_url, poll_path, request_id, {})
    append_image_generation_log(f"manual_poll request_id={request_id} poll_url={poll_url}")
    for attempt in range(image_poll_attempts()):
        if attempt > 0:
            time.sleep(IMAGE_POLL_INTERVAL)
        try:
            result = http_json("GET", poll_url, api_key, timeout=60)
        except Exception as exc:
            error_text = str(exc)
            append_image_generation_log(f"manual_poll_error request_id={request_id} error={error_text}")
            transient_markers = (
                "remote end closed connection without response",
                "closed connection without response",
                "connection reset",
                "timed out",
                "请求超时",
            )
            if "HTTP 404" in error_text and "job not found" in error_text.lower():
                if status_callback:
                    status_callback(f"等待任务可查询：{request_id}")
                continue
            if any(marker in error_text.lower() for marker in transient_markers):
                if status_callback:
                    status_callback(f"轮询连接中断，继续重试：{request_id}")
                continue
            raise
        append_image_generation_log(f"manual_poll_result={json.dumps(compact_log_data(result), ensure_ascii=False)}")
        path = save_image_from_result(result, prompt)
        if path:
            return Path(path)
        state = image_result_state(result)
        if state in ("failed", "error", "expired", "canceled", "cancelled"):
            raise RuntimeError(f"图片生成任务失败：{result}")
        if status_callback:
            status_callback(f"生成中：{state or request_id}")
    raise RuntimeError(f"图片生成轮询超时：{request_id}")


def query_image_job_once(prompt, api_key, base_url, request_id, poll_path=DEFAULT_IMAGE_POLL_PATH):
    if not api_key:
        raise RuntimeError("缺少文生图 API Key")
    if not request_id:
        raise RuntimeError("缺少图片任务 ID")
    base_url = (base_url or "https://api.openai.com/v1").strip().rstrip("/")
    poll_url = image_poll_url(base_url, poll_path, request_id, {})
    append_image_generation_log(f"single_poll request_id={request_id} poll_url={poll_url}")
    result = http_json("GET", poll_url, api_key, timeout=60)
    append_image_generation_log(f"single_poll_result={json.dumps(compact_log_data(result), ensure_ascii=False)}")
    path = save_image_from_result(result, prompt)
    state = image_result_state(result)
    return path, state, result


@dataclass
class Material:
    id: str
    alias: str
    path: str
    added_at: str
    tags: str = ""
    prompt: str = ""
    references: list[str] = field(default_factory=list)


@dataclass
class Task:
    id: str
    prompt: str
    aspect_ratio: str
    duration: int
    resolution: str
    references: list[str]
    status: str = "queued"
    request_id: str = ""
    output_path: str = ""
    error: str = ""
    created_at: str = field(default_factory=now_text)
    updated_at: str = field(default_factory=now_text)


@dataclass
class ParsedVideo:
    id: str
    source_url: str
    video_url: str = ""
    title: str = ""
    caption: str = ""
    cover_url: str = ""
    local_path: str = ""
    raw: dict = field(default_factory=dict)
    created_at: str = field(default_factory=now_text)
    updated_at: str = field(default_factory=now_text)


@dataclass
class ImageTask:
    id: str
    prompt: str
    size: str
    references: list[str]
    quality: str = "auto"
    status: str = "queued"
    request_id: str = ""
    output_path: str = ""
    error: str = ""
    created_at: str = field(default_factory=now_text)
    updated_at: str = field(default_factory=now_text)


@dataclass
class AgentConversation:
    id: str
    title: str
    messages: list[dict]
    created_at: str
    updated_at: str


def repair_image_task(item):
    if not isinstance(item, dict):
        item = {}
    refs = item.get("references") or []
    if not isinstance(refs, list):
        refs = []
    task = ImageTask(
        id=text_value(item.get("id"), uuid.uuid4().hex[:12]),
        prompt=text_value(item.get("prompt")),
        size=text_value(item.get("size"), "2048x2048"),
        references=[text_value(ref) for ref in refs],
        quality=text_value(item.get("quality"), "auto"),
        status=text_value(item.get("status"), "queued"),
        request_id=text_value(item.get("request_id")),
        output_path=text_value(item.get("output_path")),
        error=text_value(item.get("error")),
        created_at=text_value(item.get("created_at"), now_text()),
        updated_at=text_value(item.get("updated_at"), now_text()),
    )
    task.output_path = resolve_image_output_path(task.output_path, task)
    return task


def repair_agent_conversation(item):
    if not isinstance(item, dict):
        item = {}
    messages = item.get("messages") or []
    if not isinstance(messages, list):
        messages = []
    clean_messages = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = text_value(message.get("role")).strip()
        content = text_value(message.get("content")).strip()
        if role in ("system", "user", "assistant") and content:
            clean_message = {"role": role, "content": content}
            if "model_content" in message:
                model_content = message.get("model_content")
                if isinstance(model_content, str):
                    clean_message["model_content"] = text_value(model_content)
                elif isinstance(model_content, list):
                    clean_message["model_content"] = model_content
            attachments = message.get("attachments")
            if isinstance(attachments, list):
                clean_message["attachments"] = [item for item in attachments if isinstance(item, dict)]
            clean_messages.append(clean_message)
    conversation_id = text_value(item.get("id"), uuid.uuid4().hex[:12])
    title = text_value(item.get("title"), "新对话")
    return AgentConversation(
        id=conversation_id,
        title=title or "新对话",
        messages=clean_messages,
        created_at=text_value(item.get("created_at"), now_text()),
        updated_at=text_value(item.get("updated_at"), now_text()),
    )


def resolve_image_output_path(output_path, task=None):
    output_path = text_value(output_path)
    if not output_path:
        return ""
    path = Path(output_path)
    if path.exists():
        return str(path)

    candidates = []
    if path.name:
        candidates.append(GENERATED_IMAGE_DIR / path.name)
        match = re.match(r"(\d{8}_\d{6})_", path.name)
        if match and GENERATED_IMAGE_DIR.exists():
            candidates.extend(GENERATED_IMAGE_DIR.glob(f"{match.group(1)}_*"))
    if task and task.updated_at and GENERATED_IMAGE_DIR.exists():
        try:
            prefix = datetime.strptime(task.updated_at, "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d_%H%M%S")
            candidates.extend(GENERATED_IMAGE_DIR.glob(f"{prefix}_*"))
        except ValueError:
            pass

    seen = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists():
            return str(candidate)
    return output_path


def repair_parsed_video(item):
    if not isinstance(item, dict):
        item = {}
    raw = item.get("raw") if isinstance(item.get("raw"), dict) else {}
    return ParsedVideo(
        id=text_value(item.get("id"), uuid.uuid4().hex[:12]),
        source_url=text_value(item.get("source_url")),
        video_url=text_value(item.get("video_url")),
        title=text_value(item.get("title")),
        caption=text_value(item.get("caption")),
        cover_url=text_value(item.get("cover_url")),
        local_path=text_value(item.get("local_path")),
        raw=raw,
        created_at=text_value(item.get("created_at"), now_text()),
        updated_at=text_value(item.get("updated_at"), now_text()),
    )


def first_text_value(data, keys):
    if isinstance(data, dict):
        for key in keys:
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for value in data.values():
            found = first_text_value(value, keys)
            if found:
                return found
    elif isinstance(data, list):
        for value in data:
            found = first_text_value(value, keys)
            if found:
                return found
    return ""


def first_video_url(data):
    return first_text_value(data, (
        "video_url", "videoUrl", "play_url", "playUrl", "download_url", "downloadUrl",
        "video", "url", "mp4", "nwm_video_url", "wm_video_url",
    ))


class VideoParserClient:
    def __init__(self, endpoint, key, sign):
        self.endpoint = endpoint.strip()
        self.key = key.strip()
        self.sign = sign.strip()

    def parse(self, source_url):
        query = urllib.parse.urlencode({
            "sign": self.sign,
            "key": self.key,
            "url": source_url.strip(),
        })
        sep = "&" if "?" in self.endpoint else "?"
        request_url = f"{self.endpoint}{sep}{query}"
        req = urllib.request.Request(request_url, headers={"User-Agent": "GrokVideoStudio/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                text = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"解析接口 HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"解析接口请求失败：{exc.reason}") from exc
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = {"text": text}
        title = first_text_value(data, ("title", "desc", "description", "content", "copywriting", "文案"))
        return ParsedVideo(
            id=uuid.uuid4().hex[:12],
            source_url=source_url.strip(),
            video_url=first_video_url(data),
            title=title,
            caption=title,
            cover_url=first_text_value(data, ("cover", "cover_url", "coverUrl", "image", "thumbnail")),
            raw=data if isinstance(data, dict) else {"data": data},
        )


class VideoApiClient:
    def __init__(self, api_key, base_url=API_BASE, model_name=MODEL_NAME):
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name.strip() or MODEL_NAME

    def create_video(self, task, materials_by_id):
        references = []
        prompt = task.prompt
        for material_id in task.references[:MAX_REFERENCE_IMAGES]:
            material = materials_by_id.get(material_id)
            if material and Path(material.path).exists():
                image_index = len(references) + 1
                prompt = re.sub(rf"@{re.escape(material.alias)}\b", f"<IMAGE_{image_index}>", prompt)
                references.append({"image_url": data_uri_for_file(material.path)})

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "seconds": supported_video_seconds(task.duration),
            "aspect_ratio": task.aspect_ratio,
            "size": video_size_for_aspect(task.aspect_ratio),
            "resolution_name": task.resolution,
        }
        if references:
            payload["input_references"] = references
        result = http_json("POST", f"{self.base_url}/videos", self.api_key, payload, timeout=180)
        request_id = result.get("request_id") or result.get("task_id") or result.get("id")
        if not request_id:
            raise RuntimeError(f"接口未返回 request_id: {result}")
        return request_id

    def get_video(self, request_id):
        return http_json("GET", f"{self.base_url}/videos/{urllib.parse.quote(request_id)}", self.api_key, timeout=120)

    def save_video(self, video_url, destination):
        download_file(video_url, self.api_key, destination)


class LicenseClient:
    def __init__(self, server_url=DEFAULT_LICENSE_SERVER_URL):
        self.server_url = (server_url or DEFAULT_LICENSE_SERVER_URL).strip().rstrip("/")

    def request(self, action, card_key, token=""):
        if not self.server_url:
            raise RuntimeError("卡密服务器地址未配置")
        card_key = (card_key or "").strip()
        if not card_key:
            raise RuntimeError("请输入卡密")
        payload = {
            "card_key": card_key,
            "machine_id": machine_fingerprint(),
            "machine_name": machine_display_name(),
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
        }
        if token:
            payload["token"] = token
        return post_json(f"{self.server_url}/api/license/{action}", payload, timeout=20)

    def activate(self, card_key, token=""):
        return self.request("activate", card_key, token)

    def query(self, card_key, token=""):
        return self.request("query", card_key, token)

    def unbind(self, card_key, token=""):
        return self.request("unbind", card_key, token)


class LicenseGate:
    def __init__(self, root):
        ensure_dirs()
        self.root = root
        self.settings = read_json(SETTINGS_FILE, {})
        self.license_data = read_json(LICENSE_FILE, {})
        self.authorized = False
        self.machine_id = machine_fingerprint()
        self.card_var = StringVar(value=self.license_data.get("card_key", ""))
        self.status_var = StringVar(value="请输入卡密完成验证")
        self.expire_var = StringVar(value=self.license_data.get("expires_at", "未查询"))
        self.unbind_var = StringVar(value=str(self.license_data.get("remaining_unbinds", "未查询")))
        self.token = self.license_data.get("token", "")
        self.done_var = StringVar(value="")
        self.build()

    def build(self):
        self.window = self.root
        self.window.title(f"{APP_NAME} - 卡密验证")
        self.window.geometry("520x360+220+160")
        self.window.resizable(False, False)
        self.window.configure(bg=COLOR_BG)
        self.window.protocol("WM_DELETE_WINDOW", self.cancel)
        if APP_ICON_FILE.exists():
            self.window.iconbitmap(str(APP_ICON_FILE))
        body = Frame(self.window, padx=26, pady=24, bg=COLOR_BG)
        body.pack(fill=BOTH, expand=True)
        Label(body, text="卡密验证", font=("Microsoft YaHei UI", 20, "bold"), bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor="w")
        Label(body, text="一张卡密仅允许绑定一台电脑，解绑后才能绑定新电脑。", bg=COLOR_BG, fg=COLOR_MUTED, font=FONT_SMALL).pack(anchor="w", pady=(4, 18))

        form = Frame(body, bg=COLOR_BG)
        form.pack(fill=X)
        Label(form, text="卡密", width=8, anchor="w", bg=COLOR_BG, fg=COLOR_TEXT).grid(row=0, column=0, sticky="w", pady=6)
        Entry(form, textvariable=self.card_var, show="*", bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT, relief="flat").grid(row=0, column=1, sticky="ew", pady=6)
        form.columnconfigure(1, weight=1)

        info = Frame(body, bg=COLOR_PANEL, padx=12, pady=10, highlightthickness=1, highlightbackground=COLOR_BORDER)
        info.pack(fill=X, pady=(12, 8))
        Label(info, text="到期时间", bg=COLOR_PANEL, fg=COLOR_MUTED).grid(row=0, column=0, sticky="w")
        Label(info, textvariable=self.expire_var, bg=COLOR_PANEL, fg=COLOR_TEXT).grid(row=0, column=1, sticky="w", padx=(14, 0))
        Label(info, text="剩余解绑次数", bg=COLOR_PANEL, fg=COLOR_MUTED).grid(row=1, column=0, sticky="w", pady=(6, 0))
        Label(info, textvariable=self.unbind_var, bg=COLOR_PANEL, fg=COLOR_TEXT).grid(row=1, column=1, sticky="w", padx=(14, 0), pady=(6, 0))
        Label(info, text="本机码", bg=COLOR_PANEL, fg=COLOR_MUTED).grid(row=2, column=0, sticky="w", pady=(6, 0))
        Label(info, text=self.machine_id[:16], bg=COLOR_PANEL, fg=COLOR_TEXT).grid(row=2, column=1, sticky="w", padx=(14, 0), pady=(6, 0))

        Label(body, textvariable=self.status_var, anchor="w", bg=COLOR_BG, fg=COLOR_MUTED).pack(fill=X, pady=(6, 10))
        actions = Frame(body, bg=COLOR_BG)
        actions.pack(fill=X)
        Button(actions, text="查看剩余时间", command=self.query_license).pack(side=LEFT)
        Button(actions, text="解绑", command=self.unbind_license).pack(side=LEFT, padx=(8, 0))
        Button(actions, text="退出", command=self.cancel).pack(side=RIGHT)
        Button(actions, text="登录", command=self.activate_license, bg=COLOR_ACCENT_DARK, fg="#ffffff").pack(side=RIGHT, padx=(0, 8))
        self.apply_button_style(actions)
        self.card_var.trace_add("write", lambda *_: self.status_var.set("请输入卡密完成验证"))
        self.window.bind("<Return>", lambda _event: self.activate_license())
        self.window.deiconify()
        self.window.lift()
        try:
            self.window.attributes("-topmost", True)
            self.window.after(800, lambda: self.window.attributes("-topmost", False))
        except Exception:
            pass
        self.window.focus_force()
        self.window.update_idletasks()
        self.window.update()

    def apply_button_style(self, widget):
        for child in widget.winfo_children():
            if child.winfo_class() == "Button":
                try:
                    child.configure(
                        bg=child.cget("bg") if child.cget("bg") != "SystemButtonFace" else COLOR_CARD,
                        fg=child.cget("fg") if child.cget("fg") != "SystemButtonText" else COLOR_TEXT,
                        activebackground=COLOR_ACCENT_DARK,
                        activeforeground="#ffffff",
                        relief="flat",
                        bd=0,
                        padx=12,
                        pady=7,
                        font=FONT_BODY,
                    )
                except Exception:
                    pass

    def client(self):
        return LicenseClient()

    def save_license(self, result=None):
        result = result or {}
        data = {
            "server_url": DEFAULT_LICENSE_SERVER_URL,
            "card_key": self.card_var.get().strip(),
            "token": result.get("token") or self.token,
            "expires_at": result.get("expires_at") or self.expire_var.get(),
            "remaining_unbinds": result.get("remaining_unbinds", self.unbind_var.get()),
            "machine_id": self.machine_id,
            "verified_at": now_text(),
        }
        write_json(LICENSE_FILE, data)
        self.settings["license_server_url"] = DEFAULT_LICENSE_SERVER_URL
        write_json(SETTINGS_FILE, self.settings)
        self.license_data = data
        self.token = data.get("token", "")

    def update_result(self, result):
        if not result.get("ok"):
            raise RuntimeError(result.get("message") or "卡密验证失败")
        if result.get("expires_at"):
            self.expire_var.set(str(result.get("expires_at")))
        if "remaining_unbinds" in result:
            self.unbind_var.set(str(result.get("remaining_unbinds")))
        self.status_var.set(result.get("message") or "操作成功")

    def activate_license(self):
        try:
            result = self.client().activate(self.card_var.get(), self.token)
            self.update_result(result)
            self.save_license(result)
            self.authorized = True
            self.done_var.set("1")
        except Exception as exc:
            self.status_var.set(str(exc))
            messagebox.showerror("卡密验证失败", str(exc), parent=self.window)

    def query_license(self):
        try:
            result = self.client().query(self.card_var.get(), self.token)
            self.update_result(result)
            self.save_license(result)
        except Exception as exc:
            self.status_var.set(str(exc))
            messagebox.showerror("查询失败", str(exc), parent=self.window)

    def unbind_license(self):
        if not messagebox.askyesno("解绑卡密", "解绑会消耗一次解绑机会，确认解绑当前电脑？", parent=self.window):
            return
        try:
            result = self.client().unbind(self.card_var.get(), self.token)
            self.update_result(result)
            self.token = ""
            self.save_license({"token": "", "expires_at": result.get("expires_at"), "remaining_unbinds": result.get("remaining_unbinds")})
            self.status_var.set(result.get("message") or "已解绑，可以在新电脑上绑定")
        except Exception as exc:
            self.status_var.set(str(exc))
            messagebox.showerror("解绑失败", str(exc), parent=self.window)

    def cancel(self):
        self.authorized = False
        self.done_var.set("1")

    def show(self):
        self.root.wait_variable(self.done_var)
        if self.authorized:
            self.window.unbind("<Return>")
            for child in self.window.winfo_children():
                child.destroy()
        return self.authorized


class GrokVideoStudio:
    def __init__(self, root):
        ensure_dirs()
        self.root = root
        self.root.title(APP_NAME)
        if APP_ICON_FILE.exists():
            self.root.iconbitmap(str(APP_ICON_FILE))
        self.root.resizable(True, True)
        self.root.geometry("1600x900")
        self.root.minsize(1400, 800)
        self.setup_dark_style()

        self.settings = read_json(SETTINGS_FILE, {
            "api_key": "",
            "base_url": API_BASE,
            "video_model": MODEL_NAME,
            "text_api_key": "",
            "text_base_url": "https://api.openai.com/v1",
            "text_model": TEXT_MODEL_NAME,
            "image_api_key": "",
            "image_base_url": "https://api.openai.com/v1",
            "image_model": IMAGE_MODEL_NAME,
            "image_poll_path": DEFAULT_IMAGE_POLL_PATH,
            "audio_api_key": "",
            "audio_base_url": "https://api.openai.com/v1",
            "audio_model": AUDIO_MODEL_NAME,
            "transcribe_mode": "local_gpu",
            "local_whisper_model": LOCAL_WHISPER_MODEL_NAME,
            "local_whisper_model_dir": str(APP_DIR / "models" / "faster-whisper"),
            "local_whisper_compute_type": "int8_float16",
            "local_whisper_batch_size": "1",
            "local_whisper_beam_size": "3",
            "parser_endpoint": DEFAULT_PARSER_ENDPOINT,
            "parser_key": DEFAULT_PARSER_KEY,
            "parser_sign": DEFAULT_PARSER_SIGN,
            "parser_download_dir": str(OUTPUT_DIR / "parsed_videos"),
            "poll_interval": 8,
            "concurrency": 2,
            "output_dir": str(OUTPUT_DIR),
        })
        bundled_model_dir = APP_DIR / "models" / "faster-whisper"
        configured_model_dir = Path(text_value(self.settings.get("local_whisper_model_dir")) or bundled_model_dir)
        if bundled_model_dir.exists() and configured_model_dir.resolve() != bundled_model_dir.resolve():
            self.settings["local_whisper_model_dir"] = str(bundled_model_dir)
        if not text_value(self.settings.get("parser_download_dir")).strip():
            self.settings["parser_download_dir"] = str(OUTPUT_DIR / "parsed_videos")
        if not text_value(self.settings.get("output_dir")).strip():
            self.settings["output_dir"] = str(OUTPUT_DIR)
        self.materials = [repair_material(item) for item in read_json(MATERIALS_FILE, [])]
        self.persist_materials()
        self.material_groups = repair_groups(read_json(GROUPS_FILE, DEFAULT_MATERIAL_GROUPS))
        self.persist_material_groups()
        self.tasks = [repair_task(item) for item in read_json(TASKS_FILE, [])]
        self.persist_tasks()
        self.parsed_videos = [repair_parsed_video(item) for item in read_json(PARSED_VIDEOS_FILE, [])]
        self.persist_parsed_videos()
        self.image_tasks = [repair_image_task(item) for item in read_json(IMAGE_TASKS_FILE, [])]
        self.persist_image_tasks()
        self.agent_conversations = [repair_agent_conversation(item) for item in read_json(AGENT_CONVERSATIONS_FILE, [])]
        self.image_prompt_templates = repair_prompt_templates(read_json(IMAGE_PROMPT_TEMPLATES_FILE, []), DEFAULT_IMAGE_PROMPT_TEMPLATES)
        self.rewrite_prompt_templates = repair_prompt_templates(read_json(REWRITE_PROMPT_TEMPLATES_FILE, []), DEFAULT_REWRITE_PROMPT_TEMPLATES)
        self.rewrite_history = read_json(REWRITE_HISTORY_FILE, [])
        if not isinstance(self.rewrite_history, list):
            self.rewrite_history = []
        self.persist_image_prompt_templates()
        self.persist_rewrite_prompt_templates()
        self.current_agent_conversation_id = ""
        if not self.agent_conversations:
            self.agent_conversations.append(self.new_agent_conversation_object())
            self.persist_agent_conversations()
        self.current_agent_conversation_id = self.agent_conversations[0].id
        self.event_queue = queue.Queue()
        self.worker_stop = threading.Event()
        self.worker_thread = None
        self.task_checked_ids = set()
        self.active_transcribe_jobs = {}
        self.material_images = {}
        self.asset_grid_images = {}

        self.api_key_var = StringVar(value=self.settings.get("api_key", ""))
        self.base_url_var = StringVar(value=self.settings.get("base_url", API_BASE))
        self.video_model_var = StringVar(value=self.settings.get("video_model", MODEL_NAME))
        self.output_dir_var = StringVar(value=self.settings.get("output_dir", str(OUTPUT_DIR)))
        self.aspect_var = StringVar(value="16:9")
        self.duration_var = StringVar(value="6")
        self.resolution_var = StringVar(value="720p")
        self.status_var = StringVar(value="就绪")
        self.search_var = StringVar(value="")
        self.generate_search_var = StringVar(value="")
        self.generate_asset_type_var = StringVar(value="全部")
        self.image_search_var = StringVar(value="")
        self.image_asset_type_var = StringVar(value="全部")
        self.parse_url_var = StringVar(value="")
        self.parser_download_dir_var = StringVar(value=self.settings.get("parser_download_dir") or str(OUTPUT_DIR / "parsed_videos"))
        self.parser_status_var = StringVar(value="待解析")
        self.asset_type_var = StringVar(value="全部")
        self.agent_input_var = StringVar(value="")
        self.agent_attachment_var = StringVar(value="未添加附件")
        self.agent_attachment_paths = []
        self.rewrite_input_var = StringVar(value="")
        self.image_size_var = StringVar(value="2048x2048")
        self.image_width_var = StringVar(value="2048")
        self.image_height_var = StringVar(value="2048")
        self.image_quality_var = StringVar(value="auto")
        self.image_aspect_var = StringVar(value="1:1(2k)")
        self.image_width_var.trace_add("write", lambda *_: self.update_image_size_from_dimensions())
        self.image_height_var.trace_add("write", lambda *_: self.update_image_size_from_dimensions())
        self.image_status_var = StringVar(value="待生成")
        self.image_template_var = StringVar(value=self.image_prompt_templates[0]["name"] if self.image_prompt_templates else "")
        self.rewrite_template_var = StringVar(value=self.rewrite_prompt_templates[0]["name"] if self.rewrite_prompt_templates else "")
        self.generate_material_images = {}
        self.image_reference_paths = []
        self.video_reference_paths = []
        self.image_reference_images = {}
        self.video_reference_images = {}
        self.image_asset_images = {}
        self.image_reference_var = StringVar(value="未上传参考图")
        self.video_reference_var = StringVar(value="未上传参考图")
        self.last_generated_image_path = ""
        self.last_generated_image_task_id = ""

        self.build_ui()
        self.refresh_materials()
        self.refresh_tasks()
        self.refresh_parsed_videos()
        self.refresh_image_tasks()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(250, self.process_events)
        self.start_worker_if_needed()

    def setup_dark_style(self):
        self.root.configure(bg=COLOR_BG)
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(".", background=COLOR_PANEL, foreground=COLOR_TEXT, fieldbackground=COLOR_INPUT)
        style.configure("TCombobox", fieldbackground=COLOR_INPUT, background=COLOR_PANEL_2, foreground=COLOR_TEXT, arrowcolor=COLOR_TEXT, bordercolor=COLOR_BORDER, lightcolor=COLOR_BORDER, darkcolor=COLOR_BORDER, selectbackground=COLOR_INPUT, selectforeground=COLOR_TEXT)
        style.map("TCombobox", fieldbackground=[("readonly", COLOR_INPUT), ("focus", COLOR_INPUT), ("!disabled", COLOR_INPUT)], foreground=[("readonly", COLOR_TEXT), ("focus", COLOR_TEXT), ("!disabled", COLOR_TEXT)], selectbackground=[("readonly", COLOR_INPUT), ("focus", COLOR_INPUT)], selectforeground=[("readonly", COLOR_TEXT), ("focus", COLOR_TEXT)])
        style.configure("Settings.TCombobox", fieldbackground="#000000", background=COLOR_PANEL_2, foreground=COLOR_TEXT, arrowcolor=COLOR_TEXT, bordercolor=COLOR_BORDER, lightcolor=COLOR_BORDER, darkcolor=COLOR_BORDER, selectbackground="#000000", selectforeground=COLOR_TEXT)
        style.map("Settings.TCombobox", fieldbackground=[("readonly", "#000000"), ("focus", "#000000"), ("!disabled", "#000000")], foreground=[("readonly", COLOR_TEXT), ("focus", COLOR_TEXT), ("!disabled", COLOR_TEXT)], selectbackground=[("readonly", "#000000"), ("focus", "#000000")], selectforeground=[("readonly", COLOR_TEXT), ("focus", COLOR_TEXT)])
        style.configure("Dark.TCombobox", fieldbackground="#000000", background=COLOR_PANEL_2, foreground=COLOR_TEXT, arrowcolor=COLOR_TEXT, bordercolor=COLOR_BORDER, lightcolor=COLOR_BORDER, darkcolor=COLOR_BORDER, selectbackground="#000000", selectforeground=COLOR_TEXT)
        style.map("Dark.TCombobox", fieldbackground=[("readonly", "#000000"), ("focus", "#000000"), ("!disabled", "#000000")], foreground=[("readonly", COLOR_TEXT), ("focus", COLOR_TEXT), ("!disabled", COLOR_TEXT)], selectbackground=[("readonly", "#000000"), ("focus", "#000000")], selectforeground=[("readonly", COLOR_TEXT), ("focus", COLOR_TEXT)])
        style.configure("TSpinbox", fieldbackground="#000000", background=COLOR_PANEL_2, foreground=COLOR_TEXT, selectbackground="#000000", selectforeground=COLOR_TEXT)
        style.map("TSpinbox", fieldbackground=[("readonly", "#000000"), ("focus", "#000000"), ("!disabled", "#000000")], foreground=[("readonly", COLOR_TEXT), ("focus", COLOR_TEXT), ("!disabled", COLOR_TEXT)], selectbackground=[("readonly", "#000000"), ("focus", "#000000")], selectforeground=[("readonly", COLOR_TEXT), ("focus", COLOR_TEXT)])
        style.configure("TRadiobutton", background=COLOR_PANEL, foreground=COLOR_TEXT)
        style.map(
            "TRadiobutton",
            background=[("active", COLOR_PANEL), ("selected", COLOR_PANEL), ("!disabled", COLOR_PANEL)],
            foreground=[("active", COLOR_TEXT), ("selected", COLOR_TEXT), ("!disabled", COLOR_TEXT)],
        )
        self.root.option_add("*TCombobox*Listbox.background", COLOR_INPUT)
        self.root.option_add("*TCombobox*Listbox.foreground", COLOR_TEXT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", COLOR_ACCENT_DARK)
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        style.configure("Treeview", background=COLOR_INPUT, foreground=COLOR_TEXT, fieldbackground=COLOR_INPUT, bordercolor=COLOR_BORDER, rowheight=30, font=FONT_SMALL)
        style.configure("Treeview.Heading", background=COLOR_PANEL_2, foreground=COLOR_MUTED, relief="flat", font=FONT_SMALL)
        style.map("Treeview", background=[("selected", COLOR_ACCENT_DARK)], foreground=[("selected", "#ffffff")])
        style.configure("Material.Treeview", rowheight=106, background=COLOR_INPUT, foreground=COLOR_TEXT, fieldbackground=COLOR_INPUT)
        scrollbar_options = {
            "background": COLOR_PANEL_2,
            "troughcolor": COLOR_INPUT,
            "bordercolor": COLOR_BORDER,
            "lightcolor": COLOR_BORDER,
            "darkcolor": COLOR_BORDER,
            "arrowcolor": COLOR_TEXT,
            "relief": "flat",
            "borderwidth": 1,
        }
        for scrollbar_style in ("TScrollbar", "Vertical.TScrollbar", "Horizontal.TScrollbar"):
            style.configure(scrollbar_style, **scrollbar_options)
            style.map(
                scrollbar_style,
                background=[("active", COLOR_ACCENT_DARK), ("pressed", COLOR_ACCENT_DARK), ("!disabled", COLOR_PANEL_2)],
                troughcolor=[("!disabled", COLOR_INPUT)],
                arrowcolor=[("active", "#ffffff"), ("pressed", "#ffffff"), ("!disabled", COLOR_TEXT)],
            )

    def apply_dark_theme(self, widget):
        for child in widget.winfo_children():
            cls = child.winfo_class()
            try:
                if cls == "Frame":
                    child.configure(bg=COLOR_PANEL)
                elif cls == "Labelframe":
                    child.configure(bg=COLOR_PANEL, fg=COLOR_MUTED, bd=1, relief="solid", highlightbackground=COLOR_BORDER)
                elif cls == "Label":
                    child.configure(bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_BODY)
                elif cls == "Button":
                    child.configure(
                        bg=COLOR_CARD,
                        fg=COLOR_TEXT,
                        activebackground=COLOR_ACCENT_DARK,
                        activeforeground="#ffffff",
                        relief="flat",
                        bd=0,
                        padx=12,
                        pady=7,
                        font=FONT_BODY,
                    )
                elif cls == "Entry":
                    child.configure(bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT, relief="flat", bd=1, highlightthickness=1, highlightbackground=COLOR_BORDER, font=FONT_BODY)
                elif cls == "Text":
                    child.configure(bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT, relief="flat", bd=1, highlightthickness=1, highlightbackground=COLOR_BORDER, font=FONT_BODY, padx=8, pady=8)
                elif cls == "Canvas":
                    child.configure(bg=COLOR_INPUT)
            except Exception:
                pass
            self.apply_dark_theme(child)

    def build_ui(self):
        menu = Menu(self.root)
        file_menu = Menu(menu, tearoff=0)
        file_menu.add_command(label="导入批量 CSV", command=self.import_csv)
        file_menu.add_command(label="选择输出目录", command=self.choose_output_dir)
        file_menu.add_command(label="查看卡密授权", command=self.open_license_status)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_close)
        menu.add_cascade(label="文件", menu=file_menu)
        self.root.config(menu=menu)

        top = Frame(self.root, padx=14, pady=10, bg=COLOR_BG)
        top.pack(fill=X)
        Label(top, text="AI 视频内容工作台", font=FONT_TITLE, bg=COLOR_BG, fg=COLOR_TEXT).pack(side=LEFT)
        Button(top, text="配置 AI", command=self.open_ai_settings, bg=COLOR_ACCENT_DARK).pack(side=LEFT, padx=(18, 0))
        Button(top, text="打开输出目录", command=self.open_output_dir).pack(side=LEFT, padx=(8, 0))
        Label(top, textvariable=self.status_var, anchor="e", bg=COLOR_BG, fg=COLOR_MUTED, font=FONT_SMALL).pack(side=RIGHT)

        shell = Frame(self.root, padx=14, bg=COLOR_BG)
        shell.pack(fill=BOTH, expand=True, pady=(0, 8))

        nav = Frame(shell, width=190, padx=10, pady=14, bg=COLOR_NAV, highlightthickness=1, highlightbackground=COLOR_BORDER)
        nav.pack(side=LEFT, fill=Y)
        nav.pack_propagate(False)
        Label(nav, text=APP_NAME, font=("Microsoft YaHei UI", 18, "bold"), anchor="w", bg=COLOR_NAV, fg=COLOR_TEXT).pack(fill=X)
        Label(nav, text="解析 / 改写 / 生图 / 视频", font=FONT_SMALL, anchor="w", bg=COLOR_NAV, fg=COLOR_MUTED).pack(fill=X, pady=(2, 18))

        self.nav_buttons = {}
        for key, text in (
            ("agent", "Agent 对话"),
            ("parser", "视频解析"),
            ("rewrite", "文案改写"),
            ("image", "图片生成"),
            ("generate", "视频生成"),
            ("assets", "资产库"),
            ("tasks", "任务队列"),
        ):
            button = Button(
                nav,
                text=text,
                anchor="w",
                command=lambda name=key: self.show_section(name),
                bg=COLOR_NAV,
                fg=COLOR_MUTED,
                activebackground=COLOR_PANEL_2,
                activeforeground=COLOR_TEXT,
                relief="flat",
                bd=0,
                padx=14,
                pady=10,
                font=FONT_BODY,
            )
            button.pack(fill=X, pady=4)
            self.nav_buttons[key] = button

        self.workspace = Frame(shell, bg=COLOR_BG)
        self.workspace.pack(side=RIGHT, fill=BOTH, expand=True, padx=(10, 0))

        self.parser_tab = Frame(self.workspace, padx=8, pady=8)
        self.agent_tab = Frame(self.workspace, padx=8, pady=8)
        self.rewrite_tab = Frame(self.workspace, padx=8, pady=8)
        self.image_tab = Frame(self.workspace, padx=8, pady=8)
        self.generate_tab = Frame(self.workspace, padx=8, pady=8)
        self.assets_tab = Frame(self.workspace, padx=8, pady=8)
        self.tasks_tab = Frame(self.workspace, padx=8, pady=8)
        self.sections = {
            "agent": self.agent_tab,
            "parser": self.parser_tab,
            "rewrite": self.rewrite_tab,
            "image": self.image_tab,
            "generate": self.generate_tab,
            "assets": self.assets_tab,
            "tasks": self.tasks_tab,
        }

        self.build_agent_tab(self.agent_tab)
        self.build_parser_tab(self.parser_tab)
        self.build_rewrite_tab(self.rewrite_tab)
        self.build_image_tab(self.image_tab)
        self.build_generate_tab(self.generate_tab)
        self.build_assets_tab(self.assets_tab)
        self.build_tasks_tab(self.tasks_tab)
        self.show_section("parser")

        log_box = LabelFrame(self.root, text="运行日志", padx=10, pady=8, bg=COLOR_PANEL, fg=COLOR_MUTED)
        log_box.pack(fill=X, padx=14, pady=(0, 12))
        self.log_text = Text(log_box, height=4, wrap="word")
        self.log_text.pack(fill=X)
        self.apply_dark_theme(self.root)

    def show_section(self, name):
        previous_section = getattr(self, "current_section", "")
        self.current_section = name
        for frame in self.sections.values():
            frame.pack_forget()
        frame = self.sections.get(name, self.parser_tab)
        frame.pack(fill=BOTH, expand=True)
        for key, button in self.nav_buttons.items():
            if key == name:
                button.configure(bg=COLOR_ACCENT_DARK, fg="#ffffff", relief="flat")
            else:
                button.configure(bg=COLOR_NAV, fg=COLOR_MUTED, relief="flat")
        section_names = {
            "agent": "Agent 对话",
            "parser": "视频解析",
            "rewrite": "文案改写",
            "image": "图片生成",
            "generate": "视频生成",
            "assets": "资产库",
            "tasks": "任务队列",
        }
        if previous_section and previous_section != name and hasattr(self, "log_text"):
            self.log(f"切换页面：{section_names.get(name, name)}")

    def build_agent_tab(self, parent):
        left = Frame(parent, width=240)
        left.pack(side=LEFT, fill=Y)
        left.pack_propagate(False)
        actions = Frame(left)
        actions.pack(fill=X)
        Button(actions, text="新建对话", command=self.create_agent_conversation).pack(side=LEFT)
        Button(actions, text="删除对话", command=self.delete_agent_conversation).pack(side=LEFT, padx=(8, 0))
        self.agent_conversation_list = Listbox(
            left,
            bg=COLOR_INPUT,
            fg=COLOR_TEXT,
            selectbackground=COLOR_ACCENT_DARK,
            selectforeground="#ffffff",
            activestyle="none",
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            font=FONT_SMALL,
        )
        self.agent_conversation_list.pack(fill=BOTH, expand=True, pady=(8, 0))
        self.agent_conversation_list.bind("<<ListboxSelect>>", lambda _event: self.on_agent_conversation_select())
        self.agent_conversation_list.bind("<Button-3>", self.show_agent_conversation_menu)

        right = Frame(parent)
        right.pack(side=RIGHT, fill=BOTH, expand=True, padx=(10, 0))
        chat_box = LabelFrame(right, text="智能体对话", padx=8, pady=8)
        chat_box.pack(fill=BOTH, expand=True)
        chat_shell = Frame(chat_box)
        chat_shell.pack(fill=BOTH, expand=True)
        self.agent_chat_text = Text(chat_shell, wrap="word", height=20)
        self.agent_chat_text.pack(side=LEFT, fill=BOTH, expand=True)
        agent_chat_scrollbar = ttk.Scrollbar(chat_shell, orient="vertical", command=self.agent_chat_text.yview)
        agent_chat_scrollbar.pack(side=RIGHT, fill=Y)
        self.agent_chat_text.configure(yscrollcommand=agent_chat_scrollbar.set)
        self.agent_chat_text.tag_configure("user_role", foreground=COLOR_ACCENT, font=("Microsoft YaHei UI", 10, "bold"), spacing1=8, spacing3=2)
        self.agent_chat_text.tag_configure("assistant_role", foreground=COLOR_SUCCESS, font=("Microsoft YaHei UI", 10, "bold"), spacing1=8, spacing3=2)
        self.agent_chat_text.tag_configure("message_body", foreground=COLOR_TEXT, lmargin1=14, lmargin2=14, spacing3=8)
        self.agent_chat_text.configure(state="disabled")
        input_row = Frame(right)
        input_row.pack(fill=X, pady=(10, 0), ipady=4)
        self.agent_entry = Entry(input_row, textvariable=self.agent_input_var, font=("Microsoft YaHei UI", 11), relief="flat", bd=1)
        self.agent_entry.pack(side=LEFT, fill=X, expand=True, ipady=8)
        self.agent_entry.bind("<KeyPress>", self.handle_prompt_keypress)
        self.agent_entry.bind("<KeyRelease>", self.handle_prompt_keyrelease)
        self.agent_entry.bind("<Return>", lambda _event: self.send_agent_message())
        self.agent_entry.bind("<Escape>", lambda _event: self.hide_material_suggestions())
        Button(input_row, text="上传附件", command=self.choose_agent_attachments).pack(side=LEFT, padx=(8, 0), ipady=3)
        Button(input_row, text="清空附件", command=self.clear_agent_attachments).pack(side=LEFT, padx=(8, 0), ipady=3)
        Button(input_row, text="发送", command=self.send_agent_message).pack(side=LEFT, padx=(8, 0), ipady=3)
        Label(right, textvariable=self.agent_attachment_var, anchor="w", fg=COLOR_MUTED).pack(fill=X, pady=(2, 0))
        self.refresh_agent_conversations()
        self.show_agent_conversation()

    def new_agent_conversation_object(self):
        return AgentConversation(
            id=uuid.uuid4().hex[:12],
            title="新对话",
            messages=[],
            created_at=now_text(),
            updated_at=now_text(),
        )

    def refresh_agent_conversations(self):
        if not hasattr(self, "agent_conversation_list"):
            return
        self.agent_conversation_list.delete(0, END)
        for item in self.agent_conversations:
            self.agent_conversation_list.insert(END, compact_text(item.title or "新对话", 26))
        for index, item in enumerate(self.agent_conversations):
            if item.id == self.current_agent_conversation_id:
                self.agent_conversation_list.selection_set(index)
                self.agent_conversation_list.activate(index)
                break

    def current_agent_conversation(self):
        return next((item for item in self.agent_conversations if item.id == self.current_agent_conversation_id), None)

    def on_agent_conversation_select(self):
        selection = self.agent_conversation_list.curselection()
        if not selection:
            return
        index = selection[0]
        if index >= len(self.agent_conversations):
            return
        self.current_agent_conversation_id = self.agent_conversations[index].id
        self.show_agent_conversation()

    def show_agent_conversation(self):
        if not hasattr(self, "agent_chat_text"):
            return
        conversation = self.current_agent_conversation()
        self.agent_chat_text.configure(state="normal")
        self.agent_chat_text.delete("1.0", END)
        if conversation:
            for message in conversation.messages:
                if message.get("role") == "user":
                    self.agent_chat_text.insert(END, "用户：\n", "user_role")
                else:
                    self.agent_chat_text.insert(END, "智能体：\n", "assistant_role")
                content = message.get("content", "")
                if content:
                    self.agent_chat_text.insert(END, f"{content}\n\n", "message_body")
        self.agent_chat_text.configure(state="disabled")
        self.agent_chat_text.see(END)

    def append_agent_stream_delta(self, conversation_id, delta):
        if conversation_id != self.current_agent_conversation_id or not hasattr(self, "agent_chat_text"):
            return
        self.agent_chat_text.configure(state="normal")
        self.agent_chat_text.insert(END, delta, "message_body")
        self.agent_chat_text.configure(state="disabled")
        self.agent_chat_text.see(END)

    def create_agent_conversation(self):
        conversation = self.new_agent_conversation_object()
        self.agent_conversations.insert(0, conversation)
        self.current_agent_conversation_id = conversation.id
        self.persist_agent_conversations()
        self.refresh_agent_conversations()
        self.show_agent_conversation()
        self.log("已新建 Agent 对话")

    def delete_agent_conversation(self):
        conversation = self.current_agent_conversation()
        if not conversation:
            return
        if not messagebox.askyesno("删除对话", "确定删除当前 Agent 对话？"):
            return
        self.agent_conversations = [item for item in self.agent_conversations if item.id != conversation.id]
        if not self.agent_conversations:
            self.agent_conversations.append(self.new_agent_conversation_object())
        self.current_agent_conversation_id = self.agent_conversations[0].id
        self.persist_agent_conversations()
        self.refresh_agent_conversations()
        self.show_agent_conversation()
        self.log("已删除 Agent 对话")

    def show_agent_conversation_menu(self, event):
        index = self.agent_conversation_list.nearest(event.y)
        if index < 0 or index >= len(self.agent_conversations):
            return
        self.agent_conversation_list.selection_clear(0, END)
        self.agent_conversation_list.selection_set(index)
        self.agent_conversation_list.activate(index)
        self.current_agent_conversation_id = self.agent_conversations[index].id
        self.show_agent_conversation()
        menu = Menu(self.root, tearoff=0)
        menu.add_command(label="重命名对话", command=self.rename_agent_conversation)
        menu.add_command(label="删除对话", command=self.delete_agent_conversation)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def rename_agent_conversation(self):
        conversation = self.current_agent_conversation()
        if not conversation:
            return
        win = Toplevel(self.root)
        win.title("重命名对话")
        win.geometry("360x130")
        title_var = StringVar(value=conversation.title)
        row = Frame(win, padx=10, pady=14)
        row.pack(fill=X)
        Label(row, text="对话名称", width=10, anchor="w").pack(side=LEFT)
        Entry(row, textvariable=title_var).pack(side=LEFT, fill=X, expand=True)

        def save():
            title = title_var.get().strip()
            if title:
                conversation.title = compact_text(title, 28)
                conversation.updated_at = now_text()
                self.persist_agent_conversations()
                self.refresh_agent_conversations()
                self.log(f"Agent 对话已重命名：{conversation.title}")
            win.destroy()

        actions = Frame(win, padx=10, pady=10)
        actions.pack(fill=X)
        Button(actions, text="保存", command=save).pack(side=RIGHT)
        Button(actions, text="取消", command=win.destroy).pack(side=RIGHT, padx=(0, 8))

    def update_agent_attachment_label(self):
        refs = self.resolve_prompt_refs(self.agent_input_var.get())
        names = []
        materials = self.materials_by_id()
        for ref in refs:
            if ref in materials:
                names.append(f"@{materials[ref].alias}")
        for path in self.agent_attachment_paths:
            names.append(Path(path).name)
        if names:
            self.agent_attachment_var.set(f"附件 {len(names)} 个：{', '.join(names[:4])}" + (" ..." if len(names) > 4 else ""))
        else:
            self.agent_attachment_var.set("未添加附件")

    def choose_agent_attachments(self):
        paths = filedialog.askopenfilenames(
            title="选择发给 Agent 的图片或文件",
            filetypes=[
                ("图片和文本文件", "*.png *.jpg *.jpeg *.webp *.bmp *.txt *.md *.csv *.json *.xml *.html *.htm *.srt *.py *.js *.ts *.css *.log"),
                ("所有文件", "*.*"),
            ],
        )
        if not paths:
            return
        existing = list(self.agent_attachment_paths)
        for path in paths:
            if path not in existing:
                existing.append(path)
        self.agent_attachment_paths = existing[:10]
        self.update_agent_attachment_label()
        self.log(f"Agent 已添加附件 {len(self.agent_attachment_paths)} 个")

    def clear_agent_attachments(self):
        self.agent_attachment_paths = []
        self.update_agent_attachment_label()

    def build_agent_user_message(self, content, attachment_paths):
        materials = self.materials_by_id()
        refs = self.resolve_prompt_refs(content)
        image_paths = []
        text_blocks = []
        display_files = []
        attachments = []
        for ref in refs:
            material = materials.get(ref)
            if material and Path(material.path).exists():
                image_paths.append(material.path)
                display_files.append(f"@{material.alias}")
                attachments.append({"kind": "material", "id": material.id, "alias": material.alias})
        for path in attachment_paths:
            path_obj = Path(path)
            if not path_obj.exists():
                continue
            display_files.append(path_obj.name)
            if is_image_file(path_obj):
                image_paths.append(str(path_obj))
                attachments.append({"kind": "file", "type": "image", "path": str(path_obj), "name": path_obj.name})
            else:
                text = read_text_attachment(path_obj)
                if text:
                    text_blocks.append(f"【文件：{path_obj.name}】\n{text}")
                    attachments.append({"kind": "file", "type": "text", "path": str(path_obj), "name": path_obj.name, "text": text})
                else:
                    text_blocks.append(f"【文件：{path_obj.name}】该文件不是可直接读取的文本格式，请根据文件名和用户描述判断。")
                    attachments.append({"kind": "file", "type": "unknown", "path": str(path_obj), "name": path_obj.name})
        final_text = content
        if text_blocks:
            final_text += "\n\n以下是用户上传文件内容：\n\n" + "\n\n".join(text_blocks)
        if image_paths:
            parts = [{"type": "text", "text": final_text or "请分析这些图片。"}]
            for path in image_paths[:MAX_REFERENCE_IMAGES]:
                parts.append({"type": "image_url", "image_url": {"url": data_uri_for_file(path)}})
            model_content = parts
        else:
            model_content = final_text
        display_content = content
        if display_files:
            display_content += "\n\n[附件：" + "，".join(display_files[:8]) + (" ..." if len(display_files) > 8 else "") + "]"
        return display_content, model_content, attachments

    def restore_agent_model_content(self, content, attachments):
        if not attachments:
            return content
        materials = self.materials_by_id()
        image_paths = []
        text_blocks = []
        for item in attachments:
            if not isinstance(item, dict):
                continue
            if item.get("kind") == "material":
                material = materials.get(text_value(item.get("id")))
                if material and Path(material.path).exists():
                    image_paths.append(material.path)
            elif item.get("type") == "image":
                path = Path(text_value(item.get("path")))
                if path.exists():
                    image_paths.append(str(path))
            elif item.get("type") == "text":
                name = text_value(item.get("name")) or Path(text_value(item.get("path"))).name
                text = text_value(item.get("text"))
                if not text:
                    text = read_text_attachment(text_value(item.get("path")))
                if text:
                    text_blocks.append(f"【文件：{name}】\n{text}")
        final_text = content
        if text_blocks:
            final_text += "\n\n以下是用户上传文件内容：\n\n" + "\n\n".join(text_blocks)
        if image_paths:
            parts = [{"type": "text", "text": final_text or "请分析这些图片。"}]
            for path in image_paths[:MAX_REFERENCE_IMAGES]:
                parts.append({"type": "image_url", "image_url": {"url": data_uri_for_file(path)}})
            return parts
        return final_text

    def send_agent_message(self):
        content = self.agent_input_var.get().strip()
        if not content and not self.agent_attachment_paths:
            return
        attachment_paths = list(self.agent_attachment_paths)
        display_content, model_content, attachments = self.build_agent_user_message(content, attachment_paths)
        conversation = self.current_agent_conversation()
        if not conversation:
            self.create_agent_conversation()
            conversation = self.current_agent_conversation()
        if conversation.title == "新对话":
            conversation.title = compact_text(content or "附件分析", 18)
        conversation.messages.append({"role": "user", "content": display_content, "model_content": model_content, "attachments": attachments})
        conversation.updated_at = now_text()
        self.agent_input_var.set("")
        self.agent_attachment_paths = []
        self.update_agent_attachment_label()
        self.persist_agent_conversations()
        self.refresh_agent_conversations()
        self.show_agent_conversation()
        self.log(f"Agent 对话发送：{conversation.id}")
        threading.Thread(target=self.agent_chat_worker, args=(conversation.id,), daemon=True).start()

    def agent_chat_worker(self, conversation_id):
        conversation = next((item for item in self.agent_conversations if item.id == conversation_id), None)
        if not conversation:
            return
        try:
            messages = [
                {
                    "role": "system",
                    "content": "你是极影AI工作台内置的智能体助手。你需要记住当前会话上下文，帮助用户完成短视频文案、图片提示词、Grok视频提示词、素材管理和软件使用问题。回答要简洁、可执行。",
                }
            ]
            for message in conversation.messages[-20:]:
                model_content = message.get("model_content")
                if model_content is None:
                    model_content = self.restore_agent_model_content(message.get("content", ""), message.get("attachments") or [])
                messages.append({"role": message.get("role", "user"), "content": model_content})
            assistant_message = {"role": "assistant", "content": ""}
            conversation.messages.append(assistant_message)
            conversation.updated_at = now_text()
            self.persist_agent_conversations()
            self.event_queue.put(("agent_response", conversation_id))

            def on_delta(delta):
                assistant_message["content"] += delta
                conversation.updated_at = now_text()
                self.event_queue.put(("agent_stream_delta", (conversation_id, delta)))

            api_key = text_value(self.settings.get("text_api_key")).strip()
            base_url = text_value(self.settings.get("text_base_url") or "https://api.openai.com/v1")
            try:
                result = chat_completion_messages_stream(messages, api_key, base_url, "gpt-5.5", on_delta)
            except Exception as stream_exc:
                if assistant_message["content"].strip():
                    raise
                self.event_queue.put(("log", f"Agent 流式回复失败，已自动切换普通回复：{stream_exc}"))
                result = chat_completion_messages(messages, api_key, base_url, "gpt-5.5")
                if result:
                    assistant_message["content"] = result
                    self.event_queue.put(("agent_stream_delta", (conversation_id, result)))
            if not result:
                raise RuntimeError("智能体没有返回内容")
            assistant_message["content"] = result
            conversation.updated_at = now_text()
            self.persist_agent_conversations()
            self.event_queue.put(("agent_stream_done", conversation_id))
            self.event_queue.put(("log", f"Agent 已回复：{conversation_id}"))
        except Exception as exc:
            if conversation.messages and conversation.messages[-1].get("role") == "assistant" and not conversation.messages[-1].get("content"):
                conversation.messages[-1]["content"] = f"回复失败：{exc}"
                conversation.updated_at = now_text()
                self.persist_agent_conversations()
                self.event_queue.put(("agent_response", conversation_id))
            self.event_queue.put(("log", f"Agent 对话失败：{exc}"))

    def build_parser_tab(self, parent):
        input_row = Frame(parent)
        input_row.pack(fill=X)
        Label(input_row, text="视频链接").pack(side=LEFT)
        Entry(input_row, textvariable=self.parse_url_var).pack(side=LEFT, padx=8, fill=X, expand=True)
        Button(input_row, text="解析视频", command=self.parse_video_async).pack(side=LEFT)
        Label(input_row, textvariable=self.parser_status_var).pack(side=RIGHT, padx=(8, 0))

        download_row = Frame(parent)
        download_row.pack(fill=X, pady=(8, 0))
        Label(download_row, text="下载目录").pack(side=LEFT)
        Entry(download_row, textvariable=self.parser_download_dir_var).pack(side=LEFT, padx=8, fill=X, expand=True)
        Button(download_row, text="选择目录", command=self.choose_parser_download_dir).pack(side=LEFT)
        Button(download_row, text="清空列表", command=self.clear_parsed_videos).pack(side=LEFT, padx=(8, 0))

        action_row = Frame(parent)
        action_row.pack(fill=X, pady=(8, 0))
        Button(action_row, text="提取文案", command=self.extract_selected_video_text).pack(side=LEFT)
        Button(action_row, text="加入素材库", command=self.add_selected_parsed_to_materials).pack(side=LEFT, padx=6)
        Button(action_row, text="文案填入改写页", command=self.use_selected_parsed_caption).pack(side=LEFT)

        columns = ("index", "title", "caption", "video", "local", "updated")
        self.parsed_tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="browse", height=10)
        for key, title, width in (
            ("index", "序号", 56),
            ("title", "标题/平台文案", 220),
            ("caption", "音频文案/提取文案", 260),
            ("video", "视频地址", 260),
            ("local", "本地文件", 180),
            ("updated", "时间", 140),
        ):
            self.parsed_tree.heading(key, text=title)
            self.parsed_tree.column(key, width=width, anchor="center" if key == "index" else "w")
        self.parsed_tree.pack(fill=BOTH, expand=True, pady=(8, 0))
        self.parsed_tree.bind("<<TreeviewSelect>>", lambda _event: self.show_selected_parsed_detail())
        self.parsed_tree.bind("<Button-3>", self.show_parsed_context_menu)

        detail_box = LabelFrame(parent, text="解析详情 / 文案", padx=8, pady=8)
        detail_box.pack(fill=X, pady=(8, 0))
        self.parsed_detail_text = Text(detail_box, height=6, wrap="word")
        self.parsed_detail_text.pack(fill=X)

    def build_generate_tab(self, parent):
        left = Frame(parent, width=420)
        left.pack(side=LEFT, fill=Y)
        left.pack_propagate(False)

        create_box = LabelFrame(left, text="生成参数", padx=8, pady=8)
        create_box.pack(fill=X)
        Label(create_box, text="提示词（可写 @素材名 引用，也可选中素材）").pack(anchor="w")
        self.prompt_text = Text(create_box, height=12, wrap="word")
        self.prompt_text.pack(fill=X, pady=(4, 8))
        self.prompt_text.bind("<KeyPress>", self.handle_prompt_keypress)
        self.prompt_text.bind("<KeyRelease>", self.handle_prompt_keyrelease)
        self.prompt_text.bind("<Button-1>", lambda _event: self.hide_material_suggestions())
        self.prompt_text.bind("<Escape>", lambda _event: self.hide_material_suggestions())

        ref_row = Frame(create_box)
        ref_row.pack(fill=X, pady=(0, 8))
        Button(ref_row, text="上传参考图", command=self.choose_video_references).pack(side=LEFT)
        Label(ref_row, textvariable=self.video_reference_var, anchor="w", fg=COLOR_MUTED).pack(side=LEFT, padx=(8, 0), fill=X, expand=True)
        self.video_reference_frame = Frame(create_box)
        self.video_reference_frame.pack(fill=X, pady=(0, 8))

        row = Frame(create_box)
        row.pack(fill=X, pady=2)
        Label(row, text="比例").pack(side=LEFT)
        ttk.Combobox(row, textvariable=self.aspect_var, values=["16:9", "9:16", "1:1", "4:3", "3:4", "3:2", "2:3"], width=8, state="readonly", style="Dark.TCombobox").pack(side=LEFT, padx=(8, 14))
        Label(row, text="时长").pack(side=LEFT)
        ttk.Spinbox(row, textvariable=self.duration_var, from_=1, to=15, width=6).pack(side=LEFT, padx=(8, 14))
        Label(row, text="分辨率").pack(side=LEFT)
        ttk.Combobox(row, textvariable=self.resolution_var, values=["720p", "480p"], width=8, state="readonly", style="Dark.TCombobox").pack(side=LEFT, padx=(8, 0))
        Button(create_box, text="添加到批量任务", command=self.add_task_from_form).pack(fill=X, pady=(10, 0))

        output_box = LabelFrame(left, text="输出目录", padx=8, pady=8)
        output_box.pack(fill=X, pady=(10, 0))
        Entry(output_box, textvariable=self.output_dir_var).pack(fill=X)
        Button(output_box, text="选择目录", command=self.choose_output_dir).pack(side=LEFT, pady=(8, 0))
        Button(output_box, text="打开目录", command=self.open_output_dir).pack(side=LEFT, padx=6, pady=(8, 0))

        right = LabelFrame(parent, text="资产引用", padx=8, pady=8)
        right.pack(side=RIGHT, fill=BOTH, expand=True, padx=(10, 0))
        filter_row = Frame(right)
        filter_row.pack(fill=X)
        Label(filter_row, text="分类").pack(side=LEFT, padx=(0, 4))
        self.generate_asset_type_combo = ttk.Combobox(filter_row, textvariable=self.generate_asset_type_var, values=self.group_filter_values(), width=10, state="readonly", style="Dark.TCombobox")
        self.generate_asset_type_combo.pack(side=LEFT)
        self.generate_asset_type_var.trace_add("write", lambda *_: self.refresh_materials())
        Entry(right, textvariable=self.generate_search_var).pack(fill=X, pady=(8, 4))
        self.generate_search_var.trace_add("write", lambda *_: self.refresh_materials())
        grid_shell = Frame(right)
        grid_shell.pack(fill=BOTH, expand=True)
        self.generate_asset_canvas = Canvas(grid_shell, highlightthickness=0)
        self.generate_asset_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        generate_scrollbar = ttk.Scrollbar(grid_shell, orient="vertical", command=self.generate_asset_canvas.yview)
        generate_scrollbar.pack(side=RIGHT, fill=Y)
        self.generate_asset_canvas.configure(yscrollcommand=generate_scrollbar.set)
        self.generate_asset_grid = Frame(self.generate_asset_canvas)
        self.generate_asset_window = self.generate_asset_canvas.create_window((0, 0), window=self.generate_asset_grid, anchor="nw")
        self.generate_asset_grid.bind(
            "<Configure>",
            lambda _event: self.generate_asset_canvas.configure(scrollregion=self.generate_asset_canvas.bbox("all")),
        )
        self.generate_asset_canvas.bind(
            "<Configure>",
            lambda event: self.generate_asset_canvas.itemconfigure(self.generate_asset_window, width=event.width),
        )
        self.generate_selected_material_ids = set()
        self.material_suggest_popup = None
        self.material_suggest_listbox = None
        self.material_suggest_ids = []
        self.material_suggest_start_index = ""

    def build_rewrite_tab(self, parent):
        top = Frame(parent)
        top.pack(fill=BOTH, expand=True)
        left = LabelFrame(top, text="原始文案", padx=8, pady=8)
        left.pack(side=LEFT, fill=BOTH, expand=True)
        self.rewrite_input_text = Text(left, height=18, wrap="word")
        self.rewrite_input_text.pack(fill=BOTH, expand=True)

        middle = Frame(top, width=130, padx=8)
        middle.pack(side=LEFT, fill=Y)
        middle.pack_propagate(False)
        Button(middle, text="自定义模板", command=lambda: self.open_prompt_template_manager("rewrite")).pack(fill=X, pady=(20, 6))
        self.rewrite_template_combo = ttk.Combobox(middle, textvariable=self.rewrite_template_var, values=self.prompt_template_names("rewrite"), width=14, state="readonly", style="Dark.TCombobox")
        self.rewrite_template_combo.pack(fill=X, pady=(0, 12))
        Button(middle, text="历史记录", command=self.show_rewrite_history).pack(fill=X, pady=(0, 12))
        Button(middle, text="改写文案", command=self.rewrite_copy_async).pack(fill=X, pady=(8, 8))
        Button(middle, text="填入生成页", command=self.use_rewrite_output).pack(fill=X)

        right = LabelFrame(top, text="改写结果", padx=8, pady=8)
        right.pack(side=RIGHT, fill=BOTH, expand=True)
        self.rewrite_output_text = Text(right, height=18, wrap="word")
        self.rewrite_output_text.pack(fill=BOTH, expand=True)

    def build_image_tab(self, parent):
        left = Frame(parent, width=400)
        left.pack(side=LEFT, fill=Y)
        left.pack_propagate(False)
        prompt_box = LabelFrame(left, text="图片提示词", padx=10, pady=10)
        prompt_box.pack(fill=BOTH, expand=True)
        template_row = Frame(prompt_box)
        template_row.pack(fill=X, pady=(0, 8))
        Button(template_row, text="自定义图片提示词模板", command=lambda: self.open_prompt_template_manager("image")).pack(side=LEFT)
        self.image_template_combo = ttk.Combobox(template_row, textvariable=self.image_template_var, values=self.prompt_template_names("image"), width=18, state="readonly", style="Dark.TCombobox")
        self.image_template_combo.pack(side=LEFT, padx=(8, 0), fill=X, expand=True)
        self.image_template_combo.bind("<<ComboboxSelected>>", lambda _event: self.apply_selected_image_template())
        self.image_prompt_text = Text(prompt_box, height=10, wrap="word")
        self.image_prompt_text.pack(fill=BOTH, expand=True)
        self.image_prompt_text.bind("<KeyPress>", self.handle_prompt_keypress)
        self.image_prompt_text.bind("<KeyRelease>", self.handle_prompt_keyrelease)
        self.image_prompt_text.bind("<Button-1>", lambda _event: self.hide_material_suggestions())
        self.image_prompt_text.bind("<Escape>", lambda _event: self.hide_material_suggestions())
        param_box = LabelFrame(prompt_box, text="图片参数", padx=8, pady=8)
        param_box.pack(fill=X, pady=(8, 0))
        quality_row = Frame(param_box)
        quality_row.pack(fill=X)
        Label(quality_row, text="质量", width=8, anchor="w").pack(side=LEFT)
        for value in IMAGE_QUALITY_OPTIONS:
            ttk.Radiobutton(
                quality_row,
                text=IMAGE_QUALITY_LABELS.get(value, value),
                value=value,
                variable=self.image_quality_var,
            ).pack(side=LEFT, padx=(0, 8))

        size_row = Frame(param_box)
        size_row.pack(fill=X, pady=(8, 0))
        Label(size_row, text="尺寸", width=8, anchor="w").pack(side=LEFT)
        Label(size_row, text="W").pack(side=LEFT)
        Entry(size_row, textvariable=self.image_width_var, width=8).pack(side=LEFT, padx=(4, 10))
        Label(size_row, text="H").pack(side=LEFT)
        Entry(size_row, textvariable=self.image_height_var, width=8).pack(side=LEFT, padx=(4, 10))
        Label(size_row, textvariable=self.image_size_var, fg=COLOR_MUTED).pack(side=LEFT)

        aspect_box = LabelFrame(param_box, text="宽高比", padx=4, pady=4)
        aspect_box.pack(fill=X, pady=(8, 0))
        for index, (label, width, height) in enumerate(IMAGE_ASPECT_PRESETS):
            button = Button(
                aspect_box,
                text=label,
                width=9,
                command=lambda lbl=label, w=width, h=height: self.set_image_aspect_size(lbl, w, h),
            )
            button.grid(row=index // 3, column=index % 3, padx=3, pady=3, sticky="ew")
        for column in range(3):
            aspect_box.grid_columnconfigure(column, weight=1)

        row = Frame(prompt_box)
        row.pack(fill=X, pady=(8, 0))
        Button(row, text="上传参考图", command=self.choose_image_references).pack(side=LEFT)
        Button(row, text="加入任务并生成", command=self.generate_image_async).pack(side=LEFT, padx=(8, 0))
        Label(row, textvariable=self.image_status_var).pack(side=RIGHT)

        Label(prompt_box, textvariable=self.image_reference_var, anchor="w", fg=COLOR_MUTED).pack(fill=X, pady=(8, 0))
        self.image_reference_frame = Frame(prompt_box)
        self.image_reference_frame.pack(fill=X, pady=(6, 0))

        middle = LabelFrame(parent, text="资产引用", padx=8, pady=8)
        middle.pack(side=LEFT, fill=BOTH, expand=True, padx=(10, 0))
        filter_row = Frame(middle)
        filter_row.pack(fill=X)
        Label(filter_row, text="分类").pack(side=LEFT, padx=(0, 4))
        self.image_asset_type_combo = ttk.Combobox(filter_row, textvariable=self.image_asset_type_var, values=self.group_filter_values(), width=10, state="readonly", style="Dark.TCombobox")
        self.image_asset_type_combo.pack(side=LEFT)
        self.image_asset_type_var.trace_add("write", lambda *_: self.refresh_materials())
        Entry(middle, textvariable=self.image_search_var).pack(fill=X, pady=(8, 4))
        self.image_search_var.trace_add("write", lambda *_: self.refresh_materials())
        grid_shell = Frame(middle)
        grid_shell.pack(fill=BOTH, expand=True)
        self.image_asset_canvas = Canvas(grid_shell, highlightthickness=0)
        self.image_asset_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        image_asset_scrollbar = ttk.Scrollbar(grid_shell, orient="vertical", command=self.image_asset_canvas.yview)
        image_asset_scrollbar.pack(side=RIGHT, fill=Y)
        self.image_asset_canvas.configure(yscrollcommand=image_asset_scrollbar.set)
        self.image_asset_grid = Frame(self.image_asset_canvas)
        self.image_asset_window = self.image_asset_canvas.create_window((0, 0), window=self.image_asset_grid, anchor="nw")
        self.image_asset_grid.bind(
            "<Configure>",
            lambda _event: self.image_asset_canvas.configure(scrollregion=self.image_asset_canvas.bbox("all")),
        )
        self.image_asset_refresh_after = None
        self.image_asset_last_columns = 0
        self.image_asset_canvas.bind("<Configure>", self.on_image_asset_canvas_configure)
        self.image_selected_material_ids = set()

        task_box = LabelFrame(parent, text="图片任务队列", padx=10, pady=10, width=420)
        task_box.pack(side=RIGHT, fill=BOTH, expand=False, padx=(10, 0))
        task_box.pack_propagate(False)
        columns = ("status", "prompt", "refs", "job", "output", "updated")
        task_tree_shell = Frame(task_box)
        task_tree_shell.pack(fill=BOTH, expand=True)
        self.image_task_tree = ttk.Treeview(task_tree_shell, columns=columns, show="headings", selectmode="browse", height=16)
        for key, title, width in (
            ("status", "状态", 78),
            ("prompt", "提示词", 190),
            ("refs", "参考图", 60),
            ("job", "任务ID", 120),
            ("output", "结果", 140),
            ("updated", "更新时间", 140),
        ):
            self.image_task_tree.heading(key, text=title)
            self.image_task_tree.column(key, width=width, minwidth=width, stretch=False, anchor="center" if key in ("status", "refs") else "w")
        self.image_task_tree.pack(side=LEFT, fill=BOTH, expand=True)
        image_task_y_scrollbar = ttk.Scrollbar(task_tree_shell, orient="vertical", command=self.image_task_tree.yview)
        image_task_y_scrollbar.pack(side=RIGHT, fill=Y)
        image_task_x_scrollbar = ttk.Scrollbar(task_box, orient="horizontal", command=self.image_task_tree.xview)
        image_task_x_scrollbar.pack(fill=X)
        self.image_task_tree.configure(yscrollcommand=image_task_y_scrollbar.set, xscrollcommand=image_task_x_scrollbar.set)
        self.image_task_tree.bind("<<TreeviewSelect>>", lambda _event: self.show_selected_image_task())
        self.image_task_tree.bind("<Double-Button-1>", self.reuse_image_task_from_event)
        self.image_task_tree.bind("<Button-3>", self.show_image_task_context_menu)

        self.generated_image_label = None
        self.add_generated_image_button = None

    def build_assets_tab(self, parent):
        toolbar = Frame(parent)
        toolbar.pack(fill=X)
        Button(toolbar, text="上传图片", command=self.add_materials).pack(side=LEFT)
        Button(toolbar, text="配置分组", command=self.configure_material_groups).pack(side=LEFT, padx=(0, 6))
        Label(toolbar, text="分类").pack(side=LEFT, padx=(16, 4))
        self.asset_type_combo = ttk.Combobox(toolbar, textvariable=self.asset_type_var, values=self.group_filter_values(), width=10, state="readonly", style="Dark.TCombobox")
        self.asset_type_combo.pack(side=LEFT)
        self.asset_type_var.trace_add("write", lambda *_: self.refresh_materials())
        Entry(toolbar, textvariable=self.search_var).pack(side=LEFT, fill=X, expand=True, padx=(10, 0))
        self.search_var.trace_add("write", lambda *_: self.refresh_materials())

        grid_shell = Frame(parent)
        grid_shell.pack(fill=BOTH, expand=True, pady=(8, 0))
        self.asset_canvas = Canvas(grid_shell, highlightthickness=0)
        self.asset_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        asset_scrollbar = ttk.Scrollbar(grid_shell, orient="vertical", command=self.asset_canvas.yview)
        asset_scrollbar.pack(side=RIGHT, fill=Y)
        self.asset_canvas.configure(yscrollcommand=asset_scrollbar.set)
        self.asset_grid = Frame(self.asset_canvas)
        self.asset_grid_window = self.asset_canvas.create_window((0, 0), window=self.asset_grid, anchor="nw")
        self.asset_grid.bind(
            "<Configure>",
            lambda _event: self.asset_canvas.configure(scrollregion=self.asset_canvas.bbox("all")),
        )
        self.asset_canvas.bind(
            "<Configure>",
            lambda event: self.asset_canvas.itemconfigure(self.asset_grid_window, width=event.width),
        )
        self.asset_selected_material_ids = set()

    def build_material_tree(self, parent):
        material_box = LabelFrame(parent, text="资产库", padx=8, pady=8)
        material_box.pack(side=LEFT, fill=BOTH, expand=True)
        action_row = Frame(material_box)
        action_row.pack(fill=X)
        Button(action_row, text="上传图片", command=self.add_materials).pack(side=LEFT)
        Button(action_row, text="删除素材", command=self.delete_selected_materials).pack(side=LEFT)
        Entry(material_box, textvariable=self.search_var).pack(fill=X, pady=(8, 4))
        self.search_var.trace_add("write", lambda *_: self.refresh_materials())
        self.material_tree = ttk.Treeview(
            material_box,
            columns=("alias", "tags", "filename"),
            show="tree headings",
            selectmode="extended",
            height=10,
            style="Material.Treeview",
        )
        self.material_tree.heading("#0", text="预览")
        self.material_tree.heading("alias", text="引用名")
        self.material_tree.heading("tags", text="分类/标签")
        self.material_tree.heading("filename", text="文件")
        self.material_tree.column("#0", width=112, minwidth=100, stretch=False, anchor="center")
        self.material_tree.column("alias", width=100, minwidth=70, stretch=False)
        self.material_tree.column("tags", width=120, minwidth=80)
        self.material_tree.column("filename", width=220, minwidth=120)
        self.material_tree.pack(fill=BOTH, expand=True)
        self.material_tree.bind("<Double-Button-1>", lambda _event: self.insert_selected_material_refs())

    def build_tasks_tab(self, parent):
        task_actions = Frame(parent)
        task_actions.pack(fill=X)
        Button(task_actions, text="全选", command=self.toggle_all_video_tasks).pack(side=LEFT)
        Button(task_actions, text="开始任务", command=self.start_checked_or_selected_tasks).pack(side=LEFT, padx=6)
        Button(task_actions, text="暂停任务", command=self.pause_checked_or_selected_tasks).pack(side=LEFT)
        Button(task_actions, text="删除任务", command=self.delete_selected_tasks).pack(side=LEFT, padx=6)
        Button(task_actions, text="提交队列", command=self.queue_all_pending).pack(side=LEFT, padx=(12, 0))
        Button(task_actions, text="重试失败", command=self.retry_failed).pack(side=LEFT, padx=6)
        Button(task_actions, text="批量保存已完成视频", command=self.save_done_videos).pack(side=LEFT)
        Button(task_actions, text="复用选中任务", command=self.reuse_selected_task).pack(side=LEFT, padx=6)

        columns = ("index", "checked", "status", "prompt", "params", "refs", "request", "output", "updated")
        self.task_tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="extended")
        for key, title, width in (
            ("index", "序号", 56),
            ("checked", "选择", 58),
            ("status", "状态", 88),
            ("prompt", "提示词", 360),
            ("params", "参数", 120),
            ("refs", "参考图", 90),
            ("request", "Request ID", 150),
            ("output", "结果/问题", 260),
            ("updated", "更新时间", 140),
        ):
            self.task_tree.heading(key, text=title)
            self.task_tree.column(key, width=width, anchor="center" if key in ("index", "checked", "status", "params", "refs", "updated") else "w")
        self.task_tree.pack(fill=BOTH, expand=True, pady=(8, 0))
        self.task_tree.bind("<Button-1>", self.handle_task_tree_click)
        self.task_tree.bind("<Double-Button-1>", lambda _event: self.reuse_selected_task())
        self.task_tree.bind("<Button-3>", self.show_task_context_menu)

    def log(self, message):
        self.log_text.insert(END, f"[{now_text()}] {message}\n")
        self.log_text.see(END)

    def open_ai_settings(self):
        self.log("打开 AI 接口配置")
        win = Toplevel(self.root)
        win.title("配置 AI 接口")
        win.geometry("800x780")
        win.minsize(760, 620)
        win.transient(self.root)
        win.configure(bg=COLOR_PANEL)
        win.option_add("*TCombobox*Listbox.background", "#000000")
        win.option_add("*TCombobox*Listbox.foreground", COLOR_TEXT)
        win.option_add("*TCombobox*Listbox.selectBackground", COLOR_ACCENT_DARK)
        win.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")

        fields = {}
        test_status_var = StringVar(value="未测试")

        body = Frame(win, bg=COLOR_PANEL)
        body.pack(fill=BOTH, expand=True)
        canvas = Canvas(body, highlightthickness=0, bg=COLOR_PANEL)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        content = Frame(canvas, bg=COLOR_PANEL)
        content_window = canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        def sync_scroll_region(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def sync_content_width(event):
            canvas.itemconfigure(content_window, width=event.width)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        content.bind("<Configure>", sync_scroll_region)
        canvas.bind("<Configure>", sync_content_width)
        canvas.bind("<MouseWheel>", on_mousewheel)
        content.bind("<MouseWheel>", on_mousewheel)

        def add_section(parent, title, rows):
            box = LabelFrame(parent, text=title, padx=8, pady=8, bg=COLOR_PANEL, fg=COLOR_MUTED)
            box.pack(fill=X, padx=10, pady=(10, 0))
            for label, key, default, secret in rows:
                row = Frame(box, bg=COLOR_PANEL)
                row.pack(fill=X, pady=3)
                Label(row, text=label, width=14, anchor="w", bg=COLOR_PANEL, fg=COLOR_TEXT).pack(side=LEFT)
                var = StringVar(value=text_value(self.settings.get(key), default))
                Entry(row, textvariable=var, show="*" if secret else "", width=64, bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT, relief="flat").pack(side=LEFT, fill=X, expand=True)
                fields[key] = var
            return box

        def add_entry_row(parent, label, key, default="", secret=False):
            row = Frame(parent, bg=COLOR_PANEL)
            row.pack(fill=X, pady=3)
            Label(row, text=label, width=14, anchor="w", bg=COLOR_PANEL, fg=COLOR_TEXT).pack(side=LEFT)
            var = StringVar(value=text_value(self.settings.get(key), default))
            Entry(row, textvariable=var, show="*" if secret else "", width=64, bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT, relief="flat").pack(side=LEFT, fill=X, expand=True)
            fields[key] = var
            return var

        def add_folder_row(parent, label, key, default=""):
            row = Frame(parent, bg=COLOR_PANEL)
            row.pack(fill=X, pady=3)
            Label(row, text=label, width=14, anchor="w", bg=COLOR_PANEL, fg=COLOR_TEXT).pack(side=LEFT)
            var = StringVar(value=text_value(self.settings.get(key), default))
            Entry(row, textvariable=var, state="readonly", readonlybackground=COLOR_INPUT, fg=COLOR_TEXT, relief="flat").pack(side=LEFT, fill=X, expand=True)

            def choose_folder():
                initial_dir = var.get().strip() or str(APP_DIR)
                if not Path(initial_dir).exists():
                    initial_dir = str(APP_DIR)
                selected = filedialog.askdirectory(parent=win, title=f"选择{label}", initialdir=initial_dir)
                if selected:
                    var.set(selected)
                    self.log(f"{label}已选择：{selected}")

            Button(row, text="选择文件夹", command=choose_folder).pack(side=LEFT, padx=(8, 0))
            fields[key] = var
            return var

        def add_combo_row(parent, label, key, default, values, width=20):
            row = Frame(parent, bg=COLOR_PANEL)
            row.pack(fill=X, pady=3)
            Label(row, text=label, width=14, anchor="w", bg=COLOR_PANEL, fg=COLOR_TEXT).pack(side=LEFT)
            var = StringVar(value=text_value(self.settings.get(key), default))
            if var.get() not in values:
                var.set(default)
            combo = ttk.Combobox(row, textvariable=var, values=values, width=width, state="readonly", style="Settings.TCombobox")
            combo.pack(side=LEFT)
            combo.bind("<MouseWheel>", on_mousewheel)
            fields[key] = var
            return var

        add_section(content, "文本模型", (
            ("Base URL", "text_base_url", "https://api.openai.com/v1", False),
            ("API Key", "text_api_key", "", True),
            ("Model", "text_model", TEXT_MODEL_NAME, False),
        ))
        add_section(content, "文生图模型", (
            ("Base URL", "image_base_url", "https://api.openai.com/v1", False),
            ("API Key", "image_api_key", "", True),
            ("Model", "image_model", IMAGE_MODEL_NAME, False),
            ("轮询路径", "image_poll_path", DEFAULT_IMAGE_POLL_PATH, False),
        ))
        add_section(content, "图生视频模型", (
            ("Base URL", "base_url", API_BASE, False),
            ("API Key", "api_key", "", True),
            ("Model", "video_model", MODEL_NAME, False),
        ))
        transcribe_box = LabelFrame(content, text="音频转文案", padx=8, pady=8, bg=COLOR_PANEL, fg=COLOR_MUTED)
        transcribe_box.pack(fill=X, padx=10, pady=(10, 0))
        mode_var = add_combo_row(transcribe_box, "转写方式", "transcribe_mode", "local_gpu", ("local_gpu", "apikey"), width=18)

        local_box = Frame(transcribe_box, bg=COLOR_PANEL)
        add_combo_row(local_box, "本地模型", "local_whisper_model", LOCAL_WHISPER_MODEL_NAME, ("small", "medium", "large-v3", "distil-large-v3"), width=18)
        add_folder_row(local_box, "模型目录", "local_whisper_model_dir", str(APP_DIR / "models" / "faster-whisper"))
        add_combo_row(local_box, "计算精度", "local_whisper_compute_type", "int8_float16", ("int8_float16", "float16", "int8"), width=18)
        add_combo_row(local_box, "Batch Size", "local_whisper_batch_size", "1", ("1", "2", "4", "8"), width=18)
        add_combo_row(local_box, "Beam Size", "local_whisper_beam_size", "3", ("1", "3", "5"), width=18)
        Label(
            local_box,
            text="显存建议：6GB 选 small + int8_float16 + batch 1；8GB 可选 medium 或 batch 2-4；12GB 以上再考虑 large-v3 / distil-large-v3 和 batch 4-8。",
            anchor="w",
            justify="left",
            wraplength=660,
            fg=COLOR_MUTED,
            bg=COLOR_PANEL,
        ).pack(fill=X, pady=(4, 0))

        api_box = Frame(transcribe_box, bg=COLOR_PANEL)
        add_entry_row(api_box, "音频 Base URL", "audio_base_url", self.settings.get("audio_base_url") or self.settings.get("ocr_base_url", "https://api.openai.com/v1"), False)
        add_entry_row(api_box, "音频 API Key", "audio_api_key", self.settings.get("audio_api_key") or self.settings.get("ocr_api_key", ""), True)
        add_entry_row(api_box, "音频 Model", "audio_model", self.settings.get("audio_model") or self.settings.get("ocr_model", AUDIO_MODEL_NAME), False)

        def update_transcribe_fields(*_):
            if mode_var.get() == "local_gpu":
                api_box.pack_forget()
                local_box.pack(fill=X, pady=(6, 0))
            else:
                local_box.pack_forget()
                api_box.pack(fill=X, pady=(6, 0))

        mode_var.trace_add("write", update_transcribe_fields)
        update_transcribe_fields()

        def save():
            for key, var in fields.items():
                self.settings[key] = var.get().strip()
            self.settings["parser_endpoint"] = DEFAULT_PARSER_ENDPOINT
            self.settings["parser_key"] = DEFAULT_PARSER_KEY
            self.settings["parser_sign"] = DEFAULT_PARSER_SIGN
            self.api_key_var.set(self.settings.get("api_key", ""))
            self.base_url_var.set(self.settings.get("base_url", API_BASE))
            self.video_model_var.set(self.settings.get("video_model", MODEL_NAME))
            write_json(SETTINGS_FILE, self.settings)
            self.log("AI 接口配置已保存")
            win.destroy()

        def test_connection():
            values = {key: var.get().strip() for key, var in fields.items()}
            test_status_var.set("测试中...")
            self.log("开始测试 AI 接口连接")

            def worker():
                results = []
                checks = (
                    ("文本模型", values.get("text_base_url"), values.get("text_api_key")),
                    ("文生图模型", values.get("image_base_url"), values.get("image_api_key")),
                    ("图生视频模型", normalize_base_url(values.get("base_url")), values.get("api_key")),
                )
                if values.get("transcribe_mode") == "apikey":
                    checks = checks + (("音频转文案", values.get("audio_base_url"), values.get("audio_api_key")),)
                for name, base_url, api_key in checks:
                    try:
                        test_models_endpoint(base_url, api_key)
                        results.append(f"{name}：通过")
                    except Exception as exc:
                        results.append(f"{name}：失败 - {exc}")
                if values.get("transcribe_mode") == "local_gpu":
                    results.append("音频转文案：本地 GPU 模式，请通过实际提取文案验证 CUDA 和模型。")

                self.event_queue.put(("settings_test_result", "\n".join(results)))

            threading.Thread(target=worker, daemon=True).start()

        def test_local_gpu():
            values = {key: var.get().strip() for key, var in fields.items()}
            values["parser_endpoint"] = DEFAULT_PARSER_ENDPOINT
            values["parser_key"] = DEFAULT_PARSER_KEY
            values["parser_sign"] = DEFAULT_PARSER_SIGN
            test_status_var.set("验证本地 CUDA 和模型中...")
            self.log("开始验证本地 CUDA 和 faster-whisper 模型")

            def worker():
                try:
                    result = validate_local_gpu_transcription(values)
                    self.event_queue.put(("settings_test_result", result))
                    self.event_queue.put(("log", "本地 CUDA 和模型验证通过"))
                except Exception as exc:
                    self.event_queue.put(("settings_test_result", f"本地 CUDA 和模型验证失败：{exc}"))
                    self.event_queue.put(("log", f"本地 CUDA 和模型验证失败：{exc}"))

            threading.Thread(target=worker, daemon=True).start()

        def detect_gpu():
            test_status_var.set("检测 GPU 型号和显存中...")
            self.log("开始检测 GPU 型号和显存")

            def worker():
                try:
                    result = detect_nvidia_gpu_info()
                    self.event_queue.put(("settings_test_result", result))
                    self.event_queue.put(("log", "GPU 型号和显存检测完成"))
                except Exception as exc:
                    self.event_queue.put(("settings_test_result", f"GPU 检测失败：{exc}"))
                    self.event_queue.put(("log", f"GPU 检测失败：{exc}"))

            threading.Thread(target=worker, daemon=True).start()

        actions = Frame(win, padx=10, pady=10, bg=COLOR_PANEL)
        actions.pack(fill=X)
        Label(actions, textvariable=test_status_var, anchor="w", bg=COLOR_PANEL, fg=COLOR_TEXT).pack(side=LEFT, fill=X, expand=True)
        Button(actions, text="检测 GPU", command=detect_gpu).pack(side=RIGHT, padx=(8, 0))
        Button(actions, text="验证本地 CUDA 和模型", command=test_local_gpu).pack(side=RIGHT, padx=(8, 0))
        Button(actions, text="测试连接", command=test_connection).pack(side=RIGHT, padx=(8, 0))
        Button(actions, text="保存", command=save).pack(side=RIGHT)
        Button(actions, text="取消", command=win.destroy).pack(side=RIGHT, padx=(0, 8))

    def save_settings(self):
        self.settings["api_key"] = self.api_key_var.get().strip()
        self.settings["base_url"] = normalize_base_url(self.base_url_var.get())
        self.settings["video_model"] = self.video_model_var.get().strip() or MODEL_NAME
        self.base_url_var.set(self.settings["base_url"])
        if hasattr(self, "parser_download_dir_var"):
            parser_download_dir = self.parser_download_dir_var.get().strip() or str(OUTPUT_DIR / "parsed_videos")
            self.settings["parser_download_dir"] = parser_download_dir
            self.parser_download_dir_var.set(parser_download_dir)
        output_dir = self.output_dir_var.get().strip() or str(OUTPUT_DIR)
        self.settings["output_dir"] = output_dir
        self.output_dir_var.set(output_dir)
        write_json(SETTINGS_FILE, self.settings)
        self.log("设置已保存")

    def open_license_status(self):
        data = read_json(LICENSE_FILE, {})
        details = [
            f"卡密：{mask_secret(data.get('card_key', ''))}",
            f"到期时间：{data.get('expires_at', '未查询')}",
            f"剩余解绑次数：{data.get('remaining_unbinds', '未查询')}",
            f"本机码：{machine_fingerprint()[:16]}",
            f"最近验证：{data.get('verified_at', '未知')}",
        ]
        messagebox.showinfo("卡密授权", "\n".join(details))

    def parser_download_dir(self):
        path = self.settings.get("parser_download_dir") or str(OUTPUT_DIR / "parsed_videos")
        return Path(path)

    def choose_parser_download_dir(self):
        self.log("打开视频解析下载目录选择窗口")
        path = filedialog.askdirectory(title="选择视频解析下载目录")
        if not path:
            return
        self.settings["parser_download_dir"] = path
        self.parser_download_dir_var.set(path)
        write_json(SETTINGS_FILE, self.settings)
        self.log(f"视频解析下载目录：{path}")

    def choose_output_dir(self):
        self.log("打开输出目录选择窗口")
        path = filedialog.askdirectory(title="选择视频输出目录")
        if path:
            self.settings["output_dir"] = path
            self.output_dir_var.set(path)
            write_json(SETTINGS_FILE, self.settings)
            self.log(f"输出目录：{path}")

    def parse_video_async(self):
        source_text = self.parse_url_var.get().strip()
        source_url = extract_first_url(source_text) or source_text
        if not source_text:
            messagebox.showwarning("缺少链接", "请先粘贴抖音、快手或公开视频链接。")
            return
        if not source_url.startswith(("http://", "https://")):
            messagebox.showwarning("链接格式错误", "没有识别到有效的视频链接，请检查粘贴内容。")
            return
        if source_url != source_text:
            self.parse_url_var.set(source_url)
            self.log(f"已从分享文案中识别视频链接：{source_url}")
        self.save_settings()
        self.parser_status_var.set("解析中")
        self.log(f"开始解析视频：{compact_text(source_url, 80)}")
        thread = threading.Thread(target=self.parse_video_worker, args=(source_url,), daemon=True)
        thread.start()

    def parse_video_worker(self, source_url):
        try:
            config = parser_settings(self.settings)
            client = VideoParserClient(config["endpoint"], config["key"], config["sign"])
            item = client.parse(source_url)
            download_error = ""
            if item.video_url:
                try:
                    target = self.parser_download_dir()
                    target.mkdir(parents=True, exist_ok=True)
                    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{item.id}_{safe_name(item.title or 'parsed_video')}.mp4"
                    destination = target / filename
                    download_file(item.video_url, "", destination)
                    item.local_path = str(destination)
                    item.updated_at = now_text()
                except Exception as exc:
                    download_error = str(exc)
            self.parsed_videos.insert(0, item)
            self.persist_parsed_videos()
            self.event_queue.put(("refresh_parsed", None))
            if item.local_path:
                self.event_queue.put(("log", f"视频解析并下载成功：{item.id} -> {item.local_path}"))
            elif download_error:
                self.event_queue.put(("log", f"视频解析成功，但下载失败：{item.id}，{download_error}"))
            else:
                self.event_queue.put(("log", f"视频解析成功，但接口未返回可下载视频地址：{item.id}"))
        except Exception as exc:
            self.event_queue.put(("parser_status", "解析失败"))
            self.event_queue.put(("log", f"视频解析失败：{exc}"))

    def selected_parsed_video(self):
        if not hasattr(self, "parsed_tree"):
            return None
        selection = self.parsed_tree.selection()
        if not selection:
            return None
        item_id = selection[0]
        return next((item for item in self.parsed_videos if item.id == item_id), None)

    def refresh_parsed_videos(self):
        if not hasattr(self, "parsed_tree"):
            return
        for item_id in self.parsed_tree.get_children():
            self.parsed_tree.delete(item_id)
        for index, item in enumerate(self.parsed_videos, 1):
            self.parsed_tree.insert("", END, iid=item.id, values=(
                index,
                compact_text(item.title, 80),
                compact_text(item.caption, 100),
                compact_text(item.video_url, 100),
                Path(item.local_path).name if item.local_path else "",
                item.updated_at,
            ))
        self.parser_status_var.set(f"已解析 {len(self.parsed_videos)} 条")

    def show_selected_parsed_detail(self):
        item = self.selected_parsed_video()
        if not item:
            return
        self.parsed_detail_text.delete("1.0", END)
        detail = [
            f"来源链接：{item.source_url}",
            f"视频地址：{item.video_url}",
            f"本地文件：{item.local_path or '未下载'}",
            "",
            "标题/平台文案：",
            item.title or "无",
            "",
            "音频文案/提取文案：",
            item.caption or "无",
        ]
        self.parsed_detail_text.insert("1.0", "\n".join(detail))

    def show_parsed_context_menu(self, event):
        item_id = self.parsed_tree.identify_row(event.y)
        if not item_id:
            return
        self.parsed_tree.selection_set(item_id)
        self.parsed_tree.focus(item_id)
        menu = Menu(self.root, tearoff=0)
        menu.add_command(label="提取文案", command=self.extract_selected_video_text)
        menu.add_command(label="查看解析文案", command=self.show_selected_parsed_caption_popup)
        menu.add_command(label="打开所在文件夹", command=self.open_selected_parsed_folder)
        menu.add_command(label="文案填入改写页", command=self.use_selected_parsed_caption)
        menu.add_separator()
        menu.add_command(label="删除记录", command=self.delete_selected_parsed_video)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def clear_parsed_videos(self):
        if not self.parsed_videos:
            self.log("解析列表已经为空")
            return
        if not messagebox.askyesno("清空解析列表", "确定清空所有视频解析记录？本地已下载文件不会删除。"):
            return
        count = len(self.parsed_videos)
        self.parsed_videos = []
        self.persist_parsed_videos()
        self.refresh_parsed_videos()
        self.parsed_detail_text.delete("1.0", END)
        self.log(f"已清空视频解析列表：{count} 条")

    def show_selected_parsed_caption_popup(self):
        item = self.selected_parsed_video()
        if not item:
            messagebox.showinfo("查看解析文案", "请先选择一条解析记录。")
            return
        text = item.caption or item.title or ""
        if not text:
            messagebox.showinfo("查看解析文案", "该记录暂时没有解析文案。")
            return
        win = Toplevel(self.root)
        win.title("解析文案")
        win.geometry("720x420")
        win.transient(self.root)
        box = Text(win, wrap="word")
        box.pack(fill=BOTH, expand=True, padx=10, pady=10)
        box.insert("1.0", text)
        actions = Frame(win, padx=10, pady=(0, 10))
        actions.pack(fill=X)
        def copy_caption():
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.log(f"已复制解析文案：{item.id}")
            messagebox.showinfo("复制文案", "解析文案已复制到剪贴板。", parent=win)

        Button(actions, text="复制文案", command=copy_caption).pack(side=LEFT)
        Button(actions, text="关闭", command=win.destroy).pack(side=RIGHT)
        self.log(f"查看解析文案：{item.id}")

    def delete_selected_parsed_video(self):
        item = self.selected_parsed_video()
        if not item:
            return
        if not messagebox.askyesno("删除解析记录", "确定删除选中的视频解析记录？本地已下载文件不会删除。"):
            return
        self.parsed_videos = [video for video in self.parsed_videos if video.id != item.id]
        self.persist_parsed_videos()
        self.refresh_parsed_videos()
        self.parsed_detail_text.delete("1.0", END)
        self.log(f"已删除视频解析记录：{item.id}")

    def open_selected_parsed_folder(self):
        item = self.selected_parsed_video()
        if not item:
            messagebox.showinfo("打开所在文件夹", "请先选择一条解析记录。")
            return
        if not item.local_path or not Path(item.local_path).exists():
            messagebox.showinfo("打开所在文件夹", "该记录没有可用的本地视频文件，请重新解析或检查下载目录。")
            return
        path = Path(item.local_path)
        self.log(f"打开解析视频所在文件夹：{path.parent}")
        try:
            subprocess.Popen(["explorer", "/select,", str(path)])
        except Exception:
            os.startfile(path.parent)

    def download_selected_parsed_video(self):
        item = self.selected_parsed_video()
        if not item:
            messagebox.showinfo("下载视频", "请先选择一条解析记录。")
            return
        if not item.video_url:
            messagebox.showwarning("下载视频", "该解析记录没有视频地址。")
            return
        self.save_settings()
        target = self.parser_download_dir()
        target.mkdir(parents=True, exist_ok=True)
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{item.id}_{safe_name(item.title or 'parsed_video')}.mp4"
        destination = target / filename
        try:
            download_file(item.video_url, "", destination)
            item.local_path = str(destination)
            item.updated_at = now_text()
            self.persist_parsed_videos()
            self.refresh_parsed_videos()
            self.log(f"解析视频已下载：{destination}")
        except Exception as exc:
            messagebox.showerror("下载失败", str(exc))

    def add_selected_parsed_to_materials(self):
        item = self.selected_parsed_video()
        if not item:
            messagebox.showinfo("加入素材库", "请先选择一条解析记录。")
            return
        if not item.cover_url:
            messagebox.showinfo("加入素材库", "当前解析记录没有封面图。素材库目前用于图生视频参考图，暂不把 MP4 直接加入图片素材库。")
            return
        material_id = uuid.uuid4().hex[:12]
        dest = MATERIAL_DIR / f"{material_id}_{safe_name(item.title or 'cover')}.jpg"
        try:
            download_file(item.cover_url, "", dest)
        except Exception as exc:
            messagebox.showerror("加入素材库失败", f"封面下载失败：{exc}")
            return
        alias = unique_alias(item.title or f"cover_{material_id[:6]}", [material.alias for material in self.materials], f"cover_{material_id[:6]}")
        self.materials.append(Material(id=material_id, alias=alias, path=str(dest), added_at=now_text(), tags="视频封面"))
        self.persist_materials()
        self.refresh_materials()
        self.log(f"已加入素材库：@{alias}")

    def use_selected_parsed_caption(self):
        item = self.selected_parsed_video()
        if not item:
            messagebox.showinfo("填入改写页", "请先选择一条解析记录。")
            return
        text = item.caption or item.title
        if not text:
            messagebox.showwarning("填入改写页", "该记录暂时没有可用文案。")
            return
        self.rewrite_input_text.delete("1.0", END)
        self.rewrite_input_text.insert("1.0", text)
        self.show_section("rewrite")
        self.log(f"已把解析文案填入文案改写页：{item.id}")

    def extract_selected_video_text(self):
        item = self.selected_parsed_video()
        if not item:
            messagebox.showinfo("音频转文案", "请先选择一条解析记录。")
            return
        if item.local_path and not Path(item.local_path).exists():
            messagebox.showwarning("音频转文案", f"本地视频文件不存在：{item.local_path}")
            return
        mode = text_value(self.settings.get("transcribe_mode"), "local_gpu").strip() or "local_gpu"
        audio_key = text_value(self.settings.get("audio_api_key") or self.settings.get("ocr_api_key")).strip()
        if mode != "local_gpu" and not audio_key:
            messagebox.showinfo(
                "音频转文案",
                "请先在“配置 AI”里填写音频转文案 API Key 和模型。默认接口使用兼容 OpenAI 的 /audio/transcriptions。",
            )
            return
        self.parser_status_var.set("准备音频转文案")
        self.save_settings()
        local_text = item.local_path if item.local_path else "未下载，将尝试使用解析记录的视频地址下载"
        self.log(f"开始提取解析视频文案：{item.id}，方式：{mode}，本地文件：{local_text}")
        self.active_transcribe_jobs[item.id] = time.time()
        thread = threading.Thread(target=self.transcribe_parsed_video_worker, args=(item.id,), daemon=True)
        thread.start()
        self.root.after(60000, lambda item_id=item.id: self.check_transcribe_stall(item_id, 1))

    def check_transcribe_stall(self, item_id, minutes):
        started_at = self.active_transcribe_jobs.get(item_id)
        if not started_at:
            return
        elapsed = int(time.time() - started_at)
        self.parser_status_var.set(f"音频转文案仍在运行：{elapsed} 秒")
        self.log(
            f"音频转文案仍在运行：{item_id}，已耗时 {elapsed} 秒；如果长时间无结果，请检查 CUDA/显卡驱动/模型目录，详情看 transcribe_error.log"
        )
        if minutes < 10:
            self.root.after(60000, lambda item_id=item_id, minutes=minutes + 1: self.check_transcribe_stall(item_id, minutes))
        else:
            self.parser_status_var.set("音频转文案超时，请检查本地 GPU 环境")
            self.log(f"音频转文案可能卡死：{item_id}，已超过 {elapsed} 秒。可切换 API 转写或降低模型/Batch Size。")

    def transcribe_parsed_video_worker(self, item_id):
        try:
            item = next((video for video in self.parsed_videos if video.id == item_id), None)
            if not item:
                raise RuntimeError("解析记录不存在")
            if not item.local_path or not Path(item.local_path).exists():
                if not item.video_url:
                    raise RuntimeError("该解析记录没有本地视频文件。请先解析并下载视频，提取文案不需要填写视频链接输入框。")
                self.event_queue.put(("parser_status", "本地视频不存在，正在从解析记录下载视频"))
                target = self.parser_download_dir()
                target.mkdir(parents=True, exist_ok=True)
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{item.id}_{safe_name(item.title or 'parsed_video')}.mp4"
                destination = target / filename
                download_file(item.video_url, "", destination)
                item.local_path = str(destination)
                item.updated_at = now_text()
                self.persist_parsed_videos()
                self.event_queue.put(("refresh_parsed", None))

            mode = text_value(self.settings.get("transcribe_mode"), "local_gpu").strip() or "local_gpu"
            self.event_queue.put(("parser_status", f"开始转写本地视频：{Path(item.local_path).name}"))
            if mode == "local_gpu":
                text = transcribe_audio_file_local_gpu(
                    item.local_path,
                    self.settings,
                    lambda status: self.event_queue.put(("parser_status", status)),
                )
            else:
                text = transcribe_audio_file(
                    item.local_path,
                    text_value(self.settings.get("audio_api_key") or self.settings.get("ocr_api_key")).strip(),
                    text_value(self.settings.get("audio_base_url") or self.settings.get("ocr_base_url") or "https://api.openai.com/v1"),
                    text_value(self.settings.get("audio_model") or self.settings.get("ocr_model") or AUDIO_MODEL_NAME),
                )
            if not text:
                raise RuntimeError("音频转文案接口没有返回文字")
            item.caption = text
            item.updated_at = now_text()
            self.persist_parsed_videos()
            self.event_queue.put(("refresh_parsed", None))
            self.event_queue.put(("fill_prompt", text))
            self.event_queue.put(("parser_status", "音频文案已提取"))
            self.event_queue.put(("log", f"音频文案已提取：{item.id}"))
        except Exception as exc:
            append_transcribe_log(f"item_id={item_id}\n{traceback.format_exc()}")
            self.event_queue.put(("parser_status", "音频转文案失败"))
            self.event_queue.put(("log", f"音频转文案失败：{exc}"))
        finally:
            self.active_transcribe_jobs.pop(item_id, None)

    def open_output_dir(self):
        path = self.output_dir_var.get().strip() or self.settings.get("output_dir") or str(OUTPUT_DIR)
        Path(path).mkdir(parents=True, exist_ok=True)
        self.log(f"打开输出目录：{path}")
        os.startfile(path)

    def open_local_image(self, path):
        path = Path(text_value(path))
        if not path.exists():
            messagebox.showinfo("打开图片", "本地图片文件不存在。")
            return
        self.log(f"打开本地图片：{path}")
        os.startfile(path)

    def open_material_image(self, material_id):
        material = self.materials_by_id().get(material_id)
        if material:
            self.open_local_image(material.path)

    def add_materials(self):
        paths = filedialog.askopenfilenames(
            title="选择参考图片",
            filetypes=[("图片", "*.png *.jpg *.jpeg *.webp *.bmp"), ("所有文件", "*.*")]
        )
        if not paths:
            return
        for source in paths:
            src = Path(source)
            material_id = uuid.uuid4().hex[:12]
            alias = unique_alias(src.stem, [material.alias for material in self.materials], f"image_{material_id[:6]}")
            dest = MATERIAL_DIR / f"{material_id}_{safe_name(src.name)}"
            shutil.copy2(src, dest)
            self.materials.append(Material(id=material_id, alias=alias, path=str(dest), added_at=now_text()))
        self.persist_materials()
        self.refresh_materials()
        self.log(f"已上传 {len(paths)} 张图片到素材库")

    def material_prompt_widget(self):
        focus = self.root.focus_get()
        for name in ("prompt_text", "image_prompt_text", "agent_entry"):
            widget = getattr(self, name, None)
            if widget is not None and focus == widget:
                return widget
        return getattr(self, "prompt_text", None)

    def material_alias_token_at_cursor(self):
        widget = self.material_prompt_widget()
        if widget is None:
            return None
        if widget.winfo_class() == "Entry":
            insert_index = widget.index("insert")
            before_cursor = widget.get()[:insert_index]
            match = re.search(r"@([\w\-\u4e00-\u9fff]*)$", before_cursor)
            if not match:
                return None
            start_index = insert_index - len(match.group(0))
            return start_index, insert_index, match.group(1).lower()
        insert_index = widget.index("insert")
        line_start = f"{insert_index.split('.')[0]}.0"
        before_cursor = widget.get(line_start, insert_index)
        match = re.search(r"@([\w\-\u4e00-\u9fff]*)$", before_cursor)
        if not match:
            return None
        start_col = len(before_cursor) - len(match.group(0))
        start_index = f"{insert_index.split('.')[0]}.{start_col}"
        return start_index, insert_index, match.group(1).lower()

    def handle_prompt_keypress(self, event=None):
        popup = getattr(self, "material_suggest_popup", None)
        listbox = getattr(self, "material_suggest_listbox", None)
        if not popup or not popup.winfo_exists() or popup.state() == "withdrawn" or not listbox:
            return None
        if event.keysym in ("Down", "Up"):
            size = listbox.size()
            if not size:
                return "break"
            selection = listbox.curselection()
            current = selection[0] if selection else 0
            next_index = current + (1 if event.keysym == "Down" else -1)
            next_index = max(0, min(size - 1, next_index))
            listbox.selection_clear(0, END)
            listbox.selection_set(next_index)
            listbox.activate(next_index)
            listbox.see(next_index)
            return "break"
        if event.keysym == "Return":
            self.insert_material_suggestion()
            return "break"
        if event.keysym == "Escape":
            self.hide_material_suggestions()
            return "break"
        return None

    def handle_prompt_keyrelease(self, event=None):
        if event and event.keysym in ("Up", "Down", "Return", "Escape"):
            return
        token = self.material_alias_token_at_cursor()
        if not token:
            self.hide_material_suggestions()
            return
        start_index, _end_index, keyword = token
        candidates = []
        for item in self.materials:
            if not Path(item.path).exists():
                continue
            haystack = f"{item.alias} {item.tags} {Path(item.path).name}".lower()
            if keyword and keyword not in haystack:
                continue
            candidates.append(item)
        self.show_material_suggestions(candidates[:10], start_index)

    def show_material_suggestions(self, candidates, start_index):
        if not candidates:
            self.hide_material_suggestions()
            return
        widget = self.material_prompt_widget()
        if widget is None:
            return
        self.material_suggest_widget = widget
        if self.material_suggest_popup is None or not self.material_suggest_popup.winfo_exists():
            popup = Toplevel(self.root)
            popup.overrideredirect(True)
            popup.configure(bg=COLOR_BORDER)
            listbox = Listbox(
                popup,
                height=min(8, len(candidates)),
                bg="#000000",
                fg=COLOR_TEXT,
                selectbackground=COLOR_ACCENT_DARK,
                selectforeground="#ffffff",
                activestyle="none",
                relief="flat",
                bd=1,
                highlightthickness=1,
                highlightbackground=COLOR_BORDER,
                font=FONT_SMALL,
            )
            listbox.pack(fill=BOTH, expand=True, padx=1, pady=1)
            listbox.bind("<Return>", lambda _event: self.insert_material_suggestion())
            listbox.bind("<Double-Button-1>", lambda _event: self.insert_material_suggestion())
            listbox.bind("<Escape>", lambda _event: self.hide_material_suggestions())
            listbox.bind("<FocusOut>", lambda _event: self.root.after(120, self.hide_material_suggestions))
            self.material_suggest_popup = popup
            self.material_suggest_listbox = listbox
        listbox = self.material_suggest_listbox
        listbox.delete(0, END)
        self.material_suggest_ids = []
        self.material_suggest_start_index = start_index
        for item in candidates:
            label = f"@{item.alias}  {item.tags or '未分类'}  {Path(item.path).name}"
            listbox.insert(END, compact_text(label, 58))
            self.material_suggest_ids.append(item.id)
        listbox.configure(height=min(8, len(candidates)))
        listbox.selection_clear(0, END)
        listbox.selection_set(0)
        listbox.activate(0)
        bbox = widget.bbox("insert")
        if bbox:
            if widget.winfo_class() == "Entry":
                x, y, width, height = bbox
            else:
                x, y, width, height = bbox
            root_x = widget.winfo_rootx() + x
            root_y = widget.winfo_rooty() + y + height + 2
            self.material_suggest_popup.geometry(f"420x{min(8, len(candidates)) * 28}+{root_x}+{root_y}")
            self.material_suggest_popup.deiconify()
            self.material_suggest_popup.lift()

    def insert_material_suggestion(self):
        if not self.material_suggest_listbox or not self.material_suggest_ids:
            return
        selection = self.material_suggest_listbox.curselection()
        index = selection[0] if selection else 0
        if index >= len(self.material_suggest_ids):
            return
        material = self.materials_by_id().get(self.material_suggest_ids[index])
        if not material:
            return
        widget = getattr(self, "material_suggest_widget", None) or self.material_prompt_widget()
        if widget is None:
            return
        end_index = widget.index("insert")
        start_index = self.material_suggest_start_index or end_index
        widget.delete(start_index, end_index)
        widget.insert(start_index, f"@{material.alias} ")
        self.hide_material_suggestions()
        self.log(f"已插入素材引用：@{material.alias}")

    def hide_material_suggestions(self):
        popup = getattr(self, "material_suggest_popup", None)
        if popup is not None and popup.winfo_exists():
            popup.withdraw()

    def selected_material_ids(self):
        if getattr(self, "current_section", "") == "assets" and hasattr(self, "asset_selected_material_ids"):
            return list(self.asset_selected_material_ids)
        if getattr(self, "current_section", "") == "generate" and hasattr(self, "generate_selected_material_ids"):
            return list(self.generate_selected_material_ids)
        if getattr(self, "current_section", "") == "image" and hasattr(self, "image_selected_material_ids"):
            return list(self.image_selected_material_ids)
        trees = []
        if getattr(self, "current_section", "") == "assets" and hasattr(self, "material_tree"):
            trees.append(self.material_tree)
        for tree_name in ("material_tree",):
            tree = getattr(self, tree_name, None)
            if tree is not None and tree not in trees:
                trees.append(tree)
        for tree in trees:
            try:
                selection = list(tree.selection())
            except Exception:
                selection = []
            if selection:
                return selection
        return []

    def insert_selected_material_refs(self):
        materials = self.materials_by_id()
        aliases = [f"@{materials[mid].alias}" for mid in self.selected_material_ids() if mid in materials]
        if aliases:
            self.prompt_text.insert("insert", " " + " ".join(aliases) + " ")
            self.log(f"已插入素材引用：{' '.join(aliases)}")

    def delete_selected_materials(self):
        ids = set(self.selected_material_ids())
        if not ids:
            return
        if not messagebox.askyesno("删除素材", f"确定删除 {len(ids)} 个素材？"):
            return
        kept = []
        for item in self.materials:
            if item.id in ids:
                try:
                    Path(item.path).unlink(missing_ok=True)
                except OSError:
                    pass
            else:
                kept.append(item)
        self.materials = kept
        self.persist_materials()
        self.refresh_materials()
        self.log(f"已删除素材 {len(ids)} 个")

    def refresh_materials(self):
        self.update_group_combos()
        self.refresh_asset_grid()
        self.refresh_one_material_tree(
            getattr(self, "material_tree", None),
            self.material_images,
            self.search_var.get().strip().lower(),
            self.asset_type_var.get() if hasattr(self, "asset_type_var") else "全部",
        )
        self.refresh_generate_asset_grid()
        self.refresh_image_asset_grid()
        self.refresh_reference_strip("image")
        self.refresh_reference_strip("video")

    def group_filter_values(self):
        return ["全部"] + list(self.material_groups)

    def update_group_combos(self):
        values = self.group_filter_values()
        for name in ("asset_type_combo", "generate_asset_type_combo", "image_asset_type_combo"):
            combo = getattr(self, name, None)
            if combo is not None:
                combo.configure(values=values)
        if hasattr(self, "asset_type_var") and self.asset_type_var.get() not in values:
            self.asset_type_var.set("全部")
        if hasattr(self, "generate_asset_type_var") and self.generate_asset_type_var.get() not in values:
            self.generate_asset_type_var.set("全部")
        if hasattr(self, "image_asset_type_var") and self.image_asset_type_var.get() not in values:
            self.image_asset_type_var.set("全部")

    def refresh_asset_grid(self):
        if not hasattr(self, "asset_grid"):
            return
        for child in self.asset_grid.winfo_children():
            child.destroy()
        self.asset_grid_images.clear()
        visible_ids = set()
        keyword = self.search_var.get().strip().lower() if hasattr(self, "search_var") else ""
        asset_type = self.asset_type_var.get() if hasattr(self, "asset_type_var") else "全部"
        columns = 6
        row = 0
        col = 0
        for item in self.materials:
            display = f"{item.id} @{item.alias} {Path(item.path).name} {item.tags}"
            if keyword and keyword not in display.lower():
                continue
            if asset_type and asset_type != "全部" and asset_type not in item.tags:
                continue
            visible_ids.add(item.id)
            tile = Frame(self.asset_grid, bd=0, relief="flat", padx=6, pady=6, width=150, height=176, highlightthickness=1, highlightbackground=COLOR_BORDER)
            tile.grid(row=row, column=col, padx=7, pady=7, sticky="n")
            tile.grid_propagate(False)
            image = None
            thumb = create_thumbnail(item, size=112)
            if thumb:
                try:
                    image = PhotoImage(file=thumb)
                    self.asset_grid_images[item.id] = image
                except Exception:
                    image = None
            image_label = Label(tile, image=image, text="" if image else "无预览", width=118, height=112)
            image_label.pack()
            name_label = Label(tile, text=compact_text(f"@{item.alias}", 20), wraplength=128, justify="center")
            name_label.pack(fill=X, pady=(4, 0))
            tag_label = Label(tile, text=compact_text(item.tags or "未分组", 18), wraplength=128, justify="center", fg=COLOR_MUTED)
            tag_label.pack(fill=X)

            def bind_tile(widget, material_id=item.id):
                widget.bind("<Button-1>", lambda _event, mid=material_id: self.select_asset_material(mid))
                widget.bind("<Button-3>", lambda event, mid=material_id: self.show_asset_context_menu(event, mid))

            for widget in (tile, image_label, name_label, tag_label):
                bind_tile(widget)
            if item.id in self.asset_selected_material_ids:
                tile.configure(bg="#0c4a6e", highlightbackground=COLOR_ACCENT)
                image_label.configure(bg="#0c4a6e", fg="#ffffff")
                name_label.configure(bg="#0c4a6e", fg="#ffffff")
                tag_label.configure(bg="#c7e8ff", fg="#0c4a6e")
            else:
                tile.configure(bg=COLOR_CARD, highlightbackground=COLOR_BORDER)
                image_label.configure(bg=COLOR_CARD, fg=COLOR_TEXT)
                name_label.configure(bg=COLOR_CARD, fg=COLOR_TEXT)
                tag_label.configure(bg=COLOR_CARD, fg=COLOR_MUTED)
            col += 1
            if col >= columns:
                col = 0
                row += 1
        self.asset_selected_material_ids.intersection_update(visible_ids)

    def select_asset_material(self, material_id):
        self.asset_selected_material_ids = {material_id}
        self.refresh_asset_grid()

    def insert_material_ref_by_id(self, material_id):
        material = self.materials_by_id().get(material_id)
        if material:
            self.prompt_text.insert("insert", f" @{material.alias} ")
            self.log(f"已插入素材引用：@{material.alias}")

    def show_asset_context_menu(self, event, material_id):
        self.asset_selected_material_ids = {material_id}
        if hasattr(self, "image_selected_material_ids"):
            self.image_selected_material_ids = {material_id}
        menu = Menu(self.root, tearoff=0)
        menu.add_command(label="查看原图", command=lambda mid=material_id: self.open_material_image(mid))
        menu.add_separator()
        menu.add_command(label="复用提示词和参考图", command=lambda mid=material_id: self.reuse_material_for_image(mid))
        menu.add_separator()
        menu.add_command(label="重命名 / 选择分组", command=self.edit_selected_material)
        menu.add_separator()
        menu.add_command(label="删除图片资源", command=self.delete_selected_materials)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def reuse_material_for_image(self, material_id):
        material = self.materials_by_id().get(material_id)
        if not material:
            return
        if material.prompt:
            self.image_prompt_text.delete("1.0", END)
            self.image_prompt_text.insert("1.0", material.prompt)
        refs = list(material.references or [])
        if material.id not in refs:
            refs.insert(0, material.id)
        self.set_image_references(refs)
        self.show_section("image")
        self.image_status_var.set("已复用素材参考图")
        if material.prompt:
            self.log(f"已复用素材提示词和参考图：@{material.alias}")
        else:
            self.log(f"已复用素材作为图片参考图：@{material.alias}")

    def refresh_generate_asset_grid(self):
        if not hasattr(self, "generate_asset_grid"):
            return
        for child in self.generate_asset_grid.winfo_children():
            child.destroy()
        self.generate_material_images.clear()
        visible_ids = set()
        keyword = self.generate_search_var.get().strip().lower() if hasattr(self, "generate_search_var") else ""
        asset_type = self.generate_asset_type_var.get() if hasattr(self, "generate_asset_type_var") else "全部"
        columns = 4
        row = 0
        col = 0
        for item in self.materials:
            display = f"{item.id} @{item.alias} {Path(item.path).name} {item.tags}"
            if keyword and keyword not in display.lower():
                continue
            if asset_type and asset_type != "全部" and asset_type not in item.tags:
                continue
            visible_ids.add(item.id)
            tile = Frame(self.generate_asset_grid, bd=0, relief="flat", padx=6, pady=6, width=128, height=150, highlightthickness=1, highlightbackground=COLOR_BORDER)
            tile.grid(row=row, column=col, padx=6, pady=6, sticky="n")
            tile.grid_propagate(False)
            image = None
            thumb = create_thumbnail(item)
            if thumb:
                try:
                    image = PhotoImage(file=thumb)
                    self.generate_material_images[item.id] = image
                except Exception:
                    image = None
            image_label = Label(tile, image=image, text="" if image else "无预览", width=104, height=96)
            image_label.pack()
            name = compact_text(f"@{item.alias}", 18)
            name_label = Label(tile, text=name, wraplength=108, justify="center")
            name_label.pack(fill=X, pady=(4, 0))

            def bind_tile(widget, material_id=item.id):
                widget.bind("<Double-Button-1>", lambda _event, mid=material_id: self.insert_generate_material_ref(mid))

            for widget in (tile, image_label, name_label):
                bind_tile(widget)
            tile.configure(bg=COLOR_CARD, highlightbackground=COLOR_BORDER)
            image_label.configure(bg=COLOR_CARD, fg=COLOR_TEXT)
            name_label.configure(bg=COLOR_CARD, fg=COLOR_MUTED)
            col += 1
            if col >= columns:
                col = 0
                row += 1
        self.generate_selected_material_ids.clear()

    def insert_generate_material_ref(self, material_id):
        material = self.materials_by_id().get(material_id)
        if material:
            self.prompt_text.insert("insert", f" @{material.alias} ")
            self.log(f"已双击插入素材引用：@{material.alias}")

    def on_image_asset_canvas_configure(self, event):
        self.image_asset_canvas.itemconfigure(self.image_asset_window, width=event.width)
        if self.image_asset_refresh_after:
            self.root.after_cancel(self.image_asset_refresh_after)
        self.image_asset_refresh_after = self.root.after(120, self.refresh_image_asset_grid_if_columns_changed)

    def image_asset_column_count(self):
        canvas_width = self.image_asset_canvas.winfo_width() if hasattr(self, "image_asset_canvas") else 0
        return max(3, min(8, (canvas_width or 700) // 140))

    def refresh_image_asset_grid_if_columns_changed(self):
        self.image_asset_refresh_after = None
        columns = self.image_asset_column_count()
        if columns != getattr(self, "image_asset_last_columns", 0):
            self.refresh_image_asset_grid()

    def refresh_image_asset_grid(self):
        if not hasattr(self, "image_asset_grid"):
            return
        for child in self.image_asset_grid.winfo_children():
            child.destroy()
        self.image_asset_images.clear()
        visible_ids = set()
        keyword = self.image_search_var.get().strip().lower() if hasattr(self, "image_search_var") else ""
        asset_type = self.image_asset_type_var.get() if hasattr(self, "image_asset_type_var") else "全部"
        columns = self.image_asset_column_count()
        self.image_asset_last_columns = columns
        row = 0
        col = 0
        for item in self.materials:
            display = f"{item.id} @{item.alias} {Path(item.path).name} {item.tags}"
            if keyword and keyword not in display.lower():
                continue
            if asset_type and asset_type != "全部" and asset_type not in item.tags:
                continue
            visible_ids.add(item.id)
            tile = Frame(self.image_asset_grid, bd=0, relief="flat", padx=6, pady=6, width=128, height=150, highlightthickness=1, highlightbackground=COLOR_BORDER)
            tile.grid(row=row, column=col, padx=6, pady=6, sticky="n")
            tile.grid_propagate(False)
            image = None
            thumb = create_thumbnail(item)
            if thumb:
                try:
                    image = PhotoImage(file=thumb)
                    self.image_asset_images[item.id] = image
                except Exception:
                    image = None
            image_label = Label(tile, image=image, text="" if image else "无预览", width=104, height=96)
            image_label.pack()
            name_label = Label(tile, text=compact_text(f"@{item.alias}", 18), wraplength=108, justify="center")
            name_label.pack(fill=X, pady=(4, 0))

            def bind_tile(widget, material_id=item.id):
                widget.bind("<Button-1>", lambda _event, mid=material_id: self.select_image_material(mid))
                widget.bind("<Double-Button-1>", lambda _event, mid=material_id: self.insert_image_material_ref(mid))
                widget.bind("<Button-3>", lambda event, mid=material_id: self.show_asset_context_menu(event, mid))

            for widget in (tile, image_label, name_label):
                bind_tile(widget)
            if item.id in self.image_selected_material_ids:
                tile.configure(bg="#0c4a6e", highlightbackground=COLOR_ACCENT)
                image_label.configure(bg="#0c4a6e", fg="#ffffff")
                name_label.configure(bg="#0c4a6e", fg="#ffffff")
            else:
                tile.configure(bg=COLOR_CARD, highlightbackground=COLOR_BORDER)
                image_label.configure(bg=COLOR_CARD, fg=COLOR_TEXT)
                name_label.configure(bg=COLOR_CARD, fg=COLOR_MUTED)
            col += 1
            if col >= columns:
                col = 0
                row += 1
        self.image_selected_material_ids.intersection_update(visible_ids)

    def select_image_material(self, material_id):
        self.image_selected_material_ids = {material_id}

    def insert_image_material_ref(self, material_id):
        material = self.materials_by_id().get(material_id)
        if not material:
            return
        self.image_prompt_text.focus_set()
        self.image_prompt_text.insert("insert", f" @{material.alias} ")
        self.log(f"已插入图片素材引用：@{material.alias}")
        return "break"

    def refresh_one_material_tree(self, tree, image_cache, keyword, asset_type):
        if tree is None:
            return
        for item_id in tree.get_children():
            tree.delete(item_id)
        image_cache.clear()
        for item in self.materials:
            display = f"{item.id} @{item.alias} {Path(item.path).name} {item.tags}"
            if keyword and keyword not in display.lower():
                continue
            if asset_type and asset_type != "全部" and asset_type not in item.tags:
                continue
            image = None
            thumb = create_thumbnail(item)
            if thumb:
                try:
                    image = PhotoImage(file=thumb)
                    image_cache[item.id] = image
                except Exception:
                    image = None
            tree.insert(
                "",
                END,
                iid=item.id,
                text="",
                image=image,
                values=(f"@{item.alias}", item.tags, Path(item.path).name),
            )

    def edit_selected_material(self):
        ids = self.selected_material_ids()
        if not ids:
            messagebox.showinfo("编辑资产", "请先选择一个素材。")
            return
        item = next((material for material in self.materials if material.id == ids[0]), None)
        if not item:
            return
        win = Toplevel(self.root)
        win.title("编辑资产")
        win.geometry("460x220")
        alias_var = StringVar(value=item.alias)
        tags_var = StringVar(value=item.tags if item.tags in self.material_groups else (self.material_groups[0] if self.material_groups else "其他"))
        row1 = Frame(win, padx=10, pady=10)
        row1.pack(fill=X)
        Label(row1, text="引用名", width=10, anchor="w").pack(side=LEFT)
        Entry(row1, textvariable=alias_var).pack(side=LEFT, fill=X, expand=True)
        row2 = Frame(win, padx=10, pady=4)
        row2.pack(fill=X)
        Label(row2, text="分类/标签", width=10, anchor="w").pack(side=LEFT)
        ttk.Combobox(row2, textvariable=tags_var, values=self.material_groups, state="readonly", style="Dark.TCombobox").pack(side=LEFT, fill=X, expand=True)

        def save():
            existing = [material.alias for material in self.materials if material.id != item.id]
            item.alias = unique_alias(alias_var.get(), existing, item.alias)
            item.tags = tags_var.get().strip()
            self.persist_materials()
            self.refresh_materials()
            self.log(f"资产已更新：@{item.alias}")
            win.destroy()

        actions = Frame(win, padx=10, pady=10)
        actions.pack(fill=X)
        Button(actions, text="保存", command=save).pack(side=RIGHT)
        Button(actions, text="取消", command=win.destroy).pack(side=RIGHT, padx=(0, 8))

    def configure_material_groups(self):
        win = Toplevel(self.root)
        win.title("配置分组")
        win.geometry("420x360")
        win.transient(self.root)
        listbox = Listbox(
            win,
            bg=COLOR_INPUT,
            fg=COLOR_TEXT,
            selectbackground=COLOR_ACCENT_DARK,
            selectforeground="#ffffff",
            activestyle="none",
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
        )
        listbox.pack(fill=BOTH, expand=True, padx=10, pady=(10, 6))
        name_var = StringVar()
        row = Frame(win, padx=10)
        row.pack(fill=X)
        Entry(row, textvariable=name_var).pack(side=LEFT, fill=X, expand=True)

        def refresh_list():
            listbox.delete(0, END)
            for group in self.material_groups:
                listbox.insert(END, group)

        def add_group():
            name = name_var.get().strip()
            if not name:
                return
            if name not in self.material_groups:
                self.material_groups.append(name)
                self.persist_material_groups()
                self.update_group_combos()
                refresh_list()
                self.log(f"已新增资产分组：{name}")
            name_var.set("")

        def delete_group():
            selection = listbox.curselection()
            if not selection:
                return
            name = self.material_groups[selection[0]]
            if any(item.tags == name for item in self.materials):
                messagebox.showinfo("删除分组", "该分组下还有图片资源，请先调整图片分组。", parent=win)
                return
            self.material_groups = [group for group in self.material_groups if group != name]
            self.persist_material_groups()
            self.update_group_combos()
            refresh_list()
            self.log(f"已删除资产分组：{name}")

        Button(row, text="新增", command=add_group).pack(side=LEFT, padx=(8, 0))
        actions = Frame(win, padx=10, pady=10)
        actions.pack(fill=X)
        Button(actions, text="删除选中分组", command=delete_group).pack(side=LEFT)
        Button(actions, text="关闭", command=win.destroy).pack(side=RIGHT)
        refresh_list()

    def prompt_template_names(self, kind):
        templates = self.image_prompt_templates if kind == "image" else self.rewrite_prompt_templates
        return [item["name"] for item in templates]

    def selected_prompt_template(self, kind):
        templates = self.image_prompt_templates if kind == "image" else self.rewrite_prompt_templates
        var = self.image_template_var if kind == "image" else self.rewrite_template_var
        selected = var.get().strip()
        return next((item for item in templates if item["name"] == selected), templates[0] if templates else {"name": "", "template": ""})

    def persist_image_prompt_templates(self):
        write_json(IMAGE_PROMPT_TEMPLATES_FILE, self.image_prompt_templates)

    def persist_rewrite_prompt_templates(self):
        write_json(REWRITE_PROMPT_TEMPLATES_FILE, self.rewrite_prompt_templates)

    def persist_rewrite_history(self):
        write_json(REWRITE_HISTORY_FILE, self.rewrite_history[:100])

    def refresh_prompt_template_combos(self):
        if hasattr(self, "image_template_combo"):
            names = self.prompt_template_names("image")
            self.image_template_combo.configure(values=names)
            if self.image_template_var.get() not in names and names:
                self.image_template_var.set(names[0])
        if hasattr(self, "rewrite_template_combo"):
            names = self.prompt_template_names("rewrite")
            self.rewrite_template_combo.configure(values=names)
            if self.rewrite_template_var.get() not in names and names:
                self.rewrite_template_var.set(names[0])

    def open_prompt_template_manager(self, kind):
        title = "图片提示词模板" if kind == "image" else "文案改写提示词模板"
        templates = self.image_prompt_templates if kind == "image" else self.rewrite_prompt_templates
        selected_var = self.image_template_var if kind == "image" else self.rewrite_template_var
        win = Toplevel(self.root)
        win.title(f"自定义{title}")
        win.geometry("760x520")
        win.transient(self.root)

        left = Frame(win, padx=10, pady=10)
        left.pack(side=LEFT, fill=Y)
        listbox = Listbox(
            left,
            width=24,
            bg=COLOR_INPUT,
            fg=COLOR_TEXT,
            selectbackground=COLOR_ACCENT_DARK,
            selectforeground="#ffffff",
            activestyle="none",
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
        )
        listbox.pack(fill=BOTH, expand=True)

        right = Frame(win, padx=10, pady=10)
        right.pack(side=RIGHT, fill=BOTH, expand=True)
        Label(right, text="模板名称", anchor="w").pack(fill=X)
        name_var = StringVar()
        Entry(right, textvariable=name_var).pack(fill=X, pady=(4, 8))
        hint = "可使用 {prompt} 代表当前图片提示词。" if kind == "image" else "必须使用或自动追加 {source} 原始文案。"
        Label(right, text=hint, anchor="w", fg=COLOR_MUTED).pack(fill=X, pady=(0, 4))
        template_text = Text(right, wrap="word", height=18)
        template_text.pack(fill=BOTH, expand=True)

        def refresh_list(select_name=None):
            listbox.delete(0, END)
            for item in templates:
                listbox.insert(END, item["name"])
            target = select_name or selected_var.get()
            for index, item in enumerate(templates):
                if item["name"] == target:
                    listbox.selection_clear(0, END)
                    listbox.selection_set(index)
                    listbox.activate(index)
                    listbox.see(index)
                    load_selection()
                    break

        def current_index():
            selection = listbox.curselection()
            return selection[0] if selection else None

        def load_selection(_event=None):
            index = current_index()
            if index is None or index >= len(templates):
                return
            item = templates[index]
            name_var.set(item["name"])
            template_text.delete("1.0", END)
            template_text.insert("1.0", item["template"])

        def save_template():
            name = name_var.get().strip()
            template = template_text.get("1.0", END).strip()
            if not name or not template:
                messagebox.showinfo(title, "请填写模板名称和模板内容。", parent=win)
                return
            index = current_index()
            duplicate = next((i for i, item in enumerate(templates) if item["name"] == name and i != index), None)
            if duplicate is not None:
                messagebox.showinfo(title, "模板名称已存在，请换一个名称。", parent=win)
                return
            if index is None or index >= len(templates):
                templates.append({"name": name, "template": template})
            else:
                templates[index] = {"name": name, "template": template}
            selected_var.set(name)
            if kind == "image":
                self.persist_image_prompt_templates()
            else:
                self.persist_rewrite_prompt_templates()
            self.refresh_prompt_template_combos()
            refresh_list(name)
            self.log(f"已保存{title}：{name}")

        def new_template():
            listbox.selection_clear(0, END)
            name_var.set("")
            template_text.delete("1.0", END)
            template_text.insert("1.0", "{prompt}" if kind == "image" else "{source}")

        def delete_template():
            index = current_index()
            if index is None or index >= len(templates):
                return
            if len(templates) <= 1:
                messagebox.showinfo(title, "至少保留一个模板。", parent=win)
                return
            name = templates[index]["name"]
            if not messagebox.askyesno(title, f"确定删除模板“{name}”？", parent=win):
                return
            del templates[index]
            selected_var.set(templates[0]["name"])
            if kind == "image":
                self.persist_image_prompt_templates()
            else:
                self.persist_rewrite_prompt_templates()
            self.refresh_prompt_template_combos()
            refresh_list()

        listbox.bind("<<ListboxSelect>>", load_selection)
        actions = Frame(right, pady=8)
        actions.pack(fill=X)
        Button(actions, text="新建", command=new_template).pack(side=LEFT)
        Button(actions, text="删除", command=delete_template).pack(side=LEFT, padx=(8, 0))
        Button(actions, text="保存", command=save_template).pack(side=RIGHT)
        Button(actions, text="关闭", command=win.destroy).pack(side=RIGHT, padx=(0, 8))
        refresh_list()

    def apply_selected_image_template(self):
        item = self.selected_prompt_template("image")
        current = self.image_prompt_text.get("1.0", END).strip()
        content = apply_prompt_template(item.get("template", ""), "prompt", current)
        self.image_prompt_text.delete("1.0", END)
        self.image_prompt_text.insert("1.0", content)
        self.log(f"已调用图片提示词模板：{item.get('name', '')}")

    def rewrite_copy_async(self):
        source = self.rewrite_input_text.get("1.0", END).strip()
        if not source:
            messagebox.showwarning("文案改写", "请先输入需要改写的视频文案。")
            return
        template = self.selected_prompt_template("rewrite")
        prompt = apply_prompt_template(template.get("template", ""), "source", source)
        self.log(f"文案改写中：已使用模板 {template.get('name', '')}")
        thread = threading.Thread(target=self.rewrite_copy_worker, args=(prompt, source, template.get("name", "")), daemon=True)
        thread.start()

    def rewrite_copy_worker(self, prompt, source="", template_name=""):
        try:
            result = chat_completion_text(
                prompt,
                text_value(self.settings.get("text_api_key")).strip(),
                text_value(self.settings.get("text_base_url") or "https://api.openai.com/v1"),
                text_value(self.settings.get("text_model") or TEXT_MODEL_NAME),
            )
            if not result:
                raise RuntimeError("文本模型没有返回改写结果")
            self.rewrite_history.insert(0, {
                "id": uuid.uuid4().hex[:12],
                "created_at": now_text(),
                "template": template_name,
                "source": source,
                "output": result,
            })
            self.rewrite_history = self.rewrite_history[:100]
            self.persist_rewrite_history()
            self.event_queue.put(("rewrite_output", result))
            self.event_queue.put(("log", "文案改写完成"))
        except Exception as exc:
            self.event_queue.put(("log", f"文案改写失败：{exc}"))

    def show_rewrite_history(self):
        win = Toplevel(self.root)
        win.title("文案改写历史记录")
        win.geometry("820x520")
        win.transient(self.root)
        left = Frame(win, padx=10, pady=10, width=260)
        left.pack(side=LEFT, fill=Y)
        left.pack_propagate(False)
        listbox = Listbox(left)
        listbox.pack(fill=BOTH, expand=True)
        right = Frame(win, padx=(0, 10), pady=10)
        right.pack(side=RIGHT, fill=BOTH, expand=True)
        detail = Text(right, wrap="word")
        detail.pack(fill=BOTH, expand=True)
        actions = Frame(right)
        actions.pack(fill=X, pady=(8, 0))

        def record_label(record):
            created_at = record.get("created_at", "")
            template = record.get("template", "") or "未命名模板"
            source = compact_text(record.get("source", ""), 22)
            return compact_text(f"{created_at}  {template}  {source}", 48)

        for record in self.rewrite_history:
            listbox.insert(END, record_label(record))

        def selected_record():
            selection = listbox.curselection()
            if not selection:
                return None
            index = selection[0]
            if index >= len(self.rewrite_history):
                return None
            return self.rewrite_history[index]

        def show_selected(_event=None):
            record = selected_record()
            detail.delete("1.0", END)
            if not record:
                return
            detail.insert("1.0", (
                f"时间：{record.get('created_at', '')}\n"
                f"模板：{record.get('template', '')}\n\n"
                f"原文：\n{record.get('source', '')}\n\n"
                f"改写结果：\n{record.get('output', '')}"
            ))

        def fill_source():
            record = selected_record()
            if not record:
                return
            self.rewrite_input_text.delete("1.0", END)
            self.rewrite_input_text.insert("1.0", record.get("source", ""))
            win.destroy()

        def fill_output():
            record = selected_record()
            if not record:
                return
            self.rewrite_output_text.delete("1.0", END)
            self.rewrite_output_text.insert("1.0", record.get("output", ""))
            win.destroy()

        Button(actions, text="填入原文", command=fill_source).pack(side=LEFT)
        Button(actions, text="填入结果", command=fill_output).pack(side=LEFT, padx=(8, 0))
        Button(actions, text="关闭", command=win.destroy).pack(side=RIGHT)
        listbox.bind("<<ListboxSelect>>", show_selected)
        if self.rewrite_history:
            listbox.selection_set(0)
            show_selected()

    def use_rewrite_output(self):
        text = self.rewrite_output_text.get("1.0", END).strip()
        if not text:
            messagebox.showinfo("填入生成页", "请先生成改写结果。")
            return
        self.prompt_text.delete("1.0", END)
        self.prompt_text.insert("1.0", text)
        self.show_section("generate")
        self.log("已把改写结果填入视频生成页")

    def update_image_size_from_dimensions(self):
        width = text_value(self.image_width_var.get()).strip()
        height = text_value(self.image_height_var.get()).strip()
        if width.isdigit() and height.isdigit():
            self.image_size_var.set(f"{int(width)}x{int(height)}")

    def set_image_aspect_size(self, label, width, height):
        self.image_aspect_var.set(label)
        self.image_width_var.set(str(width))
        self.image_height_var.set(str(height))
        self.image_size_var.set(f"{int(width)}x{int(height)}")
        self.image_status_var.set(self.image_size_var.get())

    def current_image_size(self):
        width = text_value(self.image_width_var.get()).strip()
        height = text_value(self.image_height_var.get()).strip()
        if not width.isdigit() or not height.isdigit():
            raise ValueError("图片宽高必须是数字。")
        width_int = int(width)
        height_int = int(height)
        if width_int <= 0 or height_int <= 0:
            raise ValueError("图片宽高必须大于 0。")
        size = f"{width_int}x{height_int}"
        self.image_size_var.set(size)
        return size

    def choose_image_references(self):
        self.log("打开图片参考图选择窗口")
        paths = filedialog.askopenfilenames(
            title="上传图片生成参考图",
            filetypes=[("图片", "*.png *.jpg *.jpeg *.webp *.bmp"), ("所有文件", "*.*")]
        )
        if not paths:
            self.log("未选择图片参考图")
            return
        imported_ids = self.import_reference_materials(paths)
        refs = list(self.image_reference_paths)
        for material_id in imported_ids:
            if material_id not in refs:
                refs.append(material_id)
        self.set_image_references(refs)
        self.log(f"已选择图片参考图 {len(self.image_reference_paths)} 张")

    def choose_video_references(self):
        self.log("打开视频参考图选择窗口")
        paths = filedialog.askopenfilenames(
            title="上传视频生成参考图",
            filetypes=[("图片", "*.png *.jpg *.jpeg *.webp *.bmp"), ("所有文件", "*.*")]
        )
        if not paths:
            self.log("未选择视频参考图")
            return
        imported_ids = self.import_reference_materials(paths)
        refs = list(self.video_reference_paths)
        for material_id in imported_ids:
            if material_id not in refs:
                refs.append(material_id)
        self.set_video_references(refs)
        self.log(f"已选择视频参考图 {len(self.video_reference_paths)} 张")

    def import_reference_materials(self, paths):
        imported_ids = []
        group = "上传参考图"
        if group not in self.material_groups:
            self.material_groups.append(group)
            self.persist_material_groups()
        for path in paths:
            src = Path(path)
            if not src.exists():
                continue
            material_id = uuid.uuid4().hex[:12]
            dest = MATERIAL_DIR / f"{material_id}_{safe_name(src.name)}"
            try:
                shutil.copy2(src, dest)
            except Exception as exc:
                self.log(f"参考图导入失败：{src} {exc}")
                continue
            alias = unique_alias(src.stem, [material.alias for material in self.materials], f"ref_{material_id[:6]}")
            self.materials.append(Material(
                id=material_id,
                alias=alias,
                path=str(dest),
                added_at=now_text(),
                tags=group,
            ))
            imported_ids.append(material_id)
        if imported_ids:
            self.persist_materials()
            self.refresh_materials()
        return imported_ids

    def update_image_reference_label(self):
        refs = list(self.image_reference_paths)[:MAX_REFERENCE_IMAGES]
        if not refs:
            self.image_reference_var.set("未上传参考图")
            self.refresh_reference_strip("image")
            return
        materials = self.materials_by_id()
        names = []
        for ref in refs:
            if ref in materials:
                names.append(f"@{materials[ref].alias}")
            else:
                names.append(Path(ref).name)
        self.image_reference_var.set(f"参考图 {len(names)} 张：{', '.join(names[:3])}" + (" ..." if len(names) > 3 else ""))
        self.refresh_reference_strip("image")

    def set_image_references(self, refs):
        clean_refs = []
        materials = self.materials_by_id()
        for ref in refs or []:
            ref = text_value(ref).strip()
            if not ref:
                continue
            if ref in materials or Path(ref).exists():
                clean_refs.append(ref)
        self.image_reference_paths = clean_refs[:MAX_REFERENCE_IMAGES]
        self.update_image_reference_label()

    def update_video_reference_label(self):
        refs = list(self.video_reference_paths)[:MAX_REFERENCE_IMAGES]
        if not refs:
            self.video_reference_var.set("未上传参考图")
            self.refresh_reference_strip("video")
            return
        materials = self.materials_by_id()
        names = []
        for ref in refs:
            if ref in materials:
                names.append(f"@{materials[ref].alias}")
            else:
                names.append(Path(ref).name)
        self.video_reference_var.set(f"参考图 {len(names)} 张：{', '.join(names[:3])}" + (" ..." if len(names) > 3 else ""))
        self.refresh_reference_strip("video")

    def set_video_references(self, refs):
        clean_refs = []
        materials = self.materials_by_id()
        for ref in refs or []:
            ref = text_value(ref).strip()
            if not ref:
                continue
            if ref in materials or Path(ref).exists():
                clean_refs.append(ref)
        self.video_reference_paths = clean_refs[:MAX_REFERENCE_IMAGES]
        self.update_video_reference_label()

    def refresh_reference_strip(self, kind):
        frame = getattr(self, f"{kind}_reference_frame", None)
        if frame is None:
            return
        for child in frame.winfo_children():
            child.destroy()
        refs = list(getattr(self, f"{kind}_reference_paths", []))[:MAX_REFERENCE_IMAGES]
        cache = getattr(self, f"{kind}_reference_images", None)
        if cache is not None:
            for key in list(cache.keys()):
                if str(key).startswith("strip_"):
                    cache.pop(key, None)
        materials = self.materials_by_id()
        for ref in refs:
            material = materials.get(ref)
            path = material.path if material else ref
            temp = material or Material(id=uuid.uuid5(uuid.NAMESPACE_URL, str(path)).hex[:12], alias=Path(path).stem, path=path, added_at="")
            tile = Frame(frame, width=82, height=106, padx=3, pady=3, highlightthickness=1, highlightbackground=COLOR_BORDER, bg=COLOR_CARD)
            tile.pack(side=LEFT, padx=(0, 6), pady=(0, 4))
            tile.pack_propagate(False)
            top = Frame(tile, bg=COLOR_CARD)
            top.pack(fill=X)
            Button(top, text="×", width=2, command=lambda value=ref, k=kind: self.remove_reference(k, value)).pack(side=RIGHT)
            image = None
            thumb = create_thumbnail(temp, size=68)
            if thumb:
                try:
                    image = PhotoImage(file=thumb)
                    if cache is not None:
                        cache[f"strip_{kind}_{ref}"] = image
                except Exception:
                    image = None
            Label(tile, image=image, text="" if image else "无预览", width=68, height=64, bg=COLOR_CARD).pack()
            name = f"@{material.alias}" if material else Path(path).name
            Label(tile, text=compact_text(name, 12), wraplength=72, justify="center", bg=COLOR_CARD, fg=COLOR_MUTED).pack(fill=X)

    def remove_reference(self, kind, ref):
        attr = f"{kind}_reference_paths"
        refs = [item for item in getattr(self, attr, []) if item != ref]
        if kind == "image":
            self.set_image_references(refs)
        else:
            self.set_video_references(refs)

    def generate_image_async(self):
        prompt = self.image_prompt_text.get("1.0", END).strip()
        if not prompt:
            messagebox.showwarning("图片生成", "请先输入图片提示词。")
            return
        refs = self.resolve_prompt_refs(prompt)
        for ref in self.image_reference_paths:
            if ref not in refs:
                refs.append(ref)
        refs = refs[:MAX_REFERENCE_IMAGES]
        try:
            size = self.current_image_size()
        except ValueError as exc:
            messagebox.showwarning("图片尺寸", str(exc))
            return
        quality = self.image_quality_var.get().strip() or "auto"
        task = ImageTask(
            id=uuid.uuid4().hex[:12],
            prompt=prompt,
            size=size,
            references=refs,
            quality=quality,
            status="queued",
        )
        self.image_tasks.insert(0, task)
        self.persist_image_tasks()
        self.refresh_image_tasks()
        self.image_status_var.set(task.size)
        self.log(f"已加入图片生成任务：{task.id}，尺寸 {task.size}，参考图 {len(task.references)} 张")
        thread = threading.Thread(target=self.generate_image_worker, args=(task.id,), daemon=True)
        thread.start()

    def generate_image_worker(self, task_id):
        task = next((item for item in self.image_tasks if item.id == task_id), None)
        if not task:
            return
        try:
            self.update_image_task(task, status="submitting")
            materials = self.materials_by_id()
            reference_paths = []
            for ref in task.references:
                if ref in materials:
                    reference_paths.append(materials[ref].path)
                elif Path(ref).exists():
                    reference_paths.append(ref)
            path = generate_image_file(
                task.prompt,
                text_value(self.settings.get("image_api_key")).strip(),
                text_value(self.settings.get("image_base_url") or "https://api.openai.com/v1"),
                text_value(self.settings.get("image_model") or IMAGE_MODEL_NAME),
                task.size,
                text_value(self.settings.get("image_poll_path") or DEFAULT_IMAGE_POLL_PATH),
                lambda status: self.event_queue.put(("image_task_status", (task.id, status))),
                reference_paths,
                task.quality,
            )
            task.output_path = str(path)
            self.update_image_task(task, status="done", output_path=str(path))
            self.event_queue.put(("generated_image", str(path)))
            self.event_queue.put(("log", f"图片生成完成：{path}"))
        except Exception as exc:
            friendly_error = friendly_image_error(exc)
            task.error = friendly_error
            self.update_image_task(task, status="failed", error=friendly_error)
            (APP_DIR / "image_generation_error.log").write_text(
                f"[{now_text()}]\n{traceback.format_exc()}\n",
                encoding="utf-8",
            )
            self.event_queue.put(("image_status", "生成失败"))
            self.event_queue.put(("log", friendly_error))

    def update_image_task(self, task, status=None, request_id=None, output_path=None, error=None):
        if status:
            task.status = status
        if request_id is not None:
            task.request_id = request_id
        if output_path is not None:
            task.output_path = output_path
        if error is not None:
            task.error = error
        task.updated_at = now_text()
        self.persist_image_tasks()
        self.event_queue.put(("refresh_image_tasks", None))

    def image_task_status_label(self, status):
        status_text = text_value(status).strip()
        if not status_text:
            return "待生成"
        if status_text.startswith("已提交：") or status_text.startswith("生成中：") or status_text.startswith("任务状态："):
            return status_text
        labels = dict(STATUS_LABELS)
        labels.update({
            "refreshing": "刷新中",
            "pending": "待生成",
            "error": "失败",
            "expired": "已过期",
            "canceled": "已取消",
            "cancelled": "已取消",
        })
        return labels.get(status_text, status_text)

    def refresh_image_tasks(self):
        if not hasattr(self, "image_task_tree"):
            return
        selection = self.image_task_tree.selection()
        focused = self.image_task_tree.focus()
        for item_id in self.image_task_tree.get_children():
            self.image_task_tree.delete(item_id)
        for task in self.image_tasks:
            status_label = self.image_task_status_label(task.status)
            output = Path(task.output_path).name if task.output_path else compact_text(task.error or status_label, 60)
            self.image_task_tree.insert("", END, iid=task.id, values=(
                status_label,
                compact_text(task.prompt, 60),
                str(len(task.references)),
                task.request_id,
                output,
                task.updated_at,
            ))
        existing_ids = set(self.image_task_tree.get_children())
        kept_selection = [item_id for item_id in selection if item_id in existing_ids]
        if kept_selection:
            self.image_task_tree.selection_set(kept_selection)
        if focused in existing_ids:
            self.image_task_tree.focus(focused)

    def selected_image_task(self):
        if not hasattr(self, "image_task_tree"):
            return None
        selection = self.image_task_tree.selection()
        if not selection:
            return None
        return next((task for task in self.image_tasks if task.id == selection[0]), None)

    def show_selected_image_task(self):
        task = self.selected_image_task()
        self.show_image_task(task)

    def open_image_task_from_event(self, event):
        item_id = self.image_task_tree.identify_row(event.y)
        if not item_id:
            return
        self.image_task_tree.selection_set(item_id)
        self.image_task_tree.focus(item_id)
        task = next((item for item in self.image_tasks if item.id == item_id), None)
        if task:
            self.log(f"查看图片任务：{task.id}")
        self.show_image_task(task)

    def reuse_image_task_from_event(self, event):
        item_id = self.image_task_tree.identify_row(event.y)
        if not item_id:
            return
        self.image_task_tree.selection_set(item_id)
        self.image_task_tree.focus(item_id)
        task = next((item for item in self.image_tasks if item.id == item_id), None)
        self.reuse_image_task(task)

    def reuse_image_task(self, task):
        if not task:
            return
        self.image_prompt_text.delete("1.0", END)
        self.image_prompt_text.insert("1.0", task.prompt)
        if task.size:
            self.image_size_var.set(task.size)
            size_match = re.match(r"^\s*(\d+)\s*x\s*(\d+)\s*$", task.size, re.IGNORECASE)
            if size_match:
                self.image_width_var.set(size_match.group(1))
                self.image_height_var.set(size_match.group(2))
        if getattr(task, "quality", ""):
            self.image_quality_var.set(task.quality)
        self.set_image_references(task.references)
        self.image_status_var.set("已复用任务参数")
        self.log(f"已复用图片任务提示词和参考图：{task.id}")

    def show_image_task(self, task):
        if not task:
            return
        task.output_path = resolve_image_output_path(task.output_path, task)
        if task.output_path and Path(task.output_path).exists():
            self.show_generated_image(task.output_path)
        elif task.error:
            self.generated_preview_image = None
            if getattr(self, "generated_image_label", None):
                self.generated_image_label.configure(
                    image="",
                    text=f"任务失败\n\n{task.error}\n\n可右键该任务选择“刷新任务状态”查询一次最新状态。",
                )
            self.image_status_var.set("任务失败，可右键刷新状态")
            self.log(f"查看失败图片任务：{task.id}")
        else:
            self.generated_preview_image = None
            status_label = self.image_task_status_label(task.status)
            if getattr(self, "generated_image_label", None):
                self.generated_image_label.configure(image="", text=f"任务状态：{status_label}")
            self.image_status_var.set(status_label)

    def show_image_task_context_menu(self, event):
        item_id = self.image_task_tree.identify_row(event.y)
        if not item_id:
            return
        self.image_task_tree.selection_set(item_id)
        self.image_task_tree.focus(item_id)
        menu = Menu(self.root, tearoff=0)
        menu.add_command(label="复用提示词和参考图", command=lambda: self.reuse_image_task(self.selected_image_task()))
        menu.add_command(label="查看原图", command=self.open_selected_image_task_output)
        menu.add_command(label="打开所在文件夹", command=self.open_selected_image_task_folder)
        menu.add_command(label="加入资产库", command=self.add_selected_image_task_to_materials)
        menu.add_separator()
        menu.add_command(label="刷新任务状态", command=self.refresh_selected_image_task_once)
        menu.add_command(label="删除任务", command=self.delete_selected_image_task)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def selected_image_task_output_path(self):
        task = self.selected_image_task()
        if not task:
            return ""
        output_path = resolve_image_output_path(task.output_path, task)
        return output_path if output_path and Path(output_path).exists() else ""

    def open_selected_image_task_output(self):
        output_path = self.selected_image_task_output_path()
        if not output_path:
            messagebox.showinfo("查看原图", "该图片任务还没有可用的本地结果。")
            return
        self.open_local_image(output_path)

    def open_selected_image_task_folder(self):
        output_path = self.selected_image_task_output_path()
        if not output_path:
            messagebox.showinfo("打开所在文件夹", "该图片任务还没有可用的本地结果。")
            return
        path = Path(output_path)
        try:
            subprocess.Popen(["explorer", "/select,", str(path)])
        except Exception:
            os.startfile(path.parent)

    def add_selected_image_task_to_materials(self):
        task = self.selected_image_task()
        output_path = self.selected_image_task_output_path()
        if not task or not output_path:
            messagebox.showinfo("加入资产库", "该图片任务还没有可用的本地结果。")
            return
        self.last_generated_image_path = output_path
        self.last_generated_image_task_id = task.id
        self.add_generated_image_to_materials()

    def delete_selected_image_task(self):
        task = self.selected_image_task()
        if not task:
            return
        if not messagebox.askyesno("删除图片任务", "确定删除选中的图片任务？"):
            return
        self.image_tasks = [item for item in self.image_tasks if item.id != task.id]
        self.persist_image_tasks()
        self.refresh_image_tasks()
        self.image_status_var.set("任务已删除")
        self.log(f"已删除图片任务：{task.id}")

    def refresh_selected_image_task_once(self):
        task = self.selected_image_task()
        if not task:
            messagebox.showinfo("刷新图片任务", "请先在图片任务队列中选择一条任务。")
            return
        if task.output_path and Path(task.output_path).exists():
            self.show_generated_image(task.output_path)
            return
        if not task.request_id:
            messagebox.showinfo("刷新图片任务", "这条任务还没有服务器任务 ID，无法刷新。")
            return
        task.status = "refreshing"
        task.error = ""
        task.updated_at = now_text()
        self.persist_image_tasks()
        self.refresh_image_tasks()
        self.log(f"刷新图片任务状态：{task.id}")
        threading.Thread(target=self.refresh_image_task_once_worker, args=(task.id,), daemon=True).start()

    def refresh_image_task_once_worker(self, task_id):
        task = next((item for item in self.image_tasks if item.id == task_id), None)
        if not task:
            return
        try:
            path, state, result = query_image_job_once(
                task.prompt,
                text_value(self.settings.get("image_api_key")).strip(),
                text_value(self.settings.get("image_base_url") or "https://api.openai.com/v1"),
                task.request_id,
                text_value(self.settings.get("image_poll_path") or DEFAULT_IMAGE_POLL_PATH),
            )
            if path:
                task.output_path = str(path)
                self.update_image_task(task, status="done", output_path=str(path), error="")
                self.event_queue.put(("generated_image", str(path)))
                self.event_queue.put(("log", f"图片任务刷新完成：{path}"))
                return
            if state in ("failed", "error", "expired", "canceled", "cancelled"):
                error_text = result.get("error") or result.get("message") or json.dumps(result, ensure_ascii=False)
                task.error = friendly_image_error(text_value(error_text))
                self.update_image_task(task, status="failed", error=task.error)
                self.event_queue.put(("log", f"图片任务刷新失败：{task.error}"))
                return
            task.error = ""
            self.update_image_task(task, status=state or "processing", error="")
            self.event_queue.put(("image_status", f"任务状态：{state or task.request_id}"))
            self.event_queue.put(("log", f"图片任务状态已刷新：{task.id} {state or task.request_id}"))
        except Exception as exc:
            task.error = friendly_image_error(exc)
            self.update_image_task(task, status="failed", error=task.error)
            self.event_queue.put(("log", f"图片任务刷新失败：{task.error}"))

    def show_generated_image(self, path):
        self.last_generated_image_path = path
        task = next((item for item in self.image_tasks if resolve_image_output_path(item.output_path, item) == str(path)), None)
        self.last_generated_image_task_id = task.id if task else ""
        image = None
        preview_id = "generated_preview_" + uuid.uuid5(uuid.NAMESPACE_URL, str(Path(path).resolve())).hex[:12]
        temp_material = Material(id=preview_id, alias="preview", path=path, added_at=now_text())
        thumb = create_thumbnail(temp_material, size=320)
        if thumb:
            try:
                image = PhotoImage(file=thumb)
            except Exception:
                image = None
        self.generated_preview_image = image
        if getattr(self, "generated_image_label", None):
            if image:
                self.generated_image_label.configure(image=image, text="")
            else:
                self.generated_image_label.configure(text=Path(path).name, image="")
            self.generated_image_label.bind("<Double-Button-1>", lambda _event, image_path=path: self.open_local_image(image_path))
        self.image_status_var.set("生成完成")

    def add_generated_image_to_materials(self):
        if not self.last_generated_image_path or not Path(self.last_generated_image_path).exists():
            messagebox.showinfo("加入资产库", "请先生成一张图片。")
            return
        src = Path(self.last_generated_image_path)
        self.log(f"打开加入资产库窗口：{src.name}")
        win = Toplevel(self.root)
        win.title("加入资产库")
        win.geometry("420x180")
        alias_var = StringVar(value=safe_alias(src.stem, "ai_image"))
        group_var = StringVar(value="AI生成")
        row1 = Frame(win, padx=10, pady=10)
        row1.pack(fill=X)
        Label(row1, text="图片名称", width=10, anchor="w").pack(side=LEFT)
        Entry(row1, textvariable=alias_var).pack(side=LEFT, fill=X, expand=True)
        row2 = Frame(win, padx=10, pady=4)
        row2.pack(fill=X)
        Label(row2, text="分组", width=10, anchor="w").pack(side=LEFT)
        ttk.Combobox(row2, textvariable=group_var, values=["产品", "人物", "场景", "AI生成", "其他"], width=18).pack(side=LEFT)

        def save():
            material_id = uuid.uuid4().hex[:12]
            dest = MATERIAL_DIR / f"{material_id}_{safe_name(src.name)}"
            shutil.copy2(src, dest)
            alias = unique_alias(alias_var.get(), [material.alias for material in self.materials], f"ai_image_{material_id[:6]}")
            source_task = None
            if self.last_generated_image_task_id:
                source_task = next((item for item in self.image_tasks if item.id == self.last_generated_image_task_id), None)
            if source_task is None:
                source_task = next((item for item in self.image_tasks if resolve_image_output_path(item.output_path, item) == str(src)), None)
            self.materials.append(Material(
                id=material_id,
                alias=alias,
                path=str(dest),
                added_at=now_text(),
                tags=group_var.get().strip() or "AI生成",
                prompt=source_task.prompt if source_task else "",
                references=list(source_task.references) if source_task else [],
            ))
            self.persist_materials()
            self.refresh_materials()
            self.log(f"生成图片已加入资产库：@{alias}")
            win.destroy()

        actions = Frame(win, padx=10, pady=10)
        actions.pack(fill=X)
        Button(actions, text="保存", command=save).pack(side=RIGHT)
        Button(actions, text="取消", command=win.destroy).pack(side=RIGHT, padx=(0, 8))
        self.position_near_widget(win, getattr(self, "add_generated_image_button", None))

    def position_near_widget(self, window, widget, width=420, height=180):
        window.update_idletasks()
        if widget is None:
            return
        try:
            x = widget.winfo_rootx()
            y = widget.winfo_rooty() - height - 8
            screen_w = window.winfo_screenwidth()
            screen_h = window.winfo_screenheight()
            x = max(0, min(x, screen_w - width - 8))
            if y < 0:
                y = widget.winfo_rooty() + widget.winfo_height() + 8
            y = max(0, min(y, screen_h - height - 40))
            window.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            pass

    def use_image_prompt_for_video(self):
        prompt = self.image_prompt_text.get("1.0", END).strip()
        if not prompt:
            return
        self.prompt_text.delete("1.0", END)
        self.prompt_text.insert("1.0", prompt)
        self.show_section("generate")
        self.log("已把图片提示词填入视频生成页")

    def add_task_from_form(self):
        prompt = self.prompt_text.get("1.0", END).strip()
        if not prompt:
            messagebox.showwarning("缺少提示词", "请先输入提示词。")
            return
        try:
            duration = int(self.duration_var.get())
        except ValueError:
            messagebox.showwarning("时长错误", "时长必须是 1-15 的整数。")
            return
        if duration < 1 or duration > 15:
            messagebox.showwarning("时长错误", "时长必须是 1-15 秒。")
            return

        refs = self.resolve_prompt_refs(prompt)
        selected = self.selected_material_ids()
        for item in selected:
            if item not in refs:
                refs.append(item)
        for item in self.video_reference_paths:
            if item not in refs:
                refs.append(item)
        refs = refs[:MAX_REFERENCE_IMAGES]
        if refs:
            self.set_video_references(refs)
        if refs and duration > 10:
            messagebox.showwarning("参考图模式限制", "使用参考图时，xAI 当前限制最长 10 秒。")
            return
        task = Task(
            id=uuid.uuid4().hex[:12],
            prompt=prompt,
            aspect_ratio=self.aspect_var.get(),
            duration=duration,
            resolution=self.resolution_var.get(),
            references=refs,
        )
        self.tasks.append(task)
        self.persist_tasks()
        self.refresh_tasks()
        self.log(f"已添加视频生成任务：{task.id}，参数 {task.aspect_ratio}/{task.duration}s/{task.resolution}，参考图 {len(task.references)} 张")

    def resolve_prompt_refs(self, prompt):
        aliases = set(re.findall(r"@([\w\-\u4e00-\u9fff]+)", prompt))
        refs = []
        for material in self.materials:
            if material.alias in aliases:
                refs.append(material.id)
        return refs

    def import_csv(self):
        path = filedialog.askopenfilename(title="导入 CSV", filetypes=[("CSV", "*.csv"), ("所有文件", "*.*")])
        if not path:
            return
        count = 0
        with open(path, "r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                prompt = (row.get("prompt") or row.get("提示词") or "").strip()
                if not prompt:
                    continue
                refs = self.resolve_prompt_refs(prompt)
                duration = int(row.get("duration") or row.get("时长") or self.duration_var.get())
                if refs and duration > 10:
                    duration = 10
                task = Task(
                    id=uuid.uuid4().hex[:12],
                    prompt=prompt,
                    aspect_ratio=(row.get("aspect_ratio") or row.get("比例") or self.aspect_var.get()).strip(),
                    duration=duration,
                    resolution=(row.get("resolution") or row.get("分辨率") or self.resolution_var.get()).strip(),
                    references=refs[:MAX_REFERENCE_IMAGES],
                )
                self.tasks.append(task)
                count += 1
        self.persist_tasks()
        self.refresh_tasks()
        self.log(f"CSV 已导入 {count} 条任务")

    def queue_all_pending(self):
        changed = 0
        for task in self.tasks:
            if task.status in ("queued", "failed"):
                task.status = "queued"
                task.error = ""
                task.updated_at = now_text()
                changed += 1
        self.persist_tasks()
        self.refresh_tasks()
        self.start_worker()
        self.log(f"已提交 {changed} 条待处理任务")

    def retry_failed(self):
        changed = 0
        for task in self.tasks:
            if task.status == "failed":
                task.status = "queued"
                task.error = ""
                task.updated_at = now_text()
                changed += 1
        self.persist_tasks()
        self.refresh_tasks()
        self.start_worker()
        self.log(f"已重试 {changed} 条失败任务")

    def save_done_videos(self):
        count = 0
        missing = 0
        target = Path(self.settings.get("output_dir") or OUTPUT_DIR)
        target.mkdir(parents=True, exist_ok=True)
        for task in self.tasks:
            if task.status == "done" and task.output_path:
                src = Path(task.output_path)
                if src.exists():
                    dest = target / src.name
                    if src.resolve() != dest.resolve():
                        shutil.copy2(src, dest)
                    count += 1
                else:
                    missing += 1
        self.log(f"已保存 {count} 个视频文件，缺失 {missing} 个")
        messagebox.showinfo("批量保存完成", f"已保存 {count} 个视频文件。\n缺失 {missing} 个。")

    def delete_selected_tasks(self):
        ids = {task.id for task in self.selected_tasks()}
        if not ids:
            messagebox.showinfo("删除任务", "请先勾选或选择要删除的视频任务。")
            return
        if not messagebox.askyesno("删除任务", f"确定删除 {len(ids)} 条任务？"):
            return
        self.tasks = [task for task in self.tasks if task.id not in ids]
        self.task_checked_ids.difference_update(ids)
        self.persist_tasks()
        self.refresh_tasks()
        self.log(f"已删除视频任务 {len(ids)} 条")

    def selected_tasks(self):
        ids = set(self.task_checked_ids)
        if not ids and hasattr(self, "task_tree"):
            ids = set(self.task_tree.selection())
        return [task for task in self.tasks if task.id in ids]

    def handle_task_tree_click(self, event):
        if self.task_tree.identify_region(event.x, event.y) != "cell":
            return
        if self.task_tree.identify_column(event.x) != "#2":
            return
        item_id = self.task_tree.identify_row(event.y)
        if not item_id:
            return
        if item_id in self.task_checked_ids:
            self.task_checked_ids.remove(item_id)
        else:
            self.task_checked_ids.add(item_id)
        self.refresh_tasks()
        return "break"

    def toggle_all_video_tasks(self):
        all_ids = {task.id for task in self.tasks}
        if all_ids and all_ids.issubset(self.task_checked_ids):
            self.task_checked_ids.clear()
            self.log("已取消全选视频任务")
        else:
            self.task_checked_ids = set(all_ids)
            self.log(f"已全选视频任务 {len(self.task_checked_ids)} 条")
        self.refresh_tasks()

    def start_checked_or_selected_tasks(self):
        self.start_selected_tasks()

    def pause_checked_or_selected_tasks(self):
        self.pause_selected_tasks()

    def show_task_context_menu(self, event):
        item_id = self.task_tree.identify_row(event.y)
        if not item_id:
            return
        if item_id not in self.task_tree.selection() and item_id not in self.task_checked_ids:
            self.task_tree.selection_set(item_id)
            self.task_tree.focus(item_id)

        menu = Menu(self.root, tearoff=0)
        menu.add_command(label="开始", command=self.start_selected_tasks)
        menu.add_command(label="暂停", command=self.pause_selected_tasks)
        menu.add_command(label="结束", command=self.end_selected_tasks)
        menu.add_separator()
        menu.add_command(label="查看失败原因", command=self.show_selected_task_error)
        menu.add_command(label="复用提示词", command=self.reuse_selected_task)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def start_selected_tasks(self):
        changed = 0
        for task in self.selected_tasks():
            if task.status == "done":
                continue
            if task.status == "paused" and task.request_id:
                task.status = "processing"
            else:
                task.status = "queued"
                task.request_id = ""
                task.output_path = ""
            task.error = ""
            task.updated_at = now_text()
            changed += 1
        if changed:
            self.persist_tasks()
            self.refresh_tasks()
            self.start_worker()
        self.log(f"已开始 {changed} 条任务")

    def pause_selected_tasks(self):
        changed = 0
        for task in self.selected_tasks():
            if task.status in ("done", "failed", "ended"):
                continue
            task.status = "paused"
            task.updated_at = now_text()
            changed += 1
        if changed:
            self.persist_tasks()
            self.refresh_tasks()
        self.log(f"已暂停 {changed} 条任务")

    def end_selected_tasks(self):
        changed = 0
        for task in self.selected_tasks():
            if task.status == "done":
                continue
            task.status = "ended"
            task.error = "用户已结束任务"
            task.updated_at = now_text()
            changed += 1
        if changed:
            self.persist_tasks()
            self.refresh_tasks()
        self.log(f"已结束 {changed} 条任务")

    def show_selected_task_error(self):
        tasks = self.selected_tasks()
        if not tasks:
            messagebox.showinfo("失败原因", "请先选择一条任务。")
            return
        task = tasks[0]
        messagebox.showinfo("失败原因 / 处理建议", task_error_detail(task))

    def reuse_selected_task(self):
        selection = self.task_tree.selection()
        if not selection:
            messagebox.showinfo("复用任务", "请先在右侧任务列表中选择一条任务。")
            return

        task_id = selection[0]
        task = next((item for item in self.tasks if item.id == task_id), None)
        if not task:
            messagebox.showwarning("复用任务", "选中的任务不存在，任务列表将刷新。")
            self.refresh_tasks()
            return

        self.prompt_text.delete("1.0", END)
        self.prompt_text.insert("1.0", task.prompt)
        self.aspect_var.set(task.aspect_ratio or "16:9")
        self.duration_var.set(str(task.duration or 6))
        self.resolution_var.set(task.resolution or "720p")

        available_refs = [ref for ref in task.references if self.material_tree.exists(ref)]
        self.material_tree.selection_set(available_refs)
        if available_refs:
            self.material_tree.see(available_refs[0])

        self.log(f"已复用任务 {task.id} 的提示词和参数")

    def refresh_tasks(self):
        if not hasattr(self, "task_tree"):
            return
        existing_task_ids = {task.id for task in self.tasks}
        self.task_checked_ids.intersection_update(existing_task_ids)
        selection = set(self.task_tree.selection())
        focused = self.task_tree.focus()
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        for index, task in enumerate(self.tasks, 1):
            params = f"{task.aspect_ratio} / {task.duration}s / {task.resolution}"
            output = Path(task.output_path).name if task.output_path else task_error_summary(task)
            self.task_tree.insert("", END, iid=task.id, values=(
                index,
                "☑" if task.id in self.task_checked_ids else "☐",
                STATUS_LABELS.get(task.status, task.status),
                task.prompt.replace("\n", " ")[:120],
                params,
                str(len(task.references)),
                task.request_id,
                output,
                task.updated_at,
            ))
        existing_ids = set(self.task_tree.get_children())
        kept_selection = [item_id for item_id in selection if item_id in existing_ids]
        if kept_selection:
            self.task_tree.selection_set(kept_selection)
        if focused in existing_ids:
            self.task_tree.focus(focused)

    def materials_by_id(self):
        return {item.id: item for item in self.materials}

    def persist_materials(self):
        write_json(MATERIALS_FILE, [item.__dict__ for item in self.materials])

    def persist_material_groups(self):
        write_json(GROUPS_FILE, self.material_groups)

    def persist_agent_conversations(self):
        data = []
        for item in self.agent_conversations:
            record = item.__dict__.copy()
            clean_messages = []
            for message in item.messages:
                content = text_value(message.get("content"))
                if not content.strip():
                    continue
                clean = {"role": message.get("role", "user"), "content": content}
                model_content = message.get("model_content")
                if isinstance(model_content, str) and model_content.strip():
                    clean["model_content"] = model_content
                attachments = message.get("attachments")
                if isinstance(attachments, list) and attachments:
                    clean["attachments"] = attachments
                clean_messages.append(clean)
            record["messages"] = clean_messages
            data.append(record)
        write_json(AGENT_CONVERSATIONS_FILE, data)

    def persist_tasks(self):
        write_json(TASKS_FILE, [item.__dict__ for item in self.tasks])

    def persist_parsed_videos(self):
        write_json(PARSED_VIDEOS_FILE, [item.__dict__ for item in self.parsed_videos])

    def persist_image_tasks(self):
        write_json(IMAGE_TASKS_FILE, [item.__dict__ for item in self.image_tasks])

    def has_active_video_tasks(self):
        active_statuses = ("queued", "submitting", "submitted", "processing")
        return any(task.status in active_statuses for task in self.tasks)

    def has_active_image_tasks(self):
        active_statuses = ("queued", "submitting", "submitted", "processing", "polling", "refreshing")
        return any(task.status in active_statuses for task in self.image_tasks)

    def start_worker_if_needed(self):
        if self.has_active_video_tasks():
            self.start_worker()
        else:
            self.status_var.set("无后台任务")

    def start_worker(self):
        if not self.has_active_video_tasks():
            self.status_var.set("无后台任务")
            self.log("没有正在执行的任务，未启动后台轮询")
            return
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_stop.clear()
            self.status_var.set("后台轮询中")
            self.log("开始后台轮询")
            return
        self.worker_stop.clear()
        self.worker_thread = threading.Thread(target=self.worker_loop, daemon=True)
        self.worker_thread.start()
        self.status_var.set("后台轮询中")
        self.log("开始后台轮询")

    def stop_worker(self):
        self.worker_stop.set()
        self.status_var.set("轮询已暂停")
        self.log("暂停后台轮询")

    def worker_loop(self):
        while not self.worker_stop.is_set():
            if not self.has_active_video_tasks():
                self.event_queue.put(("worker_idle", None))
                break
            try:
                self.worker_tick()
            except Exception as exc:
                self.event_queue.put(("log", f"后台错误：{exc}"))
            if not self.has_active_video_tasks():
                self.event_queue.put(("worker_idle", None))
                break
            interval = int(self.settings.get("poll_interval") or 8)
            self.worker_stop.wait(max(3, interval))

    def worker_tick(self):
        if not self.has_active_video_tasks():
            return
        api_key = self.settings.get("api_key") or self.api_key_var.get().strip()
        if not api_key:
            return
        base_url = normalize_base_url(self.settings.get("base_url") or self.base_url_var.get())
        client = VideoApiClient(api_key, base_url, self.settings.get("video_model", MODEL_NAME))
        materials = self.materials_by_id()
        active_limit = int(self.settings.get("concurrency") or 2)
        active = sum(1 for task in self.tasks if task.status in ("submitted", "processing"))

        for task in self.tasks:
            if active >= active_limit:
                break
            if task.status == "queued":
                self.set_task_status(task, "submitting")
                try:
                    request_id = client.create_video(task, materials)
                    if task.status in ("paused", "ended"):
                        continue
                    task.request_id = request_id
                    self.set_task_status(task, "submitted")
                    self.event_queue.put(("log", f"任务 {task.id} 已提交：{request_id}"))
                    active += 1
                except Exception as exc:
                    task.error = f"提交任务失败：{exc}"
                    self.set_task_status(task, "failed")

        for task in self.tasks:
            if task.status not in ("submitted", "processing") or not task.request_id:
                continue
            try:
                result = client.get_video(task.request_id)
                if task.status in ("paused", "ended"):
                    continue
                state = result.get("status") or result.get("state") or ""
                state = state.lower()
                if state in ("pending", "queued", "running", "processing", "in_progress"):
                    self.set_task_status(task, "processing")
                elif state in ("done", "completed", "succeeded") or result.get("video_url") or result.get("url"):
                    video_url = self.extract_video_url(result)
                    if not video_url:
                        raise RuntimeError(f"完成但未找到视频 URL: {result}")
                    output_dir = Path(self.settings.get("output_dir") or OUTPUT_DIR)
                    output_dir.mkdir(parents=True, exist_ok=True)
                    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{task.id}_{safe_name(task.prompt[:24])}.mp4"
                    destination = output_dir / filename
                    client.save_video(video_url, destination)
                    task.output_path = str(destination)
                    self.set_task_status(task, "done")
                    self.event_queue.put(("log", f"任务 {task.id} 已保存：{destination}"))
                elif state in ("failed", "expired", "canceled", "cancelled"):
                    task.error = result.get("error") or result.get("message") or json.dumps(result, ensure_ascii=False)
                    self.set_task_status(task, "failed")
                else:
                    self.set_task_status(task, "processing")
            except Exception as exc:
                task.error = f"轮询或下载失败：{exc}"
                transient_markers = (
                    "HTTP 502",
                    "timed out",
                    "请求超时",
                    "closed connection without response",
                    "remote end closed connection",
                    "temporarily unavailable",
                    "connection reset",
                )
                if task.request_id and any(marker.lower() in task.error.lower() for marker in transient_markers):
                    self.set_task_status(task, "processing")
                    self.event_queue.put(("log", f"任务 {task.id} 轮询暂时失败，将继续重试：{task.error}"))
                else:
                    self.set_task_status(task, "failed")

    def extract_video_url(self, result):
        for key in ("video_url", "url", "output_url"):
            if result.get(key):
                return result[key]
        video = result.get("video")
        if isinstance(video, dict):
            for key in ("video_url", "url", "output_url"):
                if video.get(key):
                    return video[key]
        data = result.get("data")
        if isinstance(data, dict):
            for key in ("video_url", "url", "output_url"):
                if data.get(key):
                    return data[key]
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                for key in ("video_url", "url", "output_url"):
                    if first.get(key):
                        return first[key]
        return ""

    def set_task_status(self, task, status):
        task.status = status
        task.updated_at = now_text()
        self.persist_tasks()
        self.event_queue.put(("refresh_tasks", None))

    def process_events(self):
        try:
            while True:
                event, payload = self.event_queue.get_nowait()
                if event == "log":
                    self.log(payload)
                elif event == "refresh_tasks":
                    self.refresh_tasks()
                elif event == "refresh_parsed":
                    self.refresh_parsed_videos()
                    self.parser_status_var.set("解析完成")
                elif event == "parser_status":
                    self.parser_status_var.set(payload)
                elif event == "fill_prompt":
                    self.rewrite_input_text.delete("1.0", END)
                    self.rewrite_input_text.insert("1.0", payload)
                    self.show_section("rewrite")
                elif event == "rewrite_output":
                    self.rewrite_output_text.delete("1.0", END)
                    self.rewrite_output_text.insert("1.0", payload)
                elif event == "generated_image":
                    self.show_generated_image(payload)
                elif event == "image_status":
                    self.image_status_var.set(payload)
                elif event == "image_task_status":
                    task_id, status = payload
                    task = next((item for item in self.image_tasks if item.id == task_id), None)
                    if task:
                        display_status = text_value(status)
                        if display_status.startswith("已提交："):
                            task.status = "submitted"
                            task.request_id = display_status.split("：", 1)[1]
                        elif display_status.startswith("生成中："):
                            task.status = "processing"
                        elif display_status.startswith("任务状态："):
                            task.status = display_status.split("：", 1)[1] or "processing"
                        else:
                            task.status = display_status
                        task.updated_at = now_text()
                        self.persist_image_tasks()
                    self.refresh_image_tasks()
                    self.image_status_var.set(self.image_task_status_label(status))
                elif event == "refresh_image_tasks":
                    self.refresh_image_tasks()
                elif event == "agent_response":
                    if payload == self.current_agent_conversation_id:
                        self.show_agent_conversation()
                    self.refresh_agent_conversations()
                elif event == "agent_stream_delta":
                    conversation_id, delta = payload
                    self.append_agent_stream_delta(conversation_id, delta)
                elif event == "agent_stream_done":
                    if payload == self.current_agent_conversation_id and hasattr(self, "agent_chat_text"):
                        self.agent_chat_text.configure(state="normal")
                        self.agent_chat_text.insert(END, "\n\n", "message_body")
                        self.agent_chat_text.configure(state="disabled")
                        self.agent_chat_text.see(END)
                    self.refresh_agent_conversations()
                elif event == "worker_idle":
                    self.worker_stop.set()
                    self.status_var.set("无后台任务")
                    self.log("没有正在执行的任务，后台轮询已停止")
                elif event == "settings_test_result":
                    messagebox.showinfo("测试连接结果", payload)
                    self.log("AI 接口测试完成")
        except queue.Empty:
            pass
        self.root.after(250, self.process_events)

    def on_close(self):
        self.save_settings()
        self.worker_stop.set()
        self.root.destroy()


def main():
    add_nvidia_dll_directories()
    try:
        root = Tk()
        style = ttk.Style(root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        gate = LicenseGate(root)
        if not gate.show():
            root.destroy()
            return
        app = GrokVideoStudio(root)
        root.mainloop()
    except Exception:
        crash_path = APP_DIR / "crash.log"
        crash_path.write_text(traceback.format_exc(), encoding="utf-8")
        raise


if __name__ == "__main__":
    main()
