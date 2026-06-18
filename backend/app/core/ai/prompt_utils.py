def escape_for_format(value: str) -> str:
    """Escape { and } in untrusted text so str.format() treats them as literals.

    Call this on every untrusted value (news text, company names, flag
    descriptions) before passing to a prompt template's .format() call.
    Without escaping, a value containing { or } raises KeyError or causes
    unintended placeholder substitution — this already caused a crash in
    production (commit 09fadfde).
    """
    return str(value).replace("{", "{{").replace("}", "}}")
