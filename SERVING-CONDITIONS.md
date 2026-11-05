# Observed Serving Conditions

The following response conditions were verified with the production builds and
serving commands documented in the article. No campaign-specific application
caching, revalidation, incremental-regeneration, or compression rules were
added.

## HTML documents

### Angular SPA through `serve 14.2.6`

- Status: `200 OK`
- Validator: `ETag`
- Explicit `Cache-Control`: not present
- Negotiated compression: `Content-Encoding: br`
- `Vary: Accept-Encoding`

### Next.js SSR through `next start`

- Status: `200 OK`
- `Cache-Control: private, no-cache, no-store, max-age=0, must-revalidate`
- Negotiated compression: `Content-Encoding: gzip`
- `X-Powered-By: Next.js`
- `Vary` includes `Accept-Encoding` and Next.js router fields

## Versioned JavaScript resources

### Angular SPA through `serve`

- Validator: `ETag`
- Explicit `Cache-Control`: not present in the inspected response
- No `Content-Encoding` was returned for the inspected 880-byte file

### Next.js SSR through `next start`

- `Cache-Control: public, max-age=31536000, immutable`
- Validator: weak `ETag`
- No `Content-Encoding` was returned for the inspected 557-byte file

## Shared Spring Boot API

- Status: `200`
- `Cache-Control: no-cache, no-store, max-age=0, must-revalidate`
- `Pragma: no-cache`
- `Expires: 0`
- No `Content-Encoding` was observed for the inspected JSON response
- Security-related headers included `X-Content-Type-Options: nosniff` and
  `X-Frame-Options: DENY`

These headers are part of the evaluated serving stacks and must not be
interpreted as equivalent cache behavior. They were not custom-configured to
favor either treatment.

