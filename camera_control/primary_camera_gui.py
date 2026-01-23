import os
import PySpin
import numpy as np
import time


class PrimaryCamera:
    def __init__(self, system, serial_number: int = None, name="Camera"):
        self.system = system
        self.cam_list = system.GetCameras()
        self.camera = self.cam_list.GetBySerial(str(serial_number))
        self.camera.Init()
        self.name = name
        self.folder = None
        self.frame_counter = 0
        self._primed = False
        self.trigger_event = False
        self.image_format = None
        self.framerate = None
        self.reverse_x = False
        self.reverse_y = False
        self.white_balance_auto = "Off"
        self.wb_red = 1.0
        self.wb_blue = 1.0

    def prime(
        self,
        folder: str,
        fps: float = None,
        exposure_time: float = None,
        image_format: str = 'jpg',
        gain_auto_mode: str = 'Off',
        gain_value: float = None, 
        exposure_auto_mode: str = 'Off',
        width: int = None,
        height: int = None,
        center_roi: bool = True,
        offset_x: int = None,
        offset_y: int = None,
        pixel_format_name: str = 'Mono8',
        trigger_mode: str = 'On',
        reverse_x: bool = False,
        reverse_y: bool = False,
        white_balance_auto: str = "Off",             
        wb_red: float = 1.0,
        wb_blue: float = 1.0 
    ):

        if self.camera.IsStreaming():
            self.camera.EndAcquisition()

        if self.camera.IsInitialized():
            self.camera.DeInit()
        self.camera.Init()

        if self._primed:
            self.stop()

        self.folder = folder
        self.frame_counter = 0
        self.image_format = image_format
        self.reverse_x = reverse_x
        self.reverse_y = reverse_y
        self.white_balance_auto = white_balance_auto
        self.wb_red = wb_red
        self.wb_blue = wb_blue

        nodemap = self.camera.GetNodeMap()

        # GainAuto
        gain_auto_node = PySpin.CEnumerationPtr(nodemap.GetNode('GainAuto'))
        gain_node = PySpin.CFloatPtr(nodemap.GetNode('Gain'))

        if PySpin.IsAvailable(gain_auto_node) and PySpin.IsWritable(gain_auto_node):
            entry = gain_auto_node.GetEntryByName(gain_auto_mode)
            gain_auto_node.SetIntValue(entry.GetValue())

            # Gain Value
            if gain_value is not None and gain_auto_mode in ["Off", "Once"]:
                if PySpin.IsAvailable(gain_node) and PySpin.IsWritable(gain_node):
                    gain_node.SetValue(gain_value)
                    print(f"[{self.name}] Gain set to {gain_value}")

        # ExposureAuto
        exposure_auto_node = PySpin.CEnumerationPtr(nodemap.GetNode('ExposureAuto'))
        if PySpin.IsAvailable(exposure_auto_node) and PySpin.IsWritable(exposure_auto_node):
            entry = exposure_auto_node.GetEntryByName(exposure_auto_mode)
            exposure_auto_node.SetIntValue(entry.GetValue())

        # ExposureTime
        if exposure_time is not None and exposure_auto_mode in ["Off", "Once"]:
            exp_node = PySpin.CFloatPtr(nodemap.GetNode("ExposureTime"))
            if PySpin.IsAvailable(exp_node) and PySpin.IsWritable(exp_node):
                exp_node.SetValue(exposure_time)

        # FPS
        if fps is not None:
            fps_enable_node = PySpin.CBooleanPtr(nodemap.GetNode("AcquisitionFrameRateEnable"))
            fps_node = PySpin.CFloatPtr(nodemap.GetNode("AcquisitionFrameRate"))
            if PySpin.IsAvailable(fps_enable_node) and PySpin.IsWritable(fps_enable_node):
                fps_enable_node.SetValue(True)
            if PySpin.IsAvailable(fps_node) and PySpin.IsWritable(fps_node):
                fps_node.SetValue(fps)

        # --- Sync mode: Primary Digital IO settings ---
        if trigger_mode != 'Off':
            self._apply_primary_sync_io(nodemap)

        # ROI
        w_node = PySpin.CIntegerPtr(nodemap.GetNode("Width"))
        h_node = PySpin.CIntegerPtr(nodemap.GetNode("Height"))
        x_node = PySpin.CIntegerPtr(nodemap.GetNode("OffsetX"))
        y_node = PySpin.CIntegerPtr(nodemap.GetNode("OffsetY"))

        original_offset_x = x_node.GetValue()  # 元の OffsetX を保存
        original_offset_y = y_node.GetValue()  # 元の OffsetY を保存

        if PySpin.IsWritable(x_node): x_node.SetValue(0)  # 最大サイズ取得のため OffsetX = 0
        if PySpin.IsWritable(y_node): y_node.SetValue(0)  # 最大サイズ取得のため OffsetY = 0

        max_w = w_node.GetMax()  # 真の最大幅を取得
        max_h = h_node.GetMax()  # 真の最大高さを取得

        if PySpin.IsWritable(x_node): x_node.SetValue(original_offset_x)  # 元の OffsetX に戻す
        if PySpin.IsWritable(y_node): y_node.SetValue(original_offset_y)  # 元の OffsetY に戻す

        roi_w = width if width not in (None, 0) else max_w  # 実際に設定する幅
        roi_h = height if height not in (None, 0) else max_h  # 実際に設定する高さ

        print(f"[DEBUG] {self.__class__.__name__} 最大サイズ: Width={max_w}, Height={max_h}")
        print(f"[DEBUG] {self.__class__.__name__} 設定サイズ: Width={roi_w}, Height={roi_h}")

        if center_roi:
            offset_x = (max_w - roi_w) // 2  # 最大幅ベースで中央配置
            offset_y = (max_h - roi_h) // 2  # 最大高さベースで中央配置
        else:
            offset_x = 0
            offset_y = 0

        inc_x = x_node.GetInc()
        inc_y = y_node.GetInc()
        offset_x = offset_x - (offset_x % inc_x)
        offset_y = offset_y - (offset_y % inc_y)

        inc_w = w_node.GetInc()
        inc_h = h_node.GetInc()
        roi_w = roi_w - (roi_w % inc_w)
        roi_h = roi_h - (roi_h % inc_h)

        if PySpin.IsWritable(w_node): w_node.SetValue(roi_w)
        if PySpin.IsWritable(h_node): h_node.SetValue(roi_h)

        # 必ず幅・高さをセットしてから Offset を設定！
        max_offset_x = x_node.GetMax()
        max_offset_y = y_node.GetMax()
        offset_x = min(offset_x, max_offset_x)
        offset_y = min(offset_y, max_offset_y)

        if PySpin.IsWritable(x_node): x_node.SetValue(offset_x)
        if PySpin.IsWritable(y_node): y_node.SetValue(offset_y)

        # PixelFormat
        fmt_node = PySpin.CEnumerationPtr(nodemap.GetNode("PixelFormat"))
        if PySpin.IsAvailable(fmt_node) and PySpin.IsWritable(fmt_node):
            entry = fmt_node.GetEntryByName(pixel_format_name)
            if PySpin.IsAvailable(entry) and PySpin.IsReadable(entry):
                fmt_node.SetIntValue(entry.GetValue())

        # --- White Balance Settings ---
        try:
            wb_auto_node = PySpin.CEnumerationPtr(nodemap.GetNode("BalanceWhiteAuto"))
            if PySpin.IsAvailable(wb_auto_node) and PySpin.IsWritable(wb_auto_node):
                wb_entry = wb_auto_node.GetEntryByName(white_balance_auto)
                wb_auto_node.SetIntValue(wb_entry.GetValue())

            if white_balance_auto == "Off":
                selector_node = PySpin.CEnumerationPtr(nodemap.GetNode("BalanceRatioSelector"))
                ratio_node = PySpin.CFloatPtr(nodemap.GetNode("BalanceRatio"))
                if PySpin.IsAvailable(selector_node) and PySpin.IsWritable(selector_node):
                    # Red設定
                    red_entry = selector_node.GetEntryByName("Red")
                    selector_node.SetIntValue(red_entry.GetValue())
                    ratio_node.SetValue(wb_red)

                    # Blue設定
                    blue_entry = selector_node.GetEntryByName("Blue")
                    selector_node.SetIntValue(blue_entry.GetValue())
                    ratio_node.SetValue(wb_blue)

            print(f"[{self.__class__.__name__}] WB auto={white_balance_auto}, Red={wb_red}, Blue={wb_blue}")
        except Exception as e:
            print(f"[{self.__class__.__name__}] White Balance 設定エラー: {e}")
        
        # Stream mode
        self.camera.TLStream.StreamBufferHandlingMode.SetValue(PySpin.StreamBufferHandlingMode_OldestFirst)
        self.framerate = int(np.ceil(self.camera.AcquisitionFrameRate.GetValue()))
        self._primed = True

        self.roi_info = {
            'x_min': offset_x,
            'y_min': offset_y,
            'x_max': offset_x + roi_w,
            'y_max': offset_y + roi_h
        }
        print(f"[DEBUG] {self.__class__.__name__} ROI: "
            f"x_min={offset_x}, y_min={offset_y}, x_max={offset_x + roi_w}, y_max={offset_y + roi_h}")

    def trigger(self):
        if not self._primed:
            raise RuntimeError("Camera is not primed")

        if not self.camera.IsStreaming():
            try:
                self.camera.BeginAcquisition()
                time.sleep(0.1)  # 🔧 少し待って安定化（重要！）
                self.trigger_event = True
            except Exception as e:
                print(f"[Trigger] BeginAcquisition failed: {e}")
                self.trigger_event = False
        else:
            self.trigger_event = True

    def capture_frame(self, return_numpy=False, custom_filename: str = None):
        print(f"[PrimaryCamera] Capturing frame {self.frame_counter}")
        if not self.trigger_event:
            raise RuntimeError("Camera is not acquiring")
        try:
            image_result = self.camera.GetNextImage()
            if image_result.IsIncomplete():
                print("[PrimaryCamera] Incomplete image")
                return None

            timestamp = image_result.GetTimeStamp()
            print(f"[{self.name}] Timestamp = {timestamp}")
            
            img_np = image_result.GetNDArray()

            if return_numpy:
                image_result.Release()
                return img_np
            else:
                if custom_filename:
                    filename = os.path.join(self.folder, custom_filename)
                else:
                    filename = os.path.join(self.folder, f"frame_{self.frame_counter}.{self.image_format}")
                import cv2
                cv2.imwrite(filename, img_np)
                self.frame_counter += 1
                image_result.Release()
                return filename
        except PySpin.SpinnakerException as e:
            print(f"[PrimaryCamera] Capture error: {e}")
            return None

    def record(self, duration_sec: float):
        if not self._primed:
            raise RuntimeError("Camera must be primed before recording")

        total_frames = int(duration_sec * self.framerate)
        interval = 1.0 / self.framerate

        print(f"[PrimaryCamera] Start recording: {total_frames} frames at {self.framerate:.2f} FPS")

        self.camera.BeginAcquisition()
        self.trigger_event = True

        start_time = time.perf_counter()  # 高精度タイマー使用
        try:
            for i in range(total_frames):
                self.capture_frame()

                # 次に撮影すべき理論上の時間
                next_time = start_time + (i + 1) * interval
                sleep_time = next_time - time.perf_counter()
                if sleep_time > 0:
                    # 少し余裕を持ってsleep（過剰にCPUをブロックしない）
                    time.sleep(sleep_time)
        except Exception as e:
            print(f"[PrimaryCamera] Recording error: {e}")
        finally:
            self.stop()
            print(f"[PrimaryCamera] Recording finished. {self.frame_counter} frames saved.")

    def _apply_primary_sync_io(self, nodemap):
        """
        PDF準拠：
        - Line1 を Output にする
        - Line1 の LineSource を ExposureActive 等にする（推奨）
        - Line2 を選んで 3.3V enable を有効化する
        """

        line_sel = PySpin.CEnumerationPtr(nodemap.GetNode("LineSelector"))
        line_mode = PySpin.CEnumerationPtr(nodemap.GetNode("LineMode"))
        line_source = PySpin.CEnumerationPtr(nodemap.GetNode("LineSource"))

        def _set_enum(node, name):
            entry = node.GetEntryByName(name)
            if PySpin.IsAvailable(entry) and PySpin.IsReadable(entry):
                node.SetIntValue(entry.GetValue())
                return True
            return False

        # --- Line1: Output + LineSource ---
        try:
            if PySpin.IsAvailable(line_sel) and PySpin.IsWritable(line_sel):
                _set_enum(line_sel, "Line1")

                if PySpin.IsAvailable(line_mode) and PySpin.IsWritable(line_mode):
                    if _set_enum(line_mode, "Output"):
                        print(f"[{self.name}] Sync IO: Line1=Output")

                # ★ここが肝：Line1が何を出すか
                # 候補は機種依存なので、通ったやつを採用
                if PySpin.IsAvailable(line_source) and PySpin.IsWritable(line_source):
                    for src in ["ExposureActive", "FrameTriggerWait", "FrameActive"]:
                        if _set_enum(line_source, src):
                            print(f"[{self.name}] Sync IO: Line1 LineSource={src}")
                            break

        except Exception as e:
            print(f"[{self.name}] Sync IO(Line1) failed: {e}")

        # --- Line2: 3.3V enable（Line2を選んでから）---
        try:
            if PySpin.IsAvailable(line_sel) and PySpin.IsWritable(line_sel):
                _set_enum(line_sel, "Line2")

            # 機種によってノード名が違うので候補を試す
            candidates = ["V3_3Enable", "V3_3Enable0", "V3_3Enable1", "Line2V3_3Enable"]
            enabled = False
            for node_name in candidates:
                try:
                    node = PySpin.CBooleanPtr(nodemap.GetNode(node_name))
                    if PySpin.IsAvailable(node) and PySpin.IsWritable(node):
                        node.SetValue(True)
                        print(f"[{self.name}] Sync IO: {node_name}=True (3.3V enable)")
                        enabled = True
                        break
                except Exception:
                    pass

            if not enabled:
                print(f"[{self.name}] Sync IO: 3.3V enable ノードが見つからない/書き込めない可能性あり")

        except Exception as e:
            print(f"[{self.name}] Sync IO(Line2 3.3V) failed: {e}")

    def stop(self):
        if self.camera.IsStreaming():
            self.camera.EndAcquisition()
        self.trigger_event = False
        self._primed = False

    def capture_frame_for_live(self):
        """
        LiveView：カメラがサポートしている PixelFormat を自動判別し、
        未対応フォーマットの場合はデバッグ情報を1回だけ表示する。
        """

        # ------ 未対応フォーマットのログを一度だけ出すためのフラグ ------
        if not hasattr(self, "_unsupported_logged"):
            self._unsupported_logged = set()

        try:
            image_result = self.camera.GetNextImage(100)

            if image_result.IsIncomplete():
                print("[LiveCapture] Incomplete image")
                image_result.Release()
                return None

            pixel_format = image_result.GetPixelFormat()
            h = image_result.GetHeight()
            w = image_result.GetWidth()

            # ---------- デバッグ用：PixelFormat 名を取得 ----------
            try:
                pf_name = self.camera.PixelFormat.GetCurrentEntry().GetSymbolic()
            except:
                pf_name = str(pixel_format)

            # ======================================================
            # ① RGB8 へ変換してみる（Bayer・YUV・YCbCr 対応）
            # ======================================================
            try:
                converted = image_result.Convert(PySpin.PixelFormat_RGB8, PySpin.HQ_LINEAR)
                data = converted.GetData()
                arr = np.frombuffer(data, dtype=np.uint8).reshape(h, w, 3)
                image_result.Release()
                return np.ascontiguousarray(arr)
            except Exception:
                pass

            # ======================================================
            # ② BGR8 変換できるか試す（YCbCr系）
            # ======================================================
            try:
                converted = image_result.Convert(PySpin.PixelFormat_BGR8, PySpin.HQ_LINEAR)
                data = converted.GetData()
                arr = np.frombuffer(data, dtype=np.uint8).reshape(h, w, 3)
                image_result.Release()
                return np.ascontiguousarray(arr)
            except Exception:
                pass

            # ======================================================
            # ③ 変換できない → NDArray （Mono8 や RAW）
            # ======================================================
            arr = image_result.GetNDArray()
            image_result.Release()

            # ★ 未対応フォーマットのときだけデバッグを出す
            if pf_name not in self._unsupported_logged:
                print("\n==============================")
                print("🚨 未対応 PixelFormat を検出！")
                print(f"PixelFormat = {pf_name}")
                print(f"Value = {pixel_format}")
                print("このまま NDArray（生データ）で表示します。")
                print("==============================\n")

                self._unsupported_logged.add(pf_name)

            return np.ascontiguousarray(arr)

        except Exception as e:
            print(f"[LiveCapture] Error: {e}")
            return None

    def prime_for_live(
        self,
        width: int = None,
        height: int = None,
        center_roi: bool = True,
        offset_x: int = None,
        offset_y: int = None,
        pixel_format_name: str = 'Mono8',
        reverse_x: bool = False,
        reverse_y: bool = False,
        gain_auto_mode: str = 'Off',
        gain_value: float = None, 
        exposure_auto_mode: str = 'Off',
        exposure_time: float = None,
        fps: float = None,
        white_balance_auto: str = 'Off',
        wb_red: float = 1.0,
        wb_blue: float = 1.0
    ):
        """LiveView用の初期化処理（シンプル版）"""
        if self.camera.IsStreaming():
            self.camera.EndAcquisition()
        if self.camera.IsInitialized():
            self.camera.DeInit()
        self.camera.Init()

        self.reverse_x = reverse_x
        self.reverse_y = reverse_y
        nodemap = self.camera.GetNodeMap()

        # --- GainAuto / Gain ---
        gain_auto_node = PySpin.CEnumerationPtr(nodemap.GetNode('GainAuto'))
        gain_node = PySpin.CFloatPtr(nodemap.GetNode('Gain'))

        if PySpin.IsAvailable(gain_auto_node) and PySpin.IsWritable(gain_auto_node):
            entry = gain_auto_node.GetEntryByName(gain_auto_mode)
            gain_auto_node.SetIntValue(entry.GetValue())

            # Off / Once のときだけ Gain を反映
            if gain_value is not None and gain_auto_mode in ["Off", "Once"]:
                if PySpin.IsAvailable(gain_node) and PySpin.IsWritable(gain_node):
                    gain_node.SetValue(gain_value)
                    
        # --- ExposureAuto ---
        exposure_auto_node = PySpin.CEnumerationPtr(nodemap.GetNode('ExposureAuto'))
        if PySpin.IsAvailable(exposure_auto_node) and PySpin.IsWritable(exposure_auto_node):
            entry = exposure_auto_node.GetEntryByName(exposure_auto_mode)
            exposure_auto_node.SetIntValue(entry.GetValue())

        # --- ExposureTime ---
        if exposure_time is not None and exposure_auto_mode in ["Off", "Once"]:
            exp_node = PySpin.CFloatPtr(nodemap.GetNode("ExposureTime"))
            if PySpin.IsAvailable(exp_node) and PySpin.IsWritable(exp_node):
                exp_node.SetValue(exposure_time)

        # --- FPS ---
        if fps is not None:
            fps_enable_node = PySpin.CBooleanPtr(nodemap.GetNode("AcquisitionFrameRateEnable"))
            fps_node = PySpin.CFloatPtr(nodemap.GetNode("AcquisitionFrameRate"))
            if PySpin.IsAvailable(fps_enable_node) and PySpin.IsWritable(fps_enable_node):
                fps_enable_node.SetValue(True)
            if PySpin.IsAvailable(fps_node) and PySpin.IsWritable(fps_node):
                fps_node.SetValue(fps)

        # --- ROI設定 ---
        w_node = PySpin.CIntegerPtr(nodemap.GetNode("Width"))
        h_node = PySpin.CIntegerPtr(nodemap.GetNode("Height"))
        x_node = PySpin.CIntegerPtr(nodemap.GetNode("OffsetX"))
        y_node = PySpin.CIntegerPtr(nodemap.GetNode("OffsetY"))

        if PySpin.IsWritable(x_node): x_node.SetValue(0)
        if PySpin.IsWritable(y_node): y_node.SetValue(0)
        max_w = w_node.GetMax()
        max_h = h_node.GetMax()

        roi_w = width if width not in (None, 0) else max_w
        roi_h = height if height not in (None, 0) else max_h

        if center_roi:
            offset_x = (max_w - roi_w) // 2
            offset_y = (max_h - roi_h) // 2
        else:
            offset_x = 0
            offset_y = 0

        offset_x -= offset_x % x_node.GetInc()
        offset_y -= offset_y % y_node.GetInc()
        roi_w -= roi_w % w_node.GetInc()
        roi_h -= roi_h % h_node.GetInc()

        if PySpin.IsWritable(w_node): w_node.SetValue(roi_w)
        if PySpin.IsWritable(h_node): h_node.SetValue(roi_h)

        max_offset_x = x_node.GetMax()
        max_offset_y = y_node.GetMax()
        offset_x = min(offset_x, max_offset_x)
        offset_y = min(offset_y, max_offset_y)

        if PySpin.IsWritable(x_node): x_node.SetValue(offset_x)
        if PySpin.IsWritable(y_node): y_node.SetValue(offset_y)

        # --- PixelFormat ---
        fmt_node = PySpin.CEnumerationPtr(nodemap.GetNode("PixelFormat"))
        if PySpin.IsAvailable(fmt_node) and PySpin.IsWritable(fmt_node):
            entry = fmt_node.GetEntryByName(pixel_format_name)
            if PySpin.IsAvailable(entry) and PySpin.IsReadable(entry):
                fmt_node.SetIntValue(entry.GetValue())

        # --- ReverseX/Y ---
        reverse_x_node = PySpin.CBooleanPtr(nodemap.GetNode("ReverseX"))
        if PySpin.IsAvailable(reverse_x_node) and PySpin.IsWritable(reverse_x_node):
            reverse_x_node.SetValue(self.reverse_x)

        reverse_y_node = PySpin.CBooleanPtr(nodemap.GetNode("ReverseY"))
        if PySpin.IsAvailable(reverse_y_node) and PySpin.IsWritable(reverse_y_node):
            reverse_y_node.SetValue(self.reverse_y)

        # --- White Balance ---
        wb_auto_node = PySpin.CEnumerationPtr(nodemap.GetNode("BalanceWhiteAuto"))
        if PySpin.IsAvailable(wb_auto_node) and PySpin.IsWritable(wb_auto_node):
            entry = wb_auto_node.GetEntryByName(white_balance_auto)
            if PySpin.IsAvailable(entry) and PySpin.IsReadable(entry):
                wb_auto_node.SetIntValue(entry.GetValue())

        if white_balance_auto == "Off":
            selector_node = PySpin.CEnumerationPtr(nodemap.GetNode("BalanceRatioSelector"))
            ratio_node = PySpin.CFloatPtr(nodemap.GetNode("BalanceRatio"))
            if PySpin.IsAvailable(selector_node) and PySpin.IsWritable(selector_node):
                # Red設定
                red_entry = selector_node.GetEntryByName("Red")
                selector_node.SetIntValue(red_entry.GetValue())
                ratio_node.SetValue(wb_red)
                # Blue設定
                blue_entry = selector_node.GetEntryByName("Blue")
                selector_node.SetIntValue(blue_entry.GetValue())
                ratio_node.SetValue(wb_blue)

        self.roi_info = {
            'x_min': offset_x,
            'y_min': offset_y,
            'x_max': offset_x + roi_w,
            'y_max': offset_y + roi_h
        }

        # --- Stream mode for LiveView ---
        self.camera.TLStream.StreamBufferHandlingMode.SetValue(PySpin.StreamBufferHandlingMode_NewestOnly)

        # --- BeginAcquisition（絶対必要）---
        self.camera.BeginAcquisition()

        # --- 状態更新 ---
        self._primed = True

    def release(self):
        try:
            if self.camera is not None:
                if self.camera.IsValid() and self.camera.IsInitialized():
                    self.camera.DeInit()
                del self.camera
        except Exception as e:
            print(f"[PrimaryCamera] release error: {e}")
        finally:
            self.cam_list.Clear()

    def __del__(self):
        pass  # Avoid calling release() automatically

    @property
    def primed(self):
        return self._primed
