# Calculator MCP Server

本 MCE 服务器提供了一个名为 `calculate` 的工具，用于执行基本的算术运算。

## 功能

该项目实现了一个 MCP 服务器，其中包含一个 `calculate` 工具，可以执行以下操作：
- 加法 (+)
- 减法 (-)
- 乘法 (*)
- 除法 (/)

## MCP 客户端配置

要在您的 MCP 客户端中使用此服务器，请添加以下配置：

```json
{
  "mcpServers": {
    "youtube-summary-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/jmvoid/youtube-summary-mcp",
        "youtube-summary-mcp-server"
      ]
    }
  }
}
