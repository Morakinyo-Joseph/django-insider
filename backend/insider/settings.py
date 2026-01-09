"""
insider.settings
----------------

Configuration manager for the `insider` package.

Usage:
    from insider import settings as insider_settings
    cfg = insider_settings.settings
    print(cfg.IGNORE_PATHS)
    # or
    insider_settings.get("MAX_RESPONSE_LENGTH", 500)

Behavior:
- Preferred source: `INSIDER` dict in project's settings.py.
- Backwards compatible with `REQUEST_LOGGER` dict and individual INSIDER_* vars.
- Validates types and normalizes common values.
- Safe to import from anywhere inside the package.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Iterable, List, Optional
import warnings


# Django must be available at runtime for this package to be used.
try:
    from django.conf import settings as django_settings
except Exception: 
    django_settings = None


# Default configuration values
DEFAULTS: Dict[str, Any] = {
    "IGNORE_PATHS": ["/static/", "/media/", "/favicon.ico"],
    "IGNORE_ADMIN": True,
    "CAPTURE_RESPONSE": False,
    "CAPTURE_REQUEST_BODY": False,
    "SLOW_REQUEST_THRESHOLD": None,  # milliseconds or None
    "MAX_RESPONSE_LENGTH": 500,
    "MASK_FIELDS": ["password", "token", "secret", "pin", "authorization"],
    "DB_ALIAS": "default",  # which DB to use if multi-db setups
    "CAPTURE_USER": True,
    "CAPTURE_IP": True,
    "CAPTURE_USER_AGENT": True,
    "LOG_LEVEL": "INFO",  # optional: DEBUG/INFO/WARNING/ERROR
    "EXCLUDE_CONTENT_TYPES": ["application/octet-stream"],
    "CAPTURE_METHODS": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    "PUBLISHERS": [],
    "NOTIFIERS": [],
    "COOLDOWN_HOURS": 24,
}


@dataclass
class InsiderSettings:
    IGNORE_PATHS: List[str] = field(default_factory=lambda: DEFAULTS["IGNORE_PATHS"][:])
    IGNORE_ADMIN: bool = DEFAULTS["IGNORE_ADMIN"]
    CAPTURE_RESPONSE: bool = DEFAULTS["CAPTURE_RESPONSE"]
    CAPTURE_REQUEST_BODY: bool = DEFAULTS["CAPTURE_REQUEST_BODY"]
    SLOW_REQUEST_THRESHOLD: Optional[int] = DEFAULTS["SLOW_REQUEST_THRESHOLD"]
    MAX_RESPONSE_LENGTH: int = DEFAULTS["MAX_RESPONSE_LENGTH"]
    MASK_FIELDS: List[str] = field(default_factory=lambda: DEFAULTS["MASK_FIELDS"][:])
    DB_ALIAS: str = DEFAULTS["DB_ALIAS"]
    CAPTURE_USER: bool = DEFAULTS["CAPTURE_USER"]
    CAPTURE_IP: bool = DEFAULTS["CAPTURE_IP"]
    CAPTURE_USER_AGENT: bool = DEFAULTS["CAPTURE_USER_AGENT"]
    LOG_LEVEL: str = DEFAULTS["LOG_LEVEL"]
    EXCLUDE_CONTENT_TYPES: List[str] = field(default_factory=lambda: DEFAULTS["EXCLUDE_CONTENT_TYPES"][:])
    CAPTURE_METHODS: List[str] = field(default_factory=lambda: DEFAULTS["CAPTURE_METHODS"][:])
    PUBLISHERS: List[str] = field(default_factory=lambda: DEFAULTS["PUBLISHERS"][:])
    NOTIFIERS: List[str] = field(default_factory=lambda: DEFAULTS["NOTIFIERS"][:])
    COOLDOWN_HOURS: int = DEFAULTS["COOLDOWN_HOURS"]

    # Additional raw dict copy for introspection if needed
    _raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    def asdict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop("_raw", None)
        return d


def _load_user_config() -> Dict[str, Any]:
    """
    Loads configuration from the Django settings module.

    Preference order:
    1. INSIDER (dict)           <- recommended
    2. Individual INSIDER_*     <- optional overrides
    """

    if not django_settings:
        return {}

    cfg = {}

    # 1) Preferred: INSIDER = {...}
    if hasattr(django_settings, "INSIDER"):
        user_dict = getattr(django_settings, "INSIDER") or {}
        if not isinstance(user_dict, dict):
            raise ValueError("INSIDER must be a dictionary.")
        cfg.update(user_dict)

    # 2) Optional: individual INSIDER_* settings override values from INSIDER dict
    for key in DEFAULTS.keys():
        setting_name = f"INSIDER_{key}"
        if hasattr(django_settings, setting_name):
            cfg[key] = getattr(django_settings, setting_name)

    return cfg



def _validate_and_normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enforce types and normalize certain fields.
    Returns a cleaned copy of config.
    """

    cleaned: Dict[str, Any] = {}

    # IGNORE_PATHS: List of strings
    ignore_paths = raw.get("IGNORE_PATHS", DEFAULTS["IGNORE_PATHS"])
    
    if ignore_paths is None:
        ignore_paths = DEFAULTS["IGNORE_PATHS"]

    if isinstance(ignore_paths, (str, bytes)):
        # allow a comma-separated string
        ignore_paths = [p.strip() for p in str(ignore_paths).split(",") if p.strip()]
        
    elif not isinstance(ignore_paths, (list, tuple)):
        raise TypeError("INSIDER['IGNORE_PATHS'] must be a list of strings.")
    
    cleaned["IGNORE_PATHS"] = [str(p) for p in ignore_paths]


    # Booleans
    for key in (
        "IGNORE_ADMIN", "CAPTURE_RESPONSE", "CAPTURE_REQUEST_BODY", 
        "CAPTURE_USER", "CAPTURE_IP", "CAPTURE_USER_AGENT"
    ):
        val = raw.get(key, DEFAULTS[key])
        cleaned[key] = bool(val)


    # SLOW_REQUEST_THRESHOLD: None or non-negative int
    srt = raw.get("SLOW_REQUEST_THRESHOLD", DEFAULTS["SLOW_REQUEST_THRESHOLD"])
    if srt is None:
        cleaned["SLOW_REQUEST_THRESHOLD"] = None
    else:
        try:
            srt_i = int(srt)
        except Exception:
            raise TypeError("INSIDER['SLOW_REQUEST_THRESHOLD'] must be an integer (milliseconds) or None.")
        if srt_i < 0:
            raise ValueError("INSIDER['SLOW_REQUEST_THRESHOLD'] must be >= 0 or None.")
        cleaned["SLOW_REQUEST_THRESHOLD"] = srt_i


    # MAX_RESPONSE_LENGTH: positive int
    mrl = raw.get("MAX_RESPONSE_LENGTH", DEFAULTS["MAX_RESPONSE_LENGTH"])

    if mrl is None:
        cleaned["MAX_RESPONSE_LENGTH"] = None
    else:
        try:
            mrl_i = int(mrl)
        except Exception:
            raise TypeError("INSIDER['MAX_RESPONSE_LENGTH'] must be an integer or None.")
        if mrl_i < 1:
            raise ValueError("INSIDER['MAX_RESPONSE_LENGTH'] must be >= 1.")
        cleaned["MAX_RESPONSE_LENGTH"] = mrl_i


    # MASK_FIELDS: list of strings
    mask = raw.get("MASK_FIELDS", DEFAULTS["MASK_FIELDS"])
    if isinstance(mask, str):
        mask = [s.strip() for s in mask.split(",") if s.strip()]
    if not isinstance(mask, (list, tuple)):
        raise TypeError("INSIDER['MASK_FIELDS'] must be a list of strings.")
    cleaned["MASK_FIELDS"] = [str(x) for x in mask]


    # PUBLISHERS & NOTIFIERS: list of strings
    for key in ["PUBLISHERS", "NOTIFIERS"]:
        val = raw.get(key, DEFAULTS[key])
        
        if isinstance(val, str):
            val = [s.strip() for s in val.split(",") if s.strip()]
            
        if not isinstance(val, (list, tuple)):
             raise TypeError(f"INSIDER['{key}'] must be a list of strings.")
        
        # Normalize to lowercase strings to prevent mismatch in registry
        cleaned[key] = [str(v).lower() for v in val]


    # DB_ALIAS: string
    cleaned["DB_ALIAS"] = str(raw.get("DB_ALIAS", DEFAULTS["DB_ALIAS"]) or DEFAULTS["DB_ALIAS"])


    # LOG_LEVEL
    cleaned["LOG_LEVEL"] = str(raw.get("LOG_LEVEL", DEFAULTS["LOG_LEVEL"])).upper()


    # EXCLUDE_CONTENT_TYPES
    ect = raw.get("EXCLUDE_CONTENT_TYPES", DEFAULTS["EXCLUDE_CONTENT_TYPES"])
    if isinstance(ect, str):
        ect = [s.strip() for s in ect.split(",") if s.strip()]
    if not isinstance(ect, (list, tuple)):
        raise TypeError("INSIDER['EXCLUDE_CONTENT_TYPES'] must be a list of strings.")
    cleaned["EXCLUDE_CONTENT_TYPES"] = [str(x) for x in ect]


    # CAPTURE_METHOD
    valid_methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}
    raw_methods = raw.get("CAPTURE_METHODS", DEFAULTS["CAPTURE_METHODS"])

    if not isinstance(raw_methods, (list, tuple)):
        raise TypeError("INSIDER['CAPTURE_METHODS'] must be a list of methods.")

    cleaned_methods = []
    for m in raw_methods:
        if not isinstance(m, str):
            raise TypeError("Every item in INSIDER['CAPTURE_METHODS'] must be a string.")
        
        upper = m.upper()
        
        if upper not in valid_methods:
            raise ValueError(f"Invalid HTTP method in CAPTURE_METHODS: {m}")
        cleaned_methods.append(upper)

    cleaned["CAPTURE_METHODS"] = cleaned_methods


    # store full raw data for debugging.
    cleaned["_raw"] = raw.copy()

    return cleaned



def _build_settings() -> InsiderSettings:
    """
    This is the setting singleton to be used by the package.
    """

    raw = _load_user_config()
    cleaned = _validate_and_normalize(raw)
    inst = InsiderSettings(**{k: cleaned.get(k, DEFAULTS[k]) for k in DEFAULTS.keys()})
    inst._raw = raw.copy()
    return inst


# Build on import so other modules can simply import.
# This is safe because django_settings may be present in runtime; if not, defaults are used.
try:
    settings = _build_settings()
except Exception as exc:
    warnings.warn(f"Failed to build INSIDER settings, using defaults. Error: {exc}")
    settings = InsiderSettings()
    settings._raw = {}


def reload_settings() -> None:
    """
    Re-read Django settings and update the package settings object.

    Useful for tests or dynamic environments where settings change at runtime.
    """

    global settings
    try:
        settings = _build_settings()
    except Exception as exc:
        warnings.warn(f"Failed to reload INSIDER settings: {exc}")


def get(key: str, default: Any = None) -> Any:
    """
    Convenience accessor: insider.settings.get("MAX_RESPONSE_LENGTH")
    """
    return getattr(settings, key, settings._raw.get(key, default))


def should_ignore_path(path: str) -> bool:
    """
    Validation helper for middleware to check if path should be ignored
    """
    
    if not path:
        return False
    
    # Normalize leading slash
    if not path.startswith("/"):
        path = "/" + path

    # Check user-defined ignore paths and ensure they also normalize
    for prefix in settings.IGNORE_PATHS:
        if not prefix.startswith("/"):
            prefix = "/" + prefix

        if path.startswith(prefix):
            return True
            
    if settings.IGNORE_ADMIN and path.startswith("/admin/"):
        return True


    return False


__all__ = ["settings", "get", "reload_settings", "should_ignore_path", "InsiderSettings"]
