import os
import re

def clean_and_rename_folders(root_folder, dry_run=True):
    """
    root_folder: Đường dẫn thư mục cha chứa các folder cần đổi tên
    dry_run: True = Chỉ in ra màn hình để kiểm tra, False = Thực hiện đổi tên thật
    """
    if not os.path.exists(root_folder):
        print(f"❌ Không tìm thấy thư mục: {root_folder}")
        return

    print(f"🚀 Bắt đầu quét tại: {root_folder}")
    if dry_run:
        print("⚠️  CHẾ ĐỘ CHẠY THỬ (DRY RUN) - Chưa thay đổi gì cả.")
    print("-" * 60)

    # Dùng os.walk với topdown=False để đổi tên thư mục con trước, 
    # tránh lỗi không tìm thấy đường dẫn khi đổi tên thư mục cha.
    for dirpath, dirnames, filenames in os.walk(root_folder, topdown=False):
        for dirname in dirnames:
            old_name = dirname
            
            # --- XỬ LÝ LOGIC ĐỔI TÊN ---
            
            # 1. Xử lý phần đầu: Loại bỏ số thứ tự (12.), dấu thăng (#), khoảng trắng thừa
            # Regex giải thích:
            # ^          : Bắt đầu chuỗi
            # (?: ... )+ : Nhóm các mẫu khớp 1 hoặc nhiều lần
            # \d+\.\s* : Số theo sau là dấu chấm (vd: 12. , 1.)
            # #          : Dấu thăng
            # [\s\-_]+   : Dấu cách, gạch ngang, gạch dưới ở đầu
            new_name = re.sub(r'^(?:\d+\.\s*|#|[\s\-_]+)+', '', old_name)
            
            # 2. Trim khoảng trắng thừa ở 2 đầu sau khi cắt
            new_name = new_name.strip()
            
            # 3. In hoa toàn bộ (giữ nguyên ngoặc đơn vì upper() không ảnh hưởng ký tự đặc biệt)
            new_name = new_name.upper()

            # --- KẾT THÚC LOGIC ---

            if new_name != old_name:
                old_path = os.path.join(dirpath, old_name)
                new_path = os.path.join(dirpath, new_name)

                # Kiểm tra xem tên mới có bị trùng không
                if os.path.exists(new_path):
                    print(f"⚠️  BỎ QUA: '{old_name}' -> '{new_name}' (Tên mới đã tồn tại)")
                    continue

                if dry_run:
                    print(f"👀 [Dự kiến] '{old_name}'  --->  '{new_name}'")
                else:
                    try:
                        os.rename(old_path, new_path)
                        print(f"✅ [Đã đổi] '{old_name}'  --->  '{new_name}'")
                    except Exception as e:
                        print(f"❌ [Lỗi] Không thể đổi tên '{old_name}': {e}")
    
    print("-" * 60)
    if dry_run:
        print("💡 Hãy đổi biến 'dry_run = False' trong code để áp dụng thay đổi.")
    else:
        print("🎉 Hoàn tất!")

# --- CẤU HÌNH ---
if __name__ == "__main__":
    # Thay đường dẫn folder của bạn vào đây
    TARGET_FOLDER = "../image/Áo bóng đá" 
    
    # Bật True để test, bật False để chạy thật
    clean_and_rename_folders(TARGET_FOLDER, dry_run=False)