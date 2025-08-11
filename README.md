# MCP in 10 Minutes
Learn how to build a MCP Server for Yahoo Finance (and just about anything else) in 10 minutes. 

## See it live and in action 📺
<img src="https://i.imgur.com/P1uv4QN.jpeg"/>

# Startup 🚀

## Option 1: Docker (Recommended for self-hosting)

1. Clone this repository `git clone https://github.com/nicknochnack/MCPin10` and go into it `cd MCPin10`
2. Copy the environment template: `cp env.example .env`
3. Edit `.env` and add your Polygon API key (get one at https://polygon.io/)
4. Run the Docker setup script:
   - **Windows**: `.\scripts\docker-setup.ps1`
   - **Linux/Mac**: `./scripts/docker-setup.sh`
5. Or manually: `docker-compose up -d`
6. Check logs: `docker-compose logs mcp-server`

## Option 2: Local Development

1. Clone this repository `git clone https://github.com/nicknochnack/MCPin10` and go into it `cd MCPin10`
2. Create a virtual environment `uv venv` and activate it `source .venv/bin/activate`
3. Install the dependencies `uv sync`
4. Set your Polygon API key: `export POLYGON_API_KEY=your_key_here`
5. Run the inspector `uv run mcp dev server.py`
6. Run the agent `uv run agent.py`
7. Install langflow and run it: `uv pip install langflow` and `uv run langflow run`

<b>N.b.</b> Make sure you have ollama running. 

# Other stuff
- Installing Langflow: https://docs.langflow.org/get-started-installation
- Docker setup guide: See `DOCKER_README.md` for detailed Docker deployment instructions

# Who, When, Why?

👨🏾‍💻 Author: Nick Renotte <br />
📅 Version: 1.x<br />
📜 License: This project is licensed under the MIT License </br>
