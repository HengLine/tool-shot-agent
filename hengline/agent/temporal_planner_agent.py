# -*- coding: utf-8 -*-
"""
@FileName: temporal_planner_agent.py
@Description: 时序规划智能体，负责将剧本按5秒粒度切分，估算动作时长
@Author: HengLine
@Time: 2025/10 - 2025/11
"""
from typing import List, Dict, Any

from hengline.logger import debug, warning


class TemporalPlannerAgent:
    """时序规划智能体"""

    def __init__(self):
        """初始化时序规划智能体"""
        # 动作时长估算库（秒）
        self.action_duration_library = {
            # 基本动作
            "坐在": 2.0,
            "站在": 2.0,
            "躺着": 2.0,
            "低头": 1.0,
            "抬头": 1.0,
            "转身": 1.5,
            "看向": 1.0,
            "看见": 1.0,
            "愣住": 2.0,
            "发抖": 2.0,
            # 移动动作
            "走": 2.0,
            "慢走": 3.0,
            "快走": 1.5,
            "跑": 1.0,
            "进入": 3.0,
            "离开": 3.0,
            "靠近": 2.5,
            "远离": 2.5,
            # 交互动作
            "说话": 3.0,  # 一句话的平均时长
            "握手": 2.0,
            "拥抱": 3.0,
            "递东西": 2.0,
            "接东西": 1.5,
            "操作手机": 3.0,
            "喝咖啡": 2.0,
            "看书": 3.0,
            # 情绪动作
            "微笑": 1.5,
            "皱眉": 1.0,
            "哭泣": 4.0,
            "大笑": 3.0,
            "愤怒": 2.5,
            "惊讶": 2.0,
        }

        # 默认动作时长
        self.default_duration = 2.0

        # 目标分段时长（秒）
        self.target_segment_duration = 5.0

        # 允许的最大时长偏差（秒）
        self.max_duration_deviation = 0.5

    def plan_timeline(self, structured_script: Dict[str, Any], target_duration: int = None) -> List[Dict[str, Any]]:
        """
        规划剧本的时序分段
        
        Args:
            structured_script: 结构化的剧本
            target_duration: 目标分段时长（秒）
            
        Returns:
            分段计划列表
        """
        debug("开始时序规划")

        if target_duration:
            self.target_segment_duration = target_duration

        segments = []
        current_segment = {
            "id": 1,
            "actions": [],
            "est_duration": 0.0,
            "scene_id": 0
        }

        # 遍历所有场景
        scenes = structured_script.get("scenes", [])
        for scene_idx, scene in enumerate(scenes):
            scene_actions = scene.get("actions", [])
            
            # 确保场景有动作
            if not scene_actions:
                # 如果场景没有动作，创建一个默认动作
                default_action = {
                    "character": "默认角色",
                    "action": "站立",
                    "emotion": "平静"
                }
                scene_actions = [default_action]

            for action in scene_actions:
                action_duration = self._estimate_action_duration(action)

                # 检查是否需要分段
                if current_segment["est_duration"] + action_duration > self.target_segment_duration + self.max_duration_deviation:
                    # 保存当前分段
                    segments.append(current_segment)

                    # 开始新分段
                    current_segment = {
                        "id": len(segments) + 1,
                        "actions": [],
                        "est_duration": 0.0,
                        "scene_id": scene_idx
                    }

                # 添加动作到当前分段
                current_segment["actions"].append(action)
                current_segment["est_duration"] += action_duration
                current_segment["scene_id"] = scene_idx

        # 添加最后一个分段
        if current_segment["actions"]:
            segments.append(current_segment)
        elif scenes:
            # 如果没有任何动作，但有场景，创建一个默认分段
            warning("未找到任何动作，创建默认分段")
            segments.append({
                "id": 1,
                "actions": [{
                    "character": "默认角色",
                    "action": "站立",
                    "emotion": "平静"
                }],
                "est_duration": self.target_segment_duration,
                "scene_id": 0
            })

        # 优化分段
        optimized_segments = self._optimize_segments(segments)
        
        # 确保至少有一个分段
        if not optimized_segments and scenes:
            warning("分段优化后为空，创建保底分段")
            optimized_segments = [{
                "id": 1,
                "actions": [{
                    "character": "默认角色",
                    "action": "站立",
                    "emotion": "平静"
                }],
                "est_duration": self.target_segment_duration,
                "scene_id": 0
            }]

        debug(f"时序规划完成，生成了 {len(optimized_segments)} 个分段")
        return optimized_segments

    def _estimate_action_duration(self, action: Dict[str, Any]) -> float:
        """
        估算单个动作的时长
        
        Args:
            action: 动作字典
            
        Returns:
            估算的时长（秒）
        """
        duration = 0.0

        # 检查是否有对话
        if "dialogue" in action:
            dialogue = action["dialogue"]
            # 基于对话长度估算时长
            words_count = len(dialogue)
            duration += max(2.0, words_count * 0.1)  # 至少2秒，每10个字增加1秒

        # 检查动作描述
        if "action" in action:
            action_text = action["action"]
            action_duration = self._match_action_duration(action_text)
            duration = max(duration, action_duration)

        # 如果没有估算出时长，使用默认值
        if duration == 0.0:
            duration = self.default_duration

        # 根据情绪调整时长
        if "emotion" in action:
            emotion = action["emotion"]
            duration = self._adjust_duration_by_emotion(duration, emotion)

        return duration

    def _match_action_duration(self, action_text: str) -> float:
        """
        匹配动作文本中的关键词，返回对应的时长
        
        Args:
            action_text: 动作描述文本
            
        Returns:
            估算的时长（秒）
        """
        max_duration = self.default_duration

        # 查找匹配的最长关键词
        for keyword, duration in sorted(self.action_duration_library.items(), key=lambda x: len(x[0]), reverse=True):
            if keyword in action_text:
                max_duration = max(max_duration, duration)

        # 检查是否有复合动作
        compound_actions = action_text.split('，')
        if len(compound_actions) > 1:
            # 复合动作，增加时长
            max_duration *= 1.2

        return max_duration

    def _adjust_duration_by_emotion(self, duration: float, emotion: str) -> float:
        """
        根据情绪调整动作时长
        
        Args:
            duration: 原始时长
            emotion: 情绪描述
            
        Returns:
            调整后的时长
        """
        emotion_multipliers = {
            "平静": 1.0,
            "惊讶": 1.2,
            "震惊": 1.5,
            "愤怒": 1.3,
            "悲伤": 1.4,
            "快乐": 0.9,
            "紧张": 1.2,
            "恐惧": 1.3,
            "厌恶": 1.1,
            "困惑": 1.2,
            "焦虑": 1.3,
        }

        multiplier = emotion_multipliers.get(emotion, 1.0)
        return duration * multiplier

    def _optimize_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        优化分段，确保时长合理
        
        Args:
            segments: 原始分段列表
            
        Returns:
            优化后的分段列表
        """
        optimized_segments = []

        for i, segment in enumerate(segments):
            # 检查时长是否过短，最后一个分段允许时长过短
            if segment["est_duration"] < self.target_segment_duration * 0.6 and i < len(segments) - 1:
                warning(f"分段 {segment['id']} 时长过短: {segment['est_duration']}秒")
                # 可以考虑合并到前一个分段，但这里暂时保留

            # 检查时长是否过长
            if segment["est_duration"] > self.target_segment_duration + self.max_duration_deviation:
                warning(f"分段 {segment['id']} 时长过长: {segment['est_duration']}秒")
                # 尝试拆分过长的分段
                split_segments = self._split_long_segment(segment)
                optimized_segments.extend(split_segments)
            else:
                optimized_segments.append(segment)

        # 重新分配ID
        for idx, segment in enumerate(optimized_segments):
            segment["id"] = idx + 1

        return optimized_segments

    def _split_long_segment(self, segment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        拆分过长的分段
        
        Args:
            segment: 过长的分段
            
        Returns:
            拆分后的分段列表
        """
        split_segments = []
        current_split = {
            "id": segment["id"],
            "actions": [],
            "est_duration": 0.0,
            "scene_id": segment["scene_id"]
        }

        for action in segment["actions"]:
            action_duration = self._estimate_action_duration(action)

            if current_split["est_duration"] + action_duration > self.target_segment_duration:
                # 保存当前拆分
                split_segments.append(current_split)

                # 开始新的拆分
                current_split = {
                    "id": segment["id"],  # ID暂时保留原分段ID
                    "actions": [],
                    "est_duration": 0.0,
                    "scene_id": segment["scene_id"]
                }

            current_split["actions"].append(action)
            current_split["est_duration"] += action_duration

        # 添加最后一个拆分
        if current_split["actions"]:
            split_segments.append(current_split)

        return split_segments
