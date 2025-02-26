import sys
from PyQt5.QtWidgets import QApplication

from main_window import MainWindow

def main():
    """ウィンドウの作成"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()