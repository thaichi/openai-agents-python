# カスタムLLMプロバイダー

このディレクトリの例は、OpenAI以外のLLM（大規模言語モデル）プロバイダーを使用する方法を示しています。これらを実行するには、まずベースURL、APIキー、モデル名を環境変数として設定してください。

```bash
export EXAMPLE_BASE_URL="..."  # LLMプロバイダーのAPIエンドポイント
export EXAMPLE_API_KEY="..."   # APIキー
export EXAMPLE_MODEL_NAME="..." # モデル名
```

その後、以下のように例を実行できます：

```
python examples/model_providers/custom_example_provider.py

Loops within themselves,
Function calls its own being,
Depth without ending.
```

## 3つの実装方法の違い

このディレクトリには、カスタムLLMプロバイダーを使用するための3つの異なるアプローチが含まれています：

### 1. グローバル設定 (`custom_example_global.py`)
- **特徴**: システム全体のデフォルトとしてカスタムプロバイダーを設定
- **適用範囲**: すべてのエージェントに自動的に適用される
- **使用例**: `set_default_openai_client(client)`を使用
- **ユースケース**: アプリケーション全体で一貫して同じプロバイダーを使用したい場合

### 2. エージェント固有設定 (`custom_example_agent.py`)
- **特徴**: 特定のエージェントのみにカスタムプロバイダーを適用
- **適用範囲**: 指定したエージェントのみ
- **使用例**: `Agent(model=OpenAIChatCompletionsModel(...))`
- **ユースケース**: 異なるエージェントに異なるプロバイダーを使用したい場合

### 3. 実行時指定 (`custom_example_provider.py`)
- **特徴**: カスタム`ModelProvider`クラスを作成し、実行時に指定
- **適用範囲**: 特定の`Runner.run()`呼び出しのみ
- **使用例**: `Runner.run(agent, prompt, run_config=RunConfig(model_provider=CUSTOM_PROVIDER))`
- **ユースケース**: 同じエージェントでも実行ごとに異なるプロバイダーを使い分けたい場合

これらの方法は、ユースケースや必要な柔軟性に応じて選択できます。最も柔軟なのは実行時指定の方法で、最も簡単なのはグローバル設定の方法です。
