# CLAUDE.md — uml_planterator

Standards and practices for this codebase. Read before making any change.

---

## Project Overview

**uml_planterator** is a standards-first Python library that programmatically generates PlantUML diagrams (class, package, sequence, activity, state, component, use-case) by parsing multi-language source code. It uses a plugin adapter architecture so new language parsers can be registered without modifying the core.

Key modules:
- `src/uml_planterator/models.py` — immutable dataclass domain models
- `src/uml_planterator/adapters/base.py` — Adapter ABC
- `src/uml_planterator/registry.py` — Singleton registry + Factory
- `src/uml_planterator/parsers.py` — pure AST parsing helpers
- `src/uml_planterator/renderers.py` — pure PlantUML string generators
- `src/uml_planterator/generator.py` — orchestrator (`PUMLGenerator`)
- `src/uml_planterator/complexity.py` — cyclomatic complexity
- `src/uml_planterator/utils.py` — shared pure utilities
- `src/uml_planterator/io.py` — file I/O boundary
- `src/uml_planterator/lsp/jdtls_client.py` — JDT LS LSP client

---

## Toolchain

| Tool | Purpose | Config |
|---|---|---|
| Python 3.11–3.13 | Runtime | `pyproject.toml` |
| Poetry | Dependency management | `pyproject.toml` |
| pytest + pytest-cov | Testing | `pyproject.toml [tool.pytest.ini_options]` |
| ruff | Lint + format | `pyproject.toml [tool.ruff]` |
| mypy | Static type checking | `pyproject.toml [tool.mypy]` |
| black | Code formatting | `pyproject.toml` |
| pre-commit | Hook runner | `.pre-commit-config.yaml` |

### Essential commands

```bash
poetry install
poetry run pytest                       # full suite
poetry run pytest --cov=src --cov-branch --cov-report=term-missing --cov-fail-under=100
poetry run ruff check src tests
poetry run ruff format src tests
poetry run mypy src
pre-commit run --all-files              # run all hooks on every file
```

---

## Pre-commit Hooks

Pre-commit runs automatically on every `git commit`. Hooks execute in their own isolated environments managed by pre-commit — **do not invoke black or ruff directly from the project venv to replicate hook behaviour**; always use `pre-commit run`.

### Configured hooks (`.pre-commit-config.yaml`)

| Hook | Tool | Version | What it does |
|---|---|---|---|
| `black` | psf/black | 26.5.1 | Formats Python source to 88-char line length |
| `ruff` | charliermarsh/ruff-pre-commit | v0.15.14 | Lints and auto-fixes E/F/W/I/UP violations (`--fix`) |
| `isort` | pre-commit/mirrors-isort | v5.10.1 | Sorts imports with black-compatible profile |
| `end-of-file-fixer` | pre-commit/pre-commit-hooks | v6.0.0 | Ensures every file ends with a single newline |
| `trailing-whitespace` | pre-commit/pre-commit-hooks | v6.0.0 | Strips trailing whitespace |
| `check-yaml` | pre-commit/pre-commit-hooks | v6.0.0 | Validates YAML syntax |

### Installation

```powershell
pre-commit install          # installs the git hook — run once after cloning
pre-commit install --hook-type commit-msg   # optional: enforce commit message format
```

### Running hooks manually

```powershell
pre-commit run --all-files          # apply all hooks to every tracked file
pre-commit run black --all-files    # run a single hook by id
pre-commit run ruff --all-files
pre-commit autoupdate               # bump hook revisions to latest tags
```

### Safe commit workflow

Hooks auto-fix files, which creates a conflict when staged and unstaged changes coexist in the same file (`MM` status). Always follow this sequence:

```powershell
# 1. Edit files
# 2. Stage your changes
git add src/... tests/...

# 3. Check for split-staged files — any MM or RM entries are a problem
git status --short

# 4. If MM/RM entries exist, apply fixes first
pre-commit run --all-files

# 5. Re-stage the formatter fixes
git add src/... tests/...   # only the files that were just modified

# 6. Commit — hooks now run cleanly (no unstaged changes to conflict with)
git commit -m "type(scope): summary"
```

### Why MM causes hook failures

Pre-commit stashes unstaged changes before running hooks so it only lints what will actually be committed. When hooks auto-fix staged files and pre-commit tries to pop the stash, Git detects a conflict, rolls back all hook fixes, and aborts the commit. The root cause is always a file appearing in both the index and the working tree with different content.

### Hook failure meanings

| Exit code | Meaning | Action |
|---|---|---|
| Files modified by hook | Hook auto-fixed violations | Re-stage the modified files and retry |
| Hook reports errors (no fix) | Violations that require manual edits | Fix the reported lines, stage, retry |
| `check-yaml` fails | Invalid YAML syntax | Fix the YAML file |

---

## Python Standards

### Language version and style
- Target **Python 3.11+**; use `match`, `tomllib`, `Self`, `ParamSpec`, `TypeVarTuple` freely.
- Line length: **88** (ruff/black default).
- Imports: `from __future__ import annotations` at the top of every module; use `ruff` `I` rules for ordering.
- Type annotations on all public functions and method signatures. Use `list[X]`, `dict[K, V]`, `X | Y` (not `Optional`, `List`, `Dict`, `Union`) for Python 3.10+ style.
- `dataclasses.dataclass` for pure data; `@dataclass(frozen=True)` for value objects that must be immutable.
- Prefer `pathlib.Path` over `os.path` everywhere.

### Naming conventions
- `snake_case` for functions, variables, modules.
- `PascalCase` for classes.
- `UPPER_SNAKE_CASE` for module-level constants.
- Private helpers: single leading underscore `_`.
- Dunder methods only for protocol compliance; never invent custom ones.

### Error handling
- Raise concrete, typed exceptions (e.g., `AdapterError(RuntimeError)`) at system boundaries.
- Never silently swallow exceptions — log or re-raise.
- Validate only at true I/O boundaries (CLI args, file reads, network).
- Do not add `try/except` inside pure functions just for safety.

### Code quality rules (enforced by ruff)
- `E`, `F`, `W` — pycodestyle / pyflakes errors
- `I` — import order (isort)
- `UP` — pyupgrade (modern Python idioms)
- `E501` ignored — line length handled by black

---

## Object-Oriented Programming Principles

Apply these principles rigorously to every class and module.

### SOLID

| Principle | Rule |
|---|---|
| **S** — Single Responsibility | Each class/module has exactly one reason to change. `renderers.py` only renders; `parsers.py` only parses ASTs; `io.py` only writes files. |
| **O** — Open/Closed | Open for extension (new `Adapter` subclass), closed for modification (do not edit `base.py` to add language logic). |
| **L** — Liskov Substitution | Every `Adapter` subclass must honour the contract of `Adapter.parse_source` — never return `None`, raise `AdapterError` on failure. |
| **I** — Interface Segregation | Adapters expose only what the orchestrator needs: `language`, `supported_extensions()`, `parse_source()`. Optional methods (`parse_ast`, `compute_complexity`) have default implementations. |
| **D** — Dependency Inversion | `PUMLGenerator` depends on the `adapters_factory` callable, not concrete adapters. Tests inject stubs via this seam. |

### Additional OOP principles
- **DRY** — extract duplicate logic to `utils.py` or shared base methods, not copy-paste.
- **YAGNI** — only implement what a current test or feature requires.
- **Law of Demeter** — functions work with immediate collaborators, not their internal state.
- **Composition over Inheritance** — prefer injecting behaviour (strategy, factory) over deep class trees.
- **Encapsulation** — module internals prefixed `_`; public API is minimal and stable.

---

## Design Patterns

### Gang of Four (GoF) — 23 Canonical Patterns

Apply GoF patterns when they solve a demonstrated structural problem. Never introduce a pattern speculatively.

#### Creational
| Pattern | Where used / guidance |
|---|---|
| **Abstract Factory** | `AdapterRegistry` + `register_default_adapters()` form an Abstract Factory: the caller gets a family of language adapters without knowing concrete types. |
| **Factory Method** | `create_adapter(language, **kwargs)` in `registry.py` is a Factory Method that selects and instantiates the right `Adapter` subclass. |
| **Singleton** | `_INSTANCE = AdapterRegistry()` is the module-level singleton. Do not add more singletons; use dependency injection instead. |
| **Builder** | Use for constructing complex `ModuleInfo`/`ClassInfo` objects in tests when field count makes constructors unwieldy. |
| **Prototype** | Use `copy.deepcopy` when you need a modified copy of a `dataclass` model rather than mutating the original. |

#### Structural
| Pattern | Where used / guidance |
|---|---|
| **Adapter** | The entire `adapters/` sub-package is the Adapter pattern: each class wraps a language parser (javalang, libclang, regex) and exposes the uniform `Adapter` interface. |
| **Facade** | `PUMLGenerator.run()` is a Facade: it hides the orchestration of parse → filter → render → write behind a single call. |
| **Proxy** | `JDTLSClient` acts as a Proxy to the remote JDT Language Server; it handles protocol, lifecycle, and connection concerns transparently. |
| **Decorator** | Use Python function decorators (`@property`, `@abstractmethod`, `@staticmethod`) to add cross-cutting behaviour without changing the function signature. Avoid class-level Decorator chains — prefer composition. |
| **Composite** | `ModuleInfo` aggregates `ClassInfo` objects which aggregate `MethodInfo` and `AttributeInfo` — a natural composite tree. |
| **Bridge** | The adapter/renderer split is a Bridge: the abstraction (`PUMLGenerator`) is decoupled from the implementation (which renderer or adapter is used). |
| **Flyweight** | `utils.safe_id()` and the `_id_map` are a Flyweight cache: shared string identifiers are interned rather than re-computed per diagram. |

#### Behavioral
| Pattern | Where used / guidance |
|---|---|
| **Strategy** | Each `Adapter` subclass is an interchangeable parsing strategy. Swap the strategy by changing the registered adapter, not the orchestrator. |
| **Template Method** | `Adapter` base defines the parsing algorithm skeleton; subclasses fill in `parse_source` and optionally `parse_ast`/`compute_complexity`. |
| **Observer** | Future: emit parse/render events for progress reporting or plugin hooks. Use `typing.Protocol` for the listener contract. |
| **Command** | CLI flags (`--dry-run`, `--verbose`) encapsulate an action; consider wrapping them in a `RunConfig` dataclass (Command object). |
| **Iterator** | `adapter.supported_extensions()` and `_adapters_factory()` return iterables; callers always iterate, never index. |
| **Chain of Responsibility** | When multiple adapters might handle the same file extension, chain them: try each in priority order until one succeeds. |
| **Visitor** | AST walking in `parsers.py` is Visitor-style: `ast.walk` dispatches on node type. If complexity grows, formalise with `ast.NodeVisitor` subclasses. |
| **State** | `JDTLSClient` transitions through states (stopped → starting → running → stopped). Make state transitions explicit with an enum rather than boolean flags. |
| **Memento** | `utils.reset_id_map()` in `conftest.py` restores prior state — the fixture acts as a Memento restoring the map snapshot. |
| **Mediator** | `PUMLGenerator` mediates between adapters, parsers, renderers, and the I/O layer; none of these know about each other. |
| **Interpreter** | The PlantUML string builders in `renderers.py` are a simple Interpreter for the PlantUML DSL grammar. |

### GRASP Patterns (Larman)
- **Information Expert** — assign responsibility to the class that has the data. `ClassInfo` renders its own attribute visibility; `MethodInfo` knows its own complexity.
- **Controller** — `PUMLGenerator` is the system controller for the use-case "generate diagrams."
- **Creator** — `parsers.py` creates `ClassInfo` and `MethodInfo`; it owns all the data needed.
- **High Cohesion** — every module has a single, well-defined concern. Split if two concerns emerge.
- **Low Coupling** — modules communicate through `models` dataclasses, not by importing each other's internals.
- **Polymorphism** — dispatch on adapter type via `Adapter` ABC, never with `isinstance` chains.
- **Pure Fabrication** — `utils.py` and `complexity.py` are fabricated classes with no domain concept counterpart; they exist purely to achieve low coupling / high cohesion.
- **Indirection** — `adapters_factory` callable in `PUMLGenerator.__init__` introduces indirection so the generator never directly imports registry singletons.
- **Protected Variations** — the `Adapter` ABC shields the orchestrator from variations in language parsers.

### Enterprise Application Patterns (Fowler)
- **Repository** — the `io.py` module is the Repository boundary for file system writes.
- **Data Transfer Object (DTO)** — `models.ModuleInfo`, `ClassInfo`, etc. are DTOs: they carry parsed data across layer boundaries without behaviour.
- **Layer Supertype** — `Adapter` is the Layer Supertype for all language adapters.
- **Plugin** — new adapters are plugins; register via `AdapterRegistry.register()` without touching existing code.

---

## UML and PlantUML Standards

### UML 2.5 diagram types supported

| Type | Renderer function | PlantUML directive |
|---|---|---|
| Class | `gen_class_diagram` | `class`, `interface`, `abstract` |
| Package | `gen_package_diagram` | `package`, `component` |
| System Package | `gen_system_package_diagram` | `component` |
| Sequence | `gen_sequence_diagram` | `participant`, `->` |
| Activity | `gen_activity_diagram` | `start`, `stop`, `:action;` |
| State | `gen_state_diagram` | `state`, `[*]` |
| Component | `gen_component_diagram` | `component`, `[name]` |
| Use-Case | `gen_usecase_diagram` | `actor`, `usecase` |

### PlantUML conventions
- Every diagram file starts with `@startuml <diagram-id>` and ends with `@enduml`.
- Diagram IDs use kebab-case and must be unique within a generation run.
- Class diagrams use `"ClassName" as alias` with a `safe_id`-generated alias to avoid PlantUML reserved-word collisions.
- Visibility: `+` public, `-` private, `#` protected, `~` package-private.
- Abstract classes: `abstract class` keyword or `<<abstract>>` stereotype.
- Interfaces: `interface` keyword.
- Relationships: `--|>` inheritance, `..|>` realisation, `-->` dependency, `o--` aggregation, `*--` composition.
- Add `note` blocks only when a class docstring exists and is non-trivial.
- Output goes to `docs/UML/` mirroring the source tree structure under `Class/`, `Package/`, `Complexity/` sub-directories.

### UML modelling rules
- Follow UML 2.5 notation strictly; do not invent proprietary stereotypes.
- One diagram per class for class diagrams; one per directory for package diagrams.
- Generate complexity sub-diagrams only when cyclomatic complexity ≥ 10.
- State diagrams only when `ClassInfo.has_state` is `True`.

---

## Test-Driven Development

### TDD cycle
1. **Red** — write a failing test that specifies the new behaviour.
2. **Green** — write the minimum production code to pass the test.
3. **Refactor** — improve structure without changing behaviour; tests stay green.

Never write production code without a failing test first. Never skip a refactor step.

### Test structure

```
tests/
  conftest.py               # autouse fixtures (reset_id_map, etc.)
  unit/                     # fast, no I/O, all dependencies injected
    adapters/
      java/                 # Java-specific adapter tests
      test_core.py          # adapter ABC and shared contracts
    test_generator.py
    test_parsers.py
    test_renderers.py
    test_registry_*.py
    test_complexity*.py
    test_utils*.py
  integration/              # two or more real modules collaborating
    test_adapter_parse_failure.py
    test_generator_write.py
    test_registry_discovery.py
  functional/               # CLI flag behaviour, error paths
    test_cli_flags.py
    test_complexity_thresholds.py
    test_io_error_paths.py
  system/                   # require external services (JDT LS)
    test_java_jdtls_integration.py   # mark with @pytest.mark.system
```

### Pytest conventions
- **Fixtures** — define in `conftest.py` at the appropriate scope. Use `autouse=True` only for state-reset fixtures (like `_reset_safe_id_map`).
- **Parametrize** — use `@pytest.mark.parametrize` to cover input variations; do not copy-paste test functions.
- **Markers** — `system` tests require `@pytest.mark.system` and are excluded from the default run (`-m "not system"`).
- **Mocking** — use `unittest.mock.MagicMock` / `patch` only at I/O boundaries (`io.write_puml`, `JDTLSClient`). Never mock domain logic or pure functions.
- **Assertions** — use plain `assert`; never use `assertEqual`/`assertTrue` from `unittest`.
- **Coverage** — target is **100% line, branch, and path coverage** on `src/`. Use `# pragma: no cover` only for `__main__` guards and `raise NotImplementedError` stubs — never to hide untested logic. Every branch of every `if`, `try/except`, and conditional expression must have a test that exercises it.
- **Test isolation** — each test must be self-contained. No shared mutable state between tests. The `_reset_safe_id_map` autouse fixture enforces this for `utils`.
- **Naming** — `test_<function_or_class>_<scenario>`. Example: `test_parse_source_raises_adapter_error_on_invalid_java`.

### Testing pure functions
- Parsers, renderers, and utility functions are pure; test them with direct calls, no mocks.
- Use `tmp_path` (pytest built-in) for any test that needs real file system interaction.

### What to test
- Every public function and method.
- Every branch (if/else, try/except, early returns).
- Happy path + at least one failure path per function.
- Edge cases: empty inputs, `None` fields, max complexity values, reserved PlantUML keywords in identifiers.
- Adapter contract: every adapter must pass the shared contract tests in `tests/unit/adapters/test_core.py`.

---

## Software Security

### OWASP Top 10 (2021) — Applicable controls

| Risk | Control in this codebase |
|---|---|
| A01 Broken Access Control | Not applicable (no auth layer). Ensure file writes stay within `out_root`; validate that `out_root.resolve()` is a descendant of an expected base. |
| A03 Injection | Never pass source code strings to a shell. Use `subprocess` with list args only. Never use `eval()` or `exec()`. |
| A05 Security Misconfiguration | Do not commit secrets. `UML_PLANETATOR_JDTLS` path is env-var-only; never hard-code it. |
| A06 Vulnerable Components | Run `pip-audit` or `safety check` in CI. Track `.ai/.vulnerable_packages.txt`. |
| A08 Software and Data Integrity | Validate that parsed ASTs do not execute code. `ast.parse()` is safe; `compile()`+`exec()` are not. |
| A09 Security Logging | Log file paths and adapter names in verbose mode; never log source code content. |
| A10 SSRF | The JDT LS client connects only to `localhost`. Reject any host that is not loopback before opening a socket. |

### Secure coding rules
- **No shell injection** — `subprocess` calls must use `args: list[str]`, never `shell=True`.
- **Path traversal** — always call `.resolve()` and assert the result is within the expected root before writing.
- **Temporary files** — use `tempfile.NamedTemporaryFile` with `delete=True`; never leave tmp files on failure.
- **Encoding** — always specify `encoding="utf-8"` on file opens; use `errors="replace"` only for source reading where partial content is acceptable.
- **Dependency pinning** — keep `pyproject.toml` version ranges tight; avoid `*` or unbounded upper bounds for security-sensitive packages.
- **Secrets** — never read API keys or credentials from source files. Use env vars and document the variable name in README, not the value.

### SSDLC Gates

| Phase | Activity |
|---|---|
| Plan | Threat-model new external integrations (e.g., new LSP client). |
| Code | Pre-commit hook: ruff, mypy, bandit (add `bandit` to dev deps). |
| Test | pytest-cov gate ≥ 90%. Security-relevant paths have explicit tests. |
| Review | PR requires one approval. `code-review` skill run before merge. |
| Release | `pip-audit` clean. No known CVEs in transitive deps. |
| Monitor | Dependabot alerts on GitHub repo. |

---

## CI/CD and GitHub

### Branch strategy
- `main` — always deployable; protected branch.
- Feature branches: `feature/<short-description>`.
- Bug branches: `fix/<short-description>`.
- No direct commits to `main`; all changes via pull requests.

### Pull request rules
- Title: `<type>(<scope>): <summary>` (Conventional Commits). Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `ci`.
- Body: Summary + Test plan checklist.
- Required CI checks must all pass before merge.
- Keep PRs small: one logical change per PR.

### CI pipeline (GitHub Actions — target)

```yaml
# .github/workflows/ci.yml
jobs:
  quality:
    steps:
      - ruff check src tests
      - ruff format --check src tests
      - mypy src
      - bandit -r src -ll
  test:
    steps:
      - pytest --cov=src --cov-branch --cov-fail-under=100 -m "not system"
  audit:
    steps:
      - pip-audit
```

### Commit messages
Follow Conventional Commits 1.0.0:
```
<type>(<scope>): <imperative summary>

[optional body]

[optional footer: Co-Authored-By, Closes #N]
```

---

## Architecture Decisions

### Layering

```
CLI (generate_puml.py)
       ↓
  PUMLGenerator            ← orchestrator / facade
   ↓          ↓
parsers     renderers       ← pure functions
   ↓
adapters/base (Adapter ABC)
   ↓
concrete adapters (python, java, c, cpp)
   ↓
models (DTOs / dataclasses)
   ↓
io / utils / complexity     ← leaf helpers
```

Imports must only go **downward** in this stack. `renderers.py` must never import `parsers.py`; neither must import `generator.py`.

### Adapter contract (must be honoured by all implementations)
1. `language` — lowercase string identifier (e.g., `"python"`).
2. `supported_extensions()` — returns `list[str]` of dot-prefixed extensions (e.g., `[".py"]`).
3. `parse_source(path, source)` — pure, no side effects, raises `AdapterError` on failure, never returns `None`.
4. `parse_ast` and `compute_complexity` are optional overrides with defaults in the ABC.

### Models are DTOs
`models.py` dataclasses carry data across layers. They must not contain business logic, I/O, or rendering. Any computation belongs in `parsers.py`, `complexity.py`, or `renderers.py`.

### Pure functions
All functions in `parsers.py`, `renderers.py`, `utils.py`, and `complexity.py` must be pure (no side effects, deterministic output). This makes them trivially testable without mocks.

### I/O boundary
File reads happen in `PUMLGenerator._discover_and_parse()`. File writes happen in `io.write_puml()`. No other module performs file I/O. The `writer` seam on `PUMLGenerator` allows tests to inject a no-op writer.

---

## Code Review Checklist

Before marking a PR ready:

- [ ] Every new public function/method has a corresponding test (TDD red-green cycle completed).
- [ ] 100% line, branch, and path coverage (`pytest --cov=src --cov-branch --cov-fail-under=100`).
- [ ] No `isinstance` chains where polymorphism should be used.
- [ ] No new singletons; dependency injection used instead.
- [ ] All `subprocess` calls use list args, not `shell=True`.
- [ ] All file paths validated with `.resolve()` before writing.
- [ ] New adapters pass the shared adapter contract tests in `tests/unit/adapters/test_core.py`.
- [ ] PlantUML output validated: `@startuml` / `@enduml` balanced, no bare reserved words as identifiers.
- [ ] Ruff and mypy pass with zero errors.
- [ ] `pip-audit` clean.
- [ ] Commit messages follow Conventional Commits.

---

## Anti-patterns — Never Do These

- Do not add `print()` for debugging; use `logging`.
- Do not use `eval()`, `exec()`, or `compile()` on user-supplied source text.
- Do not `import *`.
- Do not add `try/except Exception: pass` — silent failures are bugs.
- Do not write tests that depend on filesystem state left by a prior test.
- Do not mock domain-layer classes in unit tests — only mock I/O and external services.
- Do not commit with `--no-verify`.
- Do not introduce a design pattern without a concrete, demonstrable need.
- Do not add `Optional[X]`; use `X | None` (Python 3.10+ union syntax).
- Do not return `None` from adapter `parse_source`; raise `AdapterError`.
- Do not hard-code paths; always derive from `Path(__file__).parents[N]` or env vars.
