from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from engine.assistant.messages import t

MAX_MESSAGE_LENGTH = 20_000
MAX_HISTORY_MESSAGES = 40


class ChatMessage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH)


class ChatRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    messages: list[ChatMessage] = Field(min_length=1)

    @model_validator(mode="after")
    def _ends_with_the_user_question(self) -> "ChatRequest":
        if self.messages[-1].role != "user":
            raise ValueError(t("conversation.last_message_not_user"))
        return self

    def recent_history(self) -> list[ChatMessage]:
        """Small local models have short contexts: older messages are dropped first."""
        return self.messages[-MAX_HISTORY_MESSAGES:]
