from PyQt5.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

class SplashScreen:
    splash = None
    splash_label = None
    
    @staticmethod
    def initialize():
        """スプラッシュ画面を初期化"""
        splash_pix = QPixmap(400, 200)
        splash_pix.fill(Qt.white)  # 背景色を白に設定
        
        # スプラッシュスクリーンを作成
        SplashScreen.splash = QSplashScreen(splash_pix)
        
        # テキストを表示するためのレイアウト
        SplashScreen.splash_label = QLabel("起動中...")
        SplashScreen.splash_label.setStyleSheet("color: black;")  # テキスト色を黒に設定
        SplashScreen.splash_label.setAlignment(Qt.AlignCenter)
        
        # レイアウトをスプラッシュウィンドウに設定（ここが重要）
        layout = QVBoxLayout()
        layout.addWidget(SplashScreen.splash_label)
        
        # スプラッシュスクリーンの中央にテキストを配置
        temp_widget = QWidget(SplashScreen.splash)
        temp_widget.setLayout(layout)
        temp_widget.setGeometry(0, 0, 400, 200)
        
        # スプラッシュを表示
        SplashScreen.splash.show()
    
    @staticmethod
    def update_message(message):
        """
        スプラッシュ画面のメッセージを更新

        Args:
        - message (str): スプラッシュに表示するテキスト
        """
        if SplashScreen.splash is None or SplashScreen.splash_label is None:
            SplashScreen.initialize()
            
        SplashScreen.splash_label.setText(message)
        SplashScreen.splash.repaint()  # 即時の再描画を強制