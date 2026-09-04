# Auth test scenarios

- valid IAM login creates HttpOnly session cookies;
- invalid password and blocked account do not create a session;
- missing IAM binding rejects an otherwise valid token;
- invalid/expired token, issuer, audience, algorithm or kid returns unauthorized/unavailable without fallback;
- refresh rotates the session; revoked/expired refresh clears it;
- logout is idempotent and clears local cookies;
- role changes and individual grant add/remove appear after token/session refresh;
- removal of an individual grant preserves the same permission when it is inherited from the role;
- unknown permissions are rejected;
- missing/invalid CSRF blocks state-changing calls;
- IAM outage fails closed;
- unit hierarchy and request/offer visibility remain enforced by Acom policies.
