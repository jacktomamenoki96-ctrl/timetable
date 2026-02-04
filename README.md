# 時間割自動生成システム 📅

公立高校の時間割を自動生成するWebアプリケーション。Google OR-Toolsを使用した制約充足問題（CSP）ソルバーにより、教員・教室・クラスの競合を避けつつ、選択科目などの複雑な制約にも対応します。

## ✨ 主な機能

- 📂 **CSVファイルで簡単入力**: 教員、教室、クラス、授業データをアップロード
- 🚀 **自動時間割生成**: ワンクリックで最適な時間割を作成
- 📊 **見やすい表示**: 全体/クラス別/教員別のタブ切り替え
- 💾 **Excelエクスポート**: 生成した時間割をダウンロード
- ⚙️ **柔軟な設定**: 複数のソルバーから選択可能

## 🎯 対応している制約

### ハード制約（必須）
- ✅ 教員の同時担当禁止
- ✅ 教室の同時使用禁止
- ✅ クラスの同時受講禁止
- ✅ 教室タイプの一致（理科室、体育館など）
- ✅ 教員の担当可能時間
- ✅ 選択科目の同時開講（synchronization_id）

## 🚀 クイックスタート

### ローカルで実行

```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# アプリの起動
streamlit run app.py
```

ブラウザで `http://localhost:8501` が自動的に開きます。

### サンプルデータで試す

`sample_data/` フォルダ内の4つのCSVファイルをアップロードしてお試しください:
- teachers.csv (8名の教員)
- rooms.csv (11の教室)
- classes.csv (3クラス)
- lessons.csv (24科目、75コマ)

## 📁 プロジェクト構成

```
timetable-engine/
├── app.py                 # Streamlit Webアプリ
├── models.py              # データモデル
├── constraints.py         # 制約検証ロジック
├── solver.py              # OR-Toolsソルバー
├── backtrack_solver.py    # バックトラックソルバー
├── utils.py               # ユーティリティ関数
├── requirements.txt       # 依存パッケージ
├── sample_data/           # サンプルCSVファイル
│   ├── teachers.csv
│   ├── rooms.csv
│   ├── classes.csv
│   └── lessons.csv
├── STREAMLIT_GUIDE.md     # アプリ使用ガイド
├── DEPLOYMENT.md          # デプロイ手順
└── README.md              # このファイル
```

## 🌐 デプロイ

### Streamlit Cloud (推奨・無料)

1. GitHubにリポジトリを作成
2. https://streamlit.io/cloud にアクセス
3. リポジトリを接続してデプロイ

詳細は [DEPLOYMENT.md](DEPLOYMENT.md) を参照してください。

## 📖 使い方

詳しい使い方は [STREAMLIT_GUIDE.md](STREAMLIT_GUIDE.md) をご覧ください。

### 基本的な流れ

1. **CSVアップロード**: 4種類のデータをアップロード
2. **設定調整**: サイドバーでソルバーや試行回数を調整（オプション）
3. **生成開始**: 「🚀 時間割生成開始」ボタンをクリック
4. **結果確認**: タブで全体/クラス別/教員別を切り替えて確認
5. **ダウンロード**: Excelファイルとしてエクスポート

## 🔧 技術スタック

- **Web Framework**: Streamlit 1.28.0+
- **数値計算**: pandas 2.0.0+
- **最適化**: Google OR-Tools 9.7.0+
- **Excel処理**: openpyxl 3.1.0+
- **言語**: Python 3.11+

## 📊 パフォーマンス

- **小規模** (1〜3クラス): 数秒〜数十秒
- **中規模** (4〜10クラス): 数十秒〜数分
- ソルバー: OR-Tools（高速）またはバックトラック法

## 🤝 コントリビューション

バグ報告や機能提案は、GitHubのIssuesでお願いします。

## 📄 ライセンス

MIT License

## 👨‍💻 開発者

Antigravity AI Assistant

## 🙏 謝辞

- Google OR-Tools: 高性能な制約プログラミングソルバー
- Streamlit: シンプルで強力なWebアプリフレームワーク
