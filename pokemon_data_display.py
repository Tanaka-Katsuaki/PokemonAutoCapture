import pyqtgraph as pg
import numpy as np
import itertools
from enum import Enum

from PyQt5.QtWidgets import (QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect, QGraphicsPathItem, QFrame )
from PyQt5.QtCore import Qt, QTimer, QElapsedTimer, QEvent, QPoint, pyqtSignal
from PyQt5.QtGui import QPainterPath, QPixmap, QFont, QColor, QBrush, QLinearGradient, QFontMetrics, QPainter
""""""
from data_config import DataConfigClass

# ポケモンのタイプごとのRGBカラーを定義
POKEMON_TYPE_COLOR = {
    "ノーマル": (144, 153, 161, 255),    #
    "ほのお": (255, 156, 84, 255),       #
    "みず": (78, 144, 214, 255),         #
    "くさ": (99, 187, 91, 255),          #
    "でんき": (244, 210, 60, 255),       #
    "こおり": (115, 206, 192, 255),      #
    "かくとう": (206, 64, 106, 255),     #
    "どく": (171, 106, 200, 255),        #
    "じめん": (217, 119, 69, 255),       #
    "ひこう": (143, 168, 221, 255),      #
    "エスパー": (249, 113, 119, 255),    #
    "むし": (144, 193, 45, 255),         #
    "いわ": (199, 183, 139, 255),        #
    "ゴースト": (83, 105, 172, 255),     #
    "ドラゴン": (10, 109, 196, 255),     #
    "あく": (90, 83, 102, 255),          #
    "はがね": (89, 142, 161, 255),       #
    "フェアリー": (237, 143, 230, 255),  #
    "ステラ": (192, 165, 238, 255)       #
}

# 汎用グラフカラー
SLICES_COLORS = ["#ff4069", "#ff9020", "#ffc234", "#22cfcf", "#059bff", "#8142ff", "#b2b6be"]

TEST_MOVE_CHART_DATA = {
    "カイリュー": {"しんそく": 86.6, "じしん": 78.1, "げきりん": 39.5, "りゅうのまい": 36.2, "はねやすめ": 30.9, "けたぐり": 23.6, "スケイルショット": 19.0, "アイアンヘッド": 17.1, "アンコール": 16.2, "アイススピナー": 9.3}
}
TEST_ABILITY_CHART_DATA = {
    "カイリュー": {"せいしんりょく": 0.6, "マルチスケイル": 99.4}
}
TEST_NATURE_CHART_DATA = {
    "カイリュー": {"いじっぱり": 83.4, "ようき": 6.3, "わんぱく": 3.8, "ずぶとい": 2.5, "ゆうかん": 1.1, "しんちょう": 0.6, "おだやか": 0.4, "ひかえめ": 0.4, "おくびょう": 0.2, "やんちゃ": 0.2}
}
TEST_ITEM_CHART_DATA = {
    "カイリュー": {"こだわりハチマキ": 43.2, "いかさまダイス": 14.7, "ゴツゴツメット": 14.1, "たべのこし": 6.4, "あつぞこブーツ": 5.3, "とつげきチョッキ": 4.7, "シルクのスカーフ": 4.7, "じゃくてんほけん": 1.7, "おんみつマント": 1.4, "ラムのみ": 1.2},
}
TEST_TYPE_CHART_DATA = {
    "ハバタクカミ": {"フェアリー": 32.2, "ノーマル": 18.8, "ステラ": 11.3, "じめん": 11.1, "みず": 6.5, "ほのお": 6.2, "でんき": 4.4, "どく": 3.1, "はがね": 2.6, "ゴースト": 1.8},
    "カイリュー": {"ノーマル": 76.3, "はがね": 10.9, "じめん": 5.0, "ひこう": 3.8, "フェアリー": 2.1, "みず": 0.5, "ほのお": 0.5, "でんき": 0.4, "どく": 0.2, "ステラ": 0.1},
}

"""データ種類の判別用列挙型"""
class GraphDataType(str, Enum):
    MOVE        = "わざ"
    ABILITY     = "とくせい"
    NATURE      = "せいかく"
    ITEM        = "もちもの"
    TERA_TYPE   = "テラスタイプ"

""""""

"""ポケモンのデータ表示用Widgetクラス"""
class PokemonDataDisplayWidget(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_StyledBackground)
    
        # QPainterのレンダリングヒントを設定
        if hasattr(self, 'setRenderHints'):
            self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        # **メインの枠 (背景付き)**
        self.overlay_widget = QWidget(self)
        self.overlay_widget.setStyleSheet("""
            background-color: rgba(255, 255, 255, 180); 
            border: 2px solid white;
            border-radius: 10px;
        """)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)  # マージンを均等に設定
        self.layout.addWidget(self.overlay_widget)

        # chart_widget のレイアウト
        self.ASPECT_RATIO = 5/3     # アスペクト比
        self.chart_layout = QHBoxLayout(self.overlay_widget)
        self.chart_layout.setContentsMargins(0, 0, 0, 0)
        self.chart_layout.setSpacing(0)
        

        self.data_charts = []

        # わざ情報
        self.move_chart = BarChartSetWidget(GraphDataType.MOVE, {}, self.overlay_widget)
        self.chart_layout.addWidget(self.move_chart)
        self.data_charts.append(self.move_chart)

        # とくせい情報
        self.ability_chart = DonutChartSetWidget(GraphDataType.ABILITY, {}, self.overlay_widget)
        self.chart_layout.addWidget(self.ability_chart)
        self.data_charts.append(self.ability_chart)

        # せいかく情報
        self.nature_chart = DonutChartSetWidget(GraphDataType.NATURE, {}, self.overlay_widget)
        self.chart_layout.addWidget(self.nature_chart)
        self.data_charts.append(self.nature_chart)

        # もちもの情報
        self.item_chart = DonutChartSetWidget(GraphDataType.ITEM, {}, self.overlay_widget)
        self.chart_layout.addWidget(self.item_chart)
        self.data_charts.append(self.item_chart)

        # テラスタイプ情報
        self.tera_type_chart = DonutChartSetWidget(GraphDataType.TERA_TYPE, {}, self.overlay_widget)
        self.chart_layout.addWidget(self.tera_type_chart)
        self.data_charts.append(self.tera_type_chart)

        # グラフウィジェットのサイズを等分する
        min_width = self.width() // len(self.data_charts)
        for chart in self.data_charts:
            # chart.setFixedWidth(min_width) 
            chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # 中央揃え用のスペーサーを追加
        spacer_left = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        spacer_right = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        # レイアウトの最初と最後にスペーサーを追加
        self.chart_layout.insertItem(0, spacer_left)
        self.chart_layout.addItem(spacer_right)
    
        
        # クリックイベントを監視するためのイベントフィルタをインストール
        if parent:
            parent.installEventFilter(self)


    def resize_overlay(self):
        """
        メインウィンドウのサイズ変更時に呼ばれる
        オーバレイウィジェットのサイズをメインウィンドウに合わせて変更する
        """
        # メインウィンドウの95%のサイズにする
        width = self.parentWidget().central_widget.width() * 95 // 100
        height = self.parentWidget().central_widget.height() * 95 // 100

        # アスペクト比を一定に
        if width / height >= self.ASPECT_RATIO:
            # 横長なら縦を基準
            scaled_width = int(height * self.ASPECT_RATIO)
            scaled_height = height
        else:
            # 縦長なら横を基準に
            scaled_width = width
            scaled_height = int(width / self.ASPECT_RATIO)            

        self.setFixedSize(scaled_width, scaled_height)

        # グラフウィジェットのサイズを等分する
        min_width = self.width() // len(self.data_charts)
        for chart in self.data_charts:
            chart.setFixedWidth(min_width) 

        self.update_layout_complete()

        # 各チャートのresize関数を呼び出す
        self.move_chart.resize()
        self.ability_chart.resize()
        self.nature_chart.resize()
        self.item_chart.resize()
        self.tera_type_chart.resize()

        self.update_layout_complete()
        self.update_position(self.parentWidget())

    def update_position(self, main_window):
        """
        main_windowのmoveEVent関数で呼び出される
        オーバーレイをメインウィンドウの中央に配置

        Args:
        - main_window (QWidget): 親として設定するウィジェット。MainWindowクラス。
        """
        global_pos = main_window.mapToGlobal(main_window.rect().center())  # ウィンドウの中心を取得
        overlay_center = self.rect().center()
        
        # 明示的に整数にキャストして位置を指定
        self.move(int(global_pos.x() - overlay_center.x()), int(global_pos.y() - overlay_center.y()))      
    

    def show_widget(self, pokemon_name=None):
        """ オーバーレイを表示 """
        self.show()

        self.resize_overlay()

        # test
        self.move_chart.set_data(TEST_MOVE_CHART_DATA["カイリュー"])

        if pokemon_name is not None:
            try:
                # 該当のポケモン名のデータを抽出
                pokemon_data = DataConfigClass.battle_datas[DataConfigClass.battle_datas["name"] == pokemon_name]

                # データをグラフWidgetにセット
                self.move_chart.set_data( dict( zip(pokemon_data["move"].iloc[0], pokemon_data["move_rate"].iloc[0]) ) )                    # わざ
                self.ability_chart.set_data( dict( zip(pokemon_data["ability"].iloc[0], pokemon_data["ability_rate"].iloc[0]) ) )           # とくせい
                self.nature_chart.set_data( dict( zip(pokemon_data["nature"].iloc[0], pokemon_data["nature_rate"].iloc[0]) ) )              # せいかく
                self.item_chart.set_data( dict( zip(pokemon_data["item"].iloc[0], pokemon_data["item_rate"].iloc[0]) ) )                    # もちもの
                self.tera_type_chart.set_data( dict( zip(pokemon_data["terastal"].iloc[0], pokemon_data["terastal_rate"].iloc[0]) ) )       # テラスタイプ
            except Exception as e:
                e.args = ("ポケモンデータエクセル読み込みエラー: " + e.args[0],)
                print(e.args)


        self.update_layout_complete()
        
    def hide_widget(self):
        """ オーバレイを非表示 """
        self.setVisible(False)

    def update_layout_complete(self):
        """
        各レイアウトやウィジェットのサイズ変更を実行する関数
        """
        self.layout.update()
        self.chart_layout.update()
        QApplication.processEvents()

""""""

"""棒グラフセット"""
class BarChartSetWidget(QWidget):
    """
    データ項目の背景に棒グラフを表示するウィジェット
    """

    def __init__(self, data_type, data, parent=None):
        """
        Args:
        - data_type (GraphDataType (str) ): グラフが何のデータかを判別するための変数。
        - data: 表示するデータ
        """
        super().__init__(parent)

        # 基本的なレイアウトを設定
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(0)

        # 単一の枠をコンテナとして作成
        self.container_frame = QFrame(self)
        self.container_frame.setFrameShape(QFrame.StyledPanel)
        self.container_frame.setStyleSheet("""
            background-color: white;
            border-radius: 8px;
        """)
        
        # コンテナフレームのレイアウト
        self.container_layout = QVBoxLayout(self.container_frame)
        self.container_layout.setContentsMargins(10, 10, 10, 10)
        self.container_layout.setSpacing(0)
        
        # タイトル
        self.title_label = QLabel(data_type, self.container_frame)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setObjectName("titleLabel")  # 後で参照するためのオブジェクト名
        title_font = QFont("Meiryo")
        self.title_label.setFont(title_font)
        self.container_layout.addWidget(self.title_label, alignment=Qt.AlignCenter)
             
        # データリスト
        self.table_widget = QWidget()
        
        # データがない場合のメッセージ
        self.no_data_label = QLabel("データがありません", self.container_frame)
        self.no_data_label.setAlignment(Qt.AlignCenter)
        self.no_data_label.setStyleSheet("color: red;")
        self.no_data_label.setObjectName("noDataLabel")  # 後で参照するためのオブジェクト名
        self.container_layout.addWidget(self.no_data_label, alignment=Qt.AlignCenter)
        
        # メインレイアウトにコンテナを追加
        self.layout.addWidget(self.container_frame)
        
        # 初期状態の設定
        # 初期状態では「データがありません」ラベルも非表示にする
        self.no_data_label.setVisible(False)
        self.table_widget.setVisible(False)
        self.adjust_all_fonts()

    def set_data(self, data):
        """
        グラフのデータを設定

        Args:
        - data (dict): 現状は{ key: データ名, value: 数値 } 
        """
        if not data:
            self.update_visibility(False)
            return

        # データリストの更新
        sorted_data = sorted(data.items(), key=lambda item: item[1], reverse=True)

        self.update_visibility(True)
        self.adjust_all_fonts()
        
        # テキストを設定した後、カスタムテーブルを作成
        self.create_custom_table(sorted_data)


    def create_custom_table(self, sorted_data):
        """
        データリスト表示用のウィジェットを作成

        Args:
        - sorted_data (dict): データ名とその割合のDictionary。大きい順に並び変え済み。
        """
        # 既存のテーブルがあれば削除
        for i in reversed(range(self.container_layout.count())):
            widget = self.container_layout.itemAt(i).widget()
            if widget and widget.objectName() == "customTableWidget":
                widget.deleteLater()
        
        # テーブルウィジェットの作成
        self.table_widget = QWidget(self.container_frame)
        self.table_widget.setObjectName("customTableWidget")
        table_layout = QVBoxLayout(self.table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(2)
        
        # コンテナの高さから、タイトルの高さを引いて、残りの高さを計算
        container_height = self.container_frame.height()
        title_height = self.title_label.height()
        remaining_height = max(20, container_height - title_height - 30)
        
        # テーブルの高さを設定
        self.table_widget.setMinimumHeight(remaining_height)

        # 各行の高さを計算（項目数を基準に均等に分配）
        row_count = len(sorted_data)
        row_height = max(20, min(40, int(remaining_height / 20)))
        
        # 最大値を計算（棒グラフの最大幅のため）
        max_value = sorted_data[0][1] if sorted_data else 100
        
        # 各行のデータを追加
        for idx, (key, value) in enumerate(sorted_data, 1):
            row_widget = QWidget()
            row_widget.setFixedHeight(row_height)  # 各行の高さを固定
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)
            
            # ランク
            rank_label = QLabel(f"{idx}")
            rank_label.setAlignment(Qt.AlignCenter)
            rank_label.setStyleSheet("background-color: transparent;")  # 透明化
            rank_label.setObjectName("rank")
            rank_label.setFixedWidth(20)
            
            # 棒グラフ付きアイテム
            bar_item = BarListItem(key, value)
            
            # フォントサイズを行の高さに合わせて調整
            font = row_widget.font()
            font.setPointSize(max(8, min(12, int(row_height * 0.4))))  # 行の高さの40%を目安に
            font.setFamily("Yu Gothic UI")  # フォント
            rank_label.setFont(font)
            font.setBold(True)
            bar_item.set_font(font)
            
            # 行レイアウトに追加
            row_layout.addWidget(rank_label)
            row_layout.addWidget(bar_item, 1)  # 1を指定して拡張させる
            
            # テーブルに行を追加
            table_layout.addWidget(row_widget)
        
        # データが少ない場合は、下に伸縮スペースを追加
        table_layout.addStretch(1)
        
        # メインコンテナにテーブルを追加
        self.container_layout.addWidget(self.table_widget)

    def resize(self):
        """ ウィジェットのリサイズ処理 """
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # コンテナの実際のサイズを取得
        container_width = self.container_frame.width()
        container_height = self.container_frame.height()
        
        # タイトルの高さを設定 (コンテナの高さの5%)
        title_height = int(container_height * 0.05)
        self.title_label.setFixedHeight(title_height)
        
        # テーブルウィジェットが存在する場合、サイズを調整
        if self.table_widget:
            # 残りの高さを計算
            remaining_height = max(20, container_height - title_height - 30)
            self.table_widget.setMinimumHeight(remaining_height)
            
            # テーブル内の各行のフォントサイズを調整
            row_layout = self.table_widget.layout()
            if row_layout:
                row_count = row_layout.count()
                if row_count > 0:
                    row_height = max(20, min(40, int(remaining_height / 20)))

                    # フォントサイズを計算
                    font_size = max(8, min(14, int(row_height * 0.4)))
                    # font = QFont("メイリオ", font_size)
                    
                    for i in range(row_count):
                        row_item = self.table_widget.layout().itemAt(i)
                        if row_item and row_item.widget():
                            row_widget = row_item.widget()
                            row_widget.setFixedHeight(row_height)
                            font = row_widget.font()
                            font.setFamily("Yu Gothic UI")  # フォント
                            font.setPointSize(font_size)  # 行の高さの40%を目安に
                            
                            # この行のすべてのラベルにフォントを適用
                            for label in row_widget.findChildren(QLabel):
                                label.setFont(font)
                            
                            # BarListItemにもフォントを適用
                            for bar_item in row_widget.findChildren(BarListItem):
                                bar_item.set_font(font)
        
        # フォントサイズを再調整
        self.adjust_all_fonts()

    def adjust_all_fonts(self):
        """ すべてのラベルのフォントサイズを調整 """
        self.adjust_font_size(self.title_label)
        self.adjust_font_size(self.no_data_label)

    def adjust_font_size(self, label):
        """
        ラベルの高さに合わせてフォントサイズを自動調整

        Args:
        - label (QLabel): 文字を表示しているQLabel。
        """
        if not label.text():
            return
            
        # 現在のフォント取得
        font = label.font()
        
        # ラベルのサイズを取得
        label_height = label.height()
        
        # テキストの行数を計算（最低1行）
        text_lines = max(1, label.text().count('\n') + 1)
        
        # 1行あたりの理想的な高さを計算
        ideal_line_height = label_height / text_lines
        
        # オブジェクト名に基づいて最適なフォントサイズを決定
        if label.objectName() == "titleLabel":
            # タイトル用のフォントサイズ調整
            new_size = max(10, min(24, int(ideal_line_height * 0.6)))
            font.setBold(True)
        elif label.objectName() == "noDataLabel":
            # データなし表示用のフォントサイズ調整
            new_size = max(10, min(18, int(ideal_line_height * 0.5)))
            font.setBold(True)
        
        # フォントサイズを設定
        font.setPointSize(new_size)
        label.setFont(font)

    def update_visibility(self, has_data):
        """
        データの有無に応じてウィジェットの表示状態を更新する

        Args:
        - has_data (bool): データがあるかどうか
        """
        # データがない場合は「データがありません」メッセージを表示
        self.no_data_label.setVisible(not has_data)
        
        # テーブルウィジェットが存在する場合は、データに応じて表示/非表示を切り替え
        if hasattr(self, 'table_widget') and self.table_widget:
            self.table_widget.setVisible(has_data)
""""""

"""棒グラフ表示表示"""
class BarListItem(QWidget):
    """
    データ項目の背景に棒グラフを表示するためのウィジェット
    """
    def __init__(self, text, value, max_value=100, parent=None):
        """
        Args:
        - text (str): 表示するテキスト
        - value (float): 値（0〜100）
        - max_value (float): 最大値（デフォルトは100）
        - parent (QWidget): 親ウィジェット
        """
        super().__init__(parent)
        self.text = text
        self.value = value
        self.max_value = max_value
        
        # レイアウト設定
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # テキストラベル
        self.label = QLabel(text)
        self.label.setObjectName("barLabel")
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label.setStyleSheet(
            "background-color: transparent;"
            "border: 0px solid white;"
            )  # 背景部分透明化
        self.label.setContentsMargins(5, 0, 0, 0)

        # ドロップシャドウ（白い影）の設定
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(3)  # 影のぼかし度
        shadow.setOffset(1, 1)  # 影のオフセット (X, Y)
        shadow.setColor(QColor(255, 255, 255))  # 影の色（白）

        self.label.setGraphicsEffect(shadow)  # ラベルに影を適用
        
        # 値ラベル
        self.value_label = QLabel(f"{value:.1f}%")
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.value_label.setStyleSheet(
            "background-color: transparent;"
            "border: 0px solid white;"
            )  # 背景部分透明化
        
        # レイアウトに追加
        layout.addWidget(self.label)
        layout.addStretch(1)
        layout.addWidget(self.value_label)
        
        # 背景を透明に設定
        self.setAttribute(Qt.WA_StyledBackground)
        
    def paintEvent(self, event):
        """
        ウィジェットの描画イベント
        背景に棒グラフを描画
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 背景の棒グラフを描画
        width = self.width()
        height = self.height()
        
        # 棒グラフの幅を計算（値の割合）
        bar_width = int((self.value / self.max_value) * width)
        
        # 棒グラフの領域をグレーで描画
        painter.setPen(QColor(200, 200, 200))
        back_color = QColor(200, 200, 200, 100)
        painter.fillRect(0, 0, width, height, back_color)

        # 棒グラフの背景を描画
        # 線形グラデーション (左→右)
        gradient = QLinearGradient(0, self.height(), width, self.height())  
        gradient.setColorAt(0, QColor(255, 173, 66))  # 開始色 (黄)
        gradient.setColorAt(1, QColor(255, 88, 51))  # 終了色 (橙)
        painter.fillRect(0, 0, bar_width, height, QBrush(gradient))
        
        # 親クラスの描画処理を呼び出す
        super().paintEvent(event)
        
    def set_value(self, value):
        """
        値を更新する
        
        Args:
        - value (float): 新しい値
        """
        self.value = value
        self.value_label.setText(f"{value:.1f}%")
        self.update()  # 再描画を要求
        
    def set_text(self, text):
        """
        テキストを更新する
        
        Args:
        - text (str): 新しいテキスト
        """
        self.text = text
        self.label.setText(text)
        
    def set_font(self, font):
        """
        フォントを設定する
        
        Args:
        - font (QFont): 設定するフォント
        """
        font.setBold(True)
        self.label.setFont(font)
        font.setBold(False)
        self.value_label.setFont(font)
""""""

"""円グラフセット"""
class DonutChartSetWidget(QWidget):
    """
    円グラフ用クラス

    - グラフタイトル
    - ドーナツ型グラフ
    - データリスト

    を一つのセットに
    """

    def __init__(self, data_type, data, parent=None):
        """
        Args:
        - data_type (GraphDataType (str) ): グラフが何のデータかを判別するための変数。
        - data: 表示するデータ
        """
        super().__init__(parent)

        # 基本的なレイアウトを設定
        self.layout = QVBoxLayout(self)
        # self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(0)

        # 単一の枠をコンテナとして作成
        self.container_frame = QFrame(self)
        self.container_frame.setFrameShape(QFrame.StyledPanel)
        self.container_frame.setStyleSheet("""
            background-color: white;
        """)
        
        # コンテナフレームのレイアウト
        self.container_layout = QVBoxLayout(self.container_frame)
        self.container_layout.setContentsMargins(10, 10, 10, 10)
        self.container_layout.setSpacing(0)
        
        # タイトル
        self.title_label = QLabel(data_type, self.container_frame)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setObjectName("titleLabel")  # 後で参照するためのオブジェクト名
        title_font = QFont("Meiryo")
        self.title_label.setFont(title_font)
        self.container_layout.addWidget(self.title_label, alignment=Qt.AlignCenter)
        
        # ドーナツグラフ
        self.donut_chart_widget = DonutChart(data_type=data_type, data={}, parent=self.container_frame)
        # self.donut_chart_widget.setFixedSize(150, 150)
        self.container_layout.addWidget(self.donut_chart_widget, alignment=Qt.AlignCenter)
        
        # データリスト
        self.table_widget = QWidget()
        
        # データがない場合のメッセージ
        self.no_data_label = QLabel("データがありません", self.container_frame)
        self.no_data_label.setAlignment(Qt.AlignCenter)
        self.no_data_label.setStyleSheet("color: red;")
        self.no_data_label.setObjectName("noDataLabel")  # 後で参照するためのオブジェクト
        font = QFont("Yu Gothic UI")
        self.no_data_label.setFont(font)
        self.container_layout.addWidget(self.no_data_label, alignment=Qt.AlignCenter)
        
        # メインレイアウトにコンテナを追加
        self.layout.addWidget(self.container_frame)
        
        # 初期状態の設定
        # 初期状態では「データがありません」ラベルも非表示にする
        self.no_data_label.setVisible(False)
        self.donut_chart_widget.setVisible(False)
        self.table_widget.setVisible(False)
        self.adjust_all_fonts()

    def set_data(self, data):
        """
        円グラフのデータを設定

        Args:
        - data (dict): 現状は{ key: データ名, value: 数値 } 
        """
        if not data:
            self.update_visibility(False)
            return

        self.donut_chart_widget.data = data
        self.donut_chart_widget.full_angle = 0  # アニメーションをリセット
        self.donut_chart_widget.plot_pie_chart()
        self.donut_chart_widget.start_animation()

        # データリストの更新
        sorted_data = sorted(data.items(), key=lambda item: item[1], reverse=True)

        self.update_visibility(True)
        self.adjust_all_fonts()
        
        # テキストを設定した後、カスタムテーブルを作成
        self.create_custom_table(sorted_data)
        QTimer.singleShot(0, self.resize)

    def create_custom_table(self, sorted_data):
        """
        データリスト表示用のウィジェットを作成

        Args:
        - sorted_data (dict): データ名とその割合のDictionary。大きい順に並び変え済み。
        """
        # 既存のテーブルがあれば削除
        for i in reversed(range(self.container_layout.count())):
            widget = self.container_layout.itemAt(i).widget()
            if widget and widget.objectName() == "customTableWidget":
                widget.deleteLater()
        
        # テーブルウィジェットの作成
        self.table_widget = QWidget(self.container_frame)
        self.table_widget.setObjectName("customTableWidget")
        table_layout = QVBoxLayout(self.table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(2)
        
        # コンテナの高さから、タイトルとドーナツチャートの高さを引いて、残りの高さを計算
        container_height = self.container_frame.height()
        title_height = self.title_label.height()
        chart_height = self.donut_chart_widget.height()
        remaining_height = max(20, container_height - title_height - chart_height - 30)

        # 高さが負になる場合は最小値を保証
        remaining_height = max(20, container_height - title_height - chart_height - 30)
        
        # テーブルの高さを設定
        self.table_widget.setMinimumHeight(remaining_height)

        # 各行の高さを計算（10項目を基準に均等に分配）
        row_count = len(sorted_data)
        row_height = max(20, min(40, int(remaining_height / 10)))
        
        # ソートを降順に変更
        sorted_data = sorted(sorted_data, key=lambda item: item[1], reverse=True)
        
        # 各行のデータを追加
        for idx, (key, value) in enumerate(sorted_data, 1):
            row_widget = QWidget()
            row_widget.setFixedHeight(row_height)  # 各行の高さを固定
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)
            
            # ランク
            rank_label = QLabel(f"{idx}")
            rank_label.setAlignment(Qt.AlignCenter)
            rank_label.setFixedWidth(20)
            
            # 補助アイコン
            icon_label = QLabel()
            # テラスタイプならタイプアイコンをリストに表示
            if self.title_label.text() == GraphDataType.TERA_TYPE:
                # アイコン (QPixmapで縮小)
                icon_path = f"img/Type Icons/{key}_rect.png"
                try:
                    pixmap = QPixmap(icon_path)
                    # アイコンの高さを行の高さに合わせる
                    icon_height = row_height - 4  # 余白を考慮
                    scaled_pixmap = pixmap.scaledToHeight(icon_height, Qt.SmoothTransformation)
                    icon_label.setPixmap(scaled_pixmap)
                except:
                    # 画像が見つからない場合は空のラベル
                    pass

            # もちものなら該当のもちもの画像をリストに表示
            elif self.title_label.text() == GraphDataType.ITEM:
                # アイコン (QPixmapで縮小)
                try:
                    icon_path = "./img/Item Icons/" + DataConfigClass.item_data_list.loc[DataConfigClass.item_data_list["Item Name"] == key, "File Name"].values[0]
                    pixmap = QPixmap(icon_path)
                    # アイコンの高さを行の高さに合わせる
                    icon_height = row_height - 4  # 余白を考慮
                    scaled_pixmap = pixmap.scaledToHeight(icon_height, Qt.SmoothTransformation)
                    icon_label.setPixmap(scaled_pixmap)
                except:
                    # 画像が見つからない場合は空のラベル
                    pass

            # タイプ名
            data_item_label = QLabel(key)
            data_item_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            
            # 値
            value_label = QLabel(f"{value:.1f}%")
            value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            # フォントサイズを行の高さに合わせて調整
            font = row_widget.font()
            font.setPointSize(max(5, min(12, int(row_height * 0.4))))  # 行の高さの40%を目安に
            font.setFamily("Yu Gothic UI")  # フォント
            rank_label.setFont(font)
            data_item_label.setFont(font)
            value_label.setFont(font)
            
            # 行レイアウトに追加
            row_layout.addWidget(rank_label)
            if self.title_label.text() == GraphDataType.TERA_TYPE or self.title_label.text() == GraphDataType.ITEM:
                row_layout.addWidget(icon_label)
            row_layout.addWidget(data_item_label, 1)  # 1を指定して拡張させる
            row_layout.addWidget(value_label)
            
            row_widget.setStyleSheet(""
                "border-bottom: 1px solid #aaa;"
                "border-radius: 0px;"
            )
            for label in row_widget.findChildren(QLabel):
                label.setStyleSheet("border: none; background-color: transparent;")

            
            # テーブルに行を追加
            table_layout.addWidget(row_widget)
        
        # データが10個未満の場合は、下に伸縮スペースを追加
        if row_count < 10:
            table_layout.addStretch(1)
        
        # メインコンテナにテーブルを追加
        self.container_layout.addWidget(self.table_widget)

    

    def resize(self):
        """ ウィジェットのリサイズ処理 """
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # コンテナの実際のサイズを取得
        container_width = self.container_frame.width()
        container_height = self.container_frame.height()
        
        # タイトルの高さを設定 (コンテナの高さの5%)
        title_height = int(container_height * 0.05)
        self.title_label.setFixedHeight(title_height)
        
        # ドーナツチャートの高さを設定 (コンテナの高さの45%)
        chart_height = int(container_height * 0.45)
        chart_width = min(container_width - 20, chart_height)  # 正方形に近づける
        self.donut_chart_widget.setFixedSize(chart_width, chart_height)
        
        # テーブルウィジェットが存在する場合、サイズを調整
        if self.table_widget:
            # 残りの高さを計算
            remaining_height = max(20, container_height - title_height - chart_height - 30)
            self.table_widget.setMinimumHeight(remaining_height)
            
            # テーブル内の各行のフォントサイズを調整
            row_layout = self.table_widget.layout()
            if row_layout:
                row_count = row_layout.count()
                if row_count > 0:
                    row_height = max(20, min(40, int(remaining_height / 10)))
                    
                    # すべてのdata_item_labelを取得
                    data_item_labels = []
                    for i in range(row_count):
                        row_item = self.table_widget.layout().itemAt(i)
                        if row_item and row_item.widget():
                            row_widget = row_item.widget()
                            row_widget.setFixedHeight(row_height)
                            # 各行のdata_item_labelを探す
                            for child in row_widget.findChildren(QLabel):
                                # 最初のラベルはrank_label、2番目がdata_item_labelと想定
                                # 行レイアウトの追加順に合わせて判定
                                if child.alignment() & Qt.AlignLeft and child.alignment() & Qt.AlignVCenter:
                                    data_item_labels.append(child)
                    
                    # 最大幅を持つラベルと最長テキストの長さを計算
                    max_width = 0
                    longest_text = ""
                    for label in data_item_labels:
                        # 利用可能な幅を計算
                        available_width = label.width()
                        max_width = max(max_width, available_width)
                        # 最長テキストを記録
                        if len(label.text()) > len(longest_text):
                            longest_text = label.text()
                    
                    # デフォルトのフォントサイズから開始
                    font = QFont("Yu Gothic UI")
                    font_size = 12
                    
                    # 最長テキストが最大幅に収まるまでフォントサイズを調整
                    while font_size > 5:  # 最小サイズ5pt
                        font.setPointSize(font_size)
                        font_metrics = QFontMetrics(font)
                        text_width = font_metrics.width(longest_text)
                        
                        if text_width <= max_width * 0.9:  # 10%の余裕を残す
                            break
                        
                        font_size -= 1
                    
                    # すべてのラベルに統一したフォントサイズを適用
                    for label in data_item_labels:
                        label.setFont(font)
                    
                    # その他のラベルに同じフォントを適用（ただしサイズは個別に調整してもよい）
                    for i in range(row_count):
                        row_item = self.table_widget.layout().itemAt(i)
                        if row_item and row_item.widget():
                            row_widget = row_item.widget()
                            
                            # すべてのラベルにフォントファミリーを適用
                            other_font = QFont(font)
                            for child in row_widget.findChildren(QLabel):
                                if child not in data_item_labels:
                                    child.setFont(other_font)
        
        # フォントサイズを再調整
        self.adjust_all_fonts()

    def adjust_all_fonts(self):
        """ すべてのラベルのフォントサイズを調整 """
        self.adjust_font_size(self.title_label)
        self.adjust_font_size(self.no_data_label)

    def adjust_font_size(self, label):
        """
        ラベルの高さに合わせてフォントサイズを自動調整

        Arges:
        - label (QLabel): 文字を表示しているQLabel。
        """
        if not label.text():
            return
            
        # 現在のフォント取得
        font = label.font()
        
        # ラベルのサイズを取得
        label_height = label.height()
        
        # テキストの行数を計算（最低1行）
        text_lines = max(1, label.text().count('\n') + 1)
        
        # 1行あたりの理想的な高さを計算
        ideal_line_height = label_height / text_lines
        
        # オブジェクト名に基づいて最適なフォントサイズを決定
        if label.objectName() == "titleLabel":
            # タイトル用のフォントサイズ調整
            new_size = max(10, min(24, int(ideal_line_height * 0.6)))
            font.setBold(True)
        elif label.objectName() == "noDataLabel":
            # データなし表示用のフォントサイズ調整
            new_size = max(10, min(18, int(ideal_line_height * 0.5)))
            font.setBold(True)
        
        # フォントサイズを設定
        font.setPointSize(new_size)
        label.setFont(font)

    def update_visibility(self, has_data):
        """
        データがある場合とない場合で表示を切り替え

        Args:
        - has_data (bool): データ有無のフラグ
        """
        self.donut_chart_widget.setVisible(has_data)
        self.table_widget.setVisible(has_data)
        self.no_data_label.setVisible(not has_data)

""""""

class DonutChart(pg.GraphicsLayoutWidget):
    """ ドーナツ型の円グラフをアニメーション付きで表示するクラス """

    def __init__(self, data_type=None, data=None, parent=None):
        """
        Args:
        - data_type (GraphDataType (str) ): グラフが何のデータかを判別するための変数。
        - data: 表示するデータ
        """
        super().__init__(parent)
        self.data = data
        self.current_angle = 0  # 現在のアニメーション角度
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        
        # 背景を透明に設定
        self.setBackground(None)

        # アンチエイリアシングを有効化
        self.setAntialiasing(True)

        # 何のデータグラフか
        self.data_type = data_type
        
        self.chart_size = 45
        self.view = self.addViewBox()
        self.view.setAspectLocked(True)
        self.view.setMouseEnabled(False, False)  # ドラッグ不可
        self.view.setRange(xRange=(-self.chart_size, self.chart_size), yRange=(-self.chart_size, self.chart_size))  # 一定サイズ
        self.slices = []  # 各パーツのリスト
        self.labels = []  # 各ラベルのリスト
        self.setVisible(False)  # 初期状態では非表示
        self.full_angle = 0  # アニメーション用の角度初期化
    
    
    def plot_pie_chart(self):
        """ ドーナツグラフの描画（アニメーション対応） """
        self.view.clear()
        self.slices.clear()
        self.labels.clear()

        # グラフの基本色サイクル
        slices_colors = itertools.cycle(SLICES_COLORS) 
        
        # データを値の大きい順にソート
        sorted_data = dict(sorted(self.data.items(), key=lambda item: item[1], reverse=True))
        
        total = sum(sorted_data.values()) if sorted_data else 1
        
        # QPainterPathでの角度計算：0度は3時の位置、時計回り
        # 真上（12時）からにするには、-90度(270度)から開始
        start_pos = -90  
        
        # 各スライスの角度を計算
        angles = []
        current_angle = start_pos
        for key, value in sorted_data.items():
            angle_size = value / total * 360
            angles.append((key, value, current_angle, angle_size))
            current_angle += angle_size
        
        # 各スライスを描画
        for key, value, start_angle, span_angle in angles:
            # アニメーション用の範囲チェック
            if start_angle - start_pos >= self.full_angle:
                break  # アニメーション範囲外は描画しない
            
            # 描画角度の計算
            actual_span = min(span_angle, self.full_angle - (start_angle - start_pos))
            if actual_span <= 0:
                continue  # 描画する角度がない場合はスキップ
            
            # パスを作成
            path = QPainterPath()
            path.moveTo(0, 0)
            path.arcTo(-50, -50, 100, 100, start_angle, actual_span)
            path.arcTo(-25, -25, 50, 50, start_angle + actual_span, -actual_span)
            path.closeSubpath()
            
            # スライスの描画
            item = QGraphicsPathItem(path)
            if self.data_type == GraphDataType.TERA_TYPE:
                color = POKEMON_TYPE_COLOR[key]
            else:
                color = next(slices_colors)
            item.setBrush(pg.mkBrush(color))
            item.setPen(pg.mkPen("white", width=2))
            self.view.addItem(item)
            self.slices.append(item)
            
            # ラベルの追加（十分な大きさのスライスのみ）
            if actual_span > 20:
                # 角度の中央値を計算（度）
                mid_angle_deg = start_angle + actual_span / 2
                # ラジアンに変換
                mid_angle_rad = np.radians(mid_angle_deg)
                
                # ラベル位置の計算（ドーナツの中心部）
                label_radius = 40  # ラベルを配置する半径（調整可能）
                x = label_radius * np.cos(mid_angle_rad)
                y = -label_radius * np.sin(mid_angle_rad)  # y軸は下が正なので反転
                
                # パーセント計算
                percentage = value / total * 100
                # label_text = f"{key}: {percentage:.1f}%"
                label_text = f"{key}"
                
                # ラベルテキストの作成と配置
                text = pg.TextItem(
                    text=label_text,
                    color=(0, 0, 0),
                    anchor=(0.5, 0.5),
                    fill=(255, 255, 255, 0)
                )

                # フォントの設定
                font = QFont("Meiryo")
                # font.setBold(True)
                text.setFont(font)

                # ラベルのz-orderをスライスより高く設定
                text.setZValue(10)
                
                text.setPos(x, y)
                
                self.view.addItem(text)
                self.labels.append(text)
    
    def start_animation(self):
        """ ドーナツグラフを時計回りに描画するアニメーション """
        self.full_angle = 0  # アニメーション角度をリセット
        self.setVisible(True)  # アニメーション開始時に表示
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.elapsed_timer = QElapsedTimer()
        self.elapsed_timer.start()  # 時間計測開始
        self.timer.start(16)  # 約60fps (16msごと)
    
    def update_animation(self):
        """ アニメーションの更新 """
        self.full_angle += 15  # 徐々に増やす
        if self.full_angle >= 360:
            self.timer.stop()
        self.plot_pie_chart()