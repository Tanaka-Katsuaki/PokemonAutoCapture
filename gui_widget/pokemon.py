import os
import cv2
import numpy as np
import cupy as cp
import pandas as pd

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QObject, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer

# os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # 0: 全て表示, 1: WARNING以上, 2: ERROR以上, 3: FATALのみ
from keras.models import load_model
from keras.utils import img_to_array, load_img
""""""
from data_config import DataConfigClass


"""ポケモン画像用クラス"""
class Pokemon(QLabel):
    show_ovelay_widget_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_name = ""

    def set_image_name(self, name):
        self.image_name = name
    
    def mousePressEvent(self, event):
        """
        クリックされた場合にポケモンの情報をPokemonDataDisplayWidget上に表示する
        """
        if event.button() == Qt.LeftButton:
            if self.image_name != "":
                self.show_ovelay_widget_signal.emit(self.image_name)

""""""



"""ポケモンのデータを管理するツール"""
class PokemonData(QObject):
    """画像表示シグナル送信"""
    show_ovelay_widget_signal = pyqtSignal(str)

    """
    ポケモンの背景用画像
        off_icon: 不明 or 未選出時
        on_icon: 選出時

        current_background: 現在の背景アイコンのSVGデータ
        background_icon (QLabel): 現在の背景アイコン用QLabel
    """
    # ポケモン画像のフォルダー
    pokemon_icons_path = "./img/Pokemon_Icons/"
    try:
        __off_icon = QSvgRenderer(pokemon_icons_path + "background.svg")
        __on_icon = None
    except Exception as e:
            e.args = ("背景画像読み込みエラー(pokemon.py): " + e.args[0],)
            print(e.args)

    # ポケモンアイコン推測モデルのロード
    pokemon_icon_model = load_model("./model/pokemon_icon_recognition_model.h5")

    def __init__(self, parent, widget_height):
        """
        Args:
        - widget (QWidget): ポケモンアイコンを保持する親Widget
        - widget_height (int): Widgetの高さ 6等分するために
        - main_window (QMainWindow): 中央にポケモンのデータ表示するために必要な親クラス
        """
        super().__init__(parent)

        # 背景画像初期化
        try:
            self.current_background = PokemonData.__off_icon
            self.background_icon = self.init_background_icon(svg=self.current_background, parent=parent, widget_height=int(widget_height))
        except Exception as e:
            e.args = ("背景画像初期化エラー(pokemon.py): " + e.args[0],)
            print(e.args)

        """
        ポケモンのパラメータ
            pokemon_name: ポケモンの種族名
            pokemon_icon: ポケモンの画像
            item: もちもの情報
            item_icon: もちもの画像
        """
        self.pokemon_icon_num = 0       # ポケモン画像用index
        self.pokemon_name = None        # ポケモンの名前

        self.pokemon_icon = Pokemon(parent)                             # ポケモン画像
        self.pokemon_icon.setScaledContents(True)                       # 画像をラベルサイズに合わせる
        self.pokemon_icon.setAttribute(Qt.WA_TranslucentBackground)     # 背景を透明に
        self.pokemon_icon.show_ovelay_widget_signal.connect(self.show_overlay_widget)   # ポケモン画像がクリックされた場合にオーバーレイウィジェットを表示する用に信号を親に出す

        self.item = None
        self.item_icon = QLabel(parent)       # 持ち物画像


    def set_pokemon(self, label):
        """
        ポケモン画像の読み込み

        Arge:
        - label (int): ポケモン推測ラベル
        """
        # labelが0なら空にする
        if label == 0:
            self.pokemon_icon.setPixmap(QPixmap())
            return
        
        self.pokemon_icon_num = label
        # labelの該当する行のデータを取得
        pokemon_data_row = DataConfigClass.pokemon_datas[DataConfigClass.pokemon_datas["label"] == label]
        # データを取得
        self.pokemon_name = pokemon_data_row["name"]
        
        # 画像データをセット
        image_path = PokemonData.pokemon_icons_path + str(pokemon_data_row["image_file"].iloc[0])
        pokemon_pixmap = QPixmap(image_path)
        self.pokemon_icon.setPixmap(pokemon_pixmap)
        self.pokemon_icon.setGeometry(self.background_icon.geometry())  # 背景画像上に配置
        self.pokemon_icon.set_image_name(pokemon_data_row["alias"].iloc[0])
        
        # 縦横比がおかしい場合
        if self.pokemon_icon.width() != self.pokemon_icon.height():
            size = min(self.pokemon_icon.width(), self.pokemon_icon.height())  # 小さい方のサイズを取得
            self.pokemon_icon.resize(size, size)
            
        self.pokemon_icon.raise_()  # 一番前面に持ってくる


    @staticmethod
    def recognize_pokemon_icon(images):
        """
        画像が何のポケモンアイコンかを推測する

        Args:
        - images[] (cupy): 画像データ配列

        Return:
        - predicted_labels[] (int): 推測される各アイコンの内部画像番号
        """
        predicted_labels = []
        try:
            for img in images:
                # 画像前処理
                # CupyならNumPy に変換
                if isinstance(img, cp.ndarray):
                    img = cp.asnumpy(img)
                resize_img = cv2.resize(img, (85, 85), interpolation=cv2.INTER_LINEAR)
                resize_img  = img_to_array(resize_img) / 255.0  # 正規化
                resize_img  = np.expand_dims(resize_img , axis=0)  # バッチ次元を追加
                # 学習モデルでアイコン推測
                predictions = PokemonData.pokemon_icon_model.predict(resize_img, verbose=0)
                predicted_labels.append( np.argmax(predictions, axis=1)[0] ) # 最も確率が高いラベルを取得
        except Exception as e:
            predicted_labels = [0, 0, 0, 0, 0, 0]

        return predicted_labels


    """
    補助用画像処理関数
    """
    def init_background_icon(self, svg, parent, widget_height):
        """
        ポケモンの背景画像初期化関数

        Args:
        - svg: svg画像データ
        - widget (QWidget): 親Widget
        - widget_height (int): パーティ表示用DockWidgetの高さ

        Return:
        - label (QLabel): アイコン背景用モンスターボール画像のQLabel
        """
        label = QLabel(parent)
        label.setMargin(0)
        label.setPixmap(self.svg_to_pixmap(svg, widget_height // 6, widget_height // 6)) # ポケモン6匹分なので高さの1/6のサイズに
        return label

    def svg_to_pixmap(self, svg, width, height):
        """
        SVGファイルを指定の幅と高さでQPixmapに変換する

        Args:
        - svg: svg画像データ
        - width (int): 設定する画像の幅
        - height (int): 設定する画像の高さ

        Return:
        - pixmap (QPixmap): SVGからPixmapに変換した画像
        """
        try:
            pixmap = QPixmap(width, height)  # 描画先のQPixmapを作成
            pixmap.fill(Qt.transparent)  # 背景を透明に設定

            # QPainterを使ってQPixmapに描画
            painter = QPainter(pixmap)
            svg.render(painter)
            painter.end()
        except Exception as e:
            e.args = ("SVG変換エラー: " + e.args[0],)

        return pixmap
    
    def resize_bg_icon(self, widget_height):
        """
        ウィンドウサイズが変化した場合に画像の大きさを調整する

        Args:
        - widget_height (int): パーティ表示用DockWidgetの高さ
        """
        try:
            size = widget_height // 6       
            scaled_pixmap = self.svg_to_pixmap(self.current_background, size, size)
            self.background_icon.setPixmap(scaled_pixmap)
            # ウィンドウが描画された後に重ねる処理を実行
            QTimer.singleShot(200, self.resize_pokemon_icon)
        except Exception as e:
            e.args = ("ポケモン背景アイコンサイズ変更エラー(pokemon.py): " + e.args[0])

        

    def resize_pokemon_icon(self):
        try:
            self.pokemon_icon.setGeometry(self.background_icon.geometry())
            if self.pokemon_icon.width() != self.pokemon_icon.height():
                size = min(self.pokemon_icon.width(), self.pokemon_icon.height())  # 小さい方のサイズを取得
                self.pokemon_icon.resize(size, size)
                #self.pokemon_icon.move(self.background_icon.x(), self.background_icon.y()) # 背景アイコンと位置を合わせる
        except Exception as e:
            e.args = ("ポケモンアイコンサイズ変更エラー(pokemon.py): " + e.args[0])

    def show_overlay_widget(self, pokemon_name):
        """
        親にオーバーレイウィジェットを表示するように信号を飛ばす

        Args:
        - pokemon_name (str): オーバーレイウィジェットに表示するポケモンの名前
        """
        self.show_ovelay_widget_signal.emit(pokemon_name)
