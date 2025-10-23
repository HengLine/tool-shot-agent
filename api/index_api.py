# -*- coding: utf-8 -*-
"""
@FileName: index_api.py
@Description: FastAPI应用，提供索引接口
@Author: HengLine
@Time: 2025/10/22 23:40
"""
import uvicorn
from fastapi import APIRouter

from hengline.logger import info, error

app = APIRouter()


@app.get("/")
def read_root():
    """
    根路径，提供API信息
    """
    return {
        "message": "剧本分镜智能体服务",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    """
    健康检查接口
    """
    return {"status": "healthy"}


@app.get("/config/styles")
def get_supported_styles():
    """
    获取支持的视频风格列表
    """
    from config.config import get_supported_styles
    return {
        "supported_styles": get_supported_styles(),
        "default_style": "realistic"
    }


if __name__ == "__main__":
    # 启动FastAPI服务器
    try:
        info("正在启动FastAPI服务器...")
        info("访问 http://127.0.0.1:8000/docs 查看API文档")
        uvicorn.run(
            "hengline.app_fast:app",
            host="127.0.0.1",
            port=8000,
            reload=True  # 开发环境启用自动重载
        )
    except Exception as e:
        error(f"FastAPI服务器启动失败: {str(e)}")
        raise
