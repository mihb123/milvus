import mysql.connector
import os
import json
import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

OUTPUT_DIR = "./product_train"
MAX_WORKERS = 20

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'test_user',
    'password': 'password123',
    'database': 'amacwebsite'
}

def download_image(task):
    """Hàm tải 1 ảnh (được chạy bởi thread)"""
    url, save_path = task
    
    if os.path.exists(save_path):
        return "skipped" # Ảnh đã tồn tại thì bỏ qua

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return "success"
        else:
            return "error_status"
    except Exception as e:
        return f"error_exception: {e}"

def main():
    # 1. Tạo folder gốc
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print(">>> Connecting to Database...")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True) # Trả về dict để dễ lấy key
        
        # Chỉ lấy những dòng có ảnh
        query = "SELECT name_key, list_p_atts FROM product_list WHERE list_p_atts IS NOT NULL"
        cursor.execute(query)
        rows = cursor.fetchall()
        
        print(f">>> Found {len(rows)} products. Preparing download tasks...")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    # 2. Chuẩn bị danh sách các file cần tải
    download_tasks = []
    
    for row in rows:
        raw_name_key = row['name_key']
        list_atts_json = row['list_p_atts']
        
        # Xử lý tên folder
        folder_name = raw_name_key
        folder_path = os.path.join(OUTPUT_DIR, folder_name)
        
        # Parse JSON (Nếu DB lưu dạng string thì cần json.loads, nếu driver tự convert thì thôi)
        data_atts = []
        if isinstance(list_atts_json, str):
            try:
                data_atts = json.loads(list_atts_json)
            except:
                continue
        elif isinstance(list_atts_json, list):
            data_atts = list_atts_json
            
        if not data_atts:
            continue

        # Tạo folder con
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # Duyệt qua từng ảnh trong list_p_atts
        for item in data_atts:
            image_url = item.get('link')
            image_id = item.get('id')
            
            if not image_url:
                continue

            # Lấy đuôi file (jpg, png...)
            ext = image_url.split('.')[-1].lower()
            if len(ext) > 4 or '?' in ext: # Fallback nếu url lạ
                ext = 'jpg'
                
            # Đặt tên file: ID_ảnh.jpg để tránh trùng lặp
            file_name = f"{image_id}.{ext}"
            save_path = os.path.join(folder_path, file_name)
            
            download_tasks.append((image_url, save_path))

    print(f">>> Total images to download: {len(download_tasks)}")

    # 3. Thực thi tải đa luồng
    results = {"success": 0, "skipped": 0, "errors": 0}
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit tất cả task
        futures = {executor.submit(download_image, task): task for task in download_tasks}
        
        # Hiển thị thanh progress bar
        for future in tqdm(as_completed(futures), total=len(download_tasks), desc="Downloading"):
            status = future.result()
            if status == "success":
                results["success"] += 1
            elif status == "skipped":
                results["skipped"] += 1
            else:
                results["errors"] += 1

    print("\n>>> DONE!")
    print(f"Success: {results['success']}")
    print(f"Skipped (Already exists): {results['skipped']}")
    print(f"Errors: {results['errors']}")

if __name__ == "__main__":
    main()