#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剧本分析完整工作流示例
展示如何使用LangChain工具链执行剧本分析、拆解和分镜生成的完整流程
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_core.tools import Tool
from langchain.chains import SequentialChain, LLMChain
from langchain.prompts import PromptTemplate
from langchain.agents import AgentType, initialize_agent

# 导入HengLine工具
from hengline.tools import (
    ScriptParser,
    create_script_intelligence,
    ScriptIntelligence
)
from hengline.client.client_factory import ClientFactory


class ScriptAnalysisWorkflow:
    """
    剧本分析工作流类
    提供完整的剧本分析、拆解和分镜生成流程
    """
    
    def __init__(self, embedding_model_name: str = "openai", 
                 storage_dir: Optional[str] = None):
        """
        初始化工作流
        
        Args:
            embedding_model_name: 嵌入模型名称
            storage_dir: 知识库存储目录
        """
        self.parser = ScriptParser()
        self.script_intel = create_script_intelligence(
            embedding_model_name=embedding_model_name,
            storage_dir=storage_dir
        )
        self.llm = ClientFactory.get_langchain_llm(provider="openai")
        self.tools = self._create_tools()
    
    def _create_tools(self) -> List[Tool]:
        """
        创建LangChain工具列表
        """
        tools = []
        
        # 1. 剧本解析工具
        tools.append(Tool(
            name="ScriptParser",
            func=self._parse_script,
            description="解析剧本文本，提取场景、角色、对话、动作等结构化信息。输入为完整的剧本文本。"
        ))
        
        # 2. 剧本统计分析工具
        tools.append(Tool(
            name="ScriptStatistics",
            func=self._analyze_statistics,
            description="分析剧本的统计信息，包括场景数量、角色数量、对话数量等。输入为完整的剧本文本。"
        ))
        
        # 3. 场景提取工具
        tools.append(Tool(
            name="SceneExtractor",
            func=self._extract_scenes,
            description="从剧本中提取指定场景或所有场景的详细信息。输入为剧本文本和可选的场景编号。"
        ))
        
        # 4. 角色分析工具
        tools.append(Tool(
            name="CharacterAnalyzer",
            func=self._analyze_characters,
            description="分析剧本中的角色信息，包括出场次数、对话数量等。输入为完整的剧本文本。"
        ))
        
        # 5. 剧本内容搜索工具
        tools.append(Tool(
            name="ScriptSearcher",
            func=self._search_script,
            description="在剧本中搜索特定内容。输入为剧本文本和搜索查询。"
        ))
        
        return tools
    
    def _parse_script(self, script_text: str) -> str:
        """
        剧本解析工具函数
        """
        result = self.parser.parse(script_text)
        # 返回格式化的JSON字符串
        return json.dumps({
            "scenes_count": len(result["scenes"]),
            "characters_count": len(result["characters"]),
            "scenes": [{
                "heading": scene["heading"],
                "characters": scene["characters"],
                "elements_count": len(scene["elements"])
            } for scene in result["scenes"]],
            "characters": list(result["characters"].keys())
        }, ensure_ascii=False, indent=2)
    
    def _analyze_statistics(self, script_text: str) -> str:
        """
        剧本统计分析工具函数
        """
        # 首先解析剧本
        parsed = self.parser.parse(script_text)
        
        # 统计对话数量
        dialogue_count = 0
        action_count = 0
        
        for scene in parsed["scenes"]:
            for element in scene["elements"]:
                if element["type"] == "dialogue":
                    dialogue_count += 1
                elif element["type"] == "action":
                    action_count += 1
        
        # 统计角色对话次数
        character_dialogues = {}
        for char_name, char_info in parsed["characters"].items():
            character_dialogues[char_name] = char_info.get("dialogue_count", 0)
        
        statistics = {
            "total_scenes": len(parsed["scenes"]),
            "total_characters": len(parsed["characters"]),
            "total_dialogues": dialogue_count,
            "total_actions": action_count,
            "character_dialogues": dict(sorted(
                character_dialogues.items(), 
                key=lambda x: x[1], 
                reverse=True
            )),
            "avg_dialogues_per_scene": round(dialogue_count / len(parsed["scenes"]), 2) if parsed["scenes"] else 0
        }
        
        return json.dumps(statistics, ensure_ascii=False, indent=2)
    
    def _extract_scenes(self, script_text: str, scene_number: Optional[int] = None) -> str:
        """
        场景提取工具函数
        """
        parsed = self.parser.parse(script_text)
        
        if scene_number is not None:
            # 提取指定场景
            if 1 <= scene_number <= len(parsed["scenes"]):
                scene = parsed["scenes"][scene_number - 1]
                return json.dumps({
                    "scene_number": scene_number,
                    "heading": scene["heading"],
                    "characters": scene["characters"],
                    "elements": [{
                        "type": elem["type"],
                        "content": elem["content"]
                    } for elem in scene["elements"]]
                }, ensure_ascii=False, indent=2)
            else:
                return f"错误: 场景编号 {scene_number} 超出范围 (1-{len(parsed['scenes'])})"
        else:
            # 提取所有场景
            scenes_summary = []
            for i, scene in enumerate(parsed["scenes"], 1):
                scenes_summary.append({
                    "scene_number": i,
                    "heading": scene["heading"],
                    "characters": scene["characters"],
                    "length": scene["end_line"] - scene["start_line"] + 1
                })
            
            return json.dumps({
                "total_scenes": len(scenes_summary),
                "scenes": scenes_summary
            }, ensure_ascii=False, indent=2)
    
    def _analyze_characters(self, script_text: str) -> str:
        """
        角色分析工具函数
        """
        parsed = self.parser.parse(script_text)
        
        # 构建角色详细信息
        characters_info = []
        for char_name, char_data in parsed["characters"].items():
            characters_info.append({
                "name": char_name,
                "dialogue_count": char_data.get("dialogue_count", 0),
                "first_appearance": char_data.get("first_appearance", "N/A"),
                "scenes": char_data.get("scenes", []),
                "scenes_count": len(char_data.get("scenes", []))
            })
        
        # 按对话次数排序
        characters_info.sort(key=lambda x: x["dialogue_count"], reverse=True)
        
        return json.dumps({
            "total_characters": len(characters_info),
            "characters": characters_info
        }, ensure_ascii=False, indent=2)
    
    def _search_script(self, script_text: str, query: str) -> str:
        """
        剧本内容搜索工具函数
        """
        # 首先解析剧本
        parsed = self.parser.parse(script_text)
        
        # 搜索结果
        search_results = []
        
        # 在每个场景中搜索
        for scene_idx, scene in enumerate(parsed["scenes"]):
            for element_idx, element in enumerate(scene["elements"]):
                # 检查元素内容是否包含查询
                if query.lower() in element["content"].lower():
                    search_results.append({
                        "scene_number": scene_idx + 1,
                        "scene_heading": scene["heading"],
                        "element_type": element["type"],
                        "content": element["content"],
                        "line_numbers": {
                            "start": element["start_line"],
                            "end": element["end_line"]
                        }
                    })
        
        return json.dumps({
            "query": query,
            "results_count": len(search_results),
            "results": search_results
        }, ensure_ascii=False, indent=2)
    
    def create_analysis_chain(self) -> SequentialChain:
        """
        创建剧本分析序列链
        """
        if not self.llm:
            print("警告: 无法获取LLM实例，无法创建完整的分析链")
            return None
        
        # 第一步：解析剧本
        parse_template = "请解析以下剧本，并提取关键信息：\n\n{script_text}"
        parse_prompt = PromptTemplate(input_variables=["script_text"], template=parse_template)
        parse_chain = LLMChain(llm=self.llm, prompt=parse_prompt, output_key="parsed_script")
        
        # 第二步：分析角色
        character_template = "基于剧本分析结果，请详细分析主要角色及其关系：\n\n{parsed_script}"
        character_prompt = PromptTemplate(input_variables=["parsed_script"], template=character_template)
        character_chain = LLMChain(llm=self.llm, prompt=character_prompt, output_key="character_analysis")
        
        # 第三步：生成场景总结
        scene_template = "请为每个场景生成简短的视觉描述和情感基调总结：\n\n{parsed_script}"
        scene_prompt = PromptTemplate(input_variables=["parsed_script"], template=scene_template)
        scene_chain = LLMChain(llm=self.llm, prompt=scene_prompt, output_key="scene_summaries")
        
        # 第四步：生成分镜建议
        storyboard_template = """
        基于以下信息，为剧本生成分镜建议，每个场景1-2个镜头：
        
        角色分析：
        {character_analysis}
        
        场景总结：
        {scene_summaries}
        
        请提供每个镜头的：
        1. 镜头类型（特写/中景/全景）
        2. 构图描述
        3. 时长估计
        4. 情感表达建议
        """
        storyboard_prompt = PromptTemplate(
            input_variables=["character_analysis", "scene_summaries"], 
            template=storyboard_template
        )
        storyboard_chain = LLMChain(llm=self.llm, prompt=storyboard_prompt, output_key="storyboard_suggestions")
        
        # 创建序列链
        overall_chain = SequentialChain(
            chains=[parse_chain, character_chain, scene_chain, storyboard_chain],
            input_variables=["script_text"],
            output_variables=["parsed_script", "character_analysis", "scene_summaries", "storyboard_suggestions"],
            verbose=True
        )
        
        return overall_chain
    
    def create_analysis_agent(self) -> Any:
        """
        创建剧本分析智能体
        """
        if not self.llm:
            print("警告: 无法获取LLM实例，无法创建智能体")
            return None
        
        agent = initialize_agent(
            self.tools,
            self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )
        
        return agent
    
    def run_full_analysis(self, script_text: str) -> Dict[str, Any]:
        """
        运行完整的剧本分析
        """
        results = {}
        
        # 使用工具进行分析
        results["parsing"] = json.loads(self._parse_script(script_text))
        results["statistics"] = json.loads(self._analyze_statistics(script_text))
        results["characters"] = json.loads(self._analyze_characters(script_text))
        results["scenes"] = json.loads(self._extract_scenes(script_text))
        
        return results
    
    def generate_storyboard_from_script(self, script_text: str) -> Dict[str, Any]:
        """
        从剧本生成分镜
        """
        # 首先运行完整分析
        analysis_results = self.run_full_analysis(script_text)
        
        # 基础分镜信息
        storyboard = {
            "title": "剧本分镜",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_scenes": analysis_results["scenes"]["total_scenes"],
            "shots": []
        }
        
        # 为每个场景生成分镜
        for scene in analysis_results["scenes"]["scenes"]:
            # 基于场景信息创建基础分镜
            scene_shots = [
                {
                    "shot_id": f"{scene['scene_number']}-1",
                    "scene_number": scene["scene_number"],
                    "scene_heading": scene["heading"],
                    "shot_type": "建立镜头",
                    "description": f"展示{scene['heading']}的整体环境",
                    "estimated_duration": 3.0,
                    "characters": scene["characters"]
                },
                {
                    "shot_id": f"{scene['scene_number']}-2",
                    "scene_number": scene["scene_number"],
                    "scene_heading": scene["heading"],
                    "shot_type": "中景",
                    "description": f"聚焦于场景中的主要角色互动",
                    "estimated_duration": 5.0,
                    "characters": scene["characters"]
                }
            ]
            
            storyboard["shots"].extend(scene_shots)
        
        # 计算总分镜数
        storyboard["total_shots"] = len(storyboard["shots"])
        
        return storyboard


def example_basic_analysis():
    """
    基本剧本分析示例
    """
    print("\n=== 基本剧本分析示例 ===")
    
    # 示例剧本
    sample_script = """
    INT. CAFETERIA - NOON
    
    繁忙的公司食堂，员工们三三两两地坐在餐桌旁吃饭聊天。ZHANG和LIU坐在靠窗的位置。
    
    ZHANG
    (狼吞虎咽)
    今天的工作太多了，我早上7点就到公司了。
    
    LIU
    (摇头)
    你总是这么拼命。项目截止日期不是还有一周吗？
    
    ZHANG
    我想提前完成，这样周末就能好好休息了。
    
    EXT. PARK - AFTERNOON
    
    阳光明媚的公园，孩子们在玩耍。WANG坐在长椅上看报纸。
    
    LI (走进画面)
    老王，在这里碰到你真巧！
    
    WANG
    是啊，我每天下午都来这里坐坐。你呢？
    
    LI
    我在附近办事，顺便过来走走。
    """
    
    # 创建工作流实例
    workflow = ScriptAnalysisWorkflow(embedding_model_name="openai", storage_dir=None)
    
    print("\n1. 使用脚本解析工具:")
    parse_result = workflow._parse_script(sample_script)
    parsed = json.loads(parse_result)
    print(f"解析出 {parsed['scenes_count']} 个场景和 {parsed['characters_count']} 个角色")
    print(f"角色列表: {', '.join(parsed['characters'])}")
    
    print("\n2. 使用统计分析工具:")
    stats_result = workflow._analyze_statistics(sample_script)
    stats = json.loads(stats_result)
    print(f"总场景数: {stats['total_scenes']}")
    print(f"总对话数: {stats['total_dialogues']}")
    print(f"角色对话统计:")
    for char, count in stats['character_dialogues'].items():
        print(f"  - {char}: {count}次对话")
    
    print("\n3. 使用角色分析工具:")
    chars_result = workflow._analyze_characters(sample_script)
    chars = json.loads(chars_result)
    print(f"共有 {chars['total_characters']} 个角色")
    
    print("\n4. 使用场景提取工具:")
    scenes_result = workflow._extract_scenes(sample_script)
    scenes = json.loads(scenes_result)
    print(f"场景列表:")
    for scene in scenes['scenes']:
        print(f"  {scene['scene_number']}. {scene['heading']} - 角色: {', '.join(scene['characters'])}")
    
    print("\n5. 使用搜索工具:")
    search_result = workflow._search_script(sample_script, "工作")
    search = json.loads(search_result)
    print(f"搜索'工作'的结果: {search['results_count']} 项")
    for result in search['results']:
        print(f"  - 在场景 {result['scene_number']} ({result['scene_heading']}) 中找到")
        print(f"    内容: {result['content']}")


def example_full_workflow():
    """
    完整工作流示例
    """
    print("\n=== 完整剧本分析工作流示例 ===")
    
    # 示例剧本
    sample_script = """
    INT. OFFICE - MORNING
    
    明亮的办公室，员工们正在工作。ZHANG坐在办公桌前，眉头紧锁地看着电脑屏幕。
    WANG拿着文件走过来。
    
    WANG
    张经理，这是您要的季度报告。
    
    ZHANG
    (接过文件)
    谢谢。放在这儿吧。
    
    WANG
    需要我帮您准备明天的会议资料吗？
    
    ZHANG
    好的，那就麻烦你了。
    
    WANG点头离开。ZHANG继续工作，表情依然严肃。
    
    INT. COFFEE SHOP - AFTERNOON
    
    温馨的咖啡店。ZHANG和LIU坐在角落的桌子旁，面前放着咖啡。
    
    LIU
    最近工作压力很大吧？看你一直愁眉苦脸的。
    
    ZHANG
    是啊，项目进度有点滞后，我正为此发愁呢。
    
    LIU
    别太担心，你团队的能力我是知道的，一定能按时完成的。
    
    ZHANG勉强笑了笑，喝了一口咖啡。
    """
    
    # 创建工作流实例
    workflow = ScriptAnalysisWorkflow(embedding_model_name="openai", storage_dir=None)
    
    # 运行完整分析
    print("\n执行完整剧本分析...")
    full_results = workflow.run_full_analysis(sample_script)
    
    print(f"\n分析完成！总场景数: {full_results['statistics']['total_scenes']}")
    print(f"总角色数: {full_results['statistics']['total_characters']}")
    print(f"总对话数: {full_results['statistics']['total_dialogues']}")
    
    # 生成分镜
    print("\n生成分镜建议...")
    storyboard = workflow.generate_storyboard_from_script(sample_script)
    
    print(f"\n分镜生成完成！共 {storyboard['total_shots']} 个镜头")
    print("\n前几个镜头示例:")
    for i, shot in enumerate(storyboard['shots'][:4], 1):
        print(f"\n镜头 {i} ({shot['shot_id']}):")
        print(f"  场景: {shot['scene_heading']}")
        print(f"  类型: {shot['shot_type']}")
        print(f"  描述: {shot['description']}")
        print(f"  时长: {shot['estimated_duration']}秒")
        print(f"  角色: {', '.join(shot['characters'])}")


def main():
    """
    运行所有示例
    """
    print("===== 剧本分析工作流示例 =====")
    
    try:
        # 运行基本分析示例
        example_basic_analysis()
        
        # 运行完整工作流示例
        example_full_workflow()
        
    except Exception as e:
        print(f"示例运行出错: {str(e)}")
    
    print("\n===== 示例结束 =====")
    print("\n使用提示:")
    print("1. 可以将示例中的剧本替换为您自己的剧本")
    print("2. 要使用LLM相关功能（如分析链和智能体），请确保配置了有效的API密钥")
    print("3. 对于大型剧本，建议配置持久化存储目录")
    print("4. 可以根据需要扩展工具列表和分析功能")


if __name__ == "__main__":
    main()