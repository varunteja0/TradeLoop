"""
Email Service — transactional email via Resend API.

In dev mode (no RESEND_API_KEY), logs emails instead of sending.
"""
from __future__ import annotations
import logging
from typing import Optional
from app.config import get_settings

logger = logging.getLogger("tradeloop.email")


class EmailService:
    async def send(self, to: str, subject: str, html: str) -> bool:
        settings = get_settings()
        resend_key = getattr(settings, 'resend_api_key', '')

        if not resend_key:
            logger.info("Email (dev mode) to=%s subject=%s", to, subject)
            logger.debug("Body: %s", html[:200])
            return True

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {resend_key}"},
                    json={
                        "from": "TradeLoop <noreply@tradeloop.io>",
                        "to": [to],
                        "subject": subject,
                        "html": html,
                    },
                    timeout=10.0,
                )
            if resp.status_code in (200, 201):
                logger.info("Email sent to %s: %s", to, subject)
                return True
            logger.error("Email failed: %s %s", resp.status_code, resp.text)
            return False
        except Exception:
            logger.exception("Email send error")
            return False

    async def send_welcome(self, email: str, name: str) -> bool:
        return await self.send(email, "Welcome to TradeLoop", f"""
            <h2>Welcome to TradeLoop, {name or 'Trader'}!</h2>
            <p>You're all set. Upload your first trades to see where your money leaks.</p>
            <p><a href="https://tradeloop.io/upload">Upload Trades</a></p>
            <p>— The TradeLoop Team</p>
        """)

    async def send_password_reset(self, email: str, reset_token: str) -> bool:
        return await self.send(email, "Reset Your Password — TradeLoop", f"""
            <h2>Password Reset</h2>
            <p>Click the link below to reset your password:</p>
            <p><a href="https://tradeloop.io/reset-password?token={reset_token}">Reset Password</a></p>
            <p>This link expires in 1 hour.</p>
        """)

    async def send_compliance_alert(self, email: str, account_name: str, status: str, message: str) -> bool:
        color = "#ff4757" if status == "violated" else "#eab308"
        return await self.send(email, f"Compliance Alert: {account_name} — {status.upper()}", f"""
            <h2 style="color:{color}">{status.upper()}: {account_name}</h2>
            <p>{message}</p>
            <p><a href="https://tradeloop.io/prop">View Dashboard</a></p>
        """)

    async def send_weekly_report(self, email: str, grade: str, summary: str) -> bool:
        return await self.send(email, f"Your Weekly Report — Grade {grade}", f"""
            <h2>Your Trading Grade: {grade}</h2>
            <p>{summary}</p>
            <p><a href="https://tradeloop.io/report">View Full Report</a></p>
        """)
