# Walkthrough: Acme Payments changelog against a small shop backend

Acme Payments is a fictional vendor. The changelog is `acme-changelog.md` and the
repository is `sample-repo/`, both in this folder, so the run is reproducible.

## Request

> Here are Acme's release notes (acme-changelog.md). Does anything in there affect
> sample-repo?

## Step 2: helper output

Command, run from this folder:

```bash
python3 ../scripts/changelog_signals.py --changelog acme-changelog.md --repo sample-repo --format md
```

Output:

```text
Source: acme-changelog.md

- line 8 [deprecation] under "2026-09-15"
  > - The `charges.create()` parameter `source` is deprecated. Use `payment_method` instead. Requests that send `source` will be rejected after March 31, 2027.
  dates: March 31, 2027
  repo uses `charges.create`: src/billing.ts:6
  repo uses `source`: src/billing.ts:6
- line 9 [removal] under "2026-09-15"
  > - Webhook signature header `Acme-Signature-V1` will be removed on 2027-01-15. Verify with `Acme-Signature-V2`.
  dates: 2027-01-15
  repo uses `Acme-Signature-V1`: src/webhooks.ts:4
- line 13 [breaking] under "2026-08-02"
  > - Breaking: the `/v1/customers/search` endpoint now requires the `query` parameter.
  repo hits: none found for the identifiers on this line
- line 18 [no-longer] under "2026-06-10"
  > - The Node SDK no longer supports Node.js 18. Upgrade to Node.js 20 or later.
  repo hits: none found for the identifiers on this line
- line 19 [end-of-life] under "2026-06-10"
  > - The `/v1/legacy-tokens` endpoint is sunset and returns 410 since 2026-06-10.
  dates: 2026-06-10
  repo hits: none found for the identifiers on this line
```

## Steps 3 and 4: reading the candidates

- Line 8: `src/billing.ts:6` calls `acme.charges.create(...)` with `source: cardToken`.
  Confirmed use of the deprecated parameter.
- Line 9: `src/webhooks.ts:4` reads the `Acme-Signature-V1` header. Confirmed.
- Line 13: no call to `/v1/customers/search` anywhere in the repository. Ruled out.
- Line 18: the script found no identifier, so check runtime versions by hand.
  `package.json` declares `"engines": { "node": ">=20" }`, which already excludes
  Node.js 18. Ruled out, but a CI image or Dockerfile could still pin 18; the
  repository has neither.
- Line 19: no use of `/v1/legacy-tokens`. Ruled out.

## Final report

```markdown
## Acme Payments changelog impact for sample-repo
Source: acme-changelog.md (pasted text), read on 2026-10-01

### Affects this repository
1. Webhook signature header V1 is being removed
   - Vendor says: "Webhook signature header `Acme-Signature-V1` will be removed on 2027-01-15. Verify with `Acme-Signature-V2`." (section "2026-09-15")
   - Deadline: 2027-01-15
   - Where: `src/webhooks.ts:4`
   - Change: verify with `Acme-Signature-V2`
2. `source` parameter on `charges.create()` is deprecated
   - Vendor says: "The `charges.create()` parameter `source` is deprecated. Use `payment_method` instead. Requests that send `source` will be rejected after March 31, 2027." (section "2026-09-15")
   - Deadline: March 31, 2027 (2027-03-31)
   - Where: `src/billing.ts:6`
   - Change: use `payment_method`

### Check manually
- None.

### Does not affect this repository
- `/v1/customers/search` now requires `query`: endpoint not used.
- Node SDK drops Node.js 18: `engines.node` is already `>=20`.
- `/v1/legacy-tokens` sunset: endpoint not used.
```
