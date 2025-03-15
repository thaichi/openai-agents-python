import asyncio

from agents import Agent, ItemHelpers, Runner, trace

"""
このサンプルは並列処理パターンを示しています。エージェントを3回並列に実行し、
最良の結果を選択します。これにより、より質の高い出力を得ることができます。
"""

# 日本語に翻訳するエージェント
japanese_agent = Agent(
    name="japanese_agent",
    instructions="You translate the user's message to Japanese",
)

# 最良の翻訳を選ぶエージェント
translation_picker = Agent(
    name="translation_picker",
    instructions="You pick the best Japanese translation from the given options.",
)


async def main():
    # ユーザーからの入力を受け取る
    msg = input("Hi! Enter a message, and we'll translate it to Japanese.\n\n")

    # ワークフロー全体を単一のトレースで実行
    with trace("Parallel translation"):
        # 同じエージェントを3回並列に実行（asyncio.gatherを使用）
        res_1, res_2, res_3 = await asyncio.gather(
            Runner.run(
                japanese_agent,
                msg,
            ),
            Runner.run(
                japanese_agent,
                msg,
            ),
            Runner.run(
                japanese_agent,
                msg,
            ),
        )

        # 3つの翻訳結果を取得
        outputs = [
            ItemHelpers.text_message_outputs(res_1.new_items),
            ItemHelpers.text_message_outputs(res_2.new_items),
            ItemHelpers.text_message_outputs(res_3.new_items),
        ]

        # 翻訳結果を結合して表示
        translations = "\n\n".join(outputs)
        print(f"\n\nTranslations:\n\n{translations}")

        # 翻訳選択エージェントを実行して最良の翻訳を選ぶ
        best_translation = await Runner.run(
            translation_picker,
            f"Input: {msg}\n\nTranslations:\n{translations}",
        )

    print("\n\n-----")

    # 最良の翻訳を表示
    print(f"Best translation: {best_translation.final_output}")


# スクリプトが直接実行された場合にmain関数を実行
if __name__ == "__main__":
    asyncio.run(main())
