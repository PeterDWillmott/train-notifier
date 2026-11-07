
# Kafka
A message system. Programs write or read from it.

**Producer** = writes messages (Darwin system publishing train updates)
**Topic** = named channel messages are written to (KAFKA_TOPIC)

## Consumer
Program that reads messages from a topic (my code - connects to Kafka, subscribes to topic to receive the train updates)

Configured with server address, login and group.id
- group.id is for server to identify what messages my program has read

# Polling
Kafka doesn't push messages. Consumer has to ask repeatedly == **Polling**

Execution stops at poll for time specified by argument
- 1 second is enough time to receive and short enough to execute further code if nothing received
- Also why consumer needs it's own thread
- Kafka expects regular polling to keep connection alive

# Finally
Last block of a try-except statement

Code in this block always executes regardless of any code executed in either try or except including return statements

# Env
``` Python
load_dotenv(override=True)
```

Override parameter forces terminal to get the fresh variables from .env rather than holding old ones when it was originally loaded

# Execution
- Consumer only: `python consume_darwin.py`
- API with the consumer: `uvicorn main:app --reload, then open http://localhost:8000/messages`


# Midnight Unsupported
For the scope I have for the project, supporting trains past midnight is unnecessary and adds complications.

Keeping trains within the same day allows data to stay within the time format rather than using `datetime`:
- No conversions needed
- Date data still available

However, this needs validating to restrict searching for trains travelling around midnight

# Running Main
```Python
if __name__ == "__main__":
    main()
```

`__name__` is a variable in every python file:
- `"__main__"` if file run directly
- `"fileName"` if imported and executed

So main only executed if file is executed directly

# Future Scope
Only personal stations at first because of converting TIPLOCs to CRS codes. Should use CORPUS dataset as reference to translate all codes.

