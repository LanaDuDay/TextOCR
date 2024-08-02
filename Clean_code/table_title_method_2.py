import cv2
import numpy as np
from img2table.document import Image
from io import BytesIO
import matplotlib.pyplot as plt

class ImageProcessor:
    def __init__(self, img_path=None, img_bytes=None, file_like=None):
        if img_path:
            self.image = Image(src=img_path)
            self.img_cv2 = cv2.imread(img_path)
        elif img_bytes:
            self.image = Image(src=img_bytes)
            self.img_cv2 = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
        elif file_like:
            self.image = Image(src=BytesIO(file_like))
            self.img_cv2 = cv2.imdecode(np.frombuffer(file_like, np.uint8), cv2.IMREAD_COLOR)
        else:
            raise ValueError("You must provide either an image path, bytes, or file-like object.")
        
        self.gray_img = None
        self.binary_img = None
        self.contrast_img = None

    def to_grayscale(self):
        self.gray_img = cv2.cvtColor(self.img_cv2, cv2.COLOR_BGR2GRAY)

    def to_binary(self):
        if self.gray_img is None:
            self.to_grayscale()
        _, self.binary_img = cv2.threshold(self.gray_img, 0, 50, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    def increase_contrast(self):
        if self.binary_img is None:
            self.to_binary()
        self.contrast_img = cv2.equalizeHist(self.binary_img)

    def show_image(self, image_type='original'):
        if image_type == 'original':
            img = cv2.cvtColor(self.img_cv2, cv2.COLOR_BGR2RGB)
        elif image_type == 'grayscale':
            if self.gray_img is None:
                self.to_grayscale()
            img = self.gray_img
        elif image_type == 'binary':
            if self.binary_img is None:
                self.to_binary()
            img = self.binary_img
        elif image_type == 'contrast':
            if self.contrast_img is None:
                self.increase_contrast()
            img = self.contrast_img
        else:
            raise ValueError("Invalid image type. Choose from 'original', 'grayscale', 'binary', 'contrast'.")
        
        plt.imshow(img, cmap='gray' if len(img.shape) == 2 else None)
        plt.title(f'{image_type.capitalize()} Image')
        plt.axis('off')
        plt.show()

# Usage example
img_path = r"C:\Users\Admin\Downloads\AI_DETECT_MODEL_DOCUMENT\pagesPdf\page2_NMQ.jpg" # Replace with your image path
processor = ImageProcessor(img_path=img_path)
processor.to_grayscale()
processor.to_binary()
processor.increase_contrast()

# Display images
processor.show_image('original')
processor.show_image('grayscale')
processor.show_image('binary')
processor.show_image('contrast')
