# 奇仔的旅行内容工作台

一个面向旅游自媒体职业化经营的内容工作台：从一次旅行拆出旅行项目、选题库、脚本与文案、拍摄清单、发布计划、数据复盘和商业化素材。

## 当前版本

这一版先聚焦四个核心内容生产模块：

- 旅行项目：记录目的地、日期、预算、平台、人设和本次旅行目标。
- 选题库：围绕目的地拆出多平台选题、内容类型、目标和状态。
- 脚本与文案：把选题转成钩子、分镜、镜头需求、旁白和结尾引导。
- 拍摄清单：按天整理现场要拍的镜头、口播点和素材缺口。

数据复盘、发布日历、攻略产品和商单媒体包作为后续模块保留入口。

## 本地运行

```bash
python3 server.py --host 127.0.0.1 --port 4174
```

打开：

```text
http://127.0.0.1:4174/index.html
```

## 数据保存

数据通过本地 SQLite 保存到 `data/dashboard.sqlite`。这个文件不会提交到 GitHub。

## Vercel 线上数据库

Vercel 部署时使用 `api/dashboard.py` 保存数据。推荐在 Vercel 项目里添加 Upstash Redis / KV 存储，并配置环境变量：

```text
KV_REST_API_URL
KV_REST_API_TOKEN
```

如果使用 Upstash 原生命名，也兼容：

```text
UPSTASH_REDIS_REST_URL
UPSTASH_REDIS_REST_TOKEN
```

配置好环境变量后，重新部署 Vercel。导入数据后刷新页面，数据会从线上数据库恢复。
