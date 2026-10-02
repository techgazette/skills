# Walkthrough: deadline audit of a small Node API with a Python worker

The repository is `sample-repo/` in this folder. The vendor sources below are real
pages, read on 2026-10-01. Dates in them will age; rerun the audit rather than
reusing this output.

## Request

> What in sample-repo has an end-of-life or shutdown coming? Give me a checklist.

## Step 1: inventory

```bash
python3 ../scripts/list_deps.py sample-repo --format md --npm-deprecated
```

```text
| kind | ecosystem | name | spec | locked | where | npm deprecated |
| --- | --- | --- | --- | --- | --- | --- |
| runtime | node | node | 20 |  | .nvmrc:1 |  |
| package | npm | express | ^4.21.2 | 4.21.2 | package.json:6 |  |
| package | npm | request | ^2.88.2 | 2.88.2 | package.json:7 | request has been deprecated, see https://github.com/request/request/issues/3142 |
| runtime | npm-engines | node | >=20 |  | package.json:4 |  |
| ci-runner | github-actions | ubuntu-latest |  |  | .github/workflows/ci.yml:5 |  |
| ci-action | github-actions | actions/checkout | v4 |  | .github/workflows/ci.yml:7 |  |
| ci-action | github-actions | actions/setup-node | v4 |  | .github/workflows/ci.yml:8 |  |
| ci-action | github-actions | actions/upload-artifact | v3 |  | .github/workflows/ci.yml:12 |  |
| runtime | python | python | >=3.10 |  | worker/pyproject.toml:4 |  |
| package | pypi | httpx | >=0.27 |  | worker/pyproject.toml:6 |  |
```

## Steps 2 to 4: vendor sources consulted

| Item | Vendor page | What it says |
| --- | --- | --- |
| Node.js 20 | https://github.com/nodejs/Release (`schedule.json`) | `"v20": {"start": "2023-04-18", "lts": "2023-10-24", "maintenance": "2024-10-22", "end": "2026-04-30", "codename": "Iron"}` |
| Python 3.10 | https://devguide.python.org/versions/ | Table row: `3.10 PEP 619 end-of-life 2021-10-04 2026-10-01` |
| actions/upload-artifact v3 | https://github.blog/changelog/2024-04-16-deprecation-notice-v3-of-the-artifact-actions/ | "Starting January 30th, 2025, GitHub Actions customers will no longer be able to use v3 of actions/upload-artifact or actions/download-artifact." |
| request 2.88.2 | https://registry.npmjs.org/request/2.88.2 | `"deprecated": "request has been deprecated, see https://github.com/request/request/issues/3142"` |
| express 4.x | https://expressjs.com/en/support/ | Table row (Major Version, Minimum Node.js Version, Support Start Date, Support End Date): `v4.x \| 0.10.0 \| April 2014 \| ongoing` |

## Final checklist

```markdown
## Deprecation deadlines for sample-repo, as of 2026-10-01

### Already past
- [ ] actions/upload-artifact v3 (`.github/workflows/ci.yml:12`): v3 can no longer be used, from January 30th, 2025.
      Source: "Starting January 30th, 2025, GitHub Actions customers will no longer be able to use v3 of actions/upload-artifact or actions/download-artifact." https://github.blog/changelog/2024-04-16-deprecation-notice-v3-of-the-artifact-actions/
      Next step: "Customers should update workflows to begin using v4 of the artifact actions as soon as possible."
- [ ] Node.js 20 (`.nvmrc:1`, `package.json:4` allows `>=20`): end of life 2026-04-30.
      Source: `"end": "2026-04-30"` for v20 in schedule.json, https://github.com/nodejs/Release
      Next step: the same file lists v22 with `"end": "2027-04-30"`; raise `.nvmrc` and `engines.node`.
- [ ] Python 3.10 (`worker/pyproject.toml:4` allows `>=3.10`): end of life 2026-10-01, today.
      Source: "3.10 PEP 619 end-of-life 2021-10-04 2026-10-01" https://devguide.python.org/versions/
      Next step: raise `requires-python` to a supported version listed on the same page.
- [ ] request 2.88.2 (`package.json:7`): deprecated by its publisher (no date given).
      Source: npm registry flag "request has been deprecated, see https://github.com/request/request/issues/3142" https://registry.npmjs.org/request/2.88.2
      Next step: vendor names no replacement in the flag; the linked issue explains the deprecation.

### Within 90 days
- None found.

### Later
- None found.

### Checked, no announced date
- express 4.21.2: support end date "ongoing" for v4.x, https://expressjs.com/en/support/

### Not checked
- httpx, actions/checkout v4, actions/setup-node v4, ubuntu-latest runner: no lookup made in this pass.
```
