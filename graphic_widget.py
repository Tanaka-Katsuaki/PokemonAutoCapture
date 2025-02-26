import numpy as np
import cv2
import time
import threading

import OpenGL.GL as gl
import cupy as cp

from PyQt5.QtCore import Qt, QTimer, QObject, pyqtSignal
import PyQt5.QtOpenGL as QtOpenGL
""""""
from party_pokemon_dock import PartyPokemonsDock
from scene_recognizer import SceneRecognizer, GameScene
from icon_capture import IconCapture

"""映像表示クラス"""
class OpenGLWidget(QtOpenGL.QGLWidget):
    """エラーメッセージ送信"""
    error_signal = pyqtSignal(Exception)

    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        
        # CUDA support (optional)
        try:
            self.CUDA_AVAILABLE = True
        except ImportError:
            self.CUDA_AVAILABLE = False
            print("CUDA unavailable. Falling back to CPU conversion.")
        
        """ゲーム映像キャプチャー変数"""
        self.video_capture = VideoCapture(cuda_available=self.CUDA_AVAILABLE)
        self.video_capture.error_signal.connect(self.error_signal_emit)
        
        self.texture = None
        self.frame = None

        # アスペクト比維持用
        self.ASPECT_RATIO = 16/9
        
        """描画処理用スレッド"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(16)  # ~60 FPS

        """シーン遷移検出用スレッド"""
        self.current_scene = GameScene.OTHER_SCENE
        self.detect_timer = QTimer(self)
        self.detect_timer.timeout.connect(self.scene_recognition)
        self.detect_timer.start(200)  # 0.2秒ごと

        """アイコンキャプチャー用変数"""
        self.next_predict_frame = None              # 画像推測待機用フレーム保持変数
        self.is_predict_running = False             # 現在推論実行中フラグ
        self.is_captured_oppponent_party = False    # 相手パーティがキャプチャー済みかどうか

        """パーティー表示用ドック"""
        self.my_party_dock = PartyPokemonsDock(Qt.LeftDockWidgetArea, main_window)
        self.opponent_party_dock = PartyPokemonsDock(Qt.RightDockWidgetArea, main_window)

    def initializeGL(self):
        """
        ゲーム映像用OpenGLの初期化
        """
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glEnable(gl.GL_TEXTURE_2D)
        
        self.texture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        
        # テクスチャパラメータの詳細設定
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)

    def paintGL(self):
        """
        ゲーム映像描画関数
        """
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        
        if self.frame is not None:
            # CuPy配列の処理
            frame_data = self.frame.get() if self.CUDA_AVAILABLE and hasattr(self.frame, 'get') else self.frame
            
            # テクスチャの再バインドと更新
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
            gl.glTexImage2D(
                gl.GL_TEXTURE_2D, 0, gl.GL_RGB, 
                frame_data.shape[1], frame_data.shape[0], 
                0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, frame_data
            )
            
            # 座標変換を明確に定義
            gl.glMatrixMode(gl.GL_PROJECTION)
            gl.glLoadIdentity()
            gl.glOrtho(-1, 1, -1, 1, -1, 1)
            
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glLoadIdentity()

            # ゲーム画面を16:9をウィンドウサイズによらず維持
            widget_width = self.width()
            widget_height = self.height()
            
            # Calculate scaled dimensions
            if widget_width / widget_height > self.ASPECT_RATIO:
                # Width is too wide, scale based on height
                scaled_width = int(widget_height * self.ASPECT_RATIO)
                scaled_height = widget_height
                x_offset = (widget_width - scaled_width) / 2
                y_offset = 0
            else:
                # Height is too tall, scale based on width
                scaled_width = widget_width
                scaled_height = int(widget_width / self.ASPECT_RATIO)
                x_offset = 0
                y_offset = (widget_height - scaled_height) / 2

            # Normalize coordinates
            norm_x_offset = x_offset / widget_width * 2 - 1
            norm_y_offset = 1 - y_offset / widget_height * 2
            norm_width = scaled_width / widget_width * 2
            norm_height = scaled_height / widget_height * 2
            
            # 映像描画
            gl.glEnable(gl.GL_TEXTURE_2D)
            gl.glBegin(gl.GL_QUADS)
            gl.glTexCoord2f(0, 0); gl.glVertex2f(norm_x_offset, norm_y_offset)
            gl.glTexCoord2f(1, 0); gl.glVertex2f(norm_x_offset + norm_width, norm_y_offset)
            gl.glTexCoord2f(1, 1); gl.glVertex2f(norm_x_offset + norm_width, norm_y_offset - norm_height)
            gl.glTexCoord2f(0, 1); gl.glVertex2f(norm_x_offset, norm_y_offset - norm_height)
            gl.glEnd()
            gl.glDisable(gl.GL_TEXTURE_2D)
        
    def resizeGL(self, width, height):
        """
        Handle widget resize events
        """
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()

    def update_frame(self):
        """
        ゲーム映像描画更新
        """
        new_frame = self.video_capture.read_frame()
        if new_frame is not None:
            self.frame = new_frame
            self.updateGL()

    def scene_recognition(self):
        """
        ゲーム映像の現在のシーン遷移を検出
        """
        current_frame = self.frame.copy()
        SceneRecognizer.current_scene_recognition(current_frame)
        if self.current_scene is not SceneRecognizer.current_scene:
            self.current_scene = SceneRecognizer.current_scene

        try: # 自分のパーティー取得処理

            # バトルチーム選択画面かどうか
            if self.current_scene == GameScene.TEAM_SELECT:
                # バトルチームが選択中で画面中央に存在するか
                if IconCapture.verify_selected_team(current_frame):
                    # チーム選択の変更が行われた後か
                    if IconCapture.is_team_switch:
                        
                        # 現在推論が行われていないなら推論実行
                        if not self.is_predict_running:
                            threading.Thread(target=self.predict_my_party, args=(current_frame,), daemon=True).start()
                            self.next_predict_frame = None      # 最新のフレームで推論してるので念のため空に

                        else: # 推論実行中なら推論待機に現在のフレームを追加
                            self.next_predict_frame = current_frame.copy()
                    
                        # 推論実行したらフラグは戻す
                        IconCapture.is_team_switch = False

                else: # チーム選択の変更が行われたらフラグを立てる
                    IconCapture.is_team_switch = True

                # モデルが推論をしていないかつ推論待機画像があるなら推論実行
                if (self.next_predict_frame is not None) and (not self.is_predict_running):
                    threading.Thread(target=self.predict_my_party, args=(self.next_predict_frame.copy(),), daemon=True).start()
                    self.next_predict_frame = None

            elif self.current_scene == GameScene.POKEMON_SELECT and not self.is_captured_oppponent_party:
                threading.Thread(target=self.predict_opponent_party, daemon=True).start()
                self.is_captured_oppponent_party = True

            elif self.current_scene == GameScene.VERSUS:
                self.is_captured_oppponent_party = False
            
        except Exception as e:
            e.args = ("パーティー取得エラー: " + e.args[0],)
            self.error_signal.emit(e)

        try: # シーン認識確認デバッグ用
            raise RuntimeError(self.current_scene)
        except Exception as e:
            e.args = ("現在のシーン: " + e.args[0],)
            self.error_signal.emit(e)

    def predict_my_party(self, frame):
        """
        映像から自分パーティを認識する

        Args: 
        - frame (cupy): 画像認識を行う映像のフレーム
        """
        # time.sleep(0.05)    # 完全にチームが中央に来るのを待つ
        imgs_cp = IconCapture.capture_my_party(frame)       # 映像からパーティアイコンのトリミング
        if not self.is_predict_running: # 念のため再チェック
            self.is_predict_running = True
            self.my_party_dock.set_pokemon_icon(imgs_cp)        # トリミングされた画像からポケモン推測及び画像表示
            self.is_predict_running = False

    def predict_opponent_party(self):
        """
        映像から相手パーティを認識する
        """
        time.sleep(0.5)   # 念のためアイコン読み込みを待つ
        current_frame = self.frame.copy()
        imgs_cp = IconCapture.capture_opponent_party(current_frame)
        if not self.is_predict_running: # 念のため再チェック
            self.is_predict_running = True
            self.opponent_party_dock.set_pokemon_icon(imgs_cp)        # トリミングされた画像からポケモン推測及び画像表示
            self.is_predict_running = False


    def get_my_party_dock(self):
        """
        パーティー表示用ドックをMainWindowクラスに渡す
        """
        return self.my_party_dock
    
    def get_opponent_party_dock(self):
        return self.opponent_party_dock

    def reload_capture(self, device_index=0):
        """
        映像表示デバイス切り替え
        """
        self.video_capture.stop_capture()
        self.video_capture.start_capture(device_index)

    def error_signal_emit(self, error):
        """
        エラーをMainWindowに送信用
        """
        self.error_signal.emit(error)

    def closeEvent(self, event):
        """
        Cleanup on window close
        """
        self.video_capture.stop_capture()
        super().closeEvent(event)


class VideoCapture(QObject):
    error_signal = pyqtSignal(Exception)

    def __init__(self, device_index=0, cuda_available=False):
        """
        Initialize video capture
        """
        super().__init__()
        self.CUDA_AVAILABLE = cuda_available

        self.start_capture(device_index)

        try:
            if not self.cap.isOpened():
                raise RuntimeError("Could not open video capture device")
            
        except Exception as e:
            self.error_signal.emit(e)

    def read_frame(self):
        """
        Read a frame from the capture device
        
        Returns:
            numpy.ndarray or cupy.ndarray: Captured frame
        """
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        # GPU-based color conversion if CUDA available
        if self.CUDA_AVAILABLE:
            gpu_frame = cp.asarray(frame)
            return gpu_frame[:, :, ::-1]  # BGR to RGB
        
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    def start_capture(self, device_index=0):
        try:
            self.cap = cv2.VideoCapture(device_index, cv2.CAP_DSHOW)
            
            # Optimized capture settings
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            self.cap.set(cv2.CAP_PROP_FPS, 60)
        except Exception as e:
            self.error_signal.emit(e)
        
        try:
            if not self.cap.isOpened():
                raise RuntimeError("Could not open video capture device")
        except Exception as e:
            self.error_signal.emit(e)
    
    def stop_capture(self):
        self.cap.release()

    def __del__(self):
        """
        Release capture device
        """
        if hasattr(self, 'cap'):
            self.cap.release()