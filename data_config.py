import os
import datetime
import pandas as pd
from enum import Enum
""""""
from initialize_splash import SplashScreen
from process.create_battle_data import LoadBattleData

# 汎用グラフカラー
SLICES_COLORS = ["#ff4069", "#ff9020", "#ffc234", "#22cfcf", "#059bff", "#8142ff", "#b2b6be"]

"""データ種類の判別用列挙型"""
class GraphDataType(str, Enum):
    MOVE        = "わざ"
    ABILITY     = "とくせい"
    NATURE      = "せいかく"
    ITEM        = "もちもの"
    TERA_TYPE   = "テラスタイプ"
""""""

# ポケモンのタイプごとのRGBカラーを定義
POKEMON_TYPE_COLOR = {
    "ノーマル": (144, 153, 161, 255),
    "ほのお": (255, 156, 84, 255),
    "みず": (78, 144, 214, 255),
    "くさ": (99, 187, 91, 255),
    "でんき": (244, 210, 60, 255),
    "こおり": (115, 206, 192, 255),
    "かくとう": (206, 64, 106, 255),
    "どく": (171, 106, 200, 255),
    "じめん": (217, 119, 69, 255),
    "ひこう": (143, 168, 221, 255),
    "エスパー": (249, 113, 119, 255),
    "むし": (144, 193, 45, 255),
    "いわ": (199, 183, 139, 255),
    "ゴースト": (83, 105, 172, 255),
    "ドラゴン": (10, 109, 196, 255),
    "あく": (90, 83, 102, 255),
    "はがね": (89, 142, 161, 255),
    "フェアリー": (237, 143, 230, 255),
    "ステラ": (192, 165, 238, 255)
}

"""各種データの読み込み"""
class DataConfigClass:
    """
    - item_data_list (pandas.DataFrame): もちものの名称と画像ファイル名の対応表
    - pokemon_datas (pandas.DataFrame): ポケモンの基礎データ. アイコン推定用のラベルと画像ファイル名も含む
    - battle_datas (pandas.DataFrame): Pokemon HOME APIからのバトルデータ
    """
    item_data_list = None
    pokemon_datas = None
    battle_datas = None
    is_battle_data_update = False

    battle_data_file = "./data/battle_data.json"
    
    @staticmethod
    def load_data_config():

        try:
            SplashScreen.update_message("もちものデータ読み込み中...")
            DataConfigClass.item_data_list = pd.read_excel("./data/item_list.xlsx")
        except Exception as e:
            e.args = ("もちものデータエクセル読み込みエラー(data_config.py): " + e.args[0],)
            print(e.args)

        # ポケモンの基礎データの読み込み
        try:
            SplashScreen.update_message("ポケモン基礎データ読み込み中...")
            DataConfigClass.pokemon_datas = pd.read_excel("./data/zukan.xlsx", sheet_name=0)
        except Exception as e:
                e.args = ("ポケモンデータエクセル読み込みエラー(data_config.py): " + e.args[0],)
                print(e.args)

        # バトルデータベースから対戦情報を取得
        try:
            
            if os.path.exists(DataConfigClass.battle_data_file):
                modified_time = os.path.getmtime(DataConfigClass.battle_data_file)
                modified_date = datetime.date.fromtimestamp(modified_time)
                today = datetime.date.today()

                if modified_date == today:
                    SplashScreen.update_message("バトルデータ読み込み中...")
                    DataConfigClass.battle_datas = pd.read_json(DataConfigClass.battle_data_file)
                else:
                    DataConfigClass.download_battle_data()
            else:
                DataConfigClass.download_battle_data()
        except Exception as e:
            e.args = ("バトルデータ読み込みエラー(data_config.py): " + e.args[0],)
            print(e.args)

        # signals.finish_signal.emit()

    @staticmethod
    def save_battle_data():
        DataConfigClass.battle_datas.to_json(DataConfigClass.battle_data_file, orient='records')

    def download_battle_data():
        """Pokemon Home APIからデータを取得"""
        try:
            SplashScreen.update_message("バトルデータダウンロード中...")    
            DataConfigClass.battle_datas = LoadBattleData.load_battle_data()
            DataConfigClass.is_battle_data_update = True
        except:
            """APIから取得できなかった場合最後に保存したjsonファイルのデータを使用"""
            try:
                SplashScreen.update_message("バトルデータ読み込み中...")
                DataConfigClass.battle_datas = pd.read_json(DataConfigClass.battle_data_file)
            except Exception as e:
                e.args = ("バトルデータ読み込みエラー(data_config.py): " + e.args[0],)
                print(e.args)


