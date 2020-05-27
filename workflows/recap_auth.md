# Recap's OAuth Process

This is a brief description of the steps involved in authentication in Recap (`https://scsb.recaplib.org/`), and some information that has been helpful in past debugging

* Upon hitting submit on the login page, Recap redirects to `isso.nypl.org/oauth/authorize` with `redirect_uri` pointing back to `scsb`, `client_id=htc_scsb`, and `scope=` set to relevant scopes

* Scopes are implemented in `clients.yaml` in `oauth-poc-config`, which controls which apps can use isso

* Recap submits the form to itself, which then uses info for LDAP negotiation which is configured in line 70 of `oauth/authorize/index.php` and read in line 83.

* OAuth POC then hits LDAP. The url for ldap is configured in OAuth POC

* LDAP responds with user authorization, and OAuth redirects
