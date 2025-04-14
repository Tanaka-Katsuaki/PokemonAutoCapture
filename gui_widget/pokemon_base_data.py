from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView, QStyleOptionHeader, QStyle
from PyQt5.QtCore import Qt
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
        self.name_rank_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.name_rank_layout.setAlignment(Qt.AlignLeft)
        self.name_rank_layout.setContentsMargins(0, 0, 0, 0)
        self.name_rank_layout.setSpacing(3)
        # 名前
        self.pokemon_name = TypeLabel()
        #デバッグ用
        self.pokemon_name.setFrameStyle(QLabel.Box)   # ボックス枠を設定
        self.pokemon_name.setLineWidth(2)             # 枠線の太さを設定
        # ランキング
        self.rank = TypeLabel()
        #デバッグ用
        self.rank.setFrameStyle(QLabel.Box)   # ボックス枠を設定
        self.rank.setLineWidth(2)             # 枠線の太さを設定

        self.name_rank_layout.addWidget(self.pokemon_name, stretch=2)
        self.name_rank_layout.addWidget(self.rank, stretch=1)

        """タイプ表示"""
        self.type_widget = QWidget()
        self.type_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.type_layout = QHBoxLayout(self.type_widget)
        self.type_layout.setContentsMargins(0, 0, 0, 0)
        self.type_layout.setSpacing(3)


        self.type_1 = TypeLabel(parent=self.type_widget)
        self.type_2 = TypeLabel(parent=self.type_widget)
        self.type_layout.addWidget(self.type_1, stretch=1)
        self.type_layout.addWidget(self.type_2, stretch=1)

        """高さ&重さ"""
        """self.height_weight_widget = QWidget()
        self.height_weight_layout = QHBoxLayout(self.height_weight_widget)
        self.height_weight_layout.setAlignment(Qt.AlignLeft)"""

        self.pokemon_height = TypeLabel(family="Yu Gothic UI")
        self.pokemon_weight = TypeLabel(family="Yu Gothic UI")

        self.pokemon_height.setMinimumHeight(0)
        self.pokemon_weight.setMinimumHeight(0)
        self.pokemon_height.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.pokemon_weight.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        """self.height_weight_layout.addWidget(self.pokemon_height, stretch=1)
        self.height_weight_layout.addWidget(self.pokemon_weight, stretch=4)"""

        self.base_info_layout.addWidget(self.name_rank_widget, stretch=2)
        self.base_info_layout.addWidget(self.type_widget, stretch=2)
        self.base_info_layout.addWidget(self.pokemon_height, stretch=1)
        self.base_info_layout.addWidget(self.pokemon_weight, stretch=1)
        # self.base_info_layout.addWidget(self.height_weight_widget, stretch=1)

        """種族値"""
        self.base_stats = BaseStatsBarChartWidget(self)

        """実数値"""
        self.real_stats = QTableWidget(self)
        self.real_stats.setRowCount(6)
        self.real_stats.setColumnCount(5)
        self.real_stats.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # セルを選択できなくする
        self.real_stats.setEditTriggers(QTableWidget.NoEditTriggers)    # 編集不可
        self.real_stats.setFocusPolicy(Qt.NoFocus)                      # フォーカス外す
        self.real_stats.setSelectionMode(QTableWidget.NoSelection)      # 選択不可
        # ヘッダー設定
        self.real_stats.setHorizontalHeaderLabels(["最大", "準", "無振", "下降", "最低"])
        self.real_stats.setVerticalHeaderLabels(["HP", "こうげき", "ぼうぎょ", "とくこう", "とくぼう", "すばやさ"])
        # VerticalHeaderのAlignを右寄せに
        self.real_stats.setVerticalHeader(RightAlignedVerticalHeader(Qt.Vertical, self.real_stats))
        # セルサイズを自動で合わせる
        self.real_stats.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.real_stats.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # ヘッダーをクリックしても何も起きないようにする
        self.real_stats.horizontalHeader().setSectionsClickable(False)
        self.real_stats.verticalHeader().setSectionsClickable(False)
        # 押されたようなビジュアル（ボタンっぽさ）をなくす
        self.real_stats.horizontalHeader().setHighlightSections(False)
        self.real_stats.verticalHeader().setHighlightSections(False)
        # ヘッダーのスタイル設定
        # HorizontalHeader（横ヘッダー）
        self.real_stats.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: rgb(135, 195, 232);
                border: 1px solid #cccccc;
                padding: 4px;
                font-family: 'Yu Gothic UI';
                font-weight: bold;
            }
        """)
        # VerticalHeader（縦ヘッダー）
        self.real_stats.verticalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: rgb(221, 238, 255);
                border: 1px solid #cccccc;
                padding: 2px;
                font-family: 'Yu Gothic UI';
                font-weight: normal;
                text-align: right;
            }
        """)
        self.real_stats.verticalHeader().setMinimumSectionSize(15)  # セルの高さの最小サイズの設定
        # 左上のコーナー部分も色を揃える
        self.real_stats.setStyleSheet("""
            QTableCornerButton::section {
                background-color: rgb(135, 195, 232);
                border: 1px solid #cccccc;
                padding: 4px;
            }
        """)

        # レイアウトに追加
        self.pokemon_detail_layout.addWidget(self.pokemon_image)
        self.pokemon_detail_layout.addWidget(self.base_info_widget)
        self.pokemon_detail_layout.addWidget(self.base_stats)
        self.pokemon_detail_layout.addWidget(self.real_stats)

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

            # 実数値
            data = [
                [pokemon_data['H_max'].iloc[0], pokemon_data['H_boost'].iloc[0], pokemon_data['H_neutral'].iloc[0], pokemon_data['H_weaken'].iloc[0], pokemon_data['H_min'].iloc[0]],
                [pokemon_data['A_max'].iloc[0], pokemon_data['A_boost'].iloc[0], pokemon_data['A_neutral'].iloc[0], pokemon_data['A_weaken'].iloc[0], pokemon_data['A_min'].iloc[0]],
                [pokemon_data['B_max'].iloc[0], pokemon_data['B_boost'].iloc[0], pokemon_data['B_neutral'].iloc[0], pokemon_data['B_weaken'].iloc[0], pokemon_data['B_min'].iloc[0]],
                [pokemon_data['C_max'].iloc[0], pokemon_data['C_boost'].iloc[0], pokemon_data['C_neutral'].iloc[0], pokemon_data['C_weaken'].iloc[0], pokemon_data['C_min'].iloc[0]],
                [pokemon_data['D_max'].iloc[0], pokemon_data['D_boost'].iloc[0], pokemon_data['D_neutral'].iloc[0], pokemon_data['D_weaken'].iloc[0], pokemon_data['D_min'].iloc[0]],
                [pokemon_data['S_max'].iloc[0], pokemon_data['S_boost'].iloc[0], pokemon_data['S_neutral'].iloc[0], pokemon_data['S_weaken'].iloc[0], pokemon_data['S_min'].iloc[0]]
            ]

            for row in range(6):
                for col in range(5):
                    item = QTableWidgetItem(str(data[row][col]))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.real_stats.setItem(row, col, item)

        except Exception as e:
            e.args = ("ベースデータUIセットエラー(pokemon_base_data.py): " + e.args[0])
            print(e.args)

    def adjustTableFontSize(self):
        """
        実数値表示用テーブルのフォントサイズ調整用
        """
        # 平均セルサイズを取得
        if self.real_stats.rowCount() == 0 or self.real_stats.columnCount() == 0:
            return

        cell_width = self.real_stats.viewport().width() / self.real_stats.columnCount()
        cell_height = self.real_stats.viewport().height() / self.real_stats.rowCount()

        # セルサイズの平均を使ってフォントサイズを決定
        font_size = int(min(cell_height, cell_width) * 0.4)
        
        # フォントサイズを適用
        font = QFont()
        font.setPointSize(max(font_size, 1))  # 小さすぎないように

        # ヘッダーのフォント
        self.real_stats.horizontalHeader().setFont(font)
        self.real_stats.verticalHeader().setFont(font)
        # セルのフォント
        for row in range(self.real_stats.rowCount()):
            for col in range(self.real_stats.columnCount()):
                item = self.real_stats.item(row, col)
                if item:
                    item.setFont(font)

    """リサイズ関数"""
    def resize(self):
        """
        オーバーレイウィジェットのサイズに合わせて基礎データ用の各UIサイズを変更する
        """
        # 画像
        self.pokemon_image.setFixedSize(self.height(), self.height())
        # 基礎データ
        self.base_info_widget.setFixedSize(self.width() // 5, self.height() * 2 // 3)
        # 種族値
        self.base_stats.resize(self.width() // 4)
        # 実数値
        self.real_stats.setFixedWidth(self.width() // 3)
        self.real_stats.horizontalHeader().setFixedHeight(self.height() // 7)
        self.real_stats.verticalHeader().setFixedWidth(self.real_stats.width() // 6)
        self.adjustTableFontSize()

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


class RightAlignedVerticalHeader(QHeaderView):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        option = QStyleOptionHeader()
        self.initStyleOption(option)
        option.rect = rect
        option.section = logicalIndex
        option.textAlignment = Qt.AlignRight | Qt.AlignVCenter  # ← 右揃え！

        option.text = self.model().headerData(logicalIndex, self.orientation(), Qt.DisplayRole)
        self.style().drawControl(QStyle.CE_Header, option, painter, self)
        painter.restore()
            