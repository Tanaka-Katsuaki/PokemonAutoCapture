import os
import sys
import time
import multiprocessing
from multiprocessing import Queue, Process
from PyQt5.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget, QApplication
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QMovie

class SplashScreen:
    """
    GIFアニメーション対応のスプラッシュスクリーン
    """
    splash = None
    splash_label = None
    splash_image = None
    process = None
    message_queue = None
    use_multiprocess = True  # プロセス版を使うかどうか
    
    @staticmethod
    def get_resource_path(*relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, *relative_path)

    @staticmethod
    def initialize():
        """スプラッシュ画面を初期化"""
        SplashScreen.splash_image = SplashScreen.get_resource_path("assets", "icons", "icon_20fps.gif")  # GIFファイルのパス
        try:
            SplashScreen
            if SplashScreen.use_multiprocess:
                SplashScreen._initialize_multiprocess()
            else:
                SplashScreen._initialize_threaded()
        except Exception as e:
            print(f"Multiprocess splash failed, falling back to threaded version: {e}")
            SplashScreen.use_multiprocess = False
            SplashScreen._initialize_threaded()
    
    @staticmethod
    def _initialize_multiprocess():
        """マルチプロセス版の初期化"""
        # メッセージ用のキューを作成
        SplashScreen.message_queue = Queue()
        
        # 別プロセスでスプラッシュを開始
        SplashScreen.process = Process(
            target=SplashScreen._run_splash_process,
            args=(SplashScreen.message_queue, SplashScreen.splash_image)
        )
        SplashScreen.process.daemon = True  # メインプロセス終了時に自動終了
        SplashScreen.process.start()
        
        # プロセス開始まで少し待機
        time.sleep(0.2)
    
    @staticmethod
    def _initialize_threaded():
        """同一プロセス版の初期化"""
        # スプラッシュの背景
        splash_pix = QPixmap(500, 300)
        splash_pix.fill(Qt.white)
        
        # スプラッシュスクリーンを作成
        SplashScreen.splash = QSplashScreen(splash_pix)
        
        # メインのコンテナウィジェット
        container = QWidget(SplashScreen.splash)
        container.setGeometry(0, 0, 500, 300)
        
        # メインレイアウト
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # GIFアニメーション用ラベル
        gif_label = QLabel()
        gif_label.setAlignment(Qt.AlignCenter)
        
        # GIFファイルが存在する場合はアニメーションを設定
        if os.path.exists(SplashScreen.splash_image):
            movie = QMovie(SplashScreen.splash_image)
            movie.setScaledSize(movie.scaledSize().scaled(180, 180, Qt.KeepAspectRatio))
            gif_label.setMovie(movie)
            movie.start()
            # movieオブジェクトを保持
            SplashScreen.movie = movie
        else:
            # GIFファイルがない場合は静止画像を表示
            static_image = SplashScreen.get_resource_path("assets", "icons", "icon.png")
            if os.path.exists(static_image):
                gif_label.setPixmap(QPixmap(static_image).scaled(
                    180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                gif_label.setText("Loading...")
                gif_label.setStyleSheet("color: #333333; font-size: 14pt;")
        
        # メッセージラベル
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
        main_layout.addStretch(1)
        main_layout.addWidget(gif_label, 4)
        main_layout.addStretch(1)
        main_layout.addWidget(SplashScreen.splash_label, 1)
        
        # アプリケーションイベント処理を定期実行
        SplashScreen.timer = QTimer()
        SplashScreen.timer.timeout.connect(lambda: QApplication.processEvents())
        SplashScreen.timer.start(16)  # 約60FPSでイベント処理
        
        # スプラッシュを表示
        SplashScreen.splash.show()
        SplashScreen.splash.raise_()  # 前面に表示
        QApplication.processEvents()  # 即座に表示
    
    @staticmethod
    def _run_splash_process(message_queue, splash_image_path):
        """別プロセスで実行されるスプラッシュ画面"""
        try:
            # 新しいQApplicationインスタンスを作成
            app = QApplication([])
            
            # スプラッシュの背景
            splash_pix = QPixmap(500, 300)
            splash_pix.fill(Qt.white)
            
            # スプラッシュスクリーンを作成
            splash = QSplashScreen(splash_pix)
            splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.SplashScreen)
            
            # メインのコンテナウィジェット
            container = QWidget(splash)
            container.setGeometry(0, 0, 500, 300)
            
            # メインレイアウト
            main_layout = QVBoxLayout(container)
            main_layout.setContentsMargins(20, 20, 20, 20)
            
            # GIFアニメーション用ラベル
            gif_label = QLabel()
            gif_label.setAlignment(Qt.AlignCenter)
            
            # GIFファイルが存在する場合はアニメーションを設定
            if os.path.exists(splash_image_path):
                movie = QMovie(splash_image_path)
                movie.setScaledSize(movie.scaledSize().scaled(180, 180, Qt.KeepAspectRatio))
                gif_label.setMovie(movie)
                movie.start()
            else:
                # GIFファイルがない場合は代替表示
                static_image = SplashScreen.get_resource_path("assets", "icons", "icon.png")
                if os.path.exists(static_image):
                    gif_label.setPixmap(QPixmap(static_image).scaled(
                        180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                else:
                    gif_label.setText("Loading...")
                    gif_label.setStyleSheet("color: #333333; font-size: 14pt;")
            
            # メッセージラベル
            message_label = QLabel("起動中...")
            message_label.setStyleSheet("""
                color: #333333;
                font-family: 'Meiryo';
                font-size: 12pt;
                font-weight: bold;
                padding: 10px;
            """)
            message_label.setAlignment(Qt.AlignCenter)
            
            # レイアウトに追加
            main_layout.addStretch(1)
            main_layout.addWidget(gif_label, 4)
            main_layout.addStretch(1)
            main_layout.addWidget(message_label, 1)
            
            # メッセージ更新用タイマー
            message_timer = QTimer()
            message_timer.timeout.connect(lambda: SplashScreen._check_message_queue(message_queue, message_label))
            message_timer.start(50)  # 50msごとにメッセージをチェック
            
            # スプラッシュを表示
            splash.show()
            splash.raise_()
            splash.activateWindow()
            
            # アプリケーションループを開始
            app.exec_()
            
        except Exception as e:
            print(f"Splash process error: {e}")
    
    @staticmethod
    def _check_message_queue(message_queue, message_label):
        """メッセージキューをチェックして表示を更新"""
        try:
            while not message_queue.empty():
                message = message_queue.get_nowait()
                if message == "__TERMINATE__":
                    QApplication.quit()
                    return
                message_label.setText(message)
                message_label.repaint()
        except:
            pass
    
    @staticmethod
    def update_message(message):
        """スプラッシュ画面のメッセージを更新"""
        try:
            if SplashScreen.use_multiprocess and SplashScreen.message_queue:
                SplashScreen.message_queue.put_nowait(message)
            elif not SplashScreen.use_multiprocess and SplashScreen.splash_label:
                SplashScreen.splash_label.setText(message)
                QApplication.processEvents()
        except Exception as e:
            print(f"Message update error: {e}")
    
    @staticmethod
    def finish(main_window):
        """スプラッシュ画面を終了"""
        try:
            if SplashScreen.use_multiprocess:
                # マルチプロセス版の終了処理
                if SplashScreen.message_queue:
                    try:
                        SplashScreen.message_queue.put_nowait("__TERMINATE__")
                    except:
                        pass
                
                if SplashScreen.process and SplashScreen.process.is_alive():
                    SplashScreen.process.join(timeout=1.0)
                    if SplashScreen.process.is_alive():
                        SplashScreen.process.terminate()
                        SplashScreen.process.join(timeout=0.5)
                        if SplashScreen.process.is_alive():
                            SplashScreen.process.kill()
            else:
                # 同一プロセス版の終了処理
                if hasattr(SplashScreen, 'timer') and SplashScreen.timer:
                    SplashScreen.timer.stop()
                if hasattr(SplashScreen, 'movie') and SplashScreen.movie:
                    SplashScreen.movie.stop()
                if SplashScreen.splash:
                    SplashScreen.splash.finish(main_window)
        except Exception as e:
            print(f"Finish error: {e}")


# デバッグ用のシンプル版（フォールバック）
class SplashScreenSimple:
    """
    シンプルな静的スプラッシュスクリーン（デバッグ用）
    """
    splash = None
    splash_label = None
    splash_image = SplashScreen.get_resource_path("assets", "icons", "icon.png")
    
    @staticmethod
    def initialize():
        """スプラッシュ画面を初期化"""
        splash_pix = QPixmap(500, 300)
        splash_pix.fill(Qt.white)
        
        SplashScreenSimple.splash = QSplashScreen(splash_pix)
        
        container = QWidget(SplashScreenSimple.splash)
        container.setGeometry(0, 0, 500, 300)
        
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 固定画像のラベル
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        if os.path.exists(SplashScreenSimple.splash_image):
            image_label.setPixmap(QPixmap(SplashScreenSimple.splash_image).scaled(
                180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            image_label.setText("Loading...")
            image_label.setStyleSheet("color: #333333; font-size: 14pt;")
        
        # メッセージラベル
        SplashScreenSimple.splash_label = QLabel("起動中...")
        SplashScreenSimple.splash_label.setStyleSheet("""
            color: #333333;
            font-family: 'Meiryo';
            font-size: 12pt;
            font-weight: bold;
            padding: 10px;
        """)
        SplashScreenSimple.splash_label.setAlignment(Qt.AlignCenter)
        
        main_layout.addStretch(1)
        main_layout.addWidget(image_label, 4)
        main_layout.addStretch(1)
        main_layout.addWidget(SplashScreenSimple.splash_label, 1)
        
        SplashScreenSimple.splash.show()
        QApplication.processEvents()
    
    @staticmethod
    def update_message(message):
        """スプラッシュ画面のメッセージを更新"""
        if SplashScreenSimple.splash_label:
            SplashScreenSimple.splash_label.setText(message)
            SplashScreenSimple.splash.repaint()
            QApplication.processEvents()
    
    @staticmethod
    def finish(main_window):
        """スプラッシュ画面を閉じる"""
        if SplashScreenSimple.splash:
            SplashScreenSimple.splash.finish(main_window)