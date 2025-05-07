from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, QPushButton
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPainter, QIcon
""""""
from data_config import *
from .bar_chart import *
from .donut_chart import *
from .pokemon_base_data import PokemonBaseDataWidget


"""ポケモンのデータ表示用シングルトンWidgetクラス"""
class PokemonDataDisplayWidget(QWidget):
    _instance = None

    @classmethod
    def get_instance(cls, parent=None):
        """
        シングルトンインスタンスを取得するクラスメソッド
        既存のインスタンスがある場合は親を更新する
        """
        if cls._instance is None:
            cls._instance = cls(parent)
        elif parent is not None and cls._instance.parent() != parent:
            # 親が指定され、既存の親と異なる場合は親を更新
            cls._instance.setParent(parent)
        return cls._instance
        
    def __new__(cls, parent=None, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PokemonDataDisplayWidget, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_StyledBackground)
    
        # QPainterのレンダリングヒントを設定
        if hasattr(self, 'setRenderHints'):
            self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        """メインとなるWidget"""
        self.ASPECT_RATIO = 5/3     # アスペクト比
        self.overlay_widget = QWidget(self)
        self.overlay_widget.setObjectName("overlay_widget")
        self.overlay_widget.setStyleSheet("""
            #overlay_widget {
                background-color: rgba(255, 255, 255, 180);
                border: 2px solid white;
                border-radius: 10px;
            }
        """)

        """大本のレイアウト"""
        self.overlay_layout = QVBoxLayout(self.overlay_widget)
        self.overlay_layout.setContentsMargins(5, 5, 5, 5)
        self.overlay_layout.setSpacing(0)  # レイアウト間のスペースを設定

        """上半分のレイアウト"""
        self.upper_widget = QWidget()
        self.upper_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.upper_layout = QHBoxLayout(self.upper_widget)
        # self.upper_layout.setAlignment(Qt.AlignTop)
        self.upper_layout.setContentsMargins(0, 0, 0, 0)
        self.upper_layout.setSpacing(0)

        # ポケモン詳細情報用のQHBoxLayout
        self.pokemon_detail_widget = PokemonBaseDataWidget()
        self.pokemon_detail_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 閉じるボタン
        self.close_button = QPushButton()
        self.close_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.close_icon = QIcon("./img/other/close_icon.png")
        self.close_button.setIcon(self.close_icon)  # アイコンの指定
        self.close_button.setIconSize(self.close_button.sizeHint())  # アイコンサイズの調整
        #self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 2px solid black;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 255);
            }
        """)
        self.close_button.clicked.connect(self.hide_widget)   # ボタンクリック時にウィジェットを非表示にする

        # upper_layoutにセット
        self.upper_layout.addWidget(self.pokemon_detail_widget, stretch=24)
        self.upper_layout.addWidget(self.close_button, stretch=1, alignment=Qt.AlignTop)
        
        """下半分のレイアウト"""
        # chart_widget
        self.chart_widget = QWidget()
        self.chart_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.chart_layout = QHBoxLayout(self.chart_widget)
        self.chart_layout.setContentsMargins(0, 0, 0, 0)
        self.chart_layout.setSpacing(0)

        self.data_charts = []

        # わざ情報
        self.move_chart = BarChartSetWidget(GraphDataType.MOVE, self.overlay_widget)
        self.chart_layout.addWidget(self.move_chart, stretch=1)
        self.data_charts.append(self.move_chart)

        # とくせい情報
        self.ability_chart = DonutChartSetWidget(GraphDataType.ABILITY, {}, self.overlay_widget)
        self.chart_layout.addWidget(self.ability_chart, stretch=1)
        self.data_charts.append(self.ability_chart)

        # せいかく情報
        self.nature_chart = DonutChartSetWidget(GraphDataType.NATURE, {}, self.overlay_widget)
        self.chart_layout.addWidget(self.nature_chart, stretch=1)
        self.data_charts.append(self.nature_chart)

        # もちもの情報
        self.item_chart = DonutChartSetWidget(GraphDataType.ITEM, {}, self.overlay_widget)
        self.chart_layout.addWidget(self.item_chart, stretch=1)
        self.data_charts.append(self.item_chart)

        # テラスタイプ情報
        self.tera_type_chart = DonutChartSetWidget(GraphDataType.TERA_TYPE, {}, self.overlay_widget)
        self.chart_layout.addWidget(self.tera_type_chart, stretch=1)
        self.data_charts.append(self.tera_type_chart)

        # 中央揃え用のスペーサーを追加
        spacer_left = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        spacer_right = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        # レイアウトの最初と最後にスペーサーを追加
        self.chart_layout.insertItem(0, spacer_left)
        self.chart_layout.addItem(spacer_right)

        # overlay_layoutにchart_widgetを追加
        self.overlay_layout.addWidget(self.upper_widget, stretch=1)
        self.overlay_layout.addWidget(self.chart_widget, stretch=3)

        # メインレイアウト
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.overlay_widget, stretch=1)
    
        
        # クリックイベントを監視するためのイベントフィルタをインストール
        if parent:
            parent.installEventFilter(self)


    def resize_overlay(self):
        """
        メインウィンドウのサイズ変更時に呼ばれる
        オーバレイウィジェットのサイズをメインウィンドウに合わせて変更する
        """
        if not self.parentWidget():
            return
        
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

        # self.pokemon_detail_widget.setFixedHeight((self.parentWidget().height()) // 4 - 20)
        self.upper_widget.setFixedHeight((self.parentWidget().height()) // 4 - 20)
        self.close_button.setFixedHeight(self.close_button.width())
        self.close_button.setIconSize(QSize(self.close_button.width() - 10, self.close_button.width() - 10))
        self.chart_widget.setFixedHeight((self.overlay_widget.height()) * 3 // 4 - 20)

        # グラフウィジェットのサイズを等分する
        min_width = self.width() // len(self.data_charts)
        for chart in self.data_charts:
            chart.setFixedWidth(min_width) 

        self.update_layout_complete()
        # 基礎データWidgetのサイズ更新
        self.pokemon_detail_widget.resize()
        # 各チャートのresize関数を呼び出す
        for chart in self.data_charts:
            chart.resize()

        self.update_layout_complete()
 

    def show_widget(self, pokemon_name=None):
        """ オーバーレイを表示 """
        self.show()

        self.resize_overlay()

        if pokemon_name is not None:
            try:
                # 該当のポケモン名のデータを抽出
                battle_data = DataConfigClass.battle_datas[DataConfigClass.battle_datas["alias"] == pokemon_name]

                # ポケモンの基礎データWidgetにセット
                self.pokemon_detail_widget.set_data(pokemon_name, battle_data)

                # データをグラフWidgetにセット
                self.move_chart.set_data( dict( zip(battle_data["move"].iloc[0], battle_data["move_rate"].iloc[0]) ) )                    # わざ
                self.ability_chart.set_data( dict( zip(battle_data["ability"].iloc[0], battle_data["ability_rate"].iloc[0]) ) )           # とくせい
                self.nature_chart.set_data( dict( zip(battle_data["nature"].iloc[0], battle_data["nature_rate"].iloc[0]) ) )              # せいかく
                self.item_chart.set_data( dict( zip(battle_data["item"].iloc[0], battle_data["item_rate"].iloc[0]) ) )                    # もちもの
                self.tera_type_chart.set_data( dict( zip(battle_data["terastal"].iloc[0], battle_data["terastal_rate"].iloc[0]) ) )       # テラスタイプ
            except Exception as e:
                e.args = ("ポケモンデータエクセルセットエラー(pokemon_data_display.py): " + e.args[0],)
                print(e.args)


        self.update_layout_complete()

    def update_position(self):
        """
        ポケモンバトルデータ表示用オーバーレイの位置更新
        オーバーレイをメインウィンドウの中央に配置
        """
        # 中央配置のための位置計算
        global_pos = self.parentWidget().mapToGlobal(self.parentWidget().rect().center())  # ウィンドウの中心を取得
        # ウィンドウの中心 - オーバレイの中心
        new_x = global_pos.x() - (self.width()) // 2 
        new_y = global_pos.y() - (self.height()) // 2

        self.move(new_x, new_y)
        
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
