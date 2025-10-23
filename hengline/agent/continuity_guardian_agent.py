# -*- coding: utf-8 -*-
"""
@FileName: continuity_guardian_agent.py
@Description: 连续性守护智能体，负责跟踪角色状态，生成/验证连续性锚点
@Author: HengLine
@Time: 2025/10 - 2025/11
"""
from typing import Dict, List, Any, Optional

from hengline.logger import debug, warning


class ContinuityGuardianAgent:
    """连续性守护智能体"""

    def __init__(self):
        """初始化连续性守护智能体"""
        # 角色状态记忆
        self.character_states = {}

        # 默认角色外观
        self.default_appearances = {
            "pose": "standing",
            "position": "center of frame",
            "emotion": "neutral",
            "gaze_direction": "forward",
            "holding": "nothing"
        }

    def generate_continuity_constraints(self,
                                        segment: Dict[str, Any],
                                        prev_continuity_state: Optional[Dict[str, Any]] = None,
                                        scene_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        生成连续性约束条件
        
        Args:
            segment: 当前分段
            prev_continuity_state: 上一段的连续性状态
            scene_context: 场景上下文
            
        Returns:
            连续性约束条件
        """
        info(f"生成连续性约束，分段ID: {segment.get('id')}")

        # 初始化结果
        continuity_constraints = {
            "characters": {},
            "scene": scene_context or {},
            "camera": {}
        }

        # 如果有上一段的状态，加载它
        if prev_continuity_state:
            self._load_prev_state(prev_continuity_state)

        # 获取当前分段中的角色
        characters_in_segment = self._extract_characters(segment)

        # 为每个角色生成连续性约束
        for character_name in characters_in_segment:
            # 获取角色的最新状态
            character_state = self._get_character_state(character_name)

            # 根据当前动作更新状态
            current_actions = [a for a in segment.get('actions', []) if a.get('character') == character_name]
            updated_state = self._update_character_state(character_state, current_actions)

            # 生成约束
            constraints = self._generate_character_constraints(character_name, updated_state)
            continuity_constraints["characters"][character_name] = constraints

            # 更新记忆中的状态
            self.character_states[character_name] = updated_state

        # 生成场景和相机约束
        continuity_constraints["camera"] = self._generate_camera_constraints(segment)

        debug(f"连续性约束生成完成: {continuity_constraints}")
        return continuity_constraints

    def extract_continuity_anchor(self,
                                  segment: Dict[str, Any],
                                  generated_shot: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从生成的分镜中提取连续性锚点
        
        Args:
            segment: 分段信息
            generated_shot: 生成的分镜
            
        Returns:
            连续性锚点列表
        """
        debug(f"提取连续性锚点，分镜ID: {generated_shot.get('shot_id')}")

        anchors = []

        # 从分镜中提取角色状态
        characters_in_frame = generated_shot.get("characters_in_frame", [])

        for character_name in characters_in_frame:
            # 构建锚点
            anchor = {
                "character_name": character_name,
                "pose": "unknown",
                "position": "unknown",
                "gaze_direction": "unknown",
                "emotion": "unknown",
                "holding": "unknown"
            }

            # 从final_state提取信息
            if "final_state" in generated_shot:
                for state in generated_shot["final_state"]:
                    if state.get("character_name") == character_name:
                        anchor.update({
                            "pose": state.get("pose", "unknown"),
                            "position": state.get("position", "unknown"),
                            "gaze_direction": state.get("gaze_direction", "unknown"),
                            "emotion": state.get("emotion", "unknown"),
                            "holding": state.get("holding", "unknown")
                        })
                        break

            # 如果没有final_state，尝试从continuity_anchor提取
            elif "continuity_anchor" in generated_shot:
                for existing_anchor in generated_shot["continuity_anchor"]:
                    if existing_anchor.get("character_name") == character_name:
                        anchor.update(existing_anchor)
                        break

            anchors.append(anchor)

        debug(f"连续性锚点提取完成: {anchors}")
        return anchors

    def verify_continuity(self,
                          prev_anchor: List[Dict[str, Any]],
                          current_constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证连续性，检查是否有不一致的地方
        
        Args:
            prev_anchor: 上一段的连续性锚点
            current_constraints: 当前段的连续性约束
            
        Returns:
            验证结果和修正建议
        """
        debug("验证连续性")

        issues = []
        suggestions = []

        # 创建角色锚点映射
        prev_anchor_map = {a["character_name"]: a for a in prev_anchor}

        # 检查每个角色的连续性
        for character_name, constraints in current_constraints["characters"].items():
            if character_name in prev_anchor_map:
                prev_state = prev_anchor_map[character_name]

                # 检查姿势连续性
                if prev_state.get("pose") != constraints.get("must_start_with_pose"):
                    issues.append(f"角色 {character_name} 姿势不连续")
                    suggestions.append(f"修正 {character_name} 的初始姿势为: {prev_state.get('pose')}")

                # 检查位置连续性
                if prev_state.get("position") != constraints.get("must_start_with_position"):
                    issues.append(f"角色 {character_name} 位置不连续")
                    suggestions.append(f"修正 {character_name} 的初始位置为: {prev_state.get('position')}")

                # 检查情绪连续性
                if prev_state.get("emotion") != constraints.get("must_start_with_emotion"):
                    # 情绪可以有变化，但应该是合理的过渡
                    if not self._is_emotion_transition_valid(prev_state.get("emotion"), constraints.get("must_start_with_emotion")):
                        issues.append(f"角色 {character_name} 情绪变化不合理")
                        suggestions.append(f"建议添加情绪过渡")

        result = {
            "is_continuous": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions
        }

        if issues:
            warning(f"连续性验证发现问题: {issues}")
        else:
            debug("连续性验证通过")

        return result

    def _load_prev_state(self, prev_continuity_state: List[Dict[str, Any]]):
        """加载上一段的连续性状态"""
        for state in prev_continuity_state:
            character_name = state.get("character_name")
            if character_name:
                self.character_states[character_name] = state

    def _extract_characters(self, segment: Dict[str, Any]) -> List[str]:
        """提取分段中的所有角色"""
        characters = set()
        for action in segment.get("actions", []):
            if "character" in action:
                characters.add(action["character"])
        return list(characters)

    def _get_character_state(self, character_name: str) -> Dict[str, Any]:
        """获取角色的当前状态"""
        if character_name in self.character_states:
            return self.character_states[character_name].copy()
        else:
            # 返回默认状态
            return {
                "character_name": character_name,
                **self.default_appearances
            }

    def _update_character_state(self, state: Dict[str, Any], actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """根据动作更新角色状态"""
        updated_state = state.copy()

        for action in actions:
            # 更新动作相关状态
            if "action" in action:
                action_text = action["action"]

                # 更新姿势
                if "坐在" in action_text:
                    updated_state["pose"] = "sitting"
                elif "站在" in action_text:
                    updated_state["pose"] = "standing"
                elif "躺着" in action_text:
                    updated_state["pose"] = "lying"
                elif "低头" in action_text:
                    updated_state["gaze_direction"] = "downward"
                elif "抬头" in action_text:
                    updated_state["gaze_direction"] = "upward"
                elif "看向" in action_text or "看见" in action_text:
                    updated_state["gaze_direction"] = "toward object"

                # 更新位置
                if "靠窗" in action_text:
                    updated_state["position"] = "by window"
                elif "门口" in action_text:
                    updated_state["position"] = "near entrance"
                elif "桌" in action_text:
                    updated_state["position"] = "at table"

                # 更新手持物品
                if "手机" in action_text:
                    updated_state["holding"] = "smartphone"
                elif "咖啡" in action_text:
                    updated_state["holding"] = "coffee cup"

            # 更新情绪
            if "emotion" in action:
                updated_state["emotion"] = action["emotion"]

        return updated_state

    def _generate_character_constraints(self, character_name: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """生成角色的连续性约束"""
        return {
            "must_start_with_pose": state.get("pose", "unknown"),
            "must_start_with_position": state.get("position", "unknown"),
            "must_start_with_emotion": state.get("emotion", "unknown"),
            "must_start_with_gaze": state.get("gaze_direction", "unknown"),
            "must_start_with_holding": state.get("holding", "unknown"),
            "character_description": self._generate_character_description(character_name, state)
        }

    def _generate_character_description(self, character_name: str, state: Dict[str, Any]) -> str:
        """生成角色描述"""
        # 这里可以根据需要生成更详细的角色描述
        # 暂时使用简单的描述模板
        return f"{character_name}, {state.get('pose')}, {state.get('emotion')}"

    def _generate_camera_constraints(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """生成相机约束"""
        # 简单的相机约束逻辑
        num_actions = len(segment.get("actions", []))

        if num_actions == 1:
            # 单个动作，使用中景或特写
            shot_type = "medium shot"
        else:
            # 多个动作，使用中景或全景
            shot_type = "medium shot"

        return {
            "recommended_shot_type": shot_type,
            "recommended_angle": "eye-level",
            "must_maintain_consistency": True
        }

    def _is_emotion_transition_valid(self, prev_emotion: str, current_emotion: str) -> bool:
        """检查情绪过渡是否合理"""
        # 定义合理的情绪过渡对
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

        # 如果当前情绪在合理过渡列表中，或者没有定义过渡规则，则认为有效
        if prev_emotion in valid_transitions:
            return current_emotion in valid_transitions[prev_emotion]

        return True
