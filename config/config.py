# -*- coding: utf-8 -*-
"""
@FileName: config.py
@Description: 配置管理模块，负责读取和管理应用配置
@Author: HengLine
@Time: 2025/08 - 2025/11
"""
import json
import os
from typing import Dict, Any, Optional

from dotenv import load_dotenv

from hengline.logger import error, warning

# 加载.env文件中的环境变量
load_dotenv()

# 默认配置
DEFAULT_CONFIG = {
    "app": {
        "name": "Script-to-Shot AI Agent",
        "version": "1.0.0",
        "debug": False
    },
    "api": {
        "host": "0.0.0.0",
        "port": 8000,
        "workers": 1
    },
    "llm": {
        "provider": "openai",
        "base_url": "https://api.openai.com/v1",
        "api_key": "",
        "timeout": 60,
        "default_model": "gpt-4o",
        "fallback_model": "",
        "temperature": 0.7,
        "max_tokens": 2000,
        "retry_count": 3
    },
    "storyboard": {
        "default_duration_per_shot": 5,
        "max_duration_deviation": 0.5,
        "max_retries": 2,
        "default_style": "realistic",
        "supported_styles": ["realistic", "anime", "cinematic", "cartoon"]
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
}

# 全局配置实例
_config_instance: Optional[Dict[str, Any]] = None


def get_config_path() -> str:
    """
    获取配置文件路径
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, 'config.json')
    return config_path


def _update_api_config_from_env(config: Dict[str, Any]) -> None:
    """
    从环境变量更新API配置
    优先从环境变量获取端口、主机等API配置
    """
    api_config = config.get("api", {})
    
    # 从环境变量获取端口配置，支持PORT或API_PORT
    port_env_var = os.environ.get("PORT")
    if not port_env_var:
        port_env_var = os.environ.get("API_PORT")
    
    if port_env_var:
        try:
            api_config["port"] = int(port_env_var)
        except ValueError:
            warning(f"无效的端口号: {port_env_var}，使用默认值")
    
    # 从环境变量获取主机配置
    host_env_var = os.environ.get("HOST")
    if not host_env_var:
        host_env_var = os.environ.get("API_HOST")
    
    if host_env_var:
        api_config["host"] = host_env_var
    
    # 从环境变量获取工作进程数
    workers_env_var = os.environ.get("WORKERS")
    if not workers_env_var:
        workers_env_var = os.environ.get("API_WORKERS")
    
    if workers_env_var:
        try:
            api_config["workers"] = int(workers_env_var)
        except ValueError:
            warning(f"无效的工作进程数: {workers_env_var}，使用默认值")

def _update_ai_config_from_env(config: Dict[str, Any]) -> None:
    """
    从环境变量更新AI配置
    根据AI_PROVIDER环境变量动态加载相应的API配置
    确保环境变量中的provider值具有最高优先级
    """
    ai_config = config.get("llm", {})
    
    # 优先从环境变量获取AI提供商，如果不存在则使用配置中的值，最后使用默认值
    env_provider = os.environ.get("AI_PROVIDER")
    if env_provider:
        # 环境变量存在，优先使用
        provider = env_provider.lower()
    else:
        # 环境变量不存在，使用配置中的值或默认值
        provider = ai_config.get("provider", "openai").lower()
    
    ai_config["provider"] = provider
    
    # 动态加载指定提供商的API配置
    # API密钥命名格式: {PROVIDER}_API_KEY
    # Base URL命名格式: {PROVIDER}_BASE_URL
    # 模型命名格式: {PROVIDER}_MODEL
    # 备用模型命名格式: {PROVIDER}_FALLBACK_MODEL
    provider_upper = provider.upper()
    api_key_env_var = f"{provider_upper}_API_KEY"
    base_url_env_var = f"{provider_upper}_BASE_URL"
    model_env_var = f"{provider_upper}_MODEL"
    fallback_model_env_var = f"{provider_upper}_FALLBACK_MODEL"
    
    # 加载API密钥
    if os.environ.get(api_key_env_var):
        ai_config["api_key"] = os.environ[api_key_env_var]

        if provider == "qwen":
            os.environ["DASHSCOPE_API_KEY"] = ai_config["api_key"]
    
    # 加载Base URL
    if os.environ.get(base_url_env_var):
        ai_config["base_url"] = os.environ[base_url_env_var]
    
    # 加载特定提供商的模型配置
    if os.environ.get(model_env_var):
        ai_config["default_model"] = os.environ[model_env_var]
    
    # 加载特定提供商的备用模型配置（可选）
    if os.environ.get(fallback_model_env_var):
        ai_config["fallback_model"] = os.environ[fallback_model_env_var]
    
    # 加载统一的超时时间配置
    if os.environ.get("AI_API_TIMEOUT"):
        try:
            ai_config["timeout"] = int(os.environ["AI_API_TIMEOUT"])
        except ValueError:
            warning("Invalid AI_API_TIMEOUT value, using default")

    # 加载温度参数
    if os.environ.get("AI_TEMPERATURE"):
        try:
            ai_config["temperature"] = float(os.environ["AI_TEMPERATURE"])
        except ValueError:
            warning("Invalid AI_TEMPERATURE value, using default")
    
    # 加载最大令牌数
    if os.environ.get("AI_MAX_TOKENS"):
        try:
            ai_config["max_tokens"] = int(os.environ["AI_MAX_TOKENS"])
        except ValueError:
            warning("Invalid AI_MAX_TOKENS value, using default")
    
    # 加载重试次数
    if os.environ.get("AI_RETRY_COUNT"):
        try:
            ai_config["retry_count"] = int(os.environ["AI_RETRY_COUNT"])
        except ValueError:
            warning("Invalid AI_RETRY_COUNT value, using default")


def get_settings_config() -> Dict[str, Any]:
    """
    获取应用设置配置
    """
    global _config_instance

    if _config_instance is not None:
        return _config_instance

    try:
        config_path = get_config_path()
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 合并默认配置和用户配置
                merged_config = DEFAULT_CONFIG.copy()
                merged_config.update(config)
                # 从环境变量更新AI模型配置
                _update_ai_config_from_env(merged_config)
                # 从环境变量更新API配置
                _update_api_config_from_env(merged_config)
                _config_instance = merged_config
                return merged_config
        else:
            # 如果配置文件不存在，返回默认配置
            default_config = DEFAULT_CONFIG.copy()
            _update_ai_config_from_env(default_config)
            _update_api_config_from_env(default_config)
            _config_instance = default_config
            return default_config
    except Exception as e:
        # 如果读取配置文件出错，返回默认配置
        error(f"读取配置文件失败: {str(e)}")
        default_config = DEFAULT_CONFIG.copy()
        _update_ai_config_from_env(default_config)
        _update_api_config_from_env(default_config)
        _config_instance = default_config
        return default_config


def get_app_root() -> str:
    """
    获取应用根目录的绝对路径
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_root = os.path.dirname(current_dir)  # 上一级目录就是应用根目录
    return app_root

def get_storyboard_config() -> Dict[str, Any]:
    """
    获取分镜配置
    """
    config = get_settings_config()
    return config.get("storyboard", {})


def get_ai_config() -> Dict[str, Any]:
    """
    获取AI配置
    """
    config = get_settings_config()
    return config.get("llm", {})


def is_debug_mode() -> bool:
    """
    检查是否为调试模式
    """
    config = get_settings_config()
    return config.get("app", {}).get("debug", False)


def get_supported_styles() -> list:
    """
    获取支持的视频风格列表
    """
    storyboard_config = get_storyboard_config()
    return storyboard_config.get("supported_styles", ["realistic"])
