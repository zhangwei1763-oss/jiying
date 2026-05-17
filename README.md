# Grok Imagine Video Studio

Windows 桌面版 AI 视频生成工具。使用 xAI `grok-imagine-video` 接口，支持单条和批量任务、素材库参考图、后台轮询、完成后直接保存 MP4 文件。

## 运行

```powershell
cd C:\Users\Administrator\grok_video_studio
python main.py
```

应用只使用 Python 标准库，不需要安装额外依赖。

## 功能

- 配置 xAI API Key。
- 单条添加视频生成任务。
- CSV 批量导入任务。
- 上传图片到本地素材库。
- 在提示词中使用 `@素材名` 引用素材。
- 支持选择比例、时长、分辨率。
- 后台自动提交任务并轮询结果。
- 任务完成后自动保存为 `.mp4` 文件。
- 支持批量保存已完成的视频文件，不打包 ZIP。
- 支持失败任务重试、删除任务、修改输出目录。

## CSV 格式

可使用 `batch_template.csv`。支持中文或英文表头：

- `prompt` 或 `提示词`
- `aspect_ratio` 或 `比例`
- `duration` 或 `时长`
- `resolution` 或 `分辨率`

示例：

```csv
prompt,aspect_ratio,duration,resolution
"A cinematic product video of @sample, slow camera push in",16:9,6,720p
```

## 参考图说明

素材库中的图片会在请求时转换成 base64 data URI，并作为 `reference_images` 发送给 xAI，不需要额外图片服务器。

使用参考图时，当前 xAI 接口最多支持 7 张参考图，且时长最长 10 秒。应用会在添加任务时做限制提醒。

## 数据目录

- `data/settings.json`：API Key 和输出目录设置。
- `data/materials.json`：素材库索引。
- `data/tasks.json`：任务记录。
- `materials/`：本地素材图片。
- `outputs/`：默认视频输出目录。

