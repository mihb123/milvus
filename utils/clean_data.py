import os
import concurrent.futures
import threading
from resize_img import resize_single_image 

# Khóa để ngăn các luồng in ra màn hình cùng lúc gây loạn chữ
print_lock = threading.Lock()

def process_one_file(file_path):
    target_size_bytes = 2 * 1024 * 1024  # 2MB
    valid_img_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
    files_to_delete = ('.ai', '.mp4', '.psd')
    
    filename = os.path.basename(file_path)
    
    try:
        # 1. Xóa file rác (.ai, .mp4)
        if filename.lower().endswith(files_to_delete):
            os.remove(file_path)
            return "DELETED", f"🗑️  Đã xóa: {filename}"

        # 2. Resize ảnh > 2MB
        if filename.lower().endswith(valid_img_extensions):
            file_size = os.path.getsize(file_path)
            if file_size > target_size_bytes:
                # Gọi hàm resize
                success, msg = resize_single_image(file_path, target_height=768)
                if success:
                    new_size = os.path.getsize(file_path)
                    return "RESIZED", f"✅ Resize {filename}: {(file_size/1024/1024):.1f}MB -> {(new_size/1024/1024):.1f}MB"
                else:
                    return "ERROR", f"❌ Lỗi resize {filename}: {msg}"
        
        # Không làm gì cả
        return "SKIPPED", None

    except Exception as e:
        return "ERROR", f"❌ Lỗi file {filename}: {e}"

def main():
    folder_to_scan = "../image/Áo bóng đá"
    if not os.path.exists(folder_to_scan):
        print(f"❌ Không tìm thấy thư mục {folder_to_scan}")
        return

    # Bước 1: Quét toàn bộ file path đưa vào danh sách trước
    print("🚀 Đang quét danh sách file...")
    all_files = []
    for root, dirs, files in os.walk(folder_to_scan):
        for filename in files:
            all_files.append(os.path.join(root, filename))
    
    total_files = len(all_files)
    print(f"📋 Tìm thấy {total_files} file. Bắt đầu xử lý đa luồng...")
    print("-" * 50)

    stats = {
        "DELETED": 0,
        "RESIZED": 0,
        "ERROR": 0,
        "SKIPPED": 0
    }
    completed_count = 0

    # Bước 2: Khởi tạo ThreadPoolExecutor
    # max_workers=10 nghĩa là xử lý 10 file cùng lúc. 
    # Bạn có thể tăng lên 20 nếu máy mạnh, hoặc giảm xuống 5 nếu máy yếu.
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Submit các file vào luồng xử lý
        future_to_file = {executor.submit(process_one_file, f): f for f in all_files}

        for future in concurrent.futures.as_completed(future_to_file):
            status, message = future.result()
            
            # Cập nhật thống kê
            stats[status] += 1
            completed_count += 1

            # In thông báo (chỉ in khi có hành động hoặc lỗi để đỡ rối mắt)
            if message:
                with print_lock:
                    print(f"[{completed_count}/{total_files}] {message}")

    print("-" * 50)
    print("🎉 TỔNG KẾT:")
    print(f"- Đã xóa: {stats['DELETED']}")
    print(f"- Đã resize: {stats['RESIZED']}")
    print(f"- Lỗi: {stats['ERROR']}")
    print(f"- Bỏ qua (không cần xử lý): {stats['SKIPPED']}")

if __name__ == "__main__":
    main()