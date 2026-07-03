import random
import logging
import time
import redis.asyncio as aioredis

class OTPManager:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis = None
        self._memory_store = {}
        self._rate_limit_store = {}

    async def connect(self):
        try:
            self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
        except Exception as e:
            logging.warning(f"Could not connect to Redis: {e}. Falling back to Python memory-based OTP.")
            self.redis = None

    async def generate_otp(self, phone: str, expiry_seconds: int = 120) -> str:
        if self.redis is None:
            await self.connect()

        rate_limit_key = f"otp_limit:{phone}"
        otp_key = f"otp_code:{phone}"
        now = time.time()

        if self.redis:
            try:
                if await self.redis.get(rate_limit_key):
                    raise ValueError("درخواست مجدد قبل از ۶۰ ثانیه امکان‌پذیر نیست.")
                
                code = str(random.randint(10000, 99999))
                await self.redis.setex(otp_key, expiry_seconds, code)
                await self.redis.setex(rate_limit_key, 60, "active")
                return code
            except Exception as e:
                if isinstance(e, ValueError):
                    raise e
                logging.error(f"Redis write error, using local fallback: {e}")
                self.redis = None

        if phone in self._rate_limit_store:
            if now < self._rate_limit_store[phone]:
                raise ValueError("درخواست مجدد قبل از ۶۰ ثانیه امکان‌پذیر نیست.")

        code = str(random.randint(10000, 99999))
        self._memory_store[phone] = {
            "code": code,
            "expires_at": now + expiry_seconds
        }
        self._rate_limit_store[phone] = now + 60
        return code

    async def verify_otp(self, phone: str, code: str) -> bool:
        if self.redis is None:
            await self.connect()

        otp_key = f"otp_code:{phone}"
        now = time.time()

        if self.redis:
            try:
                saved_code = await self.redis.get(otp_key)
                if saved_code and saved_code == code:
                    await self.redis.delete(otp_key)
                    return True
                return False
            except Exception as e:
                logging.error(f"Redis read error, using local fallback: {e}")
                self.redis = None

        if phone in self._memory_store:
            data = self._memory_store[phone]
            if now <= data["expires_at"] and data["code"] == code:
                del self._memory_store[phone]
                return True
        return False