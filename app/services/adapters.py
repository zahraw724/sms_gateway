from abc import ABC, abstractmethod
import httpx
import logging

class SMSAdapter(ABC):
    @abstractmethod
    async def send_sms(self, to: str, text: str, sender: str, config: dict) -> dict:
        pass

    @abstractmethod
    async def get_status(self, remote_id: str, config: dict) -> str:
        pass

class KavenegarAdapter(SMSAdapter):
    async def send_sms(self, to: str, text: str, sender: str, config: dict) -> dict:
        api_key = config.get("api_key")
        url = f"https://api.kavenegar.com/v1/{api_key}/sms/send.json"
        payload = {"receptor": to, "message": text, "sender": sender}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, data=payload)
                if response.status_code == 200:
                    res_json = response.json()
                    remote_id = str(res_json.get("entries", [{}])[0].get("messageid", ""))
                    return {"status": "success", "remote_id": remote_id}
                return {"status": "failed", "error": response.text}
        except Exception as e:
            logging.error(f"Kavenegar Error: {str(e)}")
            return {"status": "failed", "error": str(e)}

    async def get_status(self, remote_id: str, config: dict) -> str:
        return "delivered"

class MagfaAdapter(SMSAdapter):
    async def send_sms(self, to: str, text: str, sender: str, config: dict) -> dict:
        import random
        mock_id = str(random.randint(100000, 999999))
        return {"status": "success", "remote_id": f"magfa_{mock_id}"}

    async def get_status(self, remote_id: str, config: dict) -> str:
        return "sent"

ADAPTER_REGISTRY = {
    "kavenegar": KavenegarAdapter(),
    "magfa": MagfaAdapter()
}