_ESCAPE_MAP = (
    ("\\n", "\n"),  # def hello(): \\n print("Hello, World!") -> def hello(): \n print("Hello, World!")
    ("\\t", "\t"),
    ("\\r", "\r"),
    ("\\b", "\b"),
    ("\\f", "\f"),
)

_HTML_ENTITIES = (
    ("&lt;", "<"),
    ("&gt;", ">"),
    ("&amp;", "&"),
    ("&quot;", '"'),
    ("&apos;", "'"),
    ("&nbsp;", " "),
    ("&copy;", "©"),
    ("&reg;", "®"),
    ("&trade;", "™"),
) # <h1> hello </h1> -> &lt;h1&gt; hello &lt;/h1&gt;

def looks_like_escaped_source(text: str) -> bool:
    """True when the payload is one logical line stuffed with \\n sequences."""

    if "\\n" not in text:
        return False

    return text.count("\\n") <= 1

def normalize_source_text(text: str) -> str:
    """Turn double-escaped newlines into real newlines."""

    if not looks_like_escaped_source(text):
        return text

    normalized = text
    for escaped, raw in _ESCAPE_MAP:
        normalized = normalized.replace(escaped, raw)

    return normalized

def unescape_html_entities(text: str) -> str:
    """Undo HTML entities as some weaker models emit those instead of raw <, >, & etc."""

    if "&" not in text:
        return text

    normalized = text
    for entity, raw in _HTML_ENTITIES:
        normalized = normalized.replace(entity, raw)

    return normalized