<p align="center">
  <h1 align="center">🎬 PenShot: Script → Storyboard → Prompt</h1>
  <p align="center">
    <strong>A multi-agent collaborative screenplay storyboarding system with narrative continuity.</strong>
  </p>
  <p align="center">
    <a href="https://langchain-ai.github.io/langgraph/"><img src="https://img.shields.io/badge/LangGraph-1C3C3C.svg?style=flat-square&logo=langchain&logoColor=white" alt="LangGraph"></a>
    <a href="https://www.llamaindex.ai/"><img src="https://img.shields.io/badge/LlamaIndex-000000.svg?style=flat-square&logo=llamaindex&logoColor=white" alt="LlamaIndex"></a>
    <a href="https://github.com/neopen/story-shot-agent"><img src="https://img.shields.io/badge/LLMs-DeepSeek%20%7C%20OpenAI-4E6BFF.svg?style=flat-square" alt="LLMs"></a>
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10+-3776AB.svg?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
    <a href="https://pypi.org/project/penshot/"><img src="https://img.shields.io/pypi/v/penshot.svg?style=flat-square&logo=pypi&logoColor=white" alt="PyPI"></a>
    <a href="https://pepy.tech/project/penshot"><img src="https://img.shields.io/pepy/dt/penshot?style=flat-square&color=blue" alt="Downloads"></a>
    <a href="https://github.com/neopen/story-shot-agent"><img src="https://img.shields.io/github/stars/neopen/story-shot-agent?style=flat-square&logo=github" alt="GitHub Stars"></a>
    <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg?style=flat-square" alt="License"></a>
  </p>
  <p align="center">
    <a href="./README_CN.md">中文</a> •
    <a href="https://pengline.cn/2026/02/7e6cd67dd5ee45248f2276ac145555f5/">Documentation</a> •
    <a href="https://pypi.org/project/penshot/">PyPI</a> •
    <a href="https://shot.helpenx.com">WebSite</a> •
    <a href="https://pengline.cn/2026/02/b027d930c0b84ba6abd24bbef7d78afc/">MCP Service</a>
  </p>
</p>

---

> 🚀 **One-Click Conversion**: Any screenplay format → Shot-level descriptions → **Sora / Veo / Runway / Kling-ready prompts**  
> 🧠 **Continuity Guaranteed**: Multi-level memory + vector retrieval ensures character/scene/plot consistency across shots  
> ⚡ **Get Started in 5 Minutes**: `pip install penshot` + 3 lines of code

---

## 💡 Why PenShot?

A multi-agent collaborative screenplay storyboarding system built on **LangChain** and **LangGraph**. It automatically parses long scripts, segments them into optimal AI text-to-video prompt fragments, and enforces visual/narrative consistency using Chroma vector retrieval and multi-level memory.

| Pain Point | PenShot Solution |
| :--- | :--- |
| **Scripts too long for AI video models** | Smart chunking + precise duration planning tailored for model constraints |
| **Character outfits/scenes jump out of context** | Multi-level memory + Chroma vector retrieval auto-maintains continuity |
| **Time-consuming manual prompt engineering** | Auto-generates bilingual descriptions + negative prompts + audio cues |
| **Complex multi-model setup** | One codebase supporting OpenAI, Qwen, DeepSeek, Ollama & more |

---

## 🌟 Core Features

- 🎯 **Intelligent Script Parsing:** Auto-identifies scenes, dialogue, and action cues; supports long-text chunking.
- ⏱️ **Precise Temporal Planning:** Segments content at the shot level, allocating optimal durations for AI video generation.
- 🛡️ **Continuity Guard:** Task pool priority queuing + short/mid/long-term memory Ensures consistency in character states, props, and plot across adjacent shots.
- 🎨 **High-Quality Prompt Output:** Generates detailed bilingual (ZH/EN) visual descriptions, negative prompts, and audio prompts.
- 🔌 **Multi-Protocol & Agent Integration:** Supports Python SDK, REST API, LangGraph nodes, A2A collaboration, and standard **MCP Service**.



---

## 🏛️ System Architecture & Workflow

<p align="center">
  <img src="./assets/imgs/penshot-Roadmap.webp" alt="PenShot Workflow" width="100%">
</p>

<details>
<summary>🔍 <strong>Click to view detailed UML Class Architecture</strong></summary>

<p align="center">
  <img src="./assets/imgs/penshot.webp" alt="PenShot UML Architecture" width="100%">
</p>

</details>

> 💡 For in-depth architectural design, memory management, and continuity algorithms, please refer to our [Architecture Documentation](https://pengline.cn/2026/02/7e6cd67dd5ee45248f2276ac145555f5/).



------

## Quick Start

### 1. Environment Setup

```bash
# Install via PyPI
pip install penshot
```

> Note: `penshot` is the PyPI package name, while `story-shot-agent` is the GitHub repository name. Both refer to the same project.

### 2. Configuration

```bash
cp .env.example .env
```

Edit the `.env` file to configure the required LLM and Embedding parameters:

```properties
########################## LLM Configuration #########################
PENSHOT_LLM__DEFAULT__BASE_URL=https://api.openai.com/v1
PENSHOT_LLM__DEFAULT__API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
PENSHOT_LLM__DEFAULT__MODEL_NAME=gpt-4o
PENSHOT_LLM__DEFAULT__TIMEOUT=30

########################## Embedding Model Configuration #########################
PENSHOT_EMBED__DEFAULT__BASE_URL=https://api.openai.com/v1
PENSHOT_EMBED__DEFAULT__API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
PENSHOT_EMBED__DEFAULT__MODEL_NAME=text-embedding-v4

########################## Redis Configuration ##########################
PENSHOT_REDIS_URL=redis://:123456@localhost:6379/0
```

### 3.Usage Methods

#### 1. Python SDK

```python
from penshot.api import create_penshot_agent

agent = create_penshot_agent(max_concurrent=5)

script = "Morning, a girl reading in a cafe, sunlight streaming through the window..."
task_id = agent.breakdown_script_async(
    script,
    callback=lambda r: print(f"Task {r.task_id} completed")
)

status = agent.get_task_status(task_id)
result = await agent.wait_for_result_async(task_id)
```

Full example: [direct_usage.py](https://github.com/neopen/story-shot-agent/blob/main/examples/direct_usage.py)

#### 2. FastAPI Web Application Integration

Integrate into existing systems via standard HTTP endpoints:

```python
from fastapi import FastAPI, HTTPException
from penshot.api import create_penshot_agent

app = FastAPI(title="Penshot API", version="0.1.0")
agent = create_penshot_agent(max_concurrent=5)

@app.post("/api/generate")
async def generate(script_text: str):
    task_id = agent.breakdown_script_async(script_text)
    return {"task_id": task_id, "status": "PENDING"}
```

Full example: [web_app.py](https://github.com/neopen/story-shot-agent/blob/main/examples/web_app.py)

#### 3. LangGraph Node Integration

Can be embedded as an independent node in LangChain/LangGraph workflows for end-to-end automation. Full example: [langgraph_integration.py](https://github.com/neopen/story-shot-agent/blob/main/examples/langgraph_integration.py)

#### 4. A2A Protocol Collaboration

Supports context passing and task orchestration with upstream scriptwriting agents and downstream text-to-video/editing agents. Full example: [a2a_integration.py](https://github.com/neopen/story-shot-agent/blob/main/examples/a2a_integration.py)

#### 5. MCP (Model Context Protocol) Support

Start the MCP Server:

```bash
python -m penshot.mcp_server --max-concurrent 5 --queue-size 500
```

Clients can call the `breakdown_script` and `get_task_result` tools to seamlessly integrate with MCP-compatible IDEs or agent frameworks. Full example: [mcp_client.py](https://github.com/neopen/story-shot-agent/blob/main/examples/mcp_client.py)



------

## Docker Quick Start
```bash
docker run -d \
  --name penshot \
  -p 8000:8000 \
  -e PENSHOT_LLM__DEFAULT__BASE_URL="https://api.deepseek.com" \
  -e PENSHOT_LLM__DEFAULT__API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxx" \
  -e PENSHOT_LLM__DEFAULT__MODEL_NAME="deepseek-v4-flash" \
  -e PENSHOT_EMBED__DEFAULT__BASE_URL="https://api.openai.com/v1" \
  -e PENSHOT_EMBED__DEFAULT__API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxx" \
  -e PENSHOT_EMBED__DEFAULT__MODEL_NAME="text-embedding-v4" \
  -e PENSHOT_REDIS_URL="redis://:@host.docker.internal:6379/0" \
  neotems/penshot:latest
```

### 1. Download  Config

```bash
# Docker Compose Config
wget https://raw.githubusercontent.com/neopen/story-shot-agent/main/docker-compose.yml
# penshot Config
wget https://raw.githubusercontent.com/neopen/story-shot-agent/main/.env.example -O .env
```

### 2. Configuration

Edit the `.env` file to configure the required LLM and Embedding parameters：`vim .env`

### 3. Start Docker

`docker compose up -d`



------

## Output Data Structure

The system returns standardized JSON containing video prompts, negative prompts, duration estimates, style parameters, and accompanying audio prompts:

```json
{
  "fragments": [
    {
      "fragment_id": "frag_001",
      "prompt": "Cinematic wide shot: midnight 11 PM in a compact urban apartment living room...",
      "negative_prompt": "cartoon, anime, 3D render, bright lighting, text, watermark...",
      "duration": 4.2,
      "model": "runway_gen2",
      "style": "cinematic 35mm film, moody realism, shallow depth of field...",
      "audio_prompt": {
        "audio_id": "audio_001",
        "prompt": "Low-frequency rain ambience (intensity 0.95), distant muffled TV static...",
        "model_type": "AudioLDM_3",
        "audio_style": "cinematic"
      }
    }
  ]
}
```



------

## System Notes & Considerations

| Category              | Description                                                  |
| --------------------- | ------------------------------------------------------------ |
| Network Dependency    | Requires stable access to external LLM APIs. Proxy or domestic mirrors are recommended. |
| Long Text Processing  | For extremely long scripts, segmented input is advised. The system includes built-in context memory and RAG mechanisms. |
| Generation Duration   | AI video models may output clips with ±10% duration variance, which is industry-standard. |
| Multilingual Support  | Currently optimized for Chinese scripts. Support for other languages is under active iteration. |
| Audio Synchronization | Audio prompts are provided. Lip-sync and environmental sound fusion require downstream tooling. |
| Error Handling        | Auto-retry and fallback mechanisms are built-in. Extreme edge cases may require manual intervention. |



------

## Development Roadmap

### Short-Term

- Optimize long-shot segmentation logic for action continuity
- Implement consistency validators for character clothing, positioning, and props
- Specialized prompt format adaptation for Sora, Pika, and other models
- Hybrid architecture combining rule-based engines and LLMs
- Full English script support and intelligent node failure fallback
- Fragment confidence scoring and debug mode (intermediate result persistence)

### Mid-Term

- Advanced camera language support (pan, tilt, zoom, tracking, follow)
- Emotion-driven automatic visual style adjustment
- Ultra-long script chunking + vector DB context memory
- Multi-script batch queue processing & Web visualization interface
- Character/scene reference image integration & multi-format export (XML/EDL/JSON)

### Long-Term

- Multimodal input (image + audio + text hybrid)
- Real-time low-resolution preview & automatic continuity repair
- Professional editing software plugins (Premiere/FCP/DaVinci)
- Multi-user collaboration, version control, & autonomous learning from feedback
- Bidirectional script-fragment traceability, semantic alignment detection, & multi-round correction mechanisms

### Ultimate Goal

Achieve zero-information-loss visualization for scripts of any length, language, or genre, delivering a standardized workflow that meets professional director-level storyboarding standards. The system will feature customizable styles, full traceability, automatic optimization loops, and cross-modal high consistency.



------

## Contributing

We welcome contributions via Issues or Pull Requests:

- **Bug Reports:** Please provide reproduction steps, environment details, and error logs.
- **Feature Requests:** Use the `enhancement` label.
- **Code Optimization:** Performance tuning, architectural refactoring, or adding test cases.
- **Documentation:** Translations, example additions, or technical corrections.

Quick dev environment setup:

```bash
git clone https://github.com/neopen/story-shot-agent.git
cd story-shot-agent
pip install -e ".[dev]"
pytest tests/
```



------

## License

This project is licensed under the MIT License. See the [LICENSE](https://chat.qwen.ai/c/LICENSE) file for details. Copyright (c) 2025 HiPeng



------

## Contact

- Project Homepage: https://github.com/neopen/story-shot-agent
- Documentation: https://pengline.cn/2026/02/7e6cd67dd5ee45248f2276ac145555f5/

Special thanks to LangChain, LangGraph, Chroma, Ollama, and the open-source community for their technical support. If this project has been helpful to your work, please consider starring the repository and sharing your feedback.
