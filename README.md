# 奇仔的旅行内容工作台

一个面向旅行创作者的小红书内容工作台，支持导入笔记数据、查看增长趋势、判断目的地表现、管理旅程拍摄计划、灵感池和旅行脚本地图。

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
