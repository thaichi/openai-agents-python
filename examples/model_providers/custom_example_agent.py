import asyncio
import os

from openai import AsyncOpenAI

from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool, set_tracing_disabled

# 環境変数から設定を取得
BASE_URL = os.getenv("EXAMPLE_BASE_URL") or ""
API_KEY = os.getenv("EXAMPLE_API_KEY") or ""
MODEL_NAME = os.getenv("EXAMPLE_MODEL_NAME") or ""

# 必要な環境変数が設定されているか確認
if not BASE_URL or not API_KEY or not MODEL_NAME:
    raise ValueError(
        "Please set EXAMPLE_BASE_URL, EXAMPLE_API_KEY, EXAMPLE_MODEL_NAME via env var or code."
    )

"""This example uses a custom provider for a specific agent. Steps:
1. Create a custom OpenAI client.
2. Create a `Model` that uses the custom client.
3. Set the `model` on the Agent.

Note that in this example, we disable tracing under the assumption that you don't have an API key
from platform.openai.com. If you do have one, you can either set the `OPENAI_API_KEY` env var
or call set_tracing_export_api_key() to set a tracing specific key.
"""

"""
このサンプルは特定のエージェント用にカスタムプロバイダーを使用する方法を示しています。手順：
1. カスタムOpenAIクライアントを作成します。
2. カスタムクライアントを使用する`Model`を作成します。
3. エージェントに`model`を設定します。

注意：このサンプルでは、platform.openai.comのAPIキーを持っていないという前提でトレースを無効にしています。
APIキーをお持ちの場合は、`OPENAI_API_KEY`環境変数を設定するか、
set_tracing_export_api_key()を呼び出してトレース用の特定のキーを設定できます。
"""

# カスタムOpenAIクライアントを作成
client = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)
# トレースを無効化
set_tracing_disabled(disabled=True)

# 別のアプローチ（これも機能します）：
# PROVIDER = OpenAIProvider(openai_client=client)
# agent = Agent(..., model="some-custom-model")
# Runner.run(agent, ..., run_config=RunConfig(model_provider=PROVIDER))


@function_tool
def get_weather(city: str):
    """天気情報を取得する関数ツール"""
    print(f"[debug] getting weather for {city}")
    return f"The weather in {city} is sunny."


async def main():
    """メイン関数：エージェントを作成して実行します"""
    # このエージェントはカスタムLLMプロバイダーを使用します
    agent = Agent(
        name="Assistant",
        instructions="You only respond in haikus.",  # 俳句形式でのみ応答するよう指示
        model=OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client),
        tools=[get_weather],  # 天気情報取得ツールを追加
    )

    # エージェントを実行して東京の天気を尋ねる
    result = await Runner.run(agent, "What's the weather in Tokyo?")
    # 最終結果を出力
    print(result.final_output)


if __name__ == "__main__":
    # 非同期メイン関数を実行
    asyncio.run(main())
