# DOGA

![DOGA](assets/DOGA.png)

**Probabilistic, goal-aware thinking layer for Hermes Agent.**

DOGA (Doğa Turkish for "nature") adds scenario simulation, Monte Carlo reasoning, and goal detection to LLM responses. It guides the model to think probabilistically before answering, without modifying core Hermes behavior.

---

## Features

- **Goal Detection**  Identifies whether the user needs Information, Understanding, or Action before responding
- **Scenario Generation**  Prompts the LLM to enumerate and weigh multiple interpretations
- **Monte Carlo Simulation**  Pure Python engine (10K–50K iterations) for quantitative probability analysis, using 0 LLM tokens
- **Thinking Panel**  `<world_model>` reasoning blocks are extracted and displayed as a structured `[DOGA: Thinking Process]` panel before the final response
- **Auto Depth**  Automatic complexity assessment per query — decides low/medium/high using pure Python string analysis (0 LLM tokens)
- **Configurable Depth**  5 levels (1 = lightweight goal check, 5 = full probabilistic reasoning with simulation tool guidance)
- **Memory Integration (optional)**  Remembers goal patterns across sessions via Mnemosyne (`pip install doga-hermes[memory]`)
- **De Bono Thinking Hats**  Structured parallel reasoning through Six Thinking Hats lens — depth-aware (White, Black, Yellow, Green, Red), optional, enabled by default

---

## Installation

Copy the `doga/` directory into your Hermes plugins folder:

```bash
cp -r doga ~/.hermes/plugins/doga
```

For goal memory persistence across sessions (optional):

```bash
pip install doga-hermes[memory]
```

No config changes needed — DOGA auto-detects Mnemosyne at runtime.

Then enable it in `~/.hermes/config.yaml`:

```yaml
plugins:
  enabled: [doga]

toolsets: [hermes-cli, doga]

doga:
  depth: 3
  show_simulation: true
  max_scenarios: 5
```

---

## Usage

### Slash Commands

| Command | Description |
|---------|-------------|
| `/doga on` | Enable DOGA |
| `/doga off` | Disable DOGA |
| `/doga status` | Show current settings |
| `/doga auto` | Automatic depth — decides low/medium/high per query (default) |
| `/doga manual low\|medium\|high` | Force a specific thinking level |
| `/doga depth <1-5>` | Set thinking depth (switches to manual mode) |
| `/doga hats on` | Enable De Bono parallel thinking hats (default) |
| `/doga hats off` | Disable De Bono hats (reverts to standard goal/scenario prompts) |
| `/doga show` | Show simulation panel |
| `/doga hide` | Hide simulation panel |
| `/doga memory on` | Enable goal memory (requires Mnemosyne) |
| `/doga memory off` | Disable goal memory |

### Simulate Tool

A `simulate` tool is registered in the `doga` toolset for Monte Carlo analysis. The LLM can call it when quantitative probability weighing is needed:

```json
{
  "scenarios": [
    {
      "name": "contract_valid",
      "variables": {"signature_authorized": 0.8, "no_duress": 0.95},
      "conditions": ["signature_authorized and no_duress"]
    }
  ],
  "n_iterations": 10000
}
```

Returns probability distribution, entropy, and uncertainty level.

---

## Roadmap

- **Phase 1 (done)** — Optional Mnemosyne memory for goal pattern persistence
- **Phase 2 (done)** — Automatic depth selection based on query complexity
- **De Bono Hats (done)** — Six Thinking Hats structured reasoning, optional, depth-aware
- **Phase 3** — Recursive reasoning with nested scenario simulation

---

## Architecture

DOGA uses three Hermes plugin hooks:

| Hook | Purpose |
|------|---------|
| `pre_llm_call` | Inject goal detection + scenario guidance into the prompt |
| `transform_llm_output` | Extract `<world_model>` blocks, format as thinking panel |
| `post_tool_call` | Log `simulate` tool usage |

No core Hermes files are modified  DOGA is a pure plugin.

---

## License

MIT
