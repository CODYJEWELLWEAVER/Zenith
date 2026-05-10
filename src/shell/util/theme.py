from dataclasses import dataclass


@dataclass
class ThemeColors:
    foreground: str
    foreground_alt: str
    background: str
    background_alt: str
    background_highlight: str
    highlight: str
    error: str
