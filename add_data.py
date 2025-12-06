import os
import shutil
import sys 
from tqdm import tqdm
from extractor import FeatureExtractor, FEATURE_DIMENSION, MODEL_NAME
from milvus_db import MilvusManager
from import_data import DATA_DIR, BATCH_SIZE

ADD_DIR = "add-data"

def process_add_data(milvus_manager=None, extractor=None):
    print(f"\n>>> 🔄 STARTING ADD DATA PROCESS...", flush=True)

    if milvus_manager is None:
        try: 
            milvus_manager = MilvusManager(dimension=FEATURE_DIMENSION)
        except Exception as e: 
            print(f"❌ Error connecting to Milvus: {e}") 
            print("⚠️  Hint: Stop 'service.py' before running this script manually.") 
            return {"status": "error", "message": "Database locked"} 
    
    if extractor is None:
        print(f">>> Loading Model ({MODEL_NAME})...", flush=True)
        extractor = FeatureExtractor(MODEL_NAME)

    if not os.path.exists(ADD_DIR):
        os.makedirs(ADD_DIR)
        print(f">>> Folder '{ADD_DIR}' created. Please put images here.", flush=True)
        return {"status": "empty", "count": 0}

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    tasks = []
    for root, dirs, files in os.walk(ADD_DIR):
        current_name_key = os.path.basename(root)
        if root == ADD_DIR: continue

        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                tasks.append({
                    "path": os.path.join(root, file),
                    "name_key": current_name_key,
                    "filename": file
                })

    if not tasks:
        print(f">>> No new images found in '{ADD_DIR}'.", flush=True)
        return {"status": "no_files", "count": 0}

    print(f">>> Found {len(tasks)} new images.", flush=True)
    
    count_added = 0
    count_moved = 0
    batch_data = []

    for task in tqdm(tasks, desc="Adding"):
        try:
            file_path = task['path']
            filename = task['filename']
            name_key = task['name_key']
            
            if not milvus_manager.check_file_exists(filename):
                vector = extractor(file_path)
                if vector:
                    batch_data.append({
                        "vector": vector,
                        "name_key": name_key,
                        "filename": filename
                    })
                    count_added += 1
            
            if len(batch_data) >= BATCH_SIZE: 
                milvus_manager.insert_batch(batch_data) 
                batch_data = [] 

            dest_folder = os.path.join(DATA_DIR, name_key)
            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder)
            
            dest_path = os.path.join(dest_folder, filename)
            
            shutil.move(file_path, dest_path)
            count_moved += 1

        except Exception as e:
            print(f"Error processing {task['filename']}: {e}")

    if batch_data:
        milvus_manager.insert_batch(batch_data)

    for root, dirs, files in os.walk(ADD_DIR, topdown=False):
        for name in dirs:
            try:
                os.rmdir(os.path.join(root, name))
            except: pass

    print(f"✅ PROCESS COMPLETE.")
    print(f"   - Added to DB: {count_added}")
    print(f"   - Moved to Train: {count_moved}", flush=True)
    
    return {"status": "success", "added": count_added, "moved": count_moved}

if __name__ == "__main__":
    process_add_data()