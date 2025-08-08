from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QPushButton
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QResizeEvent
from PyQt5.QtCore import Qt, QTimer, QEvent
""""""
from gui_widget.pokemon_info_widget import PokemonInfoWidget
from gui_widget.chart_widget import ChartWidget
from data_config import DataConfigClass, GraphDataType

class OverlayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_pokemon = "ディンルー"  # デフォルトのポケモン
        
        # 独立したウィンドウとして設定（test_second.pyと同じ方式）
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        
        # ウィンドウフラグを設定してOpenGLウィジェットの上に表示
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setWindowOpacity(0.85)  # 全体の透明度
        
        # リサイズ処理のフラグ
        self._geometry_update_pending = False
        
        self.setupData()
        self.setupUI()
        self.hide()

    def paintEvent(self, event):
        """カスタム描画イベントで背景色とボーダーを描画"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # コンポジションモードを設定
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        
        # 背景を完全にクリア
        painter.fillRect(self.rect(), Qt.transparent)
        
        # 半透明背景を描画
        background_color = QColor(255, 255, 255, 180)  # より透明に
        background_brush = QBrush(background_color)
        painter.setBrush(background_brush)
        
        # ボーダーを描画
        border_pen = QPen(QColor(200, 200, 200, 180), 2)
        painter.setPen(border_pen)
        
        # 角丸四角形を描画
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(rect, 10, 10)
        
        painter.end()

    def mousePressEvent(self, event):
        """マウスクリックイベントの処理"""
        if event.button() == Qt.LeftButton:
            # クリックされた位置にあるウィジェットを取得
            clicked_widget = self.childAt(event.pos())
            
            # クリックされたウィジェットがボタンかどうかをチェック
            if self._is_button_or_button_child(clicked_widget):
                # ボタンの場合は通常の処理を継続
                super().mousePressEvent(event)
                return
            
            # ボタン以外の場合はオーバーレイを非表示にする
            self.hide()
        else:
            super().mousePressEvent(event)
    
    def _is_button_or_button_child(self, widget):
        """
        指定されたウィジェットがボタンまたはボタンの子要素かどうかを判定
        
        Args:
            widget: チェック対象のウィジェット
            
        Returns:
            bool: ボタンまたはボタンの子要素の場合True
        """
        if widget is None:
            return False
        
        # 現在のウィジェットから親を辿ってボタンを探す
        current_widget = widget
        while current_widget is not None:
            # QPushButtonかどうかをチェック
            if isinstance(current_widget, QPushButton):
                return True
            
            # FormSwitchButtonのようなカスタムボタンもチェック
            # (pokemon_info_widget.pyで定義されているFormSwitchButton)
            class_name = current_widget.__class__.__name__
            if 'Button' in class_name:
                return True
            
            # 親ウィジェットに移動
            current_widget = current_widget.parent()
            
            # 自分自身（OverlayWidget）まで辿り着いたら終了
            if current_widget == self:
                break
        
        return False

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
        main_layout.setContentsMargins(15, 15, 15, 15)

        # ポケモン情報部分
        self.pokemon_info = PokemonInfoWidget()
        self.pokemon_info.set_pokemon_data(self.current_pokemon)
        # 子ウィジェットも透明に設定
        self.pokemon_info.setAttribute(Qt.WA_TranslucentBackground, True)
        self.pokemon_info.setStyleSheet("background-color: rgba(255, 255, 255, 120);")
        
        # ウーラオス型切り替えシグナルを接続
        self.pokemon_info.form_switched.connect(self.set_pokemon)

        # チャート部分
        self.charts_container = QWidget()
        self.charts_container.setContentsMargins(0, 0, 0, 0)
        self.charts_container.setStyleSheet("background-color: transparent;")
        self.charts_container.setAttribute(Qt.WA_TranslucentBackground, True)

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
            chart.setAttribute(Qt.WA_TranslucentBackground, True)
            chart.setStyleSheet("background-color: rgba(255, 255, 255, 100);")
            self.charts.append(chart)
            self.horizontal_layout.addWidget(chart, 0, Qt.AlignCenter)

        # ボタン部分
        self.close_button = QPushButton("閉じる")
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(231, 76, 60, 200); 
                color: white; 
                border: none; 
                padding: 5px 30px; 
                font-size: 16px; 
                border-radius: 5px; 
                margin: 0px;
            }
            QPushButton:hover {
                background-color: rgba(192, 57, 43, 220);
            }
        """)
        self.close_button.clicked.connect(self.hide)

        self.button_container = QWidget()
        self.button_container.setContentsMargins(0, 0, 0, 0)
        self.button_container.setStyleSheet("background-color: transparent;")
        self.button_container.setAttribute(Qt.WA_TranslucentBackground, True)
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

    def resizeEvent(self, event):
        """リサイズイベントのオーバーライド"""
        super().resizeEvent(event)

    def show(self):
        """show時の処理、最前面にする"""
        super().show()
        self.raise_()  # 最前面に表示
        self.activateWindow()  # ウィンドウをアクティブにする

    def hide(self):
        """hide時の処理"""
        super().hide()
        # 非表示時にジオメトリ情報をクリア
        self._reset_geometry_cache()

    def _reset_geometry_cache(self):
        """ジオメトリキャッシュをリセット"""
        # 次回表示時に前回のサイズが影響しないようにリセット
        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)  # Qt default maximum size

    def set_pokemon(self, pokemon_name):
        """
        データ表示するポケモンを変更する

        Args:
        - pokemon_name (str): 表示したいポケモンの名前
        """
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
                
                # アニメーションを再開始
                self.charts[i].chart.animation_progress = 0.0
                self.charts[i].chart.startAnimation()
                
                # テーブルがある場合は更新
                if hasattr(self.charts[i], 'table') and self.charts[i].table:
                    self.charts[i].table.update_data(data)
        
        # データ更新後の再描画
        self.repaint()

    def adjustSizes(self, overlay_width, overlay_height):
        """
        リサイズされたOverlayWidgetのレイアウトの調整

        Args:
        - overlay_width (int): リサイズ後のOverlayWidgetの横幅
        - overlay_height (int): リサイズ後のOverlayWidgetの高さ
        """
        # 無限ループを防ぐためのフラグ
        if hasattr(self, '_adjusting_sizes') and self._adjusting_sizes:
            return
        
        self._adjusting_sizes = True
        
        try:        
            # ウィジェット自体のサイズ調整はMainWindowの方に任せて、レイアウトのみ調整
            
            # 高さの利用可能領域の計算
            main_layout = self.layout()
            if not main_layout:
                return
                
            total_margin = main_layout.contentsMargins().top() + main_layout.contentsMargins().bottom()
            total_spacing = main_layout.spacing() * 2  # between three rows
            available_height = overlay_height - total_margin - total_spacing

            # 各UIへの高さ振り分け
            info_h = int(available_height * 0.25)
            charts_h = int(available_height * 0.7)
            button_h = available_height - info_h - charts_h

            # 高さセット
            self.pokemon_info.setFixedHeight(info_h)
            self.button_container.setFixedHeight(button_h)
            self.charts_container.setFixedHeight(charts_h)

            # チャートUIを横並びにするために横方向に等分する
            num = len(self.charts)
            if num == 0:
                return
                
            spacing = self.horizontal_layout.spacing() * (num - 1)
            total_w_margin = self.charts_container.layout().contentsMargins().left() + self.charts_container.layout().contentsMargins().right()
            main_w_margin = main_layout.contentsMargins().left() + main_layout.contentsMargins().right()
            avail_w = overlay_width - total_w_margin - spacing - main_w_margin
            each_w = avail_w // num
            each_w = max(each_w, 120)

            chart_content_margin = self.horizontal_layout.contentsMargins().top() + self.horizontal_layout.contentsMargins().bottom()
            chart_available_h = charts_h - chart_content_margin

            for chart in self.charts:
                chart.adjustSizes(each_w, chart_available_h)
            
            # サイズ調整後の再描画
            self.repaint()
            
            # 子ウィジェットの更新を確実にする
            self.update()
            
        finally:
            self._adjusting_sizes = False