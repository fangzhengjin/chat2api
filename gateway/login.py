from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app import app, templates
from chatgpt.authorization import GATEWAY_COOKIE_NAME, resolve_gateway_seed, resolve_gateway_seed_value


@app.get("/login", response_class=HTMLResponse)
async def login_html(request: Request):
    try:
        resolve_gateway_seed(request)
        return RedirectResponse(url="/", status_code=302)
    except HTTPException:
        return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login_submit(request: Request):
    """验证后台生成的访问密码并写入浏览器 Cookie。

    Args:
        request: 包含 password 表单字段的登录请求。

    Returns:
        验证成功时重定向到 Chat 页面，否则返回带错误信息的登录页。
    """
    form = await request.form()
    password = (form.get("password") or "").strip()
    try:
        resolve_gateway_seed_value(password)
    except HTTPException:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "访问密码无效"},
            status_code=401,
        )

    response = RedirectResponse(url="/", status_code=302)
    is_https = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    response.set_cookie(
        GATEWAY_COOKIE_NAME,
        value=password,
        httponly=True,
        secure=is_https,
        samesite="lax",
        path="/",
    )
    return response
