# Acme Payments API changelog

> Fictional vendor used for this example. URLs point to example.com.

## 2026-09-15

- Added `refunds.list()` pagination with `starting_after`.
- The `charges.create()` parameter `source` is deprecated. Use `payment_method` instead. Requests that send `source` will be rejected after March 31, 2027.
- Webhook signature header `Acme-Signature-V1` will be removed on 2027-01-15. Verify with `Acme-Signature-V2`.

## 2026-08-02

- Breaking: the `/v1/customers/search` endpoint now requires the `query` parameter.
- Improved error messages for card declines.

## 2026-06-10

- The Node SDK no longer supports Node.js 18. Upgrade to Node.js 20 or later.
- The `/v1/legacy-tokens` endpoint is sunset and returns 410 since 2026-06-10.
