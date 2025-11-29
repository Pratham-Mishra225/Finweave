from fastapi import APIRouter

router = APIRouter(prefix="/demo", tags=["demo"])

@router.get("/ping")
def ping():
    return {"status": "ok", "message": "pong"}

@router.post("/echo")
def echo(data: dict):
    return {"you_sent": data}
