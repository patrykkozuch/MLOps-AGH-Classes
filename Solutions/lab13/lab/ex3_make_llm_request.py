import asyncio
import json
from openai import OpenAI

from mcp_manager import MCPManager


async def make_llm_request(prompt: str) -> str:
    mcp_servers = {
        "weather_forecast": "http://localhost:8001/mcp",
        "date_time_server": "http://localhost:8002/mcp",
    }

    vllm_client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")

    async with MCPManager(mcp_servers) as mcp:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. Use tools if you need to."
                    # "If the task is impossible based on your knowledge and tools, "
                    # "return that information."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        # guard: loop limit, we break as soon as we get an answer
        for _ in range(10):
            response = vllm_client.chat.completions.create(
                model="",
                messages=messages,
                tools=mcp.tools,
                tool_choice="auto",
                max_completion_tokens=1000,
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            )

            response = response.choices[0].message
            if not response.tool_calls:
                return response.content

            messages.append(response)
            for tool_call in response.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                print(f"Executing tool '{func_name}'")
                func_result = await mcp.call_tool(func_name, func_args)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": func_name,
                        "content": str(func_result),
                    }
                )


if __name__ == "__main__":
    prompt = "What will be weather in Birmingham in two weeks?"
    response = asyncio.run(make_llm_request(prompt))
    print("Response:\n", response)

    print()

    prompt = "What will be weather in Warsaw the day after tomorrow?"
    response = asyncio.run(make_llm_request(prompt))
    print("Response:\n", response)

    print()

    prompt = "What will be weather in New York in two months?"
    response = asyncio.run(make_llm_request(prompt))
    print("Response:\n", response)
