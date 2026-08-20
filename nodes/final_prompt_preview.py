class VelvetViceLTXFinalPromptPreview:
    """Displays and forwards the exact prompt delivered to LTXDirector."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": (
                    "STRING",
                    {"forceInput": True},
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "preview"
    CATEGORY = "VELVET VICE/LTX"
    DESCRIPTION = (
        "Shows the fully validated final prompt after Ollama has been "
        "released, then passes the exact same text to LTXDirector."
    )

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def preview(self, prompt):
        if not isinstance(prompt, str):
            raise TypeError("The final LTX prompt must be a string.")

        word_count = len(prompt.split())
        character_count = len(prompt)
        stats = (
            f"{word_count} words | {character_count} characters | "
            "exact LTXDirector input"
        )
        print(
            "[VELVET VICE] Final prompt preview ready: "
            f"{word_count} words, {character_count} characters."
        )
        return {
            "ui": {
                "final_prompt": [prompt],
                "stats": [stats],
            },
            "result": (prompt,),
        }
