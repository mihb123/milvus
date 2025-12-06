import os
import mysql.connector
from mysql.connector import Error

# Cấu hình Database
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'test_user',
    'password': 'password123',
    'database': 'ama'
}

ROOT_DIR = 'products'

def rename_folders():
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            cursor = connection.cursor()
            print("Kết nối database thành công. Bắt đầu đổi tên folder...\n")
            
            renamed_count = 0

            if not os.path.exists(ROOT_DIR):
                print(f"Không tìm thấy thư mục gốc '{ROOT_DIR}'")
                return

            # Duyệt folder Category
            for category_name in os.listdir(ROOT_DIR):
                cat_path = os.path.join(ROOT_DIR, category_name)
                
                if os.path.isdir(cat_path):
                    print(f"-> Đang quét Category: {category_name}")

                    # Duyệt folder Group
                    for group_name in os.listdir(cat_path):
                        old_group_path = os.path.join(cat_path, group_name)
                        
                        if os.path.isdir(old_group_path):
                            sql = """
                            SELECT group_id FROM products 
                            WHERE category_name = %s AND group_name = %s 
                            LIMIT 1
                            """
                            cursor.execute(sql, (category_name, group_name))
                            result = cursor.fetchone()

                            if result and result[0]:
                                group_id = result[0]
                                
                                # Tạo tên mới: group_name_group_id
                                new_group_name = f"{group_name}_{group_id}"
                                new_group_path = os.path.join(cat_path, new_group_name)

                                # Thực hiện đổi tên
                                try:
                                    os.rename(old_group_path, new_group_path)
                                    print(f"   [DONE] Đổi tên: '{group_name}' -> '{new_group_name}'")
                                    renamed_count += 1
                                except OSError as e:
                                    print(f"   [ERROR] Không thể đổi tên '{group_name}': {e}")
                            else:
                                print(f"   [SKIP] Không tìm thấy group_id trong DB cho folder: '{group_name}'")

            print(f"\n--- Hoàn tất ---")
            print(f"Tổng số folder đã đổi tên: {renamed_count}")

    except Error as e:
        print(f"Lỗi kết nối SQL: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    rename_folders()