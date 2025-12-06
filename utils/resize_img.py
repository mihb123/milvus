import os
from PIL import Image

def resize_images_in_folder(input_folder, output_folder, target_height=768):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"✅ Đã tạo folder mới: {output_folder}")

    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
    
    files = os.listdir(input_folder)
    total_files = len([f for f in files if f.lower().endswith(valid_extensions)])
    processed_count = 0

    print(f"🚀 Bắt đầu xử lý {total_files} ảnh...")
    print("-" * 30)

    for filename in files:
        if filename.lower().endswith(valid_extensions):
            try:
                input_path = os.path.join(input_folder, filename)
                output_path = os.path.join(output_folder, filename)

                with Image.open(input_path) as img:
                    aspect_ratio = img.width / img.height
                    new_height = target_height
                    new_width = int(aspect_ratio * new_height)

                    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    resized_img.save(output_path, quality=90, optimize=True)
                    
                    processed_count += 1
                    print(f"[{processed_count}/{total_files}] Đã resize: {filename} -> ({new_width}x{new_height})")

            except Exception as e:
                print(f"❌ Lỗi file {filename}: {e}")

    print("-" * 30)
    print(f"🎉 Hoàn tất! Đã xử lý {processed_count} ảnh.")
    print(f"📂 Kiểm tra folder: {output_folder}")

if __name__ == "__main__":
    FOLDER_INPUT = r"/home/minhchu1336/Downloads/super-hero" 
    FOLDER_OUTPUT = r"/home/minhchu1336/Downloads/sah-output"

    resize_images_in_folder(FOLDER_INPUT, FOLDER_OUTPUT, target_height=1080)