<!-- omit in toc -->
# Contributing to py-xbrl

First off, thanks for taking the time to contribute! ❤️

All types of contributions are encouraged and valued. See the [Table of Contents](#table-of-contents) for different ways to help and details about how this project handles them. Please make sure to read the relevant section before making your contribution. It will make it a lot easier for us maintainers and smooth out the experience for all involved. The community looks forward to your contributions. 🎉

> And if you like the project, but just don't have time to contribute, that's fine. There are other easy ways to support the project and show your appreciation, which we would also be very happy about:
> - Star the project
> - Tweet about it
> - Refer this project in your project's readme
> - Mention the project at local meetups and tell your friends/colleagues

<!-- omit in toc -->
## Table of Contents


- [I Have a Question](#i-have-a-question)
- [I Want To Contribute](#i-want-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Your First Code Contribution](#your-first-code-contribution)
  - [Improving The Documentation](#improving-the-documentation)




## I Have a Question

> If you want to ask a question, we assume that you have read the available [Documentation](https://py-xbrl.readthedocs.io/en/latest/).

Before you ask a question, it is best to search for existing [Issues](https://github.com/manusimidt/py-xbrl/issues) that might help you. In case you have found a suitable issue and still need clarification, you can write your question in this issue.

If you then still feel the need to ask a question and need clarification, we recommend the following:

- If you have a generic question or suggestion please open  the [Discussion Forum](https://github.com/manusimidt/py-xbrl/discussions).
- If you have a problem with the libary or something is not working please open a new [Issue](https://github.com/manusimidt/py-xbrl/issues/new)


## I Want To Contribute

> ### Legal Notice <!-- omit in toc -->
> When contributing to this project, you must agree that you have authored 100% of the content, that you have the necessary rights to the content and that the content you contribute may be provided under the project license.

### Reporting Bugs

<!-- omit in toc -->
#### Before Submitting a Bug Report

A good bug report shouldn't leave others needing to chase you up for more information. Therefore, we ask you to investigate carefully, collect information and describe the issue in detail in your report. Additionally, if possible, please **append the link to the XBRL document** you encountered the bug with or share it otherwise. It greatly helps us to replicate and solve the bug! 


<!-- omit in toc -->
#### How Do I Submit a Good Bug Report?

We use GitHub issues to track bugs and errors. If you run into an issue with the project:

- Open an [Issue](https://github.com/manusimidt/py-xbrl/issues/new).
- Explain the behavior you would expect and the actual behavior.
- Please provide as much context as possible and describe the *reproduction steps* that someone else can follow to recreate the issue on their own. This usually includes your code. For good bug reports you should isolate the problem and create a reduced test case.
- Please link or append the XBRL document with which you entcountered the issue



### Your First Code Contribution

This project uses [uv](https://docs.astral.sh/uv/) for dependency management,
[ruff](https://docs.astral.sh/ruff/) for linting and formatting, [ty](https://docs.astral.sh/ty/)
for type checking and [prek](https://prek.j178.dev) to run those tools as git hooks.

1. Fork the repository and clone your fork
2. Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then set up the
   environment. This installs py-xbrl together with the `dev` dependency group
   (ruff, ty, prek, pytest), pinned via `uv.lock`:
   ```shell
   uv sync
   ```
3. Install the git hooks, so linting, formatting and type checks run on every commit:
   ```shell
   uv run prek install
   ```
4. Implement and test the changes, document it as good as possible
5. Run the same checks the CI pipeline runs:
   ```shell
   uv run --frozen ruff check .
   uv run --frozen ruff format --check .
   uv run --frozen ty check
   uv run --frozen pytest tests/
   ```
   `uv run --frozen prek run --all-files` runs the lint, format and type checks in one go.
6. Commit and Push your changes to the forked repo
7. Create a pull request
8. Check if the CI/CD pipeline still executes correctly
9. Ping me with @manusimidt so I can review and approve 
10. Thanks for your contribution! 😊


### Improving The Documentation
The documentation of `py-xbrl` is build with [Sphinx](https://www.sphinx-doc.org/en/master/). It utilizes both `.rst` files and also in-code documentation in order to build the docs. You can find the `.rst` files in the [docs Folder](https://github.com/manusimidt/py-xbrl/tree/main/docs). Feel free to create an Issue or open a Pull request if you want to improve some part of the documentation.


------------------------------
This guide is based on the **contributing-gen**. [Make your own](https://github.com/bttger/contributing-gen)!
