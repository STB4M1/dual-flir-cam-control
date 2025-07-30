from PySide6.QtCore import QObject, QThread, Signal
import traceback


class CameraWorker(QObject):
    finished = Signal()
    error_occurred = Signal(str)

    def __init__(self, camera_controller, duration_sec: float, cam_id: int = 1):
        super().__init__()
        self.controller = camera_controller
        self.duration_sec = duration_sec
        self.cam_id = cam_id
        self._is_running = True

    def run(self):
        try:
            if not self._is_running:
                return

            if self.cam_id == 1:
                self.controller.record_cam1(self.duration_sec)
            elif self.cam_id == 2:
                self.controller.record_cam2(self.duration_sec)
            else:
                raise ValueError("Invalid cam_id provided to CameraWorker")

        except Exception as e:
            tb = traceback.format_exc()
            self.error_occurred.emit(f"[CameraWorker] Error: {str(e)}\n{tb}")
        finally:
            self.finished.emit()

    def stop(self):
        self._is_running = False
