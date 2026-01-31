from fastmcp import FastMCP

mcp = FastMCP("Time utils")


@mcp.tool(description="Get current date in the YYYY-MM-DD format")
def get_current_date() -> str:
    from datetime import date
    return date.today().isoformat()


@mcp.tool(description="Get current datetime in the YYYY-MM-DD HH:MM:SS format")
def get_current_datetime() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8002)
