import queue
import sounddevice as sd

from PyQt5.QtCore import QObject, pyqtSignal

class AudioManager(QObject):
    error_signal = pyqtSignal(Exception)

    def __init__(self, sample_rate=48000, channels=2, buffer_size=1024):
        """      
        Args:
            sample_rate (int): サンプリングレート
            channels (int): チャンネル数
            buffer_size (int): バッファサイズ
        """
        super().__init__()
        # デバイス設定の最適化
        sd.default.device = None  # システムのデフォルトデバイス
        sd.default.channels = channels
        sd.default.samplerate = sample_rate
        
        # ストリーム設定
        self.sample_rate = sample_rate
        self.channels = channels
        self.buffer_size = buffer_size
        self.volume = 1.0
        
        # 音声データキュー
        self.audio_queue = queue.Queue(maxsize=5) 
        
        # パフォーマンスチューニングフラグ
        self.is_running = False
        
        # デバッグ用デバイス情報のプリント
        # self._print_device_details()

    def _print_device_details(self):
        """
        デバッグ用
        利用可能なオーディオデバイスの詳細を表示
        低レイテンシデバイスを強調
        """
        print("利用可能なオーディオデバイス:")
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0 or device['max_output_channels'] > 0:
                print(f"デバイス {i}: {device['name']}")
                print(f"  入力チャンネル: {device['max_input_channels']}")
                print(f"  出力チャンネル: {device['max_output_channels']}")
                print(f"  デフォルト低レイテンシサンプルレート: {device.get('default_low_input_latency', 'N/A')}")
                print("---")

    def device_list(self):
        """
        使用可能なデバイス一覧を返す
        WASAPIが使用可能ならばWASAPIデバイス一覧を
        WASAPIが使用不可ならばMMEデバイス一覧を

        Return:
            input_devices: 入力デバイス一覧
            default_input_index: 初期設定入力デバイス(のインデックス値)
            output_devices: 出力デバイス一覧
            default_output_index: 初期設定出力デバイス(のインデックス値)
        """
        # WASAPIホストAPIインデックスを取得
        hostapis = sd.query_hostapis()
        wasapi_index = None
        input_devices, default_input_index = [], None
        output_devices, default_output_index = [], None

        for index, api in enumerate(hostapis):
            if api['name'] == 'Windows WASAPI':
                wasapi_index = index
                break

        if wasapi_index is None: # WASAPIデバイスが存在しなければMMEデバイス取得
            devices = sd.query_devices()
            default_input_index = sd.default.device[0]
            default_output_index = sd.default.device[1]

            mme_index = None
            for index, api in enumerate(hostapis):
                if api['name'] == 'MME':
                    mme_index = index
                    break

            # MMEに属するデバイスをフィルタリングして表示
            for idx, device in enumerate(devices):
                if device['hostapi'] == mme_index:
                    if device['max_input_channels'] > 0:
                        input_devices.append({'index' : idx, 'name' : device['name']})
                    elif device['max_output_channels'] > 0:
                        output_devices.append({'index' : idx, 'name' : device['name']})

        else: # WASAPIデバイス取得
            # 全デバイス情報を取得
            devices = sd.query_devices()
            default_input = devices[sd.default.device[0]]['name']
            default_output = devices[sd.default.device[1]]['name']

            # WASAPIに属するデバイスをフィルタリングして表示
            for idx, device in enumerate(devices):
                if device['hostapi'] == wasapi_index:
                    if device['max_input_channels'] > 0:
                        input_devices.append({'index' : idx, 'name' : device['name']})
                        if default_input[0:4] == device['name'][0:4]:
                            default_input_index = idx
                    elif device['max_output_channels'] > 0:
                        output_devices.append({'index' : idx, 'name' : device['name']})
                        if default_output[0:4] == device['name'][0:4]:
                            default_output_index = idx

        return input_devices, default_input_index, output_devices, default_output_index

            
    def start(self, input_device=None, output_device=None):
        """
        Args:
            input_device (int): 入力デバイスインデックス
            output_device (int): 出力デバイスインデックス
        """
        def audio_callback(indata, outdata, frames, time_info, status):
            """
            ゼロコピーのリアルタイムコールバック
            """
            # デバッグ用ステータス表示
            if status:
                print(f"オーディオステータス: {status}")
            
            # 音量調節
            outdata[:] = indata * self.volume
            
            # キューに追加
            try:
                self.audio_queue.put_nowait(indata.copy())
            except queue.Full:
                pass  # キューがいっぱいの場合は最新データを破棄

        try:
            # ストリーム設定
            self.stream = sd.Stream(
                device=(input_device, output_device),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='float32',
                callback=audio_callback,
                blocksize=self.buffer_size,
                latency='low'  # 最低レイテンシモード
            )
            
            # ストリーム開始
            self.stream.start()
            self.is_running = True
        
        except Exception as e:
            e.args = ("オーディオストリーム初期化エラー: " + e.args[0],)
            self.error_signal.emit(e)

    def reload_audio(self, input_device=None, output_device=None):
        """
        入力音源変更
        """
        self.stop()
        self.start(input_device=input_device, output_device=output_device)

    def set_volume(self, vol):
        """
        MainWindowからのボリューム設定用
        """
        self.volume = 1.0 * vol / 100.0

    def stop(self):
        """
        オーディオストリームを停止
        """
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        self.is_running = False