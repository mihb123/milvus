import time
import os
import math
import warnings
from flask import Flask, request, jsonify
from PIL import Image, ImageDraw
from extractor import FeatureExtractor, FEATURE_DIMENSION, MODEL_NAME
from milvus_db import MilvusManager
from import_data import run_import, DATA_DIR
from add_data import process_add_data, ADD_DIR

warnings.filterwarnings("ignore", category=UserWarning, module='milvus_lite')

PORT = 51200

print(">>> Initializing Milvus & Extractor...", flush=True)
extractor = FeatureExtractor(MODEL_NAME)
milvus_manager = MilvusManager(dimension=FEATURE_DIMENSION)

if not milvus_manager.has_data():
    print(">>> DB Check: EMPTY. Starting Import...", flush=True)
    run_import(milvus_manager)
else:
    print(">>> DB Check: DATA EXISTS. Skipping Import.", flush=True)

def display_results(results):
    if not results: return
    w, h, cols = 200, 200, 5
    
    rows = math.ceil(len(results) / cols)
    # Tạo ảnh nền trắng
    canvas = Image.new('RGB', (cols * w, rows * h), 'white')
    
    # Kết quả đã được sort từ search_image, nên chỉ cần duyệt tuần tự
    for i, item in enumerate(results):
        try:
            folder_path = os.path.join(DATA_DIR, item['name_key'])
            
            if not os.path.exists(folder_path):
                print(f"Missing folder: {folder_path}")
                continue

            # Lấy ảnh đầu tiên tìm thấy
            img_file = None
            for file in os.listdir(folder_path):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    img_file = file
                    break
            
            if not img_file: continue

            img_path = os.path.join(folder_path, img_file)
            img = Image.open(img_path).convert('RGB').resize((w, h))
            
            # --- VẼ SCORE LÊN ẢNH ---
            draw = ImageDraw.Draw(img)
            # Vẽ hình chữ nhật nền đen mờ ở góc để chữ dễ đọc
            draw.rectangle([(0, 0), (100, 20)], fill="black") 
            # Viết chữ (Thứ tự - Score)
            draw.text((5, 5), f"#{i+1}: {item['score']:.3f}", fill="yellow")
            # Viết tên Key ở dưới
            draw.rectangle([(0, h-20), (w, h)], fill="black")
            draw.text((5, h-15), f"{item['name_key']}", fill="white")
            # ------------------------

            x = (i % cols) * w
            y = (i // cols) * h
            canvas.paste(img, (x, y))
        except Exception as e: 
            print(f"Error drawing {item['name_key']}: {e}")

    canvas.show()

app = Flask(__name__)

@app.route('/api/search-by-image', methods=['POST'])
def search_image():
    t_start = time.time()

    if 'image' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        t1 = time.time()
        query_vector = extractor(file) 
        t2 = time.time()
        
        if not query_vector:
            return jsonify({"error": "Extraction failed"}), 500

        t3 = time.time()
        search_results = milvus_manager.search_images(query_vector, limit=50)
        t4 = time.time()
        
        t5 = time.time()
        final_results = []
        seen_keys = set()

        if search_results and len(search_results) > 0:            
            for hit in search_results[0]:
                entity = hit["entity"]
                name_key = entity.get("name_key")
                
                if name_key and name_key not in seen_keys:
                    seen_keys.add(name_key)
                    final_results.append({
                        "name_key": name_key,                        
                        "score": round(float(hit["distance"]), 4)
                    })
                    
                    if len(final_results) >= 10:
                        break
        t6 = time.time()

        dur_extract = t2 - t1
        dur_milvus = t4 - t3
        dur_logic = t6 - t5
        dur_total = time.time() - t_start

        print(f"\n{'='*10} ⏱️  PERFORMANCE REPORT ⏱️  {'='*10}")
        print(f"🔹 1. AI Extract (CPU/GPU) : {dur_extract:.4f} s")
        print(f"🔹 2. Milvus Search (DB)   : {dur_milvus:.4f} s")
        print(f"🔹 3. Logic Filter (Python): {dur_logic:.4f} s")
        print(f"----------------------------------------")
        print(f"🚀 TOTAL EXECUTION TIME    : {dur_total:.4f} s")
        print(f"{'='*46}\n", flush=True)
        
        display_results(final_results)
        
        return jsonify({
            "status": "success",
            "exec_time": round(dur_total, 3),
            "data": final_results
        })

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/search-by-image/add-image', methods=['POST'])
def add_image():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400
        
        name_key = request.form.get('name_key')
        if not name_key:
            return jsonify({"error": "Missing name_key"}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if not os.path.exists(ADD_DIR):
            os.makedirs(ADD_DIR)

        target_name_key = name_key.strip() 
        
        if os.path.exists(DATA_DIR):
            for existing_folder in os.listdir(DATA_DIR):
                if existing_folder.lower() == target_name_key.lower():
                    print(f">>> Auto-corrected '{target_name_key}' -> '{existing_folder}'")
                    target_name_key = existing_folder
                    break
        
        temp_folder = os.path.join(ADD_DIR, target_name_key)
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)

        clean_filename = file.filename.replace(" ", "_") 
        save_path = os.path.join(temp_folder, clean_filename)
        
        file.save(save_path)
        
        print(f">>> Received add request: {name_key} / {clean_filename}")

        result = process_add_data(milvus_manager=milvus_manager, extractor=extractor)

        return jsonify({
            "status": "success",
            "message": "Image processed successfully",
            "details": result,
            "saved_path": os.path.join(DATA_DIR, target_name_key, clean_filename)
        })

    except Exception as e:
        print(f"❌ Error adding image: {e}")
        return jsonify({"error": str(e)}), 500
    

if __name__ == '__main__':
    print(f">>> Service running on port {PORT}", flush=True)
    app.run(host='0.0.0.0', port=PORT, threaded=True)
    
