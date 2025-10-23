"""
@FileName: prompts_manager.py
@Description: 提示词模板管理类
@Author: HengLine
@Time: 2025/10/23 21:54
"""
import yaml
from pathlib import Path


class PromptManager:
    def __init__(self, prompt_dir: Path = Path(__file__)):
        self.prompt_dir = prompt_dir / "prompts"

    def get_prompt(self, name: str) -> str:
        file_path = self.prompt_dir / f"{name}.yaml"
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data["template"]

    def get_version(self, name: str) -> str:
        file_path = self.prompt_dir / f"{name}.yaml"
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("version", "unknown")