"""
SiteCortex — Shared VLM Caller
================================
Wraps Ollama with:
  - GPU delay between calls (your 7s observation)
  - Retry logic with adaptive temperature/context
  - GPU memory tracking
  - Timing instrumentation
"""
import time
import torch
import ollama


_last_call_time = 0.0


def gpu_mem_mb():
    """Return current GPU memory allocated in MB (CUDA only)."""
    if torch.cuda.is_available():
        return round(torch.cuda.memory_allocated() / 1024 / 1024, 1)
    return 0.0


def gpu_mem_peak_mb():
    """Return peak GPU memory in MB since last reset."""
    if torch.cuda.is_available():
        return round(torch.cuda.max_memory_allocated() / 1024 / 1024, 1)
    return 0.0


def reset_gpu_peak():
    """Reset peak memory tracker."""
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()


def _enforce_gpu_delay(delay_sec):
    """Wait so that at least `delay_sec` seconds pass between Ollama calls."""
    global _last_call_time
    if _last_call_time > 0:
        elapsed = time.time() - _last_call_time
        if elapsed < delay_sec:
            wait = delay_sec - elapsed
            time.sleep(wait)
    _last_call_time = time.time()


def ollama_chat(model_tag, messages, temperature=0.1, num_ctx=8192,
                num_predict=512, max_retries=3, gpu_delay=7,
                force_nothink=True):
    """
    Call Ollama with GPU delay, retries, and timing.

    Returns:
        (content_str, elapsed_sec, retry_count)
    """
    _enforce_gpu_delay(gpu_delay)

    # Append /nothink only for Qwen-family models.
    model_tag_l = (model_tag or "").lower()
    if force_nothink and "qwen" in model_tag_l and messages:
        messages = list(messages)
        last = messages[-1]
        if isinstance(last.get("content"), str):
            content = last["content"].rstrip()
            if not content.endswith("/nothink"):
                content += "\n/nothink"
            messages[-1] = {**last, "content": content}

    last_error = None
    # Progressive fallback: lower context + temperature on retries
    plans = [
        {"temperature": temperature, "num_ctx": num_ctx, "num_predict": num_predict},
        {"temperature": temperature, "num_ctx": num_ctx, "num_predict": num_predict},
        {"temperature": max(0.05, temperature - 0.05), "num_ctx": max(2048, num_ctx // 2),
         "num_predict": max(256, num_predict)},
    ]

    for attempt in range(1, max_retries + 1):
        opts = plans[min(attempt - 1, len(plans) - 1)]
        t0 = time.time()
        try:
            try:
                resp = ollama.chat(
                    model=model_tag,
                    messages=messages,
                    think=False,
                    options=opts,
                )
            except TypeError:
                # Older ollama versions don't support think=
                resp = ollama.chat(
                    model=model_tag,
                    messages=messages,
                    options=opts,
                )

            msg = resp.get("message", {}) if isinstance(resp, dict) else getattr(resp, "message", {})
            content = (msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", ""))
            content = (content or "").strip()

            if not content:
                raise RuntimeError("Empty response from Ollama")

            elapsed = round(time.time() - t0, 2)
            return content, elapsed, attempt - 1

        except Exception as e:
            # Some models/backends intermittently fail with a known server-side
            # sequence/numKeep issue. Retry once in this attempt with a minimal
            # request shape (no think/options) before counting the attempt failed.
            msg = str(e)
            if "SameBatch may not be specified within numKeep" in msg:
                try:
                    resp = ollama.chat(model=model_tag, messages=messages)
                    m = resp.get("message", {}) if isinstance(resp, dict) else getattr(resp, "message", {})
                    c = (m.get("content", "") if isinstance(m, dict) else getattr(m, "content", ""))
                    c = (c or "").strip()
                    if c:
                        elapsed = round(time.time() - t0, 2)
                        return c, elapsed, attempt - 1
                except Exception:
                    pass

            last_error = e
            elapsed = round(time.time() - t0, 2)
            if attempt < max_retries:
                wait = attempt * 3  # Progressive backoff: 3s, 6s
                print(f"  ⚠ Ollama attempt {attempt}/{max_retries} failed ({elapsed:.1f}s): {e}. "
                      f"Retrying in {wait}s...")
                time.sleep(wait)

    raise RuntimeError(f"Ollama failed after {max_retries} attempts: {last_error}")
