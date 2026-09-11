from fastapi import FastAPI
import uvicorn

from app.routes import get_router_and_lifespan


opencode_proxy_router, opencode_proxy_lifespan = get_router_and_lifespan()

app = FastAPI(lifespan=opencode_proxy_lifespan)
app.include_router(opencode_proxy_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
