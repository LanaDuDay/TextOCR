"""
Module: recognized_table_areas_text
Mô tả:
    Nhận diện text trong bảng  
"""
import os
import cv2 #type: ignore
from recognized_text import RecognizedTextOcr
from recognized_table_areas import TableAreaDetector # type: ignore
from table_header_row import TableAreaJson # type: ignore
from title_table_key import TableKeyTitleValue # type: ignore
from table_title_method_2 import TableHeaderRecognized
# Thiết lập biến môi trường
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
import Config as cf
class TabelAreasTextRecoginized:
    """
    Nhận diện text trong bảng, các tọa độ bảng được lưu trong table_areas_dict
    """
    def __init__(self, filename):
        self.filename = filename

    def table_image(self,image):
        """
        Lấy tọa độ vùng chứa text sử dụng TableAreaDetector
        """
        table_areas_model = TableAreaDetector(self.filename)
        table_areas_dict = table_areas_model.table_areas(image)
        extracted_images = []
        count = 0
        for _ , areas in table_areas_dict.items():
            count+=1
            for (x1, y1, x2, y2) in areas:
                table_area = image[y1:y2, x1:x2]
                extracted_images.append(table_area)
                if not os.path.exists(cf.config_table_areas_temp):
                    os.makedirs(cf.config_table_areas_temp)
                output_path = os.path.join(cf.config_table_areas_temp, f"table_area{count}.png")
                cv2.imwrite(output_path, table_area)
        return extracted_images

    def recognize_table_areas_text(self,image):
        """
        Nhận diện vùng chứa text tiếng việt
        """
        extracted_images = self.table_image(image)
        text_pages = []
        for extracted_image in extracted_images:
            recognized_model = RecognizedTextOcr(extracted_image,self.filename)
            text_page = recognized_model.recognized_text_vietnamese()
            text_pages.append(text_page.values())
        return text_pages
    
# model = TabelAreasTextRecoginized('page2.jpg')
# image_dir = r"C:\Users\Admin\Downloads\AI_DETECT_MODEL_DOCUMENT\pagesPdf\page2_DTH.jpg"
# image = cv2.imread(image_dir)
# table_image = model.table_image(image)
# text_pages = model.recognize_table_areas_text(image)
# model_header = TableHeaderRecognized(list(text_pages[0])[0])
# filtered_array, result_arrays = model_header.predict_title_value()
# # print("Header AREA: ",y1)
# print("Title table:",result_arrays)

# model_table_json = TableAreaJson(list(text_pages[0])[0])
# model_table_title = TableKeyTitleValue(list(text_pages[0])[0])
# row_data = model_table_json.main_json()
# print(row_data)