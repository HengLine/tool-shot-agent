#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HengLine 工具模块
提供LlamaIndex集成和剧本智能分析功能
"""

# LlamaIndex 核心功能
from .llama_index_loader import DocumentLoader, DirectoryLoader
from .llama_index_retriever import DocumentRetriever
from .llama_index_tool import create_vector_store, get_embedding_model

# 剧本解析功能
from .script_parser_tool import (
    ScriptParser,
    parse_script_to_documents,
    parse_script_file_to_documents,
    Scene,
    Character,
    SceneElement
)

# 剧本知识库功能
from .script_knowledge_tool import (
    ScriptKnowledgeBase,
    create_script_knowledge_base
)

# 剧本智能分析功能
from .script_intelligence_tool import (
    ScriptIntelligence,
    create_script_intelligence,
    analyze_script,
    search_script
)

__all__ = [
    # LlamaIndex 核心功能
    "DocumentLoader",
    "DirectoryLoader",
    "DocumentRetriever",
    "create_vector_store",
    "get_embedding_model",
    
    # 剧本解析
    "ScriptParser",
    "parse_script_to_documents",
    "parse_script_file_to_documents",
    "Scene",
    "Character",
    "SceneElement",
    
    # 剧本知识库
    "ScriptKnowledgeBase",
    "create_script_knowledge_base",
    
    # 剧本智能分析
    "ScriptIntelligence",
    "create_script_intelligence",
    "analyze_script",
    "search_script"
]