from dataclasses import dataclass
from typing import List, Set


@dataclass
class TaskIntent:
    complexity: int  # 0-100
    domains: Set[str]
    keywords: List[str]
    is_coding: bool = False
    prefers_speed: bool = False
    prefers_cheap: bool = False
    prefers_reasoning: bool = False


# Simple keyword mapping for intent detection
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
        "kotlin",
        "swift",
        "php",
        "ruby",
        "rails",
        "sql",
        "html",
        "css",
        "tailwind",
        "react",
        "vue",
        "svelte",
        "docker",
        "kubernetes",
        "k8s",
        "yaml",
        "json",
        "script",
        "code",
        "coding",
        "programming",
        "develop",
        "microservice",
        "api",
        "backend",
        "frontend",
        "fullstack",
    ],
    "reasoning": [
        "logic",
        "math",
        "reason",
        "think",
        "complex",
        "solve",
        "architecture",
        "r1",
        "o1",
        "thought",
    ],
    "creative": ["story", "write", "poem", "creative", "style", "novel"],
}

COMPLEXITY_TRIGGERS = {
    "microservice": 25,
    "architecture": 30,
    "auth": 20,
    "cognito": 25,
    "distributed": 30,
    "optimize": 15,
    "refactor": 15,
    "create": 5,
    "write": 5,
}


def analyze_intent(task: str) -> TaskIntent:
    task_lower = task.lower()
    words = set(task_lower.split())

    complexity = 10
    domains = set()

    # Calculate Complexity
    for trigger, weight in COMPLEXITY_TRIGGERS.items():
        if trigger in task_lower:
            complexity += weight

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
