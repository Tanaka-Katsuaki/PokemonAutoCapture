from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, pyqtProperty
import math
""""""
from data_config import GraphDataType, SLICES_COLORS, POKEMON_TYPE_COLOR

class AnimatedPieChart(QWidget):
    def __init__(self, data, title="", data_type=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: red;")
        self.data = data
        self.title = title
        self.data_type = data_type
        self.animation_progress = 0.0
        
        # データタイプに応じて色を設定
        if self.data_type == GraphDataType.TERA_TYPE:
            self.colors = self._get_tera_type_colors()
        else:
            self.colors = [QColor(c) for c in SLICES_COLORS]

        self.animation = QPropertyAnimation(self, b"animationProgress")
        self.animation.setDuration(500)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Linear)

    def _get_tera_type_colors(self):
        """テラタイプ用の色を取得"""
        colors = []
        sorted_data = sorted(self.data.items(), key=lambda x: x[1], reverse=True)
        
        for type_name, _ in sorted_data:
            if type_name in POKEMON_TYPE_COLOR:
                r, g, b, a = POKEMON_TYPE_COLOR[type_name]
                colors.append(QColor(r, g, b, a))
            else:
                # 未知のタイプの場合はデフォルト色を使用
                colors.append(QColor(128, 128, 128, 255))
        
        return colors

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
        #painter.fillRect(self.rect(), QColor(255, 255, 255, 240))

        painter.setPen(QColor(0, 0, 0))
        font = painter.font()
        font.setPointSize(max(10, min(16, self.width() // 20)))
        font.setFamily("Meiryo")
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRect(0, 10, self.width(), 30), Qt.AlignCenter, self.title)

        chart_size = self.width() - 50
        chart_rect = QRect((self.width() - chart_size) // 2, 50, chart_size, chart_size)

        if not self.data:
            return

        total = sum(self.data.values())
        if total == 0:
            return

        sorted_data = sorted(self.data.items(), key=lambda x: x[1], reverse=True)
        start_angle = 90 * 16
        total_slices = len(sorted_data)
        current_slice_count = int(total_slices * self.animation_progress)

        center_x = chart_rect.center().x()
        center_y = chart_rect.center().y()
        outer_radius = chart_size // 2
        inner_radius = outer_radius * 0.4
        inner_rect = QRect(int(center_x - inner_radius), int(center_y - inner_radius), int(inner_radius * 2), int(inner_radius * 2))

        # ラベル情報を保存するリスト
        labels_to_draw = []

        # スライスを描画
        for i, (label, value) in enumerate(sorted_data):
            span_angle = -int((value / 100) * 360 * 16)
            percentage = value
            should_draw = False
            actual_span = 0

            if i < current_slice_count:
                should_draw = True
                actual_span = span_angle
            elif i == current_slice_count:
                progress_in_slice = (total_slices * self.animation_progress) - current_slice_count
                actual_span = int(span_angle * progress_in_slice)
                if actual_span != 0:
                    should_draw = True

            if should_draw:
                painter.setBrush(self.colors[i % len(self.colors)])
                painter.setPen(QPen(QColor(255, 255, 255), 2))
                painter.drawPie(chart_rect, start_angle, actual_span)

                # ラベル描画の準備（5%以上かつ完全に描画されたスライスのみ）
                if percentage >= 5 and actual_span == span_angle:
                    mid_angle_deg = (start_angle / 16 + actual_span / 32) % 360
                    mid_angle_rad = math.radians(mid_angle_deg)
                    label_radius = inner_radius + (outer_radius - inner_radius) * 0.7
                    label_x = center_x + label_radius * math.cos(mid_angle_rad)
                    label_y = center_y - label_radius * math.sin(mid_angle_rad)
                    
                    # ラベル情報を保存（後で描画）
                    labels_to_draw.append({
                        'text': label,
                        'x': label_x,
                        'y': label_y
                    })

            start_angle += span_angle

        # 中央の円を描画（ドーナツ型にする）
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(inner_rect)

        # ラベルを最上位レイヤーで描画（中央揃え）
        label_font = painter.font()
        label_font.setPointSize(max(8, min(12, self.width() // 25)))
        label_font.setFamily("Meiryo")
        label_font.setBold(True)
        painter.setFont(label_font)

        for label_info in labels_to_draw:
            text = label_info['text']
            label_x = label_info['x']
            label_y = label_info['y']
            
            # テキストのサイズを取得
            metrics = painter.fontMetrics()
            text_width = metrics.horizontalAdvance(text)
            text_height = metrics.height()
            
            # 中央揃えのための座標調整
            centered_x = int(label_x - text_width / 2)
            centered_y = int(label_y + text_height / 4)  # ベースラインを考慮した調整
            
            # 影（アウトライン効果）を描画
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(centered_x + 1, centered_y + 1, text)
            
            # メインテキストを描画
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(centered_x, centered_y, text)