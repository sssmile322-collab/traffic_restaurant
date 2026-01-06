import requests
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime, timedelta

# Firebaseの履歴データURL
HISTORY_URL = "https://traffic-restaurant-default-rtdb.firebaseio.com/line_history.json"

def fetch_data():
    """Firebaseから過去の混雑データを取得して整形する"""
    print("📡 データを取得中...")
    resp = requests.get(HISTORY_URL)
    data = resp.json()
    
    if not data:
        print("❌ データがありません。まずはlinemonitor.pyを動かしてデータを溜めてください。")
        return None

    # 辞書型からリスト型へ変換 (FirebaseのIDは不要なので捨てる)
    records = []
    for key, val in data.items():
        if isinstance(val, dict) and 'timestamp' in val and 'people' in val:
            records.append(val)
    
    # pandasのデータフレーム（表）に変換
    df = pd.DataFrame(records)
    
    # 日付データを扱いやすい形に分解
    # timestampから「曜日(0=月曜)」「時間」「分」を作る
    df['dt'] = pd.to_datetime(df['timestamp'], unit='s', utc=True).dt.tz_convert('Asia/Tokyo')
    df['weekday'] = df['dt'].dt.weekday
    df['hour'] = df['dt'].dt.hour
    df['minute'] = df['dt'].dt.minute
    
    # 学習に使わない列を削除
    df = df[['weekday', 'hour', 'minute', 'people']]
    
    print(f"✅ {len(df)} 件の学習データを用意しました")
    return df

def train_and_predict(df):
    """AIを学習させて、明日の予測をする"""
    
    # 🤖 AIの学習フェーズ
    # X: 入力データ（曜日、時、分）
    # y: 正解データ（人数）
    X = df[['weekday', 'hour', 'minute']]
    y = df['people']
    
    # ランダムフォレスト（多数決で決める賢いモデル）を使用
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    print("🧠 AIの学習が完了しました！")

    # 🔮 未来予知フェーズ（明日の11:00〜14:00を予測）
    print("\n--- 🔮 明日の混雑予報 ---")
    
    tomorrow = datetime.now() + timedelta(days=1)
    weekday = tomorrow.weekday()
    
    # 11:00 から 14:00 まで 10分刻みで予測
    peak_people = 0
    peak_time = ""

    for h in range(11, 15): # 11時～14時
        for m in range(0, 60, 10): # 10分刻み
            # AIに「明日のこの時間はどう？」と聞く
            prediction = model.predict([[weekday, h, m]])[0]
            
            # 結果を表示（四捨五入）
            count = round(prediction, 1)
            print(f"{h:02d}:{m:02d} -> 約 {count} 人")
            
            if count > peak_people:
                peak_people = count
                peak_time = f"{h:02d}:{m:02d}"

    print("-------------------------")
    print(f"⚠️ 明日のピーク予想: {peak_time} 頃（約 {int(peak_people)} 人）")

if __name__ == "__main__":
    df = fetch_data()
    if df is not None and len(df) > 10: # データが少なすぎると学習できないのでチェック
        train_and_predict(df)
    else:
        print("まずはデータを10件以上溜めてから実行してください！")