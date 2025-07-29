from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QLinearGradient, QBrush
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, pyqtProperty

class AnimatedBarChart(QWidget):
    def __init__(self, data, title="", parent=None):
        super().__init__(parent)
        self.data = data
        self.title = title
        self.animation_progress = 0.0

        self.animation = QPropertyAnimation(self, b"animationProgress")
        self.animation.setDuration(500)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Linear)

    def getAnimationProgress(self):
        return self.animation_progress

    def setAnimationProgress(self, value):
        self.animation_progress = value
        self.update()

    animationProgress = pyqtProperty(float, getAnimationProgress, setAnimationProgress)

    def startAnimation(self):
        self.animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # タイトル描画
        painter.setPen(QColor(0, 0, 0))
        font = painter.font()
        font.setPointSize(max(10, min(16, self.width() // 20)))
        font.setFamily("Meiryo")
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRect(0, 10, self.width(), 30), Qt.AlignCenter, self.title)

        if not self.data:
            return

        # データを降順でソート
        sorted_data = sorted(self.data.items(), key=lambda x: x[1], reverse=True)
        
        # 描画領域の設定
        chart_top = 50
        chart_height = self.height() - 80
        chart_width = self.width() - 15
        chart_left = 0
        
        # バーの設定
        bar_height = chart_height // 10  # 10個のバー用
        bar_spacing = 2
        actual_bar_height = bar_height - bar_spacing
        
        # 最大値を100に固定（100%基準）
        max_value = 100.0
        
        # バーを描画
        for i in range(10):
            y_pos = chart_top + i * bar_height
            
            if i < len(sorted_data):
                label, value = sorted_data[i]
                bar_width = int((value / max_value) * chart_width * 0.8 * self.animation_progress)
                
                # グラデーションブラシを作成
                gradient = QLinearGradient(chart_left, 0, chart_left + bar_width, 0)
                gradient.setColorAt(0, QColor(255, 173, 66))  # 開始色
                gradient.setColorAt(1, QColor(255, 88, 51))   # 終了色
                
                # 背景バー（グレー）
                painter.setBrush(QColor(200, 200, 200))
                painter.setPen(Qt.NoPen)
                background_rect = QRect(chart_left, y_pos, int(chart_width * 0.8), actual_bar_height)
                painter.drawRoundedRect(background_rect, 3, 3)
                
                # メインバー（グラデーション）
                if bar_width > 0:
                    painter.setBrush(QBrush(gradient))
                    bar_rect = QRect(chart_left, y_pos, bar_width, actual_bar_height)
                    painter.drawRoundedRect(bar_rect, 3, 3)
                
                # ラベルテキスト（白の影付き黒文字）
                label_font = painter.font()
                label_font.setPointSize(max(8, min(12, self.width() // 25)))
                label_font.setFamily("Meiryo")
                label_font.setBold(True)
                painter.setFont(label_font)
                
                text_y = y_pos + actual_bar_height // 2 + 4
                
                # 影（白）
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(chart_left + 6, text_y + 1, label)
                
                # メインテキスト（黒）
                painter.setPen(QColor(0, 0, 0))
                painter.drawText(chart_left + 5, text_y, label)
                
                # パーセンテージ表示（右詰）
                percentage_text = f"{value:.1f}%"
                metrics = painter.fontMetrics()
                text_width = metrics.horizontalAdvance(percentage_text)
                percentage_x = chart_left + int(chart_width * 0.8) + 10
                
                # 影（白）
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(percentage_x + 1, text_y + 1, percentage_text)
                
                # メインテキスト（黒）
                painter.setPen(QColor(0, 0, 0))
                painter.drawText(percentage_x, text_y, percentage_text)