#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LangChain 剧本智能体示例
展示如何构建一个专门用于剧本分析和拆解的LangChain智能体
"""

import json
from typing import Dict, Any, List, Optional

from langchain_core.tools import Tool
from langchain.agents import AgentType, initialize_agent
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage

# 导入HengLine工具
from hengline.tools import (
    ScriptParser,
    create_script_intelligence,
    ScriptIntelligence,
    ScriptKnowledgeBase
)
from hengline.client.client_factory import ClientFactory


class LangChainScriptAgent:
    """
    LangChain剧本智能体类
    专门用于处理剧本分析、拆解和分镜生成任务
    """
    
    def __init__(self, 
                 embedding_model_name: str = "openai",
                 storage_dir: Optional[str] = None,
                 provider: str = "openai"):
        """
        初始化剧本智能体
        
        Args:
            embedding_model_name: 嵌入模型名称
            storage_dir: 知识库存储目录
            provider: LLM提供商名称
        """
        # 初始化工具组件
        self.parser = ScriptParser()
        self.script_intel = create_script_intelligence(
            embedding_model_name=embedding_model_name,
            storage_dir=storage_dir
        )
        
        # 获取LLM
        self.llm = ClientFactory.get_langchain_llm(provider=provider)
        
        # 创建工具列表
        self.tools = self._create_tools()
        
        # 初始化智能体
        self.agent = self._create_agent()
    
    def _create_tools(self) -> List[Tool]:
        """
        创建LangChain工具列表
        """
        tools = [
            # 1. 剧本解析工具
            Tool(
                name="剧本解析器",
                func=self.parse_script,
                description="解析剧本文本，提取场景、角色、对话和动作等结构化信息。输入为完整的剧本文本。"
            ),
            
            # 2. 场景分析工具
            Tool(
                name="场景分析器",
                func=self.analyze_scenes,
                description="分析剧本中的场景信息，包括场景数量、类型、长度等。输入为完整的剧本文本。"
            ),
            
            # 3. 角色分析工具
            Tool(
                name="角色分析器",
                func=self.analyze_characters,
                description="分析剧本中的角色信息，包括角色数量、对话次数、出场场景等。输入为完整的剧本文本。"
            ),
            
            # 4. 对话分析工具
            Tool(
                name="对话分析器",
                func=self.analyze_dialogues,
                description="分析剧本中的对话内容，统计对话数量、长度等信息。输入为完整的剧本文本。"
            ),
            
            # 5. 动作提取工具
            Tool(
                name="动作提取器",
                func=self.extract_actions,
                description="提取剧本中的动作描述，帮助理解角色行为。输入为完整的剧本文本。"
            ),
            
            # 6. 分镜生成工具
            Tool(
                name="分镜生成器",
                func=self.generate_storyboard,
                description="基于剧本内容生成初步的分镜建议。输入为完整的剧本文本。"
            ),
            
            # 7. 剧本摘要工具
            Tool(
                name="剧本摘要",
                func=self.summarize_script,
                description="生成剧本的整体摘要，包括主要情节、角色和场景。输入为完整的剧本文本。"
            ),
            
            # 8. 场景拆分工具
            Tool(
                name="场景拆分器",
                func=self.split_scenes,
                description="将剧本按场景拆分，并为每个场景生成独立的详细信息。输入为完整的剧本文本。"
            )
        ]
        
        return tools
    
    def _create_agent(self) -> Optional[Any]:
        """
        创建LangChain智能体
        """
        if not self.llm:
            print("警告: 无法获取LLM实例，智能体功能将受限")
            return None
        
        # 创建自定义提示模板
        system_prompt = (
            "你是一个专业的剧本分析智能体，擅长处理电影、电视剧和戏剧剧本。\n\n"
            "你可以使用提供的工具来执行各种剧本分析任务，包括：\n"
            "1. 解析剧本结构\n"
            "2. 分析场景和角色\n"
            "3. 提取对话和动作\n"
            "4. 生成摘要和分镜建议\n\n"
            "请根据用户的具体需求，选择合适的工具来完成任务。\n"
            "对于复杂的请求，请逐步使用多个工具来获取完整的分析结果。\n"
            "请以专业、清晰的方式呈现分析结果，突出重点信息。"
        )
        
        # 初始化智能体
        agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            agent_kwargs={
                "system_message": system_prompt
            }
        )
        
        return agent
    
    def parse_script(self, script_text: str) -> str:
        """
        剧本解析工具函数
        """
        parsed = self.parser.parse(script_text)
        
        # 构建简洁的解析结果
        result = {
            "基本信息": {
                "场景数量": len(parsed["scenes"]),
                "角色数量": len(parsed["characters"]),
            },
            "场景列表": [
                {
                    "序号": i + 1,
                    "标题": scene["heading"],
                    "角色": scene["characters"],
                    "元素数量": len(scene["elements"])
                }
                for i, scene in enumerate(parsed["scenes"])
            ],
            "角色列表": [
                {
                    "姓名": name,
                    "对话次数": info.get("dialogue_count", 0),
                    "出场场景数": len(info.get("scenes", []))
                }
                for name, info in parsed["characters"].items()
            ]
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def analyze_scenes(self, script_text: str) -> str:
        """
        场景分析工具函数
        """
        parsed = self.parser.parse(script_text)
        
        # 统计场景类型
        scene_types = {}
        for scene in parsed["scenes"]:
            if scene["heading"].startswith("INT"):
                scene_types["室内"] = scene_types.get("室内", 0) + 1
            elif scene["heading"].startswith("EXT"):
                scene_types["室外"] = scene_types.get("室外", 0) + 1
            
        # 计算场景长度
        scene_lengths = []
        for scene in parsed["scenes"]:
            length = scene["end_line"] - scene["start_line"] + 1
            scene_lengths.append({
                "标题": scene["heading"],
                "行数": length,
                "角色数": len(scene["characters"])
            })
        
        # 按长度排序
        scene_lengths.sort(key=lambda x: x["行数"], reverse=True)
        
        result = {
            "场景总数": len(parsed["scenes"]),
            "场景类型分布": scene_types,
            "最长的5个场景": scene_lengths[:5],
            "平均场景行数": round(sum(s["行数"] for s in scene_lengths) / len(scene_lengths), 2) if scene_lengths else 0
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def analyze_characters(self, script_text: str) -> str:
        """
        角色分析工具函数
        """
        parsed = self.parser.parse(script_text)
        
        # 构建角色详细分析
        characters_analysis = []
        for name, info in parsed["characters"].items():
            # 统计该角色在每个场景中的对话数
            scene_dialogues = {}
            for scene in parsed["scenes"]:
                for element in scene["elements"]:
                    if element["type"] == "dialogue" and element.get("character") == name:
                        scene_dialogues[scene["heading"]] = scene_dialogues.get(scene["heading"], 0) + 1
            
            characters_analysis.append({
                "角色名": name,
                "对话总数": info.get("dialogue_count", 0),
                "出场场景数": len(info.get("scenes", [])),
                "首次出场": info.get("first_appearance", "N/A"),
                "场景对话分布": scene_dialogues
            })
        
        # 按对话数排序
        characters_analysis.sort(key=lambda x: x["对话总数"], reverse=True)
        
        result = {
            "角色总数": len(characters_analysis),
            "主要角色": characters_analysis[:3],  # 只返回前3个主要角色的详细信息
            "角色列表（按对话数排序）": [
                {"角色名": char["角色名"], "对话数": char["对话总数"]}
                for char in characters_analysis
            ]
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def analyze_dialogues(self, script_text: str) -> str:
        """
        对话分析工具函数
        """
        parsed = self.parser.parse(script_text)
        
        # 统计对话信息
        total_dialogues = 0
        dialogue_by_character = {}
        dialogue_by_scene = {}
        
        for scene_idx, scene in enumerate(parsed["scenes"]):
            scene_dialogues = 0
            for element in scene["elements"]:
                if element["type"] == "dialogue":
                    total_dialogues += 1
                    scene_dialogues += 1
                    
                    # 按角色统计
                    char_name = element.get("character", "未知角色")
                    dialogue_by_character[char_name] = dialogue_by_character.get(char_name, 0) + 1
            
            # 按场景统计
            dialogue_by_scene[scene["heading"]] = scene_dialogues
        
        # 计算平均对话长度（这里简化为行数）
        avg_dialogues_per_scene = round(total_dialogues / len(parsed["scenes"]), 2) if parsed["scenes"] else 0
        
        result = {
            "对话总数": total_dialogues,
            "平均每场景对话数": avg_dialogues_per_scene,
            "角色对话统计": dict(sorted(
                dialogue_by_character.items(), 
                key=lambda x: x[1], 
                reverse=True
            )),
            "场景对话统计": dict(sorted(
                dialogue_by_scene.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5])  # 只返回前5个对话最多的场景
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def extract_actions(self, script_text: str) -> str:
        """
        动作提取工具函数
        """
        parsed = self.parser.parse(script_text)
        
        # 提取所有动作描述
        actions = []
        for scene_idx, scene in enumerate(parsed["scenes"]):
            for element in scene["elements"]:
                if element["type"] == "action":
                    actions.append({
                        "场景": scene["heading"],
                        "场景序号": scene_idx + 1,
                        "动作描述": element["content"],
                        "行号": {
                            "开始": element["start_line"],
                            "结束": element["end_line"]
                        }
                    })
        
        # 统计动作数量
        actions_by_scene = {}
        for scene in parsed["scenes"]:
            scene_actions = sum(1 for e in scene["elements"] if e["type"] == "action")
            if scene_actions > 0:
                actions_by_scene[scene["heading"]] = scene_actions
        
        result = {
            "动作总数": len(actions),
            "场景动作统计": dict(sorted(
                actions_by_scene.items(), 
                key=lambda x: x[1], 
                reverse=True
            )),
            "动作详情": actions[:10]  # 只返回前10个动作详情
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def generate_storyboard(self, script_text: str) -> str:
        """
        分镜生成工具函数
        """
        parsed = self.parser.parse(script_text)
        
        storyboard = {
            "项目信息": {
                "场景总数": len(parsed["scenes"]),
                "预计镜头数": len(parsed["scenes"]) * 2,  # 每个场景2个镜头
                "主要角色": sorted(
                    parsed["characters"].keys(),
                    key=lambda x: parsed["characters"][x].get("dialogue_count", 0),
                    reverse=True
                )[:3]
            },
            "镜头列表": []
        }
        
        # 为每个场景生成镜头
        shot_id = 1
        for scene_idx, scene in enumerate(parsed["scenes"]):
            # 主镜头 - 建立场景
            main_shot = {
                "镜头ID": shot_id,
                "场景序号": scene_idx + 1,
                "场景标题": scene["heading"],
                "镜头类型": "全景",
                "描述": f"展示{scene['heading']}的整体环境和氛围",
                "时长(秒)": 3,
                "主要角色": scene["characters"],
                "目的": "建立场景，介绍环境"
            }
            storyboard["镜头列表"].append(main_shot)
            shot_id += 1
            
            # 中景/特写镜头 - 聚焦角色
            if scene["characters"]:
                detail_shot = {
                    "镜头ID": shot_id,
                    "场景序号": scene_idx + 1,
                    "场景标题": scene["heading"],
                    "镜头类型": "中景" if len(scene["characters"]) > 1 else "特写",
                    "描述": f"聚焦于{', '.join(scene['characters'])}的互动和表情",
                    "时长(秒)": 5,
                    "主要角色": scene["characters"],
                    "目的": "展示角色互动和情感"
                }
                storyboard["镜头列表"].append(detail_shot)
                shot_id += 1
        
        # 更新实际镜头数
        storyboard["项目信息"]["实际镜头数"] = len(storyboard["镜头列表"])
        
        return json.dumps(storyboard, ensure_ascii=False, indent=2)
    
    def summarize_script(self, script_text: str) -> str:
        """
        剧本摘要工具函数
        """
        parsed = self.parser.parse(script_text)
        
        # 提取关键信息
        scenes_summary = [
            f"{i+1}. {scene['heading']} - 角色: {', '.join(scene['characters'])} - 元素数: {len(scene['elements'])}"
            for i, scene in enumerate(parsed["scenes"])
        ]
        
        main_characters = sorted(
            parsed["characters"].items(),
            key=lambda x: x[1].get("dialogue_count", 0),
            reverse=True
        )[:3]
        
        # 统计对话和动作
        total_dialogues = 0
        total_actions = 0
        
        for scene in parsed["scenes"]:
            for element in scene["elements"]:
                if element["type"] == "dialogue":
                    total_dialogues += 1
                elif element["type"] == "action":
                    total_actions += 1
        
        summary = {
            "剧本概览": {
                "场景总数": len(parsed["scenes"]),
                "角色总数": len(parsed["characters"]),
                "对话总数": total_dialogues,
                "动作描述总数": total_actions,
                "估计时长(分钟)": round((total_dialogues * 3 + total_actions * 5) / 60, 2)  # 粗略估计
            },
            "主要角色": [
                {
                    "姓名": name,
                    "对话次数": info.get("dialogue_count", 0),
                    "出场场景数": len(info.get("scenes", []))
                }
                for name, info in main_characters
            ],
            "场景摘要": scenes_summary,
            "剧本结构特点": []
        }
        
        # 添加结构特点
        if len(parsed["scenes"]) <= 5:
            summary["剧本结构特点"].append("场景数量较少，适合短剧或短片")
        elif len(parsed["scenes"]) > 20:
            summary["剧本结构特点"].append("场景数量较多，可能是复杂叙事或长片")
        
        dialogue_ratio = total_dialogues / (total_dialogues + total_actions) if (total_dialogues + total_actions) > 0 else 0
        if dialogue_ratio > 0.7:
            summary["剧本结构特点"].append("对话占比较大，偏戏剧化叙事")
        elif dialogue_ratio < 0.3:
            summary["剧本结构特点"].append("动作描述占比较大，偏视觉化叙事")
        
        return json.dumps(summary, ensure_ascii=False, indent=2)
    
    def split_scenes(self, script_text: str) -> str:
        """
        场景拆分工具函数
        """
        parsed = self.parser.parse(script_text)
        
        scenes_detail = []
        for scene_idx, scene in enumerate(parsed["scenes"]):
            # 提取场景中的元素
            elements = []
            for element in scene["elements"]:
                elements.append({
                    "类型": element["type"],
                    "内容": element["content"],
                    "行号": {
                        "开始": element["start_line"],
                        "结束": element["end_line"]
                    }
                })
            
            scenes_detail.append({
                "场景序号": scene_idx + 1,
                "场景标题": scene["heading"],
                "出场角色": scene["characters"],
                "元素总数": len(elements),
                "对话数量": sum(1 for e in elements if e["类型"] == "dialogue"),
                "动作数量": sum(1 for e in elements if e["类型"] == "action"),
                "长度(行数)": scene["end_line"] - scene["start_line"] + 1,
                "元素详情": elements[:10]  # 只显示前10个元素
            })
        
        result = {
            "场景总数": len(scenes_detail),
            "场景详情": scenes_detail
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def run_agent(self, query: str) -> Optional[str]:
        """
        运行智能体处理查询
        
        Args:
            query: 用户查询
            
        Returns:
            智能体的响应
        """
        if not self.agent:
            print("错误: 智能体未初始化成功")
            return None
        
        try:
            result = self.agent.run(query)
            return result
        except Exception as e:
            print(f"智能体运行出错: {str(e)}")
            return None
    
    def direct_tool_call(self, tool_name: str, script_text: str) -> Optional[str]:
        """
        直接调用指定工具
        
        Args:
            tool_name: 工具名称
            script_text: 剧本内容
            
        Returns:
            工具执行结果
        """
        tool_map = {
            "剧本解析器": self.parse_script,
            "场景分析器": self.analyze_scenes,
            "角色分析器": self.analyze_characters,
            "对话分析器": self.analyze_dialogues,
            "动作提取器": self.extract_actions,
            "分镜生成器": self.generate_storyboard,
            "剧本摘要": self.summarize_script,
            "场景拆分器": self.split_scenes
        }
        
        if tool_name in tool_map:
            return tool_map[tool_name](script_text)
        else:
            print(f"错误: 未知工具名称: {tool_name}")
            return None


# 示例用法
def example_direct_tool_calls():
    """
    直接调用工具示例
    """
    print("\n=== 直接调用LangChain工具示例 ===")
    
    # 示例剧本
    sample_script = """
    INT. LIVING ROOM - NIGHT
    
    温馨的客厅，灯光柔和。LI坐在沙发上看报纸，WANG端着两杯茶走进来。
    
    WANG
    喝杯茶吧，已经泡好了。
    
    LI
    谢谢。今天的新闻真多啊。
    
    WANG在LI旁边坐下，两人开始聊天。
    
    WANG
    工作怎么样？最近是不是很忙？
    
    LI
    是啊，项目进入关键阶段了，每天都要加班。
    
    WANG
    别太拼命了，注意身体。
    
    INT. OFFICE - DAY
    
    明亮的办公室，LI坐在电脑前工作，看起来很疲惫。ZHANG走进来。
    
    ZHANG
    李总，这个报告需要您签字。
    
    LI接过报告，快速浏览后签字。
    
    LI
    放这儿吧，我稍后处理。
    
    ZHANG离开。LI揉了揉眼睛，继续工作。
    """
    
    # 创建智能体实例
    agent = LangChainScriptAgent(embedding_model_name="openai", storage_dir=None)
    
    print("\n1. 使用剧本解析器工具:")
    result = agent.direct_tool_call("剧本解析器", sample_script)
    parsed_result = json.loads(result)
    print(f"解析出 {parsed_result['基本信息']['场景数量']} 个场景和 {parsed_result['基本信息']['角色数量']} 个角色")
    
    print("\n2. 使用场景分析器工具:")
    result = agent.direct_tool_call("场景分析器", sample_script)
    scene_result = json.loads(result)
    print(f"场景类型分布: {scene_result['场景类型分布']}")
    
    print("\n3. 使用角色分析器工具:")
    result = agent.direct_tool_call("角色分析器", sample_script)
    char_result = json.loads(result)
    print(f"主要角色: {[char['角色名'] for char in char_result['主要角色']]}")
    
    print("\n4. 使用分镜生成器工具:")
    result = agent.direct_tool_call("分镜生成器", sample_script)
    storyboard_result = json.loads(result)
    print(f"生成了 {storyboard_result['项目信息']['实际镜头数']} 个镜头")
    print(f"第一个镜头: {storyboard_result['镜头列表'][0]['描述']}")
    
    print("\n5. 使用剧本摘要工具:")
    result = agent.direct_tool_call("剧本摘要", sample_script)
    summary_result = json.loads(result)
    print(f"剧本概览: {summary_result['剧本概览']}")


def example_simple_query():
    """
    简单查询示例
    """
    print("\n=== 简单查询示例 ===")
    
    # 示例剧本
    sample_script = """
    INT. RESTAURANT - EVENING
    
    高档餐厅，灯光优雅。ZHANG和LIU坐在靠窗的位置，桌上摆着精致的菜肴。
    
    ZHANG
    这家餐厅的菜真不错，谢谢你推荐。
    
    LIU
    不客气，我经常来这儿。你喜欢就好。
    
    ZHANG
    对了，关于那个合作项目，我想和你谈谈。
    
    LIU放下刀叉，认真地看着ZHANG。
    
    LIU
    好啊，你有什么想法？
    """
    
    # 创建智能体实例
    agent = LangChainScriptAgent(embedding_model_name="openai", storage_dir=None)
    
    # 构建查询
    query = f"分析这段剧本：\n{sample_script}\n\n请告诉我有多少个场景，有哪些角色，以及他们的对话内容。"
    
    print(f"\n查询: {query}")
    print("\n注意: 要运行完整的智能体功能，需要配置有效的API密钥")
    print("\n您可以使用direct_tool_call方法来直接调用工具功能，无需配置API密钥")
    
    # 如果需要实际运行智能体，请取消下面的注释
    # result = agent.run_agent(query)
    # if result:
    #     print(f"\n智能体响应: {result}")


def main():
    """
    运行示例
    """
    print("===== LangChain 剧本智能体示例 =====")
    
    try:
        # 运行直接工具调用示例
        example_direct_tool_calls()
        
        # 运行简单查询示例
        example_simple_query()
        
    except Exception as e:
        print(f"示例运行出错: {str(e)}")
    
    print("\n===== 示例结束 =====")
    print("\n使用提示:")
    print("1. 可以将示例中的剧本替换为您自己的剧本")
    print("2. direct_tool_call方法可以直接使用，无需配置API密钥")
    print("3. 要使用完整的智能体功能(run_agent方法)，需要配置有效的API密钥")
    print("4. 可以根据需要扩展工具列表和功能")
    print("5. 对于生产环境，建议配置持久化存储目录")


if __name__ == "__main__":
    main()