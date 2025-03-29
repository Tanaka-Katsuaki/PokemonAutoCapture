from enum import Enum, auto
from typing import Dict, Tuple

class GameScene(str, Enum):
    # 初期状態
    OTHER_SCENE = "OTHER_SCENE"                     # バトルスタジアムに入っていない状態

    # 対戦準備画面
    BATTLE_STADIUM_CASUAL_MATCH = "BATTLE_STADIUM_CASUAL_MATCH"     # カジュアルマッチセレクト状態
    BATTLE_STADIUM_RANKED_MATCH = "BATTLE_STADIUM_RANKED_MATCH"     # ランクマッチセレクト状態

    ROLE_SINGLE = "ROLE_SINGLE"     # シングルルール選択状態
    ROLE_DOUBLE = "ROLE_DOUBLE"     # ダブルルール選択状態

    TEAM_SELECT = "TEAM_SELECT"     # バトルチーム選択画面

    # メインシーン
    MATCHING_WAIT = "MATCHING_WAIT"                 # マッチング待機
    POKEMON_SELECT = "POKEMON_SELECT"               # 選出画面
    OPPONENT_SELECT_WAIT = "OPPONENT_SELECT_WAIT"   # 対戦相手待機
    VERSUS = "VERSUS"                               # VS画面
    BATTLE = "BATTLE"                               # 対戦
    RESULT = "RESULT"                               # 勝敗
    RESULT_WIN = "RESULT_WIN"                       # 勝利画面
    RESULT_LOSE = "RESULT_LOSE"                     # 敗北画面
    REWARD = "REWARD"                               # 報酬
    RANKING = "RANKING"                             # 順位

    # バトルサブシーン
    BATTLE_SELECT = "BATTLE_SELECT"         # 選択画面
    BATTLE_WAITING = "BATTLE_WAITING"       # 相手選択待機
    BATTLE_ACTION = "BATTLE_ACTION"         # ターン行動中

    # 選択画面のサブシーン
    BATTLE_SELECT_MOVE = "BATTLE_SELECT_MOVE"       # 技選択
    BATTLE_SELECT_SWITCH = "BATTLE_SELECT_SWITCH"   # 交代選択
    BATTLE_SELECT_RUN = "BATTLE_SELECT_RUN"        # にげる

# シーンの階層構造を定義
SCENE_HIERARCHY = {
    GameScene.BATTLE: {
        "sub_scenes": [
            GameScene.BATTLE_SELECT,
            GameScene.BATTLE_WAITING,
            GameScene.BATTLE_ACTION
        ]
    },
    GameScene.BATTLE_SELECT: {
        "sub_scenes": [
            GameScene.BATTLE_SELECT_MOVE,
            GameScene.BATTLE_SELECT_SWITCH,
            GameScene.BATTLE_SELECT_RUN
        ]
    }
}

""""""

class ScenePriority:
    """シーンの優先度を管理するクラス"""
    
    def __init__(self):
        # シーンの優先順位を定義 (数値が小さいほど優先度が高い)
        self.priorities = {
            GameScene.BATTLE: 1,                            # バトル中が最優先
            GameScene.RESULT_WIN: 2,                        # リザルト画面(勝利)
            GameScene.RESULT_LOSE: 2,                       # リザルト画面(敗北)
            GameScene.VERSUS: 3,                            # VS画面は比較的誤検知が少ない
            # GameScene.RESULT: 2,                          # 結果画面
            GameScene.OPPONENT_SELECT_WAIT: 4,              # 対戦相手待機
            GameScene.POKEMON_SELECT: 5,                    # 選出画面
            GameScene.MATCHING_WAIT: 6,                     # マッチング待機
            GameScene.TEAM_SELECT: 7,                       # チーム選択
            GameScene.ROLE_SINGLE: 8,                       # ルール選択(シングル)
            GameScene.ROLE_DOUBLE: 8,                       # ルール選択(ダブル)
            GameScene.BATTLE_STADIUM_CASUAL_MATCH: 9,       # バトルスタジアム画面(カジュアル)
            GameScene.BATTLE_STADIUM_RANKED_MATCH: 9,       # バトルスタジアム画面(ランク)
            GameScene.RANKING: 10,                           # ランキング画面
            GameScene.REWARD: 11,                            # 報酬画面
            GameScene.OTHER_SCENE: 12,                       # その他のシーン（最も優先度が低い）
        }

""""""
import cv2
import cupy as cp
import numpy as np
from dataclasses import dataclass

@dataclass
class Region:
    """比較する領域を定義するクラス"""
    x: int       # 領域の左端のX座標
    y: int       # 領域の下端のY座標
    width: int   # 領域の幅
    height: int  # 領域の高さ

class SceneRecognizer:
    """映像とシーン画像との一致度を計算するクラス"""
    scene_priority = ScenePriority()
    # 現在のシーン(初期化)
    current_scene = GameScene.OTHER_SCENE

    # 参照画像の読み込み (モノクロ)
    ref_images = {
            'other_scene': cv2.imread("img/Scene Recognition/00_Other_Scene.jpg", cv2.IMREAD_GRAYSCALE),
            'battle_stadium_casual': cv2.imread("img/Scene Recognition/01_Battle_Stadium_Scene_Casual.jpg", cv2.IMREAD_GRAYSCALE),
            'battle_stadium_ranked': cv2.imread("img/Scene Recognition/01_Battle_Stadium_Scene_Ranked.jpg", cv2.IMREAD_GRAYSCALE),
            'role_single': cv2.imread("img/Scene Recognition/02_Role_Scene_Single.jpg", cv2.IMREAD_GRAYSCALE),
            'role_double': cv2.imread("img/Scene Recognition/02_Role_Scene_Double.jpg", cv2.IMREAD_GRAYSCALE),
            'team_select': cv2.imread("img/Scene Recognition/03_Select_Team_Scene.jpg", cv2.IMREAD_GRAYSCALE),
            'matching_wait': cv2.imread("img/Scene Recognition/04_Matching_Wait_Scene.jpg", cv2.IMREAD_GRAYSCALE),
            'pokemon_select': cv2.imread("img/Scene Recognition/05_Pokemon_Select_Scene.jpg", cv2.IMREAD_GRAYSCALE),
            'opponent_select_wait': cv2.imread("img/Scene Recognition/06_Opponent_Select_Wait_Scene.jpg", cv2.IMREAD_GRAYSCALE),
            'versus': cv2.imread("img/Scene Recognition/07_Versus_Scene.jpg", cv2.IMREAD_GRAYSCALE),
            'result': cv2.imread("img/Scene Recognition/08_Result_Scene.jpg", cv2.IMREAD_GRAYSCALE),
            'result_win': cv2.imread("img/Scene Recognition/08_Result_Scene_WIN.jpg", cv2.IMREAD_GRAYSCALE),
            'result_lose': cv2.imread("img/Scene Recognition/08_Result_Scene_LOSE.jpg", cv2.IMREAD_GRAYSCALE),
            'reward': cv2.imread("img/Scene Recognition/09_Reward_Scene.jpg", cv2.IMREAD_GRAYSCALE),
            'ranking': cv2.imread("img/Scene Recognition/10_Ranking_Scene.jpg", cv2.IMREAD_GRAYSCALE),
        }
    
    # 各画像の比較領域を定義
    regions = {
        'other_scene': (223, 790, 284, 43),
        'battle_stadium_casual': (110, 186, 634, 138),
        'battle_stadium_ranked': (209, 344, 501, 129),
        'role_single': (862, 928, 25, 30),
        'role_double': (862, 928, 25, 30),
        'team_select': (1527, 988, 172, 51),
        'matching_wait': (796, 806, 312, 55),
        'pokemon_select': (1351, 869, 128, 41),
        'opponent_select_wait': (445, 870, 119, 39),
        'versus': (869, 483, 192, 116),
        'result': (195, 204, 6, 73),
        'result_win': (431, 913, 318, 127),
        'result_lose': (485, 927, 274, 103),
        'reward': (554, 870, 209, 50),
        'ranking': (710, 793, 319, 70),
    }
      
    @staticmethod
    def calculate_match_score(frame, ref_name):
        """
        映像の各領域をOpenCVでシーン判定画像と比較

        Args:
        - frame (numpy): キャプチャーした映像
        - ref_name (str): 比較するシーンの名称

        Return:
        np.max() (float): 複数による画像比較による一致度の最大値
        """
        if frame is None:
            print("映像がありません")
            return 0.0
        
        if ref_name not in SceneRecognizer.ref_images:
            print("指定されたシーン名がありません")
            return 0.0
            
        x, y, w, h = SceneRecognizer.regions[ref_name]
        
        # フレームをグレースケールに変換して比較領域を抽出
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        roi = gray_frame[y:y+h, x:x+w]

        if roi is None:
            print("切り取り領域が0です")
            return 0.0
        
        if roi.shape[0] == 0 or roi.shape[1] == 0:
            print("切り取り領域が0です")
            return 0.0
            
        ref_roi = SceneRecognizer.ref_images[ref_name]

        if ref_roi is None:
            print("切り取り領域がありません")
            return 0.0
        
        # サイズ調整が必要な場合
        if roi.shape != ref_roi.shape:
            # ref_roi = cv2.resize(ref_roi, (roi.shape[1], roi.shape[0]))
            print("比較領域のサイズが一致していません")
            return 0.0
        
        # ヒストグラム比較やテンプレートマッチングで比較
        result = cv2.matchTemplate(roi, ref_roi, cv2.TM_CCOEFF_NORMED)
        return np.max(result)
    
    @staticmethod
    def get_current_scene(scores: Dict[GameScene, float], threshold: float = 0.8) -> Tuple[GameScene, float]:
        """
        しきい値を超えたシーンの中から、優先度が最も高いシーンを選択する
        
        Args:
            scores: 各シーンの一致度を格納した辞書
            threshold: シーン判定のしきい値
            
        Returns:
            選択されたシーンとそのスコアのタプル
        """
        # しきい値を超えたシーンをフィルタリング
        valid_scenes = {
            scene: score for scene, score in scores.items() 
            if score > threshold
        }
        
        if not valid_scenes:
            return GameScene.OTHER_SCENE, 0.0
            
        # しきい値を超えた中から優先度が最も高い（数値が最も小さい）シーンを選択
        selected_scene = min(
            valid_scenes.items(),
            key=lambda x: (SceneRecognizer.scene_priority.priorities[x[0]], -x[1])  # 優先度が同じ場合はスコアが高い方を選択
        )
        
        return selected_scene
    
    @staticmethod
    def current_scene_recognition(frame):
        """
        現在のシーンを認識

        Args:
        - frame (cupy): キャプチャーした画面
        """
        if frame is None:
            return
            
        # 前処理でフレームをNumPy配列に変換
        if isinstance(frame, cp.ndarray):
            frame = cp.asnumpy(frame)
            
        # 各シーンとの一致度を計算
        scores = {
            GameScene.OTHER_SCENE: SceneRecognizer.calculate_match_score(frame, 'other_scene'),
            GameScene.BATTLE_STADIUM_CASUAL_MATCH: SceneRecognizer.calculate_match_score(frame, 'battle_stadium_casual'),
            GameScene.BATTLE_STADIUM_RANKED_MATCH: SceneRecognizer.calculate_match_score(frame, 'battle_stadium_ranked'),
            GameScene.ROLE_SINGLE: SceneRecognizer.calculate_match_score(frame, 'role_single'),
            GameScene.ROLE_DOUBLE: SceneRecognizer.calculate_match_score(frame, 'role_double'),
            GameScene.TEAM_SELECT: SceneRecognizer.calculate_match_score(frame, 'team_select'),
            GameScene.MATCHING_WAIT: SceneRecognizer.calculate_match_score(frame, 'matching_wait'),
            GameScene.POKEMON_SELECT: SceneRecognizer.calculate_match_score(frame, 'pokemon_select'),
            GameScene.OPPONENT_SELECT_WAIT: SceneRecognizer.calculate_match_score(frame, 'opponent_select_wait'),
            GameScene.VERSUS: SceneRecognizer.calculate_match_score(frame, 'versus'),
            # GameScene.RESULT: SceneRecognizer.calculate_match_score(frame, 'result'),
            GameScene.RESULT_WIN: SceneRecognizer.calculate_match_score(frame, 'result_win'),
            GameScene.RESULT_LOSE: SceneRecognizer.calculate_match_score(frame, 'result_lose'),
            GameScene.REWARD: SceneRecognizer.calculate_match_score(frame, 'reward'),
            GameScene.RANKING: SceneRecognizer.calculate_match_score(frame, 'ranking'),
        }
        
        # 優先度を考慮してシーンを選択
        SceneRecognizer.current_scene, _ = SceneRecognizer.get_current_scene(scores)