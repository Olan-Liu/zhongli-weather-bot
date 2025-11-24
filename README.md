# 中壢天氣小精靈

每小時自動：
1. 抓中央氣象局中壢測站即時資料
2. 存進 Neon 雲端 PostgreSQL（永不遺失）
3. 用 LINE Messaging API 推播給我自己

技術棧：
- Apache Airflow 3.1.3（Docker Compose）
- Python + requests
- Neon.tech 雲端 PostgreSQL
- LINE Messaging API
- GitHub 版控
