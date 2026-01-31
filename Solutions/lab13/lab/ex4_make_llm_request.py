import asyncio
import base64
import io
import json
import os
import uuid

from openai import OpenAI

from mcp_manager import MCPManager


async def make_llm_request(prompt: str) -> str:
    mcp_servers = {
        "plot_creator": "http://localhost:8001/mcp",
    }

    vllm_client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")

    async with MCPManager(mcp_servers) as mcp:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. Use tools if you need to."
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
    # I was unable to make the LLM repsond with unchanged base64 image data,
    # so the MCP server save the image to a file and returns the filename.

    avg_temps_poland_2024 = [-0.3, 5.7, 6.7, 10.5, 16.0, 18.4, 20.3, 20.2, 16.9, 10.1, 3.8, 2.5]
    avg_temps_poland_2025 = [2.0, 3.5, 7.0, 10.0, 13.0, 17.7, 18.9, 18.1, 15.5, 10.5, 5.0, 2.3]

    prompt = f"""
    Your task is to create a line plot out of a given data.
    
    Data series:    
        * Year 2024: {avg_temps_poland_2024}
        * Year 2025: {avg_temps_poland_2025}
        
    Name it 'Average Temperature in Poland'.
    Axes should be labeled 'Months' (x-axis) and 'Average Temperature (°C) (y-axis).
    Include a legend.
        """
    response = asyncio.run(make_llm_request(prompt))
    print("Response:\n", response)

    with open("ex4_response.md", "w") as f:
        f.write(response)
