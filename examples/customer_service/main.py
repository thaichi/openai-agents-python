from __future__ import annotations as _annotations

import asyncio  # 非同期処理のためのライブラリ
import random  # ランダム値生成のためのライブラリ
import uuid  # 一意のID生成のためのライブラリ

from pydantic import BaseModel  # データバリデーションのためのライブラリ

from agents import (  # OpenAI Agentsライブラリからの各種インポート
    Agent,  # エージェントクラス
    HandoffOutputItem,  # エージェント間の引き継ぎ出力アイテム
    ItemHelpers,  # 出力アイテムを扱うためのヘルパー
    MessageOutputItem,  # メッセージ出力アイテム
    RunContextWrapper,  # 実行コンテキストのラッパー
    Runner,  # エージェント実行ランナー
    ToolCallItem,  # ツール呼び出しアイテム
    ToolCallOutputItem,  # ツール呼び出し出力アイテム
    TResponseInputItem,  # 入力アイテムの型
    function_tool,  # 関数ツールデコレータ
    handoff,  # エージェント間の引き継ぎ関数
    trace,  # トレース機能
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX  # 推奨プロンプトプレフィックス

### コンテキスト（CONTEXT）


class AirlineAgentContext(BaseModel):
    """
    航空会社エージェントのコンテキストクラス
    会話中に保持される顧客情報を管理する
    """
    passenger_name: str | None = None  # 乗客名
    confirmation_number: str | None = None  # 予約確認番号
    seat_number: str | None = None  # 座席番号
    flight_number: str | None = None  # フライト番号


### ツール（TOOLS）


@function_tool(
    name_override="faq_lookup_tool", description_override="Lookup frequently asked questions."
)
async def faq_lookup_tool(question: str) -> str:
    """
    よくある質問（FAQ）を検索するツール
    質問文字列を受け取り、関連する回答を返す
    """
    if "bag" in question or "baggage" in question:
        return (
            "You are allowed to bring one bag on the plane. "
            "It must be under 50 pounds and 22 inches x 14 inches x 9 inches."
        )
    elif "seats" in question or "plane" in question:
        return (
            "There are 120 seats on the plane. "
            "There are 22 business class seats and 98 economy seats. "
            "Exit rows are rows 4 and 16. "
            "Rows 5-8 are Economy Plus, with extra legroom. "
        )
    elif "wifi" in question:
        return "We have free wifi on the plane, join Airline-Wifi"
    return "I'm sorry, I don't know the answer to that question."


@function_tool
async def update_seat(
    context: RunContextWrapper[AirlineAgentContext], confirmation_number: str, new_seat: str
) -> str:
    """
    指定された予約確認番号の座席を更新するツール

    Args:
        confirmation_number: フライトの予約確認番号
        new_seat: 更新先の新しい座席番号
    """
    # 顧客の入力に基づいてコンテキストを更新
    context.context.confirmation_number = confirmation_number
    context.context.seat_number = new_seat
    # 引き継ぎによってフライト番号が設定されていることを確認
    assert context.context.flight_number is not None, "Flight number is required"
    return f"Updated seat to {new_seat} for confirmation number {confirmation_number}"


### フック（HOOKS）


async def on_seat_booking_handoff(context: RunContextWrapper[AirlineAgentContext]) -> None:
    """
    座席予約エージェントへの引き継ぎ時に実行されるフック関数
    ランダムなフライト番号を生成してコンテキストに設定する
    """
    flight_number = f"FLT-{random.randint(100, 999)}"
    context.context.flight_number = flight_number


### エージェント（AGENTS）

# FAQエージェントの定義
faq_agent = Agent[AirlineAgentContext](
    name="FAQ Agent",  # エージェント名
    handoff_description="A helpful agent that can answer questions about the airline.",  # 引き継ぎ時の説明
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are an FAQ agent. If you are speaking to a customer, you probably were transferred to from the triage agent.
    Use the following routine to support the customer.
    # Routine
    1. Identify the last question asked by the customer.
    2. Use the faq lookup tool to answer the question. Do not rely on your own knowledge.
    3. If you cannot answer the question, transfer back to the triage agent.""",  # エージェントの指示
    tools=[faq_lookup_tool],  # 使用可能なツール
)

# 座席予約エージェントの定義
seat_booking_agent = Agent[AirlineAgentContext](
    name="Seat Booking Agent",  # エージェント名
    handoff_description="A helpful agent that can update a seat on a flight.",  # 引き継ぎ時の説明
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a seat booking agent. If you are speaking to a customer, you probably were transferred to from the triage agent.
    Use the following routine to support the customer.
    # Routine
    1. Ask for their confirmation number.
    2. Ask the customer what their desired seat number is.
    3. Use the update seat tool to update the seat on the flight.
    If the customer asks a question that is not related to the routine, transfer back to the triage agent. """,  # エージェントの指示
    tools=[update_seat],  # 使用可能なツール
)

# トリアージエージェントの定義
triage_agent = Agent[AirlineAgentContext](
    name="Triage Agent",  # エージェント名
    handoff_description="A triage agent that can delegate a customer's request to the appropriate agent.",  # 引き継ぎ時の説明
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX} "
        "You are a helpful triaging agent. You can use your tools to delegate questions to other appropriate agents."
    ),  # エージェントの指示
    handoffs=[  # 引き継ぎ可能なエージェントリスト
        faq_agent,  # FAQエージェント
        handoff(agent=seat_booking_agent, on_handoff=on_seat_booking_handoff),  # 座席予約エージェント（フック付き）
    ],
)

# 各エージェントにトリアージエージェントへの引き継ぎを追加
faq_agent.handoffs.append(triage_agent)
seat_booking_agent.handoffs.append(triage_agent)


### 実行（RUN）


async def main():
    """
    メイン実行関数
    対話型のコマンドラインインターフェースを提供し、ユーザー入力に基づいてエージェントを実行する
    """
    current_agent: Agent[AirlineAgentContext] = triage_agent  # 現在のエージェント（初期値はトリアージエージェント）
    input_items: list[TResponseInputItem] = []  # 入力アイテムのリスト
    context = AirlineAgentContext()  # エージェントコンテキスト

    # 通常、ユーザーからの各入力はアプリへのAPIリクエストであり、リクエストをtrace()でラップできます
    # ここでは、会話IDとしてランダムなUUIDを使用します
    conversation_id = uuid.uuid4().hex[:16]

    while True:  # 無限ループで対話を続ける
        user_input = input("Enter your message: ")  # ユーザー入力を取得
        with trace("Customer service", group_id=conversation_id):  # トレース機能を使用して会話をグループ化
            input_items.append({"content": user_input, "role": "user"})  # ユーザー入力をアイテムリストに追加
            result = await Runner.run(current_agent, input_items, context=context)  # エージェントを実行

            # 新しい出力アイテムを処理
            for new_item in result.new_items:
                agent_name = new_item.agent.name
                if isinstance(new_item, MessageOutputItem):  # メッセージ出力の場合
                    print(f"{agent_name}: {ItemHelpers.text_message_output(new_item)}")
                elif isinstance(new_item, HandoffOutputItem):  # エージェント間の引き継ぎの場合
                    print(
                        f"Handed off from {new_item.source_agent.name} to {new_item.target_agent.name}"
                    )
                elif isinstance(new_item, ToolCallItem):  # ツール呼び出しの場合
                    print(f"{agent_name}: Calling a tool")
                elif isinstance(new_item, ToolCallOutputItem):  # ツール呼び出し出力の場合
                    print(f"{agent_name}: Tool call output: {new_item.output}")
                else:  # その他のアイテムの場合
                    print(f"{agent_name}: Skipping item: {new_item.__class__.__name__}")
            input_items = result.to_input_list()  # 次の入力用にアイテムリストを更新
            current_agent = result.last_agent  # 現在のエージェントを更新


if __name__ == "__main__":
    asyncio.run(main())  # メイン関数を非同期で実行
