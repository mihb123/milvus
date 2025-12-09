1. Download ảnh: rclone
2. Resize ảnh > 2MB, xóa .ai, .mp4, .psd file: clean_data.py
3. Clean lại tên folder, loại bỏ tất cả ký tự đặc biệt, trừ (): scr: rename.py, lưu ý đổi tên cả product_train folder
4. Filter and copy folder: python filter_copy_folder.py
5. Xử lý để folder trong add-data chỉ chứa filles: python process_files_to_folder.py