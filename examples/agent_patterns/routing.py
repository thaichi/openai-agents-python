import asyncio
import uuid

from openai.types.responses import ResponseContentPartDoneEvent, ResponseTextDeltaEvent

from agents import Agent, RawResponsesStreamEvent, Runner, TResponseInputItem, trace

"""
このサンプルはハンドオフ/ルーティングパターンを示しています。トリアージエージェントが最初のメッセージを
受け取り、リクエストの言語に基づいて適切なエージェントにハンドオフします。応答はユーザーに
ストリーミングされます。
"""

# フランス語を話すエージェント
french_agent = Agent(
    name="french_agent",
    instructions="You only speak French",
)

# スペイン語を話すエージェント
spanish_agent = Agent(
    name="spanish_agent",
    instructions="You only speak Spanish",
)

# 英語を話すエージェント
english_agent = Agent(
    name="english_agent",
    instructions="You only speak English",
)

# トリアージエージェント（言語に基づいて適切なエージェントに振り分ける）
triage_agent = Agent(
    name="triage_agent",
    instructions="Handoff to the appropriate agent based on the language of the request.",
    handoffs=[french_agent, spanish_agent, english_agent],  # ハンドオフ先のエージェントリスト
)


async def main():
    # この会話のIDを作成（各トレースをリンクするため）
    conversation_id = str(uuid.uuid4().hex[:16])

    # ユーザーからの入力を受け取る
    msg = input("Hi! We speak French, Spanish and English. How can I help? ")
    agent = triage_agent  # 最初はトリアージエージェントを使用
    inputs: list[TResponseInputItem] = [{"content": msg, "role": "user"}]

    while True:
        # 各会話ターンは単一のトレース。通常、ユーザーからの各入力はアプリへのAPIリクエストになり、
        # リクエストをtrace()でラップできます
        with trace("Routing example", group_id=conversation_id):
            # ストリーミングモードでエージェントを実行
            result = Runner.run_streamed(
                agent,
                input=inputs,
            )
            # イベントをストリーミングして表示
            async for event in result.stream_events():
                if not isinstance(event, RawResponsesStreamEvent):
                    continue
                data = event.data
                if isinstance(data, ResponseTextDeltaEvent):
                    # テキストの一部を受信したら表示
                    print(data.delta, end="", flush=True)
                elif isinstance(data, ResponseContentPartDoneEvent):
                    # コンテンツパートが完了したら改行
                    print("\n")

        # 次の入力用に結果を保存
        inputs = result.to_input_list()
        print("\n")

        # ユーザーからの次のメッセージを受け取る
        user_msg = input("Enter a message: ")
        inputs.append({"content": user_msg, "role": "user"})
        # 現在のエージェントを使用（ハンドオフが行われた場合は新しいエージェント）
        agent = result.current_agent


# スクリプトが直接実行された場合にmain関数を実行
if __name__ == "__main__":
    asyncio.run(main())
