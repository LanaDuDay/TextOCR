"""
Module: table_column_row_process
Mô tả:
    Đầu vào là data_text là một list và mỗi phần tử của data_text chứa các 
    2 phần tử text và tọa độ text trong ảnh.
    Đầu ra là tọa độ Key_value cho từng dòng trong bảng.
"""
# import json
import re
import json
import Config as cf
from title_table_key import TableKeyTitleValue
class TableAreaJson:
    """
    Mô tả:
    -   Đầu vào là data_text là một list và mỗi phần tử của data_text chứa các 
        2 phần tử text và tọa độ text trong ảnh.
    -   Phân các text theo các hàng các cột:
            group_by_rows(): Phân thành các hàng các hàng
            group_lines_by_x(): Phân loại thành các cột
            update_text_with_coordinates(): Update các key_value theo cột, sửa
                        trực tiếp vào data_text
            row_column_process(): Phân loại các key_value cho từng dòng.
    -   Đầu ra là tọa độ Key_value cho từng dòng trong bảng.
    """
    def __init__(self, data_text):
        self.data_text = data_text

    def main_json(self):
        """Trả về dữ liệu JSON từ các hàng của bảng đã cho."""
        rows = self.row_column_process()
        rows_data = []
        for row in rows:
            texts_dicts = [{'td': self.remove_trailing_abbreviations(item['text'])} for item in rows[row]]
            rows_data.append(texts_dicts)
        
        # Chuyển đổi dữ liệu thành định dạng JSON
        # rows_json = json.dumps(rows_data, ensure_ascii=False, indent=4)
        return rows_data

    def row_column_process(self):
        """
        Xử lý dữ liệu văn bản để nhóm thành các hàng và cột,
        lọc các nhóm dựa trên tọa độ khóa và cập nhật các mục văn bản với tọa độ mới.

        Trả về:
            list: Danh sách các hàng, mỗi hàng chứa các mục văn bản đã được nhóm lại.
        """
        # Đọc dữ liệu từ file
        data = self.data_text
        # Nhóm các dòng theo tọa độ x của chúng để tạo thành các cột
        columns_by_y = self.group_lines_by_y(data, tolerance=cf.tolerance_row)
        # Lấy key_title
        table_keys_title = TableKeyTitleValue(data)
        filtered_array,result_array = table_keys_title.predict_title_value()
        # Xóa các tọa độ trùng khớp khỏi columns_by_x
        self.remove_matching_coordinates(filtered_array, columns_by_y)
        # Cập nhật văn bản với tọa độ mới
        for i in columns_by_y:
            print("columns_by_y", columns_by_y[i])
        return columns_by_y

    def remove_matching_coordinates(self, filtered_array, merged_columns):
        """
        Loại bỏ các phần tử trong `merged_columns` có tọa độ trùng khớp với các phần tử 
        trong `filtered_array`.

        Args:
            filtered_array (list): Danh sách các nhóm phần tử đã lọc, mỗi phần tử có tọa độ.
            merged_columns (dict): Từ điển chứa các cột với các phần tử có tọa độ.

        Returns:
            None: Hàm sửa đổi `merged_columns` trực tiếp.
        """
        for filtered_item in filtered_array:
            for filtered_sub_item in filtered_item:
                filtered_coordinates = filtered_sub_item['coordinates']
                column_keys_to_remove = []
                for column_key in list(merged_columns.keys()):
                    if self.remove_if_matching(filtered_coordinates, column_key, merged_columns):
                        column_keys_to_remove.append(column_key)
                for column_key in column_keys_to_remove:
                    del merged_columns[column_key]

    def remove_if_matching(self, filtered_coordinates, column_key, merged_columns):
        """Xóa các phần tử trong merged_columns có tọa độ trùng khớp 
        và trả về True nếu cột trống."""
        columns_sub_items = merged_columns[column_key]
        for columns_sub_item in columns_sub_items:
            columns_coordinates = columns_sub_item['coordinates']
            if filtered_coordinates == columns_coordinates:
                merged_columns[column_key].remove(columns_sub_item)
                if not merged_columns[column_key]:
                    return True
                break
        return False

    def remove_trailing_abbreviations(self,text):
        '''Biểu thức chính quy tìm các từ thừa khi chúng xuất hiện riêng lẻ ở cuối câu'''
        pattern = r'\b(th|tr|ch|thuy|Ly|Thu|la|thu|nhi|là)\b\s*$'
        # Thay thế các từ tìm thấy bằng một chuỗi rỗng
        cleaned_text = re.sub(pattern, '', text)
        return cleaned_text

    def clean_value(self, value):
        """Làm sạch giá trị văn bản."""
        value = re.sub(r'([ABCD])%', r'\1+', value)
        value = value.replace("?", "-")
        value = re.sub(r'[?/\-@#$^&*]', '', value)
        return value

    def group_by_rows(self,text_items, tolerance):
        '''Hàm để phân loại các text thành các hàng'''
        rows = []
        for item in text_items:
            _, y1_item, _, y2_item = self.convert_coordinates(item['coordinates'])
            center_y = (y1_item + y2_item) / 2
            found_row = False
            for row in rows:
                _, y1_row, _, y2_row = self.convert_coordinates(row[0]['coordinates'])
                center_y_row = (y1_row + y2_row) / 2
                if abs(center_y - center_y_row) <= tolerance:
                    row.append(item)
                    found_row = True
                    break
            if not found_row:
                rows.append([item])
        return rows

    def group_lines_by_y(self, text_boxes, tolerance=cf.tolerance_row):
        '''Phân loại Text vào các hàng'''
        rows_by_y = {}
        for text, coords in text_boxes:
            y_coord = coords[0][1]  # Lấy tọa độ y của điểm đầu tiên
            found_group = False
            for group_y, group_data in rows_by_y.items():
                if abs(group_y - y_coord) <= tolerance:
                    group_data.append({"text": text, "coordinates": coords})
                    found_group = True
                    break
            if not found_group:
                rows_by_y[y_coord] = [{"text": text, "coordinates": coords}]
        
        # Sắp xếp từng hàng theo tọa độ x
        sorted_rows_by_y = {}
        for group_y, items in rows_by_y.items():
            sorted_rows_by_y[group_y] = sorted(items, key=lambda item: item['coordinates'][0][0])
        
        return dict(sorted(sorted_rows_by_y.items()))

    def group_lines_by_x(self, text_boxes, tolerance=cf.tolerance_column):
        '''Phân loại Text vào các cột'''
        columns_by_x = {}
        for text, coords in text_boxes:
            x_coord = coords[0][0]  # Lấy tọa độ x của điểm đầu tiên
            found_group = False
            for group_x, group_data in columns_by_x.items():
                if abs(group_x - x_coord) <= tolerance:
                    group_data.append({"text": text, "coordinates": coords})
                    found_group = True
                    break
            if not found_group:
                columns_by_x[x_coord] = [{"text": text, "coordinates": coords}]
        return dict(sorted(columns_by_x.items()))

    def convert_coordinates(self,coordinates):
        '''Hàm để chuyển đổi tọa độ'''
        x1 = coordinates[0][0]
        y1 = coordinates[0][1]
        x2 = coordinates[1][0]
        y2 = coordinates[2][1]
        return x1, y1, x2, y2
