# 奇仔的数据面板

一个小红书账号数据面板，支持手动导入笔记数据、查看涨粉趋势、笔记表现、拍摄计划和灵感池。

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
