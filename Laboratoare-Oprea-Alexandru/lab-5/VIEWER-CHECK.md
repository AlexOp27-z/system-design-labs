# Generated contract — inspection record

**Date:** 2026-11-12  
**Document:** `openapi.json`, generated from `api.py` using `python generate_openapi.py`  
**Viewer:** Swagger UI 5.30.2, served locally with the generated JSON; Chromium browser.

## Viewer observations

- The document loaded as OpenAPI 3.1, API version 1.0.0, with all eight operations grouped under Market, Stocks, and Watchlist. No browser script errors occurred.
- Expanded `GET /v1/stocks`: exchange, sector, search, sort, limit, and cursor parameters appeared, including XNAS, symbol, and 20 defaults.
- Selected `filteredPage`: the example displayed the AAPL record, quote freshness fields, and continuation cursor.
- Selected `emptyList`: the example displayed `items: []` and `nextCursor: null`. Switching back restored the filtered result.
- The 400 response displayed the shared `error.code` / `error.message` shape and `invalid_input` code. Authentication, rate-limit, server, stub, and availability responses were also visible.
- The viewer visibly identifies the illustrative server and the unimplemented contract handlers. Examples are synthetic; this inspection did not call a live market service.
- The Mermaid ER diagram in `SOLUTION.md` also rendered successfully, including external ownership and relationship cardinalities.

## Reproducible contract checks

From this laboratory directory:

```sh
python -m pip install -r requirements.txt
python generate_openapi.py
python check_contract.py
```

Result: OpenAPI 3.1 specification validation passed; all 8 operations and 68 request/response examples passed schema checks. The checks also passed for deterministic regeneration, explicit null examples, authentication/CSRF stub boundaries, 24 query/path checks (valid stub inputs and invalid inputs), 6 invalid request-body cases, 26 positive/invalid monetary-schema cases, first-write Watchlist version consistency, and a bodyless DELETE 204 contract. Validation errors are documented as 400, with no unintended 422 responses. Mutation security requires both the session cookie and CSRF header.

A second check run used a fresh Python 3.12 virtual environment with only `requirements.txt` installed. The full check suite passed there as well. Swagger UI was rechecked after regenerating the corrected contract.

These are source/contract checks. Database operations, provider calls, cursor signing, rate limiting, and production identity/CSRF verification remain deliberately unimplemented stubs, as permitted by the assignment; the checks do not claim end-to-end business behavior.
