import os
import json
import sys
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QCompleter,
    QComboBox, QGridLayout, QSizePolicy, QSpacerItem,
    QHeaderView, QApplication
)
from PySide6.QtCore import Qt, QStringListModel, QSize, QCoreApplication
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
        input_layout.addWidget(new_record_label, 0, 0, 1, 4)

        # 设置标签样式
        label_font = QFont()
        label_font.setPointSize(10)

        # 业务名称下拉框和添加记录按钮在同一行
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
        input_layout.addWidget(self.add_button, 1, 2)
        input_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 1, 3)

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

        # 创建增加和减少耗时的按钮
        self.increase_time_button = QPushButton("+")
        self.increase_time_button.setFixedSize(28, 28) # 设置固定大小
        self.increase_time_button.setObjectName("timeControlButton") # 设置对象名称
        self.decrease_time_button = QPushButton("-")
        self.decrease_time_button.setFixedSize(28, 28) # 设置固定大小
        self.decrease_time_button.setObjectName("timeControlButton") # 设置对象名称

        self.increase_time_button.clicked.connect(self.increase_time)
        self.decrease_time_button.clicked.connect(self.decrease_time)

        # 将任务描述和耗时相关的标签、输入框和按钮添加到GridLayout (放在第2行)
        # 任务描述标签和输入框
        input_layout.addWidget(task_label, 2, 0, alignment=Qt.AlignRight | Qt.AlignVCenter) # 任务描述标签在第0列
        input_layout.addWidget(self.task_input, 2, 1, 1, 1) # 任务描述输入框在第1列

        # 耗时标签、输入框和按钮
        input_layout.addWidget(manual_time_label, 2, 2, alignment=Qt.AlignRight | Qt.AlignVCenter) # 耗时标签在第2列
        # 使用QHBoxLayout来放置耗时输入框和增加/减少按钮
        time_input_buttons_layout = QHBoxLayout()
        time_input_buttons_layout.setContentsMargins(0, 0, 0, 0) # 移除内边距
        time_input_buttons_layout.setSpacing(5) # 调整耗时输入框和按钮之间的间隔
        time_input_buttons_layout.addWidget(self.manual_time_input)
        time_input_buttons_layout.addWidget(self.increase_time_button) # +按钮在前
        time_input_buttons_layout.addWidget(self.decrease_time_button) # -按钮在后

        input_layout.addLayout(time_input_buttons_layout, 2, 3, 1, 3) # 将耗时输入框和按钮的布局添加到网格布局的第2行第3列，跨越3列

        # 设置列的伸展因子以实现比例和调整间距
        # 任务描述输入框所在的列 (列1) 伸展因子设置为2
        input_layout.setColumnStretch(1, 2) 

        # 耗时输入框和按钮所在的列组 (列3到列5) 占比1
        # 主要通过控制列3的伸展因子来影响耗时输入框的宽度
        input_layout.setColumnStretch(3, 1)
        input_layout.setColumnStretch(4, 0) # 按钮列不伸展
        input_layout.setColumnStretch(5, 0) # 按钮列不伸展

        # 其他列 (标签) 的伸展因子为0，由内容决定宽度
        input_layout.setColumnStretch(0, 0)
        input_layout.setColumnStretch(2, 0)
        input_layout.setColumnStretch(6, 0) # 确保超出使用的列伸展因子为0

        self.layout.addWidget(input_container)

    def update_business_combo(self):
        self.business_combo.clear()
        # 根据截图，业务名称下拉框显示所有业务名称，不区分是否在记录中使用
        self.business_combo.addItems(self.business_names)


    def create_table(self):
        # 移除"时间"列，总共 4 列
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["业务", "任务", "耗时", "操作"])

        # 设置表格列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 业务名称
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 任务描述
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 耗时
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # 操作
        header.resizeSection(3, 70) # 设置操作列固定宽度

        # 设置列的最小宽度以优化编辑时的显示
        header.setMinimumSectionSize(80) # 设置所有列的统一最小宽度

        # 设置表格样式
        self.table.setAlternatingRowColors(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        # 允许双击或按 F2 键编辑单元格
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
                /* border: none; */ /* 移除默认边框 */
                width: 20px;
            }
            QComboBox::down-arrow {
                /* image: none; */ /* 移除默认图像 */
                /* border: none; */ /* 移除默认边框 */
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

        # 连接 itemChanged 信号到处理函数
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

        if not all([business, task, manual_time]):
            QMessageBox.warning(self, "警告", "请填写所有字段")
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
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        self.records.append(record)

        # 如果是新的业务名称，添加到业务名称库并保存
        if business and business not in self.business_names:
            self.business_names.append(business)
            self.save_business_names()
            self.update_business_combo()

        self.save_data()
        self.update_table()
        self.update_stats()
        self.clear_inputs()

    def update_table(self):
        self.table.setRowCount(len(self.records))
        for i, record in enumerate(reversed(self.records)):
            self.table.setItem(i, 0, QTableWidgetItem(record["business"]))
            self.table.setItem(i, 1, QTableWidgetItem(record["task"]))
            self.table.setItem(i, 2, QTableWidgetItem(str(record["manual_time"])))
            # 移除了设置"时间"列的代码

            delete_btn = QPushButton("删除")
            delete_btn.setFixedSize(60, 24) # 调整删除按钮大小
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
            delete_btn.clicked.connect(lambda checked, row=i: self.delete_record(row))
            # 将操作按钮设置到新的列索引 3
            self.table.setCellWidget(i, 3, delete_btn)

        self.table.resizeRowsToContents()


    def update_stats(self):
        manual_total = sum(r["manual_time"] for r in self.records) if self.records else 0
        # 修改统计逻辑为总记录单量
        total_records_count = len(self.records)

        self.manual_time_total.setText(f"总耗时: {manual_total:.1f}小时")
        # 更新标签文本
        self.records_today.setText(f"总记录单量: {total_records_count}条")

    def clear_inputs(self):
        # 清除输入框内容，但不清空下拉框的当前文本，以便于重复输入同一业务的记录
        # self.business_combo.setCurrentText("")
        self.task_input.clear()
        self.manual_time_input.clear()
        self.business_combo.setFocus()

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
            # 由于表格是倒序显示的，需要找到原始records列表中对应的索引
            original_index = len(self.records) - 1 - row
            if 0 <= original_index < len(self.records):
                 deleted_business = self.records[original_index]['business']
                 self.records.pop(original_index)
                 self.save_data()
                 self.update_table()
                 self.update_stats()
                # 检查删除的业务是否还在记录中使用，如果没有则从业务名称库中移除（可选）
                # if deleted_business in self.business_names and not any(r['business'] == deleted_business for r in self.records):
                #     self.business_names.remove(deleted_business)
                #     self.save_business_names()
                #     self.update_business_combo()
            else:
                 QMessageBox.warning(self, "错误", "删除记录失败，索引超出范围。")

    def generate_record_text(self):
        # 根据需求生成文本格式：小鲸 批量创建记录单\nxxx业务 完成了xxx 0.5
        if not self.records:
            QMessageBox.information(self, "提示", "没有记录可以生成文本")
            return

        text = "小鲸 批量创建记录单\n"
        # 注意：截图中的文本顺序与表格倒序不同，这里按照截图中的逻辑（最新记录在前面）生成文本
        # 如果需要按照时间正序生成，可以移除 reversed()
        for record in reversed(self.records):
            text += f"{record['business']} {record['task']} {record['manual_time']:.1f}\n"

        # 将生成的文本复制到剪贴板
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

            if os.path.exists(os.path.join(self.data_dir, "business.json")):
                with open(os.path.join(self.data_dir, "business.json"), "r", encoding="utf-8") as f:
                    self.business_names = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载数据失败: {str(e)}")

        # 在加载数据后更新业务名称下拉框的内容
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

        # 根据列索引确定编辑的是哪个字段
        field = None
        if col == 0:
            field = "business"
        elif col == 1:
            field = "task"
        elif col == 2:
            field = "manual_time"
        else:
            return # 忽略其他列的编辑

        # 对于耗时字段，验证输入是否为有效的数字
        if field in ["manual_time"]:
            try:
                new_value = float(new_value)
            except ValueError:
                QMessageBox.warning(self, "警告", "耗时必须是数字")
                # 恢复原来的值
                self.update_table()
                return

        # 找到原始 records 列表中对应的记录 (考虑表格倒序显示)
        original_index = len(self.records) - 1 - row
        if 0 <= original_index < len(self.records):
            record = self.records[original_index]
            old_value = record[field]

            # 更新记录中对应字段的值
            record[field] = new_value

            # 如果是业务名称被修改，检查新名称是否在业务名称库中
            if field == "business" and new_value not in self.business_names:
                self.business_names.append(new_value)
                self.save_business_names()
                self.update_business_combo()

            # 保存更新后的数据
            self.save_data()

            # 更新统计信息
            self.update_stats()

            # 可选：显示修改成功的提示
            # QMessageBox.information(self, "提示", f"已更新 {field} 为 {new_value}")

        else:
            QMessageBox.warning(self, "错误", "更新记录失败，索引超出范围。")
            # 恢复原来的值
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