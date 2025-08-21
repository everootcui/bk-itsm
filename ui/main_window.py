import os
import json
import sys
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QCompleter,
    QComboBox, QGridLayout, QSizePolicy, QSpacerItem,
    QHeaderView, QApplication, QDateEdit
)
from PySide6.QtCore import Qt, QStringListModel, QSize, QCoreApplication, QDate
from PySide6.QtGui import QColor, QFont, QIcon
from .business_dialog import BusinessDialog

def get_app_data_dir():
    """获取应用程序数据目录"""
    if sys.platform == 'darwin':  # macOS
        home = os.path.expanduser('~')
        return os.path.join(home, 'Library', 'Application Support', 'WorkRecordTool')
    else:  # Windows 和其他平台
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("工作记录工具")
        self.setMinimumSize(800, 700)

        # 设置窗口图标
        try:
            app_path = QCoreApplication.applicationFilePath()
            app_dir = os.path.dirname(app_path)
            # 在 Mac 上，图标文件可能在 Resources 目录下
            if sys.platform == 'darwin':
                icon_path = os.path.join(app_dir, 'Resources', 'favicon.icns')
                if not os.path.exists(icon_path):
                    icon_path = os.path.join(app_dir, 'favicon.icns')
            else:
                icon_path = os.path.join(app_dir, '_internal', 'favicon.ico')
                if not os.path.exists(icon_path):
                    icon_path = 'favicon.ico'
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            pass

        # 初始化数据
        self.records = []
        self.business_names = []
        self.data_dir = get_app_data_dir()

        # 创建主窗口部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(20, 20, 20, 20)

        # 创建输入区域 (移到加载数据之前)
        self.create_input_area()

        # 初始化数据 (移到创建输入区域之后)
        self.load_data()

        # 创建今日记录标签
        today_records_label = QLabel("今日记录")
        today_records_label.setObjectName("sectionLabel")

        # 添加一个容器用于放置今日记录标签和排序按钮
        today_records_container = QWidget()
        today_records_layout = QHBoxLayout(today_records_container)
        today_records_layout.setContentsMargins(0, 0, 0, 0)
        today_records_layout.addWidget(today_records_label, alignment=Qt.AlignBottom)

        # 创建业务排序按钮
        self.sort_business_button = QPushButton("业务排序 (升序)") # 初始状态
        self.sort_business_button.setMaximumWidth(120) # 限制按钮宽度
        self.sort_business_button.setCheckable(True) # Make it checkable to toggle sort order
        self.sort_business_button.setChecked(False) # Start with ascending
        self.sort_business_button.clicked.connect(self.sort_records_by_business)
        today_records_layout.addWidget(self.sort_business_button, alignment=Qt.AlignBottom)
        today_records_layout.addStretch() # 将按钮推到左边，占满剩余空间

        self.layout.addWidget(today_records_container)

        # 创建表格
        self.create_table()

        # 创建统计信息标签
        stats_label = QLabel("统计信息")
        stats_label.setObjectName("sectionLabel")
        self.layout.addWidget(stats_label)

        # 创建统计区域
        self.create_stats_area()

        # 创建操作按钮区域
        self.create_action_buttons_area()

        # 应用样式
        self.apply_styles()

        # 设置回车键触发添加记录
        self.manual_time_input.returnPressed.connect(self.add_record)

        # 初始化表格和统计信息
        self.update_table()
        self.update_stats()

    def create_input_area(self):
        # 创建输入区域容器
        input_container = QWidget()
        input_container.setObjectName("inputContainer")
        input_layout = QGridLayout(input_container)
        input_layout.setSpacing(10)
        input_layout.setContentsMargins(15, 10, 15, 15)

        # 添加新记录标签
        new_record_label = QLabel("添加新记录")
        new_record_label.setObjectName("sectionLabel")
        input_layout.addWidget(new_record_label, 0, 0, 1, 5)

        label_font = QFont()
        label_font.setPointSize(10)

        # 业务名称
        business_label = QLabel("业务名称:")
        business_label.setFont(label_font)
        self.business_combo = QComboBox()
        self.business_combo.setEditable(True)
        self.business_combo.setMinimumWidth(250)
        self.business_combo.setMinimumHeight(28)
        self.business_combo.setPlaceholderText("选择或输入业务名称")
        self.update_business_combo()
        self.add_button = QPushButton("添加记录")
        self.add_button.setMinimumHeight(28)
        self.add_button.setMaximumWidth(80)
        self.add_button.clicked.connect(self.add_record)

        input_layout.addWidget(business_label, 1, 0, alignment=Qt.AlignRight | Qt.AlignVCenter)
        input_layout.addWidget(self.business_combo, 1, 1)
        input_layout.addWidget(self.add_button, 1, 4)
        input_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 1, 5)

        # 提单时间
        date_label = QLabel("提单时间:")
        date_label.setFont(label_font)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setMinimumHeight(28)
        self.date_edit.setMaximumWidth(120)
        input_layout.addWidget(date_label, 1, 2, alignment=Qt.AlignRight | Qt.AlignVCenter)
        input_layout.addWidget(self.date_edit, 1, 3)

        # 任务描述和耗时输入在同一行，并与上一行对齐
        task_label = QLabel("任务描述:")
        task_label.setFont(label_font)
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("输入任务描述")
        self.task_input.setMinimumHeight(28)

        manual_time_label = QLabel("耗时(小时):")
        manual_time_label.setFont(label_font)
        self.manual_time_input = QLineEdit()
        self.manual_time_input.setPlaceholderText("输入")
        self.manual_time_input.setMinimumHeight(28)
        self.manual_time_input.setMaximumWidth(80)

        self.increase_time_button = QPushButton("+")
        self.increase_time_button.setFixedSize(28, 28)
        self.increase_time_button.setObjectName("timeControlButton")
        self.decrease_time_button = QPushButton("-")
        self.decrease_time_button.setFixedSize(28, 28)
        self.decrease_time_button.setObjectName("timeControlButton")
        self.increase_time_button.clicked.connect(self.increase_time)
        self.decrease_time_button.clicked.connect(self.decrease_time)

        input_layout.addWidget(task_label, 2, 0, alignment=Qt.AlignRight | Qt.AlignVCenter)
        input_layout.addWidget(self.task_input, 2, 1, 1, 1)
        input_layout.addWidget(manual_time_label, 2, 2, alignment=Qt.AlignRight | Qt.AlignVCenter)
        time_input_buttons_layout = QHBoxLayout()
        time_input_buttons_layout.setContentsMargins(0, 0, 0, 0)
        time_input_buttons_layout.setSpacing(5)
        time_input_buttons_layout.addWidget(self.manual_time_input)
        time_input_buttons_layout.addWidget(self.increase_time_button)
        time_input_buttons_layout.addWidget(self.decrease_time_button)
        input_layout.addLayout(time_input_buttons_layout, 2, 3, 1, 3)

        input_layout.setColumnStretch(1, 2)
        input_layout.setColumnStretch(3, 1)
        input_layout.setColumnStretch(4, 0)
        input_layout.setColumnStretch(5, 0)
        input_layout.setColumnStretch(0, 0)
        input_layout.setColumnStretch(2, 0)
        input_layout.setColumnStretch(6, 0)

        self.layout.addWidget(input_container)

    def update_business_combo(self):
        self.business_combo.clear()
        # 根据截图，业务名称下拉框显示所有业务名称，不区分是否在记录中使用
        self.business_combo.addItems(self.business_names)


    def create_table(self):
        # 5列：业务、提单时间、任务、耗时、操作
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["业务", "提单时间", "任务", "耗时", "操作"])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 业务名称
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 提单时间
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # 任务描述
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 耗时
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # 操作
        header.resizeSection(4, 70)
        header.setMinimumSectionSize(80)

        self.table.setAlternatingRowColors(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dcdee5;
                border-radius: 5px;
                background-color: white;
                gridline-color: transparent;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #f0f1f5;
                background-color: white;
            }
            QTableWidget::item:selected {
                background-color: #e1ecff;
                color: #3a84ff;
                border: 1px solid #3a84ff;
            }
            QTableWidget QLineEdit,
            QTableWidget QComboBox {
                border: 1px solid #3a84ff;
                padding: 0 4px;
                background: white;
                font-size: 11px;
                border-radius: 3px;
            }
            QTableWidget QLineEdit:focus,
            QTableWidget QComboBox:focus {
                border-color: #2b6cd9;
            }
            QComboBox::drop-down {
                width: 20px;
            }
            QComboBox::down-arrow {
            }
            QHeaderView::section {
                background-color: #f5f6fa;
                padding: 5px;
                border: none;
                border-bottom: 1px solid #dcdee5;
                font-weight: bold;
                font-size: 11px;
            }
            QLabel {
                color: #63656e;
                font-size: 11px;
            }
        """)
        self.table.itemChanged.connect(self.on_table_item_changed)
        self.layout.addWidget(self.table)

    def create_stats_area(self):
        stats_container = QWidget()
        stats_container.setObjectName("statsContainer")
        stats_layout = QHBoxLayout(stats_container)
        stats_layout.setSpacing(40) # 增加统计信息之间的间距
        stats_layout.setContentsMargins(20, 15, 20, 15) # 调整统计区域的内边距

        # 设置统计标签样式
        stats_font = QFont()
        stats_font.setPointSize(10)
        stats_font.setBold(True)

        self.manual_time_total = QLabel("总耗时: 0小时")
        # 将"今日总记录数"改为"总记录单量"
        self.records_today = QLabel("总记录单量: 0条")

        for label in [self.manual_time_total, self.records_today]:
            label.setFont(stats_font)

        # 添加伸展空间以使标签居中
        stats_layout.addStretch()
        stats_layout.addWidget(self.manual_time_total)
        stats_layout.addStretch() # 在两者之间添加伸展空间
        stats_layout.addWidget(self.records_today)
        stats_layout.addStretch()

        self.layout.addWidget(stats_container)

    def create_action_buttons_area(self):
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(15) # 增加按钮之间的间距

        self.manage_button = QPushButton("管理业务")
        self.generate_text_button = QPushButton("生成文本")
        self.clear_records_button = QPushButton("清空记录")

        self.manage_button.clicked.connect(self.show_business_dialog)
        self.generate_text_button.clicked.connect(self.generate_record_text)
        self.clear_records_button.clicked.connect(self.clear_all_records)

        # 设置清空按钮的object name以便应用特定样式
        self.clear_records_button.setObjectName("clear_records_button")

        # 调整按钮大小和间距，并按照截图顺序排列
        button_height = 30 # 调整按钮高度

        button_layout.addWidget(self.manage_button)
        button_layout.addWidget(self.generate_text_button)
        button_layout.addWidget(self.clear_records_button)

        for button in [self.manage_button, self.generate_text_button, self.clear_records_button]:
            button.setMinimumHeight(button_height)
            # 移除固定宽度设置，使用Expanding策略填充宽度
            # button.setFixedWidth(button_width)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 移除stretch，让按钮均匀分布
        # button_layout.addStretch()

        self.layout.addWidget(button_container)

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
            header_bg = "#363636"
            hover_color = "#4a4a4a"
            button_bg = "#3a84ff"
            button_hover = "#2b6cd9"
            button_pressed = "#0052cc"
            clear_button_bg = "#ea3636"
            clear_button_hover = "#c42b2b"
            clear_button_pressed = "#a12121"
            table_selected_bg = "#3a84ff"
            table_selected_text = "#ffffff"
            table_alternate_bg = "#323232"
        else:
            # 亮色主题颜色（保持原有颜色）
            bg_color = "#f5f6fa"
            text_color = "#333333"
            input_bg = "#ffffff"
            border_color = "#dcdee5"
            header_bg = "#f5f6fa"
            hover_color = "#e1ecff"
            button_bg = "#3a84ff"
            button_hover = "#2b6cd9"
            button_pressed = "#0052cc"
            clear_button_bg = "#ea3636"
            clear_button_hover = "#c42b2b"
            clear_button_pressed = "#a12121"
            table_selected_bg = "#e1ecff"
            table_selected_text = "#3a84ff"
            table_alternate_bg = "#ffffff"

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {bg_color};
                color: {text_color};
            }}
            #sectionLabel {{
                font-size: 14px;
                font-weight: bold;
                color: {text_color};
                margin-top: 10px;
                margin-bottom: 5px;
            }}
            #inputContainer,
            #statsContainer {{
                background-color: {input_bg};
                border-radius: 5px;
            }}
            QPushButton {{
                background-color: {button_bg};
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {button_hover};
            }}
            QPushButton:pressed {{
                background-color: {button_pressed};
            }}
            QPushButton#clear_records_button {{
                background-color: {clear_button_bg};
            }}
            QPushButton#clear_records_button:hover {{
                background-color: {clear_button_hover};
            }}
            QPushButton#clear_records_button:pressed {{
                background-color: {clear_button_pressed};
            }}
            QLineEdit, QComboBox {{
                padding: 5px 10px;
                border: 1px solid {border_color};
                border-radius: 3px;
                background-color: {input_bg};
                color: {text_color};
                font-size: 11px;
            }}
            QLineEdit:focus, QComboBox:focus {{
                border-color: {button_bg};
            }}
            QComboBox::drop-down {{
                width: 20px;
            }}
            QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
            }}
            QComboBox QAbstractItemView {{
                border: 1px solid {border_color};
                background-color: {input_bg};
                color: {text_color};
                selection-background-color: {hover_color};
                selection-color: {button_bg};
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                min-height: 25px;
                padding: 5px;
                font-size: 14px;
            }}
            QPushButton#timeControlButton {{
                background-color: {input_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 3px;
                padding: 2px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton#timeControlButton:hover {{
                background-color: {hover_color};
                border-color: {button_bg};
            }}
            QPushButton#timeControlButton:pressed {{
                background-color: {button_bg};
                color: white;
            }}
            QTableWidget {{
                border: 1px solid {border_color};
                border-radius: 5px;
                background-color: {input_bg};
                color: {text_color};
                gridline-color: transparent;
            }}
            QTableWidget::item {{
                padding: 5px;
                border-bottom: 1px solid {border_color};
                background-color: {input_bg};
            }}
            QTableWidget::item:selected {{
                background-color: {table_selected_bg};
                color: {table_selected_text};
                border: 1px solid {button_bg};
            }}
            QTableWidget QLineEdit,
            QTableWidget QComboBox {{
                border: 1px solid {button_bg};
                padding: 0 4px;
                background: {input_bg};
                color: {text_color};
                font-size: 11px;
                border-radius: 3px;
            }}
            QTableWidget QLineEdit:focus,
            QTableWidget QComboBox:focus {{
                border-color: {button_hover};
            }}
            QHeaderView::section {{
                background-color: {header_bg};
                padding: 5px;
                border: none;
                border-bottom: 1px solid {border_color};
                font-weight: bold;
                font-size: 11px;
                color: {text_color};
            }}
            QLabel {{
                color: {text_color};
                font-size: 11px;
            }}
        """)

    def update_business_combo(self):
        self.business_combo.clear()
        # 根据截图，业务名称下拉框显示所有业务名称，不区分是否在记录中使用
        self.business_combo.addItems(self.business_names)


    def add_record(self):
        business = self.business_combo.currentText().strip()
        task = self.task_input.text().strip()
        manual_time = self.manual_time_input.text().strip()
        submit_date = self.date_edit.date().toString("yyyy-MM-dd")

        if not all([business, task, manual_time, submit_date]):
            QMessageBox.warning(self, "警告", "请填写所有字段")
            return

        # 验证任务描述长度
        if len(task) < 10:
            QMessageBox.warning(self, "警告", "任务描述至少需要10个字符")
            return

        try:
            manual_time = float(manual_time)
        except ValueError:
            QMessageBox.warning(self, "警告", "耗时必须是数字")
            return

        record = {
            "business": business,
            "task": task,
            "manual_time": manual_time,
            "submit_date": submit_date,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        self.records.append(record)

        if business and business not in self.business_names:
            self.business_names.append(business)
            self.save_business_names()
            self.update_business_combo()

        self.save_data()
        self.update_table()
        self.update_stats()
        self.clear_inputs()

    def update_table(self):
        records_to_show = getattr(self, 'filtered_records', None) or self.records
        self.table.setRowCount(len(records_to_show))
        for i, record in enumerate(reversed(records_to_show)):
            self.table.setItem(i, 0, QTableWidgetItem(record["business"]))
            date_str = record.get("submit_date", "")
            date_fmt = date_str.replace("-", "") if date_str else ""
            self.table.setItem(i, 1, QTableWidgetItem(date_fmt))
            self.table.setItem(i, 2, QTableWidgetItem(record["task"]))
            self.table.setItem(i, 3, QTableWidgetItem(str(record["manual_time"])))
            delete_btn = QPushButton("删除")
            delete_btn.setFixedSize(60, 24)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ea3636;
                    color: white;
                    border: none;
                    padding: 2px;
                    border-radius: 3px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #c42b2b;
                }
                QPushButton:pressed {
                    background-color: #a12121;
                }
            """)
            # 直接传递当前表格行号i
            delete_btn.clicked.connect(lambda checked, row=i: self.delete_record(row))
            self.table.setCellWidget(i, 4, delete_btn)
        self.table.resizeRowsToContents()


    def update_stats(self):
        manual_total = sum(r["manual_time"] for r in self.records) if self.records else 0
        # 修改统计逻辑为总记录单量
        total_records_count = len(self.records)

        self.manual_time_total.setText(f"总耗时: {manual_total:.1f}小时")
        # 更新标签文本
        self.records_today.setText(f"总记录单量: {total_records_count}条")

    def clear_inputs(self):
        self.task_input.clear()
        self.manual_time_input.clear()
        self.business_combo.setFocus()
        # 不再自动重置日期选择器

    # 添加增加耗时的方法
    def increase_time(self):
        try:
            current_time = float(self.manual_time_input.text()) if self.manual_time_input.text() else 0.0
            self.manual_time_input.setText(f"{current_time + 0.5:.1f}")
        except ValueError:
            QMessageBox.warning(self, "警告", "耗时输入无效")

    # 添加减少耗时的方法
    def decrease_time(self):
        try:
            current_time = float(self.manual_time_input.text()) if self.manual_time_input.text() else 0.0
            new_time = max(0.0, current_time - 0.5)
            self.manual_time_input.setText(f"{new_time:.1f}")
        except ValueError:
            QMessageBox.warning(self, "警告", "耗时输入无效")

    def delete_record(self, row):
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除这条记录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            records_to_show = getattr(self, 'filtered_records', None) or self.records
            # 表格是倒序显示的，所以要反向取
            record = list(reversed(records_to_show))[row]
            if record in self.records:
                self.records.remove(record)
                self.save_data()
                self.update_table()
                self.update_stats()
            else:
                QMessageBox.warning(self, "错误", "删除记录失败，未找到对应数据。")

    def load_public_businesses(self):
        """加载公共业务名称列表"""
        public_businesses = []
        try:
            public_file = os.path.join(self.data_dir, "public.ini")
            if os.path.exists(public_file):
                with open(public_file, "r", encoding="utf-8") as f:
                    public_businesses = [line.strip() for line in f.readlines() if line.strip()]
        except Exception as e:
            print(f"加载公共业务文件失败: {str(e)}")
        return public_businesses

    def generate_record_text(self):
        # 根据需求生成文本格式，分为公共记录单和批量创建记录单
        if not self.records:
            QMessageBox.information(self, "提示", "没有记录可以生成文本")
            return

        # 加载公共业务名称
        public_businesses = self.load_public_businesses()
        
        # 分类记录
        public_records = []
        normal_records = []
        
        records_to_show = getattr(self, 'filtered_records', None) or self.records
        for record in reversed(records_to_show):
            business_name = record.get("business", "")
            # 检查是否为公共业务
            is_public = any(public_business in business_name for public_business in public_businesses)
            
            if is_public:
                public_records.append(record)
            else:
                normal_records.append(record)

        # 生成文本
        text = ""
        
        # 批量创建记录单
        if normal_records:
            text += "小鲸 批量创建记录单\n"
            for record in normal_records:
                date_fmt = record.get("submit_date", "").replace("-", "") if record.get("submit_date") else ""
                text += f"{record['business']} {date_fmt} {record['task']} {record['manual_time']:.1f}\n"
            text += "\n"
        
        # 公共记录单
        if public_records:
            text += "小鲸 公共记录单\n"
            for record in public_records:
                date_fmt = record.get("submit_date", "").replace("-", "") if record.get("submit_date") else ""
                text += f"{record['business']} {date_fmt} {record['task']} {record['manual_time']:.1f}\n"

        clipboard = QApplication.clipboard()
        clipboard.setText(text.strip())
        QMessageBox.information(self, "提示", "记录文本已复制到剪贴板")

    def clear_all_records(self):
        if not self.records:
            QMessageBox.information(self, "提示", "没有记录可以清空")
            return

        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有记录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.records = []
            self.save_data()
            self.update_table()
            self.update_stats()
            QMessageBox.information(self, "提示", "所有记录已清空")

    def load_data(self):
        try:
            if os.path.exists(os.path.join(self.data_dir, "records.json")):
                with open(os.path.join(self.data_dir, "records.json"), "r", encoding="utf-8") as f:
                    self.records = json.load(f)
                # 兼容老数据：无submit_date时补充为当前日期
                for r in self.records:
                    if "submit_date" not in r:
                        r["submit_date"] = datetime.now().strftime("%Y-%m-%d")
            if os.path.exists(os.path.join(self.data_dir, "business.json")):
                with open(os.path.join(self.data_dir, "business.json"), "r", encoding="utf-8") as f:
                    self.business_names = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载数据失败: {str(e)}")
        self.update_business_combo()

    def save_data(self):
        os.makedirs(self.data_dir, exist_ok=True)
        try:
            with open(os.path.join(self.data_dir, "records.json"), "w", encoding="utf-8") as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"保存数据失败: {str(e)}")

    def save_business_names(self):
        os.makedirs(self.data_dir, exist_ok=True)
        try:
            with open(os.path.join(self.data_dir, "business.json"), "w", encoding="utf-8") as f:
                json.dump(self.business_names, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"保存业务名称失败: {str(e)}")

    def show_business_dialog(self):
        dialog = BusinessDialog(self)
        # 业务名称管理对话框执行后，重新加载并更新业务名称下拉框
        dialog.exec() # 运行对话框，等待关闭
        # 对话框关闭后，无论如何都重新加载并更新业务名称下拉框
        self.load_business_names()
        self.update_business_combo()

    # 添加从文件重新加载业务名称的方法 (仅用于对话框修改后刷新)
    def load_business_names(self):
        try:
            if os.path.exists(os.path.join(self.data_dir, "business.json")):
                with open(os.path.join(self.data_dir, "business.json"), "r", encoding="utf-8") as f:
                    self.business_names = json.load(f)
        except Exception as e:
             QMessageBox.warning(self, "警告", f"重新加载业务名称失败: {str(e)}")

    # 添加处理表格单元格编辑完成后的方法
    def on_table_item_changed(self, item):
        if item is None:
            return
        row = item.row()
        col = item.column()
        new_value = item.text().strip()
        # 只允许编辑业务、提单时间、任务、耗时
        field = None
        if col == 0:
            field = "business"
        elif col == 1:
            field = "submit_date"
        elif col == 2:
            field = "task"
        elif col == 3:
            field = "manual_time"
        else:
            return
        if field == "manual_time":
            try:
                new_value = float(new_value)
            except ValueError:
                QMessageBox.warning(self, "警告", "耗时必须是数字")
                self.update_table()
                return
        elif field == "task":
            # 验证任务描述长度
            if len(new_value) < 10:
                QMessageBox.warning(self, "警告", "任务描述至少需要10个字符")
                self.update_table()
                return
        # 找到原始 records 列表中对应的记录 (考虑倒序显示)
        records_to_show = getattr(self, 'filtered_records', None) or self.records
        original_index = len(records_to_show) - 1 - row
        if 0 <= original_index < len(records_to_show):
            # 找到原始数据在 self.records 中的索引
            record = records_to_show[original_index]
            # 需要同步修改 self.records
            idx_in_all = self.records.index(record)
            self.records[idx_in_all][field] = new_value
            if field == "business" and new_value not in self.business_names:
                self.business_names.append(new_value)
                self.save_business_names()
                self.update_business_combo()
            self.save_data()
            self.update_stats()
        else:
            QMessageBox.warning(self, "错误", "更新记录失败，索引超出范围。")
            self.update_table()

    # 添加业务排序方法
    def sort_records_by_business(self):
        is_ascending = not self.sort_business_button.isChecked()
        # 使用 lambda 函数作为 key，按业务名称排序
        self.records.sort(key=lambda x: x['business'], reverse=not is_ascending)

        # 更新按钮文本以显示当前排序状态
        if is_ascending:
            self.sort_business_button.setText("业务排序 (升序)")
            self.sort_business_button.setChecked(False)
        else:
            self.sort_business_button.setText("业务排序 (降序)")
            self.sort_business_button.setChecked(True)

        # 更新表格显示
        self.update_table()