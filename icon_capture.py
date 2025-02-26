import numpy as np
import cupy as cp

class IconCapture:

    # バトルチーム切り替えフラグ
    is_team_switch = True

    # バトルチーム切り替えフラグチェック用領域
    VERIFICATION_REGION = (807, 190, 52, 52)
    UNIFORM_COLOR = [251, 204, 0]
    
    # バトルチーム切り抜き領域
    MY_PARTY_REGIONS = [
        (771, 257),   # First region
        (771, 354),   # Second region
        (771, 451),   # Third region
        (771, 548),   # Fourth region
        (771, 645),   # Fifth region
        (771, 741)    # Sixth region
    ]
    MY_PARTY_REGION_SIZE = 90

    # 相手パーティ切り抜き領域
    OPPONENT_PARTY_REGIONS = [
        (1233, 245),   # First region
        (1233, 342),   # Second region
        (1233, 439),   # Third region
        (1233, 536),   # Fourth region
        (1233, 633),   # Fifth region
        (1233, 730)    # Sixth region
    ]
    OPPONENT_PARTY_REGION_SIZE = 92
        
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
        
        # 目標とする色 (R, G, B) を numpy 配列にする
        target_color = cp.array([251, 204, 0], dtype=np.uint8)

        # region のデータ型を統一
        if region.dtype != cp.uint8:
            region = region.astype(cp.uint8)

        # 全ピクセルが target_color と一致するか判定
        is_uniform = cp.all(region == target_color)
        
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
            if isinstance(frame, cp.ndarray):
                output_region = frame[start_y:start_y+trim_size, start_x:start_x+trim_size, :]
            else:
                output_region = frame[start_y:start_y+trim_size, start_x:start_x+trim_size]
            output_images.append(output_region)
            
        return output_images
    
    
    