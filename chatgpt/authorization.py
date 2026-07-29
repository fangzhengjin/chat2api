import asyncio
import hashlib
import json
import random
import secrets

from fastapi import HTTPException

import utils.configs as configs
import utils.globals as globals
from chatgpt.refreshToken import rt2ac, sess2ac
from utils.Logger import logger
from utils.token_parser import is_refresh_token

GATEWAY_COOKIE_NAME = "chat2api_seed"


def _gateway_seed_key(seed):
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def resolve_gateway_seed_value(seed):
    """验证 SeedToken 明文并返回内部映射键。

    Args:
        seed: 用户提交或 Cookie 中保存的 SeedToken 明文。

    Returns:
        SeedToken 的 SHA-256 映射键。

    Raises:
        HTTPException: Cookie 缺失、无效或绑定账号不存在时返回 401。
    """
    seed_key = _gateway_seed_key(seed) if seed else ""
    seed_data = globals.seed_map.get(seed_key, {})
    if not seed_data.get("managed") or seed_data.get("token") not in globals.token_list:
        raise HTTPException(status_code=401, detail="Invalid chat password")
    return seed_key


def resolve_gateway_seed(request):
    """验证浏览器 Seed Cookie 并返回内部映射键。

    Args:
        request: 当前 FastAPI 请求。

    Returns:
        SeedToken 的 SHA-256 映射键。

    Raises:
        HTTPException: Cookie 缺失、无效或绑定账号不存在时返回 401。
    """
    return resolve_gateway_seed_value(request.cookies.get(GATEWAY_COOKIE_NAME, ""))


def generate_gateway_seed(account_token):
    """为指定账号生成并绑定唯一的浏览器访问密码。

    Args:
        account_token: 已存在于账号池中的 RT、AT 或 SessionToken。

    Returns:
        仅在本次生成响应中返回的明文 SeedToken。

    Raises:
        HTTPException: 账号不存在时返回 404。
    """
    if account_token not in globals.token_list:
        raise HTTPException(status_code=404, detail="Account token not found")

    previous = {}
    for seed_key, seed_data in list(globals.seed_map.items()):
        if seed_data.get("managed") and seed_data.get("token") == account_token:
            previous = seed_data
            del globals.seed_map[seed_key]

    seed = secrets.token_urlsafe(24)
    seed_data = {
        "token": account_token,
        "conversations": previous.get("conversations", []),
        "managed": True,
    }
    if previous.get("user_id"):
        seed_data["user_id"] = previous["user_id"]
    globals.seed_map[_gateway_seed_key(seed)] = seed_data
    with open(globals.SEED_MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(globals.seed_map, f, indent=4)
    return seed


def remove_gateway_seeds(account_token):
    """删除指定账号绑定的浏览器访问密码。

    Args:
        account_token: 即将删除的账号 Token。

    Returns:
        删除的密码数量。
    """
    removed = 0
    for seed_key, seed_data in list(globals.seed_map.items()):
        if seed_data.get("managed") and seed_data.get("token") == account_token:
            del globals.seed_map[seed_key]
            removed += 1
    if removed:
        with open(globals.SEED_MAP_FILE, "w", encoding="utf-8") as f:
            json.dump(globals.seed_map, f, indent=4)
    return removed


def has_gateway_seed(account_token):
    """判断账号是否已绑定浏览器访问密码。

    Args:
        account_token: 账号 Token。

    Returns:
        存在受控 SeedToken 时返回 True。
    """
    return any(
        seed_data.get("managed") and seed_data.get("token") == account_token
        for seed_data in globals.seed_map.values()
    )


def get_req_token(req_token, seed=None):
    if configs.auto_seed:
        available_token_list = list(set(globals.token_list) - set(globals.error_token_list))
        length = len(available_token_list)
        if seed and length > 0:
            if seed not in globals.seed_map.keys():
                globals.seed_map[seed] = {"token": random.choice(available_token_list), "conversations": []}
                with open(globals.SEED_MAP_FILE, "w") as f:
                    json.dump(globals.seed_map, f, indent=4)
            else:
                req_token = globals.seed_map[seed]["token"]
            return req_token

        if req_token in configs.authorization_list:
            if len(available_token_list) > 0:
                if configs.random_token:
                    req_token = random.choice(available_token_list)
                    return req_token
                else:
                    globals.count += 1
                    globals.count %= length
                    return available_token_list[globals.count]
            else:
                return ""
        else:
            return req_token
    else:
        seed = req_token
        if seed not in globals.seed_map.keys():
            raise HTTPException(status_code=401, detail={"error": "Invalid Seed"})
        return globals.seed_map[seed]["token"]


async def verify_token(req_token):
    if not req_token:
        if configs.authorization_list:
            logger.error("Unauthorized with empty token.")
            raise HTTPException(status_code=401)
        else:
            return None
    else:
        if req_token.startswith("eyJhbGciOi") or req_token.startswith("fk-"):
            access_token = req_token
            return access_token
        # SessionToken：带 sess- 前缀的 chatgpt.com __Secure-next-auth.session-token
        elif req_token.startswith("sess-"):
            try:
                if req_token in globals.error_token_list:
                    raise HTTPException(status_code=401, detail="Error SessionToken")
                access_token = await sess2ac(req_token, force_refresh=False)
                return access_token
            except HTTPException as e:
                raise HTTPException(status_code=e.status_code, detail=e.detail)
        elif is_refresh_token(req_token):
            try:
                if req_token in globals.error_token_list:
                    raise HTTPException(status_code=401, detail="Error RefreshToken")

                access_token = await rt2ac(req_token, force_refresh=False)
                return access_token
            except HTTPException as e:
                raise HTTPException(status_code=e.status_code, detail=e.detail)
        else:
            return req_token


async def refresh_all_tokens(force_refresh=False):
    for token in list(set(globals.token_list) - set(globals.error_token_list)):
        try:
            if token.startswith("sess-"):
                await asyncio.sleep(0.5)
                await sess2ac(token, force_refresh=force_refresh)
            elif is_refresh_token(token):
                await asyncio.sleep(0.5)
                await rt2ac(token, force_refresh=force_refresh)
        except HTTPException:
            pass
    logger.info("All tokens refreshed.")
