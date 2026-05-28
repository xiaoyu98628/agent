from fastapi import APIRouter

from app.interfaces.http.api.v1.endpoints import agent, chat, conversations, documents, knowledge_bases, memory, skills

api_v1_router = APIRouter(prefix="/v1")

api_v1_router.include_router(agent.router)
api_v1_router.include_router(chat.router)
api_v1_router.include_router(conversations.router)
api_v1_router.include_router(documents.router)
api_v1_router.include_router(knowledge_bases.router)
api_v1_router.include_router(memory.router)
api_v1_router.include_router(skills.router)
