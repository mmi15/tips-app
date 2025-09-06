from fastapi import FastAPI
from app.api.routes.users import router as users_router
from app.api.routes.topics import router as topics_router
from app.api.routes.subscriptions import router as subscriptions_router

app = FastAPI(title="Tips API", version="0.2.0")


@app.get("/health")
def health_check():
    return {"status": "ok"}


# Routers
app.include_router(users_router)
app.include_router(topics_router)
app.include_router(subscriptions_router)
