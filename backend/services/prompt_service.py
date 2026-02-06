"""
Prompt Service

Dynamic Prompt Management System (V1.0)
负责从 prompts/ 目录加载 Markdown 格式的 System Prompt，
并转换为 LangChain 可用的模板对象。

Features:
- Hot Reloading: 开发模式下每次请求重新加载文件
- Caching: 生产模式下启动时加载并缓存
- Variable Injection: 支持 {variable} 格式的变量替换
"""

from pathlib import Path
from typing import Optional
import structlog
from functools import lru_cache

from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate

logger = structlog.get_logger(__name__)


class PromptService:
    """
    Prompt 服务层

    负责管理和加载所有 Agent 的 System Prompt。

    Usage:
        service = get_prompt_service()
        template = service.get_template("story_planner")
    """

    # Prompt 文件名到逻辑名的映射
    PROMPT_MAPPING = {
        "master_router": "0_Master_Router.md",
        "market_analyst": "1_Market_Analyst.md",
        "story_planner": "2_Story_Planner.md",
        "skeleton_builder": "3_Skeleton_Builder.md",
        "novel_writer": "4_Novel_Writer.md",
        "script_adapter": "5_Script_Adapter.md",
        "storyboard_director": "6_Storyboard_Director.md",
        "editor_reviewer": "7_Editor_Reviewer.md",
        "refiner": "8_Refiner.md",
        "analysis_lab": "9_Analysis_Lab.md",
        "asset_inspector": "10_Asset_Inspector.md",
    }

    def __init__(self, prompts_dir: Optional[Path] = None, debug_mode: bool = False):
        """
        初始化 Prompt 服务

        Args:
            prompts_dir: prompts 目录的路径，默认为项目根目录的 prompts/
            debug_mode: 是否开启调试模式（热重载）
        """
        if prompts_dir is None:
            # 默认查找项目根目录的 prompts 文件夹
            # backend/services/prompt_service.py -> backend -> project_root
            prompts_dir = Path(__file__).parent.parent.parent / "prompts"

        self._prompts_dir = prompts_dir
        self._debug_mode = debug_mode
        self._cache: dict[str, str] = {}

        logger.info(
            "PromptService initialized",
            prompts_dir=str(self._prompts_dir),
            debug_mode=self._debug_mode,
            available_prompts=list(self.PROMPT_MAPPING.keys()),
        )

        # 验证目录存在
        if not self._prompts_dir.exists():
            logger.warning(
                "Prompts directory not found, will use fallback prompts",
                prompts_dir=str(self._prompts_dir),
            )

    def get_raw_prompt(self, prompt_name: str) -> str:
        """
        获取原始 Prompt 文本

        Args:
            prompt_name: 逻辑名称，如 "story_planner"

        Returns:
            Markdown 格式的 Prompt 文本

        Raises:
            FileNotFoundError: 如果 Prompt 文件不存在
        """
        # 开发模式：每次重新加载
        if self._debug_mode:
            return self._load_from_file(prompt_name)

        # 生产模式：使用缓存
        if prompt_name not in self._cache:
            self._cache[prompt_name] = self._load_from_file(prompt_name)

        return self._cache[prompt_name]

    def get_template(self, prompt_name: str) -> ChatPromptTemplate:
        """
        获取 LangChain ChatPromptTemplate (已自动转义 JSON 中的花括号)

        Args:
            prompt_name: 逻辑名称，如 "story_planner"

        Returns:
            可直接用于 chain 的 ChatPromptTemplate
        """
        raw_text = self.get_raw_prompt(prompt_name)

        # 转义 JSON 中的花括号，避免被误解析为变量
        raw_text = self._escape_braces(raw_text)

        # 创建 System Message Template
        system_template = SystemMessagePromptTemplate.from_template(
            raw_text,
            template_format="f-string",
        )

        # 包装为 ChatPromptTemplate
        return ChatPromptTemplate.from_messages([system_template])

    def _escape_braces(self, text: str) -> str:
        """
        转义文本中的花括号，避免被 ChatPromptTemplate 误解析为变量。
        将单个 { 和 } 转为 {{ 和 }}，但保留已经转义的 {{ 和 }}。
        """
        import re

        # 统计原始花括号数量
        original_single_open = text.count("{") - text.count("{{") * 2
        original_single_close = text.count("}") - text.count("}}") * 2

        # 先保护已经转义的 {{ 和 }}
        text = text.replace("{{", "\x00DBL_OPEN\x00")
        text = text.replace("}}", "\x00DBL_CLOSE\x00")

        # 转义单个花括号
        text = text.replace("{", "{{")
        text = text.replace("}", "}}")

        # 恢复原本就是双花括号的部分
        text = text.replace("\x00DBL_OPEN\x00", "{{")
        text = text.replace("\x00DBL_CLOSE\x00", "}}")

        # 记录转义结果
        logger.debug(
            "Escaped braces in prompt",
            single_open_count=original_single_open,
            single_close_count=original_single_close,
            result_length=len(text),
        )

        return text

    def get_prompt_with_variables(self, prompt_name: str, **kwargs) -> str:
        """
        获取填充变量后的 Prompt 文本（JSON 中的花括号已自动转义）

        Args:
            prompt_name: 逻辑名称
            **kwargs: 要填充的变量

        Returns:
            填充后的文本
        """
        raw_text = self.get_raw_prompt(prompt_name)

        logger.info(
            "Loading prompt",
            prompt_name=prompt_name,
            raw_length=len(raw_text),
            has_json_examples='{"' in raw_text or "{'" in raw_text,
        )

        # 安全的变量替换：只替换存在的变量
        for key, value in kwargs.items():
            placeholder = "{" + key + "}"
            if placeholder in raw_text:
                raw_text = raw_text.replace(placeholder, str(value))
                logger.debug("Replaced variable", key=key)

        # 转义剩余的花括号（JSON 示例中的），避免被 ChatPromptTemplate 误解析
        escaped_text = self._escape_braces(raw_text)

        logger.info(
            "Prompt escaped",
            prompt_name=prompt_name,
            escaped_length=len(escaped_text),
            sample=escaped_text[:200] + "..." if len(escaped_text) > 200 else escaped_text,
        )

        return escaped_text

    def _load_from_file(self, prompt_name: str) -> str:
        """
        从文件加载 Prompt
        """
        if prompt_name not in self.PROMPT_MAPPING:
            available = list(self.PROMPT_MAPPING.keys())
            raise ValueError(
                f"Unknown prompt name: '{prompt_name}'. Available prompts: {available}"
            )

        filename = self.PROMPT_MAPPING[prompt_name]
        filepath = self._prompts_dir / filename

        if not filepath.exists():
            logger.error("Prompt file not found", prompt_name=prompt_name, filepath=str(filepath))
            raise FileNotFoundError(f"Prompt file not found: {filepath}")

        content = filepath.read_text(encoding="utf-8")

        logger.debug(
            "Prompt loaded from file",
            prompt_name=prompt_name,
            filepath=str(filepath),
            content_length=len(content),
        )

        return content

    def list_available_prompts(self) -> list[str]:
        """
        列出所有可用的 Prompt 名称
        """
        return list(self.PROMPT_MAPPING.keys())

    def reload_cache(self) -> None:
        """
        清空缓存，强制重新加载所有 Prompt
        """
        self._cache.clear()
        logger.info("Prompt cache cleared")

    def preload_all(self) -> None:
        """
        预加载所有 Prompt 到缓存（用于生产环境启动时）
        """
        for prompt_name in self.PROMPT_MAPPING:
            try:
                self._cache[prompt_name] = self._load_from_file(prompt_name)
            except FileNotFoundError:
                logger.warning("Failed to preload prompt", prompt_name=prompt_name)

        logger.info(
            "All prompts preloaded",
            loaded_count=len(self._cache),
            total_count=len(self.PROMPT_MAPPING),
        )


# ===== Singleton Instance =====

_prompt_service: Optional[PromptService] = None


def get_prompt_service() -> PromptService:
    """
    获取 PromptService 单例

    Returns:
        PromptService 实例
    """
    global _prompt_service

    if _prompt_service is None:
        from backend.config import settings

        _prompt_service = PromptService(debug_mode=settings.debug)

        # 生产模式下预加载所有 Prompt
        if not settings.debug:
            _prompt_service.preload_all()

    return _prompt_service


def init_prompt_service(
    prompts_dir: Optional[Path] = None, debug_mode: bool = False
) -> PromptService:
    """
    初始化 PromptService（用于测试或自定义配置）

    Args:
        prompts_dir: 自定义 prompts 目录
        debug_mode: 是否开启调试模式

    Returns:
        新的 PromptService 实例
    """
    global _prompt_service

    _prompt_service = PromptService(prompts_dir=prompts_dir, debug_mode=debug_mode)

    return _prompt_service
