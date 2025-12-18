from pdf2image import convert_from_path
import os

# Poppler のパス（Windows の場合）
poppler_path = r"C:\Users\ic241237\Documents\poppler\poppler-25.12.0\Library\bin"  # 自分の環境に合わせて変更

# PDF のパス
pdf_path = os.path.join(os.path.dirname(__file__), "menu.pdf")

# 画像出力パス
img_path = os.path.join(os.path.dirname(__file__), "menu_img.png")

# PDF → 画像（1ページ目のみ）
images = convert_from_path(pdf_path, poppler_path=poppler_path)
images[0].save(img_path, "PNG")

print(f"画像を保存しました: {img_path}")
