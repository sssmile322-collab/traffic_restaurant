import cv2

def test_camera(index):
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        print(f"カメラ番号 {index}: ❌ 認識できません")
        return
    
    ret, frame = cap.read()
    if ret:
        print(f"カメラ番号 {index}: ✅ OK! (解像度: {frame.shape[1]}x{frame.shape[0]})")
        # 実際にウィンドウを出して確認
        cv2.imshow(f"Camera {index}", frame)
        cv2.waitKey(2000) # 2秒間表示
        cv2.destroyAllWindows()
    else:
        print(f"カメラ番号 {index}: ⚠️ 接続できましたが映像が取れません")
    
    cap.release()

print("--- カメラチェック開始 ---")
# 0番から3番までチェックしてみる
for i in range(4):
    test_camera(i)