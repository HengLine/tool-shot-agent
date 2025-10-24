#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单工具使用示例
展示如何直接使用tool目录下的工具执行剧本分析和拆解任务
"""

import json
from typing import Dict, Any, List

# 直接导入tool目录下的工具
from hengline.tools.script_parser_tool import ScriptParser, Scene, Character, SceneElement
from hengline.tools.script_intelligence_tool import (
    ScriptIntelligence, 
    create_script_intelligence,
    analyze_script
)
from hengline.tools.action_duration_tool import ActionDurationEstimator


def example_basic_parsing():
    """
    基础剧本解析示例
    展示如何使用ScriptParser工具解析剧本结构
    """
    print("\n=== 基础剧本解析示例 ===")
    
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
    """
    
    # 创建ScriptParser实例
    parser = ScriptParser()
    
    # 执行解析
    print("执行剧本解析...")
    parsed_result = parser.parse(sample_script)
    
    # 显示解析结果
    print(f"\n解析结果摘要:")
    print(f"1. 场景数量: {len(parsed_result['scenes'])}")
    print(f"2. 角色数量: {len(parsed_result['characters'])}")
    
    # 详细显示场景信息
    print(f"\n场景详情:")
    for i, scene in enumerate(parsed_result['scenes']):
        print(f"\n场景 {i+1}: {scene['heading']}")
        print(f"   行范围: {scene['start_line']}-{scene['end_line']}")
        print(f"   角色: {', '.join(scene['characters'])}")
        print(f"   元素数量: {len(scene['elements'])}")
        
        # 显示前几个元素
        print(f"   元素示例:")
        for j, element in enumerate(scene['elements'][:3]):  # 只显示前3个元素
            element_type = element['type']
            content = element['content'][:50] + "..." if len(element['content']) > 50 else element['content']
            print(f"     {j+1}. [{element_type}]: {content}")
    
    # 显示角色信息
    print(f"\n角色详情:")
    for name, info in parsed_result['characters'].items():
        print(f"- {name}: 对话次数={info.get('dialogue_count', 0)}, 出场场景={len(info.get('scenes', []))}")


def example_script_intelligence():
    """
    剧本智能分析示例
    展示如何使用ScriptIntelligence工具进行高级分析
    """
    print("\n=== 剧本智能分析示例 ===")
    
    # 示例剧本
    sample_script = """
    EXT. PARK - DAY
    
    阳光明媚的公园，人们在散步、野餐。ZHANG和LIANG坐在长椅上，聊得很投机。
    
    ZHANG
    这里环境真好，我们应该常来。
    
    LIANG
    是啊，远离城市的喧嚣，让人感觉很放松。
    
    ZHANG从包里拿出相机，开始拍照。
    
    ZHANG
    看那边的风景多美啊！
    
    INT. CAFE - AFTERNOON
    
    温馨的咖啡馆，ZHANG和LIANG坐在靠窗的位置，桌上放着咖啡和蛋糕。
    
    LIANG
    这家的咖啡真不错。
    
    ZHANG
    你喜欢就好，这是我们第一次正式约会，我想给你留下好印象。
    
    LIANG微笑着看着ZHANG。
    
    LIANG
    你已经做到了。
    """
    
    # 创建ScriptIntelligence实例
    print("初始化剧本智能分析工具...")
    script_intel = create_script_intelligence(embedding_model_name="openai")
    
    # 分析剧本
    print("分析剧本内容...")
    analysis_result = script_intel.analyze_script_text(sample_script)
    
    # 显示分析结果
    print(f"\n剧本分析摘要:")
    print(f"1. 场景数量: {analysis_result.get('scene_count', 0)}")
    print(f"2. 角色数量: {analysis_result.get('character_count', 0)}")
    print(f"3. 主要角色: {', '.join(analysis_result.get('main_characters', []))}")
    
    # 显示情感分析
    emotions = analysis_result.get('emotional_tone', {})
    if emotions:
        print(f"\n情感分析:")
        for emotion, score in emotions.items():
            print(f"- {emotion}: {score:.2f}")
    
    # 获取对话分析
    if hasattr(script_intel, 'analyze_dialogues'):
        dialogue_analysis = script_intel.analyze_dialogues(sample_script)
        if dialogue_analysis:
            print(f"\n对话分析:")
            print(f"总对话数量: {dialogue_analysis.get('total_dialogues', 0)}")
            print(f"角色对话分布: {dialogue_analysis.get('dialogues_by_character', {})}")


def example_action_duration():
    """
    动作时长估计示例
    展示如何使用ActionDurationEstimator工具估计动作时长
    """
    print("\n=== 动作时长估计示例 ===")
    
    try:
        # 创建ActionDurationEstimator实例
        print("初始化动作时长估计器...")
        estimator = ActionDurationEstimator()
        
        # 示例动作描述
        actions = [
            "LI打开门，走进房间，环视四周",
            "ZHANG从包里拿出文件，仔细阅读",
            "两人拥抱，然后分开，互相微笑",
            "角色快速奔跑穿过街道，避开车辆",
            "他坐下，倒了一杯咖啡，慢慢品尝"
        ]
        
        # 估计每个动作的时长
        print("\n动作时长估计结果:")
        for i, action in enumerate(actions):
            duration = estimator.estimate_duration(action)
            print(f"{i+1}. '{action}' - 估计时长: {duration:.2f} 秒")
        
    except Exception as e:
        print(f"\n动作时长估计出错: {str(e)}")
        print("提示: 可能需要配置正确的配置文件路径")


def example_storyboard_generation():
    """
    分镜生成示例
    基于解析的剧本自动生成分镜建议
    """
    print("\n=== 分镜生成示例 ===")
    
    # 示例剧本
    sample_script = """
    INT. BEDROOM - MORNING
    
    阳光透过窗帘照进卧室。LI躺在床上，闹钟响起。
    
    LI伸手关掉闹钟，起床，走向窗户，拉开窗帘。阳光洒满房间。
    
    LI
    又是美好的一天。
    
    INT. KITCHEN - MORNING
    
    LI走进厨房，打开冰箱，取出牛奶和面包。
    
    LI开始准备早餐，面包机发出叮的一声。
    
    突然，电话响起。LI擦了擦手，接起电话。
    
    LI
    喂？
    """
    
    # 解析剧本
    parser = ScriptParser()
    parsed = parser.parse(sample_script)
    
    # 尝试初始化时长估计器
    try:
        estimator = ActionDurationEstimator()
        has_duration_tool = True
    except:
        has_duration_tool = False
        print("注意: 无法初始化动作时长估计器，将使用默认时长")
    
    # 生成分镜
    storyboard = {
        "标题": "示例剧本分镜",
        "场景数": len(parsed["scenes"]),
        "分镜列表": []
    }
    
    shot_id = 1
    
    for scene_idx, scene in enumerate(parsed["scenes"]):
        # 场景介绍镜头
        scene_shot = {
            "镜头号": shot_id,
            "场景": scene["heading"],
            "类型": "全景",
            "描述": f"展示{scene['heading']}的整体环境",
            "时长(秒)": 3
        }
        storyboard["分镜列表"].append(scene_shot)
        shot_id += 1
        
        # 分析场景中的动作和对话
        for element in scene["elements"]:
            if element["type"] == "action":
                # 为动作生成特写镜头
                action_desc = element["content"]
                
                # 估计时长
                if has_duration_tool:
                    try:
                        duration = estimator.estimate_duration(action_desc)
                    except:
                        duration = 5  # 默认时长
                else:
                    duration = 5
                
                action_shot = {
                    "镜头号": shot_id,
                    "场景": scene["heading"],
                    "类型": "中景",
                    "描述": f"聚焦角色动作: {action_desc[:50]}",
                    "时长(秒)": round(duration, 2)
                }
                storyboard["分镜列表"].append(action_shot)
                shot_id += 1
            
            elif element["type"] == "dialogue":
                # 为对话生成特写镜头
                char_name = element.get("character", "未知角色")
                dialogue_shot = {
                    "镜头号": shot_id,
                    "场景": scene["heading"],
                    "类型": "特写",
                    "描述": f"{char_name}的对话镜头",
                    "对话内容": element["content"],
                    "时长(秒)": 3  # 对话默认时长
                }
                storyboard["分镜列表"].append(dialogue_shot)
                shot_id += 1
    
    # 显示分镜结果
    print(f"\n生成的分镜数量: {len(storyboard['分镜列表'])}")
    print("\n分镜预览（前5个）:")
    for i, shot in enumerate(storyboard["分镜列表"][:5]):
        print(f"\n镜头 {i+1}:")
        for key, value in shot.items():
            print(f"  {key}: {value}")


def example_script_segmentation():
    """
    剧本分段示例
    展示如何将剧本按照合理的逻辑拆分成段落
    """
    print("\n=== 剧本分段示例 ===")
    
    # 示例剧本
    sample_script = """
    INT. OFFICE - DAY
    
    繁忙的办公室，人们都在工作。WANG坐在电脑前，眉头紧锁，正在处理一份重要文件。
    
    ZHAO走进办公室，看到WANG在工作，轻轻敲了敲桌子。
    
    ZHAO
    王总，这份报告需要您签字。
    
    WANG抬起头，接过报告，快速浏览。
    
    WANG
    好的，我马上处理。
    
    ZHAO
    还有，李总说下午三点有个紧急会议。
    
    WANG
    知道了，我会准时参加的。
    
    ZHAO离开。WANG继续工作，然后看了看手表，显得有些焦虑。
    
    WANG拿起电话，拨了一个号码。
    
    WANG (对着电话)
    喂，张秘书吗？帮我准备下午会议的资料。
    """
    
    # 创建ScriptParser实例
    parser = ScriptParser()
    parsed = parser.parse(sample_script)
    
    # 执行分段逻辑
    segments = []
    for scene in parsed["scenes"]:
        current_segment = {
            "场景": scene["heading"],
            "段落": []
        }
        
        # 根据元素类型分组
        segment_text = []
        for element in scene["elements"]:
            # 遇到新的对话，结束当前段落并开始新段落
            if element["type"] == "dialogue" and segment_text:
                current_segment["段落"].append("\n".join(segment_text))
                segment_text = []
            
            # 添加当前元素
            if element["type"] == "action":
                segment_text.append(element["content"])
            elif element["type"] == "dialogue":
                segment_text.append(f"{element['character']}\n{element['content']}")
        
        # 添加最后一个段落
        if segment_text:
            current_segment["段落"].append("\n".join(segment_text))
        
        segments.append(current_segment)
    
    # 显示分段结果
    for i, segment in enumerate(segments):
        print(f"\n场景 {i+1}: {segment['场景']}")
        print(f"分段数: {len(segment['段落'])}")
        
        for j, para in enumerate(segment["段落"]):
            print(f"\n段落 {j+1}:")
            print(f"{para}")
            print("---")


def example_combined_analysis():
    """
    综合分析示例
    展示如何组合使用多个工具进行综合分析
    """
    print("\n=== 剧本综合分析示例 ===")
    
    # 示例剧本
    sample_script = """
    EXT. STREET - NIGHT
    
    昏暗的街道，空无一人。LIANG快步走着，不时回头张望，显得很紧张。
    
    突然，一个黑影从巷子里冲出来，拦住了LIANG的去路。
    
    THIEF
    把钱拿出来！
    
    LIANG吓得发抖，慢慢从口袋里掏出钱包。
    
    LIANG
    请...请不要伤害我。
    
    就在这时，ZHANG从对面跑来，看到这一幕，立即冲了过去。
    
    ZHANG
    住手！
    
    THIEF看到ZHANG冲过来，拿起钱包就跑。
    
    ZHANG紧追不舍。
    """
    
    # 创建工具实例
    parser = ScriptParser()
    try:
        estimator = ActionDurationEstimator()
        has_duration_tool = True
    except:
        has_duration_tool = False
    
    # 1. 基础解析
    print("1. 执行基础解析...")
    parsed = parser.parse(sample_script)
    
    # 2. 统计分析
    print("\n2. 统计分析结果:")
    total_dialogues = sum(1 for scene in parsed["scenes"] 
                         for element in scene["elements"] 
                         if element["type"] == "dialogue")
    total_actions = sum(1 for scene in parsed["scenes"] 
                       for element in scene["elements"] 
                       if element["type"] == "action")
    
    print(f"- 场景数: {len(parsed['scenes'])}")
    print(f"- 角色数: {len(parsed['characters'])}")
    print(f"- 对话数: {total_dialogues}")
    print(f"- 动作描述数: {total_actions}")
    
    # 3. 时长估计
    if has_duration_tool:
        print("\n3. 时长估计:")
        total_estimated_time = 0
        for scene in parsed["scenes"]:
            for element in scene["elements"]:
                if element["type"] == "action":
                    try:
                        duration = estimator.estimate_duration(element["content"])
                        total_estimated_time += duration
                        print(f"  - 动作: '{element['content'][:30]}...' - {duration:.2f}秒")
                    except:
                        pass
                elif element["type"] == "dialogue":
                    # 对话默认2秒/行
                    duration = len(element["content"].split('\n')) * 2
                    total_estimated_time += duration
        
        print(f"\n总估计时长: {total_estimated_time:.2f}秒 ({total_estimated_time/60:.2f}分钟)")
    
    # 4. 角色互动分析
    print("\n4. 角色互动分析:")
    character_interactions = {}
    
    for scene in parsed["scenes"]:
        characters = scene["characters"]
        if len(characters) >= 2:
            # 生成角色对
            for i in range(len(characters)):
                for j in range(i+1, len(characters)):
                    pair = tuple(sorted([characters[i], characters[j]]))
                    character_interactions[pair] = character_interactions.get(pair, 0) + 1
    
    if character_interactions:
        print("角色互动对:")
        for pair, count in character_interactions.items():
            print(f"  - {pair[0]} 和 {pair[1]}: {count}次互动")
    else:
        print("没有发现角色间的互动")
    
    # 5. 场景情绪分析（简化版）
    print("\n5. 场景情绪分析（简化版）:")
    for scene in parsed["scenes"]:
        # 简单的关键词情绪分析
        text = " ".join([e["content"] for e in scene["elements"]])
        emotions = []
        
        if any(word in text for word in ["紧张", "发抖", "害怕"]):
            emotions.append("紧张")
        if any(word in text for word in ["冲", "追", "快"]):
            emotions.append("动作激烈")
        if any(word in text for word in ["昏暗", "空无一人"]):
            emotions.append("悬疑")
        
        if emotions:
            print(f"  - {scene['heading']}: {', '.join(emotions)}")
        else:
            print(f"  - {scene['heading']}: 中性")


def main():
    """
    运行所有示例
    """
    print("===== 剧本工具使用示例集 =====")
    
    # 运行各个示例
    try:
        # 基础解析示例
        example_basic_parsing()
        
        # 智能分析示例
        example_script_intelligence()
        
        # 动作时长估计示例
        example_action_duration()
        
        # 分镜生成示例
        example_storyboard_generation()
        
        # 剧本分段示例
        example_script_segmentation()
        
        # 综合分析示例
        example_combined_analysis()
        
    except Exception as e:
        print(f"\n示例运行出错: {str(e)}")
    
    print("\n===== 示例结束 =====")
    print("\n使用提示:")
    print("1. 所有示例都直接使用tool目录下的工具，无需额外配置")
    print("2. 可以根据需要选择使用特定的工具功能")
    print("3. ActionDurationEstimator可能需要配置正确的配置文件路径")
    print("4. 对于生产环境，请确保所有依赖已正确安装")
    print("\n工具列表总结:")
    print("- ScriptParser: 基础剧本解析，提取场景、角色、对话等")
    print("- ScriptIntelligence: 智能分析，情感分析、主题识别等")
    print("- ActionDurationEstimator: 动作时长估计")


if __name__ == "__main__":
    main()