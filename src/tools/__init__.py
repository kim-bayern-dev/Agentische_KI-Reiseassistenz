import json
from tools.registry import ToolRegistry


def call_tool(tool_call) -> dict:
    """Call a tool by name with the given input.

    Args:
        tool_call: A dict with 'name' and 'input' keys.

    Returns:
        The output of the tool.
    """

    name = tool_call.name
    args = tool_call.arguments or {}

    # parse args if needed
    if isinstance(args, str):
        args = json.loads(args)

    # Execute via LangChain tool
    try:
        result = ToolRegistry().get_tool_by_name(name).invoke(args)
    except Exception as e:
        result = f"Error calling tool {name}: {e}"

    return {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "tool_args": args,
        "name": name,
        "content": json.dumps(result, ensure_ascii=False),
    }
