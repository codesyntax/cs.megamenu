# cs.megamenu

Documentation for cs.megamenu, an editable menu for Plone 6.2 Classic UI.

This project provides a Sphinx-based documentation environment for your Plone project, powered by the [Plone Sphinx Theme](https://github.com/plone/plone-sphinx-theme).
It's generated using the `documentation_starter` template from [Cookieplone](https://github.com/plone/cookieplone).


## Prerequisites

-   [uv](https://docs.astral.sh/uv/) is the recommended tool for managing Python versions and project dependencies.

To install uv, use the following command, or visit the [uv installation page](https://docs.astral.sh/uv/getting-started/installation/) for alternative methods.

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```


## Build documentation

To build the HTML documentation, issue the following command.

```shell
make html
```

To build the HTML documentation and view a live preview while editing your documentation, issue the following command.

```shell
make livehtml
```

To check for broken links in your documentation, issue the following command.

```shell
make linkcheckbroken
```

To check spelling, grammar, and style in your documentation, issue the following command.
You should pay attention to errors and warnings, and suggestions may get noisy.

```shell
make vale
```

To delete the `docs` build directory and Python virtual environment, and reinitialize Python virtual environment, issue the following command.
This is useful to force reinstall dependencies and purge cached files in Sphinx builds.

```shell
make init
```

For more `make` commands, issue the following command.

```shell
make help
```


## Customize the cs.megamenu documentation

This section provides how-to guidance to customize your documentation.

The file `docs/docs/conf.py` controls the configuration of your documentation.
It has extensive comments for each part, often with links to the authoritative documentation for extensions and configuration.

The following sections describe customization not addressed in `docs/conf.py`.


### Manage dependencies

You can configure which dependencies or requirements you want to use in your documentation using uv.
Requirements are stored in the `dev` dependency group in the `pyproject.toml` file.

To add a requirement, use the following command.

```shell
uv add --dev my-requirement
```

To remove a requirement, use the following command.

```shell
uv remove --dev my-requirement
```

See also uv's documentation [Development dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/#development-dependencies).

After installing a dependency, you might need to add it to your documentation's configuration file, `conf.py`, under the `extensions` key.


### Replace static files

You might want to replace the default static files, located in `docs/docs/_static`, `logo.svg` and `favicon.ico`.
The documentation home page also uses `menu.svg` as a menu illustration.
Plone Sphinx Theme is configured to use these files when rendering documentation to HTML.

If you rename `logo.svg`, you must update `conf.py`, under the `html_logo`, `ogp_image`, and `latex_logo` keys.


## GitHub Pages

The `.github/workflows/docs.yaml` workflow builds the Sphinx documentation and
publishes it to GitHub Pages on pushes to `main`. Pull requests build the
documentation without deploying it.

In the repository settings, enable GitHub Pages and select **GitHub Actions**
as the source. The workflow sets `DOCS_BASE_URL` from the Pages configuration,
so the Sphinx canonical URL, sitemap, and OpenGraph metadata use the deployed
site URL.

The repository also contains a `.readthedocs.yaml` for optional Read the Docs
builds.

## Credits and acknowledgements 🙏

Generated using [Cookieplone (2.0.2)](https://github.com/plone/cookieplone) and [cookieplone-templates (2e19702)](https://github.com/plone/cookieplone-templates/commit/2e19702a8c4c221b540f70eea38f6c2981329f5c) on 2026-10-17 09:34:24.128161. A special thanks to all contributors and supporters!
