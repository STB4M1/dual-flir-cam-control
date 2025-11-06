import sys
import os
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PySide6.QtCore import QThread
from ui.ui_mainwindow import Ui_MainWindow
from camera_control.camera_controller import CameraController
from camera_control.camera_worker import CameraWorker
from camera_control.camera_live_worker import CameraLiveWorker
from ui.gl_image_widget import ImageGLWidget
from ui.histogram_dialog import show_histogram_window
from ui.histogram_dialog import HistogramDialog
import PySpin
import numpy as np

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.system = PySpin.System.GetInstance()
        self.controller = CameraController(system=self.system)

        self.thread1 = None
        self.worker1 = None
        self.thread2 = None
        self.worker2 = None
        self.live_worker_cam1 = None
        self.live_worker_cam2 = None
        self.liveview_running_cam1 = False
        self.liveview_running_cam2 = False

        self.ui.pushButtonConnectCam1.clicked.connect(self.connect_camera1)
        self.ui.pushButtonConnectCam2.clicked.connect(self.connect_camera2)
        self.ui.pushButtonSelectSaveFolderCam1.clicked.connect(self.select_save_folder_cam1)
        self.ui.pushButtonSelectSaveFolderCam2.clicked.connect(self.select_save_folder_cam2)
        self.ui.pushButtonStartRecordCam1.clicked.connect(self.handle_record_cam1)
        self.ui.pushButtonStartRecordCam2.clicked.connect(self.start_record_camera2)
        self.ui.pushButtonStartRecordDualCams.clicked.connect(self.handle_dual_record_button) 
        self.ui.pushButtonCaptureOneFrameCam1_2.clicked.connect(self.capture_single_frame_sync)
        self.ui.comboBoxFpsCam1.currentTextChanged.connect(self.handle_fps_cam1_change)
        self.ui.comboBoxFpsCam2.currentTextChanged.connect(self.handle_fps_cam2_change)
        self.ui.pushButtonCaptureOneFrameCam1.clicked.connect(self.capture_single_frame_cam1)
        self.ui.pushButtonCaptureOneFrameCam2.clicked.connect(self.capture_single_frame_cam2)
        self.ui.pushButtonLiveViewCam1.clicked.connect(self.toggle_liveview_cam1)
        self.ui.pushButtonLiveViewCam2.clicked.connect(self.toggle_liveview_cam2)
        self.ui.pushButtonHistogramCam1.clicked.connect(self.on_histogram_button_cam1)
        self.ui.pushButtonHistogramCam2.clicked.connect(self.on_histogram_button_cam2)
        self.ui.pushButtonDisconnectCam1.clicked.connect(self.disconnect_cam1)
        self.ui.pushButtonDisconnectCam2.clicked.connect(self.disconnect_cam2)

    def connect_camera1(self):
        serial = self.ui.lineEditSerialCam1.text()
        self.controller.initialize_cam1(serial)
        self.ui.textEditLogCam1.append("[Cam1] Connected")

    def connect_camera2(self):
        serial = self.ui.lineEditSerialCam2_2.text()
        self.controller.initialize_cam2(serial)
        self.ui.textEditLogCam2.append("[Cam2] Connected")

    def select_save_folder_cam1(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.ui.lineEditSaveFolderCam1.setText(folder)

    def select_save_folder_cam2(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.ui.lineEditSaveFolderCam2.setText(folder)

    def capture_single_frame_cam1(self):
        try:
            self.controller.configure_cam1(
                folder=self.ui.lineEditSaveFolderCam1.text(),
                fps=self.ui.doubleSpinBoxFpsCam1.value(),
                exposure_time=self.ui.doubleSpinBoxExposureCam1.value(),
                gain_auto_mode=self.ui.comboBoxGainCam1.currentText(),
                exposure_auto_mode=self.ui.comboBoxExposureCam1.currentText(),
                width=self.ui.spinBoxWidthCam1.value(),
                height=self.ui.spinBoxHeightCam1.value(),
                offset_x=self.ui.spinBoxOffsetXCam1.value(),
                offset_y=self.ui.spinBoxOffsetYCam1.value(),
                center_roi=self.ui.checkBoxCenterROICam1.isChecked(),
                pixel_format=self.ui.comboBoxPixelFormatCam1.currentText(),
                extension=self.ui.comboBoxExtensionCam1.currentText(),
                reverse_x=self.ui.checkBoxReverseXCam1.isChecked(),
                reverse_y=self.ui.checkBoxReverseYCam1.isChecked(),
                white_balance_auto = self.ui.comboBoxWhiteBalanceAutoCam1.currentText(),
                wb_red  = self.ui.doubleSpinBoxBalanceRatioRedCam1.value(),
                wb_blue = self.ui.doubleSpinBoxBalanceRatioBlueCam1.value()
            )

            # 撮影実行！
            self.controller.cam1.trigger()
            filename = self.controller.cam1.capture_frame(custom_filename="Cam1." + self.controller.cam1.image_format)
            self.ui.textEditLogCam1.append(f"[Cam1] 1枚撮影 → {filename}")

        except Exception as e:
            self.ui.textEditLogCam1.append(f"[Cam1] 撮影エラー: {str(e)}")

    def capture_single_frame_cam2(self):
        try:
            self.controller.configure_cam2(
                folder=self.ui.lineEditSaveFolderCam2.text(),
                fps=self.ui.doubleSpinBoxFpsCam2.value(),
                exposure_time=self.ui.doubleSpinBoxExposureCam2.value(),
                gain_auto_mode=self.ui.comboBoxGainCam2.currentText(),
                exposure_auto_mode=self.ui.comboBoxExposureCam2.currentText(),
                width=self.ui.spinBoxWidthCam2.value(),
                height=self.ui.spinBoxHeightCam2.value(),
                offset_x=self.ui.spinBoxOffsetXCam2.value(),
                offset_y=self.ui.spinBoxOffsetYCam2.value(),
                center_roi=self.ui.checkBoxCenterROICam2.isChecked(),
                pixel_format=self.ui.comboBoxPixelFormatCam2.currentText(),
                extension=self.ui.comboBoxExtensionCam2.currentText(),
                reverse_x=self.ui.checkBoxReverseXCam2.isChecked(),
                reverse_y=self.ui.checkBoxReverseYCam2.isChecked(),
                white_balance_auto = self.ui.comboBoxWhiteBalanceAutoCam2.currentText(),
                wb_red  = self.ui.doubleSpinBoxBalanceRatioRedCam2.value(),
                wb_blue = self.ui.doubleSpinBoxBalanceRatioBlueCam2.value()
            )

            self.controller.cam2.trigger()
            filename = self.controller.cam2.capture_frame(custom_filename="Cam2." + self.controller.cam2.image_format)
            self.ui.textEditLogCam2.append(f"[Cam2] 1枚撮影 → {filename}")

        except Exception as e:
            self.ui.textEditLogCam2.append(f"[Cam2] 撮影エラー: {str(e)}")

    def handle_record_cam1(self):
        if self.ui.checkBoxSyncCheckCam1_2.isChecked():
            self.start_record_both_cameras()
        else:
            self.start_record_camera1()

    def start_record_camera1(self):
        was_liveview_on = self.liveview_running_cam1 #LiveViewの状態把握 
        self.stop_all_liveviews() # LiveView停止

        folder = self.ui.lineEditSaveFolderCam1.text()
        fps = self.ui.doubleSpinBoxFpsCam1.value()
        exposure_time = self.ui.doubleSpinBoxExposureCam1.value()
        gain_mode = self.ui.comboBoxGainCam1.currentText()
        exposure_mode = self.ui.comboBoxExposureCam1.currentText()
        width = self.ui.spinBoxWidthCam1.value()
        height = self.ui.spinBoxHeightCam1.value()
        offset_x = self.ui.spinBoxOffsetXCam1.value()
        offset_y = self.ui.spinBoxOffsetYCam1.value()
        center_roi = self.ui.checkBoxCenterROICam1.isChecked()
        pixel_format = self.ui.comboBoxPixelFormatCam1.currentText()
        extension = self.ui.comboBoxExtensionCam1.currentText()
        duration_sec = self.ui.doubleSpinBoxRecordingTimeCam1.value()
        reverse_x = self.ui.checkBoxReverseXCam1.isChecked()
        reverse_y = self.ui.checkBoxReverseYCam1.isChecked()
        white_balance_auto = self.ui.comboBoxWhiteBalanceAutoCam1.currentText()
        wb_red  = self.ui.doubleSpinBoxBalanceRatioRedCam1.value()
        wb_blue = self.ui.doubleSpinBoxBalanceRatioBlueCam1.value()

        self.controller.configure_cam1(
            folder=folder,
            fps=fps,
            exposure_time=exposure_time,
            gain_auto_mode=gain_mode,
            exposure_auto_mode=exposure_mode,
            width=width,
            height=height,
            offset_x=offset_x,
            offset_y=offset_y,
            center_roi=center_roi,
            pixel_format=pixel_format,
            extension=extension,
            reverse_x=reverse_x,
            reverse_y=reverse_y,
            white_balance_auto=white_balance_auto,
            wb_red=wb_red,
            wb_blue=wb_blue,
        )

        self.thread1 = QThread()
        self.worker1 = CameraWorker(self.controller, duration_sec, cam_id=1)
        self.worker1.moveToThread(self.thread1)
        self.thread1.started.connect(self.worker1.run)
        self.worker1.finished.connect(self.thread1.quit)
        self.worker1.finished.connect(self.worker1.deleteLater)
        self.thread1.finished.connect(self.thread1.deleteLater)
        self.worker1.error_occurred.connect(self.ui.textEditLogCam1.append)
        self.worker1.finished.connect(lambda: self.ui.textEditLogCam1.append("[Cam1] Recording finished."))

        # 録画終了後にLiveView復元（必要な場合だけ）
        self.worker1.finished.connect(lambda: self.resume_liveviews_if_needed(restore_cam1=was_liveview_on, restore_cam2=False))

        self.thread1.start()
        self.ui.textEditLogCam1.append("[Cam1] Recording started...")

    def start_record_camera2(self):
        was_liveview_on = self.liveview_running_cam2 #LiveViewの状態把握 
        self.stop_all_liveviews() # LiveView停止

        folder = self.ui.lineEditSaveFolderCam2.text()
        fps = self.ui.doubleSpinBoxFpsCam2.value()
        exposure_time = self.ui.doubleSpinBoxExposureCam2.value()
        gain_mode = self.ui.comboBoxGainCam2.currentText()
        exposure_mode = self.ui.comboBoxExposureCam2.currentText()
        width = self.ui.spinBoxWidthCam2.value()
        height = self.ui.spinBoxHeightCam2.value()
        offset_x = self.ui.spinBoxOffsetXCam2.value()
        offset_y = self.ui.spinBoxOffsetYCam2.value()
        center_roi = self.ui.checkBoxCenterROICam2.isChecked()
        pixel_format = self.ui.comboBoxPixelFormatCam2.currentText()
        extension = self.ui.comboBoxExtensionCam2.currentText()
        duration_sec = self.ui.doubleSpinBoxRecordingTimeCam2.value()
        reverse_x = self.ui.checkBoxReverseXCam2.isChecked()
        reverse_y = self.ui.checkBoxReverseYCam2.isChecked()
        white_balance_auto = self.ui.comboBoxWhiteBalanceAutoCam2.currentText()
        wb_red  = self.ui.doubleSpinBoxBalanceRatioRedCam2.value()
        wb_blue = self.ui.doubleSpinBoxBalanceRatioBlueCam2.value()

        self.controller.configure_cam2(
            folder=folder,
            fps=fps,
            exposure_time=exposure_time,
            gain_auto_mode=gain_mode,
            exposure_auto_mode=exposure_mode,
            width=width,
            height=height,
            offset_x=offset_x,
            offset_y=offset_y,
            center_roi=center_roi,
            pixel_format=pixel_format,
            extension=extension,
            trigger_mode='Off',
            reverse_x=reverse_x,
            reverse_y=reverse_y,
            white_balance_auto=white_balance_auto,
            wb_red=wb_red,
            wb_blue=wb_blue,
        )

        self.thread2 = QThread()
        self.worker2 = CameraWorker(self.controller, duration_sec, cam_id=2)
        self.worker2.moveToThread(self.thread2)
        self.thread2.started.connect(self.worker2.run)
        self.worker2.finished.connect(self.thread2.quit)
        self.worker2.finished.connect(self.worker2.deleteLater)
        self.thread2.finished.connect(self.thread2.deleteLater)
        self.worker2.error_occurred.connect(self.ui.textEditLogCam2.append)
        self.worker2.finished.connect(lambda: self.ui.textEditLogCam2.append("[Cam2] Recording finished."))

        # 録画終了後にLiveView復元（必要な場合だけ）
        self.worker2.finished.connect(lambda: self.resume_liveviews_if_needed(restore_cam1=False, restore_cam2=was_liveview_on))

        self.thread2.start()
        self.ui.textEditLogCam2.append("[Cam2] Recording started...")

    def handle_dual_record_button(self):  # 追加
        if self.ui.checkBoxSyncCheckCam1_2.isChecked():
            self.start_record_both_cameras()
        else:
            self.ui.textEditLogCam1.append("[Dual] 同時録画にはSyncチェックが必要です。")

    def capture_single_frame_sync(self):
        if not self.ui.checkBoxSyncCheckCam1_2.isChecked():
            self.ui.textEditLogCam1.append("[Sync Capture] Syncチェックが必要です。")
            return

        # 撮影前：LiveViewの状態を記録して一時停止
        was_cam1_live = self.liveview_running_cam1
        was_cam2_live = self.liveview_running_cam2
        self.stop_all_liveviews()

        try:
            # 🎥 Cam1設定
            self.controller.configure_cam1(
                folder=self.ui.lineEditSaveFolderCam1.text(),
                fps=self.ui.doubleSpinBoxFpsCam1.value(),
                exposure_time=self.ui.doubleSpinBoxExposureCam1.value(),
                gain_auto_mode=self.ui.comboBoxGainCam1.currentText(),
                exposure_auto_mode=self.ui.comboBoxExposureCam1.currentText(),
                width=self.ui.spinBoxWidthCam1.value(),
                height=self.ui.spinBoxHeightCam1.value(),
                offset_x=self.ui.spinBoxOffsetXCam1.value(),
                offset_y=self.ui.spinBoxOffsetYCam1.value(),
                center_roi=self.ui.checkBoxCenterROICam1.isChecked(),
                pixel_format=self.ui.comboBoxPixelFormatCam1.currentText(),
                extension=self.ui.comboBoxExtensionCam1.currentText(),
                reverse_x=self.ui.checkBoxReverseXCam1.isChecked(),
                reverse_y=self.ui.checkBoxReverseYCam1.isChecked(),
                white_balance_auto=self.ui.comboBoxWhiteBalanceAutoCam1.currentText(),
                wb_red=self.ui.doubleSpinBoxBalanceRatioRedCam1.value(),
                wb_blue=self.ui.doubleSpinBoxBalanceRatioBlueCam1.value()
            )

            # 🎥 Cam2設定
            self.controller.configure_cam2(
                folder=self.ui.lineEditSaveFolderCam2.text(),
                fps=self.ui.doubleSpinBoxFpsCam2.value(),
                exposure_time=self.ui.doubleSpinBoxExposureCam2.value(),
                gain_auto_mode=self.ui.comboBoxGainCam2.currentText(),
                exposure_auto_mode=self.ui.comboBoxExposureCam2.currentText(),
                width=self.ui.spinBoxWidthCam2.value(),
                height=self.ui.spinBoxHeightCam2.value(),
                offset_x=self.ui.spinBoxOffsetXCam2.value(),
                offset_y=self.ui.spinBoxOffsetYCam2.value(),
                center_roi=self.ui.checkBoxCenterROICam2.isChecked(),
                pixel_format=self.ui.comboBoxPixelFormatCam2.currentText(),
                extension=self.ui.comboBoxExtensionCam2.currentText(),
                trigger_mode='On',  # 🟢 Cam2もトリガー有効化
                reverse_x=self.ui.checkBoxReverseXCam2.isChecked(),
                reverse_y=self.ui.checkBoxReverseYCam2.isChecked(),
                white_balance_auto=self.ui.comboBoxWhiteBalanceAutoCam2.currentText(),
                wb_red=self.ui.doubleSpinBoxBalanceRatioRedCam2.value(),
                wb_blue=self.ui.doubleSpinBoxBalanceRatioBlueCam2.value()
            )

            # 📸 同期撮影実行！
            frame1, frame2 = self.controller.capture_single_frame(
                custom_filename1=f"Cam1.{self.controller.cam1.image_format}",
                custom_filename2=f"Cam2.{self.controller.cam2.image_format}"
            )

            self.ui.textEditLogCam1.append(f"[Cam1] 1枚撮影 → {frame1}")
            self.ui.textEditLogCam2.append(f"[Cam2] 1枚撮影 → {frame2}")

        except Exception as e:
            self.ui.textEditLogCam1.append(f"[Sync Capture] エラー: {str(e)}")

        finally:
            # 🟢 撮影後：必要ならLiveViewを再開
            self.resume_liveviews_if_needed(
                restore_cam1=was_cam1_live,
                restore_cam2=was_cam2_live
            )

    def start_record_both_cameras(self):

        was_cam1_live = self.liveview_running_cam1 # LiveViewの状態を保存
        was_cam2_live = self.liveview_running_cam2
        self.stop_all_liveviews() # LiveView一時停止

        # Cam1 UI
        folder1 = self.ui.lineEditSaveFolderCam1.text()
        fps1 = self.ui.doubleSpinBoxFpsCam1.value()
        exposure1 = self.ui.doubleSpinBoxExposureCam1.value()
        gain_mode1 = self.ui.comboBoxGainCam1.currentText()
        exposure_mode1 = self.ui.comboBoxExposureCam1.currentText()
        width1 = self.ui.spinBoxWidthCam1.value()
        height1 = self.ui.spinBoxHeightCam1.value()
        offset_x1 = self.ui.spinBoxOffsetXCam1.value()
        offset_y1 = self.ui.spinBoxOffsetYCam1.value()
        center_roi1 = self.ui.checkBoxCenterROICam1.isChecked()
        fmt1 = self.ui.comboBoxPixelFormatCam1.currentText()
        ext1 = self.ui.comboBoxExtensionCam1.currentText()
        dur1 = self.ui.doubleSpinBoxRecordingTimeCam1.value()
        reverse_x1 = self.ui.checkBoxReverseXCam1.isChecked()
        reverse_y1 = self.ui.checkBoxReverseYCam1.isChecked()
        white_balance_auto1 = self.ui.comboBoxWhiteBalanceAutoCam1.currentText()
        wb_red1 = self.ui.doubleSpinBoxBalanceRatioRedCam1.value()
        wb_blue1 = self.ui.doubleSpinBoxBalanceRatioBlueCam1.value()

        # Cam2 UI
        folder2 = self.ui.lineEditSaveFolderCam2.text()
        fps2 = self.ui.doubleSpinBoxFpsCam2.value()
        exposure2 = self.ui.doubleSpinBoxExposureCam2.value()
        gain_mode2 = self.ui.comboBoxGainCam2.currentText()
        exposure_mode2 = self.ui.comboBoxExposureCam2.currentText()
        width2 = self.ui.spinBoxWidthCam2.value()
        height2 = self.ui.spinBoxHeightCam2.value()
        offset_x2 = self.ui.spinBoxOffsetXCam2.value()
        offset_y2 = self.ui.spinBoxOffsetYCam2.value()
        center_roi2 = self.ui.checkBoxCenterROICam2.isChecked()
        fmt2 = self.ui.comboBoxPixelFormatCam2.currentText()
        ext2 = self.ui.comboBoxExtensionCam2.currentText()
        dur2 = self.ui.doubleSpinBoxRecordingTimeCam2.value()
        reverse_x2 = self.ui.checkBoxReverseXCam2.isChecked()
        reverse_y2 = self.ui.checkBoxReverseYCam2.isChecked()
        white_balance_auto2 = self.ui.comboBoxWhiteBalanceAutoCam2.currentText()
        wb_red2 = self.ui.doubleSpinBoxBalanceRatioRedCam2.value()
        wb_blue2 = self.ui.doubleSpinBoxBalanceRatioBlueCam2.value()

        self.controller.configure_cam1(
            folder=folder1,
            fps=fps1,
            exposure_time=exposure1,
            gain_auto_mode=gain_mode1,
            exposure_auto_mode=exposure_mode1,
            width=width1,
            height=height1,
            offset_x=offset_x1,
            offset_y=offset_y1,
            center_roi=center_roi1,
            pixel_format=fmt1,
            extension=ext1,
            reverse_x=reverse_x1,
            reverse_y=reverse_y1,
            white_balance_auto=white_balance_auto1,
            wb_red=wb_red1,
            wb_blue=wb_blue1,
        )

        self.controller.configure_cam2(
            folder=folder2,
            fps=fps2,
            exposure_time=exposure2,
            gain_auto_mode=gain_mode2,
            exposure_auto_mode=exposure_mode2,
            width=width2,
            height=height2,
            offset_x=offset_x2,
            offset_y=offset_y2,
            center_roi=center_roi2,
            pixel_format=fmt2,
            extension=ext2,
            trigger_mode='On',
            reverse_x=reverse_x2,
            reverse_y=reverse_y2,
            white_balance_auto=white_balance_auto2,
            wb_red=wb_red2,
            wb_blue=wb_blue2,
        )

        self.thread1 = QThread()
        self.worker1 = CameraWorker(self.controller, dur1, cam_id=1)
        self.worker1.moveToThread(self.thread1)
        self.thread1.started.connect(self.worker1.run)
        self.worker1.finished.connect(self.thread1.quit)
        self.worker1.finished.connect(self.worker1.deleteLater)
        self.thread1.finished.connect(self.thread1.deleteLater)
        self.worker1.error_occurred.connect(self.ui.textEditLogCam1.append)
        self.worker1.finished.connect(lambda: self.ui.textEditLogCam1.append("[Cam1] Sync Recording finished."))

        self.thread2 = QThread()
        self.worker2 = CameraWorker(self.controller, dur2, cam_id=2)
        self.worker2.moveToThread(self.thread2)
        self.thread2.started.connect(self.worker2.run)
        self.worker2.finished.connect(self.thread2.quit)
        self.worker2.finished.connect(self.worker2.deleteLater)
        self.thread2.finished.connect(self.thread2.deleteLater)
        self.worker2.error_occurred.connect(self.ui.textEditLogCam2.append)
        self.worker2.finished.connect(lambda: self.ui.textEditLogCam2.append("[Cam2] Sync Recording finished."))

        # 両方終了後にLiveView再開（必要なら）
        self.worker1.finished.connect(lambda: self.resume_liveviews_if_needed(was_cam1_live, was_cam2_live))
        self.worker2.finished.connect(lambda: None)  # Cam2はCam1と一緒に resume されるのでここでは何もしない

        self.thread1.start()
        self.thread2.start()

        self.ui.textEditLogCam1.append("[Cam1] Sync recording started...")
        self.ui.textEditLogCam2.append("[Cam2] Sync recording started...")

    def closeEvent(self, event):
        self.controller.release_cam1()
        self.controller.release_cam2()
        self.system.ReleaseInstance()
        event.accept()

    def handle_fps_cam1_change(self, text):
        if text.lower() == "max":
            max_fps = self.controller.get_max_fps(cam_id=1)
            self.ui.doubleSpinBoxFpsCam1.setValue(max_fps)
            self.ui.textEditLogCam1.append(f"[Cam1] Max FPS: {max_fps:.2f}")

    def handle_fps_cam2_change(self, text):
        if text.lower() == "max":
            max_fps = self.controller.get_max_fps(cam_id=2)
            self.ui.doubleSpinBoxFpsCam2.setValue(max_fps)
            self.ui.textEditLogCam2.append(f"[Cam2] Max FPS: {max_fps:.2f}")

    def toggle_liveview_cam1(self):
        """Cam1 LiveViewの開始・停止トグル"""
        if not self.liveview_running_cam1:
            try:
                cam1 = self.controller.cam1  # PrimaryCamera

                # UI設定を渡す
                cam1.prime_for_live(
                    fps=self.ui.doubleSpinBoxFpsCam1.value(),
                    exposure_time=self.ui.doubleSpinBoxExposureCam1.value(),
                    gain_auto_mode=self.ui.comboBoxGainCam1.currentText(),
                    exposure_auto_mode=self.ui.comboBoxExposureCam1.currentText(),
                    width=self.ui.spinBoxWidthCam1.value(),
                    height=self.ui.spinBoxHeightCam1.value(),
                    offset_x=self.ui.spinBoxOffsetXCam1.value(),
                    offset_y=self.ui.spinBoxOffsetYCam1.value(),
                    center_roi=self.ui.checkBoxCenterROICam1.isChecked(),
                    pixel_format_name=self.ui.comboBoxPixelFormatCam1.currentText(),
                    reverse_x=self.ui.checkBoxReverseXCam1.isChecked(),
                    reverse_y=self.ui.checkBoxReverseYCam1.isChecked(),
                    white_balance_auto=self.ui.comboBoxWhiteBalanceAutoCam1.currentText(),
                    wb_red=self.ui.doubleSpinBoxBalanceRatioRedCam1.value(),
                    wb_blue=self.ui.doubleSpinBoxBalanceRatioBlueCam1.value()
                )

                # LiveViewワーカー起動
                self.live_worker_cam1 = CameraLiveWorker(cam1)
                self.live_worker_cam1.new_frame.connect(self.update_liveview_cam1)
                self.live_worker_cam1.start()

                self.liveview_running_cam1 = True
                self.ui.pushButtonLiveViewCam1.setText("Stop LiveView")
                self.ui.textEditLogCam1.append("[Cam1] LiveView開始")

            except Exception as e:
                self.ui.textEditLogCam1.append(f"[Cam1] LiveView開始失敗: {e}")

        else:
            # Live停止
            if self.live_worker_cam1:
                # 🔹 ヒストグラム連動があれば切断
                if hasattr(self, "hist_dialog_cam1"):
                    try:
                        self.live_worker_cam1.new_frame.disconnect(self.hist_dialog_cam1.update_image)
                    except:
                        pass
                self.live_worker_cam1.stop()
                self.live_worker_cam1.wait()
                self.live_worker_cam1 = None

            self.liveview_running_cam1 = False
            self.ui.pushButtonLiveViewCam1.setText("Start LiveView")
            self.ui.textEditLogCam1.append("[Cam1] LiveView停止")


    def toggle_liveview_cam2(self):
        """Cam2 LiveViewの開始・停止トグル"""
        if not self.liveview_running_cam2:
            try:
                cam2 = self.controller.cam2  # SecondaryCamera

                cam2.prime_for_live(
                    fps=self.ui.doubleSpinBoxFpsCam2.value(),
                    exposure_time=self.ui.doubleSpinBoxExposureCam2.value(),
                    gain_auto_mode=self.ui.comboBoxGainCam2.currentText(),
                    exposure_auto_mode=self.ui.comboBoxExposureCam2.currentText(),
                    width=self.ui.spinBoxWidthCam2.value(),
                    height=self.ui.spinBoxHeightCam2.value(),
                    offset_x=self.ui.spinBoxOffsetXCam2.value(),
                    offset_y=self.ui.spinBoxOffsetYCam2.value(),
                    center_roi=self.ui.checkBoxCenterROICam2.isChecked(),
                    pixel_format_name=self.ui.comboBoxPixelFormatCam2.currentText(),
                    reverse_x=self.ui.checkBoxReverseXCam2.isChecked(),
                    reverse_y=self.ui.checkBoxReverseYCam2.isChecked(),
                    white_balance_auto=self.ui.comboBoxWhiteBalanceAutoCam2.currentText(),
                    wb_red=self.ui.doubleSpinBoxBalanceRatioRedCam2.value(),
                    wb_blue=self.ui.doubleSpinBoxBalanceRatioBlueCam2.value()
                )

                self.live_worker_cam2 = CameraLiveWorker(cam2)
                self.live_worker_cam2.new_frame.connect(self.update_liveview_cam2)
                self.live_worker_cam2.start()

                self.liveview_running_cam2 = True
                self.ui.pushButtonLiveViewCam2.setText("Stop LiveView")
                self.ui.textEditLogCam2.append("[Cam2] LiveView開始")

            except Exception as e:
                self.ui.textEditLogCam2.append(f"[Cam2] LiveView開始失敗: {e}")

        else:
            if self.live_worker_cam2:
                if hasattr(self, "hist_dialog_cam2"):
                    try:
                        self.live_worker_cam2.new_frame.disconnect(self.hist_dialog_cam2.update_image)
                    except:
                        pass
                self.live_worker_cam2.stop()
                self.live_worker_cam2.wait()
                self.live_worker_cam2 = None

            self.liveview_running_cam2 = False
            self.ui.pushButtonLiveViewCam2.setText("Start LiveView")
            self.ui.textEditLogCam2.append("[Cam2] LiveView停止")

    def update_liveview_cam1(self, img_np):
        try:
            h, w = img_np.shape[:2]  # グレースケール・カラー両対応！

            # ======== グレースケール処理 ========
            if img_np.ndim == 2:
                qimg = QImage(img_np.data, w, h, QImage.Format_Grayscale8)

            # ======== カラー処理（BGR→RGB変換） ========
            elif img_np.ndim == 3 and img_np.shape[2] == 3:
                # BGR → RGB に変換（FLIRはBGRが多い）
                img_rgb = img_np[:, :, ::-1].copy()
                qimg = QImage(img_rgb.data, w, h, 3 * w, QImage.Format_RGB888)

            else:
                raise ValueError("Unsupported image format")

            pixmap = QPixmap.fromImage(qimg)
            self.ui.openGLWidgetImageCam1.setPixmap(pixmap)

        except Exception as e:
            self.ui.textEditLogCam1.append(f"[Cam1] 表示エラー: {e}")


    def update_liveview_cam2(self, img_np):
        try:
            h, w = img_np.shape[:2]

            if img_np.ndim == 2:
                qimg = QImage(img_np.data, w, h, QImage.Format_Grayscale8)

            elif img_np.ndim == 3 and img_np.shape[2] == 3:
                img_rgb = img_np[:, :, ::-1].copy()  # BGR→RGB
                qimg = QImage(img_rgb.data, w, h, 3 * w, QImage.Format_RGB888)

            else:
                raise ValueError("Unsupported image format")

            pixmap = QPixmap.fromImage(qimg)
            self.ui.openGLWidgetImageCam2.setPixmap(pixmap)

        except Exception as e:
            self.ui.textEditLogCam2.append(f"[Cam2] 表示エラー: {e}")

    def stop_all_liveviews(self):
        if self.liveview_running_cam1 and self.live_worker_cam1 is not None:
            self.live_worker_cam1.stop()
            self.live_worker_cam1.wait()
            self.live_worker_cam1 = None
            self.liveview_running_cam1 = False
            self.ui.pushButtonLiveViewCam1.setText("Start LiveView")
            self.ui.textEditLogCam1.append("[Cam1] LiveView 強制停止")

        if self.liveview_running_cam2 and self.live_worker_cam2 is not None:
            self.live_worker_cam2.stop()
            self.live_worker_cam2.wait()
            self.live_worker_cam2 = None
            self.liveview_running_cam2 = False
            self.ui.pushButtonLiveViewCam2.setText("Start LiveView")
            self.ui.textEditLogCam2.append("[Cam2] LiveView 強制停止")

    def resume_liveviews_if_needed(self, restore_cam1: bool, restore_cam2: bool):
        if restore_cam1:
            self.toggle_liveview_cam1()
            self.ui.textEditLogCam1.append("[Cam1] 録画後にLiveViewを再開")

        if restore_cam2:
            self.toggle_liveview_cam2()
            self.ui.textEditLogCam2.append("[Cam2] 録画後にLiveViewを再開")

    def qpixmap_to_numpy(self, pixmap):
        image = pixmap.toImage().convertToFormat(QImage.Format_BGR888)
        width = image.width()
        height = image.height()

        ptr = image.bits()
        ptr.setsize(image.sizeInBytes())  # ← バッファサイズを正確に確保！
        arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 3))

        return arr.copy()  # ← 安全のためコピー（Qtバッファ切り離し）

    # def qpixmap_to_numpy(self, pixmap):
    #     image = pixmap.toImage()
    #     width = image.width()
    #     height = image.height()

    #     # 🔹 カラー形式に変換（BGR8）
    #     image = image.convertToFormat(QImage.Format_BGR888)

    #     ptr = image.bits()
    #     data = ptr.tobytes()  # ← PySide6ではこれでOK！

    #     arr = np.frombuffer(data, np.uint8).reshape((height, width, 3))
    #     arr = arr[:, :, ::-1].copy()  # BGR→RGB
    #     return arr

    def on_histogram_button_cam1(self):
        if not hasattr(self, "hist_dialog_cam1") or self.hist_dialog_cam1 is None:
            from ui.histogram_dialog import HistogramDialog
            self.hist_dialog_cam1 = HistogramDialog(title="Cam1 ライブヒストグラム")

        self.hist_dialog_cam1.show()

        if self.live_worker_cam1:
            try:
                self.live_worker_cam1.new_frame.connect(self.hist_dialog_cam1.update_image)
                print("✅ Cam1 histogram connected to live feed")
            except TypeError:
                pass
        else:
            pixmap = self.ui.openGLWidgetImageCam1.pixmap
            if pixmap:
                gray_np = self.qpixmap_to_numpy(pixmap)
                self.hist_dialog_cam1.update_image(gray_np)
            else:
                print("⚠️ Cam1: Live画像がありません")


    def on_histogram_button_cam2(self):
        if not hasattr(self, "hist_dialog_cam2") or self.hist_dialog_cam2 is None:
            from ui.histogram_dialog import HistogramDialog
            self.hist_dialog_cam2 = HistogramDialog(title="Cam2 ライブヒストグラム")

        self.hist_dialog_cam2.show()

        if self.live_worker_cam2:
            try:
                self.live_worker_cam2.new_frame.connect(self.hist_dialog_cam2.update_image)
                print("✅ Cam2 histogram connected to live feed")
            except TypeError:
                pass
        else:
            pixmap = self.ui.openGLWidgetImageCam2.pixmap
            if pixmap:
                gray_np = self.qpixmap_to_numpy(pixmap)
                self.hist_dialog_cam2.update_image(gray_np)
            else:
                print("⚠️ Cam2: Live画像がありません")


    def disconnect_cam1(self):
        try:
            # LiveViewスレッドが動いてたら止める
            if self.liveview_running_cam1 and self.live_worker_cam1 is not None:
                self.live_worker_cam1.stop()
                self.live_worker_cam1.wait()
                self.live_worker_cam1 = None
                self.liveview_running_cam1 = False
                self.ui.textEditLogCam1.append("[Cam1] LiveView 停止")

            # カメラ解放
            self.controller.release_cam1()
            self.ui.textEditLogCam1.append("[Cam1] 切断完了")

        except Exception as e:
            self.ui.textEditLogCam1.append(f"[Cam1] 切断失敗: {e}")

    def disconnect_cam2(self):
        try:
            if self.liveview_running_cam2 and self.live_worker_cam2 is not None:
                self.live_worker_cam2.stop()
                self.live_worker_cam2.wait()
                self.live_worker_cam2 = None
                self.liveview_running_cam2 = False
                self.ui.textEditLogCam2.append("[Cam2] LiveView 停止")

            self.controller.release_cam2()
            self.ui.textEditLogCam2.append("[Cam2] 切断完了")

        except Exception as e:
            self.ui.textEditLogCam2.append(f"[Cam2] 切断失敗: {e}")




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
