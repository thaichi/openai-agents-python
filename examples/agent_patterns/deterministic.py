import asyncio

from pydantic import BaseModel

from agents import Agent, Runner, trace

"""
このサンプルは決定論的フロー（順序が決まったステップ処理）を示しています。各ステップは異なるエージェントによって実行されます。
1. 最初のエージェントがストーリーのアウトラインを生成
2. そのアウトラインを2番目のエージェントに渡す
3. 2番目のエージェントはアウトラインの品質とSFストーリーかどうかを判断
4. アウトラインの品質が低いか、SFストーリーでない場合はここで処理を停止
5. アウトラインの品質が高く、SFストーリーである場合は3番目のエージェントにアウトラインを渡す
6. 3番目のエージェントがストーリーを書く
"""

# ストーリーのアウトラインを生成するエージェント
story_outline_agent = Agent(
    name="story_outline_agent",
    instructions="Generate a very short story outline based on the user's input.",
)


# アウトラインチェッカーの出力タイプを定義するクラス
class OutlineCheckerOutput(BaseModel):
    good_quality: bool  # アウトラインの品質が良いかどうか
    is_scifi: bool      # SFストーリーかどうか


# アウトラインの品質とジャンルをチェックするエージェント
outline_checker_agent = Agent(
    name="outline_checker_agent",
    instructions="Read the given story outline, and judge the quality. Also, determine if it is a scifi story.",
    output_type=OutlineCheckerOutput,  # 出力タイプを指定
)

# 実際にストーリーを書くエージェント
story_agent = Agent(
    name="story_agent",
    instructions="Write a short story based on the given outline.",
    output_type=str,  # 出力タイプは文字列
)


async def main():
    # ユーザーからの入力を受け取る
    input_prompt = input("What kind of story do you want? ")

    # ワークフロー全体を単一のトレースで実行（モニタリングのため）
    with trace("Deterministic story flow"):
        # 1. アウトラインを生成
        outline_result = await Runner.run(
            story_outline_agent,
            input_prompt,
        )
        print("Outline generated")

        # 2. アウトラインをチェック
        outline_checker_result = await Runner.run(
            outline_checker_agent,
            outline_result.final_output,
        )

        # 3. アウトラインの品質が低いかSFストーリーでない場合は処理を停止するゲートを追加
        assert isinstance(outline_checker_result.final_output, OutlineCheckerOutput)
        if not outline_checker_result.final_output.good_quality:
            print("Outline is not good quality, so we stop here.")
            exit(0)

        if not outline_checker_result.final_output.is_scifi:
            print("Outline is not a scifi story, so we stop here.")
            exit(0)

        print("Outline is good quality and a scifi story, so we continue to write the story.")

        # 4. ストーリーを書く
        story_result = await Runner.run(
            story_agent,
            outline_result.final_output,
        )
        print(f"Story: {story_result.final_output}")


# スクリプトが直接実行された場合にmain関数を実行
if __name__ == "__main__":
    asyncio.run(main())
