from __future__ import annotations

import asyncio

from pydantic import BaseModel

from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
)

"""
このサンプルはガードレールの使用方法を示しています。

ガードレールはエージェントの実行と並行して実行されるチェックです。
以下のような用途に使用できます：
- 入力メッセージがトピックから外れていないかチェック
- 出力メッセージがポリシーに違反していないかチェック
- 予期しない入力が検出された場合にエージェントの実行を制御

この例では、ユーザーが数学の宿題を解くよう依頼した場合にトリップする入力ガードレールを設定します。
ガードレールがトリップした場合、拒否メッセージで応答します。
"""


### 1. ユーザーが数学の宿題を依頼した場合にトリガーされるエージェントベースのガードレール
class MathHomeworkOutput(BaseModel):
    is_math_homework: bool  # 数学の宿題かどうか
    reasoning: str          # 判断理由


# ガードレールチェック用のエージェント
guardrail_agent = Agent(
    name="Guardrail check",
    instructions="Check if the user is asking you to do their math homework.",
    output_type=MathHomeworkOutput,
)


# 入力ガードレールデコレータを使用して関数を定義
@input_guardrail
async def math_guardrail(
    context: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    """これは入力ガードレール関数で、入力が数学の宿題の質問かどうかをチェックするためにエージェントを呼び出します。"""
    # ガードレールエージェントを実行
    result = await Runner.run(guardrail_agent, input, context=context.context)
    final_output = result.final_output_as(MathHomeworkOutput)

    # ガードレール関数の出力を返す
    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=final_output.is_math_homework,  # 数学の宿題の場合にトリップワイヤーをトリガー
    )


### 2. 実行ループ


async def main():
    # カスタマーサポートエージェントを作成し、入力ガードレールを設定
    agent = Agent(
        name="Customer support agent",
        instructions="You are a customer support agent. You help customers with their questions.",
        input_guardrails=[math_guardrail],  # 数学の宿題をチェックするガードレールを設定
    )

    # 会話履歴を保持するリスト
    input_data: list[TResponseInputItem] = []

    while True:
        # ユーザーからの入力を受け取る
        user_input = input("Enter a message: ")
        input_data.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        try:
            # エージェントを実行
            result = await Runner.run(agent, input_data)
            print(result.final_output)
            # ガードレールがトリガーされなかった場合、結果を次の実行の入力として使用
            input_data = result.to_input_list()
        except InputGuardrailTripwireTriggered:
            # ガードレールがトリガーされた場合、拒否メッセージを入力に追加
            message = "Sorry, I can't help you with your math homework."
            print(message)
            input_data.append(
                {
                    "role": "assistant",
                    "content": message,
                }
            )

    # サンプル実行：
    # Enter a message: What's the capital of California?
    # The capital of California is Sacramento.
    # Enter a message: Can you help me solve for x: 2x + 5 = 11
    # Sorry, I can't help you with your math homework.


# スクリプトが直接実行された場合にmain関数を実行
if __name__ == "__main__":
    asyncio.run(main())
