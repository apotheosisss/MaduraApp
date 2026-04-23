from ultralytics import YOLO

class YOLO26Wrapper:
    def __init__(self, model_path: str, device: str = "cpu"):
        self.model_path = model_path
        self.device = device
        self.model: YOLO = None

    def load_model(self):
        self.model = YOLO(self.model_path)
        self.warmup()

    def warmup(self):
        import numpy as np
        dummy = np.zeros((1, 3, 640, 640), dtype=np.uint8)
        self.model.predict(dummy, verbose=False)

    def predict(self, image) -> list:
        results = self.model.predict(image, imgsz=640, verbose=False)
        return results