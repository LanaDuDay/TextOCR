import cv2 #type: ignore
import os
from img2table.document import Image  # type: ignore
import Config as cf

class TableHeaderRecognized:
    def __init__(self,data_text):
        self.data_text = data_text
    
    def extract_tables(self,image_path, implicit_rows=True, borderless_tables=True, min_confidence=10):
        img_from_path = Image(image_path)
        extracted_tables = img_from_path.extract_tables(
            implicit_rows=implicit_rows,
            borderless_tables=borderless_tables,
            min_confidence=min_confidence
        )
        return extracted_tables
        
    def draw_table_cells(self,image_path,extracted_tables):
        img = cv2.imread(image_path)
        table_cells = []
        for table in extracted_tables:
            for row in table.content.values():
                for cell in row:
                    table_cells.append(cell)
                    cv2.rectangle(img, (cell.bbox.x1, cell.bbox.y1), (cell.bbox.x2, cell.bbox.y2), (0, 0, 255), 2)
                    output_path = os.path.join(cf.config_table_areas_temp, f"table_area_check.png")
                    cv2.imwrite(output_path,img)
        # Convert image from BGR to RGB (matplotlib expects RGB images)
        table_img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        cv2.imshow("Table Cells", table_img_rgb)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def get_unique_coordinates(self,extracted_tables):
        if extracted_tables is None:
            raise ValueError("Tables have not been extracted yet.")
        unique_y = set()
        for _, table in enumerate(extracted_tables):
            for _, row in enumerate(table.content.values()):
                for cell in row:
                    unique_y.add(cell.bbox.y1)
                    unique_y.add(cell.bbox.y2)
                break
        return unique_y
    
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
    
    def get_header_coords(self):
        y_header_areas = []
        for file_name in os.listdir(cf.config_table_areas_temp):
            # Tạo đường dẫn đầy đủ đến hình ảnh
            image_path = os.path.join(cf.config_table_areas_temp, file_name)
            # Extract tables with custom parameters
            extracted_tables = self.extract_tables(image_path,implicit_rows=True, borderless_tables=True, min_confidence=10)
            # Draw table cells on the image
            # self.draw_table_cells(image_path,extracted_tables)
            y_coords = self.get_unique_coordinates(extracted_tables)
            y_header_areas.append([min(y_coords),max(y_coords)])
            # os.remove(image_path)
        return y_header_areas
    
    def filter_groups(self, text_boxes, y1_key, y2_key):
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
        # filtered_array = [group for group in filtered_array
        #                   if not group[0]['text'].startswith("Năm học")]
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
            column_coords = [x1_min, y1_value, x2_max, y2_value]
            result_array.append({"text": column_text, "coordinates": column_coords})
        return result_array
    
    def predict_title_value(self):
        "Hàm trả về giá trị title của bảng"
        data = self.data_text
        # Nhóm các dòng theo tọa độ x của chúng để tạo thành các cột
        y_header_areas = self.get_header_coords()
        for y_header in y_header_areas:
            y1_header,y2_header = y_header
            # Lọc các nhóm dựa trên tọa độ khóa
            filtered_array = self.filter_groups(data, y1_header, y2_header)
            column_bounds = self.calculate_column_bounds(filtered_array)
            column_bounds_adjust = self.adjust_column_bounds(column_bounds)
            result_arrays = self.key_title_table(column_bounds_adjust, y1_header, y2_header)
            return filtered_array, result_arrays
    
    def convert_coordinates(self,coordinates):
        '''Hàm để chuyển đổi tọa độ'''
        x1 = coordinates[0][0]
        y1 = coordinates[0][1]
        x2 = coordinates[1][0]
        y2 = coordinates[2][1]
        return x1, y1, x2, y2
    
# file_name = f"table_area1.png"

# # Tạo đường dẫn đầy đủ đến hình ảnh
# image_path = os.path.join(cf.config_table_areas_temp, file_name)

# # Đọc hình ảnh
# img = cv2.imread(image_path)
# extractor = TableHeaderRecognized(image_path)

# # Extract tables with custom parameters
# extracted_tables = extractor.extract_tables(implicit_rows=True, borderless_tables=True, min_confidence=10)

# # Draw table cells on the image
# extractor.draw_table_cells(extracted_tables)

# # Print unique x and y coordinates
# y_coords = extractor.get_unique_coordinates(extracted_tables)
