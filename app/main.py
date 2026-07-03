from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from app.database import get_db, Base, engine
from app.config import settings
from app import models
from app import schemas
from app.services.routing import RoutingEngine
from app.services.otp import OTPManager

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Enterprise SMS Gateway Core API")
routing_engine = RoutingEngine()
otp_manager = OTPManager(settings.REDIS_URL)

api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=True)

async def check_api_auth(api_key: str = Depends(api_key_scheme)):
    if api_key != settings.DEFAULT_API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized API Key Access")
    return api_key

@app.post("/api/v1/providers", dependencies=[Depends(check_api_auth)])
def register_provider(payload: schemas.ProviderCreate, db: Session = Depends(get_db)):
    db_provider = models.SMSProvider(
        name=payload.name,
        adapter_type=payload.adapter_type,
        config=payload.config,
        sender_number=payload.sender_number,
        priority=payload.priority
    )
    db_provider_exists = db.query(models.SMSProvider).filter_by(name=payload.name).first()
    if db_provider_exists:
        raise HTTPException(status_code=400, detail="این درگاه از قبل تعریف شده است.")
        
    db.add(db_provider)
    db.commit()
    db.refresh(db_provider)
    return {"status": "success", "provider_id": db_provider.id}

@app.post("/api/v1/send")
async def send_single_sms(payload: schemas.SendSMSRequest, db: Session = Depends(get_db), api_key: str = Depends(check_api_auth)):
    result = await routing_engine.route_and_send(
        db=db,
        recipient=payload.recipient,
        text=payload.body,
        message_type=payload.message_type
    )
    if result["status"] == "sent":
        return result
    raise HTTPException(status_code=502, detail=result.get("reason", "Gateway processing error"))

@app.post("/api/v1/send/bulk", dependencies=[Depends(check_api_auth)])
async def send_bulk_sms(recipients: list[str], text: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    async def run_bulk_send():
        for recipient in recipients:
            await routing_engine.route_and_send(db, recipient, text, "bulk")
            
    background_tasks.add_task(run_bulk_send)
    return {"status": "accepted", "message": "ارسال گروهی در پس‌زمینه با موفقیت شروع شد."}

@app.post("/api/v1/otp/request")
async def request_otp_code(payload: schemas.OTPRequest, db: Session = Depends(get_db)):
    try:
        code = await otp_manager.generate_otp(payload.phone)
        
        sms_result = await routing_engine.route_and_send(
            db=db,
            recipient=payload.phone,
            text=f"رمز یکبار مصرف شما: {code}\nاعتبار: ۲ دقیقه",
            message_type="otp"
        )
        
        if sms_result["status"] == "sent":
            return {"status": "success", "message": "کد با موفقیت ارسال شد."}
        raise HTTPException(status_code=500, detail="خطا در تحویل فیزیکی پیامک کد تایید")
        
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))

@app.post("/api/v1/otp/verify")
async def verify_otp_code(payload: schemas.OTPVerifyRequest):
    is_valid = await otp_manager.verify_otp(payload.phone, payload.code)
    if is_valid:
        return {"status": "success", "message": "کد صحیح است."}
    raise HTTPException(status_code=400, detail="کد نامعتبر یا منقضی شده است.")

@app.post("/api/v1/blacklist", dependencies=[Depends(check_api_auth)])
def add_to_blacklist(phone_number: str, reason: str = None, db: Session = Depends(get_db)):
    item = models.RecipientList(phone_number=phone_number, list_type="black", reason=reason)
    db.merge(item)
    db.commit()
    return {"status": "success", "message": f"شماره {phone_number} وارد لیست سیاه شد."}