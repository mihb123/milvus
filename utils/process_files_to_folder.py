import os
import shutil
import concurrent.futures

def flatten_single_folder(target_folder_path):
    """
    Hàm xử lý cho 1 folder cụ thể (ví dụ: ../add-data/ABC)
    """
    folder_name = os.path.basename(target_folder_path)
    print(f"🔄 Đang xử lý: {folder_name}...")
    
    files_moved = 0
    
    # BƯỚC 1: DI CHUYỂN FILE RA NGOÀI
    # Sử dụng os.walk để duyệt cây thư mục
    # topdown=False để duyệt từ dưới lên (con trước cha sau)
    for root, dirs, files in os.walk(target_folder_path):
        # Nếu root chính là folder đích thì bỏ qua (không cần di chuyển file đang ở đúng chỗ)
        if root == target_folder_path:
            continue
            
        for filename in files:
            source_file = os.path.join(root, filename)
            destination_file = os.path.join(target_folder_path, filename)
            
            # --- XỬ LÝ TRÙNG TÊN ---
            # Nếu file đích đã tồn tại, thêm hậu tố _1, _2...
            if os.path.exists(destination_file):
                base, extension = os.path.splitext(filename)
                counter = 1
                while os.path.exists(destination_file):
                    new_name = f"{base}_{counter}{extension}"
                    destination_file = os.path.join(target_folder_path, new_name)
                    counter += 1
            # -----------------------

            try:
                shutil.move(source_file, destination_file)
                files_moved += 1
            except Exception as e:
                print(f"❌ Lỗi di chuyển file {filename}: {e}")

    # BƯỚC 2: XÓA CÁC FOLDER RỖNG (CLEAN UP)
    # Duyệt lại một lần nữa từ dưới lên trên (topdown=False) để xóa folder con
    cleaned_folders = 0
    for root, dirs, files in os.walk(target_folder_path, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                # Chỉ xóa nếu folder rỗng
                # Vì chúng ta đã move hết file nên lý thuyết là nó sẽ rỗng
                os.rmdir(dir_path) 
                cleaned_folders += 1
            except OSError:
                # Có thể folder vẫn còn chứa file rác (hidden files) hoặc lỗi permission
                # Nếu muốn xóa CƯỠNG BỨC bất kể có file rác hay không, dùng shutil.rmtree(dir_path)
                # Nhưng an toàn nhất là chỉ xóa folder rỗng.
                pass

    return f"✅ {folder_name}: Đã chuyển {files_moved} files, Xóa {cleaned_folders} folders con."

def main():
    BASE_DIR = "../add-data"
    
    if not os.path.exists(BASE_DIR):
        print(f"❌ Không tìm thấy thư mục {BASE_DIR}")
        return

    # Lấy danh sách các folder cấp 1 (ABC, XYZ...)
    subfolders = [
        os.path.join(BASE_DIR, f) 
        for f in os.listdir(BASE_DIR) 
        if os.path.isdir(os.path.join(BASE_DIR, f))
    ]

    if not subfolders:
        print("⚠️ Không có folder nào trong add-data để xử lý.")
        return

    print(f"🚀 Tìm thấy {len(subfolders)} folder cần làm phẳng. Bắt đầu...")
    print("-" * 50)

    # Chạy đa luồng để xử lý nhiều folder ABC, XYZ cùng lúc
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        results = executor.map(flatten_single_folder, subfolders)
        
        for result in results:
            print(result)

    print("-" * 50)
    print("🎉 Hoàn tất quá trình làm phẳng thư mục!")

if __name__ == "__main__":
    main()