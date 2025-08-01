from PyQt5.QtWidgets import QWidget, QTableWidget, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QHeaderView, QAbstractItemView, QTableWidgetItem
from PyQt5.QtGui import QColor, QPainter, QPixmap, QFont, QFontMetrics
from PyQt5.QtCore import Qt, QRect, QSize, QTimer
import os
""""""
from data_config import DataConfigClass, POKEMON_TYPE_COLOR

class PokemonStatsBarChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stats_data = {}
        self.setMinimumSize(300, 200)
        # サイズポリシーを設定して親のサイズに追従
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_data(self, stats_dict):
        self.stats_data = stats_dict
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if not self.stats_data:
            return
            
        # 描画領域の設定
        margin = 10
        chart_width = self.width() - 2 * margin
        chart_height = self.height() - 2 * margin
        
        # 統計名とその順序
        stat_names = ["HP", "こうげき", "ぼうぎょ", "とくこう", "とくぼう", "すばやさ", "合計"]
        
        # 実際の高さに基づいてバーの高さを動的に計算
        available_height = chart_height - 10  # 上下の余白
        bar_height = available_height // len(stat_names)
        
        # 最大値を設定（合計以外は255、合計は780程度）
        max_single_stat = 255
        max_total_stat = 780
        
        # フォントサイズを高さに応じて調整
        font_size = max(8, min(12, bar_height // 2))
        font = QFont("Meiryo", font_size)
        painter.setFont(font)
        
        # ラベル幅を動的に計算
        font_metrics = QFontMetrics(font)
        label_width = max([font_metrics.width(name) for name in stat_names]) + 10
        
        for i, stat_name in enumerate(stat_names):
            if stat_name not in self.stats_data:
                continue
                
            value = self.stats_data[stat_name]
            y_pos = margin + i * bar_height
            
            # 最大値の設定
            max_value = max_total_stat if stat_name == "合計" else max_single_stat
            
            # バーの幅を計算（ラベル幅と値表示スペースを考慮）
            bar_area_width = chart_width - label_width - 10  # 値表示用の余白
            bar_width = int((value / max_value) * bar_area_width)
            
            # 背景バー
            painter.setBrush(QColor(220, 220, 220))
            painter.setPen(Qt.NoPen)
            bg_rect = QRect(margin + label_width, y_pos + 2, bar_area_width, bar_height - 4)
            painter.drawRoundedRect(bg_rect, 2, 2)
            
            # 値バー
            if stat_name == "合計":
                painter.setBrush(QColor(255, 140, 0))  # オレンジ
            else:
                painter.setBrush(QColor(70, 130, 180))  # スチールブルー
            
            if bar_width > 0:
                value_rect = QRect(margin + label_width, y_pos + 2, bar_width, bar_height - 4)
                painter.drawRoundedRect(value_rect, 2, 2)
            
            # ラベル
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(QRect(margin, y_pos, label_width - 5, bar_height), Qt.AlignVCenter | Qt.AlignLeft, stat_name)
            
            # 値をグラフ内側右端に表示
            value_text = str(value)
            value_text_width = font_metrics.width(value_text)
            
            # 値の表示位置を計算（グラフ内側右端）
            if bar_width > value_text_width + 10:  # バーが十分に長い場合は内側に表示
                text_x = margin + label_width + bar_width - value_text_width - 5
                painter.setPen(QColor(255, 255, 255))  # 白文字
            else:  # バーが短い場合は外側に表示
                text_x = margin + label_width + bar_width + 5
                painter.setPen(QColor(0, 0, 0))  # 黒文字
            
            painter.drawText(QRect(text_x, y_pos, value_text_width + 10, bar_height), Qt.AlignVCenter | Qt.AlignLeft, value_text)

    def sizeHint(self):
        """推奨サイズを返す"""
        return QSize(300, 200)

    def minimumSizeHint(self):
        """最小サイズを返す"""
        return QSize(250, 150)

class PokemonStatsTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupTable()

    def setupTable(self):
        self.setRowCount(6)
        self.setColumnCount(5)
        
        # ヘッダー設定
        row_headers = ["HP", "こうげき", "ぼうぎょ", "とくこう", "とくぼう", "すばやさ"]
        col_headers = ["最大", "準", "無振", "下降", "最小"]
        
        self.setVerticalHeaderLabels(row_headers)
        self.setHorizontalHeaderLabels(col_headers)
        
        # スクロールバーを非表示
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # クリックとドラッグを無効化
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setFocusPolicy(Qt.NoFocus)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # ヘッダーの操作を無効化
        self.horizontalHeader().setSectionsClickable(False)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.horizontalHeader().setCursor(Qt.ArrowCursor)

        self.verticalHeader().setSectionsClickable(False)
        self.verticalHeader().setHighlightSections(False)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setCursor(Qt.ArrowCursor)
        
        # テーブルの見た目を調整
        self.setAlternatingRowColors(True)
        self.setShowGrid(True)
        self.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f0f0f0;
                font-family: Meiryo;
                font-size: 10px;
                border: 1px solid #ccc;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                border: 1px solid #ccc;
                padding: 4px;
                font-weight: bold;
            }
        """)

    def set_data(self, stats_data):
        for row in range(6):
            for col in range(5):
                if row < len(stats_data) and col < len(stats_data[row]):
                    item = QTableWidgetItem(str(stats_data[row][col]))
                    item.setTextAlignment(Qt.AlignCenter)
                    # アイテムを選択不可にする
                    item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
                    self.setItem(row, col, item)

        # データ更新後にフォントサイズを調整
        self._adjust_all_fonts()

    def adjustFontSizeToFit(self, item, width, height, max_font_size=18, min_font_size=6):
        """セルサイズに収まる最大フォントサイズを自動設定"""
        font = QFont("Meiryo")
        for size in range(max_font_size, min_font_size - 1, -1):
            font.setPointSize(size-5)
            metrics = QFontMetrics(font)
            if metrics.horizontalAdvance(item.text()) <= width and metrics.height() <= height:
                item.setFont(font)
                return
        # 最小でも合わなければ最小で設定
        font.setPointSize(min_font_size)
        item.setFont(font)

    def resizeEvent(self, event):
        """テーブルサイズが変更されたときに列と行のサイズを調整"""
        super().resizeEvent(event)

        # ヘッダーサイズを動的に調整
        available_header_height = self.height() // 7
        self.horizontalHeader().setFixedHeight(available_header_height)

        available_width = self.viewport().width()
        available_height = self.viewport().height()

        col_width = available_width // self.columnCount()
        row_height = available_height // self.rowCount()

        remaining_width = available_width - (col_width * self.columnCount())
        remaining_height = available_height - (row_height * self.rowCount())

        for col in range(self.columnCount()):
            self.setColumnWidth(col, col_width + (1 if col < remaining_width else 0))

        for row in range(self.rowCount()):
            self.setRowHeight(row, row_height + (1 if row < remaining_height else 0))

        # 各セルのフォントサイズ調整
        self._adjust_all_fonts()

    def _adjust_all_fonts(self):
        """全セルのフォントサイズを調整"""
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    cell_width = self.columnWidth(col)
                    cell_height = self.rowHeight(row)
                    self.adjustFontSizeToFit(item, cell_width - 4, cell_height - 4)


    def sizeHint(self):
        """テーブルの推奨サイズを親から決定されるように変更"""
        # 親のサイズに合わせるため、最小限のサイズを返す
        return QSize(200, 50)

    def minimumSizeHint(self):
        """最小サイズを返す"""
        return QSize(200, 50)

    def mousePressEvent(self, event):
        """マウスクリックを無効化"""
        return

    def mouseMoveEvent(self, event):
        """マウスドラッグを無効化"""
        return

    def mouseReleaseEvent(self, event):
        """マウスリリースを無効化"""
        return

    def keyPressEvent(self, event):
        """キーボード入力を無効化"""
        return

class PokemonTypeLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.type_name = ""
        self.setMinimumSize(80, 30)
        self.setAlignment(Qt.AlignCenter)
        self.base_font_size = 13  # ベースフォントサイズ
        self.setStyleSheet("""
            color: white; 
            font-weight: bold; 
            font-size: 13px;
            font-family: Meiryo;
            padding: 0px 12px;
            border: 2px solid rgba(255, 255, 255, 0.3);
        """)

    def set_type(self, type_name):
        self.type_name = type_name
        self.setText(type_name.upper())
        if type_name in POKEMON_TYPE_COLOR:
            color = POKEMON_TYPE_COLOR[type_name]
            if len(color) == 4:
                bg_color_str = f"rgba({color[0]}, {color[1]}, {color[2]}, {color[3]})"
            else:
                bg_color_str = f"rgb({color[0]}, {color[1]}, {color[2]})"
            
            self._update_style(bg_color_str)
        else:
            self._update_style()

    def _update_style(self, bg_color_str=None):
        """スタイルを更新（フォントサイズとborder-radiusを含む）"""
        height = self.height()
        
        # フォントサイズを高さに応じて調整（最小8px、最大24px）
        font_size = max(8, min(24, int(height * 0.6)))
        
        # border-radiusを高さの半分に設定
        border_radius = height // 2
        
        base_style = f"""
            color: white; 
            font-weight: bold; 
            font-size: {font_size}px;
            font-family: Meiryo;
            padding: 0px 12px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: {border_radius}px;
        """
        
        if bg_color_str:
            style = f"background-color: {bg_color_str}; {base_style}"
        else:
            style = base_style
            
        self.setStyleSheet(style)

    def resizeEvent(self, event):
        """サイズ変更時にスタイルを更新"""
        super().resizeEvent(event)
        
        # タイプが設定されている場合は背景色も含めて更新
        if self.type_name and self.type_name in POKEMON_TYPE_COLOR:
            color = POKEMON_TYPE_COLOR[self.type_name]
            if len(color) == 4:
                bg_color_str = f"rgba({color[0]}, {color[1]}, {color[2]}, {color[3]})"
            else:
                bg_color_str = f"rgb({color[0]}, {color[1]}, {color[2]})"
            self._update_style(bg_color_str)
        else:
            self._update_style()

class SquareImageContainer(QWidget):
    """高さと同じ幅を持つ正方形画像コンテナ"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        
    def resizeEvent(self, event):
        """リサイズ時に高さと同じ幅に設定"""
        super().resizeEvent(event)
        # 高さと同じ幅に設定して正方形にする
        height = self.height()
        if height > 0:
            self.setFixedWidth(height)

class PokemonInfoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_pokemon_name = None  # 現在のポケモン名を保持
        self.setupUI()

    def setupUI(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(15, 0, 15, 0)
        
        # 左側: 基本情報
        left_widget = QWidget()
        left_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 15px;
                border: 2px solid rgba(52, 152, 219, 0.3);
            }
        """)
        left_layout = QHBoxLayout(left_widget)
        left_layout.setSpacing(15)
        left_layout.setContentsMargins(15, 10, 15, 10)
        
        # ポケモン画像（正方形コンテナを使用）
        self.image_container = SquareImageContainer()
        image_layout = QVBoxLayout(self.image_container)
        image_layout.setAlignment(Qt.AlignCenter)
        image_layout.setContentsMargins(0, 0, 0, 0)
        
        self.pokemon_image = QLabel()
        self.pokemon_image.setMinimumSize(60, 60)
        self.pokemon_image.setScaledContents(False)
        self.pokemon_image.setAlignment(Qt.AlignCenter)
        self.pokemon_image.setStyleSheet("""
            QLabel {
                background-color: rgba(236, 240, 241, 0.8);
                border-radius: 40px;
                border: 2px solid rgba(52, 152, 219, 0.4);
                padding: 3px;
            }
        """)
        
        image_layout.addWidget(self.pokemon_image)
        
        # 右側の情報部分
        info_container = QWidget()
        info_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        info_layout = QVBoxLayout(info_container)
        info_layout.setSpacing(0)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        # ポケモン名
        self.pokemon_name = QLabel("ポケモン名")
        self.pokemon_name.setStyleSheet("""
            QLabel {
                font-family: 'Meiryo';
                font-size: 24px; 
                font-weight: bold; 
                color: #2c3e50;
                margin-bottom: 3px;
            }
        """)
        
        # タイプ表示コンテナ
        type_container = QWidget()
        type_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        type_layout = QHBoxLayout(type_container)
        type_layout.setSpacing(8)  # タイプラベル間のスペース
        type_layout.setContentsMargins(0, 0, 0, 0)
        type_layout.setAlignment(Qt.AlignLeft)
        
        self.type_1 = PokemonTypeLabel()
        self.type_2 = PokemonTypeLabel()
        
        # タイプラベルのサイズポリシーを調整
        self.type_1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.type_2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        type_layout.addWidget(self.type_1)
        type_layout.addWidget(self.type_2)
        # 右側にストレッチを追加して、タイプラベルが左寄せになるようにする
        type_layout.addStretch()
        
        # 基本データ
        self.stats_container = QWidget()
        self.stats_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.stats_container.setStyleSheet("""
            QWidget {
                background-color: rgba(241, 245, 249, 0.9);
                border-radius: 8px;
                border: 1px solid rgba(203, 213, 225, 0.8);
                padding: 3px;
            }
        """)
        stats_layout = QVBoxLayout(self.stats_container)
        stats_layout.setSpacing(4)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        
        # 基本データラベル（初期スタイル）
        self.usage_label = QLabel("採用率: --")
        self.height_label = QLabel("高さ: --")
        self.weight_label = QLabel("重さ: --")
        
        # 初期フォントサイズ設定
        self._update_stats_font_size()
        
        stats_layout.addWidget(self.usage_label)
        stats_layout.addWidget(self.height_label)
        stats_layout.addWidget(self.weight_label)
        
        # レイアウト構成
        info_layout.addWidget(self.pokemon_name, 1)
        info_layout.addWidget(type_container, 1)
        info_layout.addWidget(self.stats_container, 3)
        
        # 左側レイアウトに追加（正方形コンテナを使用）
        left_layout.addWidget(self.image_container, 1)
        left_layout.addWidget(info_container, 1)
        
        # 中央: 種族値チャート
        self.stats_chart = PokemonStatsBarChart()
        self.stats_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.stats_chart.setMinimumSize(300, 160)
        self.stats_chart.setMaximumWidth(400)
        
        # 右側: 実数値テーブル
        self.stats_table = PokemonStatsTable()
        self.stats_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.stats_table.setMinimumSize(300, 130)
        
        # メインレイアウトに追加
        main_layout.addWidget(left_widget, 3)
        main_layout.addWidget(self.stats_chart, 2)
        main_layout.addWidget(self.stats_table, 2)

    def _update_stats_font_size(self):
        """基本データラベルのフォントサイズを更新"""
        # stats_containerの実際のサイズを取得
        container_size = self.stats_container.size()
        container_height = max(60, container_size.height())
        container_width = max(100, container_size.width())
        
        # コンテナのサイズに基づいてフォントサイズを計算
        # 高さベースのフォントサイズ計算
        height_based_size = max(10, min(22, int(container_height / 7)))
        # 幅ベースのフォントサイズ計算（長いテキストを考慮）
        width_based_size = max(10, min(22, int(container_width / 20)))
        
        # より制限的な方を採用
        font_size = min(height_based_size, width_based_size)
        
        label_style = f"""
            QLabel {{
                font-family: 'Meiryo';
                font-size: {font_size}px;
                font-weight: 600;
                color: #475569;
                padding: 2px 0px;
            }}
        """
        
        self.usage_label.setStyleSheet(label_style)
        self.height_label.setStyleSheet(label_style)
        self.weight_label.setStyleSheet(label_style)

    def _update_type_labels_size(self):
        """タイプラベルのサイズを更新"""
        # type_containerの実際のサイズを取得
        type_container = self.type_1.parent()
        if type_container:
            container_size = type_container.size()
            container_height = max(30, container_size.height())
            container_width = max(60, container_size.width())
            
            # タイプラベルの高さを計算（コンテナの80%程度）
            type_height = max(20, int(container_height * 0.8))
            
            # タイプラベルの幅を計算（2つのタイプがある場合を考慮）
            available_width = container_width - 8  # スペース分を差し引く
            type_width = max(40, int(available_width / 2.5))  # 余裕を持たせる
            
            # 最大サイズを制限
            type_height = min(type_height, 50)
            type_width = min(type_width, 120)
            
            # タイプラベルのサイズを設定
            self.type_1.setMinimumSize(type_width, type_height)
            self.type_1.setMaximumSize(type_width * 2, type_height)  # 最大幅は2倍まで
            
            if self.type_2.isVisible():
                self.type_2.setMinimumSize(type_width, type_height)
                self.type_2.setMaximumSize(type_width * 2, type_height)

    def _update_pokemon_image(self):
        """ポケモン画像のサイズを更新"""
        if not self.current_pokemon_name:
            return
            
        try:
            # ポケモンデータの取得
            pokemon_data = DataConfigClass.pokemon_datas[DataConfigClass.pokemon_datas["alias"] == self.current_pokemon_name]
            if pokemon_data.empty:
                return
                
            pokemon_row = pokemon_data.iloc[0]
            
            # 画像設定（正方形画像を考慮した最大サイズ表示）
            image_path = f"./img/Pokemon_Icons/{pokemon_row['image_file']}"
            if os.path.exists(image_path):
                original_pixmap = QPixmap(image_path)
                
                # 正方形コンテナのサイズを取得
                container_size = self.image_container.size()
                # コンテナの余白を考慮
                available_size = max(60, min(container_size.width(), container_size.height()) - 20)
                
                # 最小サイズを保証し、最大サイズを200に制限
                max_size = max(60, min(200, available_size))
                target_size = QSize(max_size, max_size)
                
                # 正方形サイズでスケーリング
                scaled_pixmap = original_pixmap.scaled(
                    target_size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.pokemon_image.setPixmap(scaled_pixmap)
                
        except Exception as e:
            print(f"ポケモン画像更新エラー: {e}")

    def resizeEvent(self, event):
        """ウィンドウサイズ変更時の動的調整"""
        super().resizeEvent(event)
        
        # ポケモン名のフォントサイズ調整
        name_height = max(50, self.height() * 0.2)
        name_font_size = max(16, min(32, int(name_height / 2)))
        self.pokemon_name.setStyleSheet(f"""
            QLabel {{
                font-family: 'Meiryo';
                font-size: {name_font_size}px; 
                font-weight: bold; 
                color: #2c3e50;
                margin-bottom: 3px;
            }}
        """)
        
        self._update_stats_font_size()
        self._update_type_labels_size()
        self._update_pokemon_image()

    def showEvent(self, event):
        """ウィジェットが表示される際の処理"""
        super().showEvent(event)
        self._update_stats_font_size()
        self._update_type_labels_size()
        self._update_pokemon_image()

    def set_pokemon_data(self, pokemon_name):
        try:
            self.current_pokemon_name = pokemon_name  # 現在のポケモン名を保存
            
            # ポケモンデータの取得
            pokemon_data = DataConfigClass.pokemon_datas[DataConfigClass.pokemon_datas["alias"] == pokemon_name]
            if pokemon_data.empty:
                return
                
            pokemon_row = pokemon_data.iloc[0]
            
            # バトルデータの取得
            battle_data = DataConfigClass.battle_datas[DataConfigClass.battle_datas["alias"] == pokemon_name]
            battle_row = battle_data.iloc[0] if not battle_data.empty else None
            
            # 画像設定（_update_pokemon_imageで処理）
            self._update_pokemon_image()
            
            # 名前設定
            self.pokemon_name.setText(pokemon_name)
            
            # タイプ設定
            self.type_1.set_type(pokemon_row["type_1"])
            if isinstance(pokemon_row["type_2"], str):
                self.type_2.set_type(pokemon_row["type_2"])
                self.type_2.setVisible(True)
            else:
                self.type_2.setVisible(False)
            
            # タイプラベルのサイズを更新
            QTimer.singleShot(10, self._update_type_labels_size)
            
            # 使用率設定
            if battle_row is not None:
                usage_rate = battle_row.get("usage_rate", 0)
                rank = battle_row.get("rank", 9999)
                if rank != 9999:
                    self.usage_label.setText(f"採用率: {rank}位")
                else:
                    self.usage_label.setText(f"採用率: 圏外")
            else:
                self.usage_label.setText("採用率: --")
            
            # 高さ・重さ設定
            height = pokemon_row["height"]
            weight = pokemon_row["weight"]
            
            self.height_label.setText(f"高さ: {height:.1f}m")
            
            # けたぐりの威力計算
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
            
            self.weight_label.setText(f"重さ: {weight:.1f}kg (けたぐりの威力: {low_kick_damage})")
            
            # 種族値設定
            h = pokemon_row['H']
            a = pokemon_row['A']
            b = pokemon_row['B']
            c = pokemon_row['C']
            d = pokemon_row['D']
            s = pokemon_row['S']
            total = h + a + b + c + d + s
            
            base_stats = {
                "HP": h,
                "こうげき": a,
                "ぼうぎょ": b,
                "とくこう": c,
                "とくぼう": d,
                "すばやさ": s,
                "合計": total
            }
            
            self.stats_chart.set_data(base_stats)
            
            # 実数値テーブル設定
            stats_data = [
                [pokemon_row['H_max'], pokemon_row['H_boost'], pokemon_row['H_neutral'], pokemon_row['H_weaken'], pokemon_row['H_min']],
                [pokemon_row['A_max'], pokemon_row['A_boost'], pokemon_row['A_neutral'], pokemon_row['A_weaken'], pokemon_row['A_min']],
                [pokemon_row['B_max'], pokemon_row['B_boost'], pokemon_row['B_neutral'], pokemon_row['B_weaken'], pokemon_row['B_min']],
                [pokemon_row['C_max'], pokemon_row['C_boost'], pokemon_row['C_neutral'], pokemon_row['C_weaken'], pokemon_row['C_min']],
                [pokemon_row['D_max'], pokemon_row['D_boost'], pokemon_row['D_neutral'], pokemon_row['D_weaken'], pokemon_row['D_min']],
                [pokemon_row['S_max'], pokemon_row['S_boost'], pokemon_row['S_neutral'], pokemon_row['S_weaken'], pokemon_row['S_min']]
            ]
            
            self.stats_table.set_data(stats_data)
            
        except Exception as e:
            print(f"ポケモンデータ設定エラー: {e}")

    def sizeHint(self):
        return QSize(200, 100)

    def minimumSizeHint(self):
        return QSize(200, 100)