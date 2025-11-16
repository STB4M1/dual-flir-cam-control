from PySide6.QtCore import QThread, Signal
import time

class CameraLiveWorker(QThread):
    """
    FLIRカメラのLiveView用画像取得ワーカー
    別スレッドで実行され、一定間隔で画像を取得してSignalでGUIに渡す
    """
    new_frame = Signal(object)  # NumPy配列（画像データ）を送信

    def __init__(self, camera, fps=20, parent=None):
        super().__init__(parent)
        self.camera = camera
        self.interval = 1.0 / fps
        self._running = False

    def run(self):
        """
        スレッド実行：カメラから画像を取得し続ける
        """
        self._running = True

        try:
            # self.camera.trigger()  # BeginAcquisition 相当
            time.sleep(0.1)
        except Exception as e:
            print(f"[CameraLiveWorker] Trigger error: {e}")
            return

        while self._running:
            start = time.time()

            try:
                frame = self.camera.capture_frame_for_live()
                if frame is not None:
                    self.new_frame.emit(frame)
                else:
                    print("[LiveWorker] Got None frame from camera.")
            except Exception as e:
                print(f"[CameraLiveWorker] Frame capture error: {e}")

            elapsed = time.time() - start
            sleep_time = max(0, self.interval - elapsed)
            time.sleep(sleep_time)

        try:
            self.camera.stop()  # EndAcquisition 相当
        except Exception as e:
            print(f"[CameraLiveWorker] Stop error: {e}")

    def stop(self):
        """
        スレッド終了要求（安全に止めるためのフラグと待機）
        """
        self._running = False
        self.wait()  # スレッドの終了を待つ（重要！）
