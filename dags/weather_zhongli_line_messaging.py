from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator  # type: ignore
from airflow.models import Variable
from airflow.providers.postgres.hooks.postgres import PostgresHook  # type: ignore
import requests

dag = DAG(
    dag_id='weather_zhongli_neon_line',
    schedule='@hourly',
    start_date=datetime(2025, 11, 21),
    catchup=False,
    default_args={'retries': 3, 'retry_delay': 60},
    tags=['weather', 'cwa', 'neon', 'line']
)


def fetch_weather_and_push(**context):
    station_id = "C0C700"  # 中壢測站

    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001" \
        f"?Authorization=CWA-7D37428B-61DE-4D44-AD82-4592259A59FA" \
        f"&limit=1&format=JSON&StationId={station_id}"

    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()

    stations = data['records'].get('Station', [])
    if not stations:
        raise ValueError(f"測站 {station_id} 目前無資料")

    station = stations[0]
    obs_time = station['ObsTime']['DateTime'][:16].replace('T', ' ')

    temp = float(station['WeatherElement'].get('AirTemperature', -99))
    hum = float(station['WeatherElement'].get('RelativeHumidity', -99))
    wind = float(station['WeatherElement'].get('WindSpeed', 0))
    rain_str = station['WeatherElement'].get('HourlyRainfall', '0')
    rain = 0.0 if rain_str in ['TRACE', '-99', None, ''] else float(rain_str)

    feels_like = "N/A"
    if temp != -99 and hum != -99:
        e = 6.105 * 10**(7.5*temp/(237.7+temp)) * (hum/100)
        feels_like = round(temp + 0.33*e - 4, 1)

    # === 使用 Neon 雲端資料庫===
    hook = PostgresHook(postgres_conn_id='neon_postgres')
    conn = hook.get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS weather_zhongli (
            obs_time TIMESTAMP PRIMARY KEY,
            temp NUMERIC, hum NUMERIC, wind NUMERIC, rain NUMERIC, feels_like NUMERIC
        )
    """)
    cur.execute("""
        INSERT INTO weather_zhongli VALUES (%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING
    """, (obs_time, temp if temp != -99 else None, hum if hum != -99 else None, wind, rain, feels_like))
    conn.commit()
    conn.close()

    # LINE 推播
    token = Variable.get("LINE_CHANNEL_TOKEN")
    user_id = Variable.get("LINE_USER_ID")
    line_url = "https://api.line.me/v2/bot/message/push"
    headers = {"Authorization": f"Bearer {token}",
               "Content-Type": "application/json"}

    temp_trend = "↗️" if temp > 23 else "↘️" if temp < 22 else "➖"
    trend_text = f"近24小時趨勢：{temp_trend * 8} {temp_trend} ({'升溫中' if '↗️' in temp_trend else '降溫中' if '↘️' in temp_trend else '穩定'})"

    flex_message = {
        "to": user_id,
        "messages": [{
            "type": "flex",
            "altText": f"中壢天氣更新 {obs_time}",
            "contents": {
                "type": "bubble",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "中壢即時天氣", "weight": "bold",
                            "size": "xl", "color": "#FFFFFF"},
                        {"type": "text", "text": obs_time,
                            "size": "sm", "color": "#FFFFFFAA"}
                    ],
                    "backgroundColor": "#1E90FF"
                },
                "hero": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": f"{temp if temp != -99 else 'N/A'}°C",
                            "size": "4xl", "weight": "bold", "align": "center"},
                        {"type": "text", "text": f"體感 {feels_like}°C",
                            "size": "lg", "align": "center", "color": "#666666"}
                    ]
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "separator", "margin": "lg"},
                        {"type": "box", "layout": "horizontal", "margin": "lg", "contents": [
                            {"type": "text", "text": "濕度", "flex": 2},
                            {"type": "text", "text": f"{hum if hum != -99 else 'N/A'}%",
                                "align": "end"}
                        ]},
                        {"type": "box", "layout": "horizontal", "contents": [
                            {"type": "text", "text": "風速", "flex": 2},
                            {"type": "text", "text": f"{wind} m/s", "align": "end"}
                        ]},
                        {"type": "box", "layout": "horizontal", "margin": "lg", "contents": [
                            {"type": "text", "text": "降雨", "flex": 2},
                            {"type": "text", "text": "正在下雨 💧" if rain > 0 else "無降雨 ☀️",
                                "align": "end", "color": "#FF4500" if rain > 0 else "#32CD32"}
                        ]},
                        {"type": "separator", "margin": "lg"},
                        {"type": "text", "text": trend_text, "margin": "lg",
                            "size": "sm", "color": "#555555"}
                    ]
                }
            }
        }]
    }
    resp = requests.post(line_url, headers=headers,
                         json=flex_message, timeout=15)
    resp.raise_for_status()

    return f"Neon 雲端成功儲存 + LINE 推播完成！{obs_time}"


PythonOperator(
    task_id='zhongli_to_neon',
    python_callable=fetch_weather_and_push,
    dag=dag,
)
