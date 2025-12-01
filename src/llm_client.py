# src/llm_client.py
import os
import json
import traceback
import logging
from dotenv import load_dotenv
import google.generativeai as genai
import pprint
import logging
logger = logging.getLogger(__name__)

load_dotenv()
GEN_KEY = os.getenv("GEMINI_API_KEY")
if not GEN_KEY:
    raise EnvironmentError("GEMINI_API_KEY not set in .env")
genai.configure(api_key=GEN_KEY)

# Choose a model from your list_models output
MODEL_NAME = "models/gemini-2.5-flash"   # <--- change here if you want 'models/gemini-2.5-pro'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_model():
    """Return a ready-to-use GenerativeModel object."""
    return genai.GenerativeModel(MODEL_NAME)


def get_llm():
    """
    Compatibility alias.
    Some parts of the codebase (e.g. app.py) expect get_llm() to exist.
    This simply returns the same object as get_model().
    """
    return get_model()


# ------------------- Helpers for robust extraction & debugging -------------------

def safe_extract_text_from_candidate(cand):
    """
    Try many possible shapes for candidate -> text.
    Returns tuple (text_or_None, diagnostics_dict)
    """
    diag = {}
    try:
        diag['cand_type'] = type(cand).__name__
    except Exception:
        diag['cand_type'] = 'unknown'

    # 1) candidate has 'content' attribute
    try:
        content = getattr(cand, "content", None)
        diag['has_content_attr'] = content is not None
    except Exception as e:
        content = None
        diag['content_attr_error'] = str(e)

    # 2) if content is a dict-like or object with .parts
    try:
        if content is None:
            # maybe cand itself has text
            t = getattr(cand, "text", None)
            if t:
                diag['extraction_method'] = 'cand.text'
                return str(t), diag
        else:
            # content might be a simple str
            if isinstance(content, str):
                diag['extraction_method'] = 'content_is_str'
                return content, diag

            # content might have .parts (list of objects)
            parts = getattr(content, "parts", None)
            if parts is None and isinstance(content, (dict,)):
                parts = content.get("parts") or content.get("text") or None

            diag['parts_found'] = True if parts else False
            texts = []
            for p in (parts or []):
                # p may be object or dict
                t = None
                try:
                    t = getattr(p, "text", None)
                except Exception:
                    pass
                if not t and isinstance(p, dict):
                    t = p.get("text") or p.get("content") or None
                if t:
                    texts.append(str(t))
            if texts:
                diag['extraction_method'] = 'parts_join'
                return " ".join(texts), diag

            # maybe content itself has 'text' field
            t = getattr(content, "text", None) if not isinstance(content, dict) else content.get("text")
            if t:
                diag['extraction_method'] = 'content.text'
                return str(t), diag

    except Exception:
        diag['parts_exception'] = traceback.format_exc()

    # 3) cand might be dict-like
    try:
        if isinstance(cand, dict):
            if 'text' in cand and cand['text']:
                diag['extraction_method'] = 'cand_dict_text'
                return str(cand['text']), diag
            # nested: cand['content'] -> dict
            cont = cand.get('content') or {}
            if isinstance(cont, dict):
                if 'text' in cont and cont['text']:
                    diag['extraction_method'] = 'cand[content][text]'
                    return str(cont['text']), diag
                parts = cont.get('parts')
                if parts:
                    texts = [ (p.get('text') or p.get('content') or "") for p in parts ]
                    texts = [t for t in texts if t]
                    if texts:
                        diag['extraction_method'] = 'cand[content][parts]'
                        return " ".join(texts), diag
    except Exception:
        diag['cand_dict_exception'] = traceback.format_exc()

    # 4) fallback: try str(cand)
    try:
        s = str(cand)
        if s and len(s) > 0 and s != object.__str__(cand):
            diag['extraction_method'] = 'str(cand)_fallback'
            return s, diag
    except Exception:
        diag['str_fallback_error'] = traceback.format_exc()

    diag['extraction_method'] = 'none'
    return None, diag


def debug_run_verbose(prompt: str = "Say hello", max_output_tokens: int = 512):
    """
    Very-verbose diagnostic run. Returns a json-serializable dict describing the response shape.
    """
    model = get_model()
    try:
        resp = model.generate_content(prompt, generation_config={"max_output_tokens": max_output_tokens})
    except Exception as e:
        return {"error": "generate_content exception", "exc": str(e), "trace": traceback.format_exc()}

    out = {"raw_repr": repr(resp)}
    # try to convert to dict/json if possible
    try:
        out['raw_as_dict'] = json.loads(json.dumps(resp, default=lambda o: getattr(o, "__dict__", str(o))))
    except Exception as e:
        out['raw_as_dict_error'] = str(e)

    # Candidates info
    cands = getattr(resp, "candidates", None)
    out["candidates_len"] = len(cands) if cands is not None else 0

    if not cands:
        # also try resp.error / resp.message / resp.get('error')
        try:
            out['possible_error_fields'] = {
                'error_attr': getattr(resp, "error", None),
                'message_attr': getattr(resp, "message", None),
            }
        except Exception:
            pass
        return out

    # iterate over candidates and attempt extraction
    cand_infos = []
    for i, cand in enumerate(cands):
        ci = {"index": i, "type": type(cand).__name__}
        # common attrs
        for attr in ("finish_reason", "safety_ratings", "id"):
            try:
                ci[attr] = getattr(cand, attr, None)
            except Exception:
                ci[attr] = "error_reading"
        text, diag = safe_extract_text_from_candidate(cand)
        ci['extracted_text'] = text
        ci['diag'] = diag
        # also include repr of cand
        try:
            ci['cand_repr'] = repr(cand)
        except Exception:
            ci['cand_repr'] = "<repr error>"
        cand_infos.append(ci)

    out['candidates'] = cand_infos
    return out


# --- main run_prompt + lighter debug helper (drop-in replacements) ---

def run_prompt(prompt: str, max_output_tokens: int = 2048):
    """
    Calls the model and returns either:
      - {"text": "...", "raw_repr": ..., "diag": ...}
      - or an error dict with diagnostics.

    If no text is returned, this function now prints a readable dump to stdout
    and logs an error (so you can copy-paste the output here for debugging).
    """
    model = get_model()
    try:
        resp = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": max_output_tokens
            }
        )

        cands = getattr(resp, "candidates", None)
        if not cands:
            # Prepare a helpful error dict, print and log it
            err = {"error": "No candidates returned", "raw_repr": repr(resp)}
            try:
                import pprint
                print("=== LLM returned NO CANDIDATES ===")
                print("PROMPT:")
                print(prompt)
                print("RESPONSE (repr):")
                print(repr(resp))
                print("ERROR DICT:")
                pprint.pprint(err)
            except Exception:
                # fallback safe prints
                print("LLM returned no candidates. repr(resp):", repr(resp))
            logger.error("LLM returned no candidates for prompt: %s\nresp_repr: %s", prompt, repr(resp))
            return err

        cand = cands[0]
        text, diag = safe_extract_text_from_candidate(cand)
        if text:
            return {"text": text, "raw_repr": repr(resp), "diag": diag}

        # No text extracted — print & log full diagnostic info
        err = {
            "error": "No text returned by model",
            "finish_reason": getattr(cand, "finish_reason", None),
            "safety_ratings": getattr(cand, "safety_ratings", None),
            "diag": diag,
            "raw_repr": repr(resp)
        }
        try:
            import pprint
            print("=== LLM returned NO TEXT ===")
            print("PROMPT:")
            print(prompt)
            print("RESPONSE (repr):")
            print(repr(resp))
            print("CANDIDATE REPR:")
            try:
                print(repr(cand))
            except Exception:
                pass
            print("DIAGNOSTICS / ERROR DICT:")
            pprint.pprint(err)
        except Exception:
            # minimal fallback prints
            print("LLM returned no text. finish_reason:", err.get("finish_reason"))
            print("raw_repr:", err.get("raw_repr"))

        logger.error("LLM returned no text for prompt: %s\nerr: %s", prompt, err)
        return err

    except Exception as e:
        exc_info = {"error": "exception", "exc": str(e), "trace": traceback.format_exc()}
        try:
            import pprint
            print("=== Exception while calling model ===")
            print("PROMPT:")
            print(prompt)
            pprint.pprint(exc_info)
        except Exception:
            print("Exception while calling model:", str(e))
        logger.exception("Exception in run_prompt for prompt: %s", prompt)
        return exc_info


def debug_run(prompt: str = "Say hello", max_output_tokens: int = 512):
    """
    Diagnostic helper: returns a dict with candidates_len, finish_reason, safety and any extracted text.
    Use this to see exactly what the API returned.
    """
    model = get_model()
    resp = model.generate_content(prompt, generation_config={"max_output_tokens": max_output_tokens})
    out = {"raw": resp}

    cands = getattr(resp, "candidates", None)
    out["candidates_len"] = len(cands) if cands is not None else 0

    if not cands:
        return {"error": "no candidates in response", **out}

    cand = cands[0]
    out["finish_reason"] = getattr(cand, "finish_reason", None)
    out["safety_ratings"] = getattr(cand, "safety_ratings", None)

    # Try to extract any text parts
    try:
        parts = getattr(cand, "content", None).parts
        out["parts_len"] = len(parts) if parts is not None else 0
        texts = []
        for p in parts or []:
            t = getattr(p, "text", None) or (p.get("text") if isinstance(p, dict) else None)
            if t:
                texts.append(t)
        out["extracted_text"] = " ".join(texts) if texts else None
    except Exception as e:
        out["parts_error"] = str(e)

    return out
