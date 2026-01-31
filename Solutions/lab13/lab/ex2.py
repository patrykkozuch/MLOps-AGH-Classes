import datetime
import json
import polars as pl
from typing import Callable

from openai import OpenAI


def make_llm_request(prompt: str) -> str:
    client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")

    messages = [
        {"role": "developer", "content": "You are a weather assistant."},
        {"role": "user", "content": prompt},
    ]

    tool_definitions, tool_name_to_func = get_tool_definitions()

    # guard: loop limit, we break as soon as we get an answer
    for _ in range(10):
        response = client.chat.completions.create(
            model="",
            messages=messages,
            tools=tool_definitions,  # always pass all tools in this example
            tool_choice="auto",
            max_completion_tokens=1000,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        resp_message = response.choices[0].message
        messages.append(resp_message.model_dump())

        print(f"Generated message: {resp_message.model_dump()}")
        print()

        # parse possible tool calls (assume only "function" tools)
        if resp_message.tool_calls:
            for tool_call in resp_message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                # call tool, serialize result, append to messages
                func = tool_name_to_func[func_name]
                func_result = func(**func_args)

                messages.append(
                    {
                        "role": "tool",
                        "content": json.dumps(func_result),
                        "tool_call_id": tool_call.id,
                    }
                )
        else:
            # no tool calls, we're done
            return resp_message.content

    # we should not get here
    last_response = resp_message.content
    return f"Could not resolve request, last response: {last_response}"


def get_tool_definitions() -> tuple[list[dict], dict[str, Callable]]:
    tool_definitions = [
        {
            "type": "function",
            "function": {
                "name": "read_csv_from_url",
                "description": 'Reads the first 20 rows of a CSV file from a given URL and returns it as a CSV string.',
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL of the CSV file to read.",
                        },
                    },
                    "required": ["url"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read_parquet_from_url",
                "description": "Reads the first 20 rows of a Parquet file from a given URL and returns it as a CSV string.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL of the CSV file to read.",
                        },
                    },
                    "required": ["url"],
                },
            },
        },
    ]

    tool_name_to_callable = {
        "read_csv_from_url": read_csv,
        "read_parquet_from_url": read_parquet,
    }

    return tool_definitions, tool_name_to_callable


def read_csv(url: str) -> str:
    return pl.read_csv(url)[:20].write_csv()

def read_parquet(url: str) -> str:
    return pl.read_parquet(url)[:20].write_csv()


if __name__ == "__main__":
    prompt = """
    You are a specialist in toxicology data analysis.
    Your task is to answer questions based only on a given dataset. Do not use any prior knowledge.
    You can find the dataset here: https://github.com/j-adamczyk/ApisTox_dataset/raw/refs/heads/master/outputs/dataset_final.csv
    
    What is the CAS of Benzoic acid?
    """

    answer = make_llm_request(prompt)
    print("Final answer:")
    print(answer)
    # Example generated answer: "The CAS number of Benzoic acid is 65-85-0."

    prompt = """
    Your task is to answer questions based only on a given dataset. Do not use any prior knowledge.
    You can find the dataset here: https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-01.parquet 
    
    What is the longest trip distance recorded in the dataset?
    """

    answer = make_llm_request(prompt)
    print("Final answer:")
    print(answer)
    # Example generated answer: "The longest trip distance recorded in the dataset is 2.8 miles."