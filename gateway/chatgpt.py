import json

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse

from app import app, templates
from chatgpt.authorization import resolve_gateway_seed
from gateway.login import login_html
from utils.kv_utils import set_value_for_key_list

with open("templates/chatgpt_context_1.json", "r", encoding="utf-8") as f:
    chatgpt_context_1 = json.load(f)
with open("templates/chatgpt_context_2.json", "r", encoding="utf-8") as f:
    chatgpt_context_2 = json.load(f)



@app.get("/", response_class=HTMLResponse)
async def chatgpt_html(request: Request):
    try:
        resolve_gateway_seed(request)
    except HTTPException:
        return await login_html(request)

    user_chatgpt_context_1 = chatgpt_context_1.copy()
    user_chatgpt_context_2 = chatgpt_context_2.copy()

    set_value_for_key_list(user_chatgpt_context_1, "accessToken", "chat2api-browser")
    if request.cookies.get("oai-locale"):
        set_value_for_key_list(user_chatgpt_context_1, "locale", request.cookies.get("oai-locale"))
    else:
        accept_language = request.headers.get("accept-language")
        if accept_language:
            set_value_for_key_list(user_chatgpt_context_1, "locale", accept_language.split(",")[0])

    user_chatgpt_context_1 = json.dumps(user_chatgpt_context_1, separators=(',', ':'), ensure_ascii=False)
    user_chatgpt_context_2 = json.dumps(user_chatgpt_context_2, separators=(',', ':'), ensure_ascii=False)

    escaped_context_1 = user_chatgpt_context_1.replace("\\", "\\\\").replace('"', '\\"')
    escaped_context_2 = user_chatgpt_context_2.replace("\\", "\\\\").replace('"', '\\"')

    clear_localstorage_script = """
    <script>
        const chat2apiDefaultModel = localStorage.getItem("chat2api.defaultModel");
        localStorage.clear();
        if (chat2apiDefaultModel) localStorage.setItem("chat2api.defaultModel", chat2apiDefaultModel);
    </script>
    """

    response = templates.TemplateResponse("chatgpt.html", {
        "request": request,
        "react_chatgpt_context_1": escaped_context_1,
        "react_chatgpt_context_2": escaped_context_2,
        "clear_localstorage_script": clear_localstorage_script
    })
    return response
