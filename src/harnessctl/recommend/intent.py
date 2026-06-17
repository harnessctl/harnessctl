from dataclasses import dataclass
from typing import List, Set
from harnessctl.discovery.taxonomy import TaxonomyClient


@dataclass
class TaskIntent:
    complexity: int  # 0-100
    domains: Set[str]
    keywords: List[str]
    is_coding: bool = False
    prefers_speed: bool = False
    prefers_cheap: bool = False
    prefers_reasoning: bool = False


# Simple keyword mapping for intent detection (fallback/baseline)
DOMAIN_KEYWORDS = {
    "coding": [
        "python",
        "typescript",
        "javascript",
        "js",
        "ts",
        "py",
        "rust",
        "golang",
        "go-lang",
        "cpp",
        "c++",
        "c#",
        "csharp",
        "java",
        "code",
        "coding",
        "programming",
        "develop",
        "backend",
        "frontend",
    ],
    "reasoning": [
        "logic",
        "math",
        "reason",
        "think",
        "complex",
        "solve",
        "architecture",
    ],
    "creative": ["story", "write", "poem", "creative", "style", "novel"],
}

COMPLEXITY_TRIGGERS = {
    "microservice": 25,
    "architecture": 30,
    "auth": 20,
    "distributed": 30,
    "optimize": 15,
    "refactor": 15,
}


def analyze_intent(task: str, taxonomy_version: str = "latest") -> TaskIntent:
    task_lower = task.lower()
    words = set(task_lower.split())

    complexity = 10
    domains = set()

    # Calculate base complexity from basic triggers
    for trigger, weight in COMPLEXITY_TRIGGERS.items():
        if trigger in task_lower:
            complexity += weight

    # Try to enhance complexity via Taxonomy Registry (The Brain)
    try:
        tax_client = TaxonomyClient(version=taxonomy_version)
        tax_score = tax_client.get_intent_complexity(task)
        # If taxonomy found relevant matches, boost complexity
        if tax_score > 0:
            complexity += int(tax_score)
    except Exception:
        # Silently fallback to offline mode if network fails or version not found
        pass

    complexity = min(100, complexity)

    # Detect Domains
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in task_lower for kw in keywords):
            domains.add(domain)

    is_coding = "coding" in domains
    prefers_speed = any(
        kw in task_lower for kw in ["fast", "quick", "instant", "realtime", "speed"]
    )
    prefers_cheap = any(
        kw in task_lower
        for kw in ["cheap", "budget", "affordable", "free", "low-cost", "lowest"]
    )
    prefers_reasoning = "reasoning" in domains or any(
        kw in task_lower for kw in ["deep", "thought", "complex", "logic"]
    )

    return TaskIntent(
        complexity=complexity,
        domains=domains,
        keywords=list(words),
        is_coding=is_coding,
        prefers_speed=prefers_speed,
        prefers_cheap=prefers_cheap,
        prefers_reasoning=prefers_reasoning,
    )
