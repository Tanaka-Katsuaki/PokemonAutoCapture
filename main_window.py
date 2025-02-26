import numpy as np
from pygrabber.dshow_graph import FilterGraph


from graphic_widget import OpenGLWidget
from PyQt5.QtWidgets import (QMainWindow, QDockWidget, QWidget,
                              QVBoxLayout, QHBoxLayout, QAction, QLabel, QPushButton, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor

from audio_manager import AudioManager

"""メインウィンドウ"""
class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()

        """ウィンドウ"""
        self.setWindowTitle("Game Capture Application")
        self.setGeometry(100, 100, 1280, 720)
        self.setMinimumSize(1280, 720)

        # MainWindowのスタイル設定
        self.setStyleSheet("""
            QMainWindow {
                background-color: #101010;
            }
            QMainWindow::separator {
                height: 0px;
                margin: 0px;
                padding: 1px;
                background: #202020;
            }
        """)

        """グラフィック"""
        self.central_widget = OpenGLWidget(self) # ゲーム映像
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)
        self.central_widget.error_signal.connect(self.show_error)

        """オーディオ"""
        self.audio_capture = AudioManager()
        self.audio_input_index = None # 初期入力デバイス
        self.audio_output_index = None # 初期出力デバイスデバイス
        self.audio_capture.error_signal.connect(self.show_error)
        # self.audio_capture.start()

        """オプションUI"""
        # メニューバー作成
        self.camera_actions: list[QAction] = [] # 入力映像デバイス一覧
        self.audio_actions: list[QAction] = []  # 入力音声デバイス一覧
        self.volume_actions: list[QAction] = [] # ボリューム調整用選択肢
        self.create_menubar()
        # エラー表示用ドック
        self.error_dock = ErrorDock(self)
        self.error_dock.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.error_dock)
        # パーティー表示ドック
        self.my_party_dock = self.central_widget.get_my_party_dock()
        self.opponent_party_dock = self.central_widget.get_opponent_party_dock()
        self.addDockWidget(Qt.LeftDockWidgetArea, self.my_party_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.opponent_party_dock)
    

    """メニューバー初期化"""
    def create_menubar(self):
        try:
            self.menubar = self.menuBar()

            # 映像デバイスメニュー
            self.video_menu = self.menubar.addMenu('入力映像')
            self.set_camera_menu()
            self.video_menu.addActions(self.camera_actions)

            # 入力音源デバイスメニュー
            self.mic_menu = self.menubar.addMenu('入力音源')
            self.set_audio_menu()
            self.mic_menu.addActions(self.audio_actions)
            self.audio_capture.start(self.audio_input_index, self.audio_output_index)

            # 音声ボリュームメニュー
            self.audio_volume_menu = self.menubar.addMenu('ボリューム')
            self.set_audio_volume_menu()
            self.audio_volume_menu.addActions(self.volume_actions)
            self.volume_actions[5].trigger()
        except Exception as e:
            self.show_error(e)
    
    def set_camera_menu(self):
        """
        入力映像デバイス一覧を取得してメニューにセット
        """
        devices = FilterGraph().get_input_devices()
        for device_index, device_name in enumerate(devices):
            self.camera_actions.append(QAction(device_name))
            self.camera_actions[-1].triggered.connect(lambda _, idx=device_index: self.central_widget.reload_capture(idx))

    def set_audio_menu(self):
        """
        入力音声デバイス一覧を取得してメニューにセット
        """
        input_devices, default_input_index, output_devices, default_output_index = self.audio_capture.device_list()

        # 初期設定デバイスの取得
        self.audio_input_index = default_input_index
        self.audio_output_index = default_output_index

        for device in input_devices:
            self.audio_actions.append(QAction(device['name']))
            self.audio_actions[-1].triggered.connect(lambda _, idx=device['index']:
                                                     self.audio_capture.reload_audio(input_device=idx, output_device=self.audio_output_index))

    def set_audio_volume_menu(self):
        """
        ボリュームを0%-200%の間で20刻みで設定
        """
        for i in range(0, 11, 1):
            volume = i * 20
            self.volume_actions.append(QAction(f'{volume}%'))
            self.volume_actions[-1].setCheckable(True)
            self.volume_actions[-1].triggered.connect(lambda _, vol=volume: self.set_volume(vol))

    def set_volume(self, volume):
        """
        ボリュームメニューは選択中の音量にチェックマークが付くように
        """
        for vol_action in self.volume_actions:
            vol_action.setChecked(False)
        
        selected_action = self.sender()
        if selected_action:
            selected_action.setChecked(True)
        
        self.audio_capture.set_volume(volume)

    # エラー表示
    def show_error(self, error):
        error_message = str(error)
        self.error_dock.show_error(error_message)

    """オーバーライド関数"""
    def showEvent(self, event):
        super().showEvent(event)

    def resizeEvent(self, event):
        """
        ウィンドウサイズ変更時に呼び出す
        """
        super().resizeEvent(event)

        # 各種画像をウィンドウサイズに合わせて調整
        height = self.centralWidget().height() - self.error_dock.height() # メインウィジェットの高さ - 下部ドックの高さ
        self.my_party_dock.setFixedWidth(height // 6)
        self.opponent_party_dock.setFixedWidth(height // 6)
        self.my_party_dock.resize_party_icon(height)
        self.opponent_party_dock.resize_party_icon(height)

    def closeEvent(self, event):
        """ウィンドウ終了時に呼び出す"""
        if self.central_widget:
            self.central_widget.closeEvent(event)
        self.audio_capture.stop
        event.accept()


"""エラー表示用GUIクラス"""
class ErrorDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAllowedAreas(Qt.BottomDockWidgetArea) # ドックの位置は下部
        self.setFeatures(QDockWidget.NoDockWidgetFeatures)  # ドックの移動を禁止
        
        # タイトルバーを非表示にする
        self.setTitleBarWidget(QWidget())
        
        # ドック内のウィジェット
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)  # 余白

        # ウィジェットの背景色
        widget.setStyleSheet("""
            QWidget {
                background-color: #070707;
            }
        """)
        
        # エラーメッセージ用のラベル
        self.error_label = QLabel()
        self.error_label.setStyleSheet("""
            QLabel {
                color: #d32f2f;
                font-size: 12px;
                padding: 2px;
            }
        """)

        # クリアボタン
        self.clear_button = ClearButton()
        self.clear_button.clicked.connect(self.clear_error)
        
        # レイアウトにウィジェットを追加
        layout.addWidget(self.error_label, stretch=1)  # エラーラベルを伸縮可能に
        layout.addWidget(self.clear_button, alignment=Qt.AlignRight)
        
        self.setWidget(widget)
        self.setMaximumHeight(20)  # ドックの高さを制限
        self.setMinimumHeight(20)  # ドックの高さを制限
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
    def show_error(self, message):
        """エラーメッセージを表示"""
        self.error_label.setText(message)
        self.clear_button.show()
        self.show()
        
    def clear_error(self):
        """エラーメッセージをクリア"""
        self.error_label.clear()
        self.clear_button.hide()
        #self.hide()

"""エラーテキスト削除ボタンクラス"""
class ClearButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__("×", parent)
        self.setStyleSheet("""
            QPushButton {
                color: #888888;
                background-color: transparent;
                border: none;
                padding: 0px 0px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #ff6b6b;
            }
        """)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedSize(17, 17)
        self.hide()  # 初期状態では非表示