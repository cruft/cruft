[![cruft - Fight Back Against the Boilerplate Monster!](https://raw.github.com/timothycrosley/cruft/master/art/logo_large.png)](https://timothycrosley.github.io/cruft/)
_________________

[![PyPI version](https://badge.fury.io/py/cruft.svg)](http://badge.fury.io/py/cruft)
[![Build Status](https://github.com/timothycrosley/cruft/workflows/Run%20tests/badge.svg)](https://github.com/timothycrosley/cruft/actions?query=workflow%3A%22Run+tests%22+branch%3Amaster)
[![codecov](https://codecov.io/gh/timothycrosley/cruft/branch/master/graph/badge.svg)](https://codecov.io/gh/timothycrosley/cruft)
[![Join the chat at https://gitter.im/timothycrosley/cruft](https://badges.gitter.im/timothycrosley/cruft.svg)](https://gitter.im/timothycrosley/cruft?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![License](https://img.shields.io/github/license/mashape/apistatus.svg)](https://pypi.python.org/pypi/cruft/)
[![Downloads](https://pepy.tech/badge/cruft)](https://pepy.tech/project/cruft)
_________________

[Read Latest Documentation](https://timothycrosley.github.io/cruft/) - [Browse GitHub Code Repository](https://github.com/timothycrosley/cruft/)
_________________

**cruft** allows you to maintain all the necessary boilerplate for packaging and building projects separate from the code you intentionally write.
Fully compatible with existing [Cookiecutter](https://github.com/cookiecutter/cookiecutter) templates.

Creating new projects from templates using cruft is easy:

![Example Usage New Project](https://raw.githubusercontent.com/timothycrosley/cruft/master/art/example.gif)

And, so is updating them as the template changes overtime:

![Example Usage New Project](https://raw.githubusercontent.com/timothycrosley/cruft/master/art/example_update.gif)

Many project template utilities exist that automate the copying and pasting of code to create new projects. This *seems* great! However, once created, most leave you with that copy-and-pasted code to manage through the life of your project.

cruft is different. It automates the creation of new projects like the others, but then it also helps you to manage the boilerplate through the life of the project. cruft makes sure your code stays in-sync with the template it came from for you.

## Key Features:

* **Cookiecutter Compatible**: cruft utilizes [Cookiecutter](https://github.com/cookiecutter/cookiecutter) as its template expansion engine. Meaning it retains full compatibility with all existing [Cookiecutter](https://github.com/cookiecutter/cookiecutter) templates.
* **Template Validation**: cruft can quickly validate whether or not a project is using the latest version of a template using `cruft check`. This check can easily be added to CI pipelines to ensure your projects stay in-sync.
* **Automatic Template Updates**: cruft automates the process of updating code to match the latest version of a template, making it easy to utilize template improvements across many projects.

## Installation:

To get started - install `cruft` using a Python package manager:

`pip3 install cruft`

OR

`poetry add cruft`

OR

`pipenv install cruft`


## Creating a New Project:

To create a new project using cruft run `cruft create PROJECT_URL` from the command line.

For example:

        cruft create https://github.com/timothycrosley/cookiecutter-python/

cruft will then ask you any necessary questions to create your new project. It will use your answers to expand the provided template, and then return the directory it placed the expanded project.
Behind the scenes, cruft uses [Cookiecutter](https://github.com/cookiecutter/cookiecutter) to do the project expansion. The only difference in the resulting output is a `.cruft.json` file that
contains the git hash of the template used as well as the parameters specified.

## Updating a Project

To update an existing project, that was created using cruft, run `cruft update` in the root of the project.
If there are any updates, cruft will have you review them before applying. If you accept the changes cruft will apply them to your project
and update the `.cruft.json` file for you.

!!! tip
    Sometimes certain files just aren't good fits for updating. Such as test cases or `__init__` files. You can tell cruft to always skip updating these files on a project by project basis by added them
    to a skip section within your .cruft.json file:

        {
            "template": "https://github.com/timothycrosley/cookiecutter-python",
            "commit": "8a65a360d51250221193ed0ec5ed292e72b32b0b",
            "skip": [
                "cruft/__init__.py",
                "tests"
            ],
            ...
        }

    Or, if you have toml installed, you can add skip files directly to a `tool.cruft` section of your `pyproject.toml` file:

        [tool.cruft]
        skip = ["cruft/__init__.py", "tests"]


## Checking a Project

Checking to see if a project is missing a template update is as easy as running `cruft check`. If the project is out-of-date an error and exit code 1 will be returned.
`cruft check` can be added to CI pipelines to ensure projects don't unintentionally drift.


## Linking an Existing Project

Have an existing project that you created from a template in the past using Cookiecutter directly? You can link it to the template that was used to create it using: `cruft link TEMPLATE_REPOSITORY`.

For example:

        cruft link https://github.com/timothycrosley/cookiecutter-python/

You can then specify the last commit of the template the project has been updated to be consistent with, or accept the default of using the latest commit from the template.

## Why Create cruft?

Since I first saw videos of [quickly](https://www.youtube.com/watch?v=9EctXzH2dss) being used to automate Ubuntu application creation, I've had a love/hate relationship with these kinds of tools.
I've used them for many projects and certainly seen them lead to productivity improvements. However, I've always felt like they were a double-edged sword. Sure, they would automate away the copying and pasting many would do to create projects. However, by doing so,
they encouraged more code to be copied and pasted! Then, over time, you could easily be left with hundreds of projects that contained copy-and-pasted code with no way to easy way to update them. I created cruft to be a tool that recognized that balance between project creation and maintenance and provided mechanisms to keep built projects up-to-date.

I hope you too find `cruft` useful!

~Timothy Crosley
