import numpy as np
""""""
from config.data_config import DataConfigClass

class IconCapture:

    # バトルチーム切り替えフラグ
    is_team_switch = True

    # バトルチーム切り替えフラグチェック用領域
    VERIFICATION_REGION = (807, 190, 52, 52)
    UNIFORM_COLOR = [251, 204, 0]
    
    # バトルチーム切り抜き領域
    MY_PARTY_REGIONS = [
        (775, 258),   # First region
        (775, 355),   # Second region
        (775, 452),   # Third region
        (775, 549),   # Fourth region
        (775, 646),   # Fifth region
        (775, 743)    # Sixth region
    ]
    MY_PARTY_REGION_SIZE = 85

    # 相手パーティ切り抜き領域
    OPPONENT_PARTY_REGIONS = [
        (1231, 248),   # First region
        (1231, 345),   # Second region
        (1231, 442),   # Third region
        (1231, 539),   # Fourth region
        (1231, 636),   # Fifth region
        (1231, 733)    # Sixth region
    ]
    OPPONENT_PARTY_REGION_SIZE = 85

    # 目標とする色 (R, G, B) を numpy 配列にする
    target_color = np.array([251, 204, 0], dtype=np.uint8)      # Switch用
    target_color_2 = np.array([250, 203, 0], dtype=np.uint8)    # Switch2用
        
    """"""
    @classmethod
    def capture_my_party(cls, frame):
        """
        バトルチーム選択画面で、チームから切り抜かれたポケモンアイコン画像の配列を返す

        Arges:
        - frame: 入力画像

        Return:
        - images[] (numpy)
        """
        return cls.capture_icon(frame, cls.MY_PARTY_REGIONS, cls.MY_PARTY_REGION_SIZE)
    
    @classmethod
    def capture_opponent_party(cls, frame):
        """
        選出画面で、相手パーティから切り抜かれたポケモンアイコン画像の配列を返す

        Arges:
        - frame: 入力画像

        Return:
        - images[] (numpy)
        """
        return cls.capture_icon(frame, cls.OPPONENT_PARTY_REGIONS, cls.OPPONENT_PARTY_REGION_SIZE)
    

    @classmethod
    def verify_selected_team(cls, frame):
        """
        バトルチーム選択画面でカーソルがチームに選択されているかを調べる。(チーム切り替えを行っているかどうか)
        
        Args:
        - frame (numpy): キャプチャー映像
        
        Returns:
        - True or False: 特定の領域が指定した単色になっているか
        """
        start_x, start_y, width, height = IconCapture.VERIFICATION_REGION
        # Extract the specified region
        region = frame[start_y:start_y+height, start_x:start_x+width]

        # 全ピクセルが target_color と一致するか判定
        if DataConfigClass.hardware_index == 0:
            # Switchでの色判定
            is_uniform = np.all(region == cls.target_color)
        elif DataConfigClass.hardware_index == 1:
            # Switch2での色判定
            is_uniform = np.all(region == cls.target_color_2)
            
        return  is_uniform
    
    
    def capture_icon(frame, output_regions, trim_size):
        """
        指定領域を切り抜いてその画像配列を返す

        Args:
        - frame (cupy or numpy): input image
        - output_regions (list): List of (start_x, start_y) points
        - trim_size (int): 領域のサイズ

        Retuen:
        - output_images (cupy): 切り抜かれた画像
        """

        output_images = []
        # If verification passes, extract and save additional regions
        for i, (start_x, start_y) in enumerate(output_regions, 1):
            # Extract region                
            output_region = frame[start_y:start_y+trim_size, start_x:start_x+trim_size]
            output_images.append(output_region)
            
        return output_images
    
    
    