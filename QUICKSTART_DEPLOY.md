# 🚀 簡単デプロイガイド

時間割自動生成アプリを世界中どこからでもアクセスできるようにする3ステップ！

## 📊 デプロイフロー

![Deployment Workflow](/home/ryogoyamamoto/.gemini/antigravity/brain/96c96665-e902-4109-a361-dc65cd80da4a/deployment_workflow_diagram_1770173173248.png)

## ⚡ 3ステップでデプロイ

### ステップ1️⃣: GitHubにコードを保存（5分）

```bash
# プロジェクトフォルダに移動
cd /home/ryogoyamamoto/timetable-engine

# Gitの初期化
git init
git add .
git commit -m "時間割生成アプリの初期バージョン"

# GitHubと連携（事前にgithub.comで空のリポジトリを作成）
git remote add origin https://github.com/YOUR_USERNAME/timetable-app.git
git branch -M main
git push -u origin main
```

💡 **GitHub初心者？**: https://github.com で無料アカウントを作成 → 「New repository」で空のリポジトリ作成

### ステップ2️⃣: Streamlit Cloudに接続（3分）

1. **https://streamlit.io/cloud** にアクセス
2. **「Continue with GitHub」** でログイン
3. **「New app」** をクリック
4. 以下を入力:
   - Repository: `YOUR_USERNAME/timetable-app`
   - Branch: `main`
   - Main file path: `app.py`
5. **「Deploy!」** をクリック

### ステップ3️⃣: アプリにアクセス（2分）

デプロイが完了すると、URLが発行されます:
```
https://your-app-name.streamlit.app
```

このURLを共有すれば、誰でもアプリを使えます！📱💻

## 🎯 完了チェックリスト

デプロイ前の確認:

- [ ] GitHubアカウントを持っている
- [ ] 空のGitHubリポジトリを作成した
- [ ] コードをGitHubにプッシュした
- [ ] Streamlit Cloudアカウントを作成した
- [ ] アプリをデプロイした
- [ ] ブラウザでアプリが開ける ✅

## 🆓 完全無料

- **GitHub**: 無料プラン
- **Streamlit Cloud**: 無料で1つのアプリをホスティング
- **ドメイン**: `.streamlit.app` が自動で割り当て

## ❓ よくある質問

### Q: プログラミング知識がなくても大丈夫？

A: はい！上記の手順をコピー＆ペーストするだけでOKです。

### Q: 何人まで使える？

A: 制限なし。ただし、無料プランでは同時アクセスが多いと遅くなる場合があります。

### Q: カスタムドメインは使える？

A: Streamlit Cloudの有料プランで可能です。

### Q: エラーが出た場合は？

A: [DEPLOYMENT.md](DEPLOYMENT.md) の「トラブルシューティング」セクションを参照してください。

## 📚 詳細ガイド

完全なデプロイ手順とトラブルシューティングは:
→ **[DEPLOYMENT.md](DEPLOYMENT.md)**

アプリの使い方は:
→ **[STREAMLIT_GUIDE.md](STREAMLIT_GUIDE.md)**

## 🎉 デプロイ成功したら

1. URLを同僚や学校関係者に共有
2. サンプルデータでデモ
3. フィードバックを集める
4. 必要に応じて機能を追加

---

**問題が発生した場合**: GitHubでIssueを作成してください 🙋‍♂️
