# Streamlit Cloudへのデプロイ完全ガイド

このガイドでは、時間割自動生成アプリをStreamlit Cloudに無料でデプロイする手順を説明します。

## 📋 前提条件

- GitHubアカウント（無料）
- Streamlit Cloudアカウント（無料、GitHubでサインアップ可能）

## 🚀 デプロイ手順

### ステップ1: GitHubリポジトリの作成

1. **GitHubにアクセス**: https://github.com にログイン
2. **新規リポジトリ作成**:
   - 右上の「+」→「New repository」をクリック
   - Repository name: `timetable-generator`（任意の名前）
   - Public または Private を選択
   - 「Create repository」をクリック

### ステップ2: プロジェクトをGitHubにプッシュ

ローカル環境で以下のコマンドを実行:

```bash
cd /home/ryogoyamamoto/timetable-engine

# Gitリポジトリの初期化
git init

# すべてのファイルを追加
git add .

# コミット
git commit -m "Initial commit: Timetable generation app"

# GitHubリポジトリと連携（URLは自分のリポジトリに置き換え）
git remote add origin https://github.com/YOUR_USERNAME/timetable-generator.git

# プッシュ
git branch -M main
git push -u origin main
```

### ステップ3: Streamlit Cloudでアプリをデプロイ

1. **Streamlit Cloudにアクセス**: https://streamlit.io/cloud
2. **サインイン**: GitHubアカウントでログイン
3. **新しいアプリをデプロイ**:
   - 「New app」ボタンをクリック
   - **Repository**: `YOUR_USERNAME/timetable-generator` を選択
   - **Branch**: `main` を選択
   - **Main file path**: `app.py` と入力
   - 「Advanced settings」をクリック（オプション）:
     - Python version: `3.11` を選択
   - 「Deploy!」ボタンをクリック

4. **デプロイ完了を待つ**: 2〜5分程度でアプリが起動します

### ステップ4: アプリにアクセス

デプロイが完了すると、以下のようなURLが発行されます:
```
https://YOUR_APP_NAME.streamlit.app
```

このURLを共有すれば、誰でもアプリを使用できます！

## 📁 必要なファイル（すべて準備済み）

以下のファイルが既に用意されています:

✅ `app.py` - メインアプリケーション
✅ `requirements.txt` - 依存パッケージリスト
✅ `models.py` - データモデル
✅ `constraints.py` - 制約検証
✅ `solver.py` - OR-Toolsソルバー
✅ `backtrack_solver.py` - バックトラックソルバー
✅ `utils.py` - ユーティリティ
✅ `sample_data/` - サンプルCSVファイル
✅ `.gitignore` - Git除外設定
✅ `README.md` - プロジェクト説明

## 🔧 トラブルシューティング

### エラー: "ModuleNotFoundError"

**原因**: `requirements.txt` に必要なパッケージが記載されていない

**解決策**: `requirements.txt` の内容を確認:
```
ortools>=9.7.0
streamlit>=1.28.0
pandas>=2.0.0
openpyxl>=3.1.0
```

### エラー: OR-Toolsのインストール失敗

**原因**: OR-Toolsのコンパイルに時間がかかる場合がある

**解決策**: Streamlit Cloudの設定で以下を確認:
- Python version: 3.11
- 待ち時間: 最大10分程度

または、`requirements.txt` で以下のように変更:
```
ortools>=9.8.0  # 最新版を試す
```

### アプリが遅い

**原因**: 無料プランではリソースが制限されている

**解決策**:
1. バックトラックソルバーの最大試行回数を調整（デフォルト20000 → 10000）
2. OR-Toolsを優先的に使用（高速）

## 🌐 代替デプロイオプション

### オプション1: Hugging Face Spaces

1. https://huggingface.co/spaces にアクセス
2. 「Create new Space」をクリック
3. Space SDK: 「Streamlit」を選択
4. GitHubリポジトリを接続してデプロイ

### オプション2: Render

1. https://render.com にアクセス
2. 「New」→「Web Service」を選択
3. GitHubリポジトリを接続
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`

### オプション3: Google Cloud Run

より高度なデプロイ方法。Dockerコンテナを使用。

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8080
CMD streamlit run app.py --server.port=8080 --server.address=0.0.0.0
```

## 🎯 デプロイ後の使い方

1. **アプリURL**をブラウザで開く
2. **サンプルデータをダウンロード** (GitHubのsample_data/から)
3. **CSVファイルをアップロード**
4. **時間割生成開始ボタン**をクリック
5. **結果をExcelでダウンロード**

## 💡 ベストプラクティス

### セキュリティ
- 個人情報を含むデータは注意して扱う
- パブリックアプリの場合、データは一時的にのみ保存される

### パフォーマンス
- 小規模データ（3〜5クラス）から始める
- OR-Toolsソルバーを優先使用
- タイムアウトを適切に設定（120秒）

### メンテナンス
- GitHubでバージョン管理
- 定期的に依存パッケージを更新
- Streamlit Cloudは自動的に最新コードをデプロイ

## 📞 サポートが必要な場合

1. **Streamlit Community**: https://discuss.streamlit.io/
2. **GitHub Issues**: リポジトリにIssueを作成
3. **ドキュメント**: https://docs.streamlit.io/

## ✅ チェックリスト

デプロイ前に確認:

- [ ] GitHubリポジトリを作成した
- [ ] すべてのファイルをプッシュした
- [ ] requirements.txt が正しい
- [ ] .gitignore でキャッシュを除外している
- [ ] Streamlit Cloudアカウントを作成した
- [ ] アプリをデプロイした
- [ ] ブラウザでアプリが開ける
- [ ] サンプルデータでテストした

---

**成功したら**: URLを共有して誰でも時間割を生成できるようになります！🎉
