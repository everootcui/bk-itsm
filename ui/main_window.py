import os
import json
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("工作记录工具")
        self.setMinimumSize(800, 700)

        # 设置窗口图标
        try:
            # 尝试获取应用程序可执行文件所在的目录
            app_path = QCoreApplication.applicationFilePath()
            app_dir = os.path.dirname(app_path)

            # 尝试在打包后的 _internal 目录中查找图标
            icon_path_attempt1 = os.path.join(app_dir, '_internal', 'favicon.ico')
            print(f"尝试路径 1 (internal): {icon_path_attempt1}, 存在: {os.path.exists(icon_path_attempt1)}") # 打印调试信息

            icon_path = icon_path_attempt1

            # 如果 _internal 目录下的路径不存在，尝试从源码目录加载 (开发环境)
            if not os.path.exists(icon_path):
                 # 尝试项目根目录 (对于直接运行 main.py)
                 icon_path_attempt2 = 'favicon.ico' # 假设在项目根目录
                 print(f"尝试路径 2 (root): {icon_path_attempt2}, 存在: {os.path.exists(icon_path_attempt2)}") # 打印调试信息
                 icon_path = icon_path_attempt2

            # 如果找到了图标文件路径，则设置窗口图标
            if os.path.exists(icon_path):
                 self.setWindowIcon(QIcon(icon_path))
                 print(f"成功设置图标: {icon_path}") # 打印成功信息
            else:
                 print("警告: 图标文件 favicon.ico 未找到！") # 如果最终还是没找到图标，打印警告

        except Exception as e:
            # 捕获设置图标时的异常
            print(f"设置窗口图标时发生错误: {e}") # 打印异常信息

        # 初始化数据
        self.records = []
        self.business_names = []

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
        self.task_time_input.returnPressed.connect(self.add_record)

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

        # 任务描述输入
        task_label = QLabel("任务描述:")
        task_label.setFont(label_font)
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("输入任务描述")
        self.task_input.setMinimumHeight(28)
        input_layout.addWidget(task_label, 2, 0, alignment=Qt.AlignRight | Qt.AlignVCenter)
        input_layout.addWidget(self.task_input, 2, 1, 1, 3) # 任务描述跨三列

        # 手动耗时输入和任务耗时输入在同一行
        manual_time_label = QLabel("手动耗时(小时):")
        manual_time_label.setFont(label_font)
        self.manual_time_input = QLineEdit()
        self.manual_time_input.setPlaceholderText("输入")
        self.manual_time_input.setMinimumHeight(28)
        self.manual_time_input.setMaximumWidth(80)

        task_time_label = QLabel("任务耗时(小时):")
        task_time_label.setFont(label_font)
        self.task_time_input = QLineEdit()
        self.task_time_input.setPlaceholderText("输入")
        self.task_time_input.setMinimumHeight(28)
        self.task_time_input.setMaximumWidth(80)

        # 使用QHBoxLayout来排列耗时输入框，然后将QHBoxLayout添加到GridLayout
        time_inputs_layout = QHBoxLayout()
        time_inputs_layout.setSpacing(5)
        time_inputs_layout.addWidget(manual_time_label)
        time_inputs_layout.addWidget(self.manual_time_input)
        time_inputs_layout.addSpacing(15)
        time_inputs_layout.addWidget(task_time_label)
        time_inputs_layout.addWidget(self.task_time_input)
        time_inputs_layout.addStretch() # 将耗时输入框推到左边

        input_layout.addLayout(time_inputs_layout, 3, 0, 1, 4) # 耗时输入框跨四列

        self.layout.addWidget(input_container)

    def update_business_combo(self):
        self.business_combo.clear()
        # 根据截图，业务名称下拉框显示所有业务名称，不区分是否在记录中使用
        self.business_combo.addItems(self.business_names)


    def create_table(self):
        # 移除"时间"列，总共 5 列
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["业务", "任务", "手动耗时", "任务耗时", "操作"])

        # 设置表格列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 业务名称
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 任务描述
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 手动耗时
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 任务耗时
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # 操作 (新的索引是 4)
        header.resizeSection(4, 70) # 设置操作列固定宽度

        # 设置列的最小宽度以优化编辑时的显示
        header.setMinimumSectionSize(80) # 设置所有列的统一最小宽度

        # 设置表格样式
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        # 允许双击或按 F2 键编辑单元格
        self.table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet("QTableWidget { selection-background-color: #e1ecff; selection-color: #3a84ff; }\nQTableWidget::item { padding: 5px; }\nQTableWidget::item:selected { background-color: #e1ecff; color: #3a84ff; border: 1px solid #3a84ff; }") # 统一选中样式和item padding

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

        self.manual_time_total = QLabel("总手动耗时: 0小时")
        self.task_time_total = QLabel("总任务耗时: 0小时")
        # 将"今日总记录数"改为"总记录单量"
        self.records_today = QLabel("总记录单量: 0条")

        for label in [self.manual_time_total, self.task_time_total, self.records_today]:
            label.setFont(stats_font)
            stats_layout.addWidget(label)

        # 移除stretch，让间距控制分布
        # stats_layout.addStretch()
        self.layout.addWidget(stats_container)

    def create_action_buttons_area(self):
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(15) # 增加按钮之间的间距

        self.manage_button = QPushButton("管理业务")
        self.delete_selected_button = QPushButton("删除选中")
        self.generate_text_button = QPushButton("生成文本")
        self.clear_records_button = QPushButton("清空记录")

        self.manage_button.clicked.connect(self.show_business_dialog)
        self.delete_selected_button.clicked.connect(self.delete_selected_records)
        self.generate_text_button.clicked.connect(self.generate_record_text)
        self.clear_records_button.clicked.connect(self.clear_all_records)

        # 设置删除和清空按钮的object name以便应用特定样式
        self.delete_selected_button.setObjectName("delete_selected_button")
        self.clear_records_button.setObjectName("clear_records_button")

        # 调整按钮大小和间距，并按照截图顺序排列
        button_height = 30 # 调整按钮高度

        button_layout.addWidget(self.manage_button)
        button_layout.addWidget(self.delete_selected_button)
        button_layout.addWidget(self.generate_text_button)
        button_layout.addWidget(self.clear_records_button)

        for button in [self.manage_button, self.delete_selected_button, self.generate_text_button, self.clear_records_button]:
            button.setMinimumHeight(button_height)
            # 移除固定宽度设置，使用Expanding策略填充宽度
            # button.setFixedWidth(button_width)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) # 让按钮填充宽度

        # 移除stretch，让按钮均匀分布
        # button_layout.addStretch()

        self.layout.addWidget(button_container)

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
                color: #333;
            }
            #sectionLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333;
                margin-top: 10px;
                margin-bottom: 5px;
            }
            #inputContainer,
            #statsContainer {
                background-color: white;
                border-radius: 5px;
                /* padding handled by layout */
            }
            QPushButton {
                background-color: #3a84ff;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 11px;
        }
        QPushButton:hover {
            background-color: #2b6cd9;
        }
        QPushButton:pressed {
            background-color: #0052cc;
        }
         QPushButton#delete_selected_button,
         QPushButton#clear_records_button {
             background-color: #ea3636;
         }
         QPushButton#delete_selected_button:hover,
         QPushButton#clear_records_button:hover {
             background-color: #c42b2b;
         }
          QPushButton#delete_selected_button:pressed,
         QPushButton#clear_records_button:pressed {
             background-color: #a12121;
         }
        QLineEdit, QComboBox {
            padding: 5px 10px;
            border: 1px solid #dcdee5;
            border-radius: 3px;
            background-color: white;
            font-size: 11px;
        }
        QLineEdit:focus, QComboBox:focus {
            border-color: #3a84ff;
        }
        QComboBox::drop-down {
            /* border: none; */ /* 移除默认边框 */
            width: 20px;
        }
        QComboBox::down-arrow {
            /* image: none; */ /* 移除默认图像 */
            /* border: none; */ /* 移除默认边框 */
        }
        QTableWidget {
            border: 1px solid #dcdee5;
            border-radius: 5px;
            background-color: white;
            gridline-color: transparent;
        }
        QTableWidget::item {
            padding: 5px;
            border-bottom: 1px solid #f0f1f5;
        }
        QTableWidget::item:selected {
            background-color: #e1ecff;
            color: #3a84ff;
            border: 1px solid #3a84ff;
        }
        QTableWidget QLineEdit,
        QTableWidget QComboBox {
            border: 1px solid #3a84ff;
            padding: 0;
        }
        QTableWidget QLineEdit:focus,
        QTableWidget QComboBox:focus {
            border-color: #2b6cd9;
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

    def update_business_combo(self):
        self.business_combo.clear()
        # 根据截图，业务名称下拉框显示所有业务名称，不区分是否在记录中使用
        self.business_combo.addItems(self.business_names)


    def add_record(self):
        business = self.business_combo.currentText().strip()
        task = self.task_input.text().strip()
        manual_time = self.manual_time_input.text().strip()
        task_time = self.task_time_input.text().strip()

        if not all([business, task, manual_time, task_time]):
            QMessageBox.warning(self, "警告", "请填写所有字段")
            return

        try:
            manual_time = float(manual_time)
            task_time = float(task_time)
        except ValueError:
            QMessageBox.warning(self, "警告", "耗时必须是数字")
            return

        record = {
            "business": business,
            "task": task,
            "manual_time": manual_time,
            "task_time": task_time,
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
            self.table.setItem(i, 3, QTableWidgetItem(str(record["task_time"])))
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
            # 将操作按钮设置到新的列索引 4
            self.table.setCellWidget(i, 4, delete_btn)

        self.table.resizeRowsToContents()


    def update_stats(self):
        manual_total = sum(r["manual_time"] for r in self.records) if self.records else 0
        task_total = sum(r["task_time"] for r in self.records) if self.records else 0
        # 修改统计逻辑为总记录单量
        total_records_count = len(self.records)

        self.manual_time_total.setText(f"总手动耗时: {manual_total:.1f}小时")
        self.task_time_total.setText(f"总任务耗时: {task_total:.1f}小时")
        # 更新标签文本
        self.records_today.setText(f"总记录单量: {total_records_count}条")

    def clear_inputs(self):
        # 清除输入框内容，但不清空下拉框的当前文本，以便于重复输入同一业务的记录
        # self.business_combo.setCurrentText("")
        self.task_input.clear()
        self.manual_time_input.clear()
        self.task_time_input.clear()
        self.business_combo.setFocus()

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

    def delete_selected_records(self):
        selected_rows = sorted(list(set([item.row() for item in self.table.selectedItems()])), reverse=True)
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请选择要删除的记录")
            return

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除选中的 {len(selected_rows)} 条记录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            businesses_to_check = set()
            for row in selected_rows:
                original_index = len(self.records) - 1 - row
                if 0 <= original_index < len(self.records):
                    businesses_to_check.add(self.records[original_index]['business'])
                    self.records.pop(original_index)

            self.save_data()
            self.update_table()
            self.update_stats()

            # 检查删除的业务是否还在记录中使用，如果没有则从业务名称库中移除（可选）
            # for business in businesses_to_check:
            #     if business in self.business_names and not any(r['business'] == business for r in self.records):
            #         self.business_names.remove(business)
            # self.save_business_names()
            # self.update_business_combo()

    def generate_record_text(self):
        # 根据需求生成文本格式：小鲸 批量创建记录单\nxxx业务 完成了xxx任务 0.5 1
        # 过滤掉当天以外的记录
        today_records = [r for r in self.records if r["timestamp"].startswith(datetime.now().strftime("%Y-%m-%d"))]

        if not today_records:
            QMessageBox.information(self, "提示", "今日没有记录可以生成文本")
            return

        text = "小鲸 批量创建记录单\n"
        # 注意：截图中的文本顺序与表格倒序不同，这里按照截图中的逻辑（最新记录在前面）生成文本
        # 如果需要按照时间正序生成，可以移除 reversed()
        for record in reversed(today_records):
             text += f"{record["business"]} {record["task"]}任务 {record["manual_time"]:.1f} {record["task_time"]:.1f}\n"

        # 将生成的文本复制到剪贴板
        clipboard = QApplication.clipboard()
        clipboard.setText(text.strip())
        QMessageBox.information(self, "提示", "今日记录文本已复制到剪贴板")

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
            if os.path.exists("data/records.json"):
                with open("data/records.json", "r", encoding="utf-8") as f:
                    self.records = json.load(f)

            if os.path.exists("data/business.json"):
                with open("data/business.json", "r", encoding="utf-8") as f:
                    self.business_names = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载数据失败: {str(e)}")

        # 在加载数据后更新业务名称下拉框的内容
        self.update_business_combo()

    def save_data(self):
        os.makedirs("data", exist_ok=True)
        try:
            with open("data/records.json", "w", encoding="utf-8") as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"保存数据失败: {str(e)}")

    def save_business_names(self):
        os.makedirs("data", exist_ok=True)
        try:
            with open("data/business.json", "w", encoding="utf-8") as f:
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
            if os.path.exists("data/business.json"):
                with open("data/business.json", "r", encoding="utf-8") as f:
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
        elif col == 3:
            field = "task_time"
        else:
            return # 忽略其他列的编辑

        # 对于耗时字段，验证输入是否为有效的数字
        if field in ["manual_time", "task_time"]:
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