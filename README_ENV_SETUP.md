# 🧰 環境構築（Environment Setup）

## 🐍 Micromamba のインストール（Windows）

Teledyne FLIR の Spinnaker SDK を用いた撮影には、安定した Python 環境が必要です。  
本アプリでは **Micromamba（軽量な Conda 互換ツール）** を推奨しています。

公式ドキュメント：  
👉 [Micromamba Installation Guide](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html)

---

## 💿 手順

### ① PowerShell で Micromamba を取得

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

実行後、以下が表示されればOK：

```
Init powershell profile at 'C:\Users\<ユーザー名>\Documents\WindowsPowerShell\profile.ps1'
Enter admin mode to enable long paths support?: [y/N] y
Windows long-path support enabled.
```

---

### ② PowerShell のスクリプト実行を有効化

PowerShell 再起動時に次のようなエラーが出た場合：

```
このシステムではスクリプトの実行が無効になっているため...
```

次のコマンドで実行ポリシーを変更：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

その後、再び PowerShell を再起動してください。

---

### ③ 動作確認

```powershell
micromamba --help
```

バージョン情報（例：`Version: 2.3.2`）が表示されればOKです ✅

---

## 🧪 Python 3.10 環境の作成

Micromamba が動作したら、Python 3.10 用の環境を作成します。

```powershell
micromamba create -n flir -c conda-forge python=3.10
```

環境を有効化：

```powershell
micromamba activate flir
```

プロンプトが `(flir)` に変われば、環境が有効化されています。

---

## 📦 PySpin（Spinnaker SDK） のインストール

FLIR カメラ制御に必要な公式 PySpin を、ダウンロード済みの `.whl` ファイルからインストールします：

```powershell
(flir) PS C:\Users\<ユーザー名>\Documents\spinnaker_python-4.2.0.88-cp310-cp310-win_amd64> pip install spinnaker_python-4.2.0.88-cp310-cp310-win_amd64.whl
```

これで、FLIR カメラ撮影用の Python 環境が構築完了 🎉
