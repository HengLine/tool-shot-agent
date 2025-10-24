# -*- coding: utf-8 -*-
"""
@FileName: script_parser_agent.py
@Description: 优化版剧本解析智能体，将整段中文剧本转换为结构化动作序列
@Author: HengLine
@Time: 2025/10 - 2025/11
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

import jieba
import yaml

from hengline.logger import debug, error, warning
from hengline.tools.result_storage_tool import create_result_storage, save_script_parser_result
# 导入LlamaIndex相关工具
from hengline.tools.script_intelligence_tool import create_script_intelligence
from hengline.tools.script_parser_tool import ScriptParser
from utils.log_utils import print_log_exception


class ScriptParserAgent:
    """优化版剧本解析智能体"""

    def __init__(self,
                 llm=None,
                 embedding_model_name: str = "openai",
                 storage_dir: Optional[str] = None,
                 config_path: Optional[str] = None,
                 output_dir: Optional[str] = None):
        """
        初始化剧本解析智能体
        
        Args:
            llm: 语言模型实例（推荐GPT-4o）
            embedding_model_name: 嵌入模型名称
            storage_dir: 知识库存储目录
            config_path: 配置文件路径，如果为None则使用默认路径
            output_dir: 结果输出目录
        """
        self.llm = llm
        self.embedding_model_name = embedding_model_name
        self.storage_dir = storage_dir
        self.output_dir = output_dir

        # 设置配置文件路径
        self.config_path = config_path or str(Path(__file__).parent.parent / "config" / "script_parser_config.yaml")

        # 初始化基础解析器
        self.script_parser = ScriptParser()

        # 初始化智能分析工具
        try:
            self.script_intel = create_script_intelligence(
                embedding_model_name=embedding_model_name,
                storage_dir=storage_dir
            )
            debug("成功初始化ScriptIntelligence工具")
        except Exception as e:
            warning(f"初始化ScriptIntelligence失败，但将继续使用基础功能: {str(e)}")
            self.script_intel = None

        # 延迟导入以避免循环导入
        from config.config import get_data_output_path
        # 初始化结果存储工具
        self.result_storage = create_result_storage(output_dir or get_data_output_path())

        # 中文NLP相关模式和关键词
        self.initialize_patterns()

    def initialize_patterns(self):
        """初始化中文剧本解析需要的模式和关键词，从配置文件加载"""
        # 默认配置
        default_config = {
            "scene_patterns": [
                '场景[:：]\s*([^，。；\n]+)[，。；]\s*([^，。；\n]+)',
                '地点[:：]\s*([^，。；\n]+)[，。；]\s*时间[:：]\s*([^，。；\n]+)',
                '([^，。；\n]+)[，。；]\s*([^，。；\n]+)\s*[的]?场景',
            ],
            "dialogue_patterns": [
                '([^：]+)[:：]\s*(.+)',
                '([^（）]+)[（(]([^)）]+)[)）][:：]\s*(.+)',
            ],
            "action_emotion_map": {
                "走": "平静", "行走": "平静", "漫步": "轻松", "散步": "悠闲",
                "笑": "开心", "微笑": "愉悦", "哭": "悲伤", "流泪": "伤心",
                "颤抖": "恐惧", "紧张": "紧张", "冷静": "平静", "思考": "专注",
            },
            "time_keywords": {
                "早上": "早晨", "早晨": "早晨", "上午": "上午", "中午": "中午",
                "下午": "下午", "晚上": "晚上", "深夜": "深夜", "凌晨": "凌晨",
            },
            "appearance_keywords": {
                "西装": "穿着正式西装", "休闲装": "穿着休闲服装", "老人": "年长的",
                "年轻人": "年轻的", "男人": "男性", "女人": "女性",
            },
            "location_keywords": {
                "咖啡馆": "咖啡馆", "餐厅": "餐厅", "办公室": "办公室",
            },
            "emotion_keywords": {
                "高兴": ["开心", "高兴", "快乐", "愉快", "欢乐", "兴奋", "太好了", "真棒", "哈哈"],
                "悲伤": ["伤心", "难过", "悲伤", "难过", "哭", "流泪", "痛苦", "可怜", "惨"],
                "愤怒": ["生气", "愤怒", "恼火", "气死了", "混蛋", "该死", "讨厌", "烦"],
                "惊讶": ["啊", "哇", "惊讶", "震惊", "没想到", "真的吗", "什么", "怎么会"],
                "恐惧": ["害怕", "恐惧", "恐怖", "吓死了", "救命", "不要", "危险"],
                "紧张": ["紧张", "忐忑", "不安", "焦虑", "担心", "怎么办", "不会吧"],
                "平静": ["好的", "嗯", "是的", "知道了", "明白", "了解", "好"],
                "疑问": ["为什么", "什么", "哪里", "谁", "怎么", "如何", "是不是", "有没有"]
            },
            "atmosphere_keywords": {
                "温馨": ["温暖", "舒适", "柔和", "愉悦", "快乐", "放松"],
                "正式": ["严肃", "庄重", "严谨", "认真"],
                "轻松": ["愉快", "轻松", "休闲", "自在"],
                "紧张": ["紧张", "焦虑", "不安", "担忧"],
                "浪漫": ["浪漫", "甜蜜", "温馨", "幸福"],
                "悲伤": ["难过", "伤心", "悲伤", "痛苦"],
                "愤怒": ["生气", "愤怒", "恼火", "激动"],
                "惊讶": ["惊讶", "震惊", "意外", "突然"]
            }
        }

        # 尝试从配置文件加载
        config_data = default_config.copy()
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded_config = yaml.safe_load(f)
                # 确保loaded_config不为None
                if loaded_config is not None:
                    # 合并配置，保留默认值作为回退
                    for key in default_config:
                        if key in loaded_config:
                            config_data[key] = loaded_config[key]
            debug(f"成功从配置文件加载剧本解析配置: {self.config_path}")
            # 打印配置信息，用于调试
            print(f"配置加载成功: ")
            print(f"  - 场景识别模式: {len(config_data.get('scene_patterns', []))} 个")
            print(f"  - 对话识别模式: {len(config_data.get('dialogue_patterns', []))} 个")
            print(f"  - 动作情绪映射: {len(config_data.get('action_emotion_map', {}))} 个")
            print(f"  - 角色外观关键词: {len(config_data.get('appearance_keywords', {}))} 个")
            print(f"  - 时段关键词: {len(config_data.get('time_keywords', {}))} 个")
            print(f"  - 地点关键词: {len(config_data.get('location_keywords', {}))} 个")
            print(f"  - 情绪关键词: {len(config_data.get('emotion_keywords', {}))} 个")
            print(f"  - 场景氛围关键词: {len(config_data.get('atmosphere_keywords', {}))} 个")
        except Exception as e:
            warning(f"无法加载配置文件 {self.config_path}，使用默认配置: {str(e)}")

        # 编译正则表达式模式
        self.scene_patterns = []
        for pattern_str in config_data.get('scene_patterns', []):
            try:
                # 注意：这里需要添加r前缀以确保正则表达式中的转义字符正确处理
                self.scene_patterns.append(re.compile(pattern_str))
            except re.error as e:
                warning(f"正则表达式模式编译失败: {pattern_str}, 错误: {str(e)}")

        # 编译对话模式
        self.dialogue_patterns = []
        dialogue_patterns = config_data.get('dialogue_patterns', [])
        for pattern_str in dialogue_patterns:
            try:
                self.dialogue_patterns.append(re.compile(pattern_str))
            except re.error as e:
                warning(f"对话模式编译失败: {pattern_str}, 错误: {str(e)}")

        # 如果对话模式为空，使用默认模式
        if not self.dialogue_patterns:
            self.dialogue_patterns = [
                re.compile(r'([^：]+)[:：]\s*(.+)'),
                re.compile(r'([^（）]+)[（(]([^)）]+)[)）][:：]\s*(.+)')
            ]

        # 加载映射和关键词
        self.action_emotion_map = config_data.get('action_emotion_map', {})
        self.time_keywords = config_data.get('time_keywords', {})
        self.appearance_keywords = config_data.get('appearance_keywords', {})
        self.location_keywords = config_data.get('location_keywords', {})
        self.emotion_keywords = config_data.get('emotion_keywords', {})
        self.atmosphere_keywords = config_data.get('atmosphere_keywords', {})

    def parse_script(self, script_text: str, task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        优化版剧本解析函数
        将整段中文剧本转换为结构化动作序列
        
        Args:
            script_text: 原始剧本文本
            task_id: 请求的唯一标识符，如果提供将保存结果到对应路径
            
        Returns:
            结构化的剧本动作序列
        """
        debug(f"开始解析剧本: {script_text[:100]}...")

        try:
            # 初始化结果结构
            result = {
                "scenes": []
            }

            # 首先尝试使用高级解析器
            if self.script_intel:
                try:
                    intel_result = self.script_intel.analyze_script_text(script_text)
                    parsed = intel_result.get("parsed_result", {})
                    if parsed and parsed.get("scenes"):
                        debug("使用ScriptIntelligence解析成功")
                        structured_result = self._convert_to_target_format(parsed)
                        return structured_result
                except Exception as e:
                    warning(f"ScriptIntelligence解析失败，回退到基础解析: {str(e)}")

            # 回退到基础解析 + 增强逻辑
            debug("使用基础解析 + 增强逻辑")

            # 1. 首先检测是否有明确的场景划分
            scenes_data = self._detect_scenes(script_text)

            # 2. 处理每个场景
            for scene_info in scenes_data:
                scene_actions = self._parse_scene_actions(scene_info["content"])
                scene_entry = {
                    "location": scene_info["location"],
                    "time": scene_info["time"],
                    "actions": scene_actions
                }
                result["scenes"].append(scene_entry)

            # 3. 如果没有检测到场景，使用默认场景并解析整个文本
            if not result["scenes"]:
                default_actions = self._parse_scene_actions(script_text)
                result["scenes"].append({
                    "location": "城市咖啡馆",  # 默认位置
                    "time": "下午3点",  # 默认时间
                    "actions": default_actions
                })

            # 4. 使用LLM增强结果（如果可用）
            enhanced_result = self.enhance_with_llm(result)
            
            try:
                save_script_parser_result(task_id, enhanced_result, self.output_dir)
                debug(f"剧本解析结果已保存到: data/output/{task_id}/script_parser_result.json")
            except Exception as e:
                warning(f"保存结果失败 (UUID: {task_id}): {str(e)}")

            debug(f"剧本解析完成，提取了 {len(enhanced_result['scenes'])} 个场景")
            return enhanced_result

        except Exception as e:
            error(f"剧本解析失败: {str(e)}")
            # 返回默认结构
            return {
                "scenes": [{
                    "location": "未知",
                    "time": "未知",
                    "actions": []
                }]
            }

    def _detect_scenes(self, script_text: str) -> List[Dict[str, str]]:
        """
        检测剧本中的场景信息
        
        Args:
            script_text: 剧本全文
            
        Returns:
            场景信息列表，包含location、time和content
        """
        scenes = []

        # 首先尝试通过正则模式匹配场景
        for pattern in self.scene_patterns:
            matches = pattern.finditer(script_text)
            for match in matches:
                if len(match.groups()) >= 2:
                    location = match.group(1).strip()
                    time_hint = match.group(2).strip()

                    # 从时间提示中提取时间信息
                    time = self._extract_time(time_hint)

                    scenes.append({
                        "location": location,
                        "time": time,
                        "content": script_text[match.end():]  # 简化处理，实际应该找到下一个场景前的内容
                    })
                    break  # 找到一个匹配就跳出当前模式的匹配

            if scenes:  # 如果有场景匹配，跳出循环
                break

        # 如果没有通过模式匹配到场景，尝试关键词检测
        if not scenes:
            # 分割文本为段落
            paragraphs = re.split(r'[\n\r]+', script_text)

            # 分析每个段落，尝试识别场景信息
            for i, para in enumerate(paragraphs):
                para = para.strip()
                if not para:
                    continue

                # 检查段落中是否包含地点和时间信息
                location = self._extract_location_from_text(para)
                time = self._extract_time_from_text(para)

                if location:
                    scenes.append({
                        "location": location,
                        "time": time or "下午3点",  # 默认时间
                        "content": para
                    })
                    break

            # 如果仍然没有检测到场景，创建默认场景
            if not scenes:
                scenes.append({
                    "location": "城市咖啡馆",  # 默认位置
                    "time": "下午3点",  # 默认时间
                    "content": script_text
                })

        return scenes

    def _extract_location_from_text(self, text: str) -> Optional[str]:
        """从文本中提取地点信息"""
        # 地点关键词和模式
        location_patterns = [
            re.compile(r'在([^，。；\n]+)[处里]'),
            re.compile(r'位于([^，。；\n]+)'),
            re.compile(r'来到([^，。；\n]+)'),
            re.compile(r'走进([^，。；\n]+)'),
        ]

        # 使用从配置加载的地点关键词
        common_locations = list(self.location_keywords.keys()) if hasattr(self, 'location_keywords') and self.location_keywords else [
            "咖啡馆", "餐厅", "办公室", "家", "公园", "街道",
            "超市", "商场", "学校", "医院", "车站", "机场",
            "酒吧", "电影院", "健身房", "图书馆", "会议室"
        ]

        # 首先尝试模式匹配
        for pattern in location_patterns:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()

        # 然后检查常见地点关键词
        for location in common_locations:
            if location in text:
                # 尝试提取更具体的地点描述
                location_match = re.search(f'(.{{0,20}}){location}(.{{0,10}})', text)
                if location_match:
                    full_location = location_match.group(0).strip()
                    # 清理多余字符
                    full_location = re.sub(r'[，。；：]', '', full_location)
                    return full_location
                return location

        return None

    def _extract_time(self, time_hint: str) -> str:
        """从时间提示中提取标准时间格式"""
        # 检查是否包含具体时间
        time_match = re.search(r'(\d{1,2})[:：](\d{1,2})', time_hint)
        if time_match:
            hour = int(time_match.group(1))
            minute = time_match.group(2)
            period = "上午" if hour < 12 else "下午"
            if hour > 12:
                hour = hour - 12
            return f"{period}{hour}:{minute}"

        # 检查是否包含时段关键词
        for keyword, time_period in self.time_keywords.items():
            if keyword in time_hint:
                return time_period

        # 检查是否包含数字+时间单位
        hour_match = re.search(r'(\d{1,2})[点时]', time_hint)
        if hour_match:
            hour = int(hour_match.group(1))
            period = "上午" if hour < 12 else "下午"
            if hour > 12:
                hour = hour - 12
            return f"{period}{hour}点"

        return "下午3点"  # 默认时间

    def _extract_time_from_text(self, text: str) -> Optional[str]:
        """从文本中提取时间信息"""
        # 检查时间段关键词
        for keyword, time_period in self.time_keywords.items():
            if keyword in text:
                # 尝试提取具体时间
                time_match = re.search(r'(\d{1,2})[:：](\d{1,2})', text)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = time_match.group(2)
                    period = "上午" if hour < 12 else "下午"
                    if hour > 12:
                        hour = hour - 12
                    return f"{period}{hour}:{minute}"
                return time_period

        # 检查是否有具体时间
        time_match = re.search(r'(\d{1,2})[:：](\d{1,2})', text)
        if time_match:
            hour = int(time_match.group(1))
            minute = time_match.group(2)
            period = "上午" if hour < 12 else "下午"
            if hour > 12:
                hour = hour - 12
            return f"{period}{hour}:{minute}"

        return None

    def _parse_scene_actions(self, scene_content: str) -> List[Dict[str, str]]:
        """
        解析场景内容，提取动作序列
        
        Args:
            scene_content: 场景内容文本
            
        Returns:
            动作序列列表
        """
        actions = []

        # 分词处理
        words = list(jieba.cut(scene_content))

        # 按行分割场景内容
        lines = scene_content.strip().split('\n')

        # 当前正在跟踪的角色
        current_character = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 尝试匹配对话行
            dialogue_action = self._parse_dialogue_line(line)
            if dialogue_action:
                actions.append(dialogue_action)
                # 更新当前角色
                current_character = dialogue_action.get("character")
                continue

            # 尝试匹配动作行
            action_entry = self._parse_action_line(line, current_character)
            if action_entry:
                actions.append(action_entry)
                # 如果动作行包含角色信息，更新当前角色
                if "character" in action_entry:
                    current_character = action_entry["character"]

        # 如果没有识别到任何动作，尝试整体分析
        if not actions:
            actions = self._analyze_whole_content(scene_content)

        return actions

    def _parse_dialogue_line(self, line: str) -> Optional[Dict[str, str]]:
        """
        解析对话行
        
        Args:
            line: 文本行
            
        Returns:
            对话动作对象
        """
        for pattern in self.dialogue_patterns:
            match = pattern.match(line)
            if match:
                if len(match.groups()) == 2:
                    character, dialogue = match.groups()
                    emotion = self._infer_emotion_from_dialogue(dialogue)
                else:  # len(groups) == 3
                    character, emotion_hint, dialogue = match.groups()
                    emotion = emotion_hint or self._infer_emotion_from_dialogue(dialogue)

                return {
                    "character": character.strip(),
                    "dialogue": dialogue.strip(),
                    "emotion": emotion
                }

        return None

    def _parse_action_line(self, line: str, current_character: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        解析动作行
        
        Args:
            line: 文本行
            current_character: 当前上下文的角色
            
        Returns:
            动作对象
        """
        # 尝试提取角色
        character = None
        action_text = line

        # 模式1: "角色名称 动作描述"
        character_patterns = [
            re.compile(r'^([^，。；\s]+)[，。；\s]+(.+)$'),
            re.compile(r'^([^，。；\s]+)[做干]了(.+)$'),
        ]

        for pattern in character_patterns:
            match = pattern.match(line)
            if match:
                character, action_text = match.groups()
                break

        # 如果没有提取到角色但有当前角色，使用当前角色
        if not character and current_character:
            character = current_character

        # 如果仍然没有角色，尝试从文本中提取
        if not character:
            character = self._extract_character_from_text(line)

        # 如果找到了角色，创建动作对象
        if character:
            # 推断情绪
            emotion = self._infer_emotion_from_action(action_text)

            return {
                "character": character.strip(),
                "action": action_text.strip(),
                "emotion": emotion
            }

        return None

    def _extract_character_from_text(self, text: str) -> Optional[str]:
        """从文本中提取角色名称"""
        # 简单规则：中文人名通常是2-3个汉字
        name_pattern = re.compile(r'([\u4e00-\u9fa5]{2,3})(?=[是在做说])')
        match = name_pattern.search(text)
        if match:
            return match.group(1)

        # 检查是否有常见称呼 + 姓氏的模式
        title_pattern = re.compile(r'(?:先生|女士|小姐|医生|老师|经理|总)[\u4e00-\u9fa5]')
        match = title_pattern.search(text)
        if match:
            return match.group(0)

        return None

    def _infer_emotion_from_dialogue(self, dialogue: str) -> str:
        """从对话内容推断情绪"""
        # 使用从配置加载的情绪关键词，如果配置中没有则使用默认关键词
        if hasattr(self, 'emotion_keywords') and self.emotion_keywords:
            emotion_keywords = self.emotion_keywords
        else:
            # 默认情绪词汇关键词
            emotion_keywords = {
                "高兴": ["开心", "高兴", "快乐", "愉快", "欢乐", "兴奋", "太好了", "真棒", "哈哈"],
                "悲伤": ["伤心", "难过", "悲伤", "难过", "哭", "流泪", "痛苦", "可怜", "惨"],
                "愤怒": ["生气", "愤怒", "恼火", "气死了", "混蛋", "该死", "讨厌", "烦"],
                "惊讶": ["啊", "哇", "惊讶", "震惊", "没想到", "真的吗", "什么", "怎么会"],
                "恐惧": ["害怕", "恐惧", "恐怖", "吓死了", "救命", "不要", "危险"],
                "紧张": ["紧张", "忐忑", "不安", "焦虑", "担心", "怎么办", "不会吧"],
                "平静": ["好的", "嗯", "是的", "知道了", "明白", "了解", "好"],
                "疑问": ["为什么", "什么", "哪里", "谁", "怎么", "如何", "是不是", "有没有"],
            }

        # 标点符号情绪线索
        if '！' in dialogue or '!' in dialogue:
            return "激动"
        elif '？' in dialogue or '?' in dialogue:
            return "疑问"
        elif '...' in dialogue or '…' in dialogue:
            return "犹豫"

        # 关键词匹配
        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                if keyword in dialogue:
                    return emotion

        return "平静"  # 默认情绪

    def _infer_emotion_from_action(self, action_text: str) -> str:
        """从动作描述推断情绪"""
        # 检查动作关键词和对应的情绪
        for action_keyword, emotion in self.action_emotion_map.items():
            if action_keyword in action_text:
                return emotion

        # 使用从配置加载的情绪关键词
        if hasattr(self, 'emotion_keywords') and self.emotion_keywords:
            emotion_keywords = self.emotion_keywords
        else:
            # 默认情绪词汇关键词
            emotion_keywords = {
                "高兴": ["开心", "高兴", "快乐", "愉快"],
                "悲伤": ["伤心", "难过", "悲伤", "哭泣"],
                "愤怒": ["生气", "愤怒", "恼火"],
                "惊讶": ["惊讶", "震惊", "意外"],
                "恐惧": ["害怕", "恐惧", "恐怖"],
                "紧张": ["紧张", "忐忑", "不安"],
            }

        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                if keyword in action_text:
                    return emotion

        return "平静"  # 默认情绪

    def _analyze_whole_content(self, content: str) -> List[Dict[str, str]]:
        """
        整体分析内容，提取动作序列
        
        Args:
            content: 完整的场景内容
            
        Returns:
            动作序列列表
        """
        actions = []

        # 使用jieba分词进行更精细的分析
        words = list(jieba.cut(content))

        # 提取角色
        characters = self._extract_characters_from_text(content)

        if not characters:
            # 如果没有提取到角色，创建默认角色
            characters = ["李明"]  # 默认主角

        # 简单策略：将内容分割为多个动作描述
        segments = re.split(r'[，。；！？]', content)
        segments = [s.strip() for s in segments if s.strip()]

        # 为每个角色分配动作
        character_index = 0
        for segment in segments:
            character = characters[character_index % len(characters)]

            # 判断是动作还是对话
            if any(punct in segment for punct in ["\"", "''", '"', "'", "“", "”"]):
                # 对话
                actions.append({
                    "character": character,
                    "dialogue": segment,
                    "emotion": self._infer_emotion_from_dialogue(segment)
                })
            else:
                # 动作
                actions.append({
                    "character": character,
                    "action": segment,
                    "emotion": self._infer_emotion_from_action(segment)
                })

            character_index += 1

        return actions

    def _extract_characters_from_text(self, text: str) -> List[str]:
        """从文本中提取所有可能的角色名称"""
        characters = []

        # 提取2-3个汉字的人名
        name_matches = re.findall(r'([\u4e00-\u9fa5]{2,3})(?=[是在做说])', text)
        characters.extend(list(set(name_matches)))

        # 提取称呼+姓氏
        title_matches = re.findall(r'(?:先生|女士|小姐|医生|老师|经理|总)[\u4e00-\u9fa5]', text)
        characters.extend(list(set(title_matches)))

        # 对话中的角色
        for pattern in self.dialogue_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                if len(match.groups()) >= 1:
                    character = match.group(1).strip()
                    if character not in characters:
                        characters.append(character)

        return characters[:5]  # 最多返回5个角色

    def _convert_to_target_format(self, parsed_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        将解析结果转换为目标格式
        
        Args:
            parsed_result: 原始解析结果
            
        Returns:
            转换后的结构化数据
        """
        result = {
            "scenes": []
        }

        for scene in parsed_result.get("scenes", []):
            # 提取场景信息
            location = scene.get("location", "未知位置")

            # 处理时间信息
            time_of_day = scene.get("time_of_day", "")
            if time_of_day:
                time_mapping = {
                    "DAY": "白天", "NIGHT": "夜晚", "MORNING": "早晨",
                    "AFTERNOON": "下午", "EVENING": "傍晚", "DUSK": "黄昏",
                    "DAWN": "黎明"
                }
                time = time_mapping.get(time_of_day, time_of_day)
            else:
                time = "下午3点"  # 默认时间

            # 处理动作
            actions = []
            for element in scene.get("elements", []):
                element_type = element.get("type")
                content = element.get("content", "")
                metadata = element.get("metadata", {})

                if element_type == "dialogue":
                    character = metadata.get("character", "未知角色")
                    actions.append({
                        "character": character,
                        "dialogue": content,
                        "emotion": self._infer_emotion_from_dialogue(content)
                    })
                elif element_type == "action":
                    # 尝试从动作内容中提取角色
                    character = self._extract_character_from_text(content)
                    if not character and scene.get("characters"):
                        character = scene["characters"][0]  # 使用场景中的第一个角色
                    if not character:
                        character = "未知角色"

                    actions.append({
                        "character": character,
                        "action": content,
                        "emotion": self._infer_emotion_from_action(content)
                    })

            # 如果没有提取到动作，尝试从场景文本中生成
            if not actions:
                actions = self._analyze_whole_content(str(scene))

            result["scenes"].append({
                "location": location,
                "time": time,
                "actions": actions
            })

        return result

    def enhance_with_llm(self, structured_script: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用LLM增强解析结果
        添加情绪识别和角色外观推断
        
        Args:
            structured_script: 结构化的剧本数据
            
        Returns:
            增强后的结构化剧本数据
        """
        if not self.llm:
            debug("未配置LLM，使用规则增强代替")
            return self._enhance_with_rules(structured_script)

        try:
            # 准备增强提示
            prompt_template = """
            请作为一个专业的中文剧本分析专家，对以下结构化剧本进行增强处理：
            1. 确保每个动作都有合适的情绪标签
            2. 为每个角色推断合理的外观描述（年龄、穿着、外貌特征等）
            3. 优化场景信息（地点和时间）
            4. 保持原始动作序列的顺序和内容
            
            请返回增强后的JSON格式结果，不要添加额外说明。
            
            原始剧本：
            {script_json}
            """

            # 填充提示词模板
            filled_prompt = prompt_template.format(
                script_json=json.dumps(structured_script, ensure_ascii=False)
            )

            # 调用LLM
            debug("开始调用LLM增强剧本解析结果")
            response = self.llm.invoke(filled_prompt)

            # 尝试解析JSON响应
            enhanced_script = json.loads(response)
            debug("LLM增强成功，返回增强后的剧本结构")

            # 确保返回格式正确
            return self._ensure_correct_format(enhanced_script)
        except json.JSONDecodeError as e:
            warning(f"LLM增强失败：响应不是有效的JSON格式: {str(e)}")
        except Exception as e:
            print_log_exception()
            # 检查是否是API密钥错误
            if "API key" in str(e) or "401" in str(e):
                warning(f"LLM增强失败：API密钥错误或权限不足: {str(e)}")
            else:
                warning(f"LLM增强失败，使用规则增强代替: {str(e)}")

        # 使用规则增强作为后备
        return self._enhance_with_rules(structured_script)

    def _enhance_with_rules(self, structured_script: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用规则增强解析结果
        
        Args:
            structured_script: 结构化的剧本数据
            
        Returns:
            增强后的结构化剧本数据
        """
        enhanced_script = json.loads(json.dumps(structured_script))  # 深拷贝

        # 为所有角色添加外观推断
        character_appearances = {}

        # 遍历所有场景和动作
        for scene in enhanced_script.get("scenes", []):
            # 优化场景信息
            if "atmosphere" not in scene:
                scene["atmosphere"] = self._infer_atmosphere(scene)

            # 增强每个动作
            for action in scene.get("actions", []):
                character = action.get("character", "")

                # 确保有情绪
                if "emotion" not in action:
                    if "dialogue" in action:
                        action["emotion"] = self._infer_emotion_from_dialogue(action["dialogue"])
                    elif "action" in action:
                        action["emotion"] = self._infer_emotion_from_action(action["action"])
                    else:
                        action["emotion"] = "平静"

                # 推断角色外观（如果还没有）
                if character and character not in character_appearances:
                    # 收集所有与该角色相关的文本
                    character_text = ""
                    for s in enhanced_script.get("scenes", []):
                        for a in s.get("actions", []):
                            if a.get("character") == character:
                                if "dialogue" in a:
                                    character_text += " " + a["dialogue"]
                                if "action" in a:
                                    character_text += " " + a["action"]

                    # 基于文本推断外观
                    appearance = self._infer_character_appearance(character, character_text)
                    character_appearances[character] = appearance

            # 添加角色外观信息到场景
            if "characters_info" not in scene:
                scene["characters_info"] = {}

            # 收集场景中出现的角色
            scene_characters = set()
            for action in scene.get("actions", []):
                char = action.get("character")
                if char:
                    scene_characters.add(char)

            # 添加外观信息
            for char in scene_characters:
                if char in character_appearances:
                    scene["characters_info"][char] = character_appearances[char]

        return enhanced_script

    def _infer_atmosphere(self, scene: Dict[str, Any]) -> str:
        """推断场景氛围"""
        # 使用从配置加载的场景氛围关键词
        if hasattr(self, 'atmosphere_keywords') and self.atmosphere_keywords:
            # 合并所有场景内容用于氛围分析
            scene_text = scene.get("location", "") + " " + scene.get("time", "")

            # 遍历所有动作内容
            for action in scene.get("actions", []):
                if "dialogue" in action:
                    scene_text += " " + action["dialogue"]
                if "action" in action:
                    scene_text += " " + action["action"]

            # 检查氛围关键词
            for atmosphere, keywords in self.atmosphere_keywords.items():
                if any(keyword in scene_text for keyword in keywords):
                    return atmosphere

        # 回退到基于时间和地点的简单推断
        # 基于时间推断
        time = scene.get("time", "")
        if "夜晚" in time or "深夜" in time:
            return "昏暗"
        elif "清晨" in time or "早晨" in time:
            return "清新"
        elif "黄昏" in time or "傍晚" in time:
            return "温馨"

        # 基于地点推断
        location = scene.get("location", "")
        if "咖啡馆" in location or "餐厅" in location:
            return "温馨"
        elif "办公室" in location or "会议室" in location:
            return "正式"
        elif "公园" in location or "花园" in location:
            return "轻松"
        elif "医院" in location or "诊所" in location:
            return "严肃"
        elif "酒吧" in location or "夜店" in location:
            return "热闹"

        return "普通"

    def _infer_character_appearance(self, character: str, character_text: str) -> Dict[str, str]:
        """
        推断角色外观
        
        Args:
            character: 角色名称
            character_text: 与角色相关的所有文本
            
        Returns:
            外观描述字典
        """
        appearance = {
            "age": "未知",
            "clothing": "普通服装",
            "features": "普通外貌"
        }

        # 基于关键词推断
        for keyword, description in self.appearance_keywords.items():
            if keyword in character_text:
                if any(age in keyword for age in ["老人", "年轻人", "小孩"]):
                    appearance["age"] = description
                elif any(clothing in keyword for clothing in ["西装", "正装", "休闲装", "T恤", "长裙"]):
                    appearance["clothing"] = description
                else:
                    appearance["features"] = description

        # 基于对话风格推断年龄
        if any(young_kw in character_text for young_kw in ["哇塞", "酷", "帅", "小姐姐", "小哥哥"]):
            appearance["age"] = "年轻人"
        elif any(old_kw in character_text for old_kw in ["唉", "想当年", "年轻人", "现在的年轻人"]):
            appearance["age"] = "中年人"

        # 基于动作推断体型
        if any(action in character_text for action in ["跑步", "跳跃", "运动"]):
            appearance["features"] = "身材健壮"
        elif any(action in character_text for action in ["慢慢", "缓缓", "吃力"]):
            appearance["features"] = "身材一般"

        return appearance

    def _ensure_correct_format(self, data: Any) -> Dict[str, Any]:
        """
        确保返回数据格式正确
        
        Args:
            data: 输入数据
            
        Returns:
            格式正确的结构化数据
        """
        # 确保是字典格式
        if not isinstance(data, dict):
            return {
                "scenes": []
            }

        # 确保有scenes字段
        if "scenes" not in data or not isinstance(data["scenes"], list):
            data["scenes"] = []

        # 确保每个场景格式正确
        for scene in data["scenes"]:
            if not isinstance(scene, dict):
                continue

            # 确保必要字段存在
            if "location" not in scene:
                scene["location"] = "未知"
            if "time" not in scene:
                scene["time"] = "未知"
            if "actions" not in scene:
                scene["actions"] = []

            # 确保每个动作格式正确
            for action in scene["actions"]:
                if not isinstance(action, dict):
                    continue

                # 确保动作字段
                if "character" not in action:
                    action["character"] = "未知角色"
                if "emotion" not in action:
                    action["emotion"] = "平静"

                # 确保有action或dialogue字段
                if "action" not in action and "dialogue" not in action:
                    action["action"] = "未知动作"

        return data
