import asyncio

from agents import Agent, FileSearchTool, Runner, trace


async def main():
    agent = Agent(
        name="File searcher",
        instructions="You are a helpful agent.",
        tools=[
            FileSearchTool(
                max_num_results=3,
                vector_store_ids=["vs_67d5c24064048191b6ede11b35be101f"],
                include_search_results=True,
            )
        ],
    )

    with trace("File search example"):
        result = await Runner.run(
            agent, "Be concise, and tell me 1 sentence about Arrakis I might not know."
        )
        print(result.final_output)
        """
        Arrakis, the desert planet in Frank Herbert's "Dune," was inspired by the scarcity of water
        as a metaphor for oil and other finite resources.
        """

        print("\n".join([str(out) for out in result.new_items]))
        """
        {"id":"...", "queries":["Arrakis"], "results":[...]}
        """


if __name__ == "__main__":
    asyncio.run(main())
