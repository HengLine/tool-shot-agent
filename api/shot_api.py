"""
@FileName: a2a_api.py
@Description:  分镜生成API，通过A2A协议调用分镜生成功能
@Author: HengLine
@Time: 2025/10/23 11:19
"""
from typing import Optional, Dict, Any, List

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel

from hengline.generate_agent import generate_storyboard
from hengline.logger import info, error, log_with_context

app = APIRouter()


# 定义请求模型
class StoryboardRequest(BaseModel):
    """
    分镜生成请求模型
    """
    script_text: str
    style: str = "realistic"
    duration_per_shot: int = 5
    prev_continuity_state: Optional[Dict[str, Any]] = None
    debug: bool = False


# 定义响应模型
class ShotModel(BaseModel):
    """
    分镜模型
    """
    shot_id: str
    start_time: float
    end_time: float
    duration: float
    description: str
    prompt_en: str
    characters: List[str]
    dialogue: str
    camera_angle: str
    continuity_anchors: List[str]


class StoryboardResponse(BaseModel):
    """
    分镜生成响应模型
    """
    total_shots: int
    storyboard_title: str
    shots: List[ShotModel]
    final_continuity_state: Optional[Dict[str, Any]] = None
    total_duration: float
    status: str
    warnings: List[str]
    metadata: Optional[Dict[str, Any]] = None


@app.post("/generate_storyboard", response_model=StoryboardResponse)
def a2a_storyboard(request: StoryboardRequest):
    """
    通过A2A协议调用分镜生成功能

    Args:
        request: 分镜生成请求参数

    Returns:
        StoryboardResponse: 分镜生成结果
    """
    try:
        # 记录请求日志
        log_with_context(
            "INFO",
            "接收到分镜生成请求",
            {
                "style": request.style,
                "duration": request.duration_per_shot,
                "has_prev_state": request.prev_continuity_state is not None
            }
        )

        # 调用分镜生成功能
        result = generate_storyboard(
            script_text=request.script_text,
            style=request.style,
            duration_per_shot=request.duration_per_shot,
            prev_continuity_state=request.prev_continuity_state
        )

        # 确保结果包含必要字段
        if "shots" not in result:
            raise ValueError("分镜生成结果缺少shots字段")

        # 转换为响应格式
        response = StoryboardResponse(
            total_shots=result.get("total_shots", len(result["shots"])),
            storyboard_title=result.get("storyboard_title", "未命名剧本"),
            shots=result["shots"],
            final_continuity_state=result.get("final_continuity_state"),
            total_duration=result.get("total_duration", sum(shot.get("duration", 5) for shot in result["shots"])),
            status=result.get("status", "success"),
            warnings=result.get("warnings", []),
            metadata=result.get("metadata")
        )

        info(f"分镜生成成功，共生成 {response.total_shots} 个分镜")
        return response

    except ValueError as e:
        error(f"参数错误: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error(f"分镜生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")
