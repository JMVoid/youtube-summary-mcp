# YouTube Summary MCP Server

This project provides an MCP (Model Context Protocol) server that offers a tool to extract metadata and subtitles from YouTube videos.

## Features

This server implements a single tool, `summarize_subtitle_id`, which provides the following capabilities:

- **Metadata Extraction**: Retrieves the title and description of a given YouTube video.
- **Subtitle Download**: Downloads the video's transcript in a specified language.
- **Smart Language Fallback**: If the requested language is unavailable, the server intelligently searches for and downloads a suitable alternative based on a predefined priority list (e.g., English, Chinese, Spanish, etc.).
- **Best Caption Selection**: Automatically prioritizes official transcripts over auto-generated (ASR) or machine-translated ones to ensure the highest quality content.
- **Plain Text Conversion**: Converts the downloaded SRT subtitle file into a clean, easy-to-process plain text format.
- **Extensive Language Support**: Supports a wide range of languages for transcript downloads.

## Tool: `summarize_subtitle_id`

This is the primary tool exposed by the server.

### Arguments

- `url` (str): **Required**. The full URL of the YouTube video.
- `target_lang` (str): *Optional*. The desired language for the transcript, specified by a two-letter language code. Defaults to `"en"`.

#### Supported Language Codes:
`en`, `zh`, `es`, `hi`, `ar`, `pt`, `ru`, `ja`, `fr`, `de`, `ko`, `it`, `tr`, `nl`, `pl`, `vi`, `th`, `id`, `ms`, `fa`, `ur`, `bn`, `he`, `fil`, `sv`, `el`, `cs`, `hu`, `da`, `no`, `fi`, `ro`, `uk`, `sr`.

### Return Value

The tool returns a JSON object indicating the outcome:

- **On Success**:
  ```json
  {
    "status": "success",
    "title": "The Video Title",
    "description": "The video's description text.",
    "content": "The full text of the transcript..."
  }
  ```

- **On Failure**:
  ```json
  {
    "status": "failure",
    "reason": "A message explaining the cause of the failure."
  }
  ```

## MCP Client Configuration

To use this server in your MCP client (e.g., Cline, Cursor), add the following configuration:

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
