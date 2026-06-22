import sys
import os

# ==========================================
# 核心魔法：将 src 目录动态加入 Python 环境变量
# 这样就可以直接 import gui, parsers, core 了
# ==========================================
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from PyQt5.QtWidgets import QApplication
from gui.main_window import Table2SchGUI

def main():
    print("🚀 正在启动 Table2Sch V2.0 (模块化架构)...")
    app = QApplication(sys.argv)
    
    # 实例化并展示主窗口
    window = Table2SchGUI()
    window.show()
    
    # 进入 Qt 事件循环
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()