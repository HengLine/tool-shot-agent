# -*- coding: utf-8 -*-
"""
@FileName: openai_compat.py
@Description: OpenAI兼容层模块，提供核心抽象基类和包装器
@Author: HengLine
@Time: 2025/10/6
"""
import abc
from typing import Any, Callable, Dict, List, Optional


class BaseOpenAIResponse:
    """基础的OpenAI格式响应类"""

    def __init__(self, content: str = ""):
        class Choice:
            def __init__(self, content: str):
                class Message:
                    def __init__(self, content: str):
                        self.content = content

                self.message = Message(content)

        self.choices = [Choice(content)]
        
    # 确保对象可以直接转换为字符串时返回content内容
    def __str__(self):
        if self.choices and len(self.choices) > 0:
            choice = self.choices[0]
            if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                return str(choice.message.content)
        return ""
    
    # 提供方便访问content的方法
    def get_content(self):
        """获取响应内容"""
        return self.__str__()


class OpenAICompat(abc.ABC):
    """OpenAI API兼容抽象基类"""

    def __init__(self):
        # 创建chat属性
        self.chat = self.Chat(self._create_completion_impl)

    class Chat:
        """Chat接口实现"""

        def __init__(self, create_completion_impl: Callable):
            # 创建completions属性
            self.completions = self.Completions(create_completion_impl)

        class Completions:
            """Completions接口实现"""

            def __init__(self, create_completion_impl: Callable):
                self._create_completion_impl = create_completion_impl

            def create(self, model: str, messages: List[Dict], temperature: Optional[float] = None,
                       max_tokens: Optional[int] = None, response_format: Optional[Dict] = None, **kwargs) -> Any:
                """创建OpenAI格式的completion请求"""
                # 调用具体实现方法
                return self._create_completion_impl(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                    **kwargs
                )

    @abc.abstractmethod
    def _create_completion_impl(self, **kwargs) -> Any:
        """抽象方法，子类必须实现此方法来提供具体的completion实现"""
        pass


class OpenAICompatibleWrapper:
    """OpenAI API兼容包装器
    用于快速将任何AI模型客户端包装为OpenAI API兼容格式
    """

    def __init__(self, completion_handler: Callable):
        """初始化包装器
        Args:
            completion_handler: 处理completion请求的函数，返回响应内容或字典
        """
        self._completion_handler = completion_handler
        self.chat = self.Chat(self._handle_completion)

    class Chat:
        """Chat接口实现"""

        def __init__(self, handle_completion: Callable):
            self.completions = self.Completions(handle_completion)

        class Completions:
            """Completions接口实现"""

            def __init__(self, handle_completion: Callable):
                self._handle_completion = handle_completion

            def create(self, **kwargs) -> Any:
                """创建completion请求"""
                return self._handle_completion(**kwargs)

    def _handle_completion(self, **kwargs) -> Any:
        """处理completion请求并返回OpenAI格式的响应"""
        try:
            # 调用处理函数
            result = self._completion_handler(**kwargs)

            # 处理不同类型的返回结果
            if isinstance(result, str):
                # 如果返回的是字符串，直接创建响应对象
                return BaseOpenAIResponse(result)
            elif isinstance(result, dict):
                # 如果返回的是字典，尝试提取content字段
                content = result.get('content', '') or result.get('output', {}).get('text', '')
                return BaseOpenAIResponse(content)
            else:
                # 其他情况，尝试转换为字符串
                return BaseOpenAIResponse(str(result))
        except Exception as e:
            # 处理异常
            raise Exception(f"处理completion请求失败: {str(e)}")


def create_openai_compatible_client(completion_handler: Callable) -> Any:
    """创建OpenAI API兼容的客户端
    简化创建兼容客户端的过程
    
    Args:
        completion_handler: 处理completion请求的函数
        
    Returns:
        兼容OpenAI API的客户端对象
    """
    return OpenAICompatibleWrapper(completion_handler)
