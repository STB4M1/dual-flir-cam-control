
# 📷 Dual FLIRカメラ制御アプリ

2台のFLIRカメラをGUI上から個別または同期で制御・撮影・録画できるアプリケーションです。  
Teledyne FLIR社の公式Spinnaker SDK（Pythonバインディング：`PySpin`）を使用しており、外部トリガによるハード同期撮影にも対応しています。

---

## 🌟 特徴

- 🔌 2台のFLIRカメラを**個別接続／切断**
- 🎯 同期モードにより**ハードウェアトリガによる同時撮影**
- 📸 静止画撮影・🎞録画（時間指定）に対応
- 🖼 ライブビュー（OpenGLWidgetベース）
- ⚙ FPS / ROI / ゲイン / 露光時間 / ピクセルフォーマット など詳細設定可
- 📂 保存先フォルダをGUI上から指定
- 📊 ヒストグラム表示
- 💡 GUIスレッドとは別スレッドでの録画処理で安定動作
- 📄 実行ログのリアルタイム表示

---

## 🖥 GUI構成

| 機能 | 説明 |
|------|------|
| カメラ接続 | シリアル番号を指定してカメラ1・2を個別に接続／切断 |
| パラメータ設定 | FPS・露光・ゲイン・ピクセルフォーマット・ROIなどを個別に設定可能 |
| 静止画撮影 | 個別または同期（同時）で1枚撮影 |
| 録画 | 秒数指定で録画（個別または同期） |
| ライブビュー | 各カメラのリアルタイム映像を表示（OpenGL使用） |
| 保存先選択 | 保存ディレクトリを個別に選択可能 |
| ヒストグラム | 撮影画像の濃度分布を別ウィンドウで表示 |
| ログ表示 | 実行処理の詳細をリアルタイムで表示 |

---

## 🔧 カメラ制御構成

- **PrimaryCamera（親）**：ソフトウェア／外部トリガで撮影可能。必要に応じて Line 出力でトリガ送信
- **SecondaryCamera（子）**：Line3 からの外部トリガ受信で同期撮影を実現
- FPSの整合性や ROI の調整は自動補正され、カメラの仕様に沿った安全な設定が可能

---

## 🧵 録画処理とスレッド構成

- `CameraWorker` クラスを使用して、録画処理は**QThread上で非同期実行**
- GUIの応答性を保ちつつ、指定秒数で安定したキャプチャを実現
- エラー時にはシグナルで通知され、ログ表示に反映

---

## 📁 ディレクトリ構成

```txt
DualFLIRCamControlApp/
├── main.py                       # アプリ起動とGUI接続
├── camera_control/
│   ├── camera_controller.py     # カメラ制御の統括管理クラス
│   ├── primary_camera_gui.py    # 親カメラ制御クラス
│   ├── secondary_camera_gui.py  # 子カメラ制御クラス
│   ├── camera_worker.py         # 録画処理ワーカークラス
│   └── camera_live_worker.py    # ライブビュー処理ワーカークラス
├── ui/
│   └── ui_mainwindow.py         # GUIの構成要素（自動生成）
├── util/
│   ├── log_helper.py            # ログ出力整形
│   └── camera_discovery.py      # カメラ一覧取得
├── outputs/                     # 保存先（画像・録画結果）
└── .gitignore                   # 不要ファイル除外設定
```

---

## 💻 動作環境

- **OS**：Windows 10 / 11（FLIR SDK対応環境）
- **Python**：3.8〜3.11
- **依存パッケージ**（一例）：
  - `PySide6`
  - `numpy`
  - `PyOpenGL`
  - `PySpin`（＝公式Spinnaker SDKのPythonバインディング）

---

## ⚠️ 注意：PySpinの取り扱いについて

- `PySpin` は **Teledyne FLIR公式のPythonバインディング**
- **インストールは pip ではなく、Spinnaker SDK のインストーラ内にある `.whl` ファイルを使用**  
  → 例：`pip install spinnaker_python‑3.0.0.118-cp39-cp39-win_amd64.whl`
- `import PySpin` と書きます（`Spinnaker_Python` などではありません）
- PyPIにある `pyspin` などは **非公式・別物** なので注意！

---

## 🚀 起動方法（例）

```bash
# 仮想環境推奨
python -m venv venv
venv\Scripts\activate

# 必要なパッケージをインストール
pip install -r requirements.txt

# PySpin は別途 .whl をローカルからインストール
pip install spinnaker_python-*.whl

# アプリ起動
python main.py
```

---

## 🪪 ライセンス

MIT License（予定）  
※研究・教育・開発目的での利用を歓迎します

---

## 🙌 作者・貢献

本アプリは個人開発プロジェクトとして作成されました。  
高精度な同期撮影を必要とする光学・マイクロ流体の研究や、画像処理・制御の研究開発用途に最適です。
