import os

from PyQt5.QtWidgets import (QDockWidget, QWidget, QVBoxLayout)
from PyQt5.QtCore import Qt, pyqtSignal
""""""
from gui_widget.pokemon import PokemonData

"""手持ちポケモン表示用DockWidgwt"""
class PartyPokemonsDock(QDockWidget):
    show_overlay_widget_signal = pyqtSignal(str)

    def __init__(self, align=Qt.LeftDockWidgetArea, parent=None):
        """
        初期化関数
        """

        super().__init__(parent)
        self.setAllowedAreas(align) # ドックの位置
        self.setFeatures(QDockWidget.NoDockWidgetFeatures)  # ドックの移動を禁止
        
        # タイトルバーを非表示にする
        self.setTitleBarWidget(QWidget())
        
        # 背景アイコン用ウィジェット
        background_icons_widget = QWidget()
        background_icons_layout = QVBoxLayout(background_icons_widget)
        background_icons_layout.setContentsMargins(0, 0, 0, 0)  # マージンをゼロにする
        background_icons_layout.setSpacing(0)

        # ウィジェットの背景色
        background_icons_widget.setStyleSheet("""
            QWidget {
                background-color: #070707;
            }
        """)

        # ポケモンアイコン用ウィジェット
        pokemon_icons_widget = QWidget()
        pokemon_icnos_layout = QVBoxLayout(pokemon_icons_widget)
        pokemon_icnos_layout.setContentsMargins(0, 0, 0, 0)  # マージンをゼロにする
        pokemon_icnos_layout.setSpacing(0)

        """ポケモン6匹分のラベルを初期化"""
        self.pokemons = []
        for i in range(6):
            pokemon = PokemonData(parent=self, widget_height=background_icons_widget.height())
            pokemon.show_ovelay_widget_signal.connect(self.show_overlay_widget)                             # ポケモン画像がクリックされた場合にオーバーレイウィジェットを表示する用に信号を親に出す
            self.pokemons.append(pokemon)
            background_icons_layout.addWidget(self.pokemons[i].background_icon, alignment=Qt.AlignHCenter)  # 背景アイコンをQVBoxLayoutで縦に揃える
            #pokemon_icnos_layout.addWidget(self.pokemons[i].pokemon_icon, alignment=Qt.AlignHCenter)        # ポケモンアイコンをQVBoxLayoutで縦に揃える

        
        self.setWidget(background_icons_widget)
        
    def set_pokemon_icon(self, images):
        """
        切り抜かれた画像データを基にアイコンのポケモンを推測。DockWidgetにそのポケモンの画像をセットする。

        Arges:
        - images[] (cupy): アイコン部分の切り抜き画像
        """
        icon_labels = PokemonData.recognize_pokemon_icon(images)
        for label, pokemon in zip(icon_labels, self.pokemons):
            pokemon.set_pokemon(label)


    def resize_party_icon(self, height):
        """
        ウィンドウサイズ変更時の画像リサイズ

        Args:
        - height (int): サイズ変更後のwidgetの高さ
        """
        for pokemon in self.pokemons:
            pokemon.resize_bg_icon(height)

    def get_nth_file(self, folder_path, n):
        """
        推測されたラベルに相当する画像のパスを返す

        Args: 
        - folder_path (str): フォルダパス
        - n (int): 推測されたポケモンのラベル

        Return:
        - os.path.join(folder_path, files[n]): ポケモンの画像パス
        """
        # フォルダー内のファイル一覧を取得（ディレクトリは除外）
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

        # ファイルをアルファベット順でソート
        files.sort()

        # 指定されたn番目のファイルを取得（1-indexed）
        if 1 <= n <= len(files):
            return os.path.join(folder_path, files[n])
        else:
            return None

    def show_overlay_widget(self, pokemon_name):
        """
        親にオーバーレイウィジェットを表示するように信号を飛ばす

        Args:
        - pokemon_name (str): オーバーレイウィジェットに表示するポケモンの名前
        """
        self.show_overlay_widget_signal.emit(pokemon_name)