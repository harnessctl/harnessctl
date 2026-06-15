---
status: done
---

# LLD-00014: Harness Intelligence Registry (The Brain)

## 1. Overview
The "Brain" is a standalone, data-only repository that serves as a centralized Knowledge Base (KB) for technical intent. It decouples the understanding of "what things mean" (e.g., *Liskov Substitution* → *Coding/Design Principle*) from the tools that use this information.

## 2. Data Structure
The registry consists of a hierarchical taxonomy stored in compressed formats for fast delivery.

### Taxonomy Schema (`taxonomy.json`)
```json
{
  "version": "1.0.0",
  "last_updated": "2026-06-15T12:00:00Z",
  "categories": {
    "coding": {
      "weight": 1.0,
      "concepts": {
        "solid": ["liskov", "dependency inversion", "single responsibility"],
        "patterns": ["saga", "circuit breaker", "singleton", "factory"],
        "languages": ["python", "rust", "mojo", "zig"]
      }
    },
    "reasoning": {
      "weight": 0.8,
      "concepts": {
        "logic": ["first-order", "propositional", "predicate"],
        "algorithms": ["dijkstra", "a*", "minimax"]
      }
    }
  }
}
```

## 3. Storage & Delivery
- **GitHub Pages / CDN**: The registry is served as static assets.
- **Formats**: 
  - `taxonomy.json`: Human-readable (for PRs).
  - `taxonomy.msgpack.zst`: Compressed binary (for production client consumption).
- **Automations**: 
  - A GitHub Action runs weekly to scrape fresh tags from StackOverflow and GitHub Trends.
  - Generates a "Diff" report to track how the technical landscape is evolving.

## 4. Maintenance
- Community-driven via Pull Requests to the `harness-intelligence-registry` repository.
- Validation scripts ensure no circular dependencies in the taxonomy.
