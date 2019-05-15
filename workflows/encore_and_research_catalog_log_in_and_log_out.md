# Encore and Research Catalog Log in and Log out

The workflow describes the different ways to log in and log out Encore and Research Catalog, which are the library's two main catalogs.

Encore - https://browse.nypl.org/iii/encore/myaccount?lang=eng
Encore Test - https://nypl-encore-test.iii.com/iii/encore/homepage?lang=eng&suite=def
Research Catalog - https://catalog.nypl.org
Research Catalog Test - https://nypl-sierra-test.nypl.org

Notice that Encore could also called Catalog on Header.

## Log in with Header
Visit NYPL's website and use `LOG IN` dropdown menu to choose either Encore or Research Catalog to log in. Notice on Header, Encore is called Catalog. Once the user has logged in one catalog, she will be logged in to another one automatically.

For logging in to both catalogs, NYPL applies OAuth 2's pattern to manage the task.

After click either of links to log in the catalogs, Header will link the user to NYPL's OAuth log in service and then redirect the user to each catalog's account page.

Here are the links,

Encore - https://login.nypl.org/auth/login?redirect_uri=https://browse.nypl.org/iii/encore/myaccount
Research Catalog - https://login.nypl.org/auth/login?redirect_uri=https://catalog.nypl.org/patroninfo/top

As visiting the account pages need the user to log in, the user will then be asked by https://catalog.nypl.org/iii/cas/login to enter the credentials. This link is the log in endpoint offered by III.

After the credentials are approved, the user will again be transferred back to NYPL's OAuth log in service's domain. At the final step, NYPL's OAuth log in service will assign the cookie "nyplIdentitityPatron", which provide the Header the way to determine if the user has been logged in to any of the catalogs. See the section of "Related Cookies" for more information. Then, based on the value of `redirect_uri` query, to be redirect to either Encore or Research Catalog.

## Log in with Log in Button
Visit the catalog's page and use the `LOGIN` button to log in.

After click the `LOGIN` button, Encore Prod and Research Catalog Prod both will transfer the user to NYPL's log in service just as logging in from Header. Although the steps are similar, the final redirect URLs are different as the users are already on the catalog, therefore, the last step is to redirect the user back to the page they were at before.

Since the log in domain belongs to Research Catalog, if the user log in to Research Catalog Prod, then she will be logged in to Encore as well. However, if she has logged in to Encore Prod first, she still needs to log in to Research Catalog.

For Encore Test, being logged in to Encore Prod won't log the user in to Encore Test. And vice versa.

For Research Catalog Test, being logged in to Catalog Prod won't log the user in to Research  Catalog Test. And vice versa.

## Log out with Header
Visit NYPL's website and open `MY ACCOUNT` dropdown menu (it was `LOG IN` before logging in to any catalogs) and then click `LOG OUT`. It will then log the user out from both of the catalogs. If the user has been logged in to Research Catalog Test, she will be logged out from there also.

The endpoint of `LOG OUT` button is as below,
https://login.nypl.org/auth/logout?redirect_uri=https://browse.nypl.org/iii/encore/myaccount?lang=eng

We still use OAuth 2's mechanism to log the users out. After hitting the endpoint of NYPL's log in service, it will then redirect the user to the log out endpoint of Encore.
https://browse.nypl.org/iii/encore/logoutFilterRedirect

As Encore and Research Catalog share the same patron service, Encore will then redirect the user to Research Catalog's log out endpoint,
https://catalog.nypl.org/iii/cas/logout?service=https%3A%2F%2Fbrowse.nypl.org%3A443%2Fiii%2Fencore%2Fj_acegi_cas_security_check&url=https://browse.nypl.org/iii/encore

Finally, it will send the user back to Encore's main page (no matter which page the user was before) and delete the cookie "nyplIdentitityPatron".

## Log out with Log out Button
On Encore, click `LOGOUT` button on the top right corner to log out. Once you click the button, it will log the user out from Encore and also Research Catalog. If the user has been logged in to Research Catalog Test, she will be logged out from there also.

On Research Catalog, use the `Log Out` link on the left side menu to log out. Once you click the link, it will log the user out from Research Catalog and Encore. If the user has been logged in to Research Catalog Test, she will be logged out from there also.

With either way to log out, Encore Test's log in status won't be affected.

Both of the log out endpoints will call NYPL's OAuth log in service to log out the users, therefore it will go through similiar steps as logging out from Header and also land the users to Encore's main page in the end.

## Log out with Session Expired and JS Timer in Header

### Session Expired
On Encore and Research Catalog, if a user has been inactive for more than 30 minutes, the log in session will be expired and the user will be logged out silently. On Encore, it will remain on the same page until the user tries to click any links on the page and then find out she is asked to log in again. On Research Catalog, she will be logged out and delivered to the main page of Research Catalog.

More than that, as Header uses the cookie `nyplIdentityPatron` to determine the log in status display, being logged out when the session expired won't change the Header's log in status.

### JS Timer in Header

The Repo of [Header](https://github.com/NYPL/dgx-header-component)

The codes of time is located at `src/utils/encoreCatalogLogOutTimer.js`.

To improve the user experience, we are currently working on adding a timer to completely log out the users after 30 minutes if the user is not active on either Encore or Research Catalog (because they have to be logged out together). The timer will start a 30 minutes countdown once the user logged in. Every time the user reload the pages with `browse.nypl.org` (Encore's domain) or `catalog.nypl.org` (Research Catalog's domain) the timer will restart a new 30 minutes count down again.

After 30 minutes, the timer will delete three cookies, `PAT_LOGGED_IN`, which determines if the user has logged in, `nyplIdentityPatron`, which determines the Header's log in status, and `VALID_DOMAIN_LAST_VISITED`, which determines the last time the user reloads Encore or Research Catalog's domain. Then it will call a invisible iframe to load the URI of `LOGOUT` button so the user will be completely logged out.

There will be an edge case that the timer won't work. If the user has an open Encore page while she keeps working on Research Catalog, after 30 mins, even she is not logged out from Research Catalog, but because the session on Encore has been expired, she will be silently logged out from Encore. Thus, if she visits Encore again, she will be asked to log in again. And the same case will happen on Research Catalog as well, if she is working on Encore and has Research Catalog open.

## Related Cookies