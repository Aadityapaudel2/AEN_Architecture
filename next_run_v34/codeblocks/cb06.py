# Auto-extracted by Aster from AENAIMO260_0_2_3_FINAL_CB5_CB8_CLOSED_BOOK_WORKING_20260427.ipynb
# Source cell: 22 / CB06 - Session and Cache Helpers
# Intended use: replace/run this CB cell in notebook order.

import atexit
import gc
import json
import os
import socket
import subprocess
import sys
import time
import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import torch
from openai import OpenAI


RUNTIME = globals().get("RUNTIME") if isinstance(globals().get("RUNTIME"), dict) else {}
AEN11_CB6_HELPER_REVISION = "2026-04-12-vllm-cb6-r12-strip-think-display"


def ensure_jinja2_nodes_compat() -> bool:
    """Patch runtimes where ``jinja2.nodes`` imports but is not exposed as an attribute."""
    try:
        import jinja2  # type: ignore

        if not hasattr(jinja2, "nodes"):
            setattr(jinja2, "nodes", importlib.import_module("jinja2.nodes"))
        return True
    except Exception:
        return False

# Convert loose runtime values to int with a safe fallback.
def coerce_int(value: object, default: int) -> int:
    if value is None:
        return int(default)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return int(value)
    text = str(value).strip()
    if not text:
        return int(default)
    try:
        return int(text)
    except Exception:
        return int(default)


PROMPT_FIT_BUFFER_TOKENS = coerce_int(globals().get("PROMPT_FIT_BUFFER_TOKENS"), 64)
CLIENT_TIMEOUT_SECONDS = coerce_int(globals().get("CLIENT_TIMEOUT_SECONDS"), 1800)
VALIDATE_RUNTIME_ON_BOOT = bool(globals().get("VALIDATE_RUNTIME_ON_BOOT", False))
PORT_REMAP_START = coerce_int(globals().get("PORT_REMAP_START"), 8000)
PORT_REMAP_END = coerce_int(globals().get("PORT_REMAP_END"), 8100)
ENABLE_TOKEN_STREAMING = bool(globals().get("ENABLE_TOKEN_STREAMING", True))
STREAM_TOKEN_MODE = str(globals().get("STREAM_TOKEN_MODE", "word") or "word").strip().lower()
if STREAM_TOKEN_MODE not in {"chunk", "word", "char"}:
    STREAM_TOKEN_MODE = "word"
STREAM_PRINT_ROLE_PREFIX = bool(globals().get("STREAM_PRINT_ROLE_PREFIX", True))


# Create and return the runtime working directory used for logs and transient artifacts.
def ensure_runtime_dir() -> Path:
    preferred = Path("/kaggle/working/aenaimo260_vllm_runtime")
    fallback = Path.cwd() / "aenaimo260_vllm_runtime"
    for candidate in [preferred, fallback]:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
        except Exception:
            continue
    return fallback


# Safely return the last characters of a log file for concise failure diagnostics.
def read_log_tail(path_like: Any, *, max_chars: int = 4000) -> str:
    if not path_like:
        return ""
    path = Path(str(path_like))
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[-max_chars:]
    except Exception:
        return ""


def strip_think_markup_local(text: str) -> str:
    stripper = globals().get("strip_think_markup")
    if callable(stripper):
        try:
            return str(stripper(str(text or "")))
        except Exception:
            pass
    cleaned = str(text or "")
    cleaned = cleaned.replace("</think>", " ").replace("<think>", " ")
    return cleaned


# Return an explicit HF config path when provided in spec, else None.
def maybe_prepare_hf_config_path(*, runtime_label: str, spec: dict[str, Any]) -> str | None:
    if str(spec.get("hf_config_path") or "").strip():
        return str(spec["hf_config_path"])
    return None


# Build a sanitized OpenAI-style message list from system prompt and dialogue history.
def build_openai_messages(system_prompt: str, history: list[dict[str, str]]) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    if str(system_prompt or "").strip():
        messages.append({"role": "system", "content": str(system_prompt).strip()})
    for message in list(history or []):
        if not isinstance(message, dict):
            continue
        role = str(message.get("role", "")).strip().lower()
        if role not in {"system", "user", "assistant"}:
            continue
        content = clean_dialogue_text(str(message.get("content", "") or ""))
        if not content:
            continue
        messages.append({"role": role, "content": content})
    return messages


# Load tokenizer from model directory and guarantee a usable pad token for prompt packing.
class HeuristicChatTokenizer:
    def __init__(self, model_dir: str) -> None:
        self.model_dir = str(model_dir or "")
        self.pad_token_id = 0
        self.eos_token = "<eos>"
        self.unk_token = "<unk>"
        self.pad_token = self.eos_token

    @staticmethod
    def _estimate_token_count(text: str) -> int:
        cleaned = str(text or "").strip()
        if not cleaned:
            return 0
        approx_by_chars = max(1, len(cleaned) // 4)
        approx_by_words = len([item for item in cleaned.replace("\n", " ").split(" ") if item])
        return max(1, min(len(cleaned), max(int(approx_by_chars), int(approx_by_words))))

    def __call__(self, text: str, add_special_tokens: bool = False) -> dict[str, Any]:
        _ = bool(add_special_tokens)
        token_count = self._estimate_token_count(str(text or ""))
        return {"input_ids": [0] * int(token_count)}

    def apply_chat_template(
        self,
        messages: list[dict[str, str]],
        *,
        tokenize: bool = False,
        add_generation_prompt: bool = True,
        enable_thinking: bool | None = None,
    ) -> Any:
        _ = enable_thinking
        rendered: list[str] = []
        for message in list(messages or []):
            if not isinstance(message, dict):
                continue
            role = str(message.get("role", "user") or "user").strip().lower() or "user"
            content = clean_dialogue_text(str(message.get("content", "") or ""))
            if not content:
                continue
            rendered.append(f"{role.upper()}:\n{content}")
        if add_generation_prompt:
            rendered.append("ASSISTANT:\n")
        prompt = "\n\n".join(rendered).strip()
        if not bool(tokenize):
            return prompt
        return self(prompt, add_special_tokens=False)


def load_tokenizer(model_dir: str) -> Any:
    try:
        ensure_jinja2_nodes_compat()
        from transformers import AutoTokenizer as _AutoTokenizer

        tokenizer = _AutoTokenizer.from_pretrained(str(model_dir), trust_remote_code=True)
        if tokenizer.pad_token_id is None:
            if tokenizer.eos_token is not None:
                tokenizer.pad_token = tokenizer.eos_token
            elif getattr(tokenizer, "unk_token", None) is not None:
                tokenizer.pad_token = tokenizer.unk_token
        return tokenizer
    except Exception as exc:
        print(
            json.dumps(
                {
                    "event": "cb6_tokenizer_fallback",
                    "model_dir": str(model_dir),
                    "fallback": "heuristic_chat_tokenizer",
                    "reason": str(exc)[:1000],
                },
                ensure_ascii=False,
                indent=2,
            ),
            flush=True,
        )
        return HeuristicChatTokenizer(str(model_dir))


# Render chat-template text with generation prompt and optional thinking toggle compatibility.
def apply_chat_template_text(
    tokenizer: Any,
    messages: list[dict[str, str]],
    *,
    enable_thinking: bool | None = None,
) -> str:
    kwargs: dict[str, Any] = {"tokenize": False, "add_generation_prompt": True}
    if enable_thinking is not None:
        kwargs["enable_thinking"] = enable_thinking
    try:
        ensure_jinja2_nodes_compat()
        return tokenizer.apply_chat_template(list(messages or []), **kwargs)
    except TypeError:
        kwargs.pop("enable_thinking", None)
        try:
            ensure_jinja2_nodes_compat()
            return tokenizer.apply_chat_template(list(messages or []), **kwargs)
        except Exception as exc:
            print(
                json.dumps(
                    {
                        "event": "cb6_chat_template_fallback",
                        "fallback": "heuristic_chat_template",
                        "reason": str(exc)[:1000],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                flush=True,
            )
            return HeuristicChatTokenizer("").apply_chat_template(
                list(messages or []),
                tokenize=False,
                add_generation_prompt=True,
            )
    except Exception as exc:
        print(
            json.dumps(
                {
                    "event": "cb6_chat_template_fallback",
                    "fallback": "heuristic_chat_template",
                    "reason": str(exc)[:1000],
                },
                ensure_ascii=False,
                indent=2,
            ),
            flush=True,
        )
        return HeuristicChatTokenizer("").apply_chat_template(
            list(messages or []),
            tokenize=False,
            add_generation_prompt=True,
        )


# Estimate token count for plain text using the active tokenizer.
def estimate_text_tokens(tokenizer: Any, text: str) -> int:
    encoded = tokenizer(str(text or ""), add_special_tokens=False)
    return len(list(encoded.get("input_ids") or []))


# Build templated completion prompt text and return prompt plus token count.
def build_completion_prompt(
    tokenizer: Any,
    *,
    system_prompt: str,
    history: list[dict[str, str]],
    enable_thinking: bool,
) -> tuple[str, int]:
    prompt = apply_chat_template_text(
        tokenizer,
        build_openai_messages(system_prompt, history),
        enable_thinking=enable_thinking,
    )
    prompt_tokens = estimate_text_tokens(tokenizer, prompt)
    return prompt, prompt_tokens


# Compute safe max_tokens by respecting context window, prompt size, and reserved buffer.
def resolve_completion_tokens(
    *,
    requested_max_tokens: int,
    prompt_tokens: int,
    context_limit: int,
) -> int:
    budget = int(context_limit) - int(prompt_tokens) - int(PROMPT_FIT_BUFFER_TOKENS)
    if budget <= 0:
        raise ValueError(
            "prompt does not fit the requested generation budget "
            f"in the {int(context_limit)}-token context window: "
            f"prompt_tokens={int(prompt_tokens)}, requested_max_tokens={int(requested_max_tokens)}, "
            f"available={int(budget)}"
        )
    return max(1, min(int(requested_max_tokens), int(budget)))


# Translate generation profile into one normalized OpenAI completion request payload.
def build_completion_request(
    generation_profile: dict[str, Any],
    *,
    prompt_tokens: int,
    context_limit: int,
) -> dict[str, Any]:
    allow_generation_stop_sequences = bool(globals().get("ALLOW_GENERATION_STOP_SEQUENCES", False))
    request: dict[str, Any] = {
        "temperature": float(generation_profile.get("temperature", 0.23)),
        "top_p": float(generation_profile.get("top_p", 0.95)),
        "max_tokens": resolve_completion_tokens(
            requested_max_tokens=int(generation_profile.get("max_tokens", 256)),
            prompt_tokens=int(prompt_tokens),
            context_limit=int(context_limit),
        ),
    }
    if "presence_penalty" in generation_profile and generation_profile["presence_penalty"] is not None:
        request["presence_penalty"] = float(generation_profile["presence_penalty"])
    if "frequency_penalty" in generation_profile and generation_profile["frequency_penalty"] is not None:
        request["frequency_penalty"] = float(generation_profile["frequency_penalty"])
    # Do not cut generations early by default; let the turn end naturally via EOS/max_tokens.
    if allow_generation_stop_sequences and "stop" in generation_profile:
        request["stop"] = generation_profile["stop"]
    extra_body: dict[str, Any] = {}
    for key in ["top_k", "repetition_penalty", "min_p"]:
        if key in generation_profile and generation_profile[key] is not None:
            extra_body[key] = generation_profile[key]
    if extra_body:
        request["extra_body"] = extra_body
    return request


# Extract usage counters from SDK objects or dict-like responses into a plain dict.
def response_usage_dict(response: Any) -> dict[str, Any]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return {}
    if hasattr(usage, "model_dump"):
        try:
            payload = usage.model_dump()
            if isinstance(payload, dict):
                return dict(payload)
        except Exception:
            pass
    payload: dict[str, Any] = {}
    for key in ["prompt_tokens", "completion_tokens", "total_tokens"]:
        value = getattr(usage, key, None)
        if value is not None:
            payload[key] = int(value)
    return payload


# Extract one text chunk from OpenAI completion stream events.
def extract_completion_text_chunk(event: Any) -> str:
    choices = getattr(event, "choices", None)
    if choices is None and isinstance(event, dict):
        choices = event.get("choices")
    items = list(choices or [])
    if not items:
        return ""
    choice = items[0]
    text = getattr(choice, "text", None)
    if text is None and isinstance(choice, dict):
        text = choice.get("text")
        if text is None:
            delta = choice.get("delta")
            if isinstance(delta, dict):
                text = delta.get("content") or delta.get("text")
    return str(text or "")


# Emit streamed completion text in chunk/word/char mode and return pending-buffer plus flush count.
def emit_stream_text(text: str, *, pending: str, mode: str) -> tuple[str, int]:
    if not text:
        return pending, 0
    if mode == "char":
        for ch in text:
            print(ch, end="", flush=True)
        return pending, len(text)
    if mode == "word":
        buffer = f"{pending}{text}"
        split_at = max(buffer.rfind(" "), buffer.rfind("\\n"), buffer.rfind("\\t"))
        if split_at < 0:
            return buffer, 0
        ready = buffer[: split_at + 1]
        remaining = buffer[split_at + 1 :]
        if ready:
            print(ready, end="", flush=True)
            return remaining, 1
        return remaining, 0
    print(text, end="", flush=True)
    return pending, 1


# Extract model ID strings from a /v1/models response payload.
def extract_model_ids(response: Any) -> list[str]:
    data = getattr(response, "data", None)
    if data is None and isinstance(response, dict):
        data = response.get("data")
    model_ids: list[str] = []
    for item in list(data or []):
        model_id = getattr(item, "id", None)
        if model_id is None and isinstance(item, dict):
            model_id = item.get("id")
        model_name = str(model_id or "").strip()
        if model_name:
            model_ids.append(model_name)
    return model_ids


# Normalize model ID text for fuzzy equality checks across naming variants.
def normalize_model_id(value: str) -> str:
    return "".join(ch.lower() for ch in str(value or "") if ch.isalnum())


# Safely call OpenAI models.list with dynamic attribute checks (keeps static analyzers quiet).
def openai_models_list(client: Any) -> Any:
    models_api = getattr(client, "models", None)
    list_fn = getattr(models_api, "list", None)
    if not callable(list_fn):
        raise RuntimeError("OpenAI client does not expose models.list()")
    return list_fn()


# Safely call OpenAI completions.create with dynamic attribute checks.
def openai_completions_create(client: Any, **kwargs: Any) -> Any:
    completions_api = getattr(client, "completions", None)
    create_fn = getattr(completions_api, "create", None)
    if not callable(create_fn):
        raise RuntimeError("OpenAI client does not expose completions.create()")
    return create_fn(**kwargs)


# Pick a compatible served model name or raise when an existing server is incompatible.
def select_compatible_model_name(
    *,
    expected_model_name: str,
    available_model_ids: list[str],
    allow_model_name_override: bool = False,
) -> str | None:
    expected = str(expected_model_name or "").strip()
    available = [str(item).strip() for item in list(available_model_ids or []) if str(item).strip()]
    if not available:
        return expected or None
    if expected and expected in available:
        return expected

    normalized_expected = normalize_model_id(expected)
    if normalized_expected:
        for candidate in available:
            if normalize_model_id(candidate) == normalized_expected:
                return candidate

    if len(available) == 1 and bool(allow_model_name_override):
        return available[0]

    if expected:
        raise RuntimeError(
            "existing vllm server model ids do not match the expected served model name "
            f"expected={expected!r}, available={available!r}"
        )
    return available[0]


# Attach to an already-running vLLM server when the endpoint is reachable and compatible.
def try_attach_existing_vllm_server(
    *,
    runtime_label: str,
    spec: dict[str, Any],
    allow_model_name_override: bool = False,
) -> tuple[dict[str, Any], OpenAI] | None:
    requested_context_limit = int(spec.get("context_limit", 0) or 0)
    requested_hf_overrides = dict(spec.get("hf_overrides") or {})
    if requested_context_limit >= 500000 or requested_hf_overrides:
        print(
            json.dumps(
                {
                    "event": "vllm_attach_skipped_for_long_context_profile",
                    "runtime_label": str(runtime_label),
                    "server_base_url": str(spec.get("server_base_url", "")),
                    "requested_context_limit": int(requested_context_limit),
                    "hf_overrides_enabled": bool(requested_hf_overrides),
                },
                ensure_ascii=False,
                indent=2,
            ),
            flush=True,
        )
        return None

    client: Any = OpenAI(
        api_key="EMPTY",
        base_url=str(spec["server_base_url"]),
        timeout=float(spec.get("client_timeout_seconds", CLIENT_TIMEOUT_SECONDS)),
    )
    try:
        models_response = openai_models_list(client)
    except Exception:
        return None

    available_model_ids = extract_model_ids(models_response)
    expected_model_name = str(spec.get("served_model_name", "") or "").strip()
    selected_model_name = select_compatible_model_name(
        expected_model_name=expected_model_name,
        available_model_ids=available_model_ids,
        allow_model_name_override=bool(allow_model_name_override),
    )
    if str(selected_model_name or "").strip() and selected_model_name != expected_model_name:
        spec["served_model_name"] = str(selected_model_name)
        print(
            json.dumps(
                {
                    "event": "vllm_attach_model_name_adjusted",
                    "runtime_label": runtime_label,
                    "server_base_url": str(spec["server_base_url"]),
                    "expected_model_name": expected_model_name,
                    "selected_model_name": str(selected_model_name),
                    "available_model_ids": list(available_model_ids),
                },
                ensure_ascii=False,
                indent=2,
            ),
            flush=True,
        )

    metadata = {
        "attached_existing": True,
        "runtime_label": runtime_label,
        "server_base_url": str(spec["server_base_url"]),
        "available_model_ids": list(available_model_ids),
        "allow_model_name_override": bool(allow_model_name_override),
        "command": [],
        "stdout_log": "",
        "stderr_log": "",
    }
    print(
        json.dumps(
            {
                "event": "vllm_attached_existing_server",
                "runtime_label": runtime_label,
                "server_base_url": str(spec["server_base_url"]),
                "served_model_name": str(spec.get("served_model_name", "")),
                "available_model_ids": list(available_model_ids),
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )
    return metadata, client


# Issue one completion call and return normalized text and usage with log-tail errors on failure.
def request_vllm_completion(
    client: Any,
    *,
    model_name: str,
    prompt: str,
    request: dict[str, Any],
    server_metadata: dict[str, Any] | None = None,
    stream: bool = False,
    stream_label: str = "",
) -> dict[str, Any]:
    if bool(stream) and bool(ENABLE_TOKEN_STREAMING):
        try:
            stream_iter = openai_completions_create(
                client,
                model=str(model_name),
                prompt=str(prompt),
                stream=True,
                **dict(request or {}),
            )
        except Exception as exc:
            raise RuntimeError(
                "vllm completion request could not reach the server.\n"
                f"stdout_tail=\n{read_log_tail((server_metadata or {}).get('stdout_log'))}\n\n"
                f"stderr_tail=\n{read_log_tail((server_metadata or {}).get('stderr_log'))}"
            ) from exc

        raw_chunks: list[str] = []
        usage: dict[str, Any] = {}
        pending = ""
        flush_count = 0
        chunk_count = 0
        callback_seconds = 0.0

        if bool(STREAM_PRINT_ROLE_PREFIX) and str(stream_label or "").strip():
            print(f"{str(stream_label).strip()}: ", end="", flush=True)

        for event in stream_iter:
            usage_candidate = response_usage_dict(event)
            if usage_candidate:
                usage = dict(usage_candidate)
            piece = extract_completion_text_chunk(event)
            if not piece:
                continue
            raw_chunks.append(piece)
            chunk_count += 1
            callback_started = time.perf_counter()
            display_piece = strip_think_markup_local(piece)
            pending, emitted = emit_stream_text(display_piece, pending=pending, mode=STREAM_TOKEN_MODE)
            callback_seconds += time.perf_counter() - callback_started
            flush_count += int(emitted)

        if STREAM_TOKEN_MODE == "word" and pending:
            callback_started = time.perf_counter()
            print(pending, end="", flush=True)
            callback_seconds += time.perf_counter() - callback_started
            flush_count += 1

        if chunk_count > 0:
            print("", flush=True)

        return {
            "raw_text": "".join(raw_chunks),
            "usage": usage,
            "stream_stats": {
                "callback_seconds": round(float(callback_seconds), 4),
                "flush_count": int(flush_count),
                "chunk_count": int(chunk_count),
            },
        }

    try:
        response = openai_completions_create(client, model=str(model_name), prompt=str(prompt), **dict(request or {}))
    except Exception as exc:
        raise RuntimeError(
            "vllm completion request could not reach the server.\n"
            f"stdout_tail=\n{read_log_tail((server_metadata or {}).get('stdout_log'))}\n\n"
            f"stderr_tail=\n{read_log_tail((server_metadata or {}).get('stderr_log'))}"
        ) from exc

    choices = list(getattr(response, "choices", []) or [])
    if not choices:
        raise RuntimeError(f"vllm returned no choices: {response}")
    return {
        "raw_text": str(getattr(choices[0], "text", "") or ""),
        "usage": response_usage_dict(response),
        "stream_stats": {
            "callback_seconds": 0.0,
            "flush_count": 0,
            "chunk_count": 0,
        },
    }


# Run a minimal smoke completion to verify the active server can generate successfully.
def validate_vllm_completion_route(
    *,
    client: OpenAI,
    model_name: str,
    server_metadata: dict[str, Any] | None = None,
) -> None:
    response = request_vllm_completion(
        client,
        model_name=model_name,
        prompt="Return the digit 1 only.",
        request={"temperature": 0.0, "top_p": 1.0, "max_tokens": 4},
        server_metadata=server_metadata,
    )
    usage = dict(response.get("usage") or {})
    print(
        json.dumps(
            {
                "event": "vllm_completion_route_smoke",
                "raw_text_chars": len(str(response.get("raw_text") or "")),
                "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
                "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )


@dataclass
# Stateful wrapper for one vLLM OpenAI endpoint plus dialogue/session bookkeeping.
class VLLMOpenAISession:
    label: str
    model_dir: str
    model_name: str
    tokenizer: Any
    context_limit: int
    system_prompt: str
    client: OpenAI
    enable_thinking: bool = False
    server_process: subprocess.Popen[str] | None = None
    server_metadata: dict[str, Any] = field(default_factory=dict)
    load_seconds: float = 0.0
    dialogue_messages: list[dict[str, str]] = field(default_factory=list)
    visible_transcript: list[dict[str, str]] = field(default_factory=list)
    original_problem_text: str = ""
    pending_user_text: str = ""
    committed_prompt_tokens: int = 0
    last_prompt_tokens_used: int = 0
    last_generated_tokens: int = 0
    last_raw_text: str = ""
    last_visible_text: str = ""
    last_think_text: str = ""
    rebase_count: int = 0
    last_trimmed_message_count: int = 0
    last_rebase_reason: str = ""
    last_generation_metadata: dict[str, Any] = field(default_factory=dict)

    # Return fully formatted OpenAI messages for current or provided history.
    def base_messages(self, candidate_history: list[dict[str, str]] | None = None) -> list[dict[str, str]]:
        history = candidate_history if candidate_history is not None else self.dialogue_messages
        return build_openai_messages(self.system_prompt, history)

    # Clear all dialogue, transcript, usage, and generation metadata for a fresh run.
    def reset_session(self) -> None:
        self.dialogue_messages = []
        self.visible_transcript = []
        self.original_problem_text = ""
        self.pending_user_text = ""
        self.committed_prompt_tokens = 0
        self.last_prompt_tokens_used = 0
        self.last_generated_tokens = 0
        self.last_raw_text = ""
        self.last_visible_text = ""
        self.last_think_text = ""
        self.rebase_count = 0
        self.last_trimmed_message_count = 0
        self.last_rebase_reason = ""
        self.last_generation_metadata = {}

    # Append a cleaned user turn into both internal dialogue and visible transcript state.
    def append_user_turn(self, text: str) -> None:
        cleaned = clean_dialogue_text(text)
        if not cleaned:
            return
        if not self.original_problem_text:
            self.original_problem_text = cleaned
        self.pending_user_text = cleaned
        self.dialogue_messages.append({"role": "user", "content": cleaned})
        self.visible_transcript.append({"role": "user", "content": cleaned})

    # Rollback the most recent pending user turn after a generation failure.
    def rollback_pending_user_turn(self) -> None:
        pending = clean_dialogue_text(self.pending_user_text)
        if pending and self.dialogue_messages:
            last_message = dict(self.dialogue_messages[-1] or {})
            if str(last_message.get("role", "")).strip().lower() == "user" and (
                clean_dialogue_text(str(last_message.get("content", "") or "")) == pending
            ):
                self.dialogue_messages.pop()
        if pending and self.visible_transcript:
            last_visible = dict(self.visible_transcript[-1] or {})
            if str(last_visible.get("role", "")).strip().lower() == "user" and (
                clean_dialogue_text(str(last_visible.get("content", "") or "")) == pending
            ):
                self.visible_transcript.pop()
        self.pending_user_text = ""

    # Commit assistant visible text to both internal dialogue and visible transcript.
    def commit_visible_turn(self, text: str) -> None:
        cleaned = clean_dialogue_text(text)
        self.dialogue_messages.append({"role": "assistant", "content": cleaned})
        self.visible_transcript.append({"role": "assistant", "content": cleaned})
        self.pending_user_text = ""

    # Generate one assistant turn end-to-end and persist response/usage metadata.
    def generate_assistant_turn(self, generation_profile: dict[str, Any]) -> dict[str, Any]:
        if self.server_process is not None and self.server_process.poll() is not None:
            raise RuntimeError(
                "vllm server is no longer running before generation started.\n"
                f"stdout_tail=\n{read_log_tail((self.server_metadata or {}).get('stdout_log'))}\n\n"
                f"stderr_tail=\n{read_log_tail((self.server_metadata or {}).get('stderr_log'))}"
            )

        completion_prompt, prompt_tokens = build_completion_prompt(
            self.tokenizer,
            system_prompt=self.system_prompt,
            history=self.dialogue_messages,
            enable_thinking=bool(self.enable_thinking),
        )
        request = build_completion_request(
            generation_profile,
            prompt_tokens=int(prompt_tokens),
            context_limit=int(self.context_limit),
        )
        started = time.perf_counter()
        response = request_vllm_completion(
            self.client,
            model_name=self.model_name,
            prompt=completion_prompt,
            request=request,
            server_metadata=self.server_metadata,
            stream=bool(ENABLE_TOKEN_STREAMING),
            stream_label=str(self.label),
        )
        wall_seconds = time.perf_counter() - started
        raw_text = str(response.get("raw_text") or "")
        visible_text = clean_dialogue_text(raw_text) or raw_text.strip()
        think_tags_detected = "<think" in raw_text.lower() or "</think>" in raw_text.lower()

        self.commit_visible_turn(visible_text)
        usage = dict(response.get("usage") or {})
        self.committed_prompt_tokens = int(prompt_tokens)
        self.last_prompt_tokens_used = int(usage.get("prompt_tokens", prompt_tokens) or prompt_tokens)
        self.last_generated_tokens = int(usage.get("completion_tokens", 0) or 0)
        self.last_raw_text = raw_text
        self.last_visible_text = visible_text
        self.last_think_text = ""
        stream_stats = dict(response.get("stream_stats") or {})
        self.last_generation_metadata = {
            "generate_wall_seconds": round(float(wall_seconds), 4),
            "decode_seconds": round(float(wall_seconds), 4),
            "post_turn_commit_seconds": 0.0,
            "post_turn_rebuild_seconds": 0.0,
            "prompt_tokens_used": int(self.last_prompt_tokens_used),
            "generated_tokens": int(self.last_generated_tokens),
            "context_limit": int(self.context_limit),
            "rebase_count": 0,
            "last_trimmed_message_count": 0,
            "last_rebase_reason": "",
            "stream_stats": {
                "callback_seconds": float(stream_stats.get("callback_seconds", 0.0) or 0.0),
                "flush_count": int(stream_stats.get("flush_count", 0) or 0),
                "chunk_count": int(stream_stats.get("chunk_count", 0) or 0),
            },
            "think_tags_detected": bool(think_tags_detected),
            "usage": usage,
        }
        return {
            "raw_text": raw_text,
            "visible_text": visible_text,
            "think_text": "",
            **dict(self.last_generation_metadata),
        }

    # Append a user prompt, generate assistant output, and rollback safely on error.
    def execute_user_turn(self, prompt: str, generation_profile: dict[str, Any]) -> dict[str, Any]:
        self.append_user_turn(prompt)
        try:
            return self.generate_assistant_turn(generation_profile)
        except Exception:
            self.rollback_pending_user_turn()
            raise


# Gracefully terminate a server process, then force-kill if required.
def stop_server_process(process: subprocess.Popen[str] | None) -> None:
    if process is None or process.poll() is not None:
        return
    try:
        process.terminate()
        process.wait(timeout=20)
    except Exception:
        try:
            process.kill()
            process.wait(timeout=10)
        except Exception:
            pass


# Return whether a TCP port is currently occupied on the given host.
def is_port_occupied(host: str, port: int, *, timeout_seconds: float = 0.25) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(float(timeout_seconds))
            return sock.connect_ex((str(host), int(port))) == 0
    except Exception:
        return False


# Remap runtime spec to the first free port in range and emit a trace event.
def remap_spec_to_open_port(*, runtime_label: str, spec: dict[str, Any], start_port: int, end_port: int) -> int:
    host = str(spec.get("server_host") or "127.0.0.1")
    original_port = int(spec["server_port"])
    lower = min(int(start_port), int(end_port))
    upper = max(int(start_port), int(end_port))
    for candidate in range(lower, upper + 1):
        if int(candidate) == int(original_port):
            continue
        if is_port_occupied(host, int(candidate)):
            continue
        spec["server_port"] = int(candidate)
        spec["server_base_url"] = f"http://{host}:{int(candidate)}/v1"
        print(
            json.dumps(
                {
                    "event": "vllm_server_port_remapped",
                    "runtime_label": runtime_label,
                    "from_port": int(original_port),
                    "to_port": int(candidate),
                    "server_base_url": str(spec["server_base_url"]),
                },
                ensure_ascii=False,
                indent=2,
            ),
            flush=True,
        )
        return int(candidate)
    raise RuntimeError(
        "could not find a free local port for vLLM launch after model-mismatch attach rejection "
        f"(runtime_label={runtime_label!r}, requested_port={int(original_port)}, "
        f"search_range=[{int(lower)}, {int(upper)}])"
    )


# Build the complete vLLM OpenAI server launch command from runtime spec fields.
def build_vllm_command(spec: dict[str, Any]) -> list[str]:
    command = [
        str(sys.executable or "python"),
        "-m",
        "vllm.entrypoints.openai.api_server",
        "--model",
        str(spec["model_dir"]),
        "--served-model-name",
        str(spec["served_model_name"]),
        "--tensor-parallel-size",
        str(int(spec.get("tensor_parallel_size", 1))),
        "--host",
        str(spec["server_host"]),
        "--port",
        str(int(spec["server_port"])),
        "--dtype",
        str(spec.get("torch_dtype", "bfloat16")),
        "--gpu-memory-utilization",
        str(spec["gpu_memory_utilization"]),
        "--max-model-len",
        str(int(spec["context_limit"])),
        "--max-num-seqs",
        "1",
        "--disable-log-stats",
    ]
    if str(spec.get("reasoning_parser") or "").strip():
        command.extend(["--reasoning-parser", str(spec["reasoning_parser"])])
    if str(spec.get("kv_cache_dtype") or "").strip():
        command.extend(["--kv-cache-dtype", str(spec["kv_cache_dtype"])])
    if str(spec.get("attention_backend") or "").strip():
        command.extend(["--attention-backend", str(spec["attention_backend"])])
    if bool(spec.get("language_model_only", False)):
        command.append("--language-model-only")
    if bool(spec.get("trust_remote_code", True)):
        command.append("--trust-remote-code")
    if str(spec.get("hf_config_path") or "").strip():
        command.extend(["--hf-config-path", str(spec["hf_config_path"])])
    hf_overrides = spec.get("hf_overrides")
    if isinstance(hf_overrides, dict) and hf_overrides:
        command.extend(["--hf-overrides", json.dumps(hf_overrides, ensure_ascii=False, separators=(",", ":"))])
    if str(spec.get("cpu_offload_gb") or "").strip():
        command.extend(["--cpu-offload-gb", str(spec["cpu_offload_gb"])])
    if bool(spec.get("enforce_eager", False)):
        command.append("--enforce-eager")
    if spec.get("compilation_mode") is not None:
        command.append(f"-O.mode={int(spec['compilation_mode'])}")
    if str(spec.get("cudagraph_mode") or "").strip():
        command.append(f"-O.cudagraph_mode={str(spec['cudagraph_mode'])}")
    if bool(spec.get("disable_hybrid_kv_cache_manager", False)):
        command.append("--disable-hybrid-kv-cache-manager")
    return command


# Attach to compatible existing server or launch a new one and wait until ready.
def launch_vllm_process(
    *,
    runtime_label: str,
    spec: dict[str, Any],
) -> tuple[subprocess.Popen[str] | None, dict[str, Any], OpenAI]:
    runtime_dir = ensure_runtime_dir()
    log_dir = runtime_dir / "vllm_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout_log = log_dir / f"{runtime_label}_stdout.log"
    stderr_log = log_dir / f"{runtime_label}_stderr.log"
    allow_model_name_override = bool(spec.get("allow_attach_model_mismatch", False))
    auto_remap_on_model_mismatch = bool(spec.get("auto_remap_server_port_on_model_mismatch", True))
    remap_start = int(spec.get("port_remap_start", PORT_REMAP_START))
    remap_end = int(spec.get("port_remap_end", PORT_REMAP_END))
    command = build_vllm_command(spec)
    try:
        attached = try_attach_existing_vllm_server(
            runtime_label=runtime_label,
            spec=spec,
            allow_model_name_override=allow_model_name_override,
        )
    except RuntimeError as attach_error:
        print(
            json.dumps(
                {
                    "event": "vllm_attach_rejected",
                    "runtime_label": runtime_label,
                    "server_base_url": str(spec.get("server_base_url", "")),
                    "allow_attach_model_mismatch": bool(allow_model_name_override),
                    "auto_remap_server_port_on_model_mismatch": bool(auto_remap_on_model_mismatch),
                    "reason": str(attach_error),
                },
                ensure_ascii=False,
                indent=2,
            ),
            flush=True,
        )
        if not bool(auto_remap_on_model_mismatch):
            raise
        remap_spec_to_open_port(
            runtime_label=runtime_label,
            spec=spec,
            start_port=remap_start,
            end_port=remap_end,
        )
        command = build_vllm_command(spec)
        attached = None
    if attached is not None:
        metadata, client = attached
        metadata["command"] = list(command)
        metadata["ready"] = True
        metadata["effective_spec"] = dict(spec)
        return None, metadata, client

    print(
        f"starting {runtime_label} vllm backend from {spec['model_dir']} on {spec['server_base_url']} "
        f"(device={str(spec.get('device', 'auto') or 'auto')})",
        flush=True,
    )

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env.setdefault("TRANSFORMERS_NO_TF", "1")
    env.setdefault("TRANSFORMERS_NO_FLAX", "1")
    env.setdefault("USE_TF", "0")
    env.setdefault("USE_FLAX", "0")
    env.setdefault("TOKENIZERS_PARALLELISM", "false")
    env.setdefault("VLLM_LOGGING_LEVEL", "INFO")
    if str(spec.get("device") or "").strip():
        env["VLLM_TARGET_DEVICE"] = str(spec["device"])
        env["VLLM_DEVICE"] = str(spec["device"])
    if bool(spec.get("disable_compile_cache", False)):
        env["VLLM_DISABLE_COMPILE_CACHE"] = "1"
    for key, value in dict(spec.get("env_overrides") or {}).items():
        env[str(key)] = str(value)

    stdout_handle = stdout_log.open("w", encoding="utf-8")
    stderr_handle = stderr_log.open("w", encoding="utf-8")
    process = subprocess.Popen(command, stdout=stdout_handle, stderr=stderr_handle, env=env, text=True)
    stdout_handle.close()
    stderr_handle.close()

    metadata = {
        "stdout_log": str(stdout_log),
        "stderr_log": str(stderr_log),
        "command": list(command),
        "device": str(spec.get("device", "")),
    }

    client: Any = OpenAI(
        api_key="EMPTY",
        base_url=str(spec["server_base_url"]),
        timeout=float(spec.get("client_timeout_seconds", CLIENT_TIMEOUT_SECONDS)),
    )

    started = time.time()
    deadline = started + max(1, int(spec["server_start_timeout_sec"]))
    last_error = ""
    last_reported = -1
    device_retry_available = bool(str(env.get("CUDA_VISIBLE_DEVICES", "") or "").strip())
    device_retry_attempted = False
    try:
        while time.time() < deadline:
            if process.poll() is not None:
                stdout_tail = read_log_tail(stdout_log)
                stderr_tail = read_log_tail(stderr_log)
                port_in_use_markers = [
                    "address already in use",
                    "errno 98",
                    "errno 10048",
                ]
                lower_tails = f"{stdout_tail}\n{stderr_tail}".lower()
                if any(marker in lower_tails for marker in port_in_use_markers):
                    attached = try_attach_existing_vllm_server(
                        runtime_label=runtime_label,
                        spec=spec,
                        allow_model_name_override=allow_model_name_override,
                    )
                    if attached is not None:
                        attached_metadata, attached_client = attached
                        attached_metadata["command"] = list(command)
                        attached_metadata["ready"] = True
                        attached_metadata["attach_after_bind_failure"] = True
                        attached_metadata["stdout_log"] = str(stdout_log)
                        attached_metadata["stderr_log"] = str(stderr_log)
                        attached_metadata["effective_spec"] = dict(spec)
                        return None, attached_metadata, attached_client
                if (
                    "failed to infer device type" in lower_tails
                    and bool(device_retry_available)
                    and not bool(device_retry_attempted)
                ):
                    device_retry_attempted = True
                    env.pop("CUDA_VISIBLE_DEVICES", None)
                    if str(spec.get("device") or "").strip():
                        env["VLLM_TARGET_DEVICE"] = str(spec["device"])
                        env["VLLM_DEVICE"] = str(spec["device"])
                    env.setdefault("VLLM_LOGGING_LEVEL", "INFO")
                    print(
                        json.dumps(
                            {
                                "event": "vllm_device_infer_retry",
                                "runtime_label": str(runtime_label),
                                "reason": "failed_to_infer_device_type",
                                "retry_mode": "without_cuda_visible_devices",
                                "server_base_url": str(spec.get("server_base_url", "")),
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                        flush=True,
                    )
                    stdout_handle = stdout_log.open("w", encoding="utf-8")
                    stderr_handle = stderr_log.open("w", encoding="utf-8")
                    process = subprocess.Popen(command, stdout=stdout_handle, stderr=stderr_handle, env=env, text=True)
                    stdout_handle.close()
                    stderr_handle.close()
                    started = time.time()
                    deadline = started + max(1, int(spec["server_start_timeout_sec"]))
                    last_reported = -1
                    last_error = ""
                    continue
                if "failed to infer device type" in lower_tails:
                    parent_cuda_available = bool(torch.cuda.is_available())
                    parent_cuda_count = int(torch.cuda.device_count()) if parent_cuda_available else 0
                    launch_cuda_visible = str(env.get("CUDA_VISIBLE_DEVICES", "<unset>"))
                    launch_target_device = str(env.get("VLLM_TARGET_DEVICE", "<unset>"))
                    raise RuntimeError(
                        "vllm server exited before becoming ready.\n"
                        f"stdout_tail=\n{stdout_tail}\n\nstderr_tail=\n{stderr_tail}\n\n"
                        "device_inference_diagnostic:\n"
                        f"parent_torch_cuda_available={parent_cuda_available}\n"
                        f"parent_torch_cuda_device_count={parent_cuda_count}\n"
                        f"launch_env_cuda_visible_devices={launch_cuda_visible}\n"
                        f"launch_env_vllm_target_device={launch_target_device}"
                    )
                raise RuntimeError(
                    "vllm server exited before becoming ready.\n"
                    f"stdout_tail=\n{stdout_tail}\n\nstderr_tail=\n{stderr_tail}"
                )
            try:
                openai_models_list(client)
                metadata["ready"] = True
                return process, metadata, client
            except Exception as exc:
                last_error = str(exc)
            elapsed = int(time.time() - started)
            if elapsed >= 10 and elapsed % 10 == 0 and elapsed != last_reported:
                print(f"{runtime_label} waiting... {elapsed}s elapsed", flush=True)
                last_reported = elapsed
            time.sleep(2.0)
        raise TimeoutError(
            f"timed out waiting for vLLM readiness at {spec['server_base_url']}: {last_error}\n"
            f"stdout_tail=\n{read_log_tail(stdout_log)}\n\nstderr_tail=\n{read_log_tail(stderr_log)}"
        )
    except Exception:
        stop_server_process(process)
        raise


# Stop the server process associated with one runtime session object.
def unload_runtime_session(session: Any) -> None:
    if session is None:
        return
    stop_server_process(getattr(session, "server_process", None))


# Tear down solver/clerk runtime sessions and clear CUDA cache for a clean restart.
def cleanup_runtime() -> None:
    global RUNTIME
    for key in ["solver_session", "clerk_session", "agent_session"]:
        unload_runtime_session((RUNTIME or {}).get(key))
    RUNTIME = {}
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


# Return active runtime dict, raising if CB8 startup has not completed.
def ensure_runtime_started() -> dict[str, Any]:
    global RUNTIME
    if isinstance(RUNTIME, dict) and RUNTIME.get("solver_session"):
        return RUNTIME
    starter = globals().get("start_aen_runtime")
    if not callable(starter):
        raise RuntimeError("runtime is not started. Run CB8 first.")
    print({"event": "cb06_lazy_runtime_boot_start"}, flush=True)
    try:
        runtime = starter()
        if not isinstance(runtime, dict):
            raise RuntimeError("runtime starter returned invalid runtime state.")
        RUNTIME = runtime
        return runtime
    except Exception as exc:
        existing_runtime = dict(RUNTIME) if isinstance(RUNTIME, dict) else {}
        blocked_reason = f"{type(exc).__name__}: {exc}"
        runtime_at_boot_summary = {
            "event": "cb06_lazy_runtime_boot_failed",
            "passed": False,
            "status": "lazy_boot_failed",
            "blocked_reason": str(blocked_reason),
            "exception_type": str(type(exc).__name__),
            "exception_message": str(exc),
        }
        existing_runtime.update(
            {
                "runtime_at_boot_passed": False,
                "runtime_at_boot_status": "lazy_boot_failed",
                "runtime_at_boot_summary": dict(runtime_at_boot_summary),
            }
        )
        RUNTIME = existing_runtime
        print(dict(runtime_at_boot_summary), flush=True)
        return RUNTIME


# Warm tokenizer/model assets used by session startup and return model path.
def preload_model_weights(model_dir: str) -> str:
    load_tokenizer(model_dir)
    return str(model_dir)


# Load one vLLM-backed session from spec, including tokenizer and server readiness checks.
def load_vllm_openai_session(spec: dict[str, Any]) -> VLLMOpenAISession:
    spec = dict(spec)
    label = str(spec["runtime_label"])
    print(f"cb6_progress = entering load_vllm_openai_session[{label}]", flush=True)
    hf_config_path = maybe_prepare_hf_config_path(runtime_label=label, spec=spec)
    if hf_config_path:
        spec["hf_config_path"] = hf_config_path
        print(f"cb6_progress = prepared hf config[{label}] -> {hf_config_path}", flush=True)
    print(f"cb6_progress = loading tokenizer for vllm backend[{label}]", flush=True)
    tokenizer = load_tokenizer(str(spec["model_dir"]))
    print(f"cb6_progress = tokenizer loaded for vllm backend[{label}]", flush=True)
    print(f"cb6_progress = launching vllm process[{label}]", flush=True)
    launched_at = time.perf_counter()
    process, metadata, client = launch_vllm_process(runtime_label=label, spec=spec)
    if bool(metadata.get("attached_existing")):
        print(f"cb6_progress = attached existing vllm backend[{label}]", flush=True)
    else:
        print(f"cb6_progress = vllm process launched[{label}]", flush=True)
    load_seconds = round(time.perf_counter() - launched_at, 3)
    if VALIDATE_RUNTIME_ON_BOOT:
        print(f"cb6_progress = validating completion route[{label}]", flush=True)
        validate_vllm_completion_route(
            client=client,
            model_name=str(spec["served_model_name"]),
            server_metadata=metadata,
        )
        print(f"cb6_progress = completion route validated[{label}]", flush=True)
    else:
        print(f"cb6_progress = automatic generation validation disabled[{label}]", flush=True)
    print(f"{label} vllm backend ready in {load_seconds:.2f}s", flush=True)
    metadata["effective_spec"] = dict(spec)
    rope_parameters = (
        dict(dict(dict(spec.get("hf_overrides") or {}).get("text_config") or {}).get("rope_parameters") or {})
    )
    yarn_cert = {
        "event": "cb6_yarn_runtime_cert",
        "runtime_label": str(label),
        "context_limit": int(spec["context_limit"]),
        "hf_overrides_enabled": bool(spec.get("hf_overrides")),
        "rope_type": str(rope_parameters.get("rope_type", "")),
        "rope_factor": rope_parameters.get("factor"),
        "original_max_position_embeddings": rope_parameters.get("original_max_position_embeddings"),
        "yarn_expected": bool(
            int(spec.get("context_limit", 0) or 0) >= 500000
            or str(rope_parameters.get("rope_type", "") or "").strip().lower() == "yarn"
        ),
    }
    print(json.dumps(yarn_cert, ensure_ascii=False, separators=(",", ":")), flush=True)
    return VLLMOpenAISession(
        label=label,
        model_dir=str(spec["model_dir"]),
        model_name=str(spec["served_model_name"]),
        tokenizer=tokenizer,
        context_limit=int(spec["context_limit"]),
        system_prompt=str(spec["system_prompt"]),
        client=client,
        enable_thinking=bool(spec.get("enable_thinking", False)),
        server_process=process,
        server_metadata=metadata,
        load_seconds=float(load_seconds),
    )


# Preview prompt-fit accounting for one session turn without generating model output.
def preview_session_turn_prompt(
    *,
    session: VLLMOpenAISession,
    prompt: str,
    requested_max_tokens: int,
    system_prompt: str | None = None,
) -> dict[str, Any]:
    history = list(session.dialogue_messages)
    cleaned_prompt = clean_dialogue_text(prompt)
    if cleaned_prompt:
        history.append({"role": "user", "content": cleaned_prompt})
    completion_prompt, prompt_tokens = build_completion_prompt(
        session.tokenizer,
        system_prompt=str(system_prompt or session.system_prompt),
        history=history,
        enable_thinking=bool(session.enable_thinking),
    )
    resolved_max_tokens = resolve_completion_tokens(
        requested_max_tokens=int(requested_max_tokens),
        prompt_tokens=int(prompt_tokens),
        context_limit=int(session.context_limit),
    )
    return {
        "completion_prompt": completion_prompt,
        "prompt_tokens_used": int(prompt_tokens),
        "context_limit": int(session.context_limit),
        "context_tokens_remaining": int(session.context_limit) - int(prompt_tokens) - int(PROMPT_FIT_BUFFER_TOKENS),
        "resolved_max_tokens": int(resolved_max_tokens),
    }


# Convenience preview wrapper for the solver session.
def preview_solver_turn_prompt(
    *,
    prompt: str,
    requested_max_tokens: int,
    system_prompt: str | None = None,
) -> dict[str, Any]:
    session = ensure_runtime_started()["solver_session"]
    return preview_session_turn_prompt(
        session=session,
        prompt=prompt,
        requested_max_tokens=requested_max_tokens,
        system_prompt=system_prompt,
    )


# Convenience preview wrapper for the clerk session.
def preview_clerk_turn_prompt(
    *,
    prompt: str,
    requested_max_tokens: int,
    system_prompt: str | None = None,
) -> dict[str, Any]:
    session = ensure_runtime_started()["clerk_session"]
    return preview_session_turn_prompt(
        session=session,
        prompt=prompt,
        requested_max_tokens=requested_max_tokens,
        system_prompt=system_prompt,
    )


_ = atexit.register(cleanup_runtime)

"""## 06.5 - Sampling Parameters



"""
