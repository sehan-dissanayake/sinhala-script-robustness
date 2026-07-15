class TransliterationCandidate:
    name: str  # human-readable, used in comparison table

    def transliterate(self, text: str) -> str:
        """Unicode Sinhala -> Romanized Sinhala. Must raise, not silently return empty string, on failure."""
        raise NotImplementedError
