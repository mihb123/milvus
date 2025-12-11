import torch
import os
from PIL import Image
from transformers import AutoImageProcessor, AutoModel
from sklearn.preprocessing import normalize
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv('MODEL_NAME', 'facebook/dinov2-small')
FEATURE_DIMENSION = int(os.getenv('FEATURE_DIMENSION', 384))

class FeatureExtractor:
    def __init__(self, modelname=MODEL_NAME):
        self.processor = AutoImageProcessor.from_pretrained(modelname, use_fast=True)
        self.model = AutoModel.from_pretrained(modelname)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        self.model.eval()

    def __call__(self, image_input) -> list:
        try:
            input_image = Image.open(image_input).convert("RGB")
            inputs = self.processor(images=input_image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)

            feature_vector = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            return normalize(feature_vector, norm="l2").flatten().tolist()
        except Exception as e:
            print(f"Error extracting features: {e}")
            return []