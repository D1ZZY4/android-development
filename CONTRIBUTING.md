
# Contributing

Skills are organized by domain. Each domain has its own directory under `skills/<domain>/`.

## How to propose changes

1. Identify which domain your change belongs to.
2. Keep changes scoped to that domain's files within `skills/<domain>/`.
3. Update both `AGENTS.md` and `REFERENCE.md` when changing commands or
   workflows for that domain.
4. Do not create cross-domain dependencies between skills.

## Required checks before submitting

Every pull request must pass all applicable checks before review:

```bash
# Shell script syntax check
find skills -name "*.sh" -exec bash -n {} \;

# Python syntax check
find skills -name "*.py" -exec python3 -m py_compile {} \;

# SELinux selftest
bash skills/selinux-repair/scripts/tests/selftest.sh
```

All must exit without errors.

## Safety constraints (non-negotiable review criteria)

See each skill's AGENTS.md for domain-specific safety rules. The following apply across all skills:

1. No mutating commands on a live device without explicit user confirmation.
2. Evidence-first diagnosis (debug and selinux-repair skills).
3. No broad or bypass SELinux policy shapes (selinux-repair skill).

## Versioning

Each skill is independently versioned via its git tag. Breaking changes to a skill's commands or workflow should be noted in the skill's README.md.
