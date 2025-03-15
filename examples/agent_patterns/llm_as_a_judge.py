from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Literal

from agents import Agent, ItemHelpers, Runner, TResponseInputItem, trace

"""
このサンプルは「LLMを判断者として使用する」パターンを示しています。
最初のエージェントがストーリーのアウトラインを生成し、2番目のエージェントがそのアウトラインを
評価してフィードバックを提供します。判断者が満足するまでこのループを繰り返します。
"""

# ストーリーアウトラインを生成するエージェント
story_outline_generator = Agent(
    name="story_outline_generator",
    instructions=(
        "You generate a very short story outline based on the user's input."
        "If there is any feedback provided, use it to improve the outline."
    ),
)


# 評価フィードバックの構造を定義するデータクラス
@dataclass
class EvaluationFeedback:
    score: Literal["pass", "needs_improvement", "fail"]  # 評価スコア（合格/改善が必要/不合格）
    feedback: str  # フィードバックコメント


# アウトラインを評価するエージェント（判断者）
evaluator = Agent[None](
    name="evaluator",
    instructions=(
        "You evaluate a story outline and decide if it's good enough."
        "If it's not good enough, you provide feedback on what needs to be improved."
        "Never give it a pass on the first try."  # 最初の試行では必ず改善点を見つけるよう指示
    ),
    output_type=EvaluationFeedback,
)


async def main() -> None:
    # ユーザーからの入力を受け取る
    msg = input("What kind of story would you like to hear? ")
    input_items: list[TResponseInputItem] = [{"content": msg, "role": "user"}]

    # 最新のアウトラインを保持する変数
    latest_outline: str | None = None

    # ワークフロー全体を単一のトレースで実行
    with trace("LLM as a judge"):
        # 評価が「合格」になるまでループ
        while True:
            # ストーリーアウトラインを生成
            story_outline_result = await Runner.run(
                story_outline_generator,
                input_items,
            )

            # 次の入力用にアウトラインを保存
            input_items = story_outline_result.to_input_list()
            latest_outline = ItemHelpers.text_message_outputs(story_outline_result.new_items)
            print("Story outline generated")

            # 評価者エージェントを実行してアウトラインを評価
            evaluator_result = await Runner.run(evaluator, input_items)
            result: EvaluationFeedback = evaluator_result.final_output

            # 評価結果を表示
            print(f"Evaluator score: {result.score}")

            # 評価が「合格」ならループを抜ける
            if result.score == "pass":
                print("Story outline is good enough, exiting.")
                break

            print("Re-running with feedback")

            # フィードバックを入力に追加して再実行
            input_items.append({"content": f"Feedback: {result.feedback}", "role": "user"})

    # 最終的なアウトラインを表示
    print(f"Final story outline: {latest_outline}")


# スクリプトが直接実行された場合にmain関数を実行
if __name__ == "__main__":
    asyncio.run(main())
