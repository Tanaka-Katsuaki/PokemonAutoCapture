import sys
import atexit
import threading

from PyQt5.QtWidgets import QApplication
""""""
from data_config import DataConfigClass

def on_exit():
    if DataConfigClass.is_battle_data_update:
        DataConfigClass.save_battle_data()

def main():
    """メインウィンドウの作成"""
    app = QApplication(sys.argv)
    atexit.register(on_exit)

    # 起動時のスプラッシュ
    from initialize_splash import SplashScreen
    # スプラッシュスクリーンの設定
    SplashScreen.update_message("起動中...")

    # 各種データ読み込み
    load_thread = threading.Thread(target=DataConfigClass.load_data_config)
    load_thread.start()
    load_thread.join()
    
    # メインウィンドウ作成
    from main_window import MainWindow
    window = MainWindow()
    window.show()

    # スプラッシュスクリーンを閉じる
    SplashScreen.splash.finish(window)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()