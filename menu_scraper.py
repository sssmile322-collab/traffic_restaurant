import os
import sys
import shutil
import requests
import subprocess
from datetime import datetime, timedelta
from pdf2image import convert_from_path

"""
PDF Menu Scraper (Flexible Date Version)
1. 今週と来週のメニューを探します（月曜→日曜→土曜の順で検索）。
2. ファイルが見つかったら、その週の検索は終了します。
3. 「今週のメニュー」を menu_img.png として保存します。
4. Firebaseへのデプロイを実行します。
5. 最後に不要なPDF/PNGファイルを削除します。
"""

# ================= 設定エリア =================

# Popplerのパス
POPPLER_PATH = r"C:\Users\ic241237\Documents\poppler\poppler-25.12.0\Library\bin"

# 保存先フォルダ（Webサイトのpublicフォルダ）
DOWNLOAD_DIR = r"C:\Users\ic241237\Documents\line_viewer_site\public"

# ログファイルの場所
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, 'scraper_log.txt')

# URLテンプレート
URL_TEMPLATE = "https://www.okinawa-ct.ac.jp/userfiles/files/10ryoumu_kakari/{date}_ryoushoku.pdf"

# ============================================

def write_log(message):
    """ログファイルに日時付きでメッセージを追記"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_line + "\n")
    except Exception:
        pass

def get_monday_of_week(dt):
    """その日の週の月曜日を計算"""
    days_to_monday = dt.weekday()
    return dt - timedelta(days=days_to_monday)

def process_date(target_date):
    """
    指定日のダウンロードと変換を実行
    戻り値: 成功(または既にファイルがある)なら True, 失敗(404など)なら False
    """
    date_str = target_date.strftime('%Y%m%d')
    url = URL_TEMPLATE.format(date=date_str)
    
    pdf_filename = f"{date_str}_menu.pdf"
    pdf_path = os.path.join(DOWNLOAD_DIR, pdf_filename)
    img_path = os.path.join(DOWNLOAD_DIR, f"{date_str}_menu.png")

    # 画像が既にあるなら「成功」とみなす
    if os.path.exists(img_path):
        # write_log(f"既に存在します: {os.path.basename(img_path)}")
        return True

    write_log(f"チェック中: {url}")

    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (TaskSchedulerBot)'})

    try:
        resp = session.get(url, timeout=30)
        
        if resp.status_code != 200:
            return False # 見つからなかった

        # ダウンロード
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        with open(pdf_path, 'wb') as f:
            f.write(resp.content)
        write_log(f"PDFダウンロード成功: {pdf_filename}")

        # 画像変換
        try:
            images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
            if images:
                images[0].save(img_path, "PNG")
                write_log(f"画像変換成功: {os.path.basename(img_path)}")
                return True # 成功
            else:
                write_log(f"警告: PDFページなし - {pdf_filename}")
                return False
        except Exception as e:
            write_log(f"画像変換エラー: {e}")
            return False

    except Exception as e:
        write_log(f"通信エラー: {e}")
        return False

def set_current_week_image():
    """今週のメニューを menu_img.png に設定する（月・日・土の優先順で探す）"""
    try:
        today = datetime.now()
        this_monday = get_monday_of_week(today)
        
        # 探す候補日（月曜 → 日曜 → 土曜）
        offsets = [0, -1, -2]
        found_file = None

        for offset in offsets:
            target_date = this_monday + timedelta(days=offset)
            date_str = target_date.strftime('%Y%m%d')
            candidate_file = f"{date_str}_menu.png"
            src_path = os.path.join(DOWNLOAD_DIR, candidate_file)

            if os.path.exists(src_path):
                found_file = candidate_file
                break # 見つかったらループ終了

        dst_path = os.path.join(DOWNLOAD_DIR, "menu_img.png")

        # 1. 今週分（月or日or土）が見つかった場合
        if found_file:
            shutil.copy2(os.path.join(DOWNLOAD_DIR, found_file), dst_path)
            write_log(f"表示画像を今週分({found_file})に更新しました")
            return

        # 2. 今週分がない場合、一番新しいファイルを使う
        if os.path.exists(DOWNLOAD_DIR):
            files = os.listdir(DOWNLOAD_DIR)
            menu_files = [f for f in files if f.endswith('_menu.png') and f != 'menu_img.png']
            
            if menu_files:
                menu_files.sort()
                latest_file = menu_files[-1]
                shutil.copy2(os.path.join(DOWNLOAD_DIR, latest_file), dst_path)
                write_log(f"今週分がないため、最新のものを表示しました: {latest_file}")
            else:
                write_log("表示可能なメニュー画像がありません。")

    except Exception as e:
        write_log(f"画像更新処理でエラー: {e}")

def deploy_to_firebase():
    """Firebaseへのデプロイを実行し、ログに記録する"""
    write_log("--- Firebaseへのデプロイを開始します ---")
    
    project_root = BASE_DIR
    
    try:
        # ▼▼▼ --non-interactive を追加 ▼▼▼
        result = subprocess.run("firebase deploy --non-interactive", cwd=project_root, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            write_log("デプロイ成功！")
        else:
            write_log(f"デプロイ失敗:\n{result.stderr}")
            
    except Exception as e:
        write_log(f"デプロイ実行中にエラーが発生しました: {e}")

def cleanup_temp_files():
    """menu_img.png と icon.png 以外の PDF/PNG ファイルを削除する"""
    write_log("--- 不要なファイルの削除を開始します ---")
    
    KEEP_FILES = ['menu_img.png', 'icon.png']

    try:
        if not os.path.exists(DOWNLOAD_DIR):
            return

        files = os.listdir(DOWNLOAD_DIR)
        deleted_count = 0

        for f in files:
            if f.lower().endswith(('.pdf', '.png')):
                if f in KEEP_FILES:
                    continue
                
                file_path = os.path.join(DOWNLOAD_DIR, f)
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except Exception as del_err:
                    write_log(f"削除失敗 ({f}): {del_err}")

        write_log(f"クリーンアップ完了: {deleted_count} 個のファイルを削除しました")

    except Exception as e:
        write_log(f"クリーンアップ処理エラー: {e}")

def main():
    write_log("--- 実行開始 ---")
    
    try:
        today = datetime.now()
        this_monday = get_monday_of_week(today)
        
        # チェックする週（今週と来週）
        target_weeks = [this_monday, this_monday + timedelta(days=7)]
        
        # チェックする曜日のズレ（0=月曜, -1=日曜, -2=土曜）
        # 優先順位: 月曜 -> 日曜 -> 土曜
        check_offsets = [0, -1, -2]

        for base_date in target_weeks:
            # その週の中でファイルが見つかるまで探す
            for offset in check_offsets:
                target_date = base_date + timedelta(days=offset)
                
                # 見つかったら(Trueが返ったら)、その週の他の曜日は探さない
                if process_date(target_date):
                    break
        
        # 画像の更新
        set_current_week_image()

        # デプロイ実行
        deploy_to_firebase()

        # 不要ファイルを削除
        cleanup_temp_files()
            
    except Exception as e:
        write_log(f"致命的なエラー: {e}")
        sys.exit(1) # エラー終了
        
    write_log("--- 実行終了 ---")
    sys.exit(0) # 正常終了

if __name__ == '__main__':
    main()