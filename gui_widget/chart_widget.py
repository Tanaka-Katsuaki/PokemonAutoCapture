from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush
from PyQt5.QtCore import Qt
""""""
from gui_widget.animated_bar_chart import AnimatedBarChart
from gui_widget.animated_pie_chart import AnimatedPieChart
from gui_widget.custom_table_widget import CustomTableWidget
from data_config import GraphDataType

class ChartWidget(QWidget):
    def __init__(self, data_type, data, parent=None):
        super().__init__(parent)
        self.data_type = data_type
        self.data = data
        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(0)

        # データタイプに応じてグラフを選択
        if self.data_type == GraphDataType.MOVE:
            self.chart = AnimatedBarChart(self.data, title=self.data_type)
            # 「わざ」の場合はテーブルを作成しない
            self.table = None
            
            # グラフを上詰めで配置し、下にストレッチを追加
            layout.addWidget(self.chart, 0, Qt.AlignTop | Qt.AlignCenter)
            layout.addStretch(1)  # 下部にストレッチを追加して余白を埋める
            
        else:
            self.chart = AnimatedPieChart(self.data, title=self.data_type, data_type=self.data_type)
            self.table = CustomTableWidget(self.data_type, self.data)
            
            # 余白用のスペーサー
            self.spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Fixed)
            layout.addWidget(self.chart, 0, Qt.AlignCenter)
            layout.addSpacerItem(self.spacer)
            layout.addWidget(self.table, 0, Qt.AlignCenter)
        
        self.chart.setMinimumSize(200, 200)

    def paintEvent(self, event):
        """カスタム描画イベントで背景色とボーダーを描画"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 背景色を描画
        background_brush = QBrush(QColor(0, 255, 0, 128))  # 緑の半透明
        painter.setBrush(background_brush)
        
        # ボーダーを描画
        border_pen = QPen(QColor(0, 200, 0, 180), 2)  # 緑のボーダー
        painter.setPen(border_pen)
        
        # 角丸四角形を描画
        rect = self.rect().adjusted(1, 1, -1, -1)  # ボーダーの幅を考慮して調整
        painter.drawRoundedRect(rect, 10, 10)

    def adjustSizes(self, chart_width, chart_height):
        self.setFixedSize(chart_width, chart_height)

        # 内側のマージンを考慮してサイズ調整
        inner_width = chart_width - 30  # 左右のマージン15px × 2
        inner_height = chart_height - 30  # 上下のマージン15px × 2

        if self.data_type == GraphDataType.MOVE:
            # 「わざ」の場合は、利用可能な高さの大部分をグラフに使用
            # 上詰めなので、グラフの高さを大きくとる
            chart_component_width = inner_width
            chart_component_height = inner_height // 2
            self.chart.setFixedSize(chart_component_width, chart_component_height)
        else:
            # その他の場合は、元のロジックを使用
            # ChartWidgetの高さに対する割合で余白を計算
            spacing_ratio = 0.03
            spacing_height = int(chart_height * spacing_ratio)
            
            # スペーサーのサイズを更新
            self.spacer.changeSize(0, spacing_height, QSizePolicy.Minimum, QSizePolicy.Fixed)

            chart_component_height = min(inner_width, inner_height // 2)
            chart_component_width = min(inner_width, chart_component_height)
            table_height = inner_height - chart_component_height - spacing_height

            self.chart.setFixedSize(chart_component_width, chart_component_height)
            self.table.setFixedSize(chart_component_width, table_height)
        
        # レイアウトを更新
        self.layout().invalidate()

    def showEvent(self, event):
        super().showEvent(event)
        self.chart.startAnimation()