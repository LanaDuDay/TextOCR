import os
import cv2
import numpy as np
from img2table.document import Image #type: ignore
from img2table.ocr import PaddleOCR  #type: ignore
from io import BytesIO
import matplotlib.pyplot as plt

import cv2
print(dir(cv2.ximgproc))


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


# # Usage example
# img_path = r"C:\Users\Admin\Downloads\AI_DETECT_MODEL_DOCUMENT\pagesPdf\page2_NMQ.jpg" # Replace with your image path
# processor = ImageProcessor(img_path=img_path)
# processor.to_grayscale()
# processor.to_binary()
# processor.increase_contrast()

# # Display images
# processor.show_image('original')
# processor.show_image('grayscale')
# processor.show_image('binary')
# processor.show_image('contrast')


# Load the image
img_from_path = Image(r"C:\Users\Admin\Downloads\AI_DETECT_MODEL_DOCUMENT\Clean_code\table_area_462.png")
# Initialize the OCR engine

# Extract tables with custom parameters
extracted_tables = img_from_path.extract_tables(       # Use PaddleOCR for text extraction
    implicit_rows=True,       # Split implicit rows
    borderless_tables=True,   # Detect borderless tables
    min_confidence=10        # Set minimum confidence level for text extraction
)

print(type(extracted_tables))
print(extracted_tables)

import cv2
import matplotlib.pyplot as plt

img_from_path = r"C:\Users\Admin\Downloads\AI_DETECT_MODEL_DOCUMENT\Clean_code\table_area_462.png" # Update this with the actual path to your image

table_img = cv2.imread(img_from_path)
if table_img is None:
    raise ValueError(f"Could not read the image from the path: {img_from_path}")

table_cells = []
for table in extracted_tables:
    for row in table.content.values():
        for cell in row:
            table_cells.append(cell)
            cv2.rectangle(table_img, (cell.bbox.x1, cell.bbox.y1), (cell.bbox.x2, cell.bbox.y2), (0, 0, 255), 2)

# Convert image from BGR to RGB (matplotlib expects RGB images)
table_img_rgb = cv2.cvtColor(table_img, cv2.COLOR_BGR2RGB)

# Display the image using matplotlib
plt.imshow(table_img_rgb)
plt.title("Table Image")
plt.axis('off')  # Hide axis
plt.show()

