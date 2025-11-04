# 📷 Dual FLIR カメラ制御アプリ
*A Dual FLIR Camera Control Application for synchronized optical imaging and recording.*

---

## 🧭 概要（Overview）

2台の FLIR カメラを **GUI 上から個別または同期** で制御・撮影・録画できるアプリケーションです。  
Teledyne FLIR 社の公式 Spinnaker SDK（Python バインディング：`PySpin`）を使用しており、  
**外部トリガによるハードウェア同期撮影** にも対応しています。

---

## 🌟 主な特徴（Main Features）

| 分類 | 機能 | 説明 |
|------|------|------|
| 🎥 **カメラ接続** | 個別接続／切断 | 各カメラをシリアル番号指定で接続可能 |
| 🔄 **同期撮影** | ハードトリガ対応 | Primary → Secondary 間で Line3 による外部同期撮影 |
| 🖼 **ライブビュー** | OpenGL 表示 | PySide6 + OpenGL によるリアルタイム描画 |
| 📸 **静止画撮影** | 個別／同期対応 | ワンクリックで1枚キャプチャ、RAW/TIFF保存可 |
| 🎞 **動画撮影** | 時間指定録画 | 指定秒数の録画が可能（個別／同期） |
| ⚙ **カメラ設定** | FPS／露光／ゲイン／ピクセルフォーマット | 全て GUI から変更可 |
| 🎚 **ホワイトバランス** | Auto（Off／Once／Continuous）設定可 | BalanceWhiteAuto ノード制御 |
| 🔴 **Balance Ratio** | Red／Blue／値入力対応 | BalanceRatioSelector と BalanceRatio ノードを操作 |
| 🎯 **ROI設定** | Width／Height／OffsetX／OffsetY | センター寄せ or 任意位置での ROI 設定 |
| 🔁 **画像反転** | ReverseX／ReverseY | ミラー／上下反転機能 |
| 📂 **保存機能** | 出力フォルダ指定 | 撮影データ保存先を GUI から変更可 |
| 🧮 **ヒストグラム** | グレースケール分布表示 | 撮影結果の明暗分布を別ウィンドウで表示（Gray+RGB）|
| 📡 **ログ出力** | 実行ログ表示 | リアルタイムでカメラ操作をテキスト出力 |
| 🧵 **スレッド制御** | QThread録画処理 | GUIと非同期に撮影処理を実行して安定動作 |
| 🧠 **自動補正** | FPS・ROI補正 | カメラ仕様範囲に自動クランプして安全設定 |
| 🧰 **エラーハンドリング** | PySpin例外検知 | ノード未対応・範囲外設定をキャッチし安全停止 |
| 💾 **設定保存（将来対応）** | JSON保存予定 | GUI設定をJSONへ永続化予定 |

---

## 🖥 GUI 構成（GUI Layout）

| 機能 | 説明 |
|------|------|
| カメラ接続 | シリアル番号を指定してカメラ1・2を個別に接続／切断 |
| パラメータ設定 | FPS・露光・ゲイン・ピクセルフォーマット・ROIなどを個別に設定可能 |
| ホワイトバランス | White Balance Auto（Off／Once／Continuous）選択 |
| バランス比 | Balance Ratio（Red／Blue／Value）をGUIで調整可能 |
| 静止画撮影 | 個別または同期（同時）で1枚撮影 |
| 録画 | 秒数指定で録画（個別または同期） |
| ライブビュー | 各カメラのリアルタイム映像を表示（OpenGL 使用） |
| 保存先選択 | 保存ディレクトリを個別に選択可能 |
| ヒストグラム | 撮影画像の濃度分布を別ウィンドウで表示 |
| ログ表示 | 実行処理の詳細をリアルタイムで表示 |

---

## 🔧 カメラ制御構成（Camera Architecture）

- **PrimaryCamera（親）**：ソフトウェア／外部トリガで撮影可能。必要に応じて Line 出力でトリガ送信。  
- **SecondaryCamera（子）**：Line3 からの外部トリガ受信で同期撮影を実現。  
- FPS や ROI の整合性は自動補正され、カメラの仕様に沿った安全な設定が可能。

---

## 🧵 録画処理とスレッド構成（Thread Architecture）

- `CameraWorker` クラスを使用して、録画処理は **QThread 上で GUI とは別実行**
- GUI の応答性を保ちつつ、指定秒数で安定したキャプチャを実現
- エラー発生時はシグナル経由でログへ反映

---

## 🧩 UIファイル（.ui → .py 変換方法）

Qt Designer で作成・編集した `.ui` ファイル（例：`mainwindow.ui`）は、  
**PySide6 の UI コンパイラ (`pyside6-uic`)** を使用して Python コードへ変換します。

### 🔧 コマンド

```bash
pyside6-uic mainwindow.ui -o ./ui/ui_mainwindow.py
```

- `mainwindow.ui`: Qt Designer で設計した UI ファイル  
- `ui/ui_mainwindow.py`: 変換後に自動生成される Python GUI クラス  

### ⚠️ 注意点

- **日本語パス／スペースを含むディレクトリ** にあるとエラーが出る場合があります。  
  → 例: `File 'mainwindow.ui' is not valid`  
  → 対応策: 英数字パスへ移動して実行

- `.ui` を更新した場合は **再度上記コマンドを実行** してください。  
  更新が反映されない場合、古い `ui_mainwindow.py` が残っている可能性があります。

### 💡 PowerShell 例（Windows）

```powershell
micromamba activate flir
pyside6-uic mainwindow.ui -o .\ui\ui_mainwindow.py
```

---

## 🧰 FLIR環境構築（Micromamba + Python環境）

### 📦 Micromambaのインストール（Windows）

1. **公式サイト：**  
   👉 [Micromamba Installation Guide](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html)

2. **PowerShellを開いて、次を順番に実行：**
   ```powershell
   cd $HOME\Documents
   Invoke-Webrequest -URI https://micro.mamba.pm/api/micromamba/win-64/latest -OutFile micromamba.tar.bz2
   tar xf micromamba.tar.bz2
   New-Item -ItemType Directory -Path C:\micromamba -Force | Out-Null
   Move-Item -Force .\Library\bin\micromamba.exe C:\micromamba\micromamba.exe
   $Env:MAMBA_ROOT_PREFIX = "C:\micromambaenv"
   Remove-Item micromamba.tar.bz2 -Force
   C:\micromamba\micromamba.exe shell init -s powershell -r $Env:MAMBA_ROOT_PREFIX
   ```

3. **長パスを有効化する確認が出たら、`y` を入力：**
   ```
   Enter admin mode to enable long paths support?: [y/N] y
   Windows long-path support enabled.
   ```

4. **PowerShell再起動後、スクリプト実行を許可：**
   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
   ```

5. **再起動して、動作確認：**
   ```powershell
   micromamba --help
   ```
   「Version: 2.x.x」と表示されればOK ✅

---

### 🐍 Python 3.10環境の作成（FLIR用）

1. **Python 3.10で新しい環境を作成：**
   ```powershell
   micromamba create -n flir -c conda-forge python=3.10
   ```

2. **環境をアクティベート：**
   ```powershell
   micromamba activate flir
   ```
   `(flir)` の表示になれば成功 ✅

---

### 🔧 Spinnaker SDK（PySpin）のインストール

1. **公式サイトからSpinnaker SDKをダウンロード：**  
   👉 [Spinnaker SDK Downloads](https://www.teledynevisionsolutions.com/support/support-center/software-firmware-downloads/iis/spinnaker-sdk-download/spinnaker-sdk--download-files/?pn=Spinnaker+SDK&vn=Spinnaker+SDK)

   - Windows Full（SpinView付き）をインストール
   - Python binding (`spinnaker_python-*.whl`) をダウンロード

2. **.whlをインストール（Python 3.10対応版）：**
   ```powershell
   pip install C:\Path\To\spinnaker_python-4.2.0.88-cp310-cp310-win_amd64.whl
   ```

3. **PySpin動作確認：**
   ```powershell
   python -c "import PySpin; print('PySpin import OK')"
   ```

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

## 💻 動作環境（Environment）

- **OS**：Windows 10 / 11（FLIR SDK対応環境）  
- **Python**：3.8〜3.10  
- **主要依存パッケージ：**
  - `PySide6`
  - `numpy`
  - `PyOpenGL`
  - `PySpin`（＝公式 Spinnaker SDK の Python バインディング）

---

## ⚠️ PySpin の注意点（About PySpin）

- `PySpin` は **Teledyne FLIR 公式 Python バインディング**
- **pip ではなく、Spinnaker SDK 付属の `.whl` ファイルを使用してインストール**  
  ```bash
  pip install spinnaker_python‑4.2.0.88‑cp310‑cp310‑win_amd64.whl
  ```
- PyPI にある `pyspin` などは非公式・別物です

📘 公式ダウンロードページ：  
👉 [Spinnaker SDK Downloads](https://www.teledynevisionsolutions.com/support/support-center/software-firmware-downloads/iis/spinnaker-sdk-download/spinnaker-sdk--download-files/?pn=Spinnaker+SDK&vn=Spinnaker+SDK)

---

## 🚀 起動方法（Run）

```bash
python main.py
```

---

## 🧾 免責事項（Disclaimer）

本アプリは個人の研究・学習目的で開発されたものであり、  
本ソフトウェアの使用に伴ういかなる問題や損害についても、作者は一切の責任を負いません。  
利用される場合は、ご自身の責任にてお願いいたします。

