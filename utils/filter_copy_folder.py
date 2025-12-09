import os
import shutil
import concurrent.futures
import threading
import time

print_lock = threading.Lock()

def copy_single_folder(folder_name, src_path, dest_path):
    """
    Hàm xử lý copy cho 1 luồng
    """
    try:
        # dirs_exist_ok=True: Rất quan trọng khi quét nested folder.
        # Nếu tìm thấy folder cùng tên ở nhiều nơi, nó sẽ gộp (merge) chung vào đích.
        shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
        
        with print_lock:
            # Chỉ in tên folder cho ngắn gọn
            print(f"✅ [XONG] {folder_name}")
        return "SUCCESS"
    except Exception as e:
        with print_lock:
            print(f"❌ [LỖI] {src_path}: {e}")
        return "ERROR"

def main():
    # --- CẤU HÌNH ---
    REF_DIR = "../product_train"
    SOURCE_DIR = "../image/Áo bóng đá"
    DEST_DIR = "../add-data"
    MAX_WORKERS = 5

    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)

    # BƯỚC 1: Tạo Set tham chiếu (Lookup O(1))
    print("🔍 Đang quét danh sách folder tham chiếu...")
    valid_names = set()
    if os.path.exists(REF_DIR):
        for name in os.listdir(REF_DIR):
            if os.path.isdir(os.path.join(REF_DIR, name)):
                valid_names.add(name)
    
    if not valid_names:
        print("❌ Không tìm thấy folder nào trong product_train.")
        return
    print(f"📋 Đã load {len(valid_names)} tên folder hợp lệ.")

    # BƯỚC 2: Quét đệ quy (os.walk) để tìm task
    print(f"🚀 Đang quét toàn bộ thư mục con trong {SOURCE_DIR}...")
    tasks = []
    
    # os.walk trả về: đường dẫn thư mục cha, danh sách folder con, danh sách file
    for root, dirs, files in os.walk(SOURCE_DIR):
        # Duyệt qua các folder con ở cấp hiện tại
        # Lưu ý: Ta dùng list(dirs) để tạo bản sao, cho phép sửa đổi dirs gốc nếu cần
        for dir_name in list(dirs):
            if dir_name in valid_names:
                src_path = os.path.join(root, dir_name)
                dest_path = os.path.join(DEST_DIR, dir_name)
                
                tasks.append((dir_name, src_path, dest_path))
                
                # [TỐI ƯU QUAN TRỌNG]:
                # Nếu đã tìm thấy folder trùng tên (VD: "Barca"), ta copy cả folder đó.
                # Không cần đi sâu vào bên trong "Barca" để quét tiếp nữa -> Xóa khỏi danh sách duyệt.
                dirs.remove(dir_name) 

    total_tasks = len(tasks)
    print(f"🎯 Tìm thấy {total_tasks} folder khớp tên (bao gồm cả nested). Bắt đầu copy...")
    print("-" * 50)

    # BƯỚC 3: Thực thi đa luồng
    start_time = time.time()
    success_count = 0
    error_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {
            executor.submit(copy_single_folder, name, src, dest): name 
            for name, src, dest in tasks
        }

        for future in concurrent.futures.as_completed(future_map):
            if future.result() == "SUCCESS":
                success_count += 1
            else:
                error_count += 1

    end_time = time.time()
    duration = end_time - start_time

    print("-" * 50)
    print("🎉 TỔNG KẾT:")
    print(f"- Tổng tìm thấy: {total_tasks}")
    print(f"- Copy thành công: {success_count}")
    print(f"- Lỗi: {error_count}")
    print(f"- Thời gian: {duration:.2f}s")

if __name__ == "__main__":
    main()