# 中壢天氣小精靈 🌤️

使用 **Apache Airflow** 建置的自動化天氣資料管線，每小時抓取台灣中央氣象局中壢測站即時資料，存進 **Neon 雲端 PostgreSQL**，並用 **LINE Messaging API** 推播給自己。包含體感溫度計算 + 降雨警示

## 功能
- **每小時自動抓取**：中壢區 (C0C700) 溫度、濕度、風速、雨量
- **雲端儲存**：Neon PostgreSQL 
- **即時推播**：LINE 收到體感溫度 + 趨勢
- **防呆設計**：無資料時自動重試 + 錯誤通知

## 技術棧
- **排程**：Apache Airflow (Docker Compose)
- **資料來源**：氣象資料開放平臺 https://opendata.cwa.gov.tw/
- **資料庫**：Neon PostgreSQL (雲端)
- **推播**：LINE Messaging API
- **語言**：Python

## 安裝與執行
1. Clone repo：`git clone https://github.com/Olan-Liu/zhongli-weather-bot.git`
2. Docker Compose 啟動 Airflow：`docker compose up -d`
3. 設定 Neon Connection + LINE Variables（Admin → Connections/Variables）
4. Unpause DAG 並 Trigger 一次測試


## [LINE 訊息]
<img width="334" height="568" alt="image" src="https://github.com/user-attachments/assets/e1cde342-1c83-4597-8300-ce924c654c6e" />


## 歷史資料查詢
用 Neon Console 直接跑 SQL：
```sql
SELECT obs_time, temp, hum, rain FROM weather_zhongli ORDER BY obs_time DESC LIMIT 24;
