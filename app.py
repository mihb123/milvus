import os
import math
import warnings
from flask import Flask, request, jsonify
from PIL import Image, ImageDraw
from dotenv import load_dotenv
from extractor import FeatureExtractor, FEATURE_DIMENSION, MODEL_NAME
from milvus_db import MilvusManager
from import_data import run_import, DATA_DIR
from add_data import process_add_data, ADD_DIR

load_dotenv()

warnings.filterwarnings("ignore", category=UserWarning, module='milvus_lite')

PORT = int(os.getenv('PORT', 51200))

print(">>> Initializing Milvus & Extractor...", flush=True)
extractor = FeatureExtractor()
print(">>> Initializing Milvus Connection...", flush=True)
milvus_manager = MilvusManager(dimension=FEATURE_DIMENSION)

if not milvus_manager.has_data():
    print(">>> DB Check: EMPTY. Starting Import...", flush=True)
    run_import(milvus_manager)
else:
    print(">>> DB Check: DATA EXISTS. Skipping Import.", flush=True)

app = Flask(__name__)

@app.route('/api/search-by-image', methods=['POST'])
def search_image():

    if 'image' not in request.files:
        return jsonify({"status_code": 400, "message": "No file part", "data": null}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"status_code": 400, "message": "No selected file", "data": null}), 400

    try:
        query_vector = extractor(file) 
        
        if not query_vector:
            return jsonify({"status_code": 500, "message": "Extraction failed", "data": null}), 500

        search_results = milvus_manager.search_images(query_vector, limit=20)
        
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
        
        return jsonify({
            "status_code": 200,
            "message": "success",
            "data": final_results
        })

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"status_code": 500, "message": str(e), "data": null}), 500

@app.route('/api/search-by-image/add-image', methods=['POST'])
def add_image():
    try:
        if 'image' not in request.files:
            return jsonify({"status_code": 400, "message": "No image file provided", "data": null}), 400
        
        name_key = request.form.get('name_key')
        if not name_key:
            return jsonify({"status_code": 400, "message": "Missing name_key", "data": null}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({"status_code": 400, "message": "No selected file", "data": null}), 400

        if not os.path.exists(ADD_DIR):
            os.makedirs(ADD_DIR)

        target_name_key = name_key.strip() 
        
        if os.path.exists(DATA_DIR):
            for existing_folder in os.listdir(DATA_DIR):
                if existing_folder.lower().strip() == target_name_key.lower():
                    print(f">>> Auto-corrected '{target_name_key}' -> '{existing_folder}'", flush=True)
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
            "status_code": 200,
            "message": "Image processed successfully",
            "data": result,
        })

    except Exception as e:
        print(f"❌ Error adding image: {e}")
        return jsonify({"status_code": 500, "message": str(e), "data": null}), 500
    
@app.route('/api/check-healthy', methods=['GET'])
def check_healthy():
    return jsonify({"status_code": 200, "message": "Server is healthy"})

if __name__ == '__main__':
    print(f">>> Service running on port {PORT}", flush=True)
    app.run(host='0.0.0.0', port=PORT, threaded=True)
    
