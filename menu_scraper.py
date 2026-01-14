import os
import sys
import shutil
import requests
from datetime import datetime, timedelta
from pdf2image import convert_from_path

# ================= 設定エリア =================

# GitHub Actions上ではPopplerのパス指定は不要（Noneで自動検知）
POPPLER_PATH = None

# 保存先フォルダ（カレントディレクトリ配下の public を指定）
BASE_DIR = os.getcwd()
DOWNLOAD_DIR = os.path.join(BASE_DIR, "public")

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
    pdf_path = os.path.join(DOWNLOAD_DIR, pdf_filename)
    img_path = os.path.join(DOWNLOAD_DIR, f"{date_str}_menu.png")

    if os.path.exists(img_path):
        return True

    write_log(f"チェック中: {url}")

    try:
        resp = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code != 200:
            return False

        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        with open(pdf_path, 'wb') as f:
            f.write(resp.content)
        write_log(f"PDFダウンロード成功: {pdf_filename}")

        try:
            # Linux環境(GitHub Actions)ではpoppler_path=Noneで動作
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
    found_file = None

    for offset in offsets:
        target_date = this_monday + timedelta(days=offset)
        candidate_file = f"{target_date.strftime('%Y%m%d')}_menu.png"
        if os.path.exists(os.path.join(DOWNLOAD_DIR, candidate_file)):
            found_file = candidate_file
            break

    dst_path = os.path.join(DOWNLOAD_DIR, "menu_img.png")

    if found_file:
        shutil.copy2(os.path.join(DOWNLOAD_DIR, found_file), dst_path)
        write_log(f"★更新完了: {found_file} を menu_img.png に設定しました")
    else:
        write_log("今週のメニューが見つかりませんでした。更新をスキップします。")

def main():
    write_log("--- 自動更新スクリプト開始 ---")
    
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