import os
from tqdm import tqdm
from extractor import FeatureExtractor, FEATURE_DIMENSION, MODEL_NAME
from milvus_db import MilvusManager

DATA_DIR = "product_train"
BATCH_SIZE = 50

def run_import(milvus_manager=None):
    print("\n" + "="*40, flush=True)
    print("🚀 STARTING AUTO IMPORT DATA...", flush=True)
    print("="*40, flush=True)

    if milvus_manager is None:
        milvus_manager = MilvusManager(dimension=FEATURE_DIMENSION)

    extractor = FeatureExtractor(MODEL_NAME)
    valid_tasks = []

    for root, dirs, files in os.walk(DATA_DIR):
        current_folder_name = os.path.basename(root)
        
        if root == DATA_DIR or current_folder_name.startswith('.'):
            continue

        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                valid_tasks.append({
                    "path": os.path.join(root, file),
                    "name_key": current_folder_name,
                    "filename": file
                })

    if not valid_tasks:
        print(f"Folder '{DATA_DIR}' is empty.", flush=True)
        return

    batch_data = []
    total_inserted = 0

    for task in tqdm(valid_tasks, desc="Processing"):
        try:
            vector = extractor(task['path'])
            if not vector:
                continue

            batch_data.append({
                "vector": vector,
                "name_key": task['name_key'],
                "filename": task['filename']
            })

            if len(batch_data) >= BATCH_SIZE:
                milvus_manager.insert_batch(batch_data)
                total_inserted += len(batch_data)
                batch_data = []

        except Exception as e:
            print(f"Error processing {task['path']}: {e}", flush=True)

    if batch_data:
        milvus_manager.insert_batch(batch_data)
        total_inserted += len(batch_data)

    print(f"Import finished. Total: {total_inserted}", flush=True)

if __name__ == "__main__":
    run_import()