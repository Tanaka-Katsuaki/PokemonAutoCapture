import numpy as np
from pygrabber.dshow_graph import FilterGraph

from gui_process.graphic_widget import MainGraphicWidget
from PyQt5.QtWidgets import (QMainWindow, QDockWidget, QWidget,
                              QVBoxLayout, QHBoxLayout, QAction, QLabel, QPushButton, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtGui import QCursor
""""""
from initialize_splash import SplashScreen
from data_config import DataConfigClass
from gui_process.audio_manager import AudioManager
from gui_widget.overlay_widget import OverlayWidget

"""メインウィンドウ"""
class MainWindow(QMainWindow):
    
    def __init__(self, splash:SplashScreen=None):
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

        # overlay_widgetを最初にNoneで初期化
        self.overlay_widget = None              
        
        SplashScreen.update_message("グラフィック初期化中...")
        """グラフィック"""
        self.central_widget = MainGraphicWidget(self) # ゲーム映像
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)

        SplashScreen.update_message("バトルデータ表示ウィンドウ初期化中...")
        """ポケモンバトルデータ表示オーバーレイ"""
        self.overlay_widget = OverlayWidget(self)     

        SplashScreen.update_message("オーディオ初期化中...")
        """オーディオ"""
        self.audio_capture = AudioManager()
        self.audio_input_index = None # 初期入力デバイス
        self.audio_output_index = None # 初期出力デバイスデバイス

        SplashScreen.update_message("オプション初期化中...")
        """オプションUI"""
        # メニューバー作成
        self.camera_actions:    list[QAction] = []  # 入力映像デバイス一覧
        self.audio_actions:     list[QAction] = []  # 入力音声デバイス一覧
        self.volume_actions:    list[QAction] = []  # ボリューム調整用選択肢
        self.hardware_actions:  list[QAction] = []  # ハードウェア選択
        self.option_actions:    list[QAction] = []  # オプション
        self.create_menubar()
        # エラー表示用ドック
        self.error_dock = ErrorDock(self)
        self.error_dock.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.error_dock)
        # パーティー表示ドック(グラフィックWidgetの子要素)
        self.my_party_dock = self.central_widget.get_my_party_dock()
        self.opponent_party_dock = self.central_widget.get_opponent_party_dock()
        self.addDockWidget(Qt.LeftDockWidgetArea, self.my_party_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.opponent_party_dock)
        # オーバーレイウィジェットの表示シグナル(args: pokemon_name)
        self.my_party_dock.show_overlay_widget_signal.connect(self.showOverlay)
        self.opponent_party_dock.show_overlay_widget_signal.connect(self.showOverlay)
        

        # エラー表示用
        self.central_widget.error_signal.connect(self.show_error)       # MainGraphicWidget内でのエラー発生時
        self.audio_capture.error_signal.connect(self.show_error)        # AudioManager内でのエラー発生時
    

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
            self.volume_actions[DataConfigClass.volume//20].trigger()

            # Switch/Switch2の切り替えメニュー
            self.hardware_menu = self.menubar.addMenu('使用ハード')
            self.set_hardware_menu()
            self.hardware_menu.addActions(self.hardware_actions)

            # その他オプション
            self.option_menu = self.menubar.addMenu('オプション')
            self.set_option_menu()
            self.option_menu.addActions(self.option_actions)
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

        def set_volume(volume):
            """
            ボリュームメニューは選択中の音量にチェックマークが付くように

            Args:
            volume (int): 音量の大きさ
            """
            for vol_action in self.volume_actions:
                vol_action.setChecked(False)
            
            selected_action = self.sender()
            if selected_action:
                selected_action.setChecked(True)
            
            DataConfigClass.volume = volume     # 現在のボリュームを保存
            self.audio_capture.set_volume(volume)

        for i in range(0, 11, 1):
            volume = i * 20
            self.volume_actions.append(QAction(f'{volume}%'))
            self.volume_actions[-1].setCheckable(True)
            self.volume_actions[-1].triggered.connect(lambda _, vol=volume: set_volume(vol))

    def set_hardware_menu(self):
        """
        使用ハードがSwitch/Switch2かを切り替える
        それぞれで画面出力の色がわずかに異なり画面遷移判定のために区別が必要なため
        """
        # メニュー項目のセット
        self.hardware_actions.append(QAction('Switch'))
        self.hardware_actions.append(QAction('Switch2'))

        def set_hardware(idx:int):
            """
            ハードウェア選択切り替え処理関数

            Args:
            - idx (int): ハードウェア識別用のindex(Switch: 0, Switch2: 1)
            """
            # 現在の項目からチェックを外す
            self.hardware_actions[DataConfigClass.hardware_index].setChecked(False)
            # 設定を切り替えて項目にチェックを付ける
            DataConfigClass.hardware_index = idx
            self.hardware_actions[DataConfigClass.hardware_index].setChecked(True)
        
        # チェックマーク表示を可能にして選択時の処理をセット
        for i in range(len(self.hardware_actions)):
            self.hardware_actions[i].setCheckable(True)
            self.hardware_actions[i].triggered.connect(lambda _, idx=i: set_hardware(idx))

        # デフォルト項目にチェック
        self.hardware_actions[DataConfigClass.hardware_index].setChecked(True)

    def set_option_menu(self):
        """
        その他の項目用のメニュー
        """

        # FPSの表示非表示の切り替え
        self.option_actions.append(QAction('FPS表示'))
        fps_toggle_index = len(self.option_actions) - 1
        self.option_actions[-1].setCheckable(True)
        def toggle_fps_dispaly(idx):
            """
            FPS表示フラグの切り替え
            Args:
            - idx: opetion_actionsにおけるFPS表示切り替え項目のindex
            """
            DataConfigClass.is_fps_display = not DataConfigClass.is_fps_display
            self.option_actions[idx].setChecked(DataConfigClass.is_fps_display)
        self.option_actions[-1].triggered.connect(lambda _, idx=fps_toggle_index: toggle_fps_dispaly(idx))
        self.option_actions[-1].setChecked(DataConfigClass.is_fps_display)

    """"""""""""

    def _calculate_overlay_geometry(self):
        """オーバーレイのジオメトリを計算する"""
        # OpenGLウィジェットのグローバル座標とサイズを取得
        opengl_global_pos = self.central_widget.mapToGlobal(self.central_widget.rect().topLeft())
        opengl_size = self.central_widget.size()

        # オーバーレイのサイズを計算（OpenGLエリアの95%を使用）
        max_width = int(opengl_size.width() * 0.95)
        max_height = int(opengl_size.height() * 0.95)

        if max_width / 5 * 3 <= max_height:
            overlay_width = max_width
            overlay_height = int(max_width * 3 / 5)
        else:
            overlay_height = max_height
            overlay_width = int(max_height * 5 / 3)

        # OpenGLエリアの中央に配置
        x = opengl_global_pos.x() + (opengl_size.width() - overlay_width) // 2
        y = opengl_global_pos.y() + (opengl_size.height() - overlay_height) // 2

        return x, y, overlay_width, overlay_height

    # オーバーレイウィジェットの表示
    def showOverlay(self, pokemon_name=None):
        """
        オーバーレイウィジェットの表示（独立ウィンドウとして）

        Args:
        - pokemon_name (str): 表示するポケモンの名前
        """
        if not self.overlay_widget:
            # 親をNoneにして独立したウィンドウとして作成
            self.overlay_widget = OverlayWidget()
            # オーバーレイを閉じるシグナルがあれば接続
            if hasattr(self.overlay_widget, 'close_requested'):
                self.overlay_widget.close_requested.connect(self.hideOverlay)

        # ジオメトリを計算
        x, y, overlay_width, overlay_height = self._calculate_overlay_geometry()

        # 表示前に完全にジオメトリを設定（一瞬のサイズ違いを防ぐ）
        self.overlay_widget.setGeometry(x, y, overlay_width, overlay_height)
        self.overlay_widget.resize(overlay_width, overlay_height)
        
        # ポケモンデータを設定（表示前に）
        if pokemon_name:
            self.overlay_widget.set_pokemon(pokemon_name)

        # サイズ調整を表示前に実行
        self.overlay_widget.adjustSizes(overlay_width, overlay_height)
        
        # オーバーレイが「表示されるべき状態」であることをマーク
        self.overlay_widget._should_be_visible = True
        
        # 全ての準備が完了してからオーバーレイを表示
        self.overlay_widget.show()
        self.overlay_widget.raise_()
        self.overlay_widget.activateWindow()

        # QTimerによるフォーカス監視は不要（event()メソッドで自動検知）

    def hideOverlay(self):
        """オーバーレイウィジェットの非表示"""
        if self.overlay_widget:
            # オーバーレイが「表示されるべきでない状態」であることをマーク
            self.overlay_widget._should_be_visible = False
            self.overlay_widget.hide()
            
        # QTimerによるフォーカス監視は不要

    def resizeOverlay(self):
        """
        オーバーレイウィジェットのサイズ更新
        """
        if (not hasattr(self, 'overlay_widget') or 
            not self.overlay_widget or 
            not self.overlay_widget.isVisible()):
            return
            
        # ジオメトリを計算
        x, y, overlay_width, overlay_height = self._calculate_overlay_geometry()

        # オーバーレイの位置とサイズを設定
        self.overlay_widget.setGeometry(x, y, overlay_width, overlay_height)
        
        # リサイズ失敗時の処理
        if self.overlay_widget.width() != overlay_width and self.overlay_widget.height() != overlay_height:
            QTimer.singleShot(100, lambda: self.re_resizeOverlay(x, y, overlay_width, overlay_height))

        #print(f"width: {overlay_width}, height: {overlay_height}")
        #print(f"geometry: {self.overlay_widget.geometry()}")
        
        # サイズ調整
        self.overlay_widget.adjustSizes(overlay_width, overlay_height)

    def re_resizeOverlay(self, x, y, overlay_width, overlay_height):
        """
        リサイズ失敗した際にもう一度OverlayWidgetのみリサイズするための関数

        Args:
        - x (int): OverlayWidget左上のx座標
        - y (int): OverlayWidget左上のy座標
        - overlay_width (int): OverlayWidgetの横幅
        - overlay_height (int): OverlayWidgetの高さ
        """
        if (not hasattr(self, 'overlay_widget') or 
            not self.overlay_widget or 
            not self.overlay_widget.isVisible()):
            return
        # オーバーレイの位置とサイズを設定
        self.overlay_widget.setGeometry(x, y, overlay_width, overlay_height)

    # エラー表示
    def show_error(self, error):
        error_message = str(error)
        self.error_dock.show_error(error_message)

    """オーバーライド関数"""
    def showEvent(self, event):
        super().showEvent(event)

    def resizeEvent(self, event):
        """
        ウィンドウサイズ変更時に呼び出される関数
        """
        super().resizeEvent(event)

        # 各種画像をウィンドウサイズに合わせて調整
        height = self.centralWidget().height() - self.error_dock.height()
        self.my_party_dock.setFixedWidth(height // 6)
        self.opponent_party_dock.setFixedWidth(height // 6)       
        QTimer.singleShot(100, lambda: self.my_party_dock.resize_party_icon(height))
        QTimer.singleShot(100, lambda: self.opponent_party_dock.resize_party_icon(height))

        # オーバーレイウィジェットの位置更新
        if (hasattr(self, 'overlay_widget') and 
            self.overlay_widget and 
            self.overlay_widget.isVisible()):
            # 少し遅延してから位置を更新
            QTimer.singleShot(100, self.resizeOverlay)
       

    def moveEvent(self, event):
        """
        ウィンドウ移動時に呼び出される関数
        """
        super().moveEvent(event)
        
        # オーバーレイが表示されている場合、位置を調整
        if (hasattr(self, 'overlay_widget') and 
            self.overlay_widget and 
            self.overlay_widget.isVisible()):
            QTimer.singleShot(0, self.updateOverlayPosition)

    def updateOverlayPosition(self):
        """
        オーバーレイの位置を更新
        """
        if (hasattr(self, 'overlay_widget') and 
            self.overlay_widget and 
            self.overlay_widget.isVisible()):
            # ジオメトリを再計算
            x, y, overlay_width, overlay_height = self._calculate_overlay_geometry()
            
            # 位置とサイズを両方更新（ウィンドウ移動時もサイズが変わる可能性があるため）
            self.overlay_widget.setGeometry(x, y, overlay_width, overlay_height)
            self.overlay_widget.adjustSizes(overlay_width, overlay_height)

    
    def event(self, event):
        """
        アプリのEvent検知関数
        """
        # アプリのアクティブ/非アクティブを検知
        if event.type() == QEvent.ApplicationActivate:
            # オーバーレイを表示する
            self._on_app_activate()
        elif event.type() == QEvent.ApplicationDeactivate:
            # オーバーレイを非表示にする
            self._on_app_deactivate()
        return super().event(event)

    def _on_app_activate(self):
        """
        ウィンドウがアクティブになったときの処理
        """
        # オーバーレイが存在し、本来表示されるべき状態であれば表示
        if (hasattr(self, 'overlay_widget') and 
            self.overlay_widget and 
            getattr(self.overlay_widget, '_should_be_visible', False)):
            self.overlay_widget.show()
            self.overlay_widget.raise_()

    def _on_app_deactivate(self):
        """
        ウィンドウが非アクティブになったときの処理
        """
        # オーバーレイが表示されている場合のみ隠す（状態フラグは変更しない）
        if (hasattr(self, 'overlay_widget') and 
            self.overlay_widget and 
            self.overlay_widget.isVisible()):
            self.overlay_widget.hide()
        
    def closeEvent(self, event):
        """ウィンドウ終了時に呼び出す"""
        # QTimerによるフォーカス監視は不要
            
        if self.central_widget:
            self.central_widget.closeEvent(event)
        self.audio_capture.stop
        event.accept()

        # 設定の保存
        DataConfigClass.save_setting()
        

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