from PyQt5.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

class SplashScreen:
    splash = None
    splash_label = None
    splash_image = "assets/images/UI Icons/pm_placeholder_mod.png"
    
    @staticmethod
    def initialize():
        """スプラッシュ画面を初期化"""
        # スプラッシュの背景
        splash_pix = QPixmap(500, 300)
        splash_pix.fill(Qt.white)  # 背景色を白に設定
        
        # スプラッシュスクリーンを作成
        SplashScreen.splash = QSplashScreen(splash_pix)
        
        # メインのコンテナウィジェット
        container = QWidget(SplashScreen.splash)
        container.setGeometry(0, 0, 500, 300)
        
        # メインレイアウト
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 固定画像のラベル（中央に配置）
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setPixmap(QPixmap(SplashScreen.splash_image).scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        # メッセージラベル（下部に配置）
        SplashScreen.splash_label = QLabel("起動中...")
        SplashScreen.splash_label.setStyleSheet("""
            color: #333333;
            font-family: 'Meiryo';
            font-size: 12pt;
            font-weight: bold;
            padding: 10px;
        """)
        SplashScreen.splash_label.setAlignment(Qt.AlignCenter)
        
        # レイアウトに追加
        main_layout.addStretch(1)  # 上部スペース
        main_layout.addWidget(image_label, 4)  # 画像 (中央寄り)
        main_layout.addStretch(1)  # 中間スペース 
        main_layout.addWidget(SplashScreen.splash_label, 1)  # メッセージ (下部)
        
        # スプラッシュを表示
        SplashScreen.splash.show()
    
    @staticmethod
    def update_message(message):
        """スプラッシュ画面のメッセージを更新"""
        if SplashScreen.splash is None or SplashScreen.splash_label is None:
            SplashScreen.initialize()
            
        SplashScreen.splash_label.setText(message)
        SplashScreen.splash.repaint()  # 即時の再描画を強制
    
    @staticmethod
    def finish(main_window):
        """スプラッシュ画面を閉じる"""
        if SplashScreen.splash:
            SplashScreen.splash.finish(main_window)
