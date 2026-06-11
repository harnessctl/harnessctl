---
name: lang-cpp
description: C/C++ development standards, Google C++ Style, and tooling.
---

# CPP Standards

- **Style:** [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html).
- **Tooling:** `clang-format`, `clang-tidy`, CMake (3.20+), GoogleTest / Catch2.
- **Modern C++:** Use C++20+ features. Prefer `auto` when type is obvious. Use `constexpr` and `const` by default.
- **Memory:** RAII everywhere. Smart pointers only (no raw `new`/`delete`).
- **Safety:** Compile with `-Wall -Wextra -Werror`. Use sanitizers (ASan, UBSan, TSan) in CI.

Always load `clean-code` alongside this skill.
