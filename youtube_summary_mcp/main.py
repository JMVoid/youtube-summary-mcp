import operator
from typing import Literal

from mcp.server.fastmcp import FastMCP

# Define the server instance using FastMCP
mcp = FastMCP(name="youtube-summary-mcp")

Operator = Literal["+", "-", "*", "/"]

OPERATORS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
}


# Decorate the calculate function directly as a tool
@mcp.tool()
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


def start_server():
    """Synchronous entry point to run the server."""
    try:
        mcp.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    start_server()
