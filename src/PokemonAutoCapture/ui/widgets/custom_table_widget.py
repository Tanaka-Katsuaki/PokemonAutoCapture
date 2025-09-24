from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtGui import QFont, QFontMetrics, QPixmap
from PyQt5.QtCore import Qt, QTimer
import os
""""""
from config.data_config import DataConfigClass, GraphDataType

class CustomTableWidget(QWidget):
    def __init__(self, data_type, data, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: transparent;")
        self.data_type = data_type
        self.data = data
        self.row_widgets = []
        self._is_properly_sized = False  # 適切にサイズ調整されたかのフラグ
        self.setupUI()

    def setupUI(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(2)

        sorted_data = sorted(self.data.items(), key=lambda x: x[1], reverse=True)
        font = QFont("Meiryo", 10)

        for idx in range(10):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)

            if idx < len(sorted_data):
                key, value = sorted_data[idx]
                rank_text = f"{idx + 1}"
                name_text = key
                value_text = f"{value:.1f}%"
            else:
                key = None
                rank_text = ""
                name_text = ""
                value_text = ""

            rank_label = QLabel(rank_text)
            rank_label.setAlignment(Qt.AlignCenter)
            rank_label.setFixedWidth(20)
            rank_label.setFont(font)

            icon_label = QLabel()
            icon_pixmap = None
            if key and self.data_type == GraphDataType.TERA_TYPE:
                icon_path = f"assets/images/Type Icons/{key}_rect.png"
                icon_pixmap = QPixmap(icon_path)
            elif key and self.data_type == GraphDataType.ITEM:
                try:
                    match = DataConfigClass.item_data_list[DataConfigClass.item_data_list["Item Name"] == key]
                    if not match.empty:
                        file_name = match.iloc[0]["File Name"]
                        icon_path = os.path.join("assets/images", "Item Icons", file_name)
                        icon_pixmap = QPixmap(icon_path)
                except Exception as e:
                    print(f"[アイコンエラー] {key}: {e}")
            
            # アイコンラベルを初期状態では非表示に設定
            icon_label.setVisible(False)

            name_label = QLabel(name_text)
            name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            name_label.setFont(font)

            value_label = QLabel(value_text)
            value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            value_label.setFont(font)

            row_layout.addWidget(rank_label)
            row_layout.addWidget(icon_label)  # アイコンは常に追加（非表示状態で）
            row_layout.addWidget(name_label, 1)
            row_layout.addWidget(value_label)

            # 下線：空行にはなし、有効行にはあり
            if key:
                row_widget.setStyleSheet("border-bottom: 1px solid #aaa;")
            else:
                row_widget.setStyleSheet("")

            self.main_layout.addWidget(row_widget)
            self.row_widgets.append({
                "widget": row_widget,
                "icon_label": icon_label,
                "icon_pixmap": icon_pixmap,
                "rank_label": rank_label,
                "name_label": name_label,
                "value_label": value_label,
                "original_name_text": name_text,
                "original_value_text": value_text,
            })

        # 最後に stretch を別に追加（下線が消えないように）
        stretch_container = QWidget()
        stretch_layout = QVBoxLayout(stretch_container)
        stretch_layout.setContentsMargins(0, 0, 0, 0)
        stretch_layout.addStretch(1)

        self.main_layout.addWidget(stretch_container)
        
        # 初期化完了後、サイズが確定したらリサイズを実行
        QTimer.singleShot(0, self._initial_resize)

    def update_data(self, new_data):
        """テーブルのデータを更新し、表示を再描画"""
        self.data = new_data
        
        # データをソート
        sorted_data = sorted(self.data.items(), key=lambda x: x[1], reverse=True)
        
        # 各行のウィジェットを更新
        for idx, row in enumerate(self.row_widgets):
            if idx < len(sorted_data):
                key, value = sorted_data[idx]
                rank_text  = f"{idx + 1}"
                name_text  = key
                value_text = f"{value:.1f}%"
                
                # アイコンの更新
                icon_pixmap = None
                if key and self.data_type == GraphDataType.TERA_TYPE:
                    icon_path = DataConfigClass.get_resource_path("assets", "images", "Type Icons", f"{key}_rect.png")
                    icon_pixmap = QPixmap(icon_path)
                elif key and self.data_type == GraphDataType.ITEM:
                    try:
                        match = DataConfigClass.item_data_list[DataConfigClass.item_data_list["Item Name"] == key]
                        if not match.empty:
                            file_name = match.iloc[0]["File Name"]
                            icon_path = DataConfigClass.get_resource_path("assets", "images", "Item Icons", file_name)
                            icon_pixmap = QPixmap(icon_path)
                    except Exception as e:
                        print(f"[アイコンエラー] {key}: {e}")
                
                # ラベルの更新
                row["rank_label"].setText(rank_text)
                row["name_label"].setText(name_text)
                row["value_label"].setText(value_text)
                row["original_name_text"] = name_text
                row["original_value_text"] = value_text
                row["icon_pixmap"] = icon_pixmap
                
                # アイコンの設定（スケーリングはresizeEventで行う）
                row["icon_label"].setVisible(False)  # 更新時も一旦非表示
                if icon_pixmap and not icon_pixmap.isNull():
                    # Pixmapは設定するが表示はしない
                    row["icon_label"].setPixmap(icon_pixmap)
                else:
                    row["icon_label"].clear()
                
                # 下線の設定
                row["widget"].setStyleSheet("border-bottom: 1px solid #aaa;")
                
            else:
                # 空行の処理
                row["rank_label"].setText("")
                row["name_label"].setText("")
                row["value_label"].setText("")
                row["original_name_text"] = ""
                row["original_value_text"] = ""
                row["icon_pixmap"] = None
                row["icon_label"].clear()
                row["icon_label"].setVisible(False)  # 空行のアイコンも非表示
                row["widget"].setStyleSheet("")
        
        # 強制的に再描画
        self.update()
        
        # ウィジェットが表示されている場合のみ、遅延リサイズを実行
        if self.isVisible():
            self._schedule_resize()

    def _initial_resize(self):
        """初期化時のリサイズ処理"""
        if self.width() > 0 and self.height() > 0:
            self._internal_resize()

    def _schedule_resize(self):
        """遅延リサイズを実行（適切なタイミングでリサイズ処理を行う）"""
        # QTimerを使用して、レイアウト更新後にリサイズ処理を実行
        QTimer.singleShot(10, self._perform_delayed_resize)

    def _perform_delayed_resize(self):
        """遅延リサイズの実際の処理"""
        if self.isVisible() and self.width() > 0 and self.height() > 0:
            # 現在のサイズで強制的にリサイズイベントを発火
            self._internal_resize()

    def _internal_resize(self):
        """内部リサイズ処理（resizeEventの内容を直接実行）"""
        if not self.isVisible() or self.width() <= 0 or self.height() <= 0:
            return
            
        row_height = self.height() // 10

        # 名前ラベルの最小フォントサイズを事前に計算
        min_name_font_size = 12  # 最大サイズから開始
        
        for row in self.row_widgets:
            original_name_text = row["original_name_text"]
            if original_name_text:
                # 実際の利用可能な幅を正確に計算
                widget_width = self.width()  # テーブル全体の幅を使用
                rank_width = 20  # 固定幅
                
                # アイコンの実際の幅を取得
                icon_width = 0
                icon_label = row["icon_label"]
                if icon_label and row["icon_pixmap"] and not row["icon_pixmap"].isNull():
                    # 元のアイコンサイズから計算（スケール後のサイズではなく）
                    scaled_height = row_height - 4
                    original_pixmap = row["icon_pixmap"]
                    scaled_width = int(original_pixmap.width() * scaled_height / original_pixmap.height())
                    icon_width = scaled_width + 4  # スペーシング分も含める
                
                # 値表示の幅を動的に計算
                original_value_text = row["original_value_text"]
                if original_value_text:
                    temp_font = QFont("Meiryo", 10)
                    temp_metrics = QFontMetrics(temp_font)
                    value_width = temp_metrics.horizontalAdvance(original_value_text) + 10
                else:
                    value_width = 50
                    
                spacing = 4 * 3  # レイアウトのスペーシング
                
                # 名前ラベルの利用可能幅（より余裕を持って計算）
                name_available_width = widget_width - rank_width - icon_width - value_width - spacing
                
                # この行で必要な最小フォントサイズを計算
                target_width = max(name_available_width - 8, 50)  # 最小幅も確保
                
                # 必要なフォントサイズを計算
                font = QFont("Meiryo")
                required_font_size = 8  # 最小サイズ
                
                # 0.1pt刻みで最適なサイズを探す（最大サイズから降順で）
                for size_int in range(int(12 * 10), int(8 * 10) - 1, -1):
                    size = size_int / 10.0
                    font.setPointSizeF(size)
                    metrics = QFontMetrics(font)
                    text_width = metrics.horizontalAdvance(original_name_text)
                    
                    if text_width <= target_width:
                        required_font_size = size
                        break
                
                # 全体の最小サイズを更新
                min_name_font_size = min(min_name_font_size, required_font_size)

        # 実際の描画処理
        for row in self.row_widgets:
            widget = row["widget"]
            icon_label = row["icon_label"]
            icon_pixmap = row["icon_pixmap"]
            rank_label = row["rank_label"]
            name_label = row["name_label"]
            value_label = row["value_label"]
            original_name_text = row["original_name_text"]
            original_value_text = row["original_value_text"]

            widget.setFixedHeight(row_height)
            
            # アイコンの調整
            if icon_label:
                if icon_pixmap and not icon_pixmap.isNull():
                    # 適切なサイズでスケーリングしてから表示
                    scaled_pixmap = icon_pixmap.scaledToHeight(row_height - 4, Qt.SmoothTransformation)
                    icon_label.setPixmap(scaled_pixmap)
                    icon_label.setVisible(True)  # サイズ調整後に表示
                else:
                    icon_label.clear()
                    icon_label.setVisible(False)

            # 実際の利用可能な幅を正確に計算
            widget_width = self.width()  # テーブル全体の幅を使用
            rank_width = 20  # 固定幅
            
            # アイコンの実際の幅を取得
            icon_width = 0
            if icon_label and icon_label.pixmap():
                icon_width = icon_label.pixmap().width() + 4  # スペーシング分も含める
            
            # 値表示の幅を動的に計算
            if original_value_text:
                temp_font = QFont("Meiryo", 10)
                temp_metrics = QFontMetrics(temp_font)
                value_width = temp_metrics.horizontalAdvance(original_value_text) + 10
            else:
                value_width = 50
                
            spacing = 4 * 3  # レイアウトのスペーシング
            
            # 値ラベルの利用可能幅
            value_available_width = value_width
            
            # 名前ラベルのフォントサイズを統一された最小サイズに設定
            if original_name_text:
                font = QFont("Meiryo")
                font.setPointSizeF(min_name_font_size)
                name_label.setFont(font)
                name_label.setText(original_name_text)
            
            # 値ラベルのフォントサイズを調整（個別に）
            if original_value_text:
                self.adjustFontSize(value_label, original_value_text, value_available_width, 12, 8)
            
            # ランクラベルのフォントサイズも調整（個別に）
            if rank_label.text():
                self.adjustFontSize(rank_label, rank_label.text(), rank_width, 12, 8)
        
        # サイズ調整完了フラグを設定
        self._is_properly_sized = True

    def showEvent(self, event):
        """ウィジェットが表示された時に呼ばれる"""
        super().showEvent(event)
        # 表示直前に即座にリサイズを実行（ちらつき防止）
        if self.width() > 0 and self.height() > 0:
            self._internal_resize()
        # さらに遅延リサイズも実行（念のため）
        self._schedule_resize()

    def adjustFontSize(self, label, text, available_width, max_font_size=10, min_font_size=6):
        """ラベルのフォントサイズを利用可能な幅に合わせて調整"""
        if not text:
            return
        
        # 利用可能な幅からマージンを引く
        target_width = max(available_width - 8, 50)  # 最小幅も確保
        
        # 最大サイズから0.1pt刻みで調整
        best_size = min_font_size
        font = QFont("Meiryo")
        
        # 0.1pt刻みで最適なサイズを探す（最大サイズから降順で）
        for size_int in range(int(max_font_size * 10), int(min_font_size * 10) - 1, -1):
            size = size_int / 10.0
            font.setPointSizeF(size)
            metrics = QFontMetrics(font)
            text_width = metrics.horizontalAdvance(text)
            
            if text_width <= target_width:
                best_size = size
                break
        
        # 最終的なフォントサイズを設定
        font.setPointSizeF(best_size)
        label.setFont(font)
        
        # テキストをそのまま設定（省略なし）
        label.setText(text)

    def resizeEvent(self, event):
        """リサイズイベント"""
        super().resizeEvent(event)
        self._internal_resize()