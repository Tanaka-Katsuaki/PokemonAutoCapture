import os
import numpy as np
import cv2
import time
import threading
from collections import deque
from queue import Queue, Empty
import concurrent.futures

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import OpenGL.GL as gl

from PyQt5.QtCore import Qt, QTimer, QObject, pyqtSignal
from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtGui import QOpenGLVersionProfile, QSurfaceFormat
""""""
from config.data_config import DataConfigClass
from ui.splash import SplashScreen
from ui.streaming.game_timer import GameTimer
from ui.widgets.party_pokemon_dock import PartyPokemonsDock
from core.scene_recognizer import SceneRecognizer, GameScene
from core.icon_capture import IconCapture


class MainGraphicWidget(QOpenGLWidget):
    """最適化された映像表示クラス"""
    error_signal = pyqtSignal(Exception)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # フォーマット設定（初期化後に設定）
        format = QSurfaceFormat()
        format.setVersion(3, 3)  # OpenGL 3.3 Core Profile
        format.setProfile(QSurfaceFormat.CoreProfile)
        format.setSwapBehavior(QSurfaceFormat.DoubleBuffer)
        format.setRenderableType(QSurfaceFormat.OpenGL)
        format.setSwapInterval(1)  # VSync有効化（スムーズな描画のため）
        format.setSamples(0)  # MSAA無効（パフォーマンス優先）
        self.setFormat(format)
        
        SplashScreen.update_message("キャプチャー準備中...")
        
        # ビデオキャプチャー初期化
        self.video_capture = VideoCapture()
        self.video_capture.error_signal.connect(self.error_signal_emit)
        self.video_capture.frame_ready.connect(self.on_frame_ready)
        
        # OpenGL関連変数
        self.texture = None
        self.shader_program = None
        self.overlay_shader_program = None  # オーバーレイ用シェーダー
        self.vao = None
        self.vbo = None
        self.overlay_vao = None
        self.overlay_vbo = None
        self.frame = None
        self.new_frame = None  # 新しいフレーム用
        self.frame_lock = threading.Lock()  # フレーム更新の同期用
        
        # ゲーム映像アスペクト比維持用
        self.ASPECT_RATIO = 16/9
        
        # FPS表示用変数
        self.fps_display_enabled = True
        self.fps_textures = {}
        self.frame_times = deque(maxlen=60)
        self.current_fps = 0.0
        
        # 描画処理用タイマー（最適化）
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_rendering)
        self.timer.start(16)  # 約60FPS
        
        # シーン遷移検出用スレッド
        self.current_scene = GameScene.OTHER_SCENE
        self.detect_timer = QTimer(self)
        self.detect_timer.timeout.connect(self.scene_recognition)
        self.detect_timer.start(200)
        
        # ポケモンアイコンキャプチャー用変数
        self.next_predict_frame = None
        self.is_predict_running = False
        self.is_check_my_party_running = False
        self.is_captured_oppponent_party = False
        
        # 並列処理用
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self.processing_future = None
        self.last_process_time = 0
        self.is_shutting_down = False
        
        # ゲームタイマー初期化
        SplashScreen.update_message("ゲームタイマー初期化中...")
        self.game_timer = GameTimer()
        self.game_timer.timer_updated.connect(self.update_timer_display)
        self.game_timer.timer_visibility_changed.connect(self.set_timer_visibility)
        
        # タイマー表示用変数
        self.timer_visible = False
        self.current_timer_text = self.game_timer.get_remaining_time_str()
        self.timer_textures = {}
        
        SplashScreen.update_message("パーティー表示ドック初期化中...")
        # パーティー表示用ドック
        self.my_party_dock = PartyPokemonsDock(Qt.LeftDockWidgetArea, parent)
        self.opponent_party_dock = PartyPokemonsDock(Qt.RightDockWidgetArea, parent)

    def on_frame_ready(self):
        """新しいフレームが準備できた時の処理"""
        # フレームを取得して保存
        new_frame = self.video_capture.get_latest_frame()
        if new_frame is not None:
            with self.frame_lock:
                self.new_frame = new_frame

    def update_rendering(self):
        """レンダリング更新処理"""
        # 新しいフレームがあれば更新
        with self.frame_lock:
            if self.new_frame is not None:
                self.frame = self.new_frame
                self.new_frame = None
        
        # 描画更新
        self.update()

    # シェーダー作成関数
    def create_shader_program(self):
        """効率的なシェーダープログラムを作成"""
        vertex_shader_source = """
        #version 330 core
        layout (location = 0) in vec2 position;
        layout (location = 1) in vec2 texCoord;
        
        out vec2 TexCoord;
        
        void main()
        {
            gl_Position = vec4(position, 0.0, 1.0);
            TexCoord = texCoord;
        }
        """
        
        fragment_shader_source = """
        #version 330 core
        in vec2 TexCoord;
        out vec4 FragColor;
        
        uniform sampler2D videoTexture;
        
        void main()
        {
            FragColor = texture(videoTexture, TexCoord);
        }
        """
        
        # バーテックスシェーダーコンパイル
        vertex_shader = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vertex_shader, vertex_shader_source)
        gl.glCompileShader(vertex_shader)
        
        # フラグメントシェーダーコンパイル
        fragment_shader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fragment_shader, fragment_shader_source)
        gl.glCompileShader(fragment_shader)
        
        # シェーダープログラム作成とリンク
        shader_program = gl.glCreateProgram()
        gl.glAttachShader(shader_program, vertex_shader)
        gl.glAttachShader(shader_program, fragment_shader)
        gl.glLinkProgram(shader_program)
        
        # シェーダー削除（プログラムにリンク済みなので不要）
        gl.glDeleteShader(vertex_shader)
        gl.glDeleteShader(fragment_shader)
        
        return shader_program

    def create_overlay_shader_program(self):
        """オーバーレイ用シェーダープログラムを作成"""
        vertex_shader_source = """
        #version 330 core
        layout (location = 0) in vec2 position;
        layout (location = 1) in vec2 texCoord;
        
        out vec2 TexCoord;
        
        void main()
        {
            gl_Position = vec4(position, 0.0, 1.0);
            TexCoord = texCoord;
        }
        """
        
        fragment_shader_source = """
        #version 330 core
        in vec2 TexCoord;
        out vec4 FragColor;
        
        uniform sampler2D overlayTexture;
        uniform vec4 color;
        
        void main()
        {
            vec4 texColor = texture(overlayTexture, TexCoord);
            FragColor = texColor * color;
        }
        """
        
        # バーテックスシェーダーコンパイル
        vertex_shader = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vertex_shader, vertex_shader_source)
        gl.glCompileShader(vertex_shader)
        
        # フラグメントシェーダーコンパイル
        fragment_shader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fragment_shader, fragment_shader_source)
        gl.glCompileShader(fragment_shader)
        
        # シェーダープログラム作成とリンク
        shader_program = gl.glCreateProgram()
        gl.glAttachShader(shader_program, vertex_shader)
        gl.glAttachShader(shader_program, fragment_shader)
        gl.glLinkProgram(shader_program)
        
        # シェーダー削除
        gl.glDeleteShader(vertex_shader)
        gl.glDeleteShader(fragment_shader)
        
        return shader_program

    def setup_geometry(self):
        """VAO/VBO設定（現代的なOpenGL）"""
        # 正規化座標系での四角形（フルスクリーン）
        vertices = np.array([
            # 位置      テクスチャ座標
            -1.0, -1.0,  0.0, 1.0,  # 左下
             1.0, -1.0,  1.0, 1.0,  # 右下
             1.0,  1.0,  1.0, 0.0,  # 右上
            -1.0,  1.0,  0.0, 0.0   # 左上
        ], dtype=np.float32)
        
        indices = np.array([
            0, 1, 2,
            2, 3, 0
        ], dtype=np.uint32)
        
        # メインVAO作成
        self.vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self.vao)
        
        # VBO作成
        self.vbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices, gl.GL_STATIC_DRAW)
        
        # EBO作成
        self.ebo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices, gl.GL_STATIC_DRAW)
        
        # 頂点属性設定
        # 位置属性 (location = 0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 4 * 4, None)
        gl.glEnableVertexAttribArray(0)
        
        # テクスチャ座標属性 (location = 1)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 4 * 4, gl.GLvoidp(2 * 4))
        gl.glEnableVertexAttribArray(1)
        
        # オーバーレイ用VAO作成
        self.overlay_vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self.overlay_vao)
        
        self.overlay_vbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.overlay_vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices, gl.GL_DYNAMIC_DRAW)
        
        self.overlay_ebo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.overlay_ebo)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices, gl.GL_STATIC_DRAW)
        
        # 頂点属性設定
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 4 * 4, None)
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 4 * 4, gl.GLvoidp(2 * 4))
        gl.glEnableVertexAttribArray(1)
        
        gl.glBindVertexArray(0)

    def load_fps_textures(self):
        """FPS表示用テクスチャを読み込む"""
        try:
            dir = DataConfigClass.get_resource_path("assets", "images", "splite", "text")
            
            # "FPS:"テキスト画像の読み込み
            fps_text_path = os.path.join(dir, "FPS.png")
            if os.path.exists(fps_text_path):
                fps_img = cv2.imread(fps_text_path, cv2.IMREAD_UNCHANGED)
                if fps_img is not None:
                    if fps_img.shape[2] == 4:
                        fps_img = cv2.cvtColor(fps_img, cv2.COLOR_BGRA2RGBA)
                    
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
            digits_path = os.path.join(dir, "digits.png")
            if os.path.exists(digits_path):
                digits_img = cv2.imread(digits_path, cv2.IMREAD_UNCHANGED)
                if digits_img is not None:
                    if digits_img.shape[2] == 4:
                        digits_img = cv2.cvtColor(digits_img, cv2.COLOR_BGRA2RGBA)
                    
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
            
            self.load_timer_textures()
        
        except Exception as e:
            print(f"FPS用テクスチャ読み込みエラー: {e}")

    def load_timer_textures(self):
        """タイマー表示用テクスチャを読み込む"""
        try:
            dir = DataConfigClass.get_resource_path("assets", "images")
            
            # タイマーアイコン
            timer_icon_path = os.path.join(dir, "UI Icons", "timer_white.png")
            if os.path.exists(timer_icon_path):
                timer_img = cv2.imread(timer_icon_path, cv2.IMREAD_UNCHANGED)
                if timer_img is not None:
                    if timer_img.shape[2] == 4:
                        timer_img = cv2.cvtColor(timer_img, cv2.COLOR_BGRA2RGBA)
                    
                    self.timer_textures['icon'] = gl.glGenTextures(1)
                    gl.glBindTexture(gl.GL_TEXTURE_2D, self.timer_textures['icon'])
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
                    
                    gl.glTexImage2D(
                        gl.GL_TEXTURE_2D, 0, gl.GL_RGBA,
                        timer_img.shape[1], timer_img.shape[0],
                        0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, timer_img
                    )
            
            # コロン用テクスチャ
            colon_path = os.path.join(dir, "splite", "text", "colon.png")
            if os.path.exists(colon_path):
                colon_img = cv2.imread(colon_path, cv2.IMREAD_UNCHANGED)
                if colon_img is not None:
                    if colon_img.shape[2] == 4:
                        colon_img = cv2.cvtColor(colon_img, cv2.COLOR_BGRA2RGBA)
                    
                    self.timer_textures['colon'] = gl.glGenTextures(1)
                    gl.glBindTexture(gl.GL_TEXTURE_2D, self.timer_textures['colon'])
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
                    
                    gl.glTexImage2D(
                        gl.GL_TEXTURE_2D, 0, gl.GL_RGBA,
                        colon_img.shape[1], colon_img.shape[0],
                        0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, colon_img
                    )
        
        except Exception as e:
            print(f"タイマー用テクスチャ読み込みエラー: {e}")

    def calculate_fps(self):
        """FPSを計算する"""
        current_time = time.time()
        self.frame_times.append(current_time)
        
        if len(self.frame_times) >= 2:
            time_span = self.frame_times[-1] - self.frame_times[0]
            if time_span > 0:
                self.current_fps = (len(self.frame_times) - 1) / time_span

    def initializeGL(self):
        """OpenGL初期化（最適化版）"""
        # OpenGL設定
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glDisable(gl.GL_DEPTH_TEST)  # 2D描画なのでデプステスト不要
        gl.glDisable(gl.GL_CULL_FACE)   # カリング不要
        
        # シェーダープログラム作成
        self.shader_program = self.create_shader_program()
        self.overlay_shader_program = self.create_overlay_shader_program()
        
        # ジオメトリ設定
        self.setup_geometry()
        
        # メインテクスチャ作成（ゲーム映像用）
        self.texture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        
        # テクスチャパラメータ設定（最適化）
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        
        # テクスチャメモリ事前確保（1920x1080 RGB）
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D, 0, gl.GL_RGB8,
            1920, 1080, 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, None
        )
        
        # FPS表示用テクスチャ読み込み
        self.load_fps_textures()

    def paintGL(self):
        """描画関数（修正版）"""
        # FPS計算
        self.calculate_fps()
        
        # バッファクリア
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        
        if self.frame is not None:
            # メインゲーム映像描画
            gl.glUseProgram(self.shader_program)
            
            # テクスチャ更新
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
            gl.glTexSubImage2D(
                gl.GL_TEXTURE_2D, 0, 0, 0,
                self.frame.shape[1], self.frame.shape[0],
                gl.GL_RGB, gl.GL_UNSIGNED_BYTE, self.frame
            )
            
            # ユニフォーム設定
            texture_location = gl.glGetUniformLocation(self.shader_program, "videoTexture")
            gl.glUniform1i(texture_location, 0)
            
            # アスペクト比維持描画
            self.draw_with_aspect_ratio()
            
            gl.glUseProgram(0)
        
        # UIオーバーレイ描画
        self.draw_fps_display()
        self.draw_timer_display()

    def draw_with_aspect_ratio(self):
        """アスペクト比を維持してゲーム映像を描画"""
        widget_width = self.width()
        widget_height = self.height()
        
        # アスペクト比計算
        if widget_width / widget_height > self.ASPECT_RATIO:
            # 横長なら縦を基準に16:9
            scaled_height = 2.0  # 正規化座標系で全体表示
            scaled_width = scaled_height * self.ASPECT_RATIO * widget_height / widget_width
        else:
            # 縦長なら横を基準に16:9
            scaled_width = 2.0
            scaled_height = scaled_width / self.ASPECT_RATIO * widget_width / widget_height
        
        # 動的頂点データ更新
        vertices = np.array([
            -scaled_width/2, -scaled_height/2,  0.0, 1.0,
             scaled_width/2, -scaled_height/2,  1.0, 1.0,
             scaled_width/2,  scaled_height/2,  1.0, 0.0,
            -scaled_width/2,  scaled_height/2,  0.0, 0.0
        ], dtype=np.float32)
        
        # VBO更新
        gl.glBindVertexArray(self.vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferSubData(gl.GL_ARRAY_BUFFER, 0, vertices)
        
        # 描画
        gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
        
        gl.glBindVertexArray(0)

    def draw_overlay_quad(self, texture_id, x, y, width, height, color=(1.0, 1.0, 1.0, 0.9)):
        """オーバーレイクアッドを描画"""
        # 正規化座標に変換
        widget_width = self.width()
        widget_height = self.height()
        
        x_norm = (x / widget_width) * 2.0 - 1.0
        y_norm = 1.0 - (y / widget_height) * 2.0
        width_norm = (width / widget_width) * 2.0
        height_norm = (height / widget_height) * 2.0
        
        # 頂点データ作成
        vertices = np.array([
            x_norm,               y_norm - height_norm,  0.0, 1.0,  # 左下
            x_norm + width_norm,  y_norm - height_norm,  1.0, 1.0,  # 右下
            x_norm + width_norm,  y_norm,                1.0, 0.0,  # 右上
            x_norm,               y_norm,                0.0, 0.0   # 左上
        ], dtype=np.float32)
        
        # オーバーレイVAO使用
        gl.glBindVertexArray(self.overlay_vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.overlay_vbo)
        gl.glBufferSubData(gl.GL_ARRAY_BUFFER, 0, vertices)
        
        # オーバーレイシェーダー使用
        gl.glUseProgram(self.overlay_shader_program)
        
        # ブレンディング設定
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
        # テクスチャバインド
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
        
        # ユニフォーム設定
        texture_location = gl.glGetUniformLocation(self.overlay_shader_program, "overlayTexture")
        gl.glUniform1i(texture_location, 0)
        
        color_location = gl.glGetUniformLocation(self.overlay_shader_program, "color")
        gl.glUniform4f(color_location, color[0], color[1], color[2], color[3])
        
        # 描画
        gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
        
        # クリーンアップ
        gl.glDisable(gl.GL_BLEND)
        gl.glUseProgram(0)
        gl.glBindVertexArray(0)

    def draw_fps_display(self):
        """FPS表示（Core Profile版）"""
        if not DataConfigClass.is_fps_display or not self.fps_textures:
            return
        
        # 画面サイズを取得
        widget_width = self.width()
        widget_height = self.height()
        
        # 表示位置とサイズを設定（左上角）
        display_scale = min(widget_width, widget_height) / 1080
        text_width = 256 * display_scale * 0.5
        text_height = 64 * display_scale * 0.5
        digit_width = 64 * display_scale * 0.5
        digit_height = 64 * display_scale * 0.5
        
        x_start = 20 * display_scale
        y_start = 20 * display_scale
        
        # "FPS:"テキストを描画
        if 'text' in self.fps_textures:
            self.draw_overlay_quad(
                self.fps_textures['text'],
                x_start, y_start,
                text_width, text_height
            )
        
        # FPS数値を描画
        if 'digits' in self.fps_textures:
            fps_str = f"{int(self.current_fps):02d}"
            x_offset = x_start + text_width + 10 * display_scale
            
            for i, digit_char in enumerate(fps_str):
                digit = int(digit_char)
                
                # 数字テクスチャの該当部分を切り出すためのUV座標を計算
                u_start = digit / 10.0
                u_end = (digit + 1) / 10.0
                
                # 数字用の頂点データを作成（UV座標を調整）
                x_pos = x_offset + i * digit_width
                self.draw_digit_quad(
                    self.fps_textures['digits'],
                    x_pos, y_start,
                    digit_width, digit_height,
                    u_start, u_end
                )

    def draw_digit_quad(self, texture_id, x, y, width, height, u_start, u_end, color=(1.0, 1.0, 1.0, 0.9)):
        """数字用クアッドを描画（UV座標指定版）"""
        # 正規化座標に変換
        widget_width = self.width()
        widget_height = self.height()
        
        x_norm = (x / widget_width) * 2.0 - 1.0
        y_norm = 1.0 - (y / widget_height) * 2.0
        width_norm = (width / widget_width) * 2.0
        height_norm = (height / widget_height) * 2.0
        
        # 頂点データ作成（カスタムUV座標）
        vertices = np.array([
            x_norm,               y_norm - height_norm,  u_start, 1.0,  # 左下
            x_norm + width_norm,  y_norm - height_norm,  u_end,   1.0,  # 右下
            x_norm + width_norm,  y_norm,                u_end,   0.0,  # 右上
            x_norm,               y_norm,                u_start, 0.0   # 左上
        ], dtype=np.float32)
        
        # オーバーレイVAO使用
        gl.glBindVertexArray(self.overlay_vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.overlay_vbo)
        gl.glBufferSubData(gl.GL_ARRAY_BUFFER, 0, vertices)
        
        # オーバーレイシェーダー使用
        gl.glUseProgram(self.overlay_shader_program)
        
        # ブレンディング設定
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
        # テクスチャバインド
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
        
        # ユニフォーム設定
        texture_location = gl.glGetUniformLocation(self.overlay_shader_program, "overlayTexture")
        gl.glUniform1i(texture_location, 0)
        
        color_location = gl.glGetUniformLocation(self.overlay_shader_program, "color")
        gl.glUniform4f(color_location, color[0], color[1], color[2], color[3])
        
        # 描画
        gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
        
        # クリーンアップ
        gl.glDisable(gl.GL_BLEND)
        gl.glUseProgram(0)
        gl.glBindVertexArray(0)

    def draw_timer_display(self):
        """タイマー表示を描画する（Core Profile版）"""
        if not self.timer_visible or not self.timer_textures:
            return
        
        # 画面サイズを取得
        widget_width = self.width()
        widget_height = self.height()
        
        # 表示位置とサイズを設定（右上角）
        display_scale = min(widget_width, widget_height) / 1080
        icon_width = 64 * display_scale * 0.5
        icon_height = 64 * display_scale * 0.5
        digit_width = 64 * display_scale * 0.5
        digit_height = 64 * display_scale * 0.5
        colon_width = 32 * display_scale * 0.5
        
        # 総幅を計算
        total_width = icon_width + (digit_width * 5) + colon_width + (10 * display_scale)
        x_start = widget_width - 20 * display_scale - total_width
        y_start = 20 * display_scale
        
        current_x = x_start
        
        # タイマーアイコンを描画
        if 'icon' in self.timer_textures:
            self.draw_overlay_quad(
                self.timer_textures['icon'],
                current_x, y_start,
                icon_width, icon_height
            )
            current_x += icon_width + 5 * display_scale
        
        # タイマーテキスト（mm:ss）を描画
        if 'digits' in self.fps_textures:
            for i, char in enumerate(self.current_timer_text):
                if char == ':':
                    # コロンを描画
                    if 'colon' in self.timer_textures:
                        self.draw_overlay_quad(
                            self.timer_textures['colon'],
                            current_x, y_start,
                            colon_width, digit_height
                        )
                        current_x += colon_width
                elif char.isdigit():
                    # 数字を描画
                    digit = int(char)
                    u_start = digit / 10.0
                    u_end = (digit + 1) / 10.0
                    
                    self.draw_digit_quad(
                        self.fps_textures['digits'],
                        current_x, y_start,
                        digit_width, digit_height,
                        u_start, u_end
                    )
                    current_x += digit_width

    def resizeGL(self, width, height):
        """リサイズ処理"""
        gl.glViewport(0, 0, width, height)

    def scene_recognition(self):
        """シーン遷移検出（最適化版）"""
        if self.is_shutting_down:
            return
            
        current_time = time.time()
        
        if current_time - self.last_process_time < 0.2:
            return
            
        if self.frame is None:
            return
            
        self.last_process_time = current_time
        
        if hasattr(self.thread_pool, '_shutdown') and self.thread_pool._shutdown:
            return
        
        current_frame = self.frame.copy()
        if self.processing_future is None or self.processing_future.done():
            try:
                self.processing_future = self.thread_pool.submit(self._process_scene_recognition, current_frame)
            except RuntimeError as e:
                if "shutdown" in str(e):
                    self.is_shutting_down = True
                    return
                else:
                    raise

    def _process_scene_recognition(self, frame):
        """
        シーン認識処理（バックグラウンド実行

        Args:
        - frame (ndarray): 現在の映像
        """
        try:
            SceneRecognizer.current_scene_recognition(frame)
            if self.current_scene is not SceneRecognizer.current_scene:
                self.current_scene = SceneRecognizer.current_scene

            self.game_timer.check_scene_transition(self.current_scene)

            match self.current_scene:
                case GameScene.TEAM_SELECT:
                    if not self.is_check_my_party_running:
                        self.is_check_my_party_running = True
                        threading.Thread(target=self.check_battle_team, daemon=True).start()

                case GameScene.POKEMON_SELECT:
                    if self.is_check_my_party_running:
                        self.is_check_my_party_running = False

                    if not self.is_captured_oppponent_party:   
                        threading.Thread(target=self.predict_opponent_party, daemon=True).start()
                        self.is_captured_oppponent_party = True

                case GameScene.VERSUS:
                    if self.is_check_my_party_running:
                        self.is_check_my_party_running = False
                    self.is_captured_oppponent_party = False

                case _:
                    if self.is_check_my_party_running:
                        self.is_check_my_party_running = False
                
        except Exception as e:
            self.error_signal.emit(e)

    def check_battle_team(self):
        """バトルチーム検出処理"""
        while self.is_check_my_party_running and not self.is_shutting_down:
            try:
                if self.is_shutting_down:
                    break
                    
                current_frame = self.frame.copy()
                start_time = time.time()
                
                if IconCapture.verify_selected_team(current_frame):
                    
                    if IconCapture.is_team_switch:
                        
                        if not self.is_predict_running and not self.is_shutting_down:
                            time.sleep(2/30)
                            if not self.is_shutting_down:
                                current_frame = self.frame.copy()
                                threading.Thread(target=self.predict_my_party, args=(current_frame,), daemon=True).start()
                                self.next_predict_frame = None

                        else:
                            time.sleep(2/30)
                            if not self.is_shutting_down and IconCapture.verify_selected_team(self.frame):
                                self.next_predict_frame = self.frame.copy()
                    
                        IconCapture.is_team_switch = False

                else:
                    IconCapture.is_team_switch = True

                if (self.next_predict_frame is not None) and (not self.is_predict_running) and (not self.is_shutting_down):
                    threading.Thread(target=self.predict_my_party, args=(self.next_predict_frame.copy(),), daemon=True).start()
                    self.next_predict_frame = None

                elapsed_time = time.time() - start_time
                sleep_time = max(0, 1/60 - elapsed_time)
                time.sleep(sleep_time)

            except Exception as e:
                if not self.is_shutting_down:
                    e.args = ("パーティー取得エラー: " + str(e.args[0]) if e.args else "パーティー取得エラー",)
                    self.error_signal.emit(e)

    def predict_my_party(self, frame):
        """
        自分パーティ認識

        Args:
        - frame (ndarray): パーティー選択画面の画像
        """
        imgs_cp = IconCapture.capture_my_party(frame)
        if not self.is_predict_running:
            self.is_predict_running = True
            self.my_party_dock.set_pokemon_icon(imgs_cp)
            self.is_predict_running = False

    def predict_opponent_party(self):
        """相手パーティ認識"""
        time.sleep(0.5)
        current_frame = self.frame.copy()
        imgs_cp = IconCapture.capture_opponent_party(current_frame)
        if not self.is_predict_running:
            self.is_predict_running = True
            self.opponent_party_dock.set_pokemon_icon(imgs_cp)
            self.is_predict_running = False

    def get_my_party_dock(self):
        """パーティードック取得"""
        return self.my_party_dock
    
    def get_opponent_party_dock(self):
        return self.opponent_party_dock
    
    # タイマー関係
    def update_timer_display(self, time_str):
        """タイマー表示を更新"""
        self.current_timer_text = time_str

    def set_timer_visibility(self, visible):
        """タイマーの表示/非表示を設定"""
        self.timer_visible = visible
        if not visible:
            self.current_timer_text = self.game_timer.get_remaining_time_str()

    def force_stop_timer(self):
        """タイマーを強制停止"""
        self.game_timer.force_stop_timer()

    def update_timer_setting(self):
        """タイマー設定更新"""
        if not self.timer_visible:
            self.current_timer_text = self.game_timer.get_remaining_time_str()

    def reload_capture(self, device_index=0):
        """映像表示デバイス切り替え"""
        self.video_capture.stop_capture()
        self.video_capture.start_capture(device_index)

    def error_signal_emit(self, error):
        """エラー送信"""
        self.error_signal.emit(error)

    def closeEvent(self, event):
        """クリーンアップ処理"""
        self.is_shutting_down = True
        
        if hasattr(self, 'timer'):
            self.timer.stop()
        if hasattr(self, 'detect_timer'):
            self.detect_timer.stop()
            
        if self.processing_future and not self.processing_future.done():
            try:
                self.processing_future.result(timeout=1.0)
            except concurrent.futures.TimeoutError:
                pass
            except Exception:
                pass
        
        try:
            self.thread_pool.shutdown(wait=False)
        except Exception:
            pass
            
        self.video_capture.stop_capture()
        super().closeEvent(event)


class VideoCapture(QObject):
    """最適化されたビデオキャプチャクラス"""
    error_signal = pyqtSignal(Exception)
    frame_ready = pyqtSignal()

    def __init__(self, device_index=0):
        super().__init__()
        self.device_index = device_index
        
        # フレームバッファ（効率化）
        self.frame_queue = Queue(maxsize=2)  # バッファサイズを削減
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
        """キャプチャを開始（最適化版）"""
        try:
            self.cap = cv2.VideoCapture(device_index, cv2.CAP_DSHOW)
            
            # 最適化された設定
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            self.cap.set(cv2.CAP_PROP_FPS, 60)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 最小バッファ
            
            # フォーマット最適化
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
            
            # キャプチャカード固有設定
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
            self.cap.set(cv2.CAP_PROP_EXPOSURE, -6)
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
            
            if not self.cap.isOpened():
                raise RuntimeError("Could not open video capture device")
                
            self.running = True
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
        except Exception as e:
            self.error_signal.emit(e)

    def _capture_loop(self):
        """キャプチャループ（最適化版）"""
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
            
            # CPU最適化: 直接変換（CuPy不要）
            processed_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # フレームをキューに追加（古いフレームを破棄）
            try:
                # キューが満杯の場合、古いフレームを破棄
                while self.frame_queue.qsize() >= 1:
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
        """最新フレームを取得（最適化版）"""
        try:
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
        """フレーム読み込み（互換性用）"""
        return self.get_latest_frame()
    
    def stop_capture(self):
        """キャプチャを停止"""
        self.running = False
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=1.0)
        if hasattr(self, 'cap'):
            self.cap.release()

    def __del__(self):
        """リソース解放"""
        if hasattr(self, 'cap'):
            self.cap.release()