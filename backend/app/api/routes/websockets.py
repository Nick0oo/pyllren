import asyncio
import uuid
import logging

import jwt
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket
from jwt import InvalidTokenError, ExpiredSignatureError
from sqlmodel import Session
from starlette.websockets import WebSocketDisconnect

from app.api.deps import get_db
from app.core import security
from app.core.config import settings
from app.core.websocket_manager import manager
from app.models import TokenPayload, User

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_user_from_token(token: str, session: Session) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        token_data = TokenPayload(**payload)
    except ExpiredSignatureError:
        logger.warning("WS auth rejected: token expired")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token expired")
    except InvalidTokenError:
        logger.warning("WS auth rejected: invalid token signature or payload")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")
    except Exception as exc:
        logger.error("WS auth error: %s", exc)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials")

    user = session.get(User, token_data.sub)
    if not user:
        logger.warning("WS auth rejected: user not found for sub=%s", token_data.sub)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.is_active:
        logger.warning("WS auth rejected: user inactive id=%s", user.id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str, session: Session = Depends(get_db)) -> None:
    """Canal WebSocket autenticado por token JWT en query param."""
    try:
        user = _get_user_from_token(token, session)
    except HTTPException as exc:
        # Map HTTPException to appropriate WS close codes
        code = status.WS_1008_POLICY_VIOLATION if exc.status_code == status.HTTP_403_FORBIDDEN else status.WS_1011_INTERNAL_ERROR
        logger.info("WS connection rejected (%s): %s", exc.status_code, exc.detail)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = uuid.UUID(str(user.id))
    await manager.connect(user_id, websocket)

    try:
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=45)
            except asyncio.TimeoutError:
                # Heartbeat
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        logger.info("WS disconnected for user %s", user_id)
        manager.disconnect(user_id)
    except Exception:
        logger.exception("WS unexpected error for user %s", user_id)
        manager.disconnect(user_id)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)

