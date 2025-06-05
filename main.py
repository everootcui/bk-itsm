import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # Mac 特定的设置
    if sys.platform == 'darwin':
        # 设置 Mac 风格的菜单栏
        app.setAttribute(Qt.AA_DontShowIconsInMenus, True)
        # 设置应用程序名称，这会影响 Mac 的菜单栏显示
        app.setApplicationName("工作记录工具")
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()