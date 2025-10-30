import asyncio
import operator
from typing import Literal

import mcp.types as types
from mcp.server import Server, stdio

# Define the server instance
mcp_server = Server(name="youtube-summary-mcp", version="0.1.0")

Operator = Literal["+", "-", "*", "/"]

OPERATORS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
}


# The original calculate function remains the same
def calculate(
    operand1: float,
    operand2: float,
    operator: Operator,
) -> float:
    """
    Performs a basic arithmetic operation on two numbers.

    Args:
        operand1: The first number in the operation.
        operand2: The second number in the operation.
        operator: The arithmetic operator to use.
                  Must be one of '+', '-', '*', '/'.

    Returns:
        The result of the arithmetic operation.
    """
    if operator not in OPERATORS:
        raise ValueError(f"Invalid operator: {operator}")
    return OPERATORS[operator](operand1, operand2)


@mcp_server.list_tools()
async def list_tools() -> list[types.Tool]:
    """Lists the available tools."""
    return [
        types.Tool(
            name="calculate",
            description="Performs a basic arithmetic operation on two numbers.",
            inputSchema={
                "type": "object",
                "properties": {
                    "operand1": {"type": "number", "description": "The first number in the operation."},
                    "operand2": {"type": "number", "description": "The second number in the operation."},
                    "operator": {
                        "type": "string",
                        "description": "The arithmetic operator to use. Must be one of '+', '-', '*', '/'.",
                        "enum": ["+", "-", "*", "/"],
                    },
                },
                "required": ["operand1", "operand2", "operator"],
            },
        )
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.ContentBlock]:
    """Calls a tool with the given arguments."""
    if name == "calculate":
        try:
            result = calculate(
                operand1=arguments["operand1"],
                operand2=arguments["operand2"],
                operator=arguments["operator"],
            )
            return [types.TextContent(type="text", text=str(result))]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error: {e}")]
    raise ValueError(f"Tool '{name}' not found.")


async def main():
    """
    Initializes and runs the MCP server.
    """
    async with stdio.stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            mcp_server.create_initialization_options(),
        )


def start_server():
    """Synchronous entry point to run the server."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    start_server()
