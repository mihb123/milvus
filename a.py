import os
import time
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm

from extractor import FeatureExtractor, FEATURE_DIMENSION, MODEL_NAME
from milvus_db import MilvusManager

ROOT_DIR = "./products" 
QUERY_IMAGE = "./test.jpg"
INSERT_DATA = False
BATCH_SIZE = 50

def run_indexing(db_manager: MilvusManager, extractor: FeatureExtractor):
    
    all_image_paths = []
    
    print("Đang quét cấu trúc thư mục...")
    if not os.path.exists(ROOT_DIR):
        print(f"Không tìm thấy thư mục {ROOT_DIR}")
        return

    # --- LEVEL 1: CATEGORY ---
    for category_name in os.listdir(ROOT_DIR):
        cat_path = os.path.join(ROOT_DIR, category_name)
        if not os.path.isdir(cat_path):
            continue

        # --- LEVEL 2: GROUP ---
        for group_folder in os.listdir(cat_path):
            group_path = os.path.join(cat_path, group_folder)
            if not os.path.isdir(group_path):
                continue
            
            # Logic tách group_name và group_id từ tên folder
            # Ví dụ: "AoThun_AT123" -> name="AoThun", id="AT123"
            if "_" in group_folder:
                # rsplit để tách từ dấu _ cuối cùng (phòng trường hợp tên có dấu _)
                group_name, group_id = group_folder.rsplit("_", 1)
            else:
                group_name = group_folder
                group_id = "UNKNOWN"

            # --- LEVEL 3: IMAGES ---
            for filename in os.listdir(group_path):
                if filename.lower().endswith((".jpeg", ".jpg", ".png", ".bmp", ".webp")):
                    filepath = os.path.join(group_path, filename)
                    
                    all_image_paths.append({
                        "path": filepath,
                        "name": filename,
                        "category": category_name,
                        "group_name": group_name,
                        "group_id": group_id
                    })
    
    print(f"Tìm thấy tổng cộng {len(all_image_paths)} ảnh. Bắt đầu trích xuất...")

    batch_data = []
    total_inserted = 0

    for item in tqdm(all_image_paths, desc="Processing Images"):
        filepath = item["path"]
        try:
            image_embedding = extractor(filepath)
            
            if len(image_embedding) != FEATURE_DIMENSION:
                print(f"\n⚠️ Lỗi kích thước: {filepath}")
                continue
            
            # Thêm metadata mới vào đây
            batch_data.append({
                "vector": image_embedding, 
                "filename": filepath,
                "name": item["name"],
                "category": item["category"],
                "group_name": item["group_name"], # Field mới
                "group_id": item["group_id"]      # Field mới
            })
            
            if len(batch_data) >= BATCH_SIZE:
                db_manager.insert_batch(batch_data)
                total_inserted += len(batch_data)
                batch_data = []

        except Exception as e:
            print(f"\n❌ Lỗi file {filepath}: {e}")
            continue
    
    if batch_data:
        db_manager.insert_batch(batch_data)
        total_inserted += len(batch_data)
    
    print(f"Đã insert xong {total_inserted} vector vào Milvus.")


def display_results(query_path: str, search_results):
    print(f"\nQuery Image: {query_path}")
    try:
        query_img = Image.open(query_path).convert("RGB").resize((200, 200))
        query_img.show(title="Query Image")
    except Exception as e:
        print(f"Không thể mở ảnh query: {e}")
        return

    if not search_results:
        print("Không tìm thấy kết quả.")
        return

    hits = search_results[0]
    res_images = []
    print(f"\nTop {len(hits)} results:")
    
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()

    for hit in hits:
        milvus_id = hit["id"]
        score = hit["distance"]
        entity = hit["entity"]
        
        # Lấy metadata mới
        filename = entity.get("filename", "Unknown")
        cat = entity.get("category", "Unknown")
        g_name = entity.get("group_name", "Unknown")
        g_id = entity.get("group_id", "Unknown")
        
        print(f"  - ID: {milvus_id} | Score: {score:.4f}")
        print(f"    Path: {filename}")
        print(f"    Group: {g_name} (ID: {g_id}) | Cat: {cat}")
        print("-" * 30)

        try:
            img = Image.open(filename).convert("RGB").resize((200, 200))
            draw = ImageDraw.Draw(img)
            
            # Vẽ thông tin lên ảnh kết quả
            draw.rectangle([(0, 0), (200, 50)], fill="black")
            draw.text((5, 5), f"ID:{milvus_id} | {score:.2f}", fill="#00ff00", font=font)
            draw.text((5, 25), f"Grp:{g_name}", fill="white", font=font)
            
            res_images.append(img)
        except Exception as e:
            print(f"   ⚠️ Lỗi hiển thị ảnh: {filename}")

    if not res_images:
        return

    # Hiển thị grid ảnh kết quả
    cols = 5
    rows = (len(res_images) + cols - 1) // cols
    w, h = 200, 200
    grid_img = Image.new('RGB', (cols * w, rows * h), color="white")

    for idx, img in enumerate(res_images):
        x = (idx % cols) * w
        y = (idx // cols) * h
        grid_img.paste(img, (x, y))

    grid_img.show(title="Search Results")

if __name__ == "__main__":
    start_total = time.time()
    
    db_manager = MilvusManager(dimension=FEATURE_DIMENSION)
    extractor = FeatureExtractor(MODEL_NAME)
    
    # Bật cái này lên True nếu bạn muốn quét lại thư mục và insert dữ liệu mới
    if INSERT_DATA:
        start_idx = time.time()
        run_indexing(db_manager, extractor)
        print(f"Indexing time: {time.time() - start_idx:.2f}s")

    print("\nExtracting features from query image...")
    query_vector = extractor(QUERY_IMAGE)
    
    print("Searching in Milvus...")
    start_search = time.time()
    results = db_manager.search_images(query_vector, limit=10)
    print(f"Search time: {time.time() - start_search:.4f}s")

    display_results(QUERY_IMAGE, results)

    print(f"\nTotal run time: {time.time() - start_total:.2f}s")