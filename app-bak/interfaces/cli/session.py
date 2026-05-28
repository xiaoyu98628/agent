from dataclasses import dataclass


@dataclass(slots=True)
class CliSession:
    conversation_id: str | None = None
    provider: str | None = None
    model: str | None = None
    stream: bool = True

    def model_label(self) -> str:
        if self.provider and self.model:
            return f"{self.provider}:{self.model}"
        return "(default from config)"
