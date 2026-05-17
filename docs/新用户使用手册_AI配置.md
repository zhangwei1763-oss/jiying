# 新用户使用手册：配置 AI 界面

本文用于指导新用户完成软件里的“配置 AI”设置。第一次使用时，建议先按本文顺序配置，再点击保存。

## 1. 打开配置 AI

启动软件后，点击顶部的“配置 AI”按钮。

配置窗口中包含以下几类设置：

- 文本模型
- 文生图模型
- 图生视频模型
- 音频转文案

如果窗口内容显示不全，可以用鼠标滚轮向下滑动。

## 2. 文本模型

文本模型主要用于文案生成、文案改写等文字相关功能。

需要填写：

- Base URL：http://www.wuxianai.top/v1
- API Key：到www.wuxianai.top注册用户，新建apikey，分组选择gpt，然后将key填到这里
- Model：gpt-5.5


## 3. 文生图模型

文生图模型用于图片生成模块。

需要填写：

-  Base URL：http://www.wuxianai.top/v1
- API Key：到www.wuxianai.top注册用户，新建apikey，分组选择gpt，然后将key填到这里
- Model：gpt-image-2
- 轮询路径：/images/jobs/{id}

一般情况下，轮询路径保持默认即可，不建议新用户修改。

如果图片生成失败，优先检查：

- API Key 是否正确
- Base URL 是否和服务商文档一致
- Model 名称是否填写正确
- 账号额度是否充足

## 4. 图生视频模型

图生视频模型用于视频生成任务。

需要填写：

- Base URL：http://www.wuxianai.top/v1
- API Key：到www.wuxianai.top注册用户，新建apikey，分组选择grok，然后将key填到这里
- Model：gpt-image-2

视频生成通常耗时更长，提交任务后软件会根据后台任务状态自动查询。没有正在执行的任务时，软件不会持续轮询。

## 5. 音频转文案

音频转文案用于从解析后的视频中提取语音文案。

这里有两种方式：

- local_gpu：使用本机 NVIDIA 显卡和本地模型转写
- apikey：使用第三方音频转文字接口

建议优先使用 `local_gpu`，前提是电脑有可用 NVIDIA 显卡。

## 6. 选择 local_gpu

当“转写方式”选择 `local_gpu` 时，会显示本地 GPU 相关配置。

### 本地模型

建议新用户选择：

- 6GB 显存：`small`
- 8GB 显存：`small` 或 `medium`
- 12GB 以上显存：可以考虑 `large-v3` 或 `distil-large-v3`

如果不确定显存大小，先选 `small`。

### 模型目录

点击“选择文件夹”，选择模型所在目录。

便携包用户一般选择软件包内的：

`app\models\faster-whisper`

如果是在当前开发目录中使用，一般选择：

`models\faster-whisper`

不要选择到单个模型文件，应该选择模型缓存所在的文件夹。

### 计算精度

建议：

- 6GB 显存：`int8_float16`
- 8GB 显存：`int8_float16` 或 `float16`
- 显存紧张或加载失败：`int8`

说明：

- `float16` 速度和效果较好，但显存占用更高
- `int8_float16` 更适合大多数 6GB 到 8GB 显卡
- `int8` 显存占用更低，但速度和效果可能略受影响

### Batch Size

建议：

- 6GB 显存：`1`
- 8GB 显存：`2`
- 12GB 以上显存：`4` 或 `8`

如果出现显存不足、转写失败、CUDA 报错，先把 Batch Size 调回 `1`。

### Beam Size

建议：

- 普通使用：`3`
- 更快速度：`1`
- 更高识别质量：`5`

Beam Size 越大，可能越慢，也可能占用更多资源。新用户建议保持 `3`。

### 验证本地 CUDA 和模型

配置完成后，点击“验证本地 CUDA 和模型”。

如果成功，会提示类似：

`CUDA 可用，检测到 1 个 CUDA 设备；模型 small 已成功加载，计算精度 int8_float16。`

这表示本机显卡、CUDA 运行库、模型目录都可以正常使用。

如果失败，按提示检查：

- 是否有 NVIDIA 显卡
- 是否安装 NVIDIA 显卡驱动
- 模型目录是否选择正确
- 计算精度是否过高
- Batch Size 是否过大

## 7. 选择 apikey

当“转写方式”选择 `apikey` 时，会显示 API 接口配置。

需要填写：

- 音频 Base URL：音频转文字接口地址
- 音频 API Key：接口密钥
- 音频 Model：音频识别模型名称

适合以下情况：

- 用户电脑没有 NVIDIA 显卡
- 不想使用本地模型
- 希望把音频识别交给云端接口处理

注意：使用 apikey 方式通常会产生接口费用，并且需要联网。

## 8. 新用户推荐配置

如果电脑有 NVIDIA 显卡，推荐：

- 转写方式：`local_gpu`
- 本地模型：`small`
- 计算精度：`int8_float16`
- Batch Size：`1`
- Beam Size：`3`

然后点击“验证本地 CUDA 和模型”。

验证通过后，点击“保存”。

如果电脑没有 NVIDIA 显卡，推荐：

- 转写方式：`apikey`
- 填写音频接口 Base URL、API Key、Model
- 点击“测试连接”
- 测试通过后点击“保存”

## 9. 保存配置

所有配置完成后，点击“保存”。

保存后，软件会把配置写入本地配置文件。之后再次启动软件，会自动读取上一次保存的配置。

## 10. 常见问题

### 点击验证 CUDA 和模型失败

优先检查 NVIDIA 显卡驱动是否安装正常。如果驱动正常，再检查模型目录是否选择到了 `faster-whisper` 模型缓存目录。

### 转写时提示显存不足

把配置调低：

- 本地模型改为 `small`
- 计算精度改为 `int8_float16` 或 `int8`
- Batch Size 改为 `1`

### 不知道模型目录选哪里

优先选择：

`app\models\faster-whisper`



### 测试连接失败

测试连接主要检查云端 API 是否可用。请检查 Base URL、API Key、Model 是否和服务商提供的信息一致。

