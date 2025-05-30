## itsm提单工具
一个基于 PySide6 的桌面工作记录应用，用于方便地记录和管理日常工作任务和**耗时**

- **业务名称管理:** 支持添加、删除和置顶业务名称，实现业务名称的持久化管理
- **业务名称下拉提示:** 输入业务名称时提供历史记录提示，方便快速填写
- **记录添加:** 界面包含**业务名称**、**任务描述**和**耗时**输入框，支持通过回车或点击按钮添加
- **耗时调整按钮:** 在耗时输入框旁提供加减按钮，方便以0.5小时为单位调整耗时值
- **表格显示:** 在今日记录表格中清晰展示每条记录的**业务**、**任务**和**耗时**
- **表格编辑:** 直接在今日记录表格中修改业务名称、任务描述和耗时
- **业务排序:** 支持按业务名称对记录进行升序/降序排序
- **总耗时统计:** 统计所有记录的总耗时
- **总记录单量统计:** 统计所有记录的总条数
- **生成文本:** 将今日记录生成指定格式文本并复制到剪贴板


## 项目结构

```
main.py             # 应用主入口文件
requirements.txt    # 项目依赖列表
main.spec           # PyInstaller 编译配置文件
data/               # 数据存储目录
├── business.json   # 存储业务名称列表
└── records.json    # 存储工作记录 (每条记录包含业务、任务、手动耗时和时间戳)
dist/               # PyInstaller 编译输出目录
build/              # PyInstaller 编译临时目录
ui/                 # UI 相关文件目录
├── main_window.py  # 主窗口界面实现
└── business_dialog.py # 业务管理对话框实现
```

-   `main.py`: 应用程序的入口点，初始化 QApplication 并显示主窗口
-   `requirements.txt`: 列出了项目所需的 Python 库及其版本，例如 PySide6
-   `main.spec`: 当使用 PyInstaller 编译时生成的配置文件，可以用于定制编译选项，如指定图标、包含额外文件等
-   `data/`: 存放应用运行时生成的 JSON 数据文件，包括业务名称列表和工作记录
-   `dist/`: PyInstaller 编译成功后生成的包含可执行文件的目录
-   `build/`: PyInstaller 在编译过程中使用的临时目录
-   `ui/`: 包含应用程序用户界面相关的 Python 模块
    -   `main_window.py`: 实现了应用程序的主窗口界面和主要逻辑，包括记录的添加、显示、统计、排序、文本生成、记录删除/清空以及与业务管理的交互
    -   `business_dialog.py`: 实现了业务名称管理的对话框界面和相关逻辑

## 编译与使用

### 前置条件

1.  安装 Python (建议 3.6+)
2.  安装项目的依赖库。打开终端或命令提示符，切换到项目根目录，执行以下命令：
    ```bash
    pip install -r requirements.txt
    ```
3.  安装 PyInstaller 和 UPX (用于压缩可执行文件，如果使用 `--upx-dir` 参数):
    ```bash
    pip install pyinstaller upx
    ```
    如果 pip 安装 upx 遇到问题，可以从 UPX 官方网站 ([https://upx.github.io/](https://upx.github.io/)) 下载对应操作系统的二进制文件，并将其路径提供给 PyInstaller 的 `--upx-dir` 参数

### Windows 环境

在命令提示符或 PowerShell 中，切换到项目根目录，执行以下命令进行编译：

```bash
pyinstaller --noconsole --onedir --upx-dir=upx --icon=favicon.ico --add-data "favicon.ico;." .\main.py"
```


请将 `favicon.ico` 替换为您实际的图标文件名。

编译成功后，可执行文件会在 `dist` 目录下生成一个与项目同名的文件夹，运行其中的 `.exe` 文件即可启动应用

### macOS 环境

在终端中，切换到项目根目录，执行以下命令进行编译：

请注意，macOS 下使用 UPX 可能需要不同的设置或路径。如果您想使用 UPX，请确保 UPX 已正确安装并配置在系统环境变量中，或者提供 UPX 二进制文件的绝对路径给 `--upx-dir` 参数

```bash
pyinstaller --noconsole --onedir --icon=path/to/your_icon.icns .\main.py
```

编译成功后，可执行文件会在 `dist` 目录下生成一个与项目同名的文件夹，其中包含应用程序包 (`.app`)
