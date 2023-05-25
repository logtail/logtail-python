# Better Stack Python example project

To help you get started with using Better Stack in your Python projects, we have prepared a simple python program that showcases the usage of Better Stack logger in Python code.

## Download the example project

You can download the example project from GitHub directly or you can clone it to a select directory.

Then install the `logtail-python` client library as shown before:

```bash
pip install logtail-python
```

## Run the example project

To run the example application, simply run the following command:

```bash
python example-project.py <source-token>
```

Don't forget to replace `<source-token>` with your actual source toke which you can find in the source settings.

If you have trouble running the command above, check your Python installation and try running it with the `python3` command instead.

You should see the following output:

```
Output:
All done! You can check your logs now.
```

This will create a total of 6 logs. Each corresponds to its respective method. Detail explanation follows below.

# Logging

In this section, we will take a look at actual logging as shown in the example project.

## Setup

First, we need to import the Logtail client library to our code. This can be done using the import keyword. We also need to import the default logging library.

```python
# Import Logtail client library and default logging library
from logtail import LogtailHandler
import logging
```

Then we need to create a `handler`, which will be responsible for handling our log messages, and a `logger` that will create those messages and provide them to the `handler`.

```python
# Create handler
handler = LogtailHandler(source_token=sys.argv[1])

# Create logger
logger = logging.getLogger(__name__)
logger.handlers = []
logger.setLevel(logging.DEBUG) # Set minimal log level
logger.addHandler(handler) # assign handler to logger
```

### Setting log level

In logging, you can set the log level. This level determines the severity of the log and of the event that triggered that log. The available log levels are (from least to most severe) `debug, info, warning, error, exception, critical`. When and how to use them is explained in the **Logging example** section.

The `setLevel()` method is used to set the minimal log level threshold. This means that any log that is less severe than the threshold will be ignored. For example, if you set the threshold to `logging.INFO` any `logging.DEBUG` logs will be ignored and won’t be handled.

```python
...
logger.setLevel(logging.INFO) # Set minimal log level
...
```

```python
logger.debug('I am using Python!') # This call will be ignored
logger.info('I am using Better Stack!') # This call will be handled
```

Code above will generate only one log because the debug level message has lowered severity than the set threshold. 

## Logging example

The `logger` instance we created in the setup section is used to send log messages to Logtail. It provides 6 logging methods for the 6 default log levels. The log levels and their method are:

- **DEBUG** - Send debug messages using the `debug()` method
- **INFO** - Send informative messages about the application progress using the `info()` method
- **WARNING** - Report non-critical issues using the `warning()` method
- **ERROR** - Send messages about serious problems using the `error()` method
- **EXCEPTION** - Send exception level log about errors in runtime using the `exception()` method. **Error** level log will be sent. Exception info is added to the logging message.
- **CRITICAL** - Send messages about serious problems using the `critical()` method.

To send a log message of select log level, use the corresponding method. In this example, we will send the **ERROR** level log and **EXCEPTION** level log.

```python
# Send error level log about errors in runtime using the error() method
logger.error('Oops! An error occurred!')

# Send exception level log about errors in runtime using the exception() method
# Error level log will be sent. Exception info is added to the logging message. 
# This method should only be called from an exception handler.
try:
    nonexisting_function() # Calling nonexisting function
except Exception as Argument:
    logger.exception("Error occurred while calling non-existing function") # Additional info will be added
```

The code above will generate the following JSON logs:

```json
{
   "dt":"2022-02-03 12:08:55.642 UTC",
   "context":{
      "runtime":{
         "file_string":"example-project.py",
         "function_string":"<module>",
         "line_integer":"39",
         "logger_name_string":"__main__",
         "thread_id_integer":"140660399380288",
         "thread_name_string":"MainThread"
      },
      "system":{
         "pid_integer":"2701",
         "process_name_string":"MainProcess"
      }
   },
   "filename_string":"example-project.py",
   "level_string":"error",
   "message_string":"Oops! An error occured!",
   "severity_integer":"4"
}

{
   "dt":"2022-02-03 12:08:55.643 UTC",
   "context":{
      "runtime":{
         "file_string":"example-project.py",
         "function_string":"<module>",
         "line_integer":"50",
         "logger_name_string":"__main__",
         "thread_id_integer":"140660399380288",
         "thread_name_string":"MainThread"
      },
      "system":{
         "pid_integer":"2701",
         "process_name_string":"MainProcess"
      }
   },
   "filename_string":"example-project.py",
   "level_string":"error",
   "message_string":"Error occurred while calling non-existing function\nTraceback (most recent call last):\n  File \"example-project.py\", line 48, in <module>\n    nonexisting_function() # Calling nonexisting function\nNameError: name 'nonexisting_function' is not defined",
   "severity_integer":"4"
}
```

As you can see, both logs are almost identical. The key difference is that the `exception()` method generated an `error` level log and appended the log message with the exception message.

## Logging additional data

All of these methods expect a string message and they allow adding additional dictionary passed as an `extra`:

```python
# Send warning level log about worrying events using the warning() method
# You can also add custom structured information to the log by passing it as a second argument
logger.warning('Log structured data', extra={
    'item': {
        'url': "https://fictional-store.com/item-123",
        'price': 100.00
    }
})
```

This will generate the following JSON log:

```json
{
   "dt":"2022-02-03 12:08:55.642 UTC",
   "context":{
      "runtime":{
         "file_string":"example-project.py",
         "function_string":"<module>",
         "line_integer":"31",
         "logger_name_string":"__main__",
         "thread_id_integer":"140660399380288",
         "thread_name_string":"MainThread"
      },
      "system":{
         "pid_integer":"2701",
         "process_name_string":"MainProcess"
      }
   },
   "filename_string":"example-project.py",
   "item":{
      "price_float":100,
      "url_string":"https://fictional-store.com/item-123"
   },
   "level_string":"warn",
   "message_string":"Log structured data",
   "severity_integer":"3"
}
```

## Context

By default, we add information about the current runtime environment and about the current process into a `context` field of the logged item.

If you want to add some custom information to all logged items (e.g., the ID of the current user), you can do so by adding a custom context:

```python
with logtail.context(user={ 'id': 123 }):
    # ...
    logger.info('new subscription')
```

This snippet will produce the following JSON log:

```json
{
    "dt": "2021-03-29T11:24:21.788451Z",
    "level": "info",
    "message": "new subscription",
    "context": {
        "runtime": {
            "function": "function_name",
            "file": "script_file.py",
            "line": 3,
            "thread_id": "123456789",
            "thread_name": "async_thread",
            "logger_name": "logger"
        },
        "system": {
            "pid": 123456,
            "process_name": "python"
        },
        "user": {
            "id": 123
        }
    }
}
```
