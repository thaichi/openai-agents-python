from __future__ import annotations

import asyncio
import json

from pydantic import BaseModel, Field

from agents import (
    Agent,
    GuardrailFunctionOutput,
    OutputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    output_guardrail,
)

"""
このサンプルは出力ガードレールの使用方法を示しています。

出力ガードレールはエージェントの最終出力に対して実行されるチェックです。
以下のような用途に使用できます：
- 出力に機密データが含まれていないかチェック
- 出力がユーザーのメッセージに対する有効な応答かどうかチェック

この例では、エージェントの応答に電話番号が含まれているかどうかをチェックする
（わかりやすくするための）例を使用します。
"""


# エージェントの出力タイプ
class MessageOutput(BaseModel):
    reasoning: str = Field(description="Thoughts on how to respond to the user's message")  # ユーザーメッセージへの応答方法に関する思考
    response: str = Field(description="The response to the user's message")  # ユーザーへの応答
    user_name: str | None = Field(description="The name of the user who sent the message, if known")  # メッセージを送信したユーザーの名前（わかる場合）


# 出力ガードレールデコレータを使用して関数を定義
@output_guardrail
async def sensitive_data_check(
    context: RunContextWrapper, agent: Agent, output: MessageOutput
) -> GuardrailFunctionOutput:
    # 応答とreasoningに電話番号（この例では「650」）が含まれているかチェック
    phone_number_in_response = "650" in output.response
    phone_number_in_reasoning = "650" in output.reasoning

    # ガードレール関数の出力を返す
    return GuardrailFunctionOutput(
        output_info={
            "phone_number_in_response": phone_number_in_response,
            "phone_number_in_reasoning": phone_number_in_reasoning,
        },
        # 応答またはreasoningに電話番号が含まれている場合にトリップワイヤーをトリガー
        tripwire_triggered=phone_number_in_response or phone_number_in_reasoning,
    )


# 出力ガードレールを設定したエージェント
agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant.",
    output_type=MessageOutput,
    output_guardrails=[sensitive_data_check],  # 機密データチェックガードレールを設定
)


async def main():
    # これは問題なく通過するはず
    await Runner.run(agent, "What's the capital of California?")
    print("First message passed")

    # これはガードレールをトリップするはず
    try:
        result = await Runner.run(
            agent, "My phone number is 650-123-4567. Where do you think I live?"
        )
        # ガードレールがトリップしなかった場合（予期しない結果）
        print(
            f"Guardrail didn't trip - this is unexpected. Output: {json.dumps(result.final_output.model_dump(), indent=2)}"
        )

    except OutputGuardrailTripwireTriggered as e:
        # ガードレールがトリップした場合
        print(f"Guardrail tripped. Info: {e.guardrail_result.output.output_info}")


# スクリプトが直接実行された場合にmain関数を実行
if __name__ == "__main__":
    asyncio.run(main())
