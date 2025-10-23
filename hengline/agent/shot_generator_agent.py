# -*- coding: utf-8 -*-
"""
@FileName: shot_generator_agent.py
@Description: 分镜生成智能体，负责生成符合AI视频模型要求的提示词
@Author: HengLine
@Time: 2025/10 - 2025/11
"""
import json
from typing import Dict, List, Any

from langchain.chains.llm import LLMChain
# LLMChain在langchain 1.0+中已更改，我们将直接使用模型和提示词
from langchain_core.prompts import ChatPromptTemplate

from hengline.logger import debug, error, warning


class ShotGeneratorAgent:
    """分镜生成智能体"""

    def __init__(self, llm=None):
        """
        初始化分镜生成智能体
        
        Args:
            llm: 语言模型实例
        """
        self.llm = llm
        self._init_prompts()

    def _init_prompts(self):
        """初始化提示词模板"""
        # 分镜生成提示词模板
        self.shot_generation_template = ChatPromptTemplate.from_template("""
你是一位专业的电影分镜师和AI提示词工程师。请根据以下信息，为每一个5秒的短视频片段生成详细的分镜描述和AI提示词。

## 任务要求
1. 生成中文画面描述（供人阅读）
2. 生成英文AI视频提示词（供AI模型使用）
3. 确保提示词详细、准确，包含必要的视觉元素
4. 遵循指定的视频风格

## 输入信息

### 场景信息
场景位置: {location}
时间: {time}
氛围: {atmosphere}

### 动作序列
{actions_text}

### 连续性约束
{continuity_constraints_text}

### 视频风格
{style}

### 分镜ID
{shot_id}

## 输出格式
请严格按照以下JSON格式输出，不要添加任何额外的解释或说明：

{{
  "chinese_description": "详细的中文画面描述",
  "ai_prompt": "详细的英文AI视频提示词",
  "camera": {{
    "shot_type": "镜头类型",
    "angle": "拍摄角度",
    "movement": "镜头运动"
  }},
  "initial_state": [
    {{
      "character_name": "角色名",
      "pose": "初始姿势",
      "position": "初始位置",
      "holding": "手持物品",
      "emotion": "初始情绪",
      "appearance": "角色外观描述"
    }}
  ],
  "final_state": [
    {{
      "character_name": "角色名",
      "pose": "结束姿势",
      "position": "结束位置",
      "gaze_direction": "视线方向",
      "emotion": "结束情绪",
      "holding": "手持物品"
    }}
  ]
}}
""")

    def generate_shot(self,
                      segment: Dict[str, Any],
                      continuity_constraints: Dict[str, Any],
                      scene_context: Dict[str, Any],
                      style: str = "realistic",
                      shot_id: int = 1) -> Dict[str, Any]:
        """
        生成单个分镜，增强错误处理和字段验证
        
        Args:
            segment: 分段信息
            continuity_constraints: 连续性约束
            scene_context: 场景上下文
            style: 视频风格
            shot_id: 分镜ID
            
        Returns:
            分镜对象
        """
        info(f"生成分镜，ID: {shot_id}")

        # 准备输入数据
        actions_text = self._format_actions_text(segment.get("actions", []))
        continuity_constraints_text = self._format_continuity_constraints(continuity_constraints)

        # 构建提示词输入
        prompt_input = {
            "location": scene_context.get("location", "未知位置"),
            "time": scene_context.get("time", "未知时间"),
            "atmosphere": scene_context.get("atmosphere", "未知氛围"),
            "actions_text": actions_text,
            "continuity_constraints_text": continuity_constraints_text,
            "style": style,
            "shot_id": shot_id
        }

        try:
            if self.llm:
                debug("使用LLM生成分镜")
                try:
                    # 使用LLM生成
                    # 使用新的RunnableSequence方式替代废弃的LLMChain
                    chain = self.shot_generation_template | self.llm
                    response = chain.invoke(prompt_input)
                    # 确保获取到content
                    if hasattr(response, 'content'):
                        response = response.content

                    # 解析响应
                    shot_data = json.loads(response)
                except json.JSONDecodeError as jde:
                    error(f"LLM响应JSON解析失败: {str(jde)}")
                    # 回退到规则生成
                    debug("JSON解析失败，回退到规则生成分镜")
                    shot_data = self._generate_shot_with_rules(segment, continuity_constraints, scene_context, style, shot_id)
                except Exception as llm_e:
                    # 检查是否是API密钥错误
                    if "API key" in str(llm_e) or "401" in str(llm_e):
                        warning(f"LLM生成分镜失败：API密钥错误或权限不足: {str(llm_e)}")
                    else:
                        warning(f"LLM生成分镜失败: {str(llm_e)}")
                    # 回退到规则生成
                    debug("回退到规则生成分镜")
                    shot_data = self._generate_shot_with_rules(segment, continuity_constraints, scene_context, style, shot_id)
            else:
                # 如果没有LLM，使用规则生成
                debug("使用规则生成分镜")
                shot_data = self._generate_shot_with_rules(segment, continuity_constraints, scene_context, style, shot_id)

            # 计算时间信息
            start_time = (shot_id - 1) * 5
            end_time = shot_id * 5
            duration = 5

            # 构建完整的分镜对象，确保包含所有必要字段
            shot = {
                # 基础信息
                "shot_id": str(shot_id),  # 确保是字符串类型
                "time_range_sec": [(shot_id - 1) * 5, shot_id * 5],
                "scene_context": scene_context,
                "start_time": start_time,  # 添加必要的时间字段
                "end_time": end_time,
                "duration": duration,

                # 描述字段
                "chinese_description": shot_data.get("chinese_description", "默认中文描述"),
                "ai_prompt": shot_data.get("ai_prompt", "Default AI prompt"),
                "description": shot_data.get("chinese_description", "默认描述"),
                "prompt_en": shot_data.get("ai_prompt", "Default prompt"),

                # 相机信息
                "camera": shot_data.get("camera", {
                    "shot_type": "medium shot",
                    "angle": "eye-level",
                    "movement": "static"
                }),
                "camera_angle": "medium_shot",  # 添加必要的相机角度字段

                # 角色相关
                "characters_in_frame": self._extract_characters_in_frame(shot_data),
                "characters": self._extract_characters_in_frame(shot_data),  # 添加必要的角色字段
                "dialogue": "",  # 添加对话字段

                # 状态信息
                "initial_state": shot_data.get("initial_state", []),
                "final_state": shot_data.get("final_state", []),
                "continuity_anchor": self._generate_continuity_anchor(shot_data),
                "continuity_anchors": [],  # 添加必要的连续性锚点字段
                # 确保final_continuity_state字段为字典类型
                "final_continuity_state": {}
            }

            debug(f"分镜生成完成: {shot.get('chinese_description', '')[:100]}...")
            return shot

        except Exception as e:
            error(f"分镜生成失败: {str(e)}")
            # 返回默认分镜
            default_shot = self._get_default_shot(segment, scene_context, style, shot_id)
            # 确保默认分镜中也包含final_continuity_state字段
            if "final_continuity_state" not in default_shot:
                default_shot["final_continuity_state"] = {}
            return default_shot

    def _format_actions_text(self, actions: List[Dict[str, Any]]) -> str:
        """格式化动作文本"""
        lines = []
        for idx, action in enumerate(actions):
            if "dialogue" in action:
                lines.append(f"{idx + 1}. {action['character']}（{action['emotion']}）：{action['dialogue']}")
            else:
                lines.append(f"{idx + 1}. {action['character']} {action.get('action', '')}（{action.get('emotion', '平静')}）")
        return "\n".join(lines)

    def _format_continuity_constraints(self, constraints: Dict[str, Any]) -> str:
        """格式化连续性约束"""
        lines = []

        # 添加角色约束
        for character_name, char_constraints in constraints.get("characters", {}).items():
            lines.append(f"角色 {character_name} 的约束：")
            for key, value in char_constraints.items():
                if key.startswith("must_start_with_"):
                    constraint_name = key.replace("must_start_with_", "")
                    lines.append(f"  - 必须以 {constraint_name}: {value} 开始")

        # 添加相机约束
        if "camera" in constraints:
            lines.append("相机约束：")
            camera_constraints = constraints["camera"]
            if "recommended_shot_type" in camera_constraints:
                lines.append(f"  - 推荐镜头类型: {camera_constraints['recommended_shot_type']}")
            if "recommended_angle" in camera_constraints:
                lines.append(f"  - 推荐角度: {camera_constraints['recommended_angle']}")

        return "\n".join(lines)

    def _generate_shot_with_rules(self,
                                  segment: Dict[str, Any],
                                  continuity_constraints: Dict[str, Any],
                                  scene_context: Dict[str, Any],
                                  style: str,
                                  shot_id: int) -> Dict[str, Any]:
        """使用规则生成分镜（当LLM不可用时）"""
        actions = segment.get("actions", [])
        characters = list(continuity_constraints.get("characters", {}).keys())

        # 生成中文描述
        chinese_description = f"场景：{scene_context.get('location', '')}，{scene_context.get('time', '')}。"
        for action in actions:
            if "dialogue" in action:
                chinese_description += f"{action['character']}（{action['emotion']}）说：{action['dialogue']}。"
            else:
                chinese_description += f"{action['character']} {action.get('action', '')}。"

        # 生成英文提示词
        style_prefix = self._get_style_prefix(style)
        ai_prompt = f"{style_prefix} A scene in {scene_context.get('location', 'a place')} at {scene_context.get('time', 'some time')}. "

        for action in actions:
            character = action['character']
            if "dialogue" in action:
                emotion = action.get('emotion', 'neutral')
                dialogue = action['dialogue']
                ai_prompt += f"A person named {character} says '{dialogue}' with {emotion} expression. "
            else:
                action_desc = action.get('action', 'does something')
                emotion = action.get('emotion', 'neutral')
                ai_prompt += f"A person named {character} {action_desc} with {emotion} expression. "

        # 生成相机信息
        camera = {
            "shot_type": "medium shot",
            "angle": "eye-level",
            "movement": "static"
        }

        # 生成初始状态和结束状态
        initial_state = []
        final_state = []

        for character in characters:
            char_constraints = continuity_constraints["characters"][character]

            initial_state.append({
                "character_name": character,
                "pose": char_constraints.get("must_start_with_pose", "standing"),
                "position": char_constraints.get("must_start_with_position", "center"),
                "holding": char_constraints.get("must_start_with_holding", "nothing"),
                "emotion": char_constraints.get("must_start_with_emotion", "neutral"),
                "appearance": f"A person named {character}"
            })

            # 简单的结束状态（可以根据动作更新）
            final_state.append({
                "character_name": character,
                "pose": char_constraints.get("must_start_with_pose", "standing"),
                "position": char_constraints.get("must_start_with_position", "center"),
                "gaze_direction": "forward",
                "emotion": char_constraints.get("must_start_with_emotion", "neutral"),
                "holding": char_constraints.get("must_start_with_holding", "nothing")
            })

        return {
            "chinese_description": chinese_description,
            "ai_prompt": ai_prompt,
            "camera": camera,
            "initial_state": initial_state,
            "final_state": final_state
        }

    def _get_style_prefix(self, style: str) -> str:
        """获取风格前缀"""
        style_mapping = {
            "realistic": "Realistic, high detail, natural lighting,",
            "anime": "Anime style, colorful, expressive, 2D animation,",
            "cinematic": "Cinematic, professional lighting, shallow depth of field,",
            "cartoon": "Cartoon style, exaggerated features, vibrant colors,"
        }
        return style_mapping.get(style, "Detailed, realistic,")

    def _extract_characters_in_frame(self, shot_data: Dict[str, Any]) -> List[str]:
        """提取画面中的角色"""
        characters = set()

        # 从初始状态提取
        for state in shot_data.get("initial_state", []):
            if "character_name" in state:
                characters.add(state["character_name"])

        return list(characters)

    def _generate_continuity_anchor(self, shot_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成连续性锚点"""
        anchors = []

        # 从结束状态生成锚点
        for state in shot_data.get("final_state", []):
            anchor = {
                "character_name": state.get("character_name", ""),
                "pose": state.get("pose", "unknown"),
                "position": state.get("position", "unknown"),
                "gaze_direction": state.get("gaze_direction", "unknown"),
                "emotion": state.get("emotion", "unknown"),
                "holding": state.get("holding", "unknown")
            }
            anchors.append(anchor)

        return anchors

    def _get_default_shot(self,
                          segment: Dict[str, Any],
                          scene_context: Dict[str, Any],
                          style: str,
                          shot_id: int) -> Dict[str, Any]:
        """获取默认分镜（当生成失败时），确保包含所有必要字段以满足Pydantic验证"""
        # 从segment和scene_context中提取有用信息
        actions = segment.get("actions", [])
        location = scene_context.get("location", "未知位置")
        time = scene_context.get("time", "未知时间")
        atmosphere = scene_context.get("atmosphere", "未知氛围")

        # 提取角色信息
        characters = []
        dialogue = ""
        for action in actions:
            character_name = action.get("character", "角色")
            if character_name not in characters:
                characters.append(character_name)
            if "dialogue" in action:
                dialogue += f"{character_name}: {action['dialogue']}\n"

        if not characters:
            characters = ["默认角色"]

        # 计算时间信息
        start_time = (shot_id - 1) * 5
        end_time = shot_id * 5
        duration = end_time - start_time

        # 生成完整的默认分镜，确保包含所有Pydantic验证所需字段
        return {
            # 基础信息
            "shot_id": str(shot_id),  # 确保是字符串类型
            "time_range_sec": [(shot_id - 1) * 5, shot_id * 5],
            "scene_context": scene_context,
            "start_time": start_time,  # 添加必要的时间字段
            "end_time": end_time,
            "duration": duration,

            # 描述字段
            "chinese_description": f"场景：{location}，{time}，{atmosphere}。分镜生成失败，使用默认描述。",
            "ai_prompt": f"Default shot of {location} at {time}",
            "description": f"场景：{location}，{time}，{atmosphere}。分镜生成失败，使用默认描述。",
            "prompt_en": f"Default shot of {location} at {time}, {atmosphere}",

            # 相机信息
            "camera": {
                "shot_type": "medium shot",
                "angle": "eye-level",
                "movement": "static"
            },
            "camera_angle": "medium_shot",  # 添加必要的相机角度字段

            # 角色相关
            "characters_in_frame": characters,
            "characters": characters,  # 添加必要的角色字段
            "dialogue": dialogue.strip(),  # 添加对话字段

            # 状态信息
            "initial_state": [],
            "final_state": [],
            "continuity_anchor": [],
            "continuity_anchors": [],  # 添加必要的连续性锚点字段
            "final_continuity_state": {}  # 确保包含final_continuity_state字段，为字典类型
        }
