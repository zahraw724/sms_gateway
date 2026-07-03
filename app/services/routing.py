import re
import json
import logging
from sqlalchemy.orm import Session
from app import models
from app.services.adapters import ADAPTER_REGISTRY

class RoutingEngine:
    @staticmethod
    def detect_operator(phone_number: str) -> str:
        mci = r"^(\+98|0)?9(1[0-9]|9[0-4])\d{7}$"
        irancell = r"^(\+98|0)?9(3[0-9]|0[1-5]|41)\d{7}$"
        rightel = r"^(\+98|0)?9(2[0-2])\d{7}$"

        if re.match(mci, phone_number):
            return "mci"
        elif re.match(irancell, phone_number):
            return "irancell"
        elif re.match(rightel, phone_number):
            return "rightel"
        return "all"

    async def route_and_send(self, db: Session, recipient: str, text: str, message_type: str) -> dict:
        blacklisted = db.query(models.RecipientList).filter_by(phone_number=recipient, list_type="black").first()
        if blacklisted:
            return {"status": "ignored", "reason": "Recipient is blacklisted"}

        operator = self.detect_operator(recipient)

        rules = db.query(models.RoutingRule).filter(
            models.RoutingRule.is_active == True,
            models.RoutingRule.message_type == message_type,
            models.RoutingRule.operator.in_([operator, "all"])
        ).order_by(models.RoutingRule.priority.asc()).all()

        providers = []
        if rules:
            for r in rules:
                p = db.query(models.SMSProvider).filter_by(id=r.provider_id, is_active=True).first()
                if p:
                    providers.append(p)
        else:
            providers = db.query(models.SMSProvider).filter_by(is_active=True).order_by(models.SMSProvider.priority.asc()).all()

        if not providers:
            return {"status": "failed", "reason": "No active providers available"}

        for provider in providers:
            adapter = ADAPTER_REGISTRY.get(provider.adapter_type)
            if not adapter:
                continue

            config_dict = provider.config if isinstance(provider.config, dict) else json.loads(provider.config)

            result = await adapter.send_sms(
                to=recipient,
                text=text,
                sender=provider.sender_number,
                config=config_dict
            )

            if result["status"] == "success":
                msg = models.SMSMessage(
                    sender_number=provider.sender_number,
                    recipient_number=recipient,
                    body=text,
                    provider_id=provider.id,
                    status="sent",
                    message_type=message_type,
                    remote_message_id=result["remote_id"]
                )
                db.add(msg)
                db.commit()
                return {"status": "sent", "provider": provider.name, "message_id": result["remote_id"]}
            else:
                logging.warning(f"Failed via {provider.name}. Error: {result.get('error')}. Trying fallback...")

        return {"status": "failed", "reason": "All configured fallback providers failed."}