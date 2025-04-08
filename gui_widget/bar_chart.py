from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QGraphicsDropShadowEffect, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QBrush, QLinearGradient, QPainter

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