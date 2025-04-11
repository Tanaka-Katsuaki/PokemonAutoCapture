from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QSizePolicy
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont, QFontMetrics
""""""
import data_config
from data_config import DataConfigClass
from .base_stats_bar_chart import BaseStatsBarChartWidget

"""
ポケモンの基礎データを表示するWidget
- 画像
- 名前
- タイプ
- 使用率順位
- 重さ & 高さ
- 種族値
- 実数値の範囲
"""
class PokemonBaseDataWidget(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("base_data")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setStyleSheet("""
            #base_data {
                background-color: rgba(255, 255, 255, 180); 
                border: 2px solid white;
                border-radius: 10px;
            }
        """)

        self.pokemon_detail_layout = QHBoxLayout(self)
        self.pokemon_detail_layout.setContentsMargins(0, 0, 0, 0)

        # 各ウィジェットの作成と追加
        """ポケモン画像"""
        self.pokemon_image = QLabel()
        self.setObjectName("pokemon_image")
        self.pokemon_image.setScaledContents(True)                       # 画像をラベルサイズに合わせる
        self.pokemon_image.setAttribute(Qt.WA_TranslucentBackground)     # 背景を透明に
        #デバッグ用
        #self.pokemon_image.setFrameStyle(QLabel.Box)   # ボックス枠を設定
        #self.pokemon_image.setLineWidth(2)             # 枠線の太さを設定

        """"""
        self.base_info_widget = QWidget(self)
        self.base_info_layout = QVBoxLayout(self.base_info_widget)
        self.base_info_layout.setContentsMargins(3, 3, 3, 3)
        self.base_info_layout.setSpacing(3)

        """名前とランキング"""
        self.name_rank_widget = QWidget()
        self.name_rank_layout = QHBoxLayout(self.name_rank_widget)
        self.name_rank_layout.setAlignment(Qt.AlignLeft)
        self.name_rank_layout.setContentsMargins(0, 0, 0, 0)
        self.name_rank_layout.setSpacing(3)
        # 名前
        self.pokemon_name = TypeLabel()
        #デバッグ用
        #self.pokemon_name.setFrameStyle(QLabel.Box)   # ボックス枠を設定
        #self.pokemon_name.setLineWidth(2)             # 枠線の太さを設定
        # ランキング
        self.rank = TypeLabel()
        #デバッグ用
        self.rank.setFrameStyle(QLabel.Box)   # ボックス枠を設定
        self.rank.setLineWidth(2)             # 枠線の太さを設定

        self.name_rank_layout.addWidget(self.pokemon_name, stretch=2)
        self.name_rank_layout.addWidget(self.rank, stretch=1)

        """タイプ表示"""
        self.type_widget = QWidget()
        self.type_layout = QHBoxLayout(self.type_widget)
        self.type_layout.setContentsMargins(0, 0, 0, 0)
        self.type_layout.setSpacing(3)


        self.type_1 = TypeLabel(parent=self.type_widget)
        self.type_2 = TypeLabel(parent=self.type_widget)
        self.type_layout.addWidget(self.type_1, stretch=1)
        self.type_layout.addWidget(self.type_2, stretch=1)

        """高さ&重さ"""
        self.height_weight_widget = QWidget()
        self.height_weight_layout = QHBoxLayout(self.height_weight_widget)
        self.height_weight_layout.setAlignment(Qt.AlignLeft)

        self.pokemon_height = TypeLabel(family="Yu Gothic UI")
        self.pokemon_weight = TypeLabel(family="Yu Gothic UI")
        self.height_weight_layout.addWidget(self.pokemon_height, stretch=2)
        self.height_weight_layout.addWidget(self.pokemon_weight, stretch=5)

        self.base_info_layout.addWidget(self.name_rank_widget, stretch=1)
        self.base_info_layout.addWidget(self.type_widget, stretch=1)
        self.base_info_layout.addWidget(self.height_weight_widget, stretch=1)

        """種族値"""
        self.base_stats = BaseStatsBarChartWidget(self)
        # self.real_stats = QLabel()


        # レイアウトに追加
        self.pokemon_detail_layout.addWidget(self.pokemon_image)
        self.pokemon_detail_layout.addWidget(self.base_info_widget)
        self.pokemon_detail_layout.addWidget(self.base_stats)
        #self.pokemon_detail_layout.addWidget(self.real_stats)

        # 余白のために左右にスペーサーを追加
        self.pokemon_detail_layout.insertStretch(0, 1)
        self.pokemon_detail_layout.addStretch(1)

    def set_data(self, pokemon_name, battle_data):
        """
        該当の名前のポケモンの基礎情報をUIにセットする

        Arges:
        - pokemon_name (str): ポケモンの名前
        - battle_data (list): ポケモンのバトルデータ
        """
        try:
            pokemon_data = DataConfigClass.pokemon_datas[DataConfigClass.pokemon_datas["name"] == pokemon_name]

            # 画像
            self.pokemon_image.setPixmap(QPixmap("./img/Pokemon_Icons/" + pokemon_data["image_file"].iloc[0]))
            # 名前
            self.pokemon_name.setText(pokemon_name)
            #ランキング
            if battle_data["rank"].iloc[0] != 9999:
                self.rank.setText(f"{battle_data['rank'].iloc[0]}位")
            else:
                self.rank.setText("圏外")
            # タイプ
            self.type_1.set_type(pokemon_data["type_1"].iloc[0])
            if pokemon_data["type_2"].iloc[0]:
                self.type_2.set_type(pokemon_data["type_2"].iloc[0])
                self.type_2.setVisible(True)
            else:
                self.type_2.setVisible(False)
            # 高さ
            self.pokemon_height.setText(f"高さ: {pokemon_data['height'].iloc[0]:.1f}m")
            # 重さ
            weight = pokemon_data["weight"].iloc[0]
            low_kick_damage = 0
            # けたぐりの威力
            if weight < 10.0:
                low_kick_damage = 20
            elif weight < 25.0:
                low_kick_damage = 40
            elif weight < 50.0:
                low_kick_damage = 60
            elif weight < 100.0:
                low_kick_damage = 80
            elif weight < 200.0:
                low_kick_damage = 100
            else:
                low_kick_damage = 120
            self.pokemon_weight.setText(f"重さ: {weight:.1f}kg （けたぐり等の威力: {low_kick_damage}）")

            # 種族値
            h = pokemon_data['H'].iloc[0]
            a = pokemon_data['A'].iloc[0]
            b = pokemon_data['B'].iloc[0]
            c = pokemon_data['C'].iloc[0]
            d = pokemon_data['D'].iloc[0]
            s = pokemon_data['S'].iloc[0]
            sum = h + a + b + c + d + s
            base_stat_dict = {"HP": h, "こうげき": a, "ぼうぎょ": b, "とくこう": c, "とくぼう": d, "すばやさ": s, "合計": sum}
            self.base_stats.set_data(base_stat_dict)
        except Exception as e:
            e.args = ("ベースデータUIセットエラー(pokemon_base_data.py): " + e.args[0])
            print(e.args)


    def resize(self):
        """
        オーバーレイウィジェットのサイズに合わせて基礎データ用の各UIサイズを変更する
        """

        self.pokemon_image.setFixedSize(self.height(), self.height())
        self.base_info_widget.setFixedSize(self.width() // 4, self.height() * 2 // 3)
        self.base_stats.resize(self.width() // 4)

        #self.pokemon_name.setFixedSize(self.width() // 6, self.height() // 3)
        #self.type_widget.setFixedSize(self.width() // 4, self.height() // 3)

"""タイプ表示ラベル"""
class TypeLabel(QLabel):
    
    def __init__(self, text=None, family=None, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
                border: 2px solid white;
                border-radius: 10px;
        """)

        if text is not None:
            self.setText(text)
        if family is not None:
            font = QFont()
            font.setFamily(family)
            self.setFont(font)

    
    def set_type(self, text):
        """
        タイプ名とタイプ色をセット

        Args:
        - text (str): タイプ名, タイプ表示UIにて表示するテキスト
        """
        if not text:
            return
        
        # タイプテキストセット
        self.setText(text)

        # タイプ名から色をセット
        bg_color = data_config.POKEMON_TYPE_COLOR[text]
        bg_color_str = f"rgba({bg_color[0]}, {bg_color[1]}, {bg_color[2]}, {bg_color[3]})"

        # 文字列フォーマットを使用して変数を適用
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color_str};   /* 背景色 */
                color: white;                       /* 文字色 */
                font-family: "Yu Gothic UI";        /* フォント */
                border-radius: 10px;                /* 面取り */
            }}
        """)
        

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjustFontSize()

    def adjustFontSize(self):
        """ QLabel のサイズに合わせてフォントサイズを自動調整する """
        text = self.text()
        if not text:
            return

        # 初期フォントサイズを設定（ラベルの高さを基準）
        font = self.font()
        min_font_size = 3
        max_font_size = self.height()
        
        for font_size in range(max_font_size, min_font_size - 1, -1):
            font.setPointSize(font_size)
            fm = QFontMetrics(font)
            
            # テキストの幅と高さをチェック
            text_width = fm.horizontalAdvance(text)
            text_height = fm.height()
            
            # ラベルの幅と高さに収まるかを確認
            if text_width <= self.width() and text_height <= self.height():
                self.setFont(font)
                return
        
        # 最小フォントサイズでも収まらない場合は最小サイズに設定
        font.setPointSize(min_font_size)
        self.setFont(font)
            