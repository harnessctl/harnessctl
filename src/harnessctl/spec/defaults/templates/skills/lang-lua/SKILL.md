---
name: lang-lua
description: Lua development standards and tooling.
---

# LUA Standards

- **Style:** [Lua Style Guide](https://github.com/Olivine-Labs/lua-style-guide).
- **Tooling:** `StyLua`, `luacheck`, `busted`.
- **Scoping:** Use `local` for ALL variables and functions to avoid global namespace pollution.
- **Errors:** Return `nil, err_msg` for expected failures. Use `pcall`/`xpcall` for unexpected ones.
- **OOP:** Use Metatables and `__index` for object-oriented patterns.

Always load `clean-code` alongside this skill.
