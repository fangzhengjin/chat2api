"""模型响应名称、请求解析和远程模型列表提取工具。"""


model_proxy = {
    "gpt-3.5-turbo": "gpt-3.5-turbo-0125",
    "gpt-3.5-turbo-16k": "gpt-3.5-turbo-16k-0613",
    "gpt-4": "gpt-4-0613",
    "gpt-4-32k": "gpt-4-32k-0613",
    "gpt-4-turbo-preview": "gpt-4-0125-preview",
    "gpt-4-vision-preview": "gpt-4-1106-vision-preview",
    "gpt-4-turbo": "gpt-4-turbo-2024-04-09",
    "gpt-4o": "gpt-4o-2024-08-06",
    "gpt-4o-mini": "gpt-4o-mini-2024-07-18",
    "gpt-5": "gpt-5",
    "gpt-5-mini": "gpt-5-mini",
    "gpt-5-thinking": "gpt-5-thinking",
    "gpt-5-pro": "gpt-5-pro",
    "gpt-5-5": "gpt-5-5",
    "o1-preview": "o1-preview-2024-09-12",
    "o1-mini": "o1-mini-2024-09-12",
    "o1": "o1-2024-12-18",
    "o3-mini": "o3-mini-2025-01-31",
    "o3-mini-high": "o3-mini-high-2025-01-31",
    "o3-deep-research": "o3-deep-research-2025-06-26",
    "o4-mini-deep-research": "o4-mini-deep-research-2025-06-26",
    "gpt-4o-deep-research": "gpt-4o-deep-research",
    "deep-research": "deep-research",
    "claude-3-opus": "claude-3-opus-20240229",
    "claude-3-sonnet": "claude-3-sonnet-20240229",
    "claude-3-haiku": "claude-3-haiku-20240307",
}

CHATGPT_MODEL_DISPLAY_NAMES = {
    "gpt-5-3": "ChatGPT 5.3",
    "gpt-5-3-instant": "ChatGPT 5.3 Instant",
    "gpt-5-3-mini": "ChatGPT 5.3 Mini",
    "gpt-5-5": "ChatGPT 5.5",
    "gpt-5-5-instant": "ChatGPT 5.5 Instant",
    "gpt-5-5-mini": "ChatGPT 5.5 Mini",
    "gpt-5-5-pro": "ChatGPT 5.5 Pro",
    "gpt-5-5-thinking": "ChatGPT 5.5 Thinking",
    "gpt-5-6-pro": "ChatGPT 5.6 Pro",
    "gpt-5-6-thinking": "ChatGPT 5.6 Thinking",
}

model_system_fingerprint = {
    "gpt-3.5-turbo-0125": ["fp_b28b39ffa8"],
    "gpt-3.5-turbo-1106": ["fp_592ef5907d"],
    "gpt-4-0125-preview": ["fp_f38f4d6482", "fp_2f57f81c11", "fp_a7daf7c51e", "fp_a865e8ede4", "fp_13c70b9f70",
                           "fp_b77cb481ed"],
    "gpt-4-1106-preview": ["fp_e467c31c3d", "fp_d986a8d1ba", "fp_99a5a401bb", "fp_123d5a9f90", "fp_0d1affc7a6",
                           "fp_5c95a4634e"],
    "gpt-4-turbo-2024-04-09": ["fp_d1bac968b4"],
    "gpt-4o-2024-05-13": ["fp_3aa7262c27"],
    "gpt-4o-mini-2024-07-18": ["fp_c9aa9c0491"]
}

def get_response_model(origin_model):
    """返回兼容响应使用的模型名，参数为原始请求模型名。"""
    return model_proxy.get(origin_model, origin_model)


def resolve_request_model(origin_model):
    """解析请求模型与自定义 GPT ID，返回上游模型 slug 和 gizmo_id。"""
    origin_model = (origin_model or "gpt-5-5").strip()
    base_model = origin_model
    gizmo_id = None

    if "-gizmo-g-" in origin_model:
        base_model, _, gizmo_suffix = origin_model.partition("-gizmo-")
        gizmo_id = gizmo_suffix
    elif origin_model.startswith("g-"):
        gizmo_id = origin_model
        base_model = "gpt-5-5"

    return base_model, gizmo_id


def extract_model_slugs(models_payload):
    """从远程模型响应中提取 slug，参数为响应对象，返回 slug 集合。"""
    slugs = set()
    model_items = models_payload.get("models", [])
    if isinstance(model_items, dict):
        model_items = model_items.values()

    for model in model_items:
        if not isinstance(model, dict):
            continue

        for key in ("slug", "id", "model_slug"):
            value = model.get(key)
            if isinstance(value, str) and value:
                slugs.add(value)

        nested_model = model.get("model")
        if isinstance(nested_model, dict):
            for key in ("slug", "id", "model_slug"):
                value = nested_model.get(key)
                if isinstance(value, str) and value:
                    slugs.add(value)

    return slugs


def filter_chatgpt_models_payload(models_payload):
    """过滤网页端模型列表并重建选择菜单。

    Args:
        models_payload: 当前账号的上游 ``/backend-api/models`` 响应对象。

    Returns:
        仅保留允许模型、按固定顺序排列并默认选择 ``gpt-5-5`` 的新响应对象。
    """
    model_items = models_payload.get("models")
    if not isinstance(model_items, (list, dict)):
        return models_payload

    entries = model_items.items() if isinstance(model_items, dict) else enumerate(model_items)
    selected = {}
    for key, model in entries:
        if not isinstance(model, dict):
            continue
        slug = next((model.get(name) for name in ("slug", "id", "model_slug") if model.get(name)), None)
        nested_model = model.get("model")
        if not slug and isinstance(nested_model, dict):
            slug = next((nested_model.get(name) for name in ("slug", "id", "model_slug") if nested_model.get(name)), None)
        if not slug and isinstance(key, str):
            slug = key
        if slug not in CHATGPT_MODEL_DISPLAY_NAMES:
            continue

        filtered_model = model.copy()
        filtered_model["title"] = CHATGPT_MODEL_DISPLAY_NAMES[slug]
        filtered_model["display_name"] = CHATGPT_MODEL_DISPLAY_NAMES[slug]
        selected[slug] = (key, filtered_model)

    ordered_slugs = [slug for slug in CHATGPT_MODEL_DISPLAY_NAMES if slug in selected]
    filtered_payload = models_payload.copy()
    if isinstance(model_items, dict):
        filtered_payload["models"] = {selected[slug][0]: selected[slug][1] for slug in ordered_slugs}
    else:
        filtered_payload["models"] = [selected[slug][1] for slug in ordered_slugs]
    # 官方前端按 categories 构造一级菜单，并在渲染前反转数组。
    filtered_payload["categories"] = [
        {
            "category": slug,
            "human_category_name": CHATGPT_MODEL_DISPLAY_NAMES[slug],
            "human_category_short_name": CHATGPT_MODEL_DISPLAY_NAMES[slug],
            "human_category_shorter_name": CHATGPT_MODEL_DISPLAY_NAMES[slug],
            "default_model": slug,
            "short_explainer": slug,
            "title": CHATGPT_MODEL_DISPLAY_NAMES[slug],
        }
        for slug in reversed(ordered_slugs)
    ]
    filtered_payload["internal_groups"] = []
    filtered_payload["default_model_slug"] = "gpt-5-5"
    return filtered_payload
