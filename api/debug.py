from fastapi import FastAPI

app = FastAPI()

@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "Backend is live"}

@app.get("/api/test")
async def test():
    return {"message": "Test successful"}
