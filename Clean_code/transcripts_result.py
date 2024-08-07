import os
import cv2 #type: ignore
from recognized_text import RecognizedTextOcr
from recognized_table_areas import TableAreaDetector # type: ignore
from table_header_row import TableAreaJson # type: ignore
from title_table_key import TableKeyTitleValue # type: ignore
from table_title_method_2 import TableHeaderRecognized
from recognized_table_areas_text import TabelAreasTextRecoginized

model = TabelAreasTextRecoginized('page2.jpg')
image_dir = r"C:\Users\Admin\Downloads\AI_DETECT_MODEL_DOCUMENT\pagesPdf\page2_DTH.jpg"
image = cv2.imread(image_dir)
table_image = model.table_image(image)
text_pages = model.recognize_table_areas_text(image)
model_header = TableHeaderRecognized(list(text_pages[0])[0])
filtered_array, result_arrays = model_header.predict_title_value()
# print("Header AREA: ",y1)
print("Title table:",result_arrays)

model_table_json = TableAreaJson(list(text_pages[0])[0])
model_table_title = TableKeyTitleValue(list(text_pages[0])[0])
row_data = model_table_json.main_json()
for row in row_data:
    print(row)