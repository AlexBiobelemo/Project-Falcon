# Airport Simulator – Coding Standards & Best Practices
A brief guid on how i strictly guide the AI model

## 1. Language & Style
- Python 3.12+
- Strict PEP 8 compliance (use `ruff` or `black` with line length 88).
- Type hints required on all function parameters and return values.
- Maximum function length: 40 lines (excluding docstrings).
- All public classes/methods require complete Google-style docstrings.


## 2. Django-Specific Rules
- Views must be class-based where appropriate; function views only for simple HTMX endpoints.
- All data mutation occurs inside atomic transactions.
- Forms must use Django `forms` or `ModelForm` classes.
- Model signals (`post_save`, `pre_save`) may be used only for automatic logging or basic conflict flagging.
- Template partials must be placed in `simulation/templates/simulation/partials/`.


## 3. Project Structure Enforcement
- Models: `core/models.py` only
- Simulation logic: `simulation/services.py` (AirportSimulator class)
- Views: `simulation/views.py`
- URLs: `simulation/urls.py`
- Commands: `simulation/management/commands/`
- No business logic in models or views.


## 4. Testing & Quality
- Every phase must include at least unit tests for new functionality.
- Simulation determinism: random.seed must be taken from `SimulationRun.config['seed']`.
- All database writes after SimPy advancement must use `bulk_update` where possible.

## 5. Naming & Documentation
- Model fields and variables use clear domain language (e.g., `scheduled_time`, `actual_time`, `delay_minutes`).
- Every major simulation step must generate an `EventLog` entry with timestamp, flight reference, and description.
- Comments must explain “why”, not “what”.

**Compliance Statement**: All generated code must be accompanied by the line: “# Rules compliance: PEP8, type hints, docstrings, atomic transactions verified.”