import json
from confluent_kafka import Consumer, KafkaError

from config import get_kafka_config, get_kafka_topic


def run_consumer(on_message, stop_event=None):
    """Poll the Darwin feed and pass each decoded message to on_message.

    Runs until stop_event is set (or forever if no stop_event is given).
    """
    consumer = Consumer(get_kafka_config())
    consumer.subscribe([get_kafka_topic()])

    try:
        while stop_event is None or not stop_event.is_set():
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue

            # Assign error to a variable so error.code() type-checks
            error = msg.error()
            if error:
                if error.code() != KafkaError._PARTITION_EOF:
                    print(f"Consumer error: {error}")
                continue

            # Prove the value is not None before decoding
            msg_value = msg.value()
            if msg_value is None:
                continue

            # Skip malformed messages instead of crashing the consumer
            try:
                data = json.loads(msg_value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"Skipping malformed message: {e}")
                continue

            on_message(data)
    finally:
        consumer.close()


def print_message(data):
    print("Received message:")
    print(json.dumps(data, indent=2)[:500])  # Print a 500-character preview
    print("-" * 50)


def main():
    print(f"Listening to Darwin feed on topic: {get_kafka_topic()}...\nPress Ctrl+C to exit.")
    try:
        run_consumer(print_message)
    except KeyboardInterrupt:
        print("\nStopping consumer...")


if __name__ == "__main__":
    main()
