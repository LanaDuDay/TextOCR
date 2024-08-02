"""
Module: table_column_row_process
Mô tả:
    Đầu vào là data_text là một list và mỗi phần tử của data_text chứa các 
    2 phần tử text và tọa độ text trong ảnh.
    Đầu ra là tọa độ Key_value cho từng dòng trong bảng.
"""
import unicodedata
import Config as cf

class TableKeyTitleValue:
    """
    Mô tả:
    -   Đầu vào là data_text là một list và mỗi phần tử của data_text chứa các 
        2 phần tử text và tọa độ text trong ảnh.
    -   Phân các text theo các hàng các cột:
            group_lines_by_x(): Phân loại thành các cột
            filter_groups(): Tìm các key được phân loại theo cột
            calculate_column_bounds(): Từ filter_groups() sẽ tổng
                        hợp lại các key(In hoa, Shift_,Lọc các kí tự đặc biệt)
    -   Đầu ra là mảng result_array chứa các key title value cho bảng.
    """
    def __init__(self, data_text):
        self.data_text = data_text

    def is_in_table(self,coordinates, table):
        """
        Hàm để kiểm tra tọa độ có nằm trong vùng table hay không
        """
        xmin, ymin, xmax, ymax = table
        x_coords = [coord[0] for coord in coordinates]
        y_coords = [coord[1] for coord in coordinates]
        return all(xmin <= x <= xmax and ymin <= y <= ymax for x, y in zip(x_coords, y_coords))

    def convert_coordinates(self,coordinates):
        '''Hàm để chuyển đổi tọa độ'''
        x1 = coordinates[0][0]
        y1 = coordinates[0][1]
        x2 = coordinates[1][0]
        y2 = coordinates[2][1]
        return x1, y1, x2, y2

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

    def find_key_array(self, merged_columns):
        '''Hàm trả về tọa độ y của vùng chứa title'''
        key_array = []
        key_x1, key_y1, key_x2, key_y2 = 0, 0, 0, 0
        first_stt_text = 0
        # Find key area
        for _, text_data_list in merged_columns.items():
            if text_data_list[0]['text'] in ['stt', 'TT', 'STT']:
                key_array.append(text_data_list[0])
                key_x1, key_y1, key_x2, key_y2 = (
                    self.convert_coordinates(key_array[0]['coordinates'])
                )
                if len(text_data_list) > 1:
                    first_stt_text = text_data_list[1]['text']
                    key_array.append(text_data_list[1])
                else:
                    key_array = (
                        self.find_overlapping_keys(key_x1, key_x2, merged_columns, text_data_list)
                    )
                break
        # If no key area found, use the first available text data
        if not key_array:
            for _, text_data_list in merged_columns.items():
                key_array.append(text_data_list[0])
                key_x1, key_y1, key_x2, key_y2 = (
                    self.convert_coordinates(key_array[0]['coordinates'])
                )
                if len(text_data_list) > 1:
                    key_array.append(text_data_list[1])
                else:
                    key_array = (
                        self.find_overlapping_keys(key_x1, key_x2, merged_columns, text_data_list)
                    )
                break
        return key_array, first_stt_text, key_x1, key_y1, key_x2, key_y2

    def find_overlapping_keys(self,x1, x2, merged_columns, current_data_list):
        '''Xử lí các row dạng merged cell'''
        for _, data_list_other in merged_columns.items():
            if data_list_other[0]['text'] != current_data_list[0]['text']:
                x1_dl, _, x2_dl, _ = self.convert_coordinates(data_list_other[0]['coordinates'])
                if x1_dl <= x1 < x2_dl or x1 <= x2_dl <= x2:
                    return [current_data_list[0], data_list_other[0]]
        return [current_data_list[0]]

    def calculate_distance(self, y1_next, y2, stt_first):
        '''Tinh vùng chứa tiêu đề của bảng'''
        if int(stt_first) > 1:
            return abs(y1_next - y2) * (0.6 / int(stt_first))
        return abs(y1_next - y2) * 0.7

    def filter_groups(self, text_boxes, y1_key, y2_key, _):
        '''Lấy giá trị key title của table chính là các text nằm trong vùng title 
            đã được xác định'''
        # Group lines by x coordinates
        merged_columns = self.group_lines_by_x(text_boxes)
        filtered_array = []
        # Process each group of text boxes
        for _, data_list in merged_columns.items():
            for item in data_list:
                x1_item, y1_item, _, _ = self.convert_coordinates(item['coordinates'])
                if y1_key <= y1_item <= y2_key:
                    found_group = False
                    for group in filtered_array:
                        group_x = group[0]['coordinates'][0][0]
                        if abs(group_x - x1_item) <= cf.tolerance_column_key:  # Tolerance for keys
                            group.append({"text": item['text'], "coordinates": item['coordinates']})
                            found_group = True
                            break
                    if not found_group:
                        filtered_array.append([{"text": item['text'],
                                                "coordinates": item['coordinates']}])
        # Filter out items based on y1_next
        # filtered_array = [group for group in filtered_array if
        #                   all(item['coordinates'][2][1] < y1_next - 1 for item in group)]
        # Remove groups where the first text starts with "Năm học"
        filtered_array = [group for group in filtered_array
                          if not group[0]['text'].startswith("Năm học")]
        return filtered_array

    def calculate_column_bounds(self, filtered_array):
        '''Trả về column_bounds là các tọa độ cột đã được xử lý'''
        column_bounds = []
        # Tính toán tọa độ các cột
        for group in filtered_array:
            x1_min = min(item['coordinates'][0][0] for item in group)
            x2_max = max(item['coordinates'][2][0] for item in group)
            column_bounds.append((x1_min, x2_max, group))
        # Sắp xếp các cột theo x1_min
        column_bounds.sort(key=lambda x: x[0])
        return column_bounds

    def adjust_column_bounds(self, column_bounds):
        '''Điều chỉnh tọa độ cột và phân phối các mục giữa các cột'''
        for i in range(len(column_bounds) - 1):
            x1_min_current, x2_max_current, group_current = column_bounds[i]
            x1_min_next, _, group_next = column_bounds[i + 1]
            if x1_min_current <= x1_min_next < x2_max_current:
                x2_max_current = x1_min_next - 1
                column_bounds[i] = (x1_min_current, x2_max_current, group_current)
            for item in group_current:
                _, _, x2_item, _ = self.convert_coordinates(item['coordinates'])
                if x2_item > x1_min_next:
                    group_next.append(item)
        return column_bounds

    def key_title_table(self, column_bounds, y1_value, y2_value):
        '''Xây dựng mảng kết quả với văn bản đã được sắp xếp'''
        result_array = []
        for x1_min, x2_max, group in column_bounds:
            group.sort(key=lambda item: item['coordinates'][0][1])
            column_text = " ".join(item['text'] for item in group)
            column_text = self.remove_accents(column_text)
            column_coords = [x1_min, y1_value, x2_max, y2_value]
            result_array.append({"text": column_text, "coordinates": column_coords})
            self.key_format_text(result_array)
        return result_array

    def key_format_text(self, result_array):
        '''Hàm loại bỏ một số kí tự đặc biệt trong key'''
        for item in result_array:
            text = item['text']
            text_no_accents = self.remove_accents(text)
            text_upper = text_no_accents.upper()
            text_final = text_upper.replace(' ', '_').replace('?', '')
            item['text'] = text_final

    def remove_accents(self, input_str):
        '''Hàm để Fommat lại key dạng SHIFT_, in hoa và không dấu'''
        # Chuyển chuỗi về dạng chuẩn NFKD
        nfkd_form = unicodedata.normalize('NFKD', input_str)
        # Loại bỏ các ký tự kết hợp (combining characters) để giữ lại các ký tự cơ bản
        normalized_str = ''.join([c for c in nfkd_form if not unicodedata.combining(c)])
        # Chuyển tất cả các ký tự thành chữ hoa
        return normalized_str.upper().replace("Đ","D")

    def predict_title_value(self):
        "Hàm trả về giá trị title của bảng"
        data = self.data_text
        # Nhóm các dòng theo tọa độ x của chúng để tạo thành các cột
        columns_by_x = self.group_lines_by_x(data)
        # Tìm mảng khóa và tọa độ của nó
        key_array_moc, stt_first, _, y1, _, y2 = self.find_key_array(columns_by_x)
        # Chuyển đổi tọa độ và tính khoảng cách đến khóa tiếp theo
        _, y1_next, _, _ = self.convert_coordinates(key_array_moc[1]['coordinates'])
        distance_to_next = self.calculate_distance(y1_next, y2, stt_first)
        y1_key = max(y1 - 40, 0)
        y2_key = y2 + distance_to_next
        # Lọc các nhóm dựa trên tọa độ khóa
        filtered_array = self.filter_groups(self.data_text, y1_key, y2_key, y1_next)
        column_bounds = self.calculate_column_bounds(filtered_array)
        column_bounds_adjust = self.adjust_column_bounds(column_bounds)
        result_arrays = self.key_title_table(column_bounds_adjust, y1_key, y2_key)
        return filtered_array, result_arrays
