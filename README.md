# 剧本分镜智能体 (Script-to-Shot AI Agent)

一个基于多智能体协作的AI系统，能够将剧本智能拆分为短视频脚本单元，生成高质量分镜描述，并保证叙事连续性。支持多种AI提供商，具有强大的可扩展性和易用性。

## 核心功能

- **智能剧本解析**：自动识别场景、对话和动作指令，支持自然语言和JSON格式
- **精准时序规划**：按短视频粒度智能切分内容，优化叙事节奏
- **连续性守护**：确保相邻分镜间角色状态、场景和情节的一致性
- **高质量分镜生成**：生成详细的中文画面描述和英文AI提示词，包含镜头角度、角色状态等
- **多模型支持**：兼容OpenAI、Qwen、DeepSeek、Ollama等多种AI提供商
- **自动重试机制**：请求失败时自动重试，提高系统稳定性
- **质量审查**：自动检查分镜质量和连续性问题，提供优化建议

## 技术架构

项目采用多智能体协作架构，基于以下技术栈：

- **Python 3.10+**：核心开发语言
- **FastAPI**：高性能Web框架
- **LangChain + LangGraph**：工作流编排和智能体管理
- **多模型支持**：兼容OpenAI、Qwen、DeepSeek、Ollama等
- **Pydantic**：数据验证和设置管理
- **环境变量配置**：灵活的配置管理

## 快速上手

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/HengLine/tool-storyboard-agent.git
cd tool-storyboard-agent

# 直接运行，自动创建虚拟环境
python .\start_app.py

# 或者手动创建虚拟环境
python -m venv .venv
# 激活虚拟环境 (Windows)
.venv\Scripts\activate
# 激活虚拟环境 (Linux/Mac)
source .venv/bin/activate
# 安装依赖
pip install -r requirements.txt
```

### 2. 配置设置

复制配置文件并设置环境变量：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置必要的参数：

```properties
# 选择AI提供商：openai, qwen, deepseek, ollama
AI_PROVIDER=qwen

# 根据选择的提供商配置对应的API密钥
QWEN_API_KEY=your_qwen_api_key
QWEN_BASE_URL=https://api.example.com/v1

# 或 OPENAI_API_KEY=your_openai_api_key
# 或 DEEPSEEK_API_KEY=your_deepseek_api_key

# 可选：设置超时时间和重试次数
AI_API_TIMEOUT=60
AI_RETRY_COUNT=3
```

### 3. 启动应用

```bash
python start_app.py
```

应用将在 `http://0.0.0.0:8000` 启动，提供API接口服务。



## 使用方法

### 1. 作为Python库使用

```python
from hengline.generate_agent import generate_storyboard

# 基本使用：传入中文剧本文本
script_text = """
场景：咖啡馆内
小明坐在窗边，看着窗外的雨。
小红：你看起来心情不太好。
小明：嗯，工作上遇到了一些问题。
小红：别担心，一切都会好起来的。
"""

# 生成分镜
result = generate_storyboard(script_text)
print(f"生成了 {result['total_shots']} 个分镜")
for shot in result['shots']:
    print(f"\n分镜 {shot['shot_id']}:")
    print(f"时间: {shot['start_time']}-{shot['end_time']}s")
    print(f"描述: {shot['description']}")
```

### 2. 高级参数设置

```python
# 自定义风格和时长
result = generate_storyboard(
    script_text,
    style="cinematic",  # 可选: realistic, anime, cinematic, cartoon
    duration_per_shot=8,  # 每段目标时长（秒）
    prev_continuity_state=None  # 用于长剧本续生成
)
```

### 3. API接口调用

启动服务后，可以通过HTTP接口调用：

```bash
curl -X POST http://localhost:8000/api/generate_storyboard \
  -H "Content-Type: application/json" \
  -d '{"script_text": "场景：咖啡馆内\n小明坐在窗边...", "style": "realistic"}'
```

### 4. 集成到其他系统

#### 集成到Web应用

```python
# Flask示例
from flask import Flask, request, jsonify
from hengline.generate_agent import generate_storyboard

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    result = generate_storyboard(
        script_text=data['script_text'],
        style=data.get('style', 'realistic')
    )
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
```

#### 集成到LangChain工作流

```python
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from hengline.client.client_factory import get_ai_client

# 获取配置的AI客户端
llm = get_ai_client()

# 创建LangChain链
prompt = PromptTemplate(
    input_variables=["story"],
    template="总结这个故事：{story}"
)
chain = LLMChain(llm=llm, prompt=prompt)

# 使用链
result = chain.run(story="小明和小红在咖啡馆的对话...")
print(result)
```

#### 集成到A2A系统

```python
# A2A Agent示例
from a2a import Agent, Message
from hengline.generate_agent import generate_storyboard

class StoryboardAgent(Agent):
    def process_message(self, message: Message) -> Message:
        # 处理传入的剧本消息
        script = message.content
        storyboard = generate_storyboard(script)
        
        # 返回分镜结果
        return Message(
            content=storyboard,
            type="storyboard_result"
        )

# 注册和使用Agent
agent = StoryboardAgent(name="storyboard_agent")
```

## 输出格式

生成的分镜结果为结构化JSON，包含以下核心字段：

```json
{
  "total_shots": 3,              // 生成的分镜总数
  "storyboard_title": "咖啡馆对话", // 分镜标题
  "shots": [
    {
      "shot_id": "shot_001",    // 分镜ID
      "start_time": 0.0,         // 开始时间（秒）
      "end_time": 5.0,           // 结束时间（秒）
      "duration": 5.0,           // 分镜时长
      "description": "小明坐在咖啡馆窗边...", // 中文画面描述
      "prompt_en": "A man sitting by the window...", // 英文AI提示词
      "characters": ["小明"],    // 角色列表
      "dialogue": "",           // 对话内容
      "camera_angle": "medium shot", // 镜头角度
      "continuity_anchors": ["小明位置:窗边", "天气:下雨"] // 连续性锚点
    },
    // 更多分镜...
  ],
  "status": "success",          // 生成状态
  "warnings": []                 // 警告信息
}
```



## 配置说明

系统配置支持两种方式：配置文件和环境变量（优先级更高）。

### 环境变量配置

关键环境变量：

| 环境变量 | 说明 | 默认值 |
|---------|------|-------|
| AI_PROVIDER | AI提供商名称（openai/qwen/deepseek/ollama） | openai |
| OPENAI_API_KEY | OpenAI API密钥 | - |
| QWEN_API_KEY | 文心一言API密钥 | - |
| DEEPSEEK_API_KEY | DeepSeek API密钥 | - |
| AI_API_TIMEOUT | API请求超时时间（秒） | 60 |
| AI_RETRY_COUNT | 请求失败重试次数 | 3 |
| AI_TEMPERATURE | 生成温度参数 | 0.7 |
| AI_MAX_TOKENS | 最大生成令牌数 | 2000 |

### 配置文件

`config/config.json` 包含默认配置，可通过环境变量覆盖。

## 实际应用场景

### 短视频内容创作
- 将小说章节转换为短视频分镜脚本
- 为广告创意生成详细的镜头规划
- 自动将剧本拆分为社交媒体短视频格式

### 影视前期制作辅助
- 快速生成剧本的视觉化预览
- 辅助导演进行镜头规划和调度
- 为分镜头绘制提供详细参考

### 教育培训应用
- 为教学内容创建情景化视频脚本
- 将复杂概念通过分镜形式直观呈现
- 辅助培训视频的标准化制作

## 最佳实践

1. **剧本格式优化**
   - 使用明确的场景标识和角色对白格式
   - 避免过于冗长的描述，保持每个场景的焦点
   - 为重要动作和情感变化添加明确标记

2. **参数调优**
   - 对于对话密集型内容，可适当延长`duration_per_shot`
   - 情感细腻的场景推荐使用`cinematic`风格
   - 动作场景可选择`realistic`风格获得更准确的描述

3. **性能优化**
   - 对于长剧本，建议分段处理并使用`prev_continuity_state`保持连贯性
   - 根据服务器资源调整`AI_RETRY_COUNT`参数
   - 生产环境中推荐使用`gpt-4o`或同等性能模型

## 故障排除

### 常见问题及解决方案

1. **API密钥错误**
   - 检查环境变量中的API密钥是否正确设置
   - 确保密钥未过期，并有足够的使用额度
   - 验证AI_PROVIDER与密钥类型是否匹配

2. **分镜生成失败**
   - 检查剧本格式是否规范，尝试简化复杂描述
   - 增加`AI_RETRY_COUNT`参数值
   - 查看日志文件获取详细错误信息

3. **连续性问题**
   - 确保相邻场景描述包含足够的上下文信息
   - 对于长剧本，使用分段处理并传递连续性状态
   - 检查`continuity_anchors`字段是否正确捕获关键信息

4. **性能问题**
   - 降低模型温度参数可提高响应速度
   - 减少单次处理的剧本长度
   - 优化系统资源分配

## 许可证

MIT License

## 贡献指南

欢迎提交Issue和Pull Request！贡献前请确保：

1. 遵循现有代码风格和架构
2. 为新功能添加适当的测试用例
3. 更新相关文档

## 联系方式

如有问题或建议，请提交GitHub Issue或联系项目维护团队。