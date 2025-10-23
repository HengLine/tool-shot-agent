# -*- coding: utf-8 -*-
"""
@FileName: script_parser_agent.py
@Description: 剧本解析智能体，负责解析原始剧本，提取结构化元素
@Author: HengLine
@Time: 2025/10 - 2025/11
"""
import json
import re
from typing import Dict, List, Any
from pathlib import Path

from hengline.logger import debug, error, warning
from hengline.prompts.prompts_manager import PromptManager
from utils.log_utils import print_log_exception


class ScriptParserAgent:
    """剧本解析智能体"""

    def __init__(self, llm=None):
        """
        初始化剧本解析智能体
        
        Args:
            llm: 语言模型实例
        """
        self.llm = llm
        self.scene_pattern = re.compile(r'场景：(.+)，(.+)，(.+)')
        self.character_pattern = re.compile(r'([^（]+)（([^）]+)）：(.+)')
        self.action_pattern = re.compile(r'([^（]+)坐在([^，]+)，(.*)')

    def parse_script(self, script_text: str) -> Dict[str, Any]:
        """
        解析原始剧本文本
        
        Args:
            script_text: 原始剧本文本
            
        Returns:
            结构化的剧本对象
        """
        debug(f"开始解析剧本: {script_text[:100]}...")

        try:
            # 初始化结果结构
            result = {
                "scenes": []
            }

            # 按行分割剧本
            lines = script_text.strip().split('\n')

            current_scene = None
            scene_buffer = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 检测场景行
                scene_match = self.scene_pattern.match(line)
                if scene_match:
                    # 如果已经有场景在处理，先保存
                    if current_scene:
                        self._process_scene_buffer(scene_buffer, current_scene)
                        result["scenes"].append(current_scene)

                    # 创建新场景
                    location, time, atmosphere = scene_match.groups()
                    current_scene = {
                        "location": location,
                        "time": time,
                        "atmosphere": atmosphere,
                        "actions": []
                    }
                    scene_buffer = []
                # 检测对话行
                elif self.character_pattern.match(line):
                    char_match = self.character_pattern.match(line)
                    if char_match:
                        character, emotion, dialogue = char_match.groups()
                        action = {
                            "character": character,
                            "dialogue": dialogue,
                            "emotion": emotion
                        }
                        scene_buffer.append(action)
                # 检测动作行
                elif any(keyword in line for keyword in ["坐在", "站在", "看见", "走", "跑", "愣住"]):
                    # 尝试提取角色和动作
                    parts = line.split('，')
                    if parts:
                        character = parts[0]
                        action_description = ','.join(parts[1:])
                        action = {
                            "character": character,
                            "action": action_description,
                            "emotion": "平静"  # 默认情绪
                        }
                        scene_buffer.append(action)
                else:
                    # 其他情况添加到缓冲区
                    scene_buffer.append(line)

            # 处理最后一个场景
            if current_scene:
                self._process_scene_buffer(scene_buffer, current_scene)
                result["scenes"].append(current_scene)

            # 如果没有检测到场景，使用默认场景
            if not result["scenes"]:
                result["scenes"].append({
                    "location": "默认场景",
                    "time": "默认时间",
                    "atmosphere": "默认氛围",
                    "actions": self._parse_raw_actions(script_text)
                })

            debug(f"剧本解析完成，提取了 {len(result['scenes'])} 个场景")
            return result

        except Exception as e:
            error(f"剧本解析失败: {str(e)}")
            # 返回默认结构
            return {
                "scenes": [{
                    "location": "未知",
                    "time": "未知",
                    "atmosphere": "未知",
                    "actions": []
                }]
            }

    def _process_scene_buffer(self, buffer: List[Any], scene: Dict[str, Any]):
        """处理场景缓冲区中的内容"""
        for item in buffer:
            if isinstance(item, dict):
                scene["actions"].append(item)
            elif isinstance(item, str):
                # 尝试解析文本行
                actions = self._parse_raw_actions(item)
                scene["actions"].extend(actions)

    def _parse_raw_actions(self, text: str) -> List[Dict[str, Any]]:
        """解析原始文本行中的动作"""
        actions = []
        # 简单的动作解析规则
        action_keywords = [
            ("坐在", "平静"),
            ("站在", "平静"),
            ("看见", "惊讶"),
            ("走", "平静"),
            ("跑", "匆忙"),
            ("愣住", "震惊"),
            ("低头", "沉思"),
            ("抬头", "注意"),
        ]

        # 尝试提取角色名
        parts = text.split('，', 1)
        if len(parts) >= 2:
            character = parts[0]
            action_text = parts[1]

            # 查找动作关键词
            for keyword, emotion in action_keywords:
                if keyword in action_text:
                    actions.append({
                        "character": character,
                        "action": action_text,
                        "emotion": emotion
                    })
                    break
            else:
                # 未找到关键词，使用默认
                actions.append({
                    "character": character,
                    "action": action_text,
                    "emotion": "平静"
                })

        return actions

    def enhance_with_llm(self, structured_script: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用LLM增强解析结果
        
        Args:
            structured_script: 结构化的剧本数据
            
        Returns:
            增强后的结构化剧本数据
        """
        if not self.llm:
            debug("未配置LLM，跳过增强步骤")
            return structured_script

        try:
            # 使用PromptManager获取提示词
            prompt_manager = PromptManager(prompt_dir=Path(__file__).parent.parent)
            prompt = prompt_manager.get_prompt("script_parser")

            # 填充提示词模板
            filled_prompt = prompt.format(raw_script=json.dumps(structured_script, ensure_ascii=False))

            # 调用LLM
            debug("开始调用LLM增强剧本解析结果")
            response = self.llm.invoke(filled_prompt)

            # 尝试解析JSON响应
            enhanced_script = json.loads(response)
            debug("LLM增强成功，返回增强后的剧本结构")
            return enhanced_script
        except json.JSONDecodeError as e:
            warning(f"LLM增强失败：响应不是有效的JSON格式: {str(e)}")
        except Exception as e:
            print_log_exception()
            # 检查是否是API密钥错误
            if "API key" in str(e) or "401" in str(e):
                warning(f"LLM增强失败：API密钥错误或权限不足: {str(e)}")
            else:
                warning(f"LLM增强失败，返回原始解析结果: {str(e)}")

            # 手动增强剧本结构，添加一些基本信息
            enhanced_structured = structured_script.copy()
            for scene in enhanced_structured.get("scenes", []):
                # 确保场景有完整的基本信息
                if not scene.get("location"):
                    scene["location"] = "默认场景"
                if not scene.get("time"):
                    scene["time"] = "默认时间"
                if not scene.get("atmosphere"):
                    scene["atmosphere"] = "默认氛围"
                # 确保每个动作都有情绪
                for action in scene.get("actions", []):
                    if "emotion" not in action:
                        action["emotion"] = "平静"
            return enhanced_structured
