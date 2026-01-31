import json
import os
import asyncio
import dotenv
from guardrails import Guard
from guardrails_grhub_detect_jailbreak import DetectJailbreak

from openai import OpenAI
from tryolabs_grhub_restricttotopic import RestrictToTopic

from mcp_manager import MCPManager

dotenv.load_dotenv()

message_history = [
    {
        "role": "system",
        "content": (
            """
            You are a helpful trip planning assistant.
            
            You answer only to requests about trips, destinations and connected activities.
            For other requests, you MUST politely refuse to answer.
            
            Use provided tools if you need to.
            """
        ),
    }
]


def generate_completion(*, messages, **kwargs):
    async def _generate_completion_async():
        global message_history
        client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")
        tavily_key = os.getenv("TAVILY_API_KEY", "")
        mcp_servers = {
            "tavily": f"https://mcp.tavily.com/mcp/?tavilyApiKey={tavily_key}",
            "time": "http://localhost:8002/mcp",
            "weather": "http://localhost:8001/mcp",
        }

        async with MCPManager(mcp_servers) as mcp:
            for _ in range(10):
                chat_response = client.chat.completions.create(
                    model="",
                    messages=messages,
                    tools=mcp.tools,
                    max_completion_tokens=1000,
                    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
                )

                chat_response = chat_response.choices[0].message
                if not chat_response.tool_calls:
                    message_history = messages
                    return chat_response.content

                for tool_call in chat_response.tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments)

                    func_result = await mcp.call_tool(func_name, func_args)

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": func_name,
                            "content": str(func_result),
                        }
                    )

        message_history = messages
        return "Too many tool calls, aborting."

    return asyncio.run(_generate_completion_async())


def make_llm_request(prompt: str) -> str:
    guard = Guard().use(
        DetectJailbreak(on_fail="exception"),
        on="messages",
    ).use(
        RestrictToTopic(
            valid_topics=["travel", "trips", "activities", "weather", "time", "destinations"],
            on_fail="exception",
            custom_message="You are only allowed to talk about fish.",
        ),
        on="messages",
    )

    message_history.append(
        {"role": "user", "content": prompt}
    )

    try:
        return guard(
            generate_completion,
            messages=message_history,
        ).validated_output
    except Exception as e:
        return f"Sorry, I cannot help you with that, reason: {e}"


if __name__ == "__main__":
    print("Welcome to the TripPlanning Assistant!")
    print("-----------------------------------")
    print("Type your requests below or use /exit to quit")
    print("How can I help you today?")
    prompt = input("> ")

    while prompt.strip() != "/exit":
        result = make_llm_request(prompt)
        print("\n" + result + "\n")
        prompt = input("> ")
