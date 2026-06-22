from app.tools import ALL_TOOLS


class ToolRegistry:
    def __init__(self, db=None):
        self.db = db
        self.tools = ALL_TOOLS

    def list_tools(self) -> list[dict]:
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "required_parameters": tool["required_parameters"],
                "optional_parameters": tool.get("optional_parameters", [])
            }
            for tool in self.tools.values()
        ]

    def get_tool(self, tool_name: str):
        return self.tools.get(tool_name)

    def execute(self, tool_name: str, parameters: dict, token: str | None = None) -> dict:
        tool = self.get_tool(tool_name)

        if tool is None:
            return {
                "success": False,
                "tool_name": tool_name,
                "result": None,
                "error": f"Outil inconnu : {tool_name}"
            }

        missing_parameters = self._validate_parameters(tool, parameters)

        if missing_parameters:
            return {
                "success": False,
                "tool_name": tool_name,
                "result": None,
                "error": f"Paramètres manquants : {', '.join(missing_parameters)}"
            }

        try:
            result = tool["function"](parameters)

            return {
                "success": True,
                "tool_name": tool_name,
                "result": result,
                "error": None
            }

        except Exception as exception:
            return {
                "success": False,
                "tool_name": tool_name,
                "result": None,
                "error": str(exception)
            }

    def _validate_parameters(self, tool: dict, parameters: dict) -> list[str]:
        missing = []

        for parameter in tool["required_parameters"]:
            if parameter not in parameters or parameters[parameter] is None:
                missing.append(parameter)

        return missing