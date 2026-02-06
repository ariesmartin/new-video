"""
Model Router Service

实现 Task-Model Routing，将不同任务路由到合适的 LLM。
"""

from typing import Any
import structlog
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel

from backend.schemas.model_config import TaskType, ProtocolType

logger = structlog.get_logger(__name__)


class ModelRouter:
    """模型路由器"""

    def __init__(self, db_service):
        self._db = db_service
        self._cache: dict[str, BaseChatModel] = {}

    async def get_model(
        self, user_id: str, task_type: TaskType, project_id: str | None = None
    ) -> BaseChatModel:
        """获取任务对应的 LLM 实例"""
        # 查找映射配置
        mapping = await self._db.get_model_mapping(user_id, task_type.value, project_id)

        logger.info(
            "Model mapping lookup",
            user_id=user_id,
            task_type=task_type.value,
            project_id=project_id,
            has_mapping=bool(mapping),
        )

        # 定义 task_type 到 category 的映射（用于回退）
        TASK_TYPE_TO_CATEGORY: dict[TaskType, TaskType] = {
            # creative 类别
            TaskType.ROUTER: TaskType.NOVEL_WRITER,
            TaskType.MARKET_ANALYST: TaskType.NOVEL_WRITER,
            TaskType.STORY_PLANNER: TaskType.NOVEL_WRITER,
            TaskType.SKELETON_BUILDER: TaskType.NOVEL_WRITER,
            # content 类别
            TaskType.SCRIPT_ADAPTER: TaskType.SCRIPT_FORMATTER,
            TaskType.SCRIPT_PARSER: TaskType.SCRIPT_FORMATTER,
            TaskType.REFINER: TaskType.SCRIPT_FORMATTER,
            # quality 类别
            TaskType.ANALYSIS_LAB: TaskType.EDITOR,
            # video 类别
            TaskType.STORYBOARD_ARTIST: TaskType.STORYBOARD_DIRECTOR,
            TaskType.PROMPT_GENERATOR: TaskType.STORYBOARD_DIRECTOR,
            TaskType.ASSET_INSPECTOR: TaskType.STORYBOARD_DIRECTOR,
            # image_process 类别
            TaskType.IMAGE_INPAINTER: TaskType.IMAGE_ENHANCER,
            TaskType.IMAGE_OUTPAINTER: TaskType.IMAGE_ENHANCER,
        }

        # 如果没有找到配置，尝试回退到对应类别的配置
        if not mapping and task_type in TASK_TYPE_TO_CATEGORY:
            fallback_task = TASK_TYPE_TO_CATEGORY[task_type]
            logger.info(
                f"{task_type.value} has no dedicated mapping, falling back to {fallback_task.value}"
            )
            mapping = await self._db.get_model_mapping(user_id, fallback_task.value, project_id)
            if mapping:
                logger.info(f"Using {fallback_task.value} config for {task_type.value}")

        if not mapping:
            # 没有配置模型映射，抛出错误提示用户配置
            logger.error(
                "No model mapping configured",
                user_id=user_id,
                task_type=task_type.value,
                project_id=project_id,
            )
            raise RuntimeError(
                f"未配置模型映射: 请前往设置 -> LLM 服务商 -> "
                f"配置 {task_type.value} 的模型映射，或者配置其所属类别的默认模型"
            )

        provider = mapping.get("llm_providers", {})
        cache_key = f"{provider.get('id')}:{mapping['model_name']}"

        logger.info(
            "Provider data",
            provider_id=provider.get("id"),
            provider_name=provider.get("name"),
            has_api_key=bool(provider.get("api_key")),
            api_key_preview=provider.get("api_key", "")[:10] if provider.get("api_key") else None,
            protocol=provider.get("protocol"),
        )

        if cache_key in self._cache:
            return self._cache[cache_key]

        api_key = provider.get("api_key")
        if not api_key:
            logger.error(
                "API key is missing or empty",
                provider_id=provider.get("id"),
                provider_keys=list(provider.keys()),
            )
            raise RuntimeError(
                f"No API key configured for provider {provider.get('name', 'unknown')}"
            )

        model = self._create_model(
            protocol=provider.get("protocol", "openai"),
            api_key=api_key,
            base_url=provider.get("base_url"),
            model_name=mapping["model_name"],
            parameters=mapping.get("parameters", {}),
        )

        self._cache[cache_key] = model
        return model

    def _create_model(
        self,
        protocol: str,
        api_key: str,
        base_url: str | None,
        model_name: str,
        parameters: dict[str, Any],
    ) -> BaseChatModel:
        """创建 LLM 实例"""
        temp = parameters.get("temperature", 0.7)
        max_tokens = parameters.get("max_tokens", 4096)

        if protocol == ProtocolType.OPENAI.value:
            return ChatOpenAI(
                api_key=api_key,
                base_url=base_url,
                model=model_name,
                temperature=temp,
                max_tokens=max_tokens,
                streaming=True,
            )
        elif protocol == ProtocolType.ANTHROPIC.value:
            return ChatAnthropic(
                api_key=api_key,
                model=model_name,
                temperature=temp,
                max_tokens=max_tokens,
                base_url=base_url,
                streaming=True,
            )
        elif protocol == ProtocolType.GEMINI.value:
            client_options = None

            if base_url:
                client_options = {"api_endpoint": base_url}
                logger.info("Configuring Gemini with custom endpoint", api_endpoint=base_url)

            return ChatGoogleGenerativeAI(
                google_api_key=api_key,
                model=model_name,
                temperature=temp,
                max_output_tokens=max_tokens,
                client_options=client_options,
            )
        else:
            raise ValueError(f"Unknown protocol: {protocol}")


_model_router: ModelRouter | None = None


def init_model_router(db_service) -> ModelRouter:
    global _model_router
    _model_router = ModelRouter(db_service)
    return _model_router


def get_model_router() -> ModelRouter:
    if _model_router is None:
        raise RuntimeError("Model router not initialized")
    return _model_router
