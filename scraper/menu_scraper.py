import os
import sys
import shutil
import requests
from datetime import datetime, timedelta
from pdf2image import convert_from_path

# ================= 設定エリア =================

# Windowsで動かす場合、Popplerのbinフォルダへのパスが必要な場合があります。
# エラーが出る場合はここにパスを記入してください（例: r"C:\Program Files\poppler-xx\bin"）
POPPLER_PATH = None 

# 1. menu_img.png の保存先 (public直下)
PUBLIC_DIR = r"C:\Users\ic241237\Documents\line_viewer_site\public"

# 2. PDFや日付付きPNGの保存先 (public\picture)
PICTURE_DIR = os.path.join(PUBLIC_DIR, "picture")

# 保存先フォルダが存在しない場合は自動作成
os.makedirs(PUBLIC_DIR, exist_ok=True)
os.makedirs(PICTURE_DIR, exist_ok=True)

# URLテンプレート
URL_TEMPLATE = "https://www.okinawa-ct.ac.jp/userfiles/files/10ryoumu_kakari/{date}_ryoushoku.pdf"

# ============================================

def write_log(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def get_monday_of_week(dt):
    days_to_monday = dt.weekday()
    return dt - timedelta(days=days_to_monday)

def process_date(target_date):
    date_str = target_date.strftime('%Y%m%d')
    url = URL_TEMPLATE.format(date=date_str)
    
    pdf_filename = f"{date_str}_menu.pdf"
    
    # 【変更点】保存先を PICTURE_DIR (public\picture) に指定
    pdf_path = os.path.join(PICTURE_DIR, pdf_filename)
    img_path = os.path.join(PICTURE_DIR, f"{date_str}_menu.png")

    if os.path.exists(img_path):
        return True

    write_log(f"チェック中: {url}")

    try:
        resp = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code != 200:
            return False

        with open(pdf_path, 'wb') as f:
            f.write(resp.content)
        write_log(f"PDFダウンロード成功: {pdf_filename}")

        try:
            images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
            if images:
                images[0].save(img_path, "PNG")
                write_log(f"画像変換成功: {os.path.basename(img_path)}")
                return True
            else:
                return False
        except Exception as e:
            write_log(f"画像変換エラー: {e}")
            return False

    except Exception as e:
        write_log(f"通信エラー: {e}")
        return False

def set_current_week_image():
    today = datetime.now()
    this_monday = get_monday_of_week(today)
    
    # 優先順位: 月曜 -> 日曜 -> 土曜
    offsets = [0, -1, -2]
    found_file_path = None

    for offset in offsets:
        target_date = this_monday + timedelta(days=offset)
        candidate_file = f"{target_date.strftime('%Y%m%d')}_menu.png"
        
        # 【変更点】探す場所を PICTURE_DIR に変更
        candidate_path = os.path.join(PICTURE_DIR, candidate_file)
        
        if os.path.exists(candidate_path):
            found_file_path = candidate_path
            break

    # 【変更点】最終出力先は PUBLIC_DIR (public直下)
    dst_path = os.path.join(PUBLIC_DIR, "menu_img.png")

    if found_file_path:
        # pictureフォルダから public直下へコピー
        shutil.copy2(found_file_path, dst_path)
        write_log(f"★更新完了: {os.path.basename(found_file_path)} を menu_img.png に設定しました")
    else:
        write_log("今週のメニューが見つかりませんでした。更新をスキップします。")

def main():
    write_log("--- 自動更新スクリプト開始 ---")
    write_log(f"保存先(Main): {PUBLIC_DIR}")
    write_log(f"保存先(Pic) : {PICTURE_DIR}")
    
    today = datetime.now()
    this_monday = get_monday_of_week(today)
    
    # 今週と来週をチェック
    target_weeks = [this_monday, this_monday + timedelta(days=7)]
    check_offsets = [0, -1, -2]

    for base_date in target_weeks:
        for offset in check_offsets:
            if process_date(base_date + timedelta(days=offset)):
                break
    
    set_current_week_image()
    write_log("--- 処理終了 ---")

if __name__ == '__main__':
    main()