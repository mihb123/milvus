import os
import math
from PIL import Image, ImageDraw

def display_results(results):
    if not results: return
    w, h, cols = 200, 200, 5
    
    rows = math.ceil(len(results) / cols)
    # Tạo ảnh nền trắng
    canvas = Image.new('RGB', (cols * w, rows * h), 'white')
    
    for i, item in enumerate(results):
        try:
            folder_path = os.path.join(DATA_DIR, item['name_key'])
            
            if not os.path.exists(folder_path):
                print(f"Missing folder: {folder_path}")
                continue

            # Lấy ảnh đầu tiên tìm thấy
            img_file = None
            for file in os.listdir(folder_path):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    img_file = file
                    break
            
            if not img_file: continue

            img_path = os.path.join(folder_path, img_file)
            img = Image.open(img_path).convert('RGB').resize((w, h))
            
            # --- VẼ SCORE LÊN ẢNH ---
            draw = ImageDraw.Draw(img)
            # Vẽ hình chữ nhật nền đen mờ ở góc để chữ dễ đọc
            draw.rectangle([(0, 0), (100, 20)], fill="black") 
            # Viết chữ (Thứ tự - Score)
            draw.text((5, 5), f"#{i+1}: {item['score']:.3f}", fill="yellow")
            # Viết tên Key ở dưới
            draw.rectangle([(0, h-20), (w, h)], fill="black")
            draw.text((5, h-15), f"{item['name_key']}", fill="white")
            # ------------------------

            x = (i % cols) * w
            y = (i // cols) * h
            canvas.paste(img, (x, y))
        except Exception as e: 
            print(f"Error drawing {item['name_key']}: {e}")

    canvas.show()