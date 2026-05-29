import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.application.dto.model_setup import ModelOption


class ModelCost(BaseModel):
    input: float = 0
    output: float = 0
    cache_read: float = 0
    cache_write: float = 0


class ModelCatalogItem(BaseModel):
    id: str
    name: str
    reasoning: bool = False
    input: list[str] = Field(default_factory=lambda: ["text"])
    cost: ModelCost = Field(default_factory=ModelCost)
    context_window: int | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_option(self) -> ModelOption:
        return ModelOption(
            id=self.id,
            name=self.name,
            reasoning=self.reasoning,
            input=self.input,
            context_window=self.context_window,
            max_tokens=self.max_tokens,
            metadata={
                "cost": self.cost.model_dump(mode="json"),
                **self.metadata,
            },
        )


class ProviderCatalog(BaseModel):
    id: str
    name: str
    base_url: str | None = None
    models: list[ModelCatalogItem] = Field(default_factory=list)

    def model_by_id(self, model_id: str) -> ModelCatalogItem:
        for model in self.models:
            if model.id == model_id:
                return model
        raise ValueError(f"Unknown model: {model_id}")


def load_provider_catalog(path: Path) -> ProviderCatalog:
    with path.open("r", encoding="utf-8") as file:
        return ProviderCatalog.model_validate(json.load(file))
