<div align="center">
    <h1 align="center">collective.editablemenu</h1>
</div>
<div align="center">
[![PyPI](https://img.shields.io/pypi/v/collective.editablemenu)](https://pypi.org/project/collective.editablemenu/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/collective.editablemenu)](https://pypi.org/project/collective.editablemenu/)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/collective.editablemenu)](https://pypi.org/project/collective.editablemenu/)
[![PyPI - License](https://img.shields.io/pypi/l/collective.editablemenu)](https://pypi.org/project/collective.editablemenu/)
[![PyPI - Status](https://img.shields.io/pypi/status/collective.editablemenu)](https://pypi.org/project/collective.editablemenu/)


[![PyPI - Plone Versions](https://img.shields.io/pypi/frameworkversions/plone/collective.editablemenu)](https://pypi.org/project/collective.editablemenu/)

[![CI](https://github.com/collective/collective.editablemenu/actions/workflows/main.yml/badge.svg)](https://github.com/collective/collective.editablemenu/actions/workflows/main.yml)
![Code Style](https://img.shields.io/badge/Code%20Style-Black-000000)

[![GitHub contributors](https://img.shields.io/github/contributors/collective/collective.editablemenu)](https://github.com/collective/collective.editablemenu)
[![GitHub Repo stars](https://img.shields.io/github/stars/collective/collective.editablemenu?style=social)](https://github.com/collective/collective.editablemenu)

</div>

A new addon for Plone Blicca that provides a behavior to create a custom menu in a given folder

## Features

TODO: List our awesome features

## Installation

Install collective.editablemenu with `pip`:

```shell
pip install collective.editablemenu
```

And to create the Plone site:

```shell
make create-site
```

## Contribute

- [Issue tracker](https://github.com/collective/collective.editablemenu/issues)
- [Source code](https://github.com/collective/collective.editablemenu/)

### Prerequisites ✅

-   An [operating system](https://6.docs.plone.org/install/create-project-cookieplone.html#prerequisites-for-installation) that runs all the requirements mentioned.
-   [uv](https://6.docs.plone.org/install/create-project-cookieplone.html#uv)
-   [Make](https://6.docs.plone.org/install/create-project-cookieplone.html#make)
-   [Git](https://6.docs.plone.org/install/create-project-cookieplone.html#git)
-   [Docker](https://docs.docker.com/get-started/get-docker/) (optional)

### Installation 🔧

1.  Clone this repository, then change your working directory.

    ```shell
    git clone git@github.com:collective/collective.editablemenu.git
    cd collective.editablemenu
    ```

2.  Install this code base.

    ```shell
    make install
    ```


### Add features using `plonecli` or `bobtemplates.plone`

This package provides markers as strings (`<!-- extra stuff goes here -->`) that are compatible with [`plonecli`](https://github.com/plone/plonecli) and [`bobtemplates.plone`](https://github.com/plone/bobtemplates.plone).
These markers act as hooks to add all kinds of subtemplates, including behaviors, control panels, upgrade steps, or other subtemplates from `plonecli`.

To run `plonecli` with configuration to target this package, run the following command.

```shell
make add <template_name>
```

For example, you can add a content type to your package with the following command.

```shell
make add content_type
```

You can add a behavior with the following command.

```shell
make add behavior
```

```{seealso}
You can check the list of available subtemplates in the [`bobtemplates.plone` `README.md` file](https://github.com/plone/bobtemplates.plone/?tab=readme-ov-file#provided-subtemplates).
See also the documentation of [Mockup and Patternslib](https://6.docs.plone.org/classic-ui/mockup.html) for how to build the UI toolkit for Classic UI.
```

## License

The project is licensed under GPLv2.

## Credits and acknowledgements 🙏

Generated using [Cookieplone (2.0.2)](https://github.com/plone/cookieplone) and [cookieplone-templates (2e19702)](https://github.com/plone/cookieplone-templates/commit/2e19702a8c4c221b540f70eea38f6c2981329f5c) on 2026-10-17 09:34:24.128161. A special thanks to all contributors and supporters!
