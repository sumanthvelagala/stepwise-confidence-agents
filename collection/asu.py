"""ASU Research Computing's free API; credentials never enter run metadata."""
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

BASE_URL = "https://openai.rc.asu.edu/v1"


def load_key(path):
    for name in ("ASU_API_KEY", "ASU_AIR_API_KEY"):
        if os.environ.get(name, "").strip():
            return os.environ[name].strip()
    path = Path(path)
    if path.exists():
        for line in path.read_text().splitlines():
            name, sep, value = line.strip().removeprefix("export ").partition("=")
            if sep and name.strip() in {"ASU_API_KEY", "ASU_AIR_API_KEY"}:
                value = value.strip().strip("\"'")
                if value:
                    return value
    raise ValueError("Save your Voyager key as ASU_API_KEY in the credential file; do not paste it into chat")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward a bearer token to another endpoint.
        raise ValueError("ASU API redirected; refusing to forward credentials")


def list_models(key):
    request = urllib.request.Request(BASE_URL + "/models", headers={"Authorization": "Bearer " + key})
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=30) as response:
            models = json.load(response)["data"]
    except urllib.error.HTTPError as exc:
        raise ValueError(f"ASU model discovery failed (HTTP {exc.code}); check your Voyager key") from None
    except urllib.error.URLError:
        raise ValueError("Cannot reach ASU's API; check network connectivity") from None
    fields = ("id", "model_type", "context_window", "supports_function_calling", "supports_tool_choice",
              "reasoning", "family", "status", "replacement", "retire_at", "owned_by")
    return [{k: model[k] for k in fields if k in model} for model in models]


def model_identity(models, model, context):
    if model == "auto" or "/" in model or not model:
        raise ValueError("Choose one explicit ASU catalog model ID, without a provider prefix")
    info = next((m for m in models if m.get("id") == model), None)
    if info is None:
        raise ValueError("Requested model is absent from the ASU catalog; run --list-models")
    if info.get("model_type") != "chat" or info.get("supports_function_calling") is not True:
        raise ValueError("ASU model must advertise chat and function calling")
    if info.get("context_window", 0) < context:
        raise ValueError("ASU model context window is smaller than the requested collection context")
    if info.get("status") in {"deprecated", "retired"}:
        raise ValueError("Choose an active model rather than a retiring ASU model")
    return {"catalog": info, "weight_digest": None,
            "revision_limit": "Hosted catalog metadata is recorded; immutable weights are not exposed by this API"}
