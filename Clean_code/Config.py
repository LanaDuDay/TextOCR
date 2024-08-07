import os

import torch #type: ignore

tolerance_row = 38 #Phân loại các text thành các hàng dựa trên tọa độ y với tolerance
tolerance_column = 30 
tolerance_column_key = 20 #Phân loại key theo cột 
config_table_areas_temp = r"C:\Users\Admin\Downloads\AI_DETECT_MODEL_DOCUMENT\Temptable"
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
dataset_dir =  r'C:/Users/Admin/Downloads/AI_DETECT_MODEL_DOCUMENT'
config_table_detect_path = 'lp://TableBank/ppyolov2_r50vd_dcn_365e_tableBank_word/config'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Cefiticate: ROW_tolerance key value: 30-40,
# Transcript: Row_tolerance key value: 15