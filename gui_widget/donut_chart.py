import pyqtgraph as pg
import numpy as np
import itertools

from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QGraphicsPathItem, QFrame
from PyQt5.QtCore import Qt, QTimer, QElapsedTimer
from PyQt5.QtGui import QPainterPath, QPixmap, QFont, QFontMetrics

""""""
from data_config import DataConfigClass, GraphDataType, SLICES_COLORS, POKEMON_TYPE_COLOR

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
        
        # ドーナツグラフ
        self.donut_chart_widget = DonutChart(data_type=data_type, data={}, parent=self.container_frame)
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
        
        # データをリセット
        self.reset_data()

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

    def reset_data(self):
        """
        テーブルとグラフを完全にリセットする
        
        データ更新前に呼び出すことで、以前のデータの残存を防ぎ、
        クリーンな状態でデータを再設定できるようにする
        """
        # アニメーションタイマーが動いていれば停止
        if hasattr(self.donut_chart_widget, 'timer') and self.donut_chart_widget.timer.isActive():
            self.donut_chart_widget.timer.stop()
        
        # ドーナツチャートのリセット
        self.donut_chart_widget.view.clear()  # ビューの中身を消去
        self.donut_chart_widget.slices.clear()  # スライスリストをクリア
        self.donut_chart_widget.labels.clear()  # ラベルリストをクリア
        self.donut_chart_widget.full_angle = 0  # アニメーション角度をリセット
        self.donut_chart_widget.data = {}  # データをクリア
        
        # テーブルウィジェットの削除
        if hasattr(self, 'table_widget') and self.table_widget:
            # テーブルウィジェットをレイアウトから削除
            if self.table_widget.parentWidget():
                self.container_layout.removeWidget(self.table_widget)
            self.table_widget.deleteLater()
            self.table_widget = QWidget()
            self.table_widget.setVisible(False)
        
        # 表示状態を更新
        self.update_visibility(False)
        
        # レイアウトの更新を促す
        self.updateGeometry()

    def resize(self):
        """ ウィジェットのリサイズ処理 """
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # コンテナの実際のサイズを取得
        container_width = self.container_frame.width()
        container_height = self.container_frame.height()
        
        # タイトルの高さを設定 (コンテナの高さの5%)
        title_height = int(container_height * 0.05)
        self.title_label.setFixedHeight(title_height)
        
        # ドーナツチャートの高さを設定 (コンテナの高さの40%)
        chart_height = int(container_height * 0.4)
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
