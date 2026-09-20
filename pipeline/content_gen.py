"""Generate bilingual narrative for a POI within a storyline via LLM.

The LLM self-rates each entry's confidence (no extra call). Malformed
output is tolerated; entries below the threshold are dropped.
"""
from __future__ import annotations

import json
import re
from typing import List, Tuple

from pipeline.models import NARRATIVE_TYPES, Narrative, meets_threshold

_SYSTEM = (
    "你是严谨的文旅内容编辑。只输出一个 JSON 数组,不要额外解释。"
    "数组每个元素含字段:type(scene/anecdote/masterpiece/history 之一)、"
    "text_zh、text_en、confidence(high/mid/low,依据史料/作品出处自评)、reason。"
    "Output ONLY a JSON array."
)


def build_narrative_prompt(storyline_theme: str, poi_name: str) -> Tuple[str, str]:
    """Build (system, user) prompts for narrative generation."""
    user = (
        f"故事线主题:{storyline_theme}\n地点:{poi_name}\n"
        f"请只围绕『{storyline_theme}』这条故事线,写该地点相关的剧情/轶事/名作/历史。"
        f"无可靠内容的类型就不要编,confidence 如实标注。"
    )
    return _SYSTEM, user


def _extract_json_array(raw: str) -> str:
    """Extract the first top-level JSON array substring from raw text."""
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    return match.group(0) if match else ""


def parse_narrative_response(raw: str) -> List[Narrative]:
    """Parse LLM output into Narrative list; skip malformed/unknown entries."""
    if not raw:
        return []
    payload = _extract_json_array(raw)
    if not payload:
        return []
    try:
        items = json.loads(payload)
    except (ValueError, TypeError):
        return []
    if not isinstance(items, list):
        return []
    out: List[Narrative] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        if it.get("type") not in NARRATIVE_TYPES:
            continue
        out.append(Narrative(
            type=it["type"], text_zh=it.get("text_zh", ""),
            text_en=it.get("text_en", ""), confidence=it.get("confidence", "low"),
        ))
    return out


def generate_narrative(client, storyline_theme: str, poi_name: str,
                       threshold: str = "mid") -> List[Narrative]:
    """Generate + parse + confidence-filter narrative for one POI in a storyline."""
    system, user = build_narrative_prompt(storyline_theme, poi_name)
    raw = client.complete(system, user)
    parsed = parse_narrative_response(raw)
    return [n for n in parsed if meets_threshold(n.confidence, threshold)]
