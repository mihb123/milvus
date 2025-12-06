import os
import re
import mysql.connector
from mysql.connector import Error
import random

# Cấu hình Database
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'test_user',
    'password': 'password123',
    'database': 'ama'
}

ROOT_DIR = './products'
FORCE_UPDATE = True 

def generate_group_id(group_name):
    if not group_name:
        return "UNK" + str(random.randint(1, 1000))
    clean_name = group_name.replace(" ", "")
    prefix = clean_name[:3].upper()
    rand_num = random.randint(1, 1000)
    return f"{prefix}{rand_num}"

def smart_create_search_pattern(filename):
    """
    Xử lý tên file thông minh để tránh nhầm lẫn
    """
    # 1. Lấy tên gốc
    base_name = os.path.splitext(filename)[0]
    
    # 2. Xử lý case đặc biệt: Năm liền nhau (20252026 -> 2025%2026)
    # Regex: Tìm 4 số + 4 số ở cuối chuỗi và chèn % vào giữa
    base_name = re.sub(r'(\d{4})(\d{4})$', r'\1%\2', base_name)

    # 3. Thay thế các ký tự ngăn cách (- _ .) thành %
    # Ví dụ: "Ao-Thun" -> "Ao%Thun"
    search_pattern = re.sub(r'[\s_\-\.]+', '%', base_name)
    
    # 4. Thêm % vào cuối để khớp phần mở rộng trong DB (nếu có)
    return search_pattern + '%'

def update_product_groups():
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            cursor = connection.cursor()
            print("Kết nối DB thành công. Đang xử lý...\n")
            
            updated_count = 0
            
            if not os.path.exists(ROOT_DIR):
                return

            for category_name in os.listdir(ROOT_DIR):
                cat_path = os.path.join(ROOT_DIR, category_name)
                
                if os.path.isdir(cat_path):
                    for group_name in os.listdir(cat_path):
                        group_path = os.path.join(cat_path, group_name)
                        
                        if os.path.isdir(group_path):
                            current_group_id = generate_group_id(group_name)
                            
                            # --- QUAN TRỌNG: SẮP XẾP FILE ---
                            # Lấy danh sách file
                            files = [f for f in os.listdir(group_path) if os.path.isfile(os.path.join(group_path, f))]
                            
                            # Sắp xếp theo độ dài tên file GIẢM DẦN (Dài trước, Ngắn sau)
                            # Logic: "Ao-Thun-Dai-Tay" (Dài) xử lý trước -> Match chính xác nó.
                            # Sau đó "Ao-Thun" (Ngắn) xử lý sau -> Sẽ không match nhầm thằng dài vì thằng dài (có thể) đã xong rồi.
                            files.sort(key=lambda x: len(x), reverse=True)

                            for filename in files:
                                search_pattern = smart_create_search_pattern(filename)

                                # SQL Update
                                sql = """
                                UPDATE products 
                                SET group_name = %s, group_id = %s 
                                WHERE name LIKE %s 
                                AND category_name = %s
                                """
                                
                                # Tùy chọn: Nếu muốn cực kỳ an toàn, chỉ update dòng chưa có Group ID
                                # if not FORCE_UPDATE:
                                #    sql += " AND (group_id IS NULL OR group_id = '')"
                                
                                sql += " LIMIT 1"
                                
                                val = (group_name, current_group_id, search_pattern, category_name)
                                cursor.execute(sql, val)
                                
                                if cursor.rowcount > 0:
                                    updated_count += 1
                                    print(f"[OK] {filename} -> Pattern: {search_pattern}")
                                else:
                                    print(f"[MISS] {filename}")
                                    pass

            connection.commit()
            print(f"\n--- Hoàn tất: {updated_count} sản phẩm ---")

    except Error as e:
        print(f"Lỗi: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    update_product_groups()