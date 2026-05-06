"""
Personal advantage trait bank for daily grounding.

This module provides a deterministic rotation of strategic traits so each run
anchors on both external environment advantages (Canada fact pack) and internal
capability advantages (trait pack).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence


@dataclass(frozen=True)
class PersonalTrait:
    trait_id: str
    title: str
    descriptor: str
    leverage_prompt: str


PERSONAL_TRAITS: List[PersonalTrait] = [
    PersonalTrait(
        trait_id="T001",
        title="Systems thinker",
        descriptor="Models dependencies, not just tools.",
        leverage_prompt="Map key bottlenecks and sequence work to unlock compounding gains.",
    ),
    PersonalTrait(
        trait_id="T002",
        title="First-principles reasoning",
        descriptor="Breaks problems to fundamentals before choosing tactics.",
        leverage_prompt="Reduce decisions to core constraints and optimize from ground truth.",
    ),
    PersonalTrait(
        trait_id="T003",
        title="Pattern recognition across domains",
        descriptor="Connects signals across cyber, business, and power structures.",
        leverage_prompt="Transfer winning patterns between domains instead of starting from zero.",
    ),
    PersonalTrait(
        trait_id="T004",
        title="High ambiguity tolerance",
        descriptor="Acts without full clarity while preserving downside control.",
        leverage_prompt="Run fast experiments under uncertainty and update quickly from feedback.",
    ),
    PersonalTrait(
        trait_id="T005",
        title="Rapid learning curve",
        descriptor="Ramps quickly on new stacks and frameworks.",
        leverage_prompt="Convert unknown tooling into short learning loops with fast execution.",
    ),
    PersonalTrait(
        trait_id="T006",
        title="Leverage mindset",
        descriptor="Prefers automation, AI, and scalable systems over linear effort.",
        leverage_prompt="Build once, reuse many times, and compound output through systems.",
    ),
    PersonalTrait(
        trait_id="T007",
        title="Hybrid profile",
        descriptor="Combines technical, business, and sales awareness.",
        leverage_prompt="Translate technical work into business outcomes and market positioning.",
    ),
    PersonalTrait(
        trait_id="T008",
        title="Narrative control",
        descriptor="Positions self effectively in resumes, interviews, and opportunities.",
        leverage_prompt="Frame achievements in terms of strategic value and clear impact.",
    ),
    PersonalTrait(
        trait_id="T009",
        title="Direct, truth-oriented thinking",
        descriptor="Cuts through noise and focuses on reality.",
        leverage_prompt="Prioritize hard constraints and evidence over social friction or hype.",
    ),
    PersonalTrait(
        trait_id="T010",
        title="Independent orientation",
        descriptor="Not psychologically tied to one employment path.",
        leverage_prompt="Preserve optionality across job, freelance, and builder paths.",
    ),
    PersonalTrait(
        trait_id="T011",
        title="Strategic curiosity",
        descriptor="Questions systems, not just outcomes.",
        leverage_prompt="Interrogate incentives and architecture to find structural opportunities.",
    ),
    PersonalTrait(
        trait_id="T012",
        title="Adaptability",
        descriptor="Moves across tools, platforms, and environments.",
        leverage_prompt="Reconfigure quickly when context shifts without losing momentum.",
    ),
    PersonalTrait(
        trait_id="T013",
        title="Execution potential",
        descriptor="Can outpace peers when focused.",
        leverage_prompt="Concentrate on one high-leverage objective and ship relentlessly.",
    ),
    PersonalTrait(
        trait_id="T014",
        title="Resourcefulness",
        descriptor="Uses available tools to build quickly.",
        leverage_prompt="Exploit constraints creatively to deliver results with limited resources.",
    ),
    PersonalTrait(
        trait_id="T015",
        title="Risk awareness",
        descriptor="Understands trade-offs in systems and decisions.",
        leverage_prompt="Protect downside explicitly while advancing upside bets.",
    ),
    PersonalTrait(
        trait_id="T016",
        title="Long-term thinking",
        descriptor="Builds durable advantage over short-term optics.",
        leverage_prompt="Choose compounding moves that increase strategic freedom over years.",
    ),
]


def choose_daily_traits(day_of_year: int, count: int = 4) -> List[PersonalTrait]:
    """Select a rotating subset of traits for the day."""
    n_traits = len(PERSONAL_TRAITS)
    if n_traits == 0 or count <= 0:
        return []

    start = day_of_year % n_traits
    selected: List[PersonalTrait] = []
    for i in range(count):
        selected.append(PERSONAL_TRAITS[(start + i) % n_traits])
    return selected


def render_trait_pack(traits: Sequence[PersonalTrait]) -> str:
    """Render trait pack text to append to the LLM prompt."""
    lines = [
        "Personal strategic trait pack for today (ground your response in these):",
        "- Use at least 3 trait IDs from this pack.",
        "- Link each selected trait to one concrete action pattern.",
        "",
    ]
    for trait in traits:
        lines.extend(
            [
                f"{trait.trait_id} | {trait.title}",
                f"Descriptor: {trait.descriptor}",
                f"Leverage action: {trait.leverage_prompt}",
                "",
            ]
        )
    return "\n".join(lines).strip()


LIFE_ARC_CONTEXT: List[str] = [
    "Early life shaped by displacement, which developed an observer mindset.",
    "Built real-world cybersecurity experience across SOC, incident response, and enterprise systems.",
    "Evolved into systems-level thinking across telemetry, control loops, and attack paths.",
    "Expanded thinking into power structures, business leverage, and AI systems.",
    "Experienced work-environment misalignment and developed intolerance for limitation.",
    "Now at a divergence point with high capability and a risk of fragmentation.",
    "Current requirement is focused execution over exploration.",
]


CURRENT_OBJECTIVE: List[str] = [
    "Transition from capable thinker to focused operator.",
    "Build leverage through AI systems or high-value cybersecurity positioning.",
    "Anchor identity in control, clarity, discipline, and forward movement.",
    "Eliminate low-leverage distraction and prioritize compounding execution.",
]


def render_identity_context() -> str:
    """Render life-arc and objective context for message generation."""
    lines = [
        "Identity and trajectory context (use for personalization):",
        "",
        "Life arc:",
    ]
    lines.extend([f"- {item}" for item in LIFE_ARC_CONTEXT])
    lines.extend(
        [
            "",
            "Current objective:",
        ]
    )
    lines.extend([f"- {item}" for item in CURRENT_OBJECTIVE])
    return "\n".join(lines).strip()
