# Copilot Instructions for trycast

## Project Overview

**trycast** is a runtime type validation library that parses JSON-like values against Python type annotations (TypedDict, Union, Literal, etc.). Core API: `trycast()` returns value or None/failure, `checkcast()` raises ValidationError, `isassignable()` returns a TypeGuard-enhanced bool.

Single-file implementation in `trycast/__init__.py` (~1300 lines).

## Architecture & Design Patterns

### Version Compatibility Strategy

**Critical**: trycast supports Python 3.10-3.13 with extensive conditional imports:
- Use `sys.version_info >= (major, minor)` checks to conditionally import features
- Import from `typing_extensions` as fallback for older Python versions
- Example pattern (lines 43-50, 53-65, 67-77):
  ```python
  if sys.version_info >= (3, 13):
      from typing import _eval_type
      def eval_type(x, y, z):
          return _eval_type(x, y, z, type_params=())
  else:
      from typing import _eval_type as eval_type
  ```
- TypedDict compatibility: prefer `typing.TypedDict`, fallback to `typing_extensions.TypedDict`

### Debugging CPython typing.py Changes

**Intimate CPython dependency**: trycast uses private internals from Python's `typing.py` module (e.g., `_eval_type`, `_type_check`, `_TypedDictMeta`). When upgrading to a new Python version, these internals may change behavior or signatures, breaking existing logic.

**Debugging workflow for version-related breakage**:
1. Compare CPython source code between the new Python version and the last working version
2. Look at `Lib/typing.py` in CPython repo: https://github.com/python/cpython/blob/main/Lib/typing.py
3. Identify signature changes, renamed internals, or behavioral differences
4. Add version-specific conditional imports/wrappers (see `eval_type` pattern above)
5. Test thoroughly with `make testall` across all Python versions

### Type Validation Core

The validation logic uses a recursive pattern:
1. `trycast()`/`checkcast()` → `_checkcast_outer()` → `_checkcast_inner()`
2. `_checkcast_inner()` returns `None` on success, `ValidationError` on failure
3. Specialized handlers for each type kind: `_checkcast_listlike()`, `_checkcast_tuple()`, `_checkcast_typed_dict()`, etc.
4. Special numeric coercion: `bool`→`int`, `int`→`float`→`complex` (unlike isinstance())

### TypeChecker-Specific Ignores

Code contains extensive typechecker annotations:
- `# type: ignore[error-code]` for mypy
- `# pyre` for pyre  
- `# pyright` for pyright

When adding features, test against all typecheckers: `make typecheck` runs mypy, pyright, and pyre.

## Development Workflows

### Testing Commands (Makefile)
- `make test` - Run unittest against current Python version
- `make testall` - Run tox across Python 3.10-3.13 (uses venv3.10/, venv3.11/, etc.)
- `make typecheck` - Run all typecheckers (mypy, pyright, pyre)
- `make format` - Format with black + isort
- `make lint` - Check black/isort/flake8 compliance

### Test Organization
- `tests.py` - Main test suite (~3100 lines, unittest framework)
- `tests_shape_example.py` - Integration example from README
- `test_data/` - Forward reference test modules
- `benchmarks/` - **Informal** performance tests (run with `python -m timeit`)
  - No automated tracking or CI integration
  - No failure thresholds
  - Run ad-hoc when changes might cause performance regressions
  - Example: `python -m timeit -s 'from benchmarks import http_request_parsing_example__fail as b' 'b.run()'`

### Virtual Environments
Multiple venvs for each Python version: `venv3.10/`, `venv3.11/`, ..., `venv3.13/`. Use Poetry for dependency management.

## Critical Patterns

### Adding New Type Support
1. Add case in `_checkcast_inner()` checking `get_origin()` and/or `get_args()`
2. Create helper function (e.g., `_checkcast_newtype()`) following existing patterns
3. Return `None` for valid values, `ValidationError(tp, value)` for invalid
4. Add comprehensive tests in `tests.py`
5. Update README.md "Feature Reference" section
6. Test against all Python versions and typecheckers

### Error Handling
Three custom exceptions in API:
- `TypeNotSupportedError` - Type cannot be validated (e.g., TypeVars)
- `UnresolvedForwardRefError` - Forward reference cannot be resolved
- `UnresolvableTypeError` - String type reference cannot be evaluated
- `ValidationError` - Value doesn't match type (lazy message generation)

### Forward References
Special handling for string type annotations:
- `eval=True` parameter enables eval() to resolve strings
- Use `eval_type()` (compatibility-wrapped for Python 3.13's signature change)
- Check `ForwardRef` types and attempt resolution with module context

## Code Style

- Black formatter (line length 88)
- Isort for imports (Black-compatible profile)
- Flake8 linting (config in `.flake8`)
- Type annotations throughout, but implementation must work at runtime

## Publishing

`make publish` builds with Poetry and pushes to PyPI, then creates git tag from version in `pyproject.toml` (look for `# publish: version` comment).

## Getting Started

Activate the local venv using `source venv/bin/activate`. If `venv` directory missing then prefix commands with `poetry run ...`.
