"""Configuration management for the LangGraph Slack Agent.

This module defines the Pydantic models used for managing application settings.
It leverages Pydantic Settings to load configurations from environment
variables and .env files. The settings are structured into logical groups
such as LangGraph, LLM, Slack, and general application settings.

The primary entry point for accessing settings is the `get_settings()`
function, which implements a singleton pattern to ensure settings are
loaded once.
"""

from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """Base settings for Large Language Models (LLMs).

    These settings are designed to configure LLMs, particularly for use with
    LangChain's `langchain.chat_models.init_chat_model` function. They define
    common parameters such as API keys for various providers (Google Vertex AI,
    Google GenAI, Anthropic, OpenAI), the model name, provider, temperature,
    and retry/timeout configurations. The `validate_api_key` method ensures
    that the necessary credentials are present based on the selected
    `llm_model_provider`.

    Attributes:
        gcp_project_id: Google Cloud Project ID, used if `llm_model_provider`
            is 'google_vertexai'.
        gcp_location: Google Cloud Location, used if `llm_model_provider` is
            'google_vertexai'.
        gcp_credentials_path: Path to Google Cloud credentials file, used if
            `llm_model_provider` is 'google_vertexai'.
        gemini_api_key: API key for Gemini, used if `llm_model_provider` is
            'google_genai'.
        anthropic_api_key: API key for Anthropic, used if `llm_model_provider`
            is 'anthropic'.
        openai_api_key: API key for OpenAI, used if `llm_model_provider` is
            'openai'.
        llm_model_name: The specific name of the LLM model to use (e.g.,
            'gemini-2.5-pro-preview-03-25'). This is passed to
            `init_chat_model`.
        llm_model_provider: The provider of the LLM model (e.g.,
            'google_genai', 'openai'). This is passed to `init_chat_model`.
        temperature: The temperature setting for the LLM, controlling the
            randomness of the output (0.0 to 1.0).
        max_retries: The maximum number of retries for LLM API requests.
        timeout_seconds: The timeout in seconds for LLM API requests.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gcp_project_id: str | None = Field(
        default=None,
        description="Google Cloud Project ID",
        validation_alias="GCP_PROJECT_ID",
    )
    gcp_location: str | None = Field(
        default=None,
        description="Google Cloud Location",
        validation_alias="GCP_LOCATION",
    )
    gcp_credentials_path: str | None = Field(
        default=None,
        description="Google Cloud Credentials Path",
        validation_alias="GCP_CREDENTIALS_PATH",
    )
    gemini_api_key: str | None = Field(
        default=None,
        description="Gemini API Key",
        validation_alias="GEMINI_API_KEY",
    )
    anthropic_api_key: str | None = Field(
        default=None,
        description="Anthropic API Key",
        validation_alias="ANTHROPIC_API_KEY",
    )
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API Key",
        validation_alias="OPENAI_API_KEY",
    )
    llm_model_name: str = Field(
        ...,
        description="LLM Model Name",
        validation_alias="LLM_MODEL_NAME",
    )
    llm_model_provider: str = Field(
        ...,
        description="LLM Model Provider",
        validation_alias="LLM_MODEL_PROVIDER",
    )
    temperature: float = Field(
        default=0.1,
        ge=0,
        le=1,
        description="Temperature",
        validation_alias="TEMPERATURE",
    )
    max_retries: int = Field(
        default=3,
        description="Max Retries",
        validation_alias="MAX_RETRIES",
    )
    timeout_seconds: float = Field(
        default=30.0,
        description="Timeout Seconds",
        validation_alias="TIMEOUT_SECONDS",
    )

    _PROVIDER_CONFIG_CHECKS: dict[str, list[tuple[str, str, str]]] = {
        "google_vertexai": [
            (
                "gcp_project_id",
                "your-project-id-here",
                "GCP_PROJECT_ID",
            ),
            ("gcp_location", "your-location-here", "GCP_LOCATION"),
            (
                "gcp_credentials_path",
                "your-credentials-path-here",
                "GCP_CREDENTIALS_PATH",
            ),
        ],
        "google_genai": [
            (
                "gemini_api_key",
                "your-api-key-here",
                "GEMINI_API_KEY",
            )
        ],
        "anthropic": [
            (
                "anthropic_api_key",
                "your-api-key-here",
                "ANTHROPIC_API_KEY",
            )
        ],
        "openai": [
            (
                "openai_api_key",
                "your-api-key-here",
                "OPENAI_API_KEY",
            )
        ],
    }

    @model_validator(mode="after")
    def validate_api_key(self) -> Self:
        """Validates that necessary API keys are provided for the LLM provider.

        Returns:
            The validated instance of LLMSettings.

        Raises:
            ValueError: If the required API key or related settings for the
                specified provider are missing or are placeholder values, or if
                the provider is unsupported.
        """
        provider_checks = self._PROVIDER_CONFIG_CHECKS.get(self.llm_model_provider)

        if provider_checks is None:
            raise ValueError(f"Unsupported model provider: {self.llm_model_provider}")

        for (
            attr_name,
            placeholder_value,
            error_field_name,
        ) in provider_checks:
            value = getattr(self, attr_name)
            if not value or value == placeholder_value:
                raise ValueError(f"Valid {error_field_name} required")
        return self


class ChatNodeLLMSettings(LLMSettings):
    """LLM settings specifically for the 'chat_node'.

    Inherits from LLMSettings and overrides defaults for chat-specific
    configurations.

    Attributes:
        llm_model_name: The name of the LLM model for the chat node.
        llm_model_provider: The provider of the LLM model for the chat node.
        temperature: The temperature setting for the chat node's LLM.
        max_retries: The maximum number of retries for the chat node's LLM
            requests.
        timeout_seconds: The timeout in seconds for chat node's LLM requests.
    """

    model_config = SettingsConfigDict(
        env_prefix="CHAT_NODE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    llm_model_name: str = Field(
        default="gpt-4o-mini",
        description="LLM Model Name",
        validation_alias="CHAT_NODE_LLM_MODEL_NAME",
    )
    llm_model_provider: str = Field(
        default="openai",
        description="LLM Model Provider",
        validation_alias="CHAT_NODE_LLM_MODEL_PROVIDER",
    )
    temperature: float = Field(
        default=0.1,
        ge=0,
        le=1,
        description="Temperature",
        validation_alias="CHAT_NODE_TEMPERATURE",
    )
    max_retries: int = Field(
        default=3,
        description="Max Retries",
        validation_alias="CHAT_NODE_MAX_RETRIES",
    )


class LangSmithSettings(BaseSettings):
    """Settings for LangSmith observability and tracing.

    Manages all configurations for LangSmith tracing and monitoring.

    Attributes:
        langsmith_api_key: API key for authenticating with LangSmith service.
        langsmith_tracing: Whether to enable LangSmith tracing.
        langsmith_project: The project name for organizing traces in LangSmith.
    """

    model_config = SettingsConfigDict(
        env_prefix="LANGSMITH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Set as environment variable from SecretManager by Terraform
    langsmith_api_key: str = Field(
        ...,
        description="LangSmith API Key",
        validation_alias="LANGSMITH_API_KEY",
        min_length=1,
    )
    # Set as environment variable from Terraform variable
    langsmith_project: str = Field(
        ...,
        description="LangSmith project name",
        validation_alias="LANGSMITH_PROJECT",
        min_length=1,
    )
    # Set as environment variable from Terraform variable
    langsmith_tracing: Literal["true", "false"] = Field(
        default="true",
        description="Enable LangSmith tracing",
        validation_alias="LANGSMITH_TRACING",
    )


class McpServerConnectionSettings(BaseSettings):
    """Settings for LangSmith observability and tracing.

    Manages all configurations for LangSmith tracing and monitoring.

    Attributes:
        langsmith_api_key: API key for authenticating with LangSmith service.
        langsmith_tracing: Whether to enable LangSmith tracing.
        langsmith_project: The project name for organizing traces in LangSmith.
    """

    model_config = SettingsConfigDict(
        env_prefix="MCP_SERVER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    timeout: float = Field(
        default=30.0,
        description="Timeout in seconds for establishing MCP server connection",
        validation_alias="MCP_SERVER_TIMEOUT",
    )
    sse_read_timeout: float = Field(
        default=300,
        description="Timeout in seconds for SSE read before disconnecting",
        validation_alias="MCP_SERVER_SSE_READ_TIMEOUT",
    )
    terminate_on_close: bool = Field(
        default=True,
        description="Terminate the session when the connection is closed",
        validation_alias="MCP_SERVER_TERMINATE_ON_CLOSE",
    )


class AppSettings(BaseSettings):
    """Global application settings.

    This class consolidates all other settings classes and provides
    application-wide configurations.

    Attributes:
        environment: The current operating environment (e.g., 'development',
            'staging', 'production').
        chat_llm: Instance of ChatNodeLLMSettings for chat functionalities.
        langsmith: Instance of LangSmithSettings for LangSmith tracing.
    """

    environment: str = Field(
        default="development",
        pattern="^(development|staging|production)$",
        validation_alias="ENVIRONMENT",
    )

    # Nested settings
    chat_llm: ChatNodeLLMSettings = Field(default_factory=ChatNodeLLMSettings)
    langsmith: LangSmithSettings = Field(default_factory=LangSmithSettings)
    mcp_server_connection: McpServerConnectionSettings = Field(default_factory=McpServerConnectionSettings)

    # MCP server URLs
    review_agent_mcp_server_url: str = Field(..., validation_alias="REVIEW_AGENT_MCP_SERVER_URL")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Singleton pattern for managing settings
_settings: AppSettings | None = None


def get_settings() -> AppSettings:
    """Retrieves the application settings.

    Implements a singleton pattern to ensure that settings are loaded only
    once.

    Returns:
        The application settings instance.
    """
    global _settings
    if _settings is None:
        _settings = AppSettings()
    return _settings