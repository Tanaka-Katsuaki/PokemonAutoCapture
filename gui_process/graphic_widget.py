import os
import numpy as np
import cv2
import time
import threading
from collections import deque
from queue import Queue, Empty
import concurrent.futures

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # 0: 全て表示, 1: WARNING以上, 2: ERROR以上, 3: FATALのみ
import OpenGL.GL as gl
import cupy as cp

from PyQt5.QtCore import Qt, QTimer, QObject, pyqtSignal
import PyQt5.QtOpenGL as QtOpenGL
""""""
from data_config import DataConfigClass
from gui_widget.party_pokemon_dock import PartyPokemonsDock
from process.scene_recognizer import SceneRecognizer, GameScene
from process.icon_capture import IconCapture

from initialize_splash import SplashScreen

"""映像表示クラス"""
class MainGraphicWidget(QtOpenGL.QGLWidget):
    """エラーメッセージ送信"""
    error_signal = pyqtSignal(Exception)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # CUDA support (optional)
        try:
            self.CUDA_AVAILABLE = True
        except ImportError:
            self.CUDA_AVAILABLE = False
            print("CUDA unavailable. Falling back to CPU conversion.")
        
        SplashScreen.update_message("キャプチャー準備中...")
        """ゲーム映像キャプチャー変数"""
        self.video_capture = VideoCapture(cuda_available=self.CUDA_AVAILABLE)
        self.video_capture.error_signal.connect(self.error_signal_emit)
        self.video_capture.frame_ready.connect(self.on_frame_ready)
        
        self.texture = None
        self.frame = None
        self.pending_frame_update = False

        # ゲーム映像アスペクト比維持用
        self.ASPECT_RATIO = 16/9
        
        # FPS表示用変数
        self.fps_display_enabled = True  # FPS表示のON/OFF
        self.fps_textures = {}           # FPS表示用テクスチャ
        self.frame_times = deque(maxlen=60)  # 過去60フレームの時間を保持
        self.last_fps_time = time.time()
        self.current_fps = 0.0
        
        """描画処理用スレッド"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(16)  # ~60 FPS

        """シーン遷移検出用スレッド"""
        self.current_scene = GameScene.OTHER_SCENE
        self.detect_timer = QTimer(self)
        self.detect_timer.timeout.connect(self.scene_recognition)
        self.detect_timer.start(200)  # 0.2秒ごと（最適化のため頻度を下げる）

        """ポケモンアイコンキャプチャー用変数"""
        self.next_predict_frame = None              # 画像推測待機用フレーム保持変数
        self.is_predict_running = False             # 現在推論実行中フラグ
        self.is_check_my_party_running = False      # バトルチーム確認スレッド実行中フラグ
        self.is_captured_oppponent_party = False    # 相手パーティがキャプチャー済みかどうか

        # 並列処理用
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self.processing_future = None
        self.last_process_time = 0

        SplashScreen.update_message("パーティー表示ドック初期化中...")
        """パーティー表示用ドック"""
        self.my_party_dock = PartyPokemonsDock(Qt.LeftDockWidgetArea, parent)
        self.opponent_party_dock = PartyPokemonsDock(Qt.RightDockWidgetArea, parent)
     
        # オーバーレイ描画追跡用
        self.overlay_regions = []

    def on_frame_ready(self):
        """新しいフレームが準備できた時の処理"""
        self.pending_frame_update = True

    def load_fps_textures(self):
        """FPS表示用テクスチャを読み込む"""
        try:
            # "FPS:"テキスト画像の読み込み
            fps_text_path = "img/splite/text/FPS.png"
            if os.path.exists(fps_text_path):
                fps_img = cv2.imread(fps_text_path, cv2.IMREAD_UNCHANGED)
                if fps_img is not None:
                    # BGRAからRGBAに変換
                    if fps_img.shape[2] == 4:
                        fps_img = cv2.cvtColor(fps_img, cv2.COLOR_BGRA2RGBA)
                    
                    # テクスチャ生成
                    self.fps_textures['text'] = gl.glGenTextures(1)
                    gl.glBindTexture(gl.GL_TEXTURE_2D, self.fps_textures['text'])
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
                    
                    gl.glTexImage2D(
                        gl.GL_TEXTURE_2D, 0, gl.GL_RGBA,
                        fps_img.shape[1], fps_img.shape[0],
                        0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, fps_img
                    )
            
            # 数字画像の読み込み
            digits_path = "img/splite/text/digits.png"
            if os.path.exists(digits_path):
                digits_img = cv2.imread(digits_path, cv2.IMREAD_UNCHANGED)
                if digits_img is not None:
                    # BGRAからRGBAに変換
                    if digits_img.shape[2] == 4:
                        digits_img = cv2.cvtColor(digits_img, cv2.COLOR_BGRA2RGBA)
                    
                    # テクスチャ生成
                    self.fps_textures['digits'] = gl.glGenTextures(1)
                    gl.glBindTexture(gl.GL_TEXTURE_2D, self.fps_textures['digits'])
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
                    
                    gl.glTexImage2D(
                        gl.GL_TEXTURE_2D, 0, gl.GL_RGBA,
                        digits_img.shape[1], digits_img.shape[0],
                        0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, digits_img
                    )
        
        except Exception as e:
            print(f"FPS用テクスチャ読み込みエラー: {e}")

    def calculate_fps(self):
        """FPSを計算する"""
        current_time = time.time()
        self.frame_times.append(current_time)
        
        if len(self.frame_times) >= 2:
            # 過去60フレーム（または利用可能なフレーム）の平均FPSを計算
            time_span = self.frame_times[-1] - self.frame_times[0]
            if time_span > 0:
                self.current_fps = (len(self.frame_times) - 1) / time_span

    def draw_fps_display(self):
        """FPS表示を描画する"""
        if not DataConfigClass.is_fps_display or not self.fps_textures:
            return
        
        # 画面サイズを取得
        widget_width = self.width()
        widget_height = self.height()
        
        # 表示位置とサイズを設定（左上角）
        display_scale = min(widget_width, widget_height) / 1080  # 1080pを基準にスケール
        text_width = 256 * display_scale * 0.5  # FPS:テキストの幅
        text_height = 64 * display_scale * 0.5   # FPS:テキストの高さ
        digit_width = 64 * display_scale * 0.5   # 数字1つの幅
        digit_height = 64 * display_scale * 0.5  # 数字の高さ
        
        # 正規化座標に変換
        x_start = -1.0 + (20 * display_scale) / widget_width * 2  # 左端から20px
        y_start = 1.0 - (20 * display_scale) / widget_height * 2  # 上端から20px
        
        text_norm_width = text_width / widget_width * 2
        text_norm_height = text_height / widget_height * 2
        digit_norm_width = digit_width / widget_width * 2
        digit_norm_height = digit_height / widget_height * 2
        
        # ブレンディングを有効化（透過表示用）
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glEnable(gl.GL_TEXTURE_2D)
        
        # デプステストを一時的に無効化（オーバーレイ表示用）
        gl.glDisable(gl.GL_DEPTH_TEST)
        
        # "FPS:"テキストを描画
        if 'text' in self.fps_textures:
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.fps_textures['text'])
            gl.glColor4f(1.0, 1.0, 1.0, 0.9)  # 少し透明に
            
            gl.glBegin(gl.GL_QUADS)
            gl.glTexCoord2f(0, 0); gl.glVertex2f(x_start, y_start)
            gl.glTexCoord2f(1, 0); gl.glVertex2f(x_start + text_norm_width, y_start)
            gl.glTexCoord2f(1, 1); gl.glVertex2f(x_start + text_norm_width, y_start - text_norm_height)
            gl.glTexCoord2f(0, 1); gl.glVertex2f(x_start, y_start - text_norm_height)
            gl.glEnd()
        
        # FPS数値を描画
        if 'digits' in self.fps_textures:
            fps_str = f"{int(self.current_fps):02d}"  # 2桁で表示
            x_offset = x_start + text_norm_width + (10 * display_scale) / widget_width * 2  # テキストとの間隔
            
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.fps_textures['digits'])
            
            for i, digit_char in enumerate(fps_str):
                digit = int(digit_char)
                
                # UV座標を計算（640x64の画像から64x64の数字を切り出し）
                u_start = digit / 10.0
                u_end = (digit + 1) / 10.0
                
                # 数字を描画
                x_pos = x_offset + i * digit_norm_width
                
                gl.glBegin(gl.GL_QUADS)
                gl.glTexCoord2f(u_start, 0); gl.glVertex2f(x_pos, y_start)
                gl.glTexCoord2f(u_end, 0); gl.glVertex2f(x_pos + digit_norm_width, y_start)
                gl.glTexCoord2f(u_end, 1); gl.glVertex2f(x_pos + digit_norm_width, y_start - digit_norm_height)
                gl.glTexCoord2f(u_start, 1); gl.glVertex2f(x_pos, y_start - digit_norm_height)
                gl.glEnd()
        
        # 設定を元に戻す
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glDisable(gl.GL_BLEND)
        gl.glDisable(gl.GL_TEXTURE_2D)

    def toggle_fps_display(self):
        """FPS表示のON/OFFを切り替える"""
        self.fps_display_enabled = not self.fps_display_enabled

    def initializeGL(self):
        """
        ゲーム映像用OpenGLの初期化
        """
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)  # 完全不透明な黒背景
        gl.glEnable(gl.GL_TEXTURE_2D)
        
        # デプステストを有効にして描画の重なりを適切に処理
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glDepthFunc(gl.GL_LEQUAL)
        
        # ダブルバッファリング設定
        gl.glDrawBuffer(gl.GL_BACK)
        
        self.texture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        
        # テクスチャパラメータの詳細設定
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        
        # テクスチャメモリの事前確保（最適化）
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D, 0, gl.GL_RGB,
            1920, 1080, 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, None
        )
        
        # FPS表示用テクスチャを読み込み
        self.load_fps_textures()

    def paintGL(self):
        """
        ゲーム映像描画関数
        """
        # FPS計算
        self.calculate_fps()
        
        # バッファを完全にクリア（アルファチャンネルは1.0で完全不透明）
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        
        # カラーマスクをRGBのみに設定（アルファは書き込まない）
        gl.glColorMask(gl.GL_TRUE, gl.GL_TRUE, gl.GL_TRUE, gl.GL_FALSE)
        
        if self.frame is not None:
            # CuPy配列の処理
            frame_data = self.frame.get() if self.CUDA_AVAILABLE and hasattr(self.frame, 'get') else self.frame
            
            # テクスチャの再バインドと更新（最適化：サブイメージ更新）
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
            gl.glTexSubImage2D(
                gl.GL_TEXTURE_2D, 0, 0, 0,
                frame_data.shape[1], frame_data.shape[0],
                gl.GL_RGB, gl.GL_UNSIGNED_BYTE, frame_data
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
                # 横長なら縦を基準に16:9
                scaled_width = int(widget_height * self.ASPECT_RATIO)
                scaled_height = widget_height
                x_offset = (widget_width - scaled_width) / 2
                y_offset = 0
            else:
                # 縦長なら横を基準に16:9
                scaled_width = widget_width
                scaled_height = int(widget_width / self.ASPECT_RATIO)
                x_offset = 0
                y_offset = (widget_height - scaled_height) / 2

            # Normalize coordinates
            norm_x_offset = x_offset / widget_width * 2 - 1
            norm_y_offset = 1 - y_offset / widget_height * 2
            norm_width = scaled_width / widget_width * 2
            norm_height = scaled_height / widget_height * 2
            
            # ブレンディングを無効にして映像を描画
            gl.glDisable(gl.GL_BLEND)
            
            # 映像描画（頂点配列使用で最適化）
            gl.glEnable(gl.GL_TEXTURE_2D)
            gl.glColor4f(1.0, 1.0, 1.0, 1.0)  # 完全不透明で描画
            
            vertices = np.array([
                norm_x_offset, norm_y_offset,
                norm_x_offset + norm_width, norm_y_offset,
                norm_x_offset + norm_width, norm_y_offset - norm_height,
                norm_x_offset, norm_y_offset - norm_height
            ], dtype=np.float32)
            
            texcoords = np.array([0, 0, 1, 0, 1, 1, 0, 1], dtype=np.float32)
            
            gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
            gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)
            
            gl.glVertexPointer(2, gl.GL_FLOAT, 0, vertices)
            gl.glTexCoordPointer(2, gl.GL_FLOAT, 0, texcoords)
            
            gl.glDrawArrays(gl.GL_QUADS, 0, 4)
            
            gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
            gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)
            gl.glDisable(gl.GL_TEXTURE_2D)
        
        # FPS表示を描画
        self.draw_fps_display()
        
        # カラーマスクを元に戻す
        gl.glColorMask(gl.GL_TRUE, gl.GL_TRUE, gl.GL_TRUE, gl.GL_TRUE)
        
        # バッファをフラッシュ
        gl.glFlush()
        
    def resizeGL(self, width, height):
        """
        Handle widget resize events
        """
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()

    def clearOverlayArea(self, overlay_rect):
        """
        オーバーレイウィジェットが更新される前に該当領域をクリア
        この関数は削除または簡素化
        """
        # 単純にOpenGLの再描画を強制実行
        self.makeCurrent()
        self.updateGL()

    def update_frame(self):
        """
        ゲーム映像描画更新
        """
        if self.pending_frame_update:
            new_frame = self.video_capture.get_latest_frame()
            if new_frame is not None:
                self.frame = new_frame
                self.pending_frame_update = False
                
        # 常にレンダリングを実行
        self.makeCurrent()
        self.updateGL()

    def scene_recognition(self):
        """
        ゲーム映像の現在のシーン遷移を検出（最適化版）
        """
        current_time = time.time()
        
        # 処理頻度制限（CPU負荷軽減）
        if current_time - self.last_process_time < 0.2:  # 0.2秒に1回
            return
            
        if self.frame is None:
            return
            
        self.last_process_time = current_time
        
        # フレームのコピーを作成して非同期処理
        current_frame = self.frame.copy()
        if self.processing_future is None or self.processing_future.done():
            self.processing_future = self.thread_pool.submit(self._process_scene_recognition, current_frame)

    def _process_scene_recognition(self, frame):
        """シーン認識処理（バックグラウンド実行）"""
        try:
            SceneRecognizer.current_scene_recognition(frame)
            if self.current_scene is not SceneRecognizer.current_scene:
                self.current_scene = SceneRecognizer.current_scene

            # 各シーンで必要な処理
            match self.current_scene:
                # バトルチーム選択画面
                case GameScene.TEAM_SELECT:
                    # バトルチームのアイコンを読み込み推測
                    if not self.is_check_my_party_running:
                        self.is_check_my_party_running = True
                        threading.Thread(target=self.check_battle_team, daemon=True).start()

                # ポケモン選出画面
                case GameScene.POKEMON_SELECT:
                    if self.is_check_my_party_running:
                        self.is_check_my_party_running = False

                    # 相手チームのアイコンを読み込み推測
                    if not self.is_captured_oppponent_party:   
                        threading.Thread(target=self.predict_opponent_party, daemon=True).start()
                        self.is_captured_oppponent_party = True

                # バーサス画面
                case GameScene.VERSUS:
                    if self.is_check_my_party_running:
                        self.is_check_my_party_running = False
                    self.is_captured_oppponent_party = False

                # その他
                case _:
                    if self.is_check_my_party_running:
                        self.is_check_my_party_running = False

            try: # シーン認識確認デバッグ用
                raise RuntimeError(self.current_scene)
            except Exception as e:
                e.args = ("現在のシーン: " + e.args[0],)
                self.error_signal.emit(e)
                
        except Exception as e:
            self.error_signal.emit(e)

    def check_battle_team(self):
        """
        画像からバトルチームの切り替わりの検出とアイコン推論実行を行う
        バトルチーム選択画面で呼び出される
        """
        while self.is_check_my_party_running:
            try:
                current_frame = self.frame.copy()
                start_time = time.time()  # ループ開始時間を記録

                # バトルチームが選択中で画面中央に存在するか
                if IconCapture.verify_selected_team(current_frame):
                    # チーム選択の変更が行われた後か
                    if IconCapture.is_team_switch:
                        
                        # 現在推論が行われていないなら推論実行
                        if not self.is_predict_running:
                            #print("現在の画像を処理")
                            time.sleep(2/30) # 2フレーム待機
                            current_frame = self.frame.copy()
                            threading.Thread(target=self.predict_my_party, args=(current_frame,), daemon=True).start()  
                            self.next_predict_frame = None      # 最新のフレームで推論してるので念のため空に

                        else: # 推論実行中なら推論待機に現在のフレームを追加
                            time.sleep(2/30) # 2フレーム待機
                            if IconCapture.verify_selected_team(self.frame):
                                self.next_predict_frame = self.frame.copy()
                    
                        # 推論実行したらフラグは戻す
                        IconCapture.is_team_switch = False

                else: # バトルチームが中央から動いたらフラグを立てる
                    IconCapture.is_team_switch = True

                # モデルが推論をしていないかつ推論待機画像があるなら推論実行
                if (self.next_predict_frame is not None) and (not self.is_predict_running):
                    #print("待機画像を処理")
                    threading.Thread(target=self.predict_my_party, args=(self.next_predict_frame.copy(),), daemon=True).start()
                    self.next_predict_frame = None

                # 60fpsで処理を回す
                # 経過時間を計算し、次のフレームまで待機
                elapsed_time = time.time() - start_time
                sleep_time = max(0, 1/60 - elapsed_time)  # 負の値にならないように調整
                time.sleep(sleep_time)

            except Exception as e:
                e.args = ("パーティー取得エラー: " + e.args[0],)
                self.error_signal.emit(e)

    def predict_my_party(self, frame):
        """
        画像から自分パーティを認識する

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
        self.thread_pool.shutdown(wait=False)
        super().closeEvent(event)


class VideoCapture(QObject):
    """最適化されたビデオキャプチャクラス"""
    error_signal = pyqtSignal(Exception)
    frame_ready = pyqtSignal()

    def __init__(self, device_index=0, cuda_available=False):
        """
        Initialize video capture
        """
        super().__init__()
        self.CUDA_AVAILABLE = cuda_available
        self.device_index = device_index
        
        # フレームバッファ（トリプルバッファリング）
        self.frame_queue = Queue(maxsize=3)
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        # キャプチャスレッド
        self.capture_thread = None
        self.running = False
        
        # 統計情報
        self.capture_fps = 0
        self.dropped_frames = 0
        
        self.start_capture(device_index)

    def start_capture(self, device_index=0):
        """キャプチャを開始"""
        try:
            self.cap = cv2.VideoCapture(device_index, cv2.CAP_DSHOW)
            
            # より最適化された設定
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            self.cap.set(cv2.CAP_PROP_FPS, 60)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 最小バッファ
            
            # フォーマット最適化
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
            
            if not self.cap.isOpened():
                raise RuntimeError("Could not open video capture device")
                
            self.running = True
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
        except Exception as e:
            self.error_signal.emit(e)

    def _capture_loop(self):
        """専用スレッドでのキャプチャループ"""
        last_time = time.time()
        frame_count = 0
        
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue
                
            # FPS計算
            frame_count += 1
            current_time = time.time()
            if current_time - last_time >= 1.0:
                self.capture_fps = frame_count / (current_time - last_time)
                frame_count = 0
                last_time = current_time
            
            # GPU変換（可能な場合）
            if self.CUDA_AVAILABLE:
                try:
                    gpu_frame = cp.asarray(frame)
                    processed_frame = gpu_frame[:, :, ::-1]  # BGR to RGB
                except:
                    processed_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                processed_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # フレームをキューに追加（古いフレームを破棄）
            try:
                # キューが満杯の場合、古いフレームを破棄
                while self.frame_queue.qsize() >= 2:
                    try:
                        self.frame_queue.get_nowait()
                        self.dropped_frames += 1
                    except Empty:
                        break
                
                self.frame_queue.put_nowait(processed_frame)
                self.frame_ready.emit()
                
            except:
                self.dropped_frames += 1

    def get_latest_frame(self):
        """最新フレームを取得"""
        try:
            # 利用可能な最新フレームを取得
            latest_frame = None
            while not self.frame_queue.empty():
                try:
                    latest_frame = self.frame_queue.get_nowait()
                except Empty:
                    break
            
            if latest_frame is not None:
                with self.frame_lock:
                    self.current_frame = latest_frame
                    
            return self.current_frame
            
        except Exception:
            return self.current_frame

    def read_frame(self):
        """
        Read a frame from the capture device (互換性のため)
        
        Returns:
            numpy.ndarray or cupy.ndarray: Captured frame
        """
        return self.get_latest_frame()
    
    def stop_capture(self):
        """キャプチャを停止"""
        self.running = False
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=1.0)
        if hasattr(self, 'cap'):
            self.cap.release()

    def __del__(self):
        """
        Release capture device
        """
        if hasattr(self, 'cap'):
            self.cap.release()