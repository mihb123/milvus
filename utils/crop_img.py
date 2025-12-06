import os
import cv2
import numpy as np
from ultralytics import YOLO

INPUT_FOLDER = "train/AC-MILAN"
OUTPUT_FOLDER = "train_cropped2"
MODEL_NAME = "yolov8x-seg.pt"

def main():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    model = YOLO(MODEL_NAME)

    for filename in os.listdir(INPUT_FOLDER):
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp')):
            continue

        file_path = os.path.join(INPUT_FOLDER, filename)
        img = cv2.imread(file_path)

        if img is None:
            continue

        results = model.predict(img, conf=0.5, classes=[0], verbose=False)
        result = results[0]

        if result.masks is None:
            continue

        masks = result.masks.data.cpu().numpy()
        boxes = result.boxes.data.cpu().numpy()

        best_idx = -1
        max_area = 0

        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = map(int, box[:4])
            area = (x2 - x1) * (y2 - y1)
            if area > max_area:
                max_area = area
                best_idx = i
        
        if best_idx == -1:
            continue

        h, w = img.shape[:2]
        mask = masks[best_idx]
        mask = cv2.resize(mask, (w, h))
        binary_mask = (mask > 0.5).astype(np.uint8)

        background = np.zeros_like(img, dtype=np.uint8)
        
        mask_3ch = cv2.merge([binary_mask, binary_mask, binary_mask])
        segmented_img = np.where(mask_3ch == 1, img, background)

        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, cw, ch = cv2.boundingRect(largest_contour)
            
            final_crop = segmented_img[y:y+ch, x:x+cw]
            
            output_path = os.path.join(OUTPUT_FOLDER, filename)
            cv2.imwrite(output_path, final_crop)
            print(f"Saved: {filename}")

if __name__ == "__main__":
    main()