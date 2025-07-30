import os
import PySpin
from camera_control.primary_camera_gui import PrimaryCamera
from camera_control.secondary_camera_gui import SecondaryCamera

class CameraController:
    def __init__(self, system):
        self.system = system
        self.cam1 = None
        self.cam2 = None

    def initialize_cam1(self, serial_number: str):
        self.cam1 = PrimaryCamera(self.system, serial_number=serial_number)

    def initialize_cam2(self, serial_number: str):
        self.cam2 = SecondaryCamera(self.system, serial_number=serial_number)

    def configure_cam1(self,
                       folder: str,
                       fps: float,
                       exposure_time: float,
                       gain_auto_mode: str,
                       exposure_auto_mode: str,
                       width: int,
                       height: int,
                       offset_x: int,
                       offset_y: int,
                       center_roi: bool,
                       pixel_format: str,
                       extension: str,
                       reverse_x: bool = False,
                       reverse_y: bool = False):
        os.makedirs(folder, exist_ok=True)

        self.cam1.prime(
            folder=folder,
            fps=fps,
            exposure_time=exposure_time,
            gain_auto_mode=gain_auto_mode,
            exposure_auto_mode=exposure_auto_mode,
            width=width,
            height=height,
            offset_x=offset_x,
            offset_y=offset_y,
            center_roi=center_roi,
            pixel_format_name=pixel_format,
            image_format=extension,
            reverse_x=reverse_x,
            reverse_y=reverse_y
        )

    def configure_cam2(self,
                       folder: str,
                       fps: float,
                       exposure_time: float,
                       gain_auto_mode: str,
                       exposure_auto_mode: str,
                       width: int,
                       height: int,
                       offset_x: int,
                       offset_y: int,
                       center_roi: bool,
                       pixel_format: str,
                       extension: str,
                       trigger_mode: str = 'On',
                       reverse_x: bool = False,
                       reverse_y: bool = False):
        os.makedirs(folder, exist_ok=True)

        self.cam2.prime(
            folder=folder,
            primary_camera_framerate=fps,
            fps=fps,
            exposure_time=exposure_time,
            gain_auto_mode=gain_auto_mode,
            exposure_auto_mode=exposure_auto_mode,
            width=width,
            height=height,
            offset_x=offset_x,
            offset_y=offset_y,
            center_roi=center_roi,
            pixel_format_name=pixel_format,
            image_format=extension,
            trigger_mode=trigger_mode,
            reverse_x=reverse_x,
            reverse_y=reverse_y
        )

    def capture_single_frame(self, custom_filename1=None, custom_filename2=None):
        if self.cam1 is None or self.cam2 is None:
            raise RuntimeError("カメラが初期化されていません")
        
        self.cam1.trigger()
        self.cam2.trigger()
        
        frame1 = self.cam1.capture_frame(custom_filename=custom_filename1)
        frame2 = self.cam2.capture_frame(custom_filename=custom_filename2)
        
        return frame1, frame2

    def record_cam1(self, duration_sec: float):
        if self.cam1 is None:
            raise RuntimeError("Camera 1 is not initialized")
        self.cam1.record(duration_sec=duration_sec)

    def record_cam2(self, duration_sec: float):
        if self.cam2 is None:
            raise RuntimeError("Camera 2 is not initialized")
        self.cam2.record(duration_sec=duration_sec)

    def release_cam1(self):
        if self.cam1:
            self.cam1.release()
            self.cam1 = None

    def release_cam2(self):
        if self.cam2:
            self.cam2.release()
            self.cam2 = None

    def get_max_fps(self, cam_id):
        cam_wrapper = self.cam1 if cam_id == 1 else self.cam2
        if cam_wrapper is None:
            raise RuntimeError(f"Camera {cam_id} not initialized.")

        cam = cam_wrapper.camera 

        nodemap = cam.GetNodeMap()
        node = PySpin.CFloatPtr(nodemap.GetNode("AcquisitionFrameRate"))
        if PySpin.IsAvailable(node) and PySpin.IsReadable(node):
            return node.GetMax()
        else:
            raise RuntimeError(f"Camera {cam_id}: Cannot read max FPS.")
