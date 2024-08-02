import os
import cv2
from PIL import Image
from paddleocr import PaddleOCR
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg
import Config as cf

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

class RecognizedTextOcr:
    def __init__(self,image,filename):
        self.image = image
        self.filename = filename

    def recognized_text_english(self):
        text_pages = {}
        if self.filename.endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
            text_dict = self.perform_ocr_english(self.image)
            text_pages[self.filename] = text_dict
        return text_pages

    def recognized_text_vietnamese(self):
        text_pages_vietnamese = {}
        text_pages = self.recognized_text_english()
        for text_page in text_pages:
            image_filename = text_page
            boxes = text_pages[image_filename]
            text_dict = self.perform_ocr_vietnamese(boxes)
            text_pages_vietnamese[self.filename] = text_dict
        return text_pages_vietnamese

    def initialize_ocr(self):
        return PaddleOCR(
            lang='en',
            log_level='DEBUG',
            det_db_box_thresh=0.3,
            use_angle_cls=True,
            det_db_thresh=0.8,
            cls_batch_num=40,
            drop_score=0
        )
     
    def viet_ocr(self):
        config = Cfg.load_config_from_name('vgg_seq2seq')
        config['cnn']['pretrained'] = True
        config['device'] = cf.device
        viet_ocr_detector = Predictor(config)
        return viet_ocr_detector
        
    def perform_ocr_vietnamese(self, boxes):
        viet_ocr_detector = self.viet_ocr()
        text_key_value_list = []
        for box in boxes:
            # Extract coordinates
            x_coords = [int(point[0]) for point in box[1]]
            y_coords = [int(point[1]) for point in box[1]]

            # Define ROI boundaries with padding
            startx = max(0, min(x_coords) - 2)
            starty = max(0, min(y_coords) - 2)
            endx = min(self.image.shape[1], max(x_coords) + 1)
            endy = min(self.image.shape[0], max(y_coords) + 1)

            # Extract ROI from image and convert to PIL Image
            roi = self.image[starty:endy, startx:endx]
            roi_pil = Image.fromarray(roi)

            # Perform OCR
            text = viet_ocr_detector.predict(roi_pil)

            # Append results
            text_key_value_list.append([text, box[1]])
        return text_key_value_list

    def perform_ocr_english(self, image):
        if image is None:
            print(f"Không thể đọc ảnh: {self.filename}")
            return
        ocr_model = self.initialize_ocr()
        result = ocr_model.ocr(image)[0]
        boxes = [line[0] for line in result]
        texts = [line[1][0] for line in result]
        probabilities = [line[1][1] for line in result]
        text_list = []
        for box, text, _ in zip(boxes, texts, probabilities):
            key = text
            value = box
            text_list.append([key,value])
        return text_list
             
if __name__ == "__main__":
    image_dir = r'C:\Users\Admin\Downloads\AI_DETECT_MODEL_DOCUMENT\pages\page2_NMQ.jpg'
    label_map = {0: "Table", 1: "Title", 2: "List", 3: "Table1", 4: "Figure"}
    image = cv2.imread(image_dir)
    document_ocr = RecognizedTextOcr(image,'page2_NMQ.jpg')
    text_pages = document_ocr.recognized_text_english()
    text_pages = document_ocr.recognized_text_vietnamese()
    print(text_pages)
    print("Hoàn thành quá trình xử lý tất cả các ảnh.")
