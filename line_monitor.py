from ultralytics import YOLO
import cv2
import requests
import time
import csv           # ← 追加
import datetime      # ← 追加
import os            # ← 追加

# Firebase URL
FIREBASE_URL = "https://traffic-restaurant-default-rtdb.firebaseio.com/line_status.json"
HISTORY_URL = "https://traffic-restaurant-default-rtdb.firebaseio.com/line_history.json"


def upload_people_count(count):
    data = {
        "people": count,
        "timestamp": int(time.time())
    }

    try:
        # 最新状態
        r1 = requests.put(FIREBASE_URL, json=data)
        # 履歴
        r2 = requests.post(HISTORY_URL, json=data)

        print(
            "Firebase送信:",
            count,
            "人",
            "status:", r1.status_code,
            "history:", r2.status_code
        )
    except Exception as e:
        print(f"送信エラー: {e}")


def save_learning_data(count):
    """AI学習用にデータをCSVに保存する（11:30〜13:30限定）"""
    
    dt = datetime.datetime.now()
    
    # 時間を「1130」のような4桁の数字に変換して比較しやすくする
    # 例: 11時30分 → 1130, 13時30分 → 1330
    current_time_num = dt.hour * 100 + dt.minute

    # ▼▼▼ 時間チェックの門番 ▼▼▼
    # 1130 (11:30) より前、または 1330 (13:30) より後は保存しない
    if current_time_num < 1130 or current_time_num > 1330:
        return # 何もせず帰る
    # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

    file_path = "ai_training_data.csv"
    timestamp = int(time.time())
    
    # [タイムスタンプ, 年, 月, 日, 曜日, 時, 分, 人数]
    row = [
        timestamp,
        dt.year,
        dt.month,
        dt.day,
        dt.weekday(),
        dt.hour,
        dt.minute,
        count
    ]

    file_exists = os.path.isfile(file_path)
    
    try:
        with open(file_path, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "year", "month", "day", "weekday", "hour", "minute", "people"])
            
            writer.writerow(row)
            print("💾 学習データを記録しました (Time: {}:{})".format(dt.hour, dt.minute))
    except Exception as e:
        print(f"CSV保存エラー: {e}")


model = YOLO("yolov8n.pt")
cap = cv2.VideoCapture(0)

last_upload = 0

# ▼▼▼ ここを変更しました (1 -> 10) ▼▼▼
UPLOAD_INTERVAL = 1 
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # YOLO 推論
    results = model(frame, imgsz=640, conf=0.4)

    # 人数カウント
    person_count = 0
    for result in results:
        for box in result.boxes:
            if int(box.cls[0]) == 0:  # person
                person_count += 1

    # 🔥 設定した秒数（10秒）ごとに Firebase に送信
    now = time.time()
    if now - last_upload >= UPLOAD_INTERVAL:
        upload_people_count(person_count)
        save_learning_data(person_count)
        last_upload = now        

    # 📷 カメラ映像表示
    cv2.putText(
        frame,
        f"People: {person_count}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )
    #ここはラズパイ用
    #cv2.imshow("Line Monitor", frame)

    # q で終了
    #if cv2.waitKey(1) & 0xFF == ord('q'):
    #    break

cap.release()
#cv2.destroyAllWindows()