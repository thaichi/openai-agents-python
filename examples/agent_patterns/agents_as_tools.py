import asyncio

from agents import Agent, ItemHelpers, MessageOutputItem, Runner, trace

"""
このサンプルは「エージェントをツールとして使用する」パターンを示しています。
フロントラインエージェントがユーザーメッセージを受け取り、どのエージェントをツールとして
呼び出すかを選択します。この例では、複数の翻訳エージェントから選択します。
"""

# スペイン語に翻訳するエージェント
spanish_agent = Agent(
    name="spanish_agent",
    instructions="You translate the user's message to Spanish",
    handoff_description="An english to spanish translator",
)

# フランス語に翻訳するエージェント
french_agent = Agent(
    name="french_agent",
    instructions="You translate the user's message to French",
    handoff_description="An english to french translator",
)

# イタリア語に翻訳するエージェント
italian_agent = Agent(
    name="italian_agent",
    instructions="You translate the user's message to Italian",
    handoff_description="An english to italian translator",
)

# オーケストレーターエージェント（他のエージェントを呼び出す司令塔）
orchestrator_agent = Agent(
    name="orchestrator_agent",
    instructions=(
        "You are a translation agent. You use the tools given to you to translate."
        "If asked for multiple translations, you call the relevant tools in order."
        "You never translate on your own, you always use the provided tools."
    ),
    # 他のエージェントをツールとして登録
    tools=[
        spanish_agent.as_tool(
            tool_name="translate_to_spanish",
            tool_description="Translate the user's message to Spanish",
        ),
        french_agent.as_tool(
            tool_name="translate_to_french",
            tool_description="Translate the user's message to French",
        ),
        italian_agent.as_tool(
            tool_name="translate_to_italian",
            tool_description="Translate the user's message to Italian",
        ),
    ],
)

# 翻訳結果を統合するエージェント
synthesizer_agent = Agent(
    name="synthesizer_agent",
    instructions="You inspect translations, correct them if needed, and produce a final concatenated response.",
)


async def main():
    # ユーザーからの入力を受け取る
    msg = input("Hi! What would you like translated, and to which languages? ")

    # オーケストレーション全体を単一のトレースで実行
    with trace("Orchestrator evaluator"):
        # オーケストレーターエージェントを実行（適切な翻訳ツールを選択して実行する）
        orchestrator_result = await Runner.run(orchestrator_agent, msg)

        # 翻訳結果を表示
        for item in orchestrator_result.new_items:
            if isinstance(item, MessageOutputItem):
                text = ItemHelpers.text_message_output(item)
                if text:
                    print(f"  - Translation step: {text}")

        # 翻訳結果を統合エージェントに渡して最終結果を生成
        synthesizer_result = await Runner.run(
            synthesizer_agent, orchestrator_result.to_input_list()
        )

    # 最終結果を表示
    print(f"\n\nFinal response:\n{synthesizer_result.final_output}")


# スクリプトが直接実行された場合にmain関数を実行
if __name__ == "__main__":
    asyncio.run(main())
