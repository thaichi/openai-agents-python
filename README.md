# OpenAI Agents SDK

OpenAI Agents SDKは、マルチエージェントワークフローを構築するための軽量かつ強力なフレームワークです。

<img src="https://cdn.openai.com/API/docs/images/orchestration.png" alt="Agents Tracing UIの画像" style="max-height: 803px;">

### 主要概念:

1. [**エージェント**](https://openai.github.io/openai-agents-python/agents): 指示、ツール、ガードレール、ハンドオフで構成されたLLM
2. [**ハンドオフ**](https://openai.github.io/openai-agents-python/handoffs/): 特定のタスクのために他のエージェントに制御を移す機能
3. [**ガードレール**](https://openai.github.io/openai-agents-python/guardrails/): 入出力の検証のための設定可能な安全性チェック
4. [**トレーシング**](https://openai.github.io/openai-agents-python/tracing/): エージェントの実行を追跡し、ワークフローの表示、デバッグ、最適化を可能にする機能

[examples](examples)ディレクトリでSDKの実際の動作を確認し、詳細については[ドキュメント](https://openai.github.io/openai-agents-python/)をご覧ください。

特筆すべきは、このSDKはOpenAI Chat Completions APIフォーマットをサポートする任意のモデルプロバイダーと[互換性がある](https://openai.github.io/openai-agents-python/models/)ことです。

## WSL環境でのセットアップ

WSL（Windows Subsystem for Linux）環境でOpenAI Agents SDKを使用するための手順は以下の通りです：

1. WSLがインストールされていない場合は、インストールします

```bash
# 管理者権限でPowerShellを開き、以下のコマンドを実行
wsl --install
```

2. WSLを起動し、必要なパッケージをインストールします

```bash
# WSLを起動後、以下のコマンドでパッケージを更新
sudo apt update && sudo apt upgrade -y

# Pythonと必要なツールをインストール
sudo apt install python3 python3-pip python3-venv -y
```

3. プロジェクトディレクトリを作成し、移動します

```bash
mkdir openai-agents-project
cd openai-agents-project
```

## 使い方

1. Python環境をセットアップ

```bash
python3 -m venv env
source env/bin/activate
```

2. Agents SDKをインストール

```bash
pip install openai-agents
```

## Hello worldの例

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="You are a helpful assistant")

result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
print(result.final_output)

# コードの中のコード、
# 自分自身を呼び出す関数、
# 無限ループの舞。
```

(_実行する際は、`OPENAI_API_KEY`環境変数を設定してください_)

(_Jupyterノートブックユーザーは[hello_world_jupyter.py](examples/basic/hello_world_jupyter.py)を参照してください_)

## ハンドオフの例

```python
from agents import Agent, Runner
import asyncio

spanish_agent = Agent(
    name="Spanish agent",
    instructions="You only speak Spanish.",
)

english_agent = Agent(
    name="English agent",
    instructions="You only speak English",
)

triage_agent = Agent(
    name="Triage agent",
    instructions="Handoff to the appropriate agent based on the language of the request.",
    handoffs=[spanish_agent, english_agent],
)


async def main():
    result = await Runner.run(triage_agent, input="Hola, ¿cómo estás?")
    print(result.final_output)
    # ¡Hola! Estoy bien, gracias por preguntar. ¿Y tú, cómo estás?


if __name__ == "__main__":
    asyncio.run(main())
```

## 関数の例

```python
import asyncio

from agents import Agent, Runner, function_tool


@function_tool
def get_weather(city: str) -> str:
    return f"The weather in {city} is sunny."


agent = Agent(
    name="Hello world",
    instructions="You are a helpful agent.",
    tools=[get_weather],
)


async def main():
    result = await Runner.run(agent, input="What's the weather in Tokyo?")
    print(result.final_output)
    # 東京の天気は晴れです。


if __name__ == "__main__":
    asyncio.run(main())
```

## エージェントループ

`Runner.run()`を呼び出すと、最終出力が得られるまでループが実行されます。

1. モデルと設定、メッセージ履歴を使用してLLMを呼び出します。
2. LLMはツール呼び出しを含む可能性のある応答を返します。
3. 応答に最終出力がある場合（詳細は後述）、それを返してループを終了します。
4. 応答にハンドオフがある場合、エージェントを新しいエージェントに設定し、ステップ1に戻ります。
5. ツール呼び出しがある場合はそれを処理し、ツール応答メッセージを追加します。その後、ステップ1に戻ります。

ループの実行回数を制限するための`max_turns`パラメータがあります。

### 最終出力

最終出力は、エージェントがループで生成する最後のものです。

1. エージェントに`output_type`を設定した場合、LLMがそのタイプのものを返したときが最終出力です。これには[構造化出力](https://platform.openai.com/docs/guides/structured-outputs)を使用します。
2. `output_type`がない場合（つまり、プレーンテキスト応答）、ツール呼び出しやハンドオフのない最初のLLM応答が最終出力と見なされます。

その結果、エージェントループの概念モデルは次のようになります：

1. 現在のエージェントに`output_type`がある場合、エージェントがそのタイプに一致する構造化出力を生成するまでループが実行されます。
2. 現在のエージェントに`output_type`がない場合、現在のエージェントがツール呼び出し/ハンドオフのないメッセージを生成するまでループが実行されます。

## 一般的なエージェントパターン

Agents SDKは非常に柔軟に設計されており、決定論的フロー、反復ループなど、幅広いLLMワークフローをモデル化できます。[`examples/agent_patterns`](examples/agent_patterns)の例を参照してください。

## トレーシング

Agents SDKは自動的にエージェントの実行を追跡し、エージェントの動作を簡単に追跡およびデバッグできるようにします。トレーシングは設計上拡張可能であり、カスタムスパンと、[Logfire](https://logfire.pydantic.dev/docs/integrations/llms/openai/#openai-agents)、[AgentOps](https://docs.agentops.ai/v1/integrations/agentssdk)、[Braintrust](https://braintrust.dev/docs/guides/traces/integrations#openai-agents-sdk)、[Scorecard](https://docs.scorecard.io/docs/documentation/features/tracing#openai-agents-sdk-integration)、[Keywords AI](https://docs.keywordsai.co/integration/development-frameworks/openai-agent)などの様々な外部送信先をサポートしています。トレーシングのカスタマイズや無効化に関する詳細については、[トレーシング](http://openai.github.io/openai-agents-python/tracing)を参照してください。

## 開発（SDK/例を編集する必要がある場合のみ）

0. [`uv`](https://docs.astral.sh/uv/)がインストールされていることを確認してください。

```bash
uv --version
```

1. 依存関係をインストール

```bash
make sync
```

2. （変更後）リント/テスト

```
make tests  # テスト実行
make mypy   # 型チェッカー実行
make lint   # リンター実行
```

## 謝辞

以下のオープンソースコミュニティの優れた成果に感謝します：

-   [Pydantic](https://docs.pydantic.dev/latest/)（データ検証）と[PydanticAI](https://ai.pydantic.dev/)（高度なエージェントフレームワーク）
-   [MkDocs](https://github.com/squidfunk/mkdocs-material)
-   [Griffe](https://github.com/mkdocstrings/griffe)
-   [uv](https://github.com/astral-sh/uv)と[ruff](https://github.com/astral-sh/ruff)

私たちはAgents SDKをオープンソースフレームワークとして継続的に構築し、コミュニティの他のメンバーが私たちのアプローチを拡張できるよう取り組んでいます。
