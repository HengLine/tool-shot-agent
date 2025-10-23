# -*- coding: utf-8 -*-
"""
@FileName: qa_agent.py
@Description: 分镜审查智能体，负责审查分镜质量和连续性
@Author: HengLine
@Time: 2025/10 - 2025/11
"""
import json
from pathlib import Path
from typing import Dict, List, Any

from hengline.logger import debug, warning
from hengline.prompts.prompts_manager import PromptManager


class QAAgent:
    """质量审查智能体"""

    def __init__(self, llm=None):
        """
        初始化质量审查智能体
        
        Args:
            llm: 语言模型实例（可选，用于高级审查）
        """
        self.llm = llm
        self.max_shot_duration = 5.5  # 最大允许时长（秒）

    def review_single_shot(self, shot: Dict[str, Any], segment: Dict[str, Any]) -> Dict[str, Any]:
        """
        审查单个分镜
        
        Args:
            shot: 分镜对象
            segment: 对应的分段信息
            
        Returns:
            审查结果
        """
        debug(f"审查分镜，ID: {shot.get('shot_id')}")

        issues = []
        suggestions = []

        # 检查基本字段
        basic_check = self._check_basic_fields(shot)
        issues.extend(basic_check["issues"])
        suggestions.extend(basic_check["suggestions"])

        # 检查时长
        duration_check = self._check_duration(shot)
        issues.extend(duration_check["issues"])
        suggestions.extend(duration_check["suggestions"])

        # 检查角色状态
        character_check = self._check_character_states(shot)
        issues.extend(character_check["issues"])
        suggestions.extend(character_check["suggestions"])

        # 检查提示词质量
        prompt_check = self._check_prompt_quality(shot)
        issues.extend(prompt_check["issues"])
        suggestions.extend(prompt_check["suggestions"])

        # 如果有LLM，进行高级审查
        if self.llm:
            advanced_check = self._advanced_review_with_llm(shot, segment)
            issues.extend(advanced_check["issues"])
            suggestions.extend(advanced_check["suggestions"])

        result = {
            "shot_id": shot.get("shot_id"),
            "is_valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions
        }

        if issues:
            warning(f"分镜 {shot.get('shot_id')} 审查发现问题: {issues}")
        else:
            debug(f"分镜 {shot.get('shot_id')} 审查通过")

        return result

    def review_shot_sequence(self, shots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        审查分镜序列的连续性
        
        Args:
            shots: 分镜列表
            
        Returns:
            审查结果
        """
        debug(f"审查分镜序列，共 {len(shots)} 个分镜")

        continuity_issues = []
        continuity_suggestions = []

        # 检查分镜之间的连续性
        for i in range(1, len(shots)):
            prev_shot = shots[i - 1]
            current_shot = shots[i]

            # 检查时间连续性
            time_continuity = self._check_time_continuity(prev_shot, current_shot)
            if not time_continuity["is_continuous"]:
                continuity_issues.append(f"分镜 {prev_shot.get('shot_id')} 和 {current_shot.get('shot_id')} 时间不连续")
                continuity_suggestions.extend(time_continuity["suggestions"])

            # 检查角色连续性
            character_continuity = self._check_character_continuity(prev_shot, current_shot)
            continuity_issues.extend(character_continuity["issues"])
            continuity_suggestions.extend(character_continuity["suggestions"])

            # 检查场景连续性
            scene_continuity = self._check_scene_continuity(prev_shot, current_shot)
            if not scene_continuity["is_continuous"]:
                continuity_issues.append(f"分镜 {prev_shot.get('shot_id')} 和 {current_shot.get('shot_id')} 场景不连续")
                continuity_suggestions.extend(scene_continuity["suggestions"])

        # 检查整体叙事连贯性
        narrative_check = self._check_narrative_coherence(shots)
        continuity_issues.extend(narrative_check["issues"])
        continuity_suggestions.extend(narrative_check["suggestions"])

        result = {
            "total_shots": len(shots),
            "has_continuity_issues": len(continuity_issues) > 0,
            "continuity_issues": continuity_issues,
            "continuity_suggestions": continuity_suggestions,
            "overall_assessment": "通过" if len(continuity_issues) == 0 else "需要修正"
        }

        if continuity_issues:
            warning(f"分镜序列审查发现连续性问题: {continuity_issues}")
        else:
            debug("分镜序列连续性审查通过")

        return result

    def _check_basic_fields(self, shot: Dict[str, Any]) -> Dict[str, Any]:
        """检查基本字段是否完整"""
        issues = []
        suggestions = []

        required_fields = [
            "shot_id", "chinese_description", "ai_prompt",
            "camera", "characters_in_frame"
        ]

        for field in required_fields:
            if field not in shot or not shot[field]:
                issues.append(f"缺少必要字段: {field}")
                suggestions.append(f"请添加 {field}")

        return {"issues": issues, "suggestions": suggestions}

    def _check_duration(self, shot: Dict[str, Any]) -> Dict[str, Any]:
        """检查分镜时长"""
        issues = []
        suggestions = []

        time_range = shot.get("time_range_sec", [0, 5])
        duration = time_range[1] - time_range[0]

        if duration > self.max_shot_duration:
            issues.append(f"分镜时长长于允许的最大值 {self.max_shot_duration} 秒")
            suggestions.append("请缩短分镜时长或拆分为多个分镜")

        return {"issues": issues, "suggestions": suggestions}

    def _check_character_states(self, shot: Dict[str, Any]) -> Dict[str, Any]:
        """检查角色状态是否合理"""
        issues = []
        suggestions = []

        # 检查初始状态和结束状态
        initial_state = shot.get("initial_state", [])
        final_state = shot.get("final_state", [])
        characters_in_frame = shot.get("characters_in_frame", [])

        # 检查角色列表一致性
        state_characters = set(s.get("character_name") for s in initial_state + final_state)
        frame_characters = set(characters_in_frame)

        if state_characters != frame_characters:
            issues.append("角色列表不一致")
            suggestions.append("确保 initial_state、final_state 和 characters_in_frame 中的角色一致")

        # 检查角色状态的合理性
        for state in initial_state + final_state:
            if "pose" not in state:
                issues.append(f"角色 {state.get('character_name')} 缺少姿势信息")
            if "emotion" not in state:
                issues.append(f"角色 {state.get('character_name')} 缺少情绪信息")
            if "position" not in state:
                issues.append(f"角色 {state.get('character_name')} 缺少位置信息")

        return {"issues": issues, "suggestions": suggestions}

    def _check_prompt_quality(self, shot: Dict[str, Any]) -> Dict[str, Any]:
        """检查提示词质量"""
        issues = []
        suggestions = []

        ai_prompt = shot.get("ai_prompt", "")

        # 检查提示词长度
        if len(ai_prompt) < 20:
            issues.append("AI提示词过短")
            suggestions.append("请添加更多细节到提示词")

        # 检查是否包含必要元素
        essential_elements = ["shot", "lighting", "style"]
        for element in essential_elements:
            if element not in ai_prompt.lower():
                suggestions.append(f"建议在提示词中添加 {element} 相关描述")

        return {"issues": issues, "suggestions": suggestions}

    def _advanced_review_with_llm(self, shot: Dict[str, Any], segment: Dict[str, Any]) -> Dict[str, Any]:
        """使用LLM进行高级审查"""
        try:
            # 使用PromptManager获取提示词，使用正确的提示词目录路径
            prompt_manager = PromptManager(prompt_dir=Path(__file__).parent.parent)
            prompt = prompt_manager.get_prompt("qa_review")

            # 填充提示词模板
            filled_prompt = prompt.format(
                shot_info=json.dumps(shot, ensure_ascii=False),
                segment_info=json.dumps(segment, ensure_ascii=False)
            )

            # 调用LLM
            response = self.llm.invoke(filled_prompt)

            # 处理可能的响应对象
            response_text = response.content if hasattr(response, 'content') else response

            # 检查响应是否为空
            if not response_text or not str(response_text).strip():
                warning("LLM高级审查响应为空")
                return {"issues": [], "suggestions": []}

            # 确保response_text是字符串
            response_text = str(response_text).strip()

            # 尝试提取纯JSON部分（移除可能的前后文本）
            if '{' in response_text and '}' in response_text:
                # 提取第一个{到最后一个}之间的内容
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                response_text = response_text[start_idx:end_idx]

            result = json.loads(response_text)
            return result
        except json.JSONDecodeError as e:
            warning(f"LLM高级审查JSON解析失败: {str(e)}, 响应文本: {str(response_text)[:100]}...")
            return {"issues": [], "suggestions": []}
        except Exception as e:
            warning(f"LLM高级审查失败: {str(e)}")
            return {"issues": [], "suggestions": []}

    def _check_time_continuity(self, prev_shot: Dict[str, Any], current_shot: Dict[str, Any]) -> Dict[str, Any]:
        """检查时间连续性"""
        prev_end = prev_shot.get("time_range_sec", [0, 5])[1]
        current_start = current_shot.get("time_range_sec", [5, 10])[0]

        is_continuous = abs(prev_end - current_start) < 0.1

        suggestions = []
        if not is_continuous:
            suggestions.append("修正时间范围以确保连续")

        return {
            "is_continuous": is_continuous,
            "suggestions": suggestions
        }

    def _check_character_continuity(self, prev_shot: Dict[str, Any], current_shot: Dict[str, Any]) -> Dict[str, Any]:
        """检查角色连续性"""
        issues = []
        suggestions = []

        # 获取前一个分镜的结束状态和当前分镜的初始状态
        prev_final_state = {s.get("character_name"): s for s in prev_shot.get("final_state", [])}
        current_initial_state = {s.get("character_name"): s for s in current_shot.get("initial_state", [])}

        # 检查共同角色
        common_characters = set(prev_final_state.keys()) & set(current_initial_state.keys())

        for character in common_characters:
            prev_state = prev_final_state[character]
            current_state = current_initial_state[character]

            # 检查位置连续性
            if prev_state.get("position") != current_state.get("position"):
                issues.append(f"角色 {character} 位置不连续")
                suggestions.append(f"确保 {character} 的位置从 '{prev_state.get('position')}' 平滑过渡到 '{current_state.get('position')}'")

            # 检查情绪连续性
            prev_emotion = prev_state.get("emotion")
            current_emotion = current_state.get("emotion")
            if prev_emotion != current_emotion:
                # 检查是否是合理的情绪过渡
                if not self._is_valid_emotion_transition(prev_emotion, current_emotion):
                    issues.append(f"角色 {character} 情绪过渡不合理")
                    suggestions.append(f"建议添加 {character} 的情绪过渡描述")

        return {"issues": issues, "suggestions": suggestions}

    def _check_scene_continuity(self, prev_shot: Dict[str, Any], current_shot: Dict[str, Any]) -> Dict[str, Any]:
        """检查场景连续性"""
        prev_scene = prev_shot.get("scene_context", {})
        current_scene = current_shot.get("scene_context", {})

        is_continuous = True
        suggestions = []

        # 检查位置、时间、氛围是否连续
        if prev_scene.get("location") != current_scene.get("location"):
            is_continuous = False
            suggestions.append("场景位置发生变化，请确保有合理的转场")

        if prev_scene.get("time") != current_scene.get("time"):
            is_continuous = False
            suggestions.append("场景时间发生变化，请添加时间过渡说明")

        return {
            "is_continuous": is_continuous,
            "suggestions": suggestions
        }

    def _check_narrative_coherence(self, shots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """检查叙事连贯性"""
        issues = []
        suggestions = []

        # 简单的叙事连贯性检查
        total_duration = len(shots) * 5
        if total_duration > 300:  # 超过5分钟
            issues.append("视频总时长过长，可能影响叙事连贯性")
            suggestions.append("考虑精简内容或分章节制作")

        # 检查角色出现频率
        character_counts = {}
        for shot in shots:
            for character in shot.get("characters_in_frame", []):
                character_counts[character] = character_counts.get(character, 0) + 1

        # 检查是否有角色突然消失
        for i in range(1, len(shots)):
            prev_characters = set(shots[i - 1].get("characters_in_frame", []))
            current_characters = set(shots[i].get("characters_in_frame", []))

            disappeared_characters = prev_characters - current_characters
            for character in disappeared_characters:
                # 如果角色出现过多次但突然消失，可能是问题
                if character_counts.get(character, 0) > 2:
                    issues.append(f"角色 {character} 突然消失")
                    suggestions.append(f"请添加 {character} 的离开场景")

        return {"issues": issues, "suggestions": suggestions}

    def _is_valid_emotion_transition(self, prev_emotion: str, current_emotion: str) -> bool:
        """检查情绪过渡是否合理"""
        # 定义有效的情绪过渡对
        valid_transitions = {
            "平静": ["惊讶", "注意", "思考", "微笑"],
            "惊讶": ["震惊", "恐惧", "困惑", "平静"],
            "震惊": ["恐惧", "悲伤", "愤怒", "平静"],
            "愤怒": ["攻击", "冷静", "悲伤"],
            "悲伤": ["哭泣", "平静", "接受"],
            "快乐": ["大笑", "平静", "兴奋"],
            "紧张": ["焦虑", "恐惧", "平静"],
            "恐惧": ["逃跑", "震惊", "平静"],
        }

        if prev_emotion in valid_transitions:
            return current_emotion in valid_transitions[prev_emotion] or current_emotion == prev_emotion

        return True
