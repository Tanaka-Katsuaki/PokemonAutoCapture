import time
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, pyqtSlot
""""""
from config.data_config import DataConfigClass
from core.scene_recognizer import GameScene

class GameTimer(QObject):
    """ゲームタイマー管理クラス"""
    timer_updated = pyqtSignal(str)  # タイマー表示用シグナル (mm:ss形式)
    timer_visibility_changed = pyqtSignal(bool)  # タイマー表示/非表示用シグナル
    
    # 内部通信用シグナル（スレッドセーフ）
    _start_timer_signal = pyqtSignal(int)  # duration_minutes
    _stop_timer_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # タイマー関連
        self.is_timer_running = False
        self.start_time = None
        self.duration_seconds = DataConfigClass.timer * 60  # タイマーの時間。timer=分
        self.remaining_time = self.duration_seconds
        
        # 更新用タイマー
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.setInterval(1000)  # 1秒間隔で更新
        
        # 前回のシーン状態（遷移検知用）
        self.previous_scene = GameScene.OTHER_SCENE
        
        # 内部シグナルをスロットに接続
        self._start_timer_signal.connect(self._start_timer_slot)
        self._stop_timer_signal.connect(self._stop_timer_slot)
        
    def check_scene_transition(self, current_scene):
        """
        シーン遷移をチェックしてタイマーの開始/停止を制御
        スレッドセーフ版：シグナルを使用してメインスレッドでタイマー操作
        
        Args:
            current_scene: 現在のゲームシーン
        """
        # 前回と同じシーンなら何もしない
        if self.previous_scene == current_scene:
            return
            
        # VERSUS画面への遷移でタイマー開始
        if (self.previous_scene != GameScene.VERSUS and 
            current_scene == GameScene.VERSUS):
            # シグナルを使ってメインスレッドでタイマー開始
            self._start_timer_signal.emit(DataConfigClass.timer)
            
        # 終了条件のシーンへの遷移でタイマー停止
        elif current_scene in [GameScene.PORTAL, GameScene.RESULT_WIN, GameScene.RESULT_LOSE, GameScene.REWARD,
                              GameScene.RANKING, GameScene.ERROR_SWITCH, GameScene.ERROR_SWITCH2]:
            if self.is_timer_running:
                # シグナルを使ってメインスレッドでタイマー停止
                self._stop_timer_signal.emit()
        
        self.previous_scene = current_scene
    
    @pyqtSlot(int)
    def _start_timer_slot(self, duration_minutes):
        """
        タイマー開始のスロット（メインスレッドで実行）
        """
        self.start_timer(duration_minutes)
    
    @pyqtSlot()
    def _stop_timer_slot(self):
        """
        タイマー停止のスロット（メインスレッドで実行）
        """
        self.stop_timer()
    
    def start_timer(self, duration_minutes=None):
        """
        タイマーを開始
        
        Args:
            duration_minutes: タイマーの長さ（分）、Noneの場合は設定値を使用
        """
        if self.is_timer_running:
            self.stop_timer()
        
        if duration_minutes is None:
            duration_minutes = DataConfigClass.timer
            
        self.duration_seconds = duration_minutes * 60
        self.remaining_time = self.duration_seconds
        self.start_time = time.time()
        self.is_timer_running = True
        
        # 表示開始
        self.timer_visibility_changed.emit(True)
        self.update_timer.start()
        
        # 初回表示更新
        self.update_display()
    
    def stop_timer(self):
        """タイマーを停止"""
        if not self.is_timer_running:
            return
            
        self.is_timer_running = False
        self.update_timer.stop()
        
        # 非表示
        self.timer_visibility_changed.emit(False)
    
    def force_stop_timer(self):
        """強制的にタイマーを停止（ボタン用）"""
        self.stop_timer()
    
    def update_display(self):
        """タイマー表示を更新"""
        if not self.is_timer_running:
            return
            
        # 経過時間を計算
        elapsed = time.time() - self.start_time
        self.remaining_time = max(0, self.duration_seconds - elapsed)
        
        # タイムアップ
        if self.remaining_time <= 0:
            self.stop_timer()
            return
        
        # mm:ss形式で表示
        minutes = int(self.remaining_time // 60)
        seconds = int(self.remaining_time % 60)
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        self.timer_updated.emit(time_str)
    
    def get_remaining_time_str(self):
        """現在の残り時間を文字列で取得"""
        if not self.is_timer_running:
            minutes = DataConfigClass.timer
            seconds = 0
            return f"{minutes:02d}:{seconds:02d}"
            
        minutes = int(self.remaining_time // 60)
        seconds = int(self.remaining_time % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def is_visible(self):
        """タイマーが表示中かどうか"""
        return self.is_timer_running