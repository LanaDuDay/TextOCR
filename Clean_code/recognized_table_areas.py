"""
Module: recognized_table_areas
Mô tả:
    Xử lý và nhận diện các vùng bảng từ layout tài liệu.  
"""
import layoutparser as lp #type: ignore
import Config as cf

class TableAreaDetector:
    """
    Xác định các vùng bảng trong ảnh tài liệu.
    """
    def __init__(self, filename):
        self.filename = filename

    def setup_layout_model(self):
        """
        Thiết lập mô hình nhận diện bảng.
        """
        return lp.PaddleDetectionLayoutModel(
            config_path = cf.config_table_detect_path,
            threshold=0.5,
            label_map = {0: "Table"},
            enforce_cpu=True,
            batch_size=4
        )

    def detect_layout(self, image):
        """
        Trả về giá trị tọa độ của bảng.
        """
        return self.setup_layout_model().detect(image)

    def compute_table_area(self, layout):
        """
        Trả về tọa độ bảng được làm tròn
        """
        x_1, y_1, x_2, y_2 = 0, 0, 0, 0
        table_areas = []
        for l in layout:
            if l.type == 'Table':
                x_1 = max(int(l.block.x_1) - 4, 0)
                y_1 = max(int(l.block.y_1) - 2, 0)
                x_2 = int(l.block.x_2) + 4
                y_2 = int(l.block.y_2) + 2
                table_areas.append((x_1, y_1, x_2, y_2))
        return table_areas

    def table_areas(self, image):
        """
        Trả về từ điển(dictionary) chứa tọa độ bảng của ảnh.
        """
        table_areas_dict = {}
        if self.filename.startswith('page') and self.filename.endswith('.jpg'):
            layout = self.detect_layout(image)
            table_areas = self.compute_table_area(layout)
            table_areas_dict[self.filename] = table_areas
            print(f"Đã lưu các vùng bảng cho {self.filename}")
        return table_areas_dict
