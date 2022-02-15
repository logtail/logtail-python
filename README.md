# Logtail - Python Logging Made Easy
  
  [![Logtail python client](https://user-images.githubusercontent.com/19272921/154085622-59997d5a-3f91-4bc9-a815-3b8ead16d28d.jpeg)](https://betterstack.com/logtail)


[![ISC License](https://img.shields.io/badge/license-ISC-ff69b4.svg)](LICENSE.md)
[![PyPI version](https://badge.fury.io/py/logtail-python.svg)](https://badge.fury.io/py/logtail-python)
![Logtail python client](https://github.com/logtail/logtail-python/actions/workflows/main.yml/badge.svg?branch=master)

Collect logs directly from any Python code, including Django.

[Logtail](https://betterstack.com/logtail) is a hosted service that centralizes all of your logs into one place. Allowing for analysis, correlation and filtering with SQL. Actionable Grafana dashboards and collaboration come built-in. Logtail works with [any language or platform and any data source](https://docs.logtail.com/). 

### Features
- Simple integration. Integrates with the Python `logging` library.
- Support for structured logging and events.
- Automatically captures useful context.
- Performant, light weight, with a thoughtful design.

### Supported language versions
- Python 3.6.5 or newer
- `pip` 20.0.2 or newer

# Installation
Install the Logtail Python client library using the `pip` command:

```bash
pip install logtail-python
```

*Make sure you install the `logtail-python` package and not a different package with the `logtail` keyword in the package name from a different author.*

---

# Example project

To help you get started with using Logtail in your Python projects, we have prepared a simple Python program that showcases the usage of Logtail logger.

## Download and install the example project

You can download the [example project](https://github.com/logtail/logtail-python/tree/master/example-project) from GitHub directly or you can clone it to a select directory. Then install the `logtail-python` client library as shown before:

```bash
pip install logtail-python
```

 ## Run the example project
 
 To run the example application, simply run the following command:

```bash
python main.py <source-token>
```

*Don't forget to replace `<source-token>` with your actual source token which you can find by going to logtail.com -> sources -> edit.*


If you have trouble running the command above, check your Python installation and try running it with the `python3` command instead. It should give you the following output:

```
Output:
All done! You can check your logs now.
```

This example project will create a total of 6 logs. Each corresponding to its respective method.

## Explore how example project works
 
Learn how to setup Python logging by exploring the workings of the [example project](https://github.com/logtail/logtail-python/tree/master/example-project) in detail. 
 
---
 
## Get in touch

Have any questions? Please explore the Logtail [documentation](https://docs.logtail.com/) or contact our [support](https://betterstack.com/help).
