# Browser checks

These Selenium checks exercise the master-detail editor against a running
Plone site. They are skipped by the normal test suite unless `PLONE_URL` is set.

## Prerequisites

- A running Plone 6.2 site with `cs.megamenu` installed.
- Chrome and a compatible Selenium driver (Selenium Manager handles the driver).
- An admin account. The defaults are `admin` / `admin`; override them with
  `PLONE_USER` and `PLONE_PASSWORD`.

## Run

```shell
PLONE_URL=http://127.0.0.1:8080/Plone make test-browser
```

The content-browser test creates a uniquely named Document at the site root,
selects it through the content browser, checks the stored UID, then deletes the
link and verifies that the picker is gone and no severe browser errors were
logged.

To check an LRF edit form, install `plone.app.multilingual`, reapply the add-on
profile if necessary, and pass an LRF edit URL:

```shell
PLONE_URL=http://127.0.0.1:8080/Plone \
LRF_URL=http://127.0.0.1:8080/Plone/en/edit \
make test-browser
```
