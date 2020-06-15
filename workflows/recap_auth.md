# Recap's OAuth Process

This is a brief description of the steps involved in authentication in Recap (`https://scsb.recaplib.org/`), and some information that has been helpful in past debugging

## Repos

There are two repos that house the relavant code:

* OAuth POC: https://bitbucket.org/NYPL/oauth-poc/src/master/oauth/authorize/index.php

This serves up the authorization form in https://bitbucket.org/NYPL/oauth-poc/src/master/oauth/authorize/template.php and implements most of the logic to process the resulting request.

* OAuth POC config available at https://bitbucket.org/NYPL/oauth-poc-config/src/development/ which configures which scopes are available to which users (clients)

* LDAP is an external dependency managed by IT.

## Authorization Process

* Selecting `New York Public Library` and submitting on the SCSB landing page redirects to the login page

* Upon hitting submit on the login page, Recap redirects to `isso.nypl.org/oauth/authorize` with `redirect_uri` pointing back to `scsb`, `client_id=htc_scsb`, and `scope=` set to relevant scopes. For example, this could be the full url:

```https://isso.nypl.org/oauth/authorize/?client_id=htc_scsb&redirect_uri=https://scsb.recaplib.org/login&response_type=code&scope=openid%20offline_access%20login:staff%20role:client%20read:item%20read:patron%20write:hold_request%20write:checkin_request%20write:checkout_request%20write:recall_request%20write:refile_request&state=agTuxo
```

* Scopes are implemented in `clients.yaml` in `oauth-poc-config`, which controls which apps can use isso

* The logic for handling the authorization request is implemented by OAuth POC available here: `https://bitbucket.org/NYPL/oauth-poc/src/master/oauth/authorize/index.php`. This involves the following steps:

  1. Recap submits the form to itself.

  2. The post request initiates LDAP negotiation. Info for LDAP negotiation is configured beginning in line 70 of `oauth/authorize/index.php` and read in line 83.

  3. OAuth POC then hits LDAP

  4. LDAP responds with user authorization, and OAuth redirects
