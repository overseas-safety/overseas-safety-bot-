# Overseas Safety Alert Bot

米国務省などの海外渡航アラート（RSS）を自動取得し、DeepLで日本語へ翻訳して、**Bluesky**へ自動投稿するPythonスクリプトです。GitHub Actionsを利用することで、インフラ運用コストを無料（$0）に抑えて完全自動稼働させることができます。

## 初期設定（ローカルでの実行テスト）

Python 3.10+での動作を想定しています。

1. **必要なライブラリのインストール**
   ```bash
   pip install -r requirements.txt
   ```

2. **API情報の取得と設定**
   - [DeepL API (Free)](https://www.deepl.com/pro-api)
   - **Bluesky App Password**: Blueskyのスマホアプリ（またはWeb版）を開き、「設定」>「高度な設定」>「アプリパスワード（App Passwords）」から「Add App Password」を押して専用パスワードを発行します。
   
   リポジトリ内にある `.env.example` をコピーして `.env` を作成し、自身の情報を入力します。
   - `BLUESKY_HANDLE`: あなたのBlueskyのID（例: `safetyinfo.bsky.social`）
   - `BLUESKY_PASSWORD`: 先ほど発行した専用パスワード
   - `DEEPL_AUTH_KEY`: 取得済みのDeepL APIキー

3. **ローカルでのテスト実行 (Dry Run)**
   ```bash
   python main.py
   ```

## 自動稼働の設定（GitHub Actions）

1. 新しくGitHubリポジトリを作成し、このディレクトリの中身を全てプッシュします。
2. GitHubリポジトリの `Settings` > `Secrets and variables` > `Actions` にアクセスします。
3. 以下の名前で **New repository secret** を作成し、それぞれ値を登録します。
   - `BLUESKY_HANDLE`
   - `BLUESKY_PASSWORD`
   - `DEEPL_AUTH_KEY`
4. 設定が完了すると、`.github/workflows/bot.yml` に定義されたスケジュール（初期設定：4時間おき）に従って完全自動でボットが巡回し、Blueskyに自動投稿します。

## 💡 マネタイズ（1日10ドルの自動収益）への道

BlueskyはXに代わるプラットフォームとして急速に伸びており、アフィリエイトの投稿も公式に許可されています。

1. **自動リプライアフィリエイト戦略（おすすめ）**
   - リアルタイム性の高い安全情報（特に治安悪化や通信障害のニュース）は拡散されやすい傾向があります。
   - こうした特定のアラート投稿に対し、「手動で」または「プログラムを拡張して自動で」、その投稿への**リプライとしてアフィリエイトリンクを繋げる**手法が有効です。
   - おすすめの商材: 海外用VPNサービスの登録、海外eSIMの手配、海外旅行保険の比較サイトなど（A8.net や もしもアフィリエイト等で取得可能）
2. **専門アカウントとしての成長**
   - スパム的な売り込みではなく、「有益な安全速報」という軸をブレさせずに運用を続ければ、旅行・出張層のフォロワーが確実に増えます。成長後にはPR案件を受けたり、他媒体への送客ハブとして機能します。
