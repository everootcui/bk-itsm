import json
import os
import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
    QPushButton, QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt

def get_app_data_dir():
    """获取应用程序数据目录"""
    if sys.platform == 'darwin':  # macOS
        home = os.path.expanduser('~')
        return os.path.join(home, 'Library', 'Application Support', 'WorkRecordTool')
    else:  # Windows 和其他平台
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')

class BusinessDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("业务名称管理")
        self.setMinimumSize(400, 500)
        
        self.business_names = []
        self.load_business_names()
        
        self.init_ui()
        self.apply_styles()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 添加业务名称区域
        add_layout = QHBoxLayout()
        self.business_input = QLineEdit()
        self.business_input.setPlaceholderText("输入业务名称")
        add_layout.addWidget(self.business_input)
        
        add_button = QPushButton("添加")
        add_button.clicked.connect(self.add_business)
        add_layout.addWidget(add_button)
        
        layout.addLayout(add_layout)
        
        # 业务名称列表
        self.list_widget = QListWidget()
        self.update_list()
        layout.addWidget(self.list_widget)
        
        # 操作按钮区域
        button_layout = QHBoxLayout()
        
        delete_button = QPushButton("删除")
        delete_button.clicked.connect(self.delete_business)
        button_layout.addWidget(delete_button)
        
        top_button = QPushButton("置顶")
        top_button.clicked.connect(self.top_business)
        button_layout.addWidget(top_button)
        
        layout.addLayout(button_layout)
    
    def apply_styles(self):
        # 检测是否为暗黑主题
        is_dark_mode = False
        if sys.platform == 'darwin':
            # 在 Mac 上检测系统主题
            try:
                from Foundation import NSAppearance
                appearance = NSAppearance.currentAppearance()
                is_dark_mode = appearance.name().localizedString().lower().contains('dark')
            except:
                pass

        # 根据主题设置颜色
        if is_dark_mode:
            # 暗黑主题颜色
            bg_color = "#2c2c2c"
            text_color = "#ffffff"
            input_bg = "#3c3c3c"
            border_color = "#4c4c4c"
            button_bg = "#3a84ff"
            button_hover = "#2b6cd9"
            list_selected_bg = "#3a84ff"
            list_selected_text = "#ffffff"
        else:
            # 亮色主题颜色
            bg_color = "#f5f6fa"
            text_color = "#333333"
            input_bg = "#ffffff"
            border_color = "#dcdee5"
            button_bg = "#3a84ff"
            button_hover = "#2b6cd9"
            list_selected_bg = "#e1ecff"
            list_selected_text = "#3a84ff"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                color: {text_color};
            }}
            QPushButton {{
                background-color: {button_bg};
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: {button_hover};
            }}
            QLineEdit {{
                padding: 5px;
                border: 1px solid {border_color};
                border-radius: 3px;
                background-color: {input_bg};
                color: {text_color};
            }}
            QListWidget {{
                border: 1px solid {border_color};
                border-radius: 3px;
                background-color: {input_bg};
                color: {text_color};
            }}
            QListWidget::item {{
                padding: 5px;
            }}
            QListWidget::item:selected {{
                background-color: {list_selected_bg};
                color: {list_selected_text};
            }}
        """)
    
    def load_business_names(self):
        try:
            data_dir = get_app_data_dir()
            business_file = os.path.join(data_dir, "business.json")
            if os.path.exists(business_file):
                with open(business_file, "r", encoding="utf-8") as f:
                    self.business_names = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载业务名称失败: {str(e)}")
    
    def save_business_names(self):
        data_dir = get_app_data_dir()
        os.makedirs(data_dir, exist_ok=True)
        try:
            business_file = os.path.join(data_dir, "business.json")
            with open(business_file, "w", encoding="utf-8") as f:
                json.dump(self.business_names, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"保存业务名称失败: {str(e)}")
    
    def update_list(self):
        self.list_widget.clear()
        self.list_widget.addItems(self.business_names)
    
    def add_business(self):
        business = self.business_input.text().strip()
        if not business:
            QMessageBox.warning(self, "警告", "请输入业务名称")
            return
        
        if business in self.business_names:
            QMessageBox.warning(self, "警告", "该业务名称已存在")
            return
        
        self.business_names.append(business)
        self.save_business_names()
        self.update_list()
        self.business_input.clear()
    
    def delete_business(self):
        current_item = self.list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请选择要删除的业务名称")
            return
        
        business = current_item.text()
        reply = QMessageBox.question(
            self, "确认删除",
            f'确定要删除业务名称"{business}"吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.business_names.remove(business)
            self.save_business_names()
            self.update_list()
    
    def top_business(self):
        current_item = self.list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请选择要置顶的业务名称")
            return
        
        business = current_item.text()
        self.business_names.remove(business)
        self.business_names.insert(0, business)
        self.save_business_names()
        self.update_list()