from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView, QStyleOptionHeader, QStyle
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont, QFontMetrics, QColor
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

        """基礎データテーブル"""
        self.base_info_table = QTableWidget(self)
        self.base_info_table.setRowCount(5)  # 名前 + タイプ + 使用率 + 高さ + 重さ
        self.base_info_table.setColumnCount(2)
        self.base_info_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # セルサイズを自動で合わせる
        self.base_info_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.base_info_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.base_info_table.verticalHeader().setMinimumSectionSize(21)  # セルの最小高さを設定
        # ヘッダーやインターフェース非表示
        self.base_info_table.horizontalHeader().hide()
        self.base_info_table.verticalHeader().hide()
        self.base_info_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.base_info_table.setFocusPolicy(Qt.NoFocus)
        self.base_info_table.setSelectionMode(QTableWidget.NoSelection)
        self.base_info_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.base_info_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        """名前セル"""
        self.base_info_table.setSpan(0, 0, 1, 2)    # 2列のセルをまとめて一つに
        self.pokemon_name_label = QLabel()
        self.pokemon_name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.pokemon_name_label.setAlignment(Qt.AlignCenter)
        self.pokemon_name_label.setStyleSheet("""
            background-color: rgb(255, 128, 64); 
            color: white;
            margin: 0px;
            padding: 0px;
            border: none;
        """)
        self.base_info_table.setCellWidget(0, 0, self.pokemon_name_label)
        """タイプセル"""
        # タイプ表示UI用Widgetを作成
        self.type_widget = QWidget()
        self.type_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.type_layout = QHBoxLayout(self.type_widget)
        self.type_layout.setContentsMargins(15, 5, 15, 5)
        self.type_layout.setSpacing(10)

        # タイプラベルを作成してレイアウトにセット
        self.type_1 = TypeLabel(parent=self.type_widget)
        self.type_2 = TypeLabel(parent=self.type_widget)
        self.type_spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.type_layout.addWidget(self.type_1, stretch=1)
        self.type_layout.addWidget(self.type_2, stretch=1)
        #self.type_layout.addSpacerItem(self.type_spacer)
        #self.type_layout.setStretch(2, 1)

        # レイアウトをセルにセット
        self.base_info_table.setSpan(1, 0, 1, 2)    # 2列のセルをまとめて一つに
        self.base_info_table.setCellWidget(1, 0, self.type_widget)
        """使用率セル"""
        usage_label = QTableWidgetItem("使用率")
        usage_label.setBackground(QColor(221, 238, 255))
        usage_label.setTextAlignment(Qt.AlignCenter)
        self.base_info_table.setItem(2, 0, usage_label)
        usage_item = QTableWidgetItem()
        usage_item.setTextAlignment(Qt.AlignCenter)
        self.base_info_table.setItem(2, 1, usage_item)
        """高さセル"""
        height_label = QTableWidgetItem("高さ")
        height_label.setBackground(QColor(221, 238, 255))
        height_label.setTextAlignment(Qt.AlignCenter)
        self.base_info_table.setItem(3, 0, height_label)
        height_item = QTableWidgetItem()
        height_item.setTextAlignment(Qt.AlignCenter)
        self.base_info_table.setItem(3, 1, height_item)
        """重さセル"""
        weight_label = QTableWidgetItem("重さ")
        weight_label.setBackground(QColor(221, 238, 255))
        weight_label.setTextAlignment(Qt.AlignCenter)
        self.base_info_table.setItem(4, 0, weight_label)
        weight_item = QTableWidgetItem()
        weight_item.setTextAlignment(Qt.AlignCenter)
        self.base_info_table.setItem(4, 1, weight_item)
        

        """種族値"""
        self.base_stats = BaseStatsBarChartWidget(self)

        """実数値"""
        self.real_stats_table = QTableWidget(self)
        self.real_stats_table.setRowCount(6)
        self.real_stats_table.setColumnCount(5)
        self.real_stats_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # セルを選択できなくする
        self.real_stats_table.setEditTriggers(QTableWidget.NoEditTriggers)    # 編集不可
        self.real_stats_table.setFocusPolicy(Qt.NoFocus)                      # フォーカス外す
        self.real_stats_table.setSelectionMode(QTableWidget.NoSelection)      # 選択不可
        # ヘッダー設定
        self.real_stats_table.setHorizontalHeaderLabels(["最大", "準", "無振", "下降", "最低"])
        self.real_stats_table.setVerticalHeaderLabels(["HP", "こうげき", "ぼうぎょ", "とくこう", "とくぼう", "すばやさ"])
        # VerticalHeaderのAlignを右寄せに
        self.real_stats_table.setVerticalHeader(RightAlignedVerticalHeader(Qt.Vertical, self.real_stats_table))
        # セルサイズを自動で合わせる
        self.real_stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.real_stats_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # ヘッダーをクリックしても何も起きないようにする
        self.real_stats_table.horizontalHeader().setSectionsClickable(False)
        self.real_stats_table.verticalHeader().setSectionsClickable(False)
        # 押されたようなビジュアル（ボタンっぽさ）をなくす
        self.real_stats_table.horizontalHeader().setHighlightSections(False)
        self.real_stats_table.verticalHeader().setHighlightSections(False)
        # ヘッダーのスタイル設定
        # HorizontalHeader（横ヘッダー）
        self.real_stats_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: rgb(135, 195, 232);
                border: 1px solid #cccccc;
                padding: 4px;
                font-family: 'Yu Gothic UI';
                font-weight: bold;
            }
        """)
        # VerticalHeader（縦ヘッダー）
        self.real_stats_table.verticalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: rgb(221, 238, 255);
                border: 1px solid #cccccc;
                padding: 2px;
                font-family: 'Yu Gothic UI';
                font-weight: normal;
                text-align: right;
            }
        """)
        self.real_stats_table.verticalHeader().setMinimumSectionSize(15)  # セルの高さの最小サイズの設定
        # 左上のコーナー部分も色を揃える
        self.real_stats_table.setStyleSheet("""
            QTableCornerButton::section {
                background-color: rgb(135, 195, 232);
                border: 1px solid #cccccc;
                padding: 4px;
            }
        """)

        """閉じるボタン"""

        # レイアウトに追加
        self.pokemon_detail_layout.addWidget(self.pokemon_image)
        self.pokemon_detail_layout.addWidget(self.base_info_table)
        self.pokemon_detail_layout.addWidget(self.base_stats)
        self.pokemon_detail_layout.addWidget(self.real_stats_table)

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
        # DataConfigからポケモンの基礎でデータを取得
        pokemon_data = DataConfigClass.pokemon_datas[DataConfigClass.pokemon_datas["alias"] == pokemon_name]

        # 画像
        try:
            self.pokemon_image.setPixmap(QPixmap("./img/Pokemon_Icons/" + pokemon_data["image_file"].iloc[0]))
        except Exception as e:
            e.args = ("ベースデータポケモン画像セットエラー(pokemon_base_data.py): " + e.args[0],)
            print(e.args)

        # 名前
        try:
            self.pokemon_name_label.setText(pokemon_name)
        except Exception as e:
            e.args = ("ベースデータポケモンネームセットエラー(pokemon_base_data.py): " + e.args[0],)
            print(e.args)
        

        #ランキング
        try:
            if battle_data["rank"].iloc[0] != 9999:
                self.base_info_table.item(2, 1).setText(f"{battle_data['rank'].iloc[0]}位")
            else:
                self.base_info_table.item(2, 1).setText("圏外")
        except Exception as e:
            e.args = ("ベースデータ順位セットエラー(pokemon_base_data.py): " + e.args[0],)
            print(e.args)
        

        # タイプ
        try:
            self.type_1.set_type(pokemon_data["type_1"].iloc[0])
            if isinstance(pokemon_data["type_2"].iloc[0], str):
                self.type_2.set_type(pokemon_data["type_2"].iloc[0])
                self.type_2.setVisible(True)
                self.type_spacer.changeSize(0, 0)
            else:
                self.type_2.setVisible(False)
                self.type_spacer.changeSize(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)

        except Exception as e:
            e.args = ("ベースデータタイプセットエラー(pokemon_base_data.py): " + e.args[0],)
            print(e.args)
        

        # 高さ
        try:
            self.base_info_table.item(3, 1).setText(f"{pokemon_data['height'].iloc[0]:.1f}m")
        except Exception as e:
            e.args = ("ベースデータ高さセットエラー(pokemon_base_data.py): " + e.args[0],)
            print(e.args)
        
        
        # 重さ
        try:
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
            self.base_info_table.item(4, 1).setText(f"{weight:.1f}kg\n(けたぐり等の威力: {low_kick_damage})")
        except Exception as e:
            e.args = ("ベースデータ重さセットエラー(pokemon_base_data.py): " + e.args[0],)
            print(e.args)
        

        # 種族値
        try:
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
            e.args = ("ベースデータ種族値セットエラー(pokemon_base_data.py): " + e.args[0],)
            print(e.args)
        

        # 実数値
        try:
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
                    self.real_stats_table.setItem(row, col, item)
                    self.adjustTableFontSize(self.real_stats_table)
        except Exception as e:
            e.args = ("ベースデータ実数値セットエラー(pokemon_base_data.py): " + e.args[0],)
            print(e.args)
            

    def adjustTableCellSize(self, table, row_stretches):
        """
        テーブルのセルの高さを指定したstretchに応じて割合配分し、
        高さの合計をViewportの高さにぴったり合わせる
        Args:
            - table (QTableWidget): 調整したいテーブル
            - row_stretches (list(int)): 各行の全体に対する割合
        """          
        total_height = table.viewport().height()
        total_stretch = sum(row_stretches)
        
        # 行の高さを計算（端数を保持）
        target_heights = []
        actual_sum = 0
        
        # まず小数点以下も含めて計算
        for row, stretch in enumerate(row_stretches):
            exact_height = total_height * stretch / total_stretch
            # 整数に切り捨て
            integer_height = int(exact_height)
            target_heights.append(integer_height)
            actual_sum += integer_height
        
        # 端数による差分を計算
        remainder = total_height - actual_sum
        
        # 差分を各行に分配（大きな比率の行から順に1ピクセルずつ追加）
        if remainder > 0:
            # stretchの大きい順にインデックスをソート
            sorted_indices = sorted(range(len(row_stretches)), 
                                key=lambda i: row_stretches[i], reverse=True)
            
            for i in range(min(remainder, len(row_stretches))):
                target_heights[sorted_indices[i % len(row_stretches)]] += 1
        
        # 行の高さを設定
        for row, height in enumerate(target_heights):
            table.setRowHeight(row, height)
        
        # フォントサイズを調整
        QTimer.singleShot(100, lambda: self.adjustTableFontSize(table))


    def adjustTableFontSize(self, table):
        """
        テーブルのフォントサイズを調整するが、行の高さは変更しない
        Args:
        - table (QTableWidget): フォントサイズを調整したいテーブル
        - target_heights (list): 各行の目標高さ
        """
        if table.rowCount() == 0 or table.columnCount() == 0:
            return
        
        font_size = 10 # デフォルト
        font = QFont()

        # フォントサイズの計算
        # 左1列の内、テキストが表示されているセルのサイズを基準にフォントサイズを決定
        for row in range(table.rowCount()):
            item = table.item(row, 0)
            if item:
                row_height = table.rowHeight(row) # 2行目のセルのサイズを基準に
                cell_width = table.viewport().width() / table.columnCount()
                
                # この行のフォントサイズを計算
                font_size = int(row_height * 0.4)
                font.setPointSize(max(font_size, 1))  # 小さすぎないように
                break
    
        # セルのフォントを設定
        # 上で計算したフォントサイズを使用
        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item: # テキストセル
                    item.setFont(font)
                else: # ラベルセル
                    widget = table.cellWidget(row, col)
                    if isinstance(widget, QLabel):
                        label_height = table.rowHeight(row)
                        label_width = widget.width()
                        text = widget.text()

                        # 探索するフォントサイズの範囲を定義
                        min_size = 1
                        max_size = int(label_height * 0.5)  # 高さを基準に最大値を設定（必要に応じて調整）

                        best_fit_size = min_size
                        for size in range(min_size, max_size + 1):
                            test_font = QFont()
                            test_font.setPointSize(size)
                            fm = QFontMetrics(test_font)
                            text_width = fm.horizontalAdvance(text)

                            if text_width <= label_width:
                                best_fit_size = size
                            else:
                                break  # 超えたら終了

                        final_font = QFont()
                        final_font.setPointSize(best_fit_size)
                        widget.setFont(final_font)

        # ヘッダーのフォント
        avg_height = table.horizontalHeader().height()
        header_font_size = int(avg_height * 0.4)
        header_font = QFont()
        header_font.setPointSize(max(header_font_size, 1))
        if table.horizontalHeader().isVisible():
            table.horizontalHeader().setFont(header_font)
        if table.verticalHeader().isVisible():
            table.verticalHeader().setFont(header_font)


    """リサイズ関数"""
    def resize(self):
        """
        オーバーレイウィジェットのサイズに合わせて基礎データ用の各UIサイズを変更する
        """
        # 画像
        self.pokemon_image.setFixedSize(self.height(), self.height())
        # 基礎データテーブル
        self.base_info_table.setFixedSize(self.width() // 4, self.height())
        # 基礎データテーブルのセルの調整
        self.adjustTableCellSize(table=self.base_info_table, row_stretches=[2, 2, 1, 1, 2])
        # 種族値
        self.base_stats.resize(self.width() // 4)
        # 実数値テーブル
        self.real_stats_table.setFixedWidth(self.width() * 7 // 24)
        self.real_stats_table.horizontalHeader().setFixedHeight(self.height() // 7)
        self.real_stats_table.verticalHeader().setFixedWidth(self.real_stats_table.width() // 6)
        self.adjustTableFontSize(self.real_stats_table)

"""タイプ表示ラベル"""
class TypeLabel(QLabel):
    
    def __init__(self, text=None, family=None, align=None, parent=None):
        """
        Args:
        - text (str): QLabelで表示するテキスト
        - family (str): テキストのフォント
        - align (Qt.AlignmetFlag): QLabelのテキストの位置調整
        """
        super().__init__(parent)

        self.setStyleSheet("""
                border: 2px solid white;
                border-radius: 10px;
        """)

        self.setAlignment(Qt.AlignVCenter)

        if text is not None:
            self.setText(text)
        if family is not None:
            font = QFont()
            font.setFamily(family)
            self.setFont(font)
        if align is not None:
            self.setAlignment(align)
        else:
            self.setAlignment(Qt.AlignCenter)

    
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
                border-radius: 5px;                /* 面取り */
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
            