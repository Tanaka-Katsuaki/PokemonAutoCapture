import pandas as pd
""""""
from initialize_splash import SplashScreen
from create_battle_data import LoadBattleData

"""各種データの読み込み"""
class DataConfigClass:
    """
    - item_data_list (pandas.DataFrame): もちものの名称と画像ファイル名の対応表
    - pokemon_datas (pandas.DataFrame): ポケモンの基礎データ. アイコン推定用のラベルと画像ファイル名も含む
    - battle_datas (pandas.DataFrame): Pokemon HOME APIからのバトルデータ
    """
    SplashScreen.update_message("もちものデータ読み込み中...")
    item_data_list = pd.read_excel("./data/item_list.xlsx")

    # ポケモンの基礎データの読み込み
    try:
        SplashScreen.update_message("ポケモン基礎データ読み込み中...")
        pokemon_datas = pd.read_excel("./data/zukan.xlsx", sheet_name=0)
    except Exception as e:
            e.args = ("ポケモンデータエクセル読み込みエラー: " + e.args[0],)
            print(e.args)

    # バトルデータベースから対戦情報を取得
    try:
        SplashScreen.update_message("バトルデータダウンロード中...")
        battle_datas = LoadBattleData.load_battle_data()
    except Exception as e:
        e.args = ("バトルデータ読み込みエラー: " + e.args[0],)
        print(e.args)
