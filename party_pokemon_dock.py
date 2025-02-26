import os

from PyQt5.QtWidgets import (QDockWidget, QWidget, QVBoxLayout)
from PyQt5.QtCore import Qt

from pokemon import PokemonData

"""手持ちポケモン表示用DockWidgwt"""
class PartyPokemonsDock(QDockWidget):
    def __init__(self, align=Qt.LeftDockWidgetArea, parent=None):
        """
        初期化関数
        """

        super().__init__(parent)
        self.setAllowedAreas(align) # ドックの位置
        self.setFeatures(QDockWidget.NoDockWidgetFeatures)  # ドックの移動を禁止
        
        # タイトルバーを非表示にする
        self.setTitleBarWidget(QWidget())
        
        # メインウィジェット
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)  # マージンをゼロにする
        layout.setSpacing(0)

        # ウィジェットの背景色
        widget.setStyleSheet("""
            QWidget {
                background-color: #070707;
            }
        """)

        """ポケモン6匹分のラベルを初期化"""
        self.pokemons = []
        for i in range(6):
            pokemon = PokemonData(self, widget.height())
            self.pokemons.append(pokemon)
            layout.addWidget(self.pokemons[i].background_icon, alignment=Qt.AlignHCenter)    
        
        self.setWidget(widget)
        
    def set_pokemon_icon(self, images):
        """
        切り抜かれた画像データを基にアイコンのポケモンを推測。DockWidgetにそのポケモンの画像をセットする。

        Arges:
        - images[] (cupy): アイコン部分の切り抜き画像
        """
        icon_labels = PokemonData.recognize_pokemon_icon(images)
        for label, pokemon in zip(icon_labels, self.pokemons):
            image_path = self.get_nth_file("./img/Pokemon Icons/", label)
            pokemon.set_pokemon(image_path)


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