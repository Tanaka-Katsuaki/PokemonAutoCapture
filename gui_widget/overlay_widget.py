from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QPushButton
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush
from PyQt5.QtCore import Qt
""""""
from gui_widget.pokemon_info_widget import PokemonInfoWidget
from gui_widget.chart_widget import ChartWidget
from data_config import DataConfigClass, GraphDataType

class OverlayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_pokemon = "ディンルー"  # デフォルトのポケモン
        self.setupData()
        self.setupUI()
        self.hide()

    def paintEvent(self, event):
        """カスタム描画イベントで背景色とボーダーを描画"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 背景色を描画
        background_brush = QBrush(QColor(255, 255, 255, 180))  # 白の半透明（少し濃く）
        painter.setBrush(background_brush)
        
        # ボーダーを描画
        border_pen = QPen(QColor(200, 200, 200, 200), 3)  # グレーのボーダー（少し太く）
        painter.setPen(border_pen)
        
        # 角丸四角形を描画
        rect = self.rect().adjusted(2, 2, -2, -2)  # ボーダーの幅を考慮して調整
        painter.drawRoundedRect(rect, 15, 15)  # 角丸を少し大きく

    def setupData(self):
        battle_data = DataConfigClass.battle_datas[DataConfigClass.battle_datas["alias"] == self.current_pokemon]
        
        def extract_dict(key_col, rate_col):
            if battle_data.empty:
                return {}
            try:
                key_list = battle_data[key_col].iloc[0]
                val_list = battle_data[rate_col].iloc[0]
                return dict(zip(key_list, val_list))
            except Exception as e:
                print(f"[データ抽出エラー] {key_col}: {e}")
                return {}

        self.sample_data = [
            extract_dict("move", "move_rate"),
            extract_dict("ability", "ability_rate"),
            extract_dict("nature", "nature_rate"),
            extract_dict("item", "item_rate"),
            extract_dict("terastal", "terastal_rate"),
        ]

    def setupUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)  # 外側のマージンを増加（ボーダー分）

        # ポケモン情報部分
        self.pokemon_info = PokemonInfoWidget()
        self.pokemon_info.set_pokemon_data(self.current_pokemon)

        # チャート部分
        self.charts_container = QWidget()
        self.charts_container.setContentsMargins(0, 0, 0, 0)
        self.charts_container.setStyleSheet("background-color: transparent;")  # 透明に設定

        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.charts_container.setSizePolicy(size_policy)

        self.horizontal_layout = QHBoxLayout(self.charts_container)
        self.horizontal_layout.setSpacing(10)
        self.horizontal_layout.setContentsMargins(10, 10, 10, 10)

        self.charts = []
        chart_info = [
            (GraphDataType.MOVE, self.sample_data[0]),          # わざ
            (GraphDataType.ABILITY, self.sample_data[1]),       # とくせい
            (GraphDataType.NATURE, self.sample_data[2]),        # せいかく
            (GraphDataType.ITEM, self.sample_data[3]),          # もちもの
            (GraphDataType.TERA_TYPE, self.sample_data[4]),     # テラスタイプ
        ]

        for data_type, data in chart_info:
            chart = ChartWidget(data_type, data)
            self.charts.append(chart)
            self.horizontal_layout.addWidget(chart, 0, Qt.AlignCenter)

        # ボタン部分
        self.close_button = QPushButton("閉じる")
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c; 
                color: white; 
                border: none; 
                padding: 10px 30px; 
                font-size: 16px; 
                border-radius: 5px; 
                margin: 0px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.close_button.clicked.connect(self.hide)

        self.button_container = QWidget()
        self.button_container.setContentsMargins(0, 0, 0, 0)
        self.button_container.setStyleSheet("background-color: transparent;")  # 透明に設定
        button_layout = QHBoxLayout(self.button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        button_layout.addStretch()

        # ウィジェットを追加
        main_layout.addWidget(self.pokemon_info)
        main_layout.addWidget(self.charts_container)
        main_layout.addWidget(self.button_container)

        # 比率設定：ポケモン情報25%, チャート70%, ボタン5%
        main_layout.setStretch(0, 25)  # pokemon_info: 25%
        main_layout.setStretch(1, 70)  # charts: 70%
        main_layout.setStretch(2, 5)  # button: 5%

    def set_pokemon(self, pokemon_name):
        """表示するポケモンを変更"""
        self.current_pokemon = pokemon_name
        self.setupData()
        self.pokemon_info.set_pokemon_data(pokemon_name)
        
        # チャートデータも更新
        chart_info = [
            (GraphDataType.MOVE, self.sample_data[0]),
            (GraphDataType.ABILITY, self.sample_data[1]),
            (GraphDataType.NATURE, self.sample_data[2]),
            (GraphDataType.ITEM, self.sample_data[3]),
            (GraphDataType.TERA_TYPE, self.sample_data[4]),
        ]
        
        for i, (data_type, data) in enumerate(chart_info):
            if i < len(self.charts):
                # データを更新
                self.charts[i].data = data
                self.charts[i].chart.data = data
                
                # テラタイプの場合は色も再計算
                if data_type == GraphDataType.TERA_TYPE:
                    self.charts[i].chart.colors = self.charts[i].chart._get_tera_type_colors()
                
                # アニメーションを再開始（重要！）
                self.charts[i].chart.animation_progress = 0.0
                self.charts[i].chart.startAnimation()
                
                # テーブルがある場合は更新
                if hasattr(self.charts[i], 'table') and self.charts[i].table:
                    self.charts[i].table.update_data(data)

    def adjustSizes(self, overlay_width, overlay_height):
        # 高さの利用可能領域の計算
        total_margin = self.layout().contentsMargins().top() + self.layout().contentsMargins().bottom()
        total_spacing = self.layout().spacing() * 2  # between three rows
        available_height = overlay_height - total_margin - total_spacing

        # 各UIへの高さ振り分け
        info_h = int(available_height * 0.25)
        charts_h = int(available_height * 0.7)
        button_h = available_height - info_h - charts_h

        # 高さセット
        self.pokemon_info.setFixedHeight(info_h)
        self.button_container.setFixedHeight(button_h)
        self.charts_container.setFixedHeight(charts_h)

        # チャートUIを横並びにするために横方向に等分する(スペースも計算)
        num = len(self.charts)
        spacing = self.horizontal_layout.spacing() * (num - 1)
        total_w_margin = self.charts_container.layout().contentsMargins().left() + self.charts_container.layout().contentsMargins().right()
        avail_w = overlay_width - total_w_margin - spacing - (self.layout().contentsMargins().left() + self.layout().contentsMargins().right())
        each_w = avail_w // num
        each_w = max(each_w, 120)

        for chart in self.charts:
            chart.adjustSizes(each_w, charts_h - (self.horizontal_layout.contentsMargins().top() + self.horizontal_layout.contentsMargins().bottom()))