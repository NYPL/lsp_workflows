# Encore and Research Catalog Log in and Log out

This workflow describes the different paths a patron can take to log in and out - and how we understand them to work.

All logging in routes through "Classic Catalog".

 * "Classic Catalog" (aka "Research Catalog):
   * Production: https://catalog.nypl.org
   * Test: https://nypl-sierra-test.iii.com/
 * "Encore" (aka "Catalog"):
   * Production: https://browse.nypl.org
   * Test: https://nypl-encore-test.iii.com

## Log in paths

There are several ways for a patron to log in:

1. Follow "Log In" > "Log [Into](https://english.stackexchange.com/questions/5302/log-in-to-or-log-into-or-login-to#5303) the Catalog"
1. Follow "Log In" > "Log Into the Research Catalog"
1. Follow "Login" in upper-right of Encore
1. Follow "Log In" in left-hand sidebar of Classic Catalog
1. Perform an action that requires authentication, thus bouncing through the login redirect (e.g. place a [hold-request in SCC](./patron_hold_request.md))

Although the redirect paths and end result differs for each of the above, the essential set of steps is as follows:

* Hit `login.nypl.org` with `redirect_uri` of destination page
* `Auth.nypl.org` bounces user to `catalog.nypl.org` where a login prompt is served
* Patron posts credentials to `catalog.nypl.org`
* If successful, `catalog.nypl.org` creates the `PAT_LOGGED_IN` cookie
* `Auth.nypl.org` bounces user to `login.nypl.org` where the `nyplIdentityPatron` cookie is created and user is finally redirected to the `redirect_uri` (which may itself issue its own redirects)

See [#a1-logging-in-via-log-into-the-catalog](#A1. Logging in via "Log Into the Catalog) and [#a2-logging-in-via-log-into-the-research-catalog](#A1. Logging in via "Log Into the Research Catalog) for a detailed script of the redirects that occur in those paths.

See [#a3-related-cookies](#A3. Related Cookies) for notes on the cookies involved.

### Special Considerations

~Logging in by following the "Research Catalog" login link is the only way to log in to that catalog; Logging in via Encore will not log you into the Classic Catalog. I do not know why.~ [TODO Confirm/correct this.]

Logging into the Test environment of either catalog will not log you into the Prod environment of that catalog - and vice versa.

## Log out

One can log out through a number of paths:

 * Header: Follow the Logout link under 'My Account'
 * Encore: Click `LOGOUT` button on the top right corner to log out. Once you click the button, it will log the user out from Encore and also Research Catalog. If the user has been logged in to Research Catalog Test, she will be logged out from there also.
 * Research Catalog: Use the `Log Out` link on the left side menu to log out. Once you click the link, it will log the user out from Research Catalog and Encore. If the user has been logged in to Research Catalog Test, she will be logged out from there also.

### Session Expiration

In Encore and Research Catalog, if a user has been inactive for more than 30 minutes, the log in session will be expired and the user will be logged out silently. On Encore, it will remain on the same page until the user tries to click any links on the page and then find out she is asked to log in again. On Research Catalog, she will be logged out and delivered to the main page of Research Catalog.

Neither Encore nor the Research Catalog are aware of the `nyplIdentityPatron` cookie, so that cookie will remain if session expiration forces the user to logout without explicity logging out through the logout URL used by all logout links (`https://login.nypl.org/logout?redirect_uri=...`). This dischord is mitigated by a recently added "JS Timer in Header".

### JS Timer in Header

The [Header Component](https://github.com/NYPL/dgx-header-component) includes [code](https://github.com/NYPL/dgx-header-component/blob/master/src/utils/encoreCatalogLogOutTimer.js) to assist session expiration by doing its damnedest to delete stale login cookies any time it appears a patron has not visited a catalog page in 30 or more minutes.

We observe that `PAT_LOGGED_IN` is created on `.nypl.org` any time a user logs in. `PAT_LOGGED_IN` is removed if 1) the user follows an explicit Logout link or 2) is forced to log out of a catalog by lingering on a catalog page for 30+ minutes. However, a user that logs in and then proceeds to visit exclusively non-catalog pages (or simply closes browser) will retain the `PAT_LOGGED_IN` cookie. The presense of a stale `PAT_LOGGED_IN` cookie confuses Sierra, sometimes causing it to request authorization to perform tasks that needn't require authorization (like search). (We'll refer to this category of bug as "login-to-search" hereafter.)

To ensure that `PAT_LOGGED_IN` is removed after 30mins of non-catalog activity, we drop a second cookie that represnts the last time the user visited a catalog page (a "valid domain").

`VALID_DOMAIN_LAST_VISITED` stores a UNIX timestamp in milliseconds indicating the last time the user visited a catalog page. It [is set to the current Unix timestamp](https://github.com/NYPL/dgx-header-component/blob/a652d44c416f1e677687e2e2044404f9a7ddf35c/src/utils/encoreCatalogLogOutTimer.js#L49) any time the user visits a catalog page* (because one's session is extended every time one visits a catalog page). On non-catalog pages, `VALID_DOMAIN_LAST_VISITED` is not typically* changed. On non-catalog pages, `VALID_DOMAIN_LAST_VISITED` is inspected to determine how much time has passed since the user visited a catalog page. A timer is thus initialized to forcefully log the user out when it completes.

When `VALID_DOMAIN_LAST_VISITED` indicates the visitor hasn't visited a catalog page in 30+ minutes, the Header Component [deletes](https://github.com/NYPL/dgx-header-component/blob/a652d44c416f1e677687e2e2044404f9a7ddf35c/src/utils/encoreCatalogLogOutTimer.js#L78-L80) `PAT_LOGGED_IN`, `VALID_DOMAIN_LAST_VISITED`, and `nyplIdentityPatron`. It also creates a hidden iframe that loads `https://browse.nypl.org/iii/encore/logoutFilterRedirect?suite=def` to ensure Encore (and by extension the Classic Catalog) fully terminate the user's session.

\* Note that `VALID_DOMAIN_LAST_VISITED` *may* be created on non-catalog pages in one case: The user appears to be logged in but does not have a `VALID_DOMAIN_LAST_VISITED` cookie. This can only** arise when the user logged in, but has not visited a catalog page (i.e. their login redirect did not land them on a catalog page). To ensure the `VALID_DOMAIN_LAST_VISITED` resembles as close to the actual login time as possible. For argument's sake, we could simplify this logic by removing the domain check entirely and simply set `VALID_DOMAIN_LAST_VISITED` immediately on *any* page the moment we notice `PAT_LOGGED_IN` exists without it. (i.e. doing so would effectively produce the same cookie value at the same time.

\** There are, in truth, many other reasons besides the one noted that explain how one may arrive on a page with a `PAT_LOGGED_IN` cookie but no `VALID_DOMAIN_LAST_VISITED`. Here are the ones I can think of, with the reason I don't care about them:
  * *User logged in, selectively deleted `VALID_DOMAIN_LAST_VISITED`*: In this case, they will effectively extend the logout timer by 30 minutes, which means they may encounter the catalog bug where they're asked to log in when performing tasks that needn't require a login. Selectively modifying cookies voids your warranty and only makes your experience a little worse for a short period.
  * *User does not have JS*: The logout timer running in the Header Component depends on JS, so if `VALID_DOMAIN_LAST_VISITED` isn't written because JS is disabled, there will likely be no JS enabled to run the logout timer based on it. `VALID_DOMAIN_LAST_VISITED` is set by JS and exists solely for use by that same JS code; If JS is disabled at the moment it would have been written, it is unlikely to be enabled at the moment it would be read. One contrived exception: If the user disables JS during the login process and enables it later on while on a non-catalog page, `VALID_DOMAIN_LAST_VISITED` will then be initialized to the full 30 minutes, leading to a forced logout in 30 minutes (unless they log out or visit a catalog page again). They may thus be vulnerable to the login-to-search bug for as much as 30 minutes. Without the logout timer in place, they would be vulnerable forever, so this edge case is not handled perfectly, but is an improvment on what would otherwise happen.
  * *User last visited a catalog page before we deployed the code that writes `VALID_DOMAIN_LAST_VISITED`*: Okay, that's real. We can't determine the age of `PAT_LOGGED_IN` (which is precisely what `VALID_DOMAIN_LAST_VISITED` is standing in to do). In this case, we'll optimistically initialize `LAST_DOMAIN_VISITED` to the current time, and the Header Component will log them out in 30 minutes. If they wander over to a catalog, they may encounter the login-to-search bug.

## Appendix

### A1. Logging in via "Log Into the Catalog"

* **Patron** follows "Log Into the Catalog" link in header, which goes to:
* `https://login.nypl.org/auth/login?redirect_uri=https://browse.nypl.org/iii/encore/myaccount`, which responds with `302` redirect to:
* `https://auth.nypl.org/authorize?response_type=code&client_id=app_myaccount&scope=openid+offline_access+patron%3Aread&redirect_uri=https%3A%2F%2Flogin.nypl.org%2Fauth%2Flogin&state=[snip]`, which responds with `302` redirect to:
* `https://catalog.nypl.org/iii/cas/login?service=http%3A%2F%2Fauth.nypl.org%2Fauthorize%3Fresponse_type%3Dcode%26client_id%3Dapp_myaccount%26scope%3Dopenid%2Boffline_access%2Bpatron%253Aread%26redirect_uri%3Dhttps%253A%252F%252Flogin.nypl.org%252Fauth%252Flogin%26state%3D[snip]`, which responds with **the login prompt**
* **Patron** `POST`s credentials to `https://catalog.nypl.org/iii/cas/login?service=http%3A%2F%2Fauth.nypl.org%2Fauthorize%3Fresponse_type%3Dcode%26client_id%3Dapp_myaccount%26scope%3Dopenid%2Boffline_access%2`
* If successful*, the Catalog **sets `PAT_LOGGED_IN` cookie** and responds with `302` redirect to:
* `http://auth.nypl.org/authorize?response_type=code&client_id=app_myaccount&scope=openid+offline_access+patron%3Aread&redirect_uri=https%3A%2F%2Flogin.nypl.org%2Fauth%2Flogin&state=[snip]%3D&ticket=[snip]`, which responds with `302` redirect to:
* `https://login.nypl.org/auth/login?code=[snip]&state=[snip]&ticket_used=[snip]-20&patron_id=[patronid]`, which **sets the `nyplIdentityPatron` cookie** and responds with a `302` redirect to:
* `https://browse.nypl.org/iii/encore/myaccount`, which responds with `302` redirect to:
* `https://catalog.nypl.org:443/iii/cas/login?service=https%3A%2F%2Fbrowse.nypl.org%3A443%2Fiii%2Fencore%2Fj_acegi_cas_security_check`, which responds with `302` redirect to:
* `https://browse.nypl.org:443/iii/encore/j_acegi_cas_security_check?ticket=[snip]`, which responds with a `302` redirect to:
* `https://browse.nypl.org/iii/encore/myaccount`, which responds with `302` redirect to:
* `https://browse.nypl.org/iii/encore/myaccount?lang=eng`, which responds with **My Account page** (showing "My Holds")

\* If patron login is unsuccessful, the Catalog immediately responds with a `200` and content for the login prompt including an error message.

### A2. Logging in via "Log Into the Research Catalog"

* **Patron** follows "Log Into the Research Catalog" link in header, which goes to:
* `https://login.nypl.org/auth/login?redirect_uri=https://catalog.nypl.org/patroninfo/top`, which responds with a `302` redirect to:
* `https://auth.nypl.org/authorize?response_type=code&client_id=app_myaccount&scope=openid+offline_access+patron%3Aread&redirect_uri=https%3A%2F%2Flogin.nypl.org%2Fauth%2Flogin&state=[snip]`, which responds with a `302` redirect to:
* `https://catalog.nypl.org/iii/cas/login?service=http%3A%2F%2Fauth.nypl.org%2Fauthorize%3Fresponse_type%3Dcode%26client_id%3Dapp_myaccount%26scope%3Dopenid%2Boffline_access%2Bpatron%253Aread%26redirect_uri%3Dhttps%253A%252F%252Flogin.nypl.org%252Fauth%252Flogin%26state%3D[snip]`, which responds with `200` and content for **the login prompt**
* **Patron** `POST`s credentials to `https://catalog.nypl.org/iii/cas/login?service=http%3A%2F%2Fauth.nypl.org%2Fauthorize%3Fresponse_type%3Dcode%26client_id%3Dapp_myaccount%26scope%3Dopenid%2Boffline_access%2Bpatron%253Aread%26redirect_uri%3Dhttps%253A%252F%252Flogin.nypl.org%252Fauth%252Flogin%26state%3D[snip]`
* If successful*, the Catalog **sets `PAT_LOGGED_IN` cookie** and responds with `302` redirect to:
* `http://auth.nypl.org/authorize?response_type=code&client_id=app_myaccount&scope=openid+offline_access+patron%3Aread&redirect_uri=https%3A%2F%2Flogin.nypl.org%2Fauth%2Flogin&state=[snip]&ticket=[snip]`, which responds with `302` redirect to:
* `https://login.nypl.org/auth/login?code=70d66230cfb1559651a333b417b4600b6111f367&state=[snip]&ticket_used=[snip]&patron_id=[patronid]`, which **sets the `nyplIdentityPatron` cookie** and responds with a `302` redirect to:
* `https://catalog.nypl.org/patroninfo/top`, which responds with a `302` redirect to:
* `/patroninfo~S1/[patronid]/items`, which responds with a `200` and the content for "My Account" (showing checked out items)

\* If patron login is unsuccessful, the Catalog immediately responds with a `200` and content for the login prompt including an error message.

### A3. Related Cookies

* `PAT_LOGGED_IN`: Session cookie on `.nypl.org` containing true/false. It will only assigned the moment the user logs in Encore or Research Catalog. It will be deleted when the user is logged out from either of the catalog. This cookie is for Encore and Research Catalog to know whether the user should be treated is logged in. I believe if the cookie exists but `JSESSIONID` is expired, the user will be asked to log in again.
* `JSESSIONID`: Session cookie on `browse.nypl.org` so it will only be accessed when on Encore. I believe this cookie is how Encore depends on to log the user out after the log in time is expired.
* `nyplIdentitityPatron`: This is the session cookie assigned by NYPL's OAuth log in service. It provides NYPL's Header to know if the user has been logged in, and based on that Header will display correct UI. For now, we have some issue to keep `nyplIdentitityPatron` synced with `PAT_LOGGED_IN` because when the session expired on Encore or Research Catalog, it won't necessary delete `nyplIdentitityPatron` at the same time.
* `VALID_DOMAIN_LAST_VISITED`: This cookie is set by 1) catalog pages and 2) any page used as `redirect_uri` in a login flow. It's a UNIX timestamp in milliseconds that stores the last time the user visited (or is assumed to have visited) a catalog page.
