// LLD-00015: Config Sample in Jsonnet
// This file demonstrates how to use Jsonnet for hierarchical, 
// DRY (Don't Repeat Yourself) agentic configurations.

// Base definition for all harnesses
local base_harness = {
  templates: ['generic-coding'],
  agents: ['coder-smart'],
  skills: ['lang-js', 'lang-ts'],
  mcp_servers: [],
  providers: [],
};

{
  version: '1.0',

  harnesses: {
    // OpenCode inherits from base and appends specific data
    opencode: base_harness {
      templates+: ['game-coding'],
      agents: ['coder-medium', 'coder-cheap'], // Overriding the agent list entirely
      skills+: ['lang-py', 'caveman', 'whatever'], // Appending to the inherited skills
      config_templates: ['templates/opencode.json.md'],
    },

    // Pi harness inherits from base
    pi: base_harness {
      tools: ['do-the-tonga-dance'],
      config_templates: ['templates/pi.json.md'],
    },

    // Example of a specialized future harness
    'mobile-edge': base_harness {
      templates: ['edge-optimized'],
      agents: ['nano-coder'],
      hardware_constraints: {
        max_tps: 10,
        power_profile: 'low',
      },
      providers+: [
        {
          name: 'ollama-local',
          endpoint: 'http://192.168.1.50:11434',
        },
      ],
    },
  },
}

/*
  Lead-Engineer Notes:
  1. Skill Discovery: 
     The 'config_templates' (Markdown files) will still contain Jinja-style tags:
     {% load_skill skills="lang-js,lang-ts" %}
     
  2. Jsonnet vs Jinja:
     - Use Jsonnet for generating 'opencode.json' or 'pi.json'.
     - Use Jinja2 for the text-heavy instructions inside '.md' templates.
     
  3. The '+' Operator:
     Note the use of 'templates+:' and 'skills+:'. 
     In Jsonnet, this automatically appends to the inherited array from 'base_harness'.
*/
