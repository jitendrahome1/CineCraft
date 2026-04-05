"""
Shared prompt builders for all AI providers.
Centralizes prompt logic so all providers generate consistent output.
"""
from typing import Optional


def build_cinematic_story_prompt(
    title: str,
    context: Optional[str] = None,
    language: str = "english",
    video_length: str = "short"
) -> str:
    """
    Build a cinematic YouTube-style storytelling prompt.
    Generates emotional, line-by-line narration like trending YouTube videos.

    Args:
        title: Story/video title (topic)
        context: Optional additional context from user
        language: 'english' or 'hindi'
        video_length: 'short' or 'long'
    """
    if language == "hindi":
        lang_label = "Hindi"
        style_example = '''STYLE EXAMPLE:

"एक छोटे से गांव में,
जहां हर सुबह नई उम्मीद लेकर आती थी,
वहीं रहता था अर्जुन।

वह साधारण था,
लेकिन उसके सपने बिल्कुल असाधारण थे...
सपने जो उसकी हकीकत से कहीं बड़े थे।

एक दिन, कुछ ऐसा हुआ...
जिसने उसकी पूरी ज़िन्दगी बदल दी।"'''
    else:
        lang_label = "English"
        style_example = '''STYLE EXAMPLE:

"In a small forgotten village,
where every morning brought a new hope,
there lived a boy named Arjun.

He was ordinary in every way,
but his dreams were anything but ordinary...
Dreams that were far bigger than his reality.

One day, something happened...
something that changed his entire life forever."'''

    context_block = ""
    if context:
        context_block = f"\n- additional_context: {context}"

    prompt = f"""You are a professional cinematic storyteller.

Your task is to generate a HIGH-QUALITY cinematic narration script for AI video creation.

---------------------------------------------------
INPUT:
- topic: {title}{context_block}
- language: {lang_label}
---------------------------------------------------

STORY STYLE REQUIREMENTS:

1. Write like a trending YouTube storytelling video.
2. Make it emotional, engaging, and immersive.
3. Write in SHORT PARAGRAPHS (2-3 lines each), NOT single-line format.
4. Use "..." for dramatic pauses within paragraphs.
5. Each paragraph should feel cinematic and visual.
6. Maintain smooth, continuous storytelling flow.

---------------------------------------------------
VISUAL INTELLIGENCE RULE (SMART, NOT STRICT)

- Maintain logical visual consistency
- Avoid random scene jumps
- Environment should feel natural to the story
- If story starts in a village, don't randomly jump to ocean unless story explains it

---------------------------------------------------
{style_example}

---------------------------------------------------
STRUCTURE:

- Hook (first 2 lines must grab attention)
- Character introduction
- Build curiosity
- Emotional or dramatic journey
- Strong ending

---------------------------------------------------
IMPORTANT RULES:

- Write in SHORT PARAGRAPHS (2-3 lines each)
- DO NOT write like an article or essay
- DO NOT write single-line format
- Keep it voice-friendly
- Make every paragraph visually meaningful
- Keep flow smooth and cinematic
- Make it similar to trending YouTube storytelling videos with emotional narration and cinematic pacing

---------------------------------------------------
OUTPUT FORMAT:

Return ONLY the story text.

No JSON
No explanation
No headings
No markdown

---------------------------------------------------

Now generate the story."""

    return prompt


def build_scene_breakdown_prompt(
    story: str,
    language: str = "english",
    video_length: str = "short",
    characters: Optional[list[dict]] = None
) -> str:
    """
    Build a scene breakdown prompt from an existing cinematic story.
    Splits story paragraphs into scenes (1 paragraph = 1 scene).

    Args:
        story: Full cinematic narration text
        language: 'english' or 'hindi'
        video_length: 'short' or 'long'
        characters: Optional list of character dicts for visual consistency
    """
    prompt = f"""You are a scene breakdown engine.

TASK: Split this story into scenes based on paragraphs.

---------------------------------------------------
STORY:
{story}
---------------------------------------------------

INSTRUCTIONS:

1. Split story into scenes based on paragraphs.
   - 1 paragraph = 1 scene
   - Do NOT split line-by-line

2. Each scene must include:
   - scene_number
   - narration (same paragraph text, unchanged)
   - emotion (emotional / happy / sad / dramatic)

3. Maintain story continuity
4. Do NOT add new story content
5. Keep narration unchanged — copy the exact paragraph text

---------------------------------------------------

OUTPUT FORMAT (STRICT JSON ONLY):

Return ONLY valid JSON, no other text:
{{
  "scenes": [
    {{
      "scene_number": 1,
      "narration": "",
      "emotion": ""
    }}
  ]
}}

IMPORTANT:
- Return ONLY JSON
- No markdown
- No explanation
- No extra text"""

    return prompt


def build_image_prompt_generation_prompt(
    narration: str,
    previous_narration: Optional[str] = None
) -> str:
    """
    Build a prompt to generate an accurate, story-matched image prompt
    for a single scene based on its narration and previous scene context.

    Args:
        narration: The narration text of the current scene
        previous_narration: Optional narration of the previous scene for continuity
    """
    previous_context = ""
    if previous_narration:
        previous_context = f"""
PREVIOUS SCENE NARRATION (for visual continuity):
{previous_narration}

"""

    return f"""You are an expert visual prompt engineer for AI image generation.

TASK: Generate ONE highly detailed image generation prompt that EXACTLY matches the scene narration below.

---------------------------------------------------
{previous_context}CURRENT SCENE NARRATION:
{narration}

---------------------------------------------------

RULES FOR THE VISUAL PROMPT:

1. ENVIRONMENT CONTROL:
   - The environment MUST match what the narration describes
   - If narration says "village", show a village — NOT mountains, oceans, or random landscapes
   - If narration says "room", show a room — NOT outdoor scenery
   - Stay faithful to the story setting

2. CHARACTER CONSISTENCY:
   - Describe characters based on what the narration implies
   - Maintain consistent appearance with previous scene if provided
   - Include age, clothing, expression matching the emotion

3. SHOT TYPE:
   - Choose an appropriate cinematic shot type (wide shot, close-up, medium shot, over-the-shoulder, etc.)
   - Match shot type to the emotional tone of the scene

4. LIGHTING & MOOD:
   - Lighting must match the emotion (warm for happy, dim for sad, dramatic for tense)
   - Include time of day if implied by narration

5. STYLE:
   - Cinematic, photorealistic, high quality
   - 16:9 aspect ratio composition
   - Film-like color grading

---------------------------------------------------

OUTPUT FORMAT (STRICT JSON ONLY):

Return ONLY valid JSON, no other text:
{{"visual_prompt": "A detailed, cinematic image prompt here..."}}

IMPORTANT:
- Return ONLY JSON
- No markdown
- No explanation
- No extra text
- The visual_prompt must be a single detailed paragraph"""


def build_character_extraction_prompt(story: str) -> str:
    """
    Build a character extraction prompt from a cinematic story.
    Extracts detailed character appearance for consistent image generation.

    Args:
        story: Full cinematic narration text
    """
    return f"""Extract all characters/people mentioned or implied in this cinematic narration.

STORY:
{story}

---------------------------------------------------

For each character provide DETAILED appearance for consistent AI image generation.

Each character must include:
1. name: Character name (infer from context if not explicitly named)
2. age: Age or age range
3. role: Their story role (protagonist, antagonist, mentor, narrator, etc.)
4. appearance: DETAILED physical appearance:
   - Face features, skin tone
   - Hair color, style, length
   - Build/posture
   - Distinguishing features (glasses, beard, scars, accessories)
5. clothing: Specific outfit with colors, style, materials
6. style_reference: Full cinematic description for image generation consistency
   (combine appearance + clothing into one visual description)
7. personality: Key traits (3-5 words)
8. metadata: age, gender, occupation, era

---------------------------------------------------

Return ONLY a valid JSON array:
[
  {{
    "name": "",
    "age": "",
    "role": "",
    "appearance": "",
    "clothing": "",
    "style_reference": "",
    "personality": "",
    "description": "",
    "metadata": {{"age": "", "gender": "", "occupation": "", "era": ""}}
  }}
]

STRICT: Return ONLY valid JSON, no other text."""


# === Aliases for backward compatibility ===

def build_documentary_story_prompt(
    title: str,
    context: Optional[str] = None,
    language: str = "english",
    video_length: str = "short"
) -> str:
    """Alias — routes to cinematic story prompt."""
    return build_cinematic_story_prompt(title, context, language, video_length)


def build_documentary_scene_prompt(
    story: str,
    language: str = "english",
    video_length: str = "short",
    characters: Optional[list[dict]] = None
) -> str:
    """Alias — routes to scene breakdown prompt."""
    return build_scene_breakdown_prompt(story, language, video_length, characters)


def build_documentary_character_prompt(story: str) -> str:
    """Alias — routes to character extraction prompt."""
    return build_character_extraction_prompt(story)
