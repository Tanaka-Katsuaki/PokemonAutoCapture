import sys
from PyQt5.QtWidgets import QApplication

def main():
    """メインウィンドウの作成"""
    app = QApplication(sys.argv)

    # 起動時のスプラッシュ
    from initialize_splash import SplashScreen

    # スプラッシュスクリーンの設定
    SplashScreen.update_message("起動中...")
    
    # メインウィンドウ作成
    from main_window import MainWindow
    window = MainWindow()
    window.show()

    # スプラッシュスクリーンを閉じる
    SplashScreen.splash.finish(window)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()