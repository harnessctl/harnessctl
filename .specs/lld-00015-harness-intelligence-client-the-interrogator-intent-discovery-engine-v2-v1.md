---
status: draft
---

# LLD-00015: Harness Intelligence Client (The Interrogator)

## 1. Overview
The "Interrogator" is the client-side engine (initially integrated into `harnessctl`) that pulls the "Brain" from the Registry and uses it to perform high-precision intent classification.

## 2. Components

### 2.1 Registry Sync (`updater.py`)
- **Location**: `~/.local/share/harnessctl/intelligence/`
- **Protocol**: HTTP/HTTPS with ETag validation.
- **Frequency**: Checked daily or upon explicit `--refresh`.
- **Offline Logic**: Always falls back to the last successful sync. If no sync exists, uses a hardcoded "Emergency Lexicon" (Tier 0).

### 2.2 Extraction Engine (`engine.py`)
- **Trie Matching**: Uses `FlashText` or `Aho-Corasick` for O(n) keyword extraction. It matches multi-word phrases (e.g., "SAGA Pattern") in a single pass through the user's prompt.
- **Weighted Scoring**:
  - Each concept in the taxonomy has an associated category weight.
  - The Interrogator calculates a "Domain Vector" (e.g., `Coding: 0.85, Reasoning: 0.40`).

### 2.3 Semantic Resolver (`semantic.py`)
- **Optional**: For high-complexity tasks, it can cross-reference extracted keywords with a local "Similarity Matrix" (shipped with the registry) to find related concepts that weren't explicitly mentioned.

## 3. Integration with `harnessctl`
1. **Bootstrap**: On CLI start, check if Registry update is needed (background).
2. **Analysis**: 
   - User prompt: *"I need an orchestrator for a SAGA-based microservice."*
   - Interrogator matches: `orchestrator` (Architect), `SAGA` (Pattern/Coding), `microservice` (Infra/Coding).
   - Final Intent: `is_coding=True`, `complexity=85`, `prefers_architect=True`.
3. **Recommendation**: Passes the enriched `TaskIntent` to the Ranker.

## 4. Portability
The Interrogator is designed as a standalone Python package (`harness-intelligence-client`) that can be used by other tools in the future.
