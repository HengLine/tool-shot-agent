#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LlamaIndex 工具函数模块
提供向量存储创建、嵌入模型获取等实用功能
"""

import os
from typing import Optional, List, Any

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.storage import StorageContext
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.storage.index_store import SimpleIndexStore
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding

from hengline.logger import debug, info, error


def get_embedding_model(
        model_type: str = "openai",
        model_name: Optional[str] = None,
        **kwargs
) -> BaseEmbedding:
    """
    获取嵌入模型实例
    
    Args:
        model_type: 模型类型，支持 "openai", "huggingface", "ollama"
        model_name: 模型名称
        **kwargs: 额外参数
        
    Returns:
        BaseEmbedding实例
    """
    try:
        debug(f"获取嵌入模型: type={model_type}, name={model_name}")

        if model_type == "openai":
            # OpenAI嵌入模型
            model_name = model_name or "text-embedding-3-small"
            return OpenAIEmbedding(
                model=model_name,
                **kwargs
            )

        elif model_type == "huggingface":
            # HuggingFace嵌入模型
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding
            model_name = model_name or "BAAI/bge-small-zh-v1.5"
            return HuggingFaceEmbedding(
                model_name=model_name,
                **kwargs
            )

        elif model_type == "ollama":
            # Ollama本地嵌入模型
            from llama_index.embeddings.ollama import OllamaEmbedding
            model_name = model_name or "llama2"
            return OllamaEmbedding(
                model_name=model_name,
                **kwargs
            )

        else:
            raise ValueError(f"不支持的嵌入模型类型: {model_type}")

    except Exception as e:
        error(f"获取嵌入模型失败: {str(e)}")
        # 如果出错，尝试返回默认的OpenAI嵌入模型
        try:
            info("尝试使用默认的OpenAI嵌入模型")
            return OpenAIEmbedding(model="text-embedding-3-small")
        except:
            raise RuntimeError("无法初始化任何嵌入模型")


def create_vector_store(
        documents: Optional[List] = None,
        index_name: str = "default_index",
        storage_dir: Optional[str] = None,
        embedding_model: Optional[BaseEmbedding] = None,
        rebuild: bool = False
) -> VectorStoreIndex:
    """
    创建或加载向量存储索引
    
    Args:
        documents: 要索引的文档列表，如果为None则尝试加载现有索引
        index_name: 索引名称
        storage_dir: 存储目录路径
        embedding_model: 嵌入模型实例
        rebuild: 是否重建索引，即使已存在
        
    Returns:
        VectorStoreIndex实例
    """
    try:
        # 如果提供了存储目录，配置存储上下文
        storage_context = None

        if storage_dir:
            debug(f"配置存储目录: {storage_dir}")
            os.makedirs(storage_dir, exist_ok=True)

            # 创建存储上下文
            vector_store = SimpleVectorStore.from_persist_dir(storage_dir) if os.path.exists(storage_dir) and not rebuild else SimpleVectorStore()
            doc_store = SimpleDocumentStore.from_persist_dir(storage_dir) if os.path.exists(storage_dir) and not rebuild else SimpleDocumentStore()
            index_store = SimpleIndexStore.from_persist_dir(storage_dir) if os.path.exists(storage_dir) and not rebuild else SimpleIndexStore()

            storage_context = StorageContext.from_defaults(
                vector_store=vector_store,
                docstore=doc_store,
                index_store=index_store
            )

        # 如果需要重建或没有文档，从文档创建新索引
        if documents or rebuild or (not storage_dir):
            if documents:
                debug(f"从{len(documents)}个文档创建向量存储索引: {index_name}")

                index = VectorStoreIndex.from_documents(
                    documents,
                    storage_context=storage_context,
                    embed_model=embedding_model,
                    show_progress=True
                )

                # 保存索引到存储目录
                if storage_dir:
                    index.storage_context.persist(persist_dir=storage_dir)
                    info(f"索引已保存到: {storage_dir}")

                return index
            else:
                raise ValueError("创建向量存储索引需要提供文档列表")

        # 否则，从存储加载现有索引
        else:
            debug(f"从存储目录加载向量存储索引: {storage_dir}")
            index = VectorStoreIndex.from_vector_store(
                storage_context.vector_store,
                storage_context=storage_context,
                embed_model=embedding_model
            )
            info(f"成功加载向量存储索引: {index_name}")
            return index

    except Exception as e:
        error(f"创建向量存储索引失败: {str(e)}")
        raise


def create_index_from_directory(
        directory_path: str,
        index_name: str = "directory_index",
        storage_dir: Optional[str] = None,
        embedding_model: Optional[BaseEmbedding] = None,
        recursive: bool = True,
        required_exts: Optional[List[str]] = None,
        rebuild: bool = False
) -> VectorStoreIndex:
    """
    从目录创建向量存储索引
    
    Args:
        directory_path: 包含文档的目录路径
        index_name: 索引名称
        storage_dir: 存储目录路径
        embedding_model: 嵌入模型实例
        recursive: 是否递归加载子目录
        required_exts: 必需的文件扩展名列表
        rebuild: 是否重建索引
        
    Returns:
        VectorStoreIndex实例
    """
    try:
        # 先检查是否可以直接加载现有索引
        if storage_dir and os.path.exists(storage_dir) and not rebuild:
            try:
                return create_vector_store(
                    index_name=index_name,
                    storage_dir=storage_dir,
                    embedding_model=embedding_model
                )
            except Exception as e:
                debug(f"加载现有索引失败，将创建新索引: {str(e)}")

        # 加载目录中的文档
        debug(f"从目录加载文档: {directory_path}")
        loader = SimpleDirectoryReader(
            input_dir=directory_path,
            recursive=recursive,
            required_exts=required_exts
        )

        documents = loader.load_data()
        info(f"从目录加载了{len(documents)}个文档")

        # 创建向量存储索引
        return create_vector_store(
            documents=documents,
            index_name=index_name,
            storage_dir=storage_dir,
            embedding_model=embedding_model,
            rebuild=rebuild
        )

    except Exception as e:
        error(f"从目录创建索引失败: {str(e)}")
        raise


def get_retriever_from_index(
        index: VectorStoreIndex,
        similarity_top_k: int = 3,
        search_type: str = "similarity",
        **kwargs
) -> Any:
    """
    从索引获取检索器
    
    Args:
        index: 向量存储索引
        similarity_top_k: 返回的最相似文档数量
        search_type: 搜索类型，支持 "similarity", "mmr"
        **kwargs: 额外参数
        
    Returns:
        检索器实例
    """
    try:
        debug(f"获取检索器: search_type={search_type}, top_k={similarity_top_k}")

        if search_type == "mmr":
            # 使用最大边际相关性搜索
            retriever = index.as_retriever(
                retriever_mode="mmr",
                similarity_top_k=similarity_top_k,
                **kwargs
            )
        else:
            # 默认使用相似度搜索
            retriever = index.as_retriever(
                retriever_mode="similarity",
                similarity_top_k=similarity_top_k,
                **kwargs
            )

        return retriever

    except Exception as e:
        error(f"获取检索器失败: {str(e)}")
        raise
