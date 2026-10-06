import re


def parse_docstring_param(docstring: str) -> dict[str, str]:
    """Extract parameter help messages from reST :param: directives."""
    return {
        name: ' '.join(help_text.strip().split())
        for name, help_text in re.findall(
            r':param (\w+):\s*(.*?)(?=\s*:(?:param|returns|raises)|\s*$)',
            docstring,
            re.DOTALL,
        )
    }
