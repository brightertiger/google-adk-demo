# Agents Demo

A multi-agent system that demonstrates AI agents working together to extract and process information from web pages. This project showcases how specialized AI agents can collaborate to perform complex tasks like web scraping, address extraction, and geocoding.

Built with **Google ADK 1.21+** and **MCP 1.25+**.

## Overview

This project implements a team of specialized AI agents that work together to:
1. Crawl web pages and extract their content
2. Identify and parse addresses from the content
3. Convert addresses into geographic coordinates
4. Present the results in a structured JSON format

## Agent Architecture

| Agent | Role | Tools |
|-------|------|-------|
| **Manager Agent** | Orchestrates the workflow between all agents | MCP Tools |
| **Crawler Agent** | Fetches and cleans webpage content | `crawl_to_markdown` |
| **Address Agent** | Extracts structured address information from text | None (LLM-based) |
| **Geocoding Agent** | Converts addresses to lat/long coordinates | `geocode_address` |

## Project Structure

```
.
├── src/
│   ├── agents/
│   │   ├── agent.py       # Main agent logic and coordination
│   │   └── config.yaml    # Agent configurations and instructions
│   └── mcp_server/
│       └── mcp_server.py  # MCP tools (crawl_to_markdown, geocode_address)
├── assets/                # Screenshots and static assets
├── index.html             # Project landing page
├── output.json            # Sample output
├── .env                   # Environment variables
└── pyproject.toml         # Project dependencies
```

## How It Works

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Manager Agent  │────▶│  Crawler Agent  │────▶│  Address Agent  │
│  (Orchestrator) │     │  (Web Scraping) │     │  (Extraction)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   JSON Output   │◀────│ Geocoding Agent │
                        │   (output.json) │     │  (Coordinates)  │
                        └─────────────────┘     └─────────────────┘
```

1. **Manager Agent** receives a URL and delegates to specialized agents
2. **Crawler Agent** fetches webpage content using the MCP `crawl_to_markdown` tool
3. **Address Agent** extracts structured addresses from the text content
4. **Geocoding Agent** converts addresses to coordinates using OpenStreetMap
5. Results are compiled into a structured JSON output

## Prerequisites

- Python 3.12+
- Google API key (get one at [Google AI Studio](https://aistudio.google.com/apikey))

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/agents-demo.git
cd agents-demo
```

2. Install dependencies:
```bash
pip install -e .
```

3. Set up your API key:
```bash
export GOOGLE_API_KEY=your_api_key_here
```

Or create a `.env` file:
```
GOOGLE_API_KEY=your_api_key_here
```

## Usage

Run the agent system:
```bash
python src/agents/agent.py
```

The output will be saved to `output.json`:
```json
{
  "addresses": [
    {
      "address": "Google Bangalore Office, RMZ Infinity Tower E",
      "city": "Bangalore",
      "state": "Karnataka",
      "zip": "560016",
      "country": "India"
    }
  ]
}
```

### Custom URL

Edit the `query_url` in `src/agents/agent.py`:
```python
query_url = "https://your-target-webpage.com"
```

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| google-adk | ≥1.21.0 | Agent Development Kit |
| mcp | ≥1.25.0 | Model Context Protocol |
| litellm | ≥1.80.0 | LLM API wrapper |
| beautifulsoup4 | ≥4.13.0 | HTML parsing |
| json-repair | ≥0.54.0 | JSON error recovery |

## MCP Server Tools

The MCP server provides two tools:

### `crawl_to_markdown`
Fetches a webpage and extracts clean text content.
```python
crawl_to_markdown(url: str) -> str
```

### `geocode_address`
Converts addresses to geographic coordinates using OpenStreetMap Nominatim.
```python
geocode_address(addresses: str) -> str  # JSON input/output
```

## License

MIT License - See LICENSE file for details.
