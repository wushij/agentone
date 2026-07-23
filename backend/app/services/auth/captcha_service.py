"""backend/app/services/captcha_service.py"""

import base64
import io
import uuid

from captcha.image import ImageCaptcha
from redis.asyncio import Redis

CAPTCHA_TTL_SECONDS = 5 * 60


class CaptchaService:
    def __init__(self, redis: Redis):
        self.redis = redis
        self._generator = ImageCaptcha(width=130, height=48)

    async def create(self) -> dict[str, str]:
        captcha_id = uuid.uuid4().hex
        code = self._generator.generate().decode("ascii")[:4]
        image = self._generator.generate_image(code)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode("ascii")

        await self.redis.set(self._key(captcha_id), code.lower(), ex=CAPTCHA_TTL_SECONDS)
        return {"id": captcha_id, "img": img_base64}

    async def verify(self, captcha_id: str | None, answer: str | None) -> None:
        if not captcha_id or not answer:
            raise ValueError("请完成验证码")

        key = self._key(captcha_id)
        expected = await self.redis.get(key)
        await self.redis.delete(key)

        if not expected:
            raise ValueError("验证码已过期，请刷新")
        if expected != answer.strip().lower():
            raise ValueError("验证码错误")

    def _key(self, captcha_id: str) -> str:
        return f"captcha:{captcha_id}"
