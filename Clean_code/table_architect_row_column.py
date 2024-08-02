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
        for row in rows:
            row.sort(key=lambda item: item['coordinates'][0][0])
        rows_data = []
        for row in rows:
            row_dict, row_dict2 = self.process_row_json(row)
            rows_data.append(row_dict)
            if row_dict2:
                rows_data.append(row_dict2)
        # Chuyển đổi dữ liệu thành định dạng JSON
        rows_json = json.dumps(rows_data, ensure_ascii=False, indent=4)
        return rows_json

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
        columns_by_x = self.group_lines_by_x(data)
        # Lấy key_title
        table_keys_title = TableKeyTitleValue(data)
        filtered_array,result_array = table_keys_title.predict_title_value()
        # Xóa các tọa độ trùng khớp khỏi columns_by_x
        self.remove_matching_coordinates(filtered_array, columns_by_x)
        # Cập nhật văn bản với tọa độ mới
        self.update_text_with_coordinates(result_array, columns_by_x)
        # Thu thập tất cả các mục văn bản từ columns_by_x sau khi cập nhật
        all_text_items = []
        for _, data_list in columns_by_x.items():
            all_text_items.extend(data_list)
        # Phân loại các mục văn bản thành các hàng dựa trên tọa độ y với độ dung sai
        rows = self.group_by_rows(all_text_items, tolerance=cf.tolerance_row)
        return rows

    def process_row_json(self, row):
        """Xử lý một hàng để tách và chuẩn hóa dữ liệu."""
        merged_row = self.merge_texts_in_row(row)
        row_texts = [item['text'] for item in merged_row]
        row_coords = [item['coordinates'] for item in merged_row]
        row_dict, row_dict2 = {}, {}
        key_available = set()
        count = 0
        for text, _ in zip(row_texts, row_coords):
            key, value = self.split_key_value(text)
            if key in key_available:
                count = 1
            key_available.add(key)
            if value.strip():
                value = self.clean_value(value)
                if count == 0:
                    row_dict[key] = self.remove_trailing_abbreviations(value)
                else:
                    row_dict2[key] = self.remove_trailing_abbreviations(value)
        return row_dict, row_dict2

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

    def update_text_with_coordinates(self, result_array, merged_columns):
        """
        Cập nhật văn bản trong `merged_columns` dựa trên tọa độ và văn bản từ `result_array`.

        Args:
            result_array (list): Danh sách các mục chứa văn bản và tọa độ.
            merged_columns (dict): Từ điển chứa các cột với các phần tử có tọa độ.

        Returns:
            None: Hàm sửa đổi `merged_columns` và `result_array` trực tiếp.
        """
        for item in result_array:
            item_text = item['text']
            x1_item, _, x2_item, _ = item['coordinates']
            for _, data_list in merged_columns.items():
                # Tìm x1_min và x2_max trong data_list
                text_x1_min = float('inf')  # Khởi tạo x1_min với giá trị lớn nhất có thể
                text_x2_max = float('-inf') # Khởi tạo x2_max với giá trị nhỏ nhất có thể
                for text_item in data_list:
                    text_x1, _, text_x2, _ = self.convert_coordinates(text_item['coordinates'])
                    text_x1_min = min(text_x1_min, text_x1)
                    text_x2_max = max(text_x2_max, text_x2)
                # Cập nhật văn bản nếu tọa độ trùng khớp
                for text_item in data_list:
                    text_x1, _, text_x2, _ = self.convert_coordinates(
                        text_item['coordinates'])
                    if (x1_item <= text_x1_min <= x2_item) or (x1_item <= text_x2_max <= x2_item) or (text_x1_min <= x1_item <= text_x2_max) or (text_x1_min <= x2_item <= text_x2_max):
                        if ":::" not in text_item['text']:
                            text_item['text'] = f"{item_text} ::: {text_item['text']}"

    def merge_texts_in_row(self, row):
        '''Hàm trích key_value theo hàng'''
        merged_row = []
        skip_indices = set()
        for i, current_item in enumerate(row):
            if i in skip_indices:
                continue
            merged_text = current_item['text']
            current_coords = current_item['coordinates']
            current_x1, current_y1, current_x2, _ = self.convert_coordinates(current_coords)
            for j, next_item in enumerate(row[i + 1:], start=i + 1):
                if j in skip_indices:
                    continue
                next_coords = next_item['coordinates']
                next_x1, next_y1, next_x2, _ = self.convert_coordinates(next_coords)
                if (current_x1 <= next_x1 <= current_x2) or (current_x1 <= next_x2 <= current_x2) or (next_x1 <= current_x1 <= next_x2) or (next_x1 <= current_x2 <= next_x2):
                    if current_y1 < next_y1:
                        merged_text += " " + (next_item['text'].split(":::")[1] if "::: "
                                              in next_item['text'] else next_item['text'])
                    else:
                        merged_text = (next_item['text'].split(":::")[1] if "::: " in
                                       next_item['text'] else next_item['text']) + " " + merged_text
                    skip_indices.add(j)
            merged_row.append({"text": merged_text, "coordinates": current_coords})
        return merged_row

    def split_key_value(self, text):
        """Tách key và value từ một chuỗi văn bản."""
        parts = text.split(' ::: ', 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return parts[0], ""

    def remove_trailing_abbreviations(self,text):
        '''Biểu thức chính quy tìm các từ thừa khi chúng xuất hiện riêng lẻ ở cuối câu'''
        pattern = r'\b(th|tr|ch|thuy|Ly|Thu|la|thu)\b\s*$'
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

    def get_y_coordinate(self,item):
        '''Hàm lấy tọa độ y đầu tiên của Text'''
        return item['coordinates'][0][1]

    def convert_coordinates(self,coordinates):
        '''Hàm để chuyển đổi tọa độ'''
        x1 = coordinates[0][0]
        y1 = coordinates[0][1]
        x2 = coordinates[1][0]
        y2 = coordinates[2][1]
        return x1, y1, x2, y2
