# Project Instructions

## Architecture & Conventions
- **Backend**: FastAPI with SQLAlchemy 2.0. Async session management is preferred where applicable.
- **Frontend**: React 19 with Vite. Use OKLCH colors and the custom design system in `frontend/src/components/ui/`.
- **Authentication**: JWT-based. `passlib` is used for password hashing.
- **Dependency Management**: Rigorously specify versions in `requirements.txt` to avoid library incompatibilities.

## Known Issues & Fixes
- **Bcrypt Compatibility**: Always use `bcrypt==3.2.0` with `passlib==1.7.4`. Newer versions of `bcrypt` (4.0+) break `passlib` due to the removal of `__about__` and changes in password length handling.

## Workflows
- **Verification**: Always run `verify_fix.py` (or a similar script) after modifying authentication or core business logic to ensure E2E functionality.
