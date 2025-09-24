import os
import sys
import atexit
import threading
import multiprocessing

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
""""""
from config.data_config import DataConfigClass

def on_exit():
    if DataConfigClass.is_battle_data_update:
        DataConfigClass.save_battle_data()

def main():
    """メインウィンドウの作成"""
    # Windows環境でのmultiprocessing対策
    if sys.platform.startswith('win'):
        multiprocessing.freeze_support()

    # Windows用：アプリケーションIDを設定
    if os.name == 'nt':  # Windows
        import ctypes
        myappid = 'mycompany.myproduct.subproduct.version'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(DataConfigClass.get_resource_path("assets", "icons", "icon.png")))
    atexit.register(on_exit)

    # 起動時のスプラッシュ
    try:
        from ui.splash import SplashScreen
        SplashScreen.initialize()
    except Exception as e:
        print(f"Splash screen error, using simple version: {e}")
        from ui.splash import SplashScreenSimple as SplashScreen
        SplashScreen.initialize()
    # スプラッシュスクリーンの設定
    SplashScreen.update_message("起動中...")

    # 各種データ読み込み
    load_thread = threading.Thread(target=DataConfigClass.load_data_config)
    load_thread.start()
    load_thread.join()  # データ読み込み完了まで待機
    
    # メインウィンドウ作成
    from ui.widgets.main_window import MainWindow
    window = MainWindow()
    #window.setWindowIcon(QIcon(DataConfigClass.get_resource_path('assets/icons/icon.ico')))
    window.show()

    # スプラッシュスクリーンを閉じる
    SplashScreen.finish(window)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()