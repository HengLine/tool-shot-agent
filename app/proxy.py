# -*- coding: utf-8 -*-
"""
@FileName: proxy.py
@Description: 代理服务模块 - 处理API请求的代理和转发
@Author: HengLine
@Time: 2025/10/6
"""
import asyncio
import os

import httpx
import starlette
# import websockets
from fastapi import APIRouter, WebSocket
from httpx import ConnectError
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import PlainTextResponse, StreamingResponse

from hengline.logger import logger

router = APIRouter()


def reverse_proxy_maker(url_type: str, full_path: bool = False):
    if url_type == "tensorboard":
        host = os.environ.get("NOME_TENSORBOARD_HOST", "127.0.0.1")
        port = os.environ.get("NOME_TENSORBOARD_PORT", "6006")
    elif url_type == "tageditor":
        host = os.environ.get("MIKAZUKI_TAGEDITOR_HOST", "127.0.0.1")
        port = os.environ.get("MIKAZUKI_TAGEDITOR_PORT", "28001")

    client = httpx.AsyncClient(base_url=f"http://{host}:{port}/", proxies={}, trust_env=False, timeout=360)

    async def _reverse_proxy(request: Request):
        if full_path:
            url = httpx.URL(path=request.url.path, query=request.url.query.encode("utf-8"))
        else:
            url = httpx.URL(
                path=request.path_params.get("path", ""),
                query=request.url.query.encode("utf-8")
            )
        rp_req = client.build_request(
            request.method, url,
            headers=request.headers.raw,
            content=request.stream() if request.method != "GET" else None
        )
        try:
            rp_resp = await client.send(rp_req, stream=True)
        except ConnectError:
            return PlainTextResponse(
                content="The requested service not started yet or service started fail. This may cost a while when you first time startup\n请求的服务尚未启动或启动失败。若是第一次启动，可能需要等待一段时间后再刷新网页。",
                status_code=502
            )
        return StreamingResponse(
            rp_resp.aiter_raw(),
            status_code=rp_resp.status_code,
            headers=rp_resp.headers,
            background=BackgroundTask(rp_resp.aclose),
        )

    return _reverse_proxy
