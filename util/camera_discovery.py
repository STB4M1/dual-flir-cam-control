
# util/camera_discovery.py

import PySpin

def list_available_cameras(system, log_func=None):
    """接続されているFLIRカメラのシリアル番号をログ出力する"""
    try:
        cam_list = system.GetCameras()
        num_cams = cam_list.GetSize()
        if num_cams == 0:
            if log_func:
                log_func("カメラが見つかりません")
            return []
        if log_func:
            log_func(f"接続されているカメラ数: {num_cams}")
        serials = []
        for i in range(num_cams):
            cam = cam_list.GetByIndex(i)
            cam.Init()
            sn = cam.DeviceSerialNumber.ToString()
            serials.append(sn)
            if log_func:
                log_func(f" - Serial: {sn}")
            cam.DeInit()
        cam_list.Clear()
        return serials
    except Exception as e:
        if log_func:
            log_func(f"カメラ検出エラー: {e}")
        return []
