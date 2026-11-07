import os
from dotenv import load_dotenv

# override=True so edits to .env win over stale variables already in the shell
load_dotenv(override=True)


def on_error(err):
    print(f"Kafka error: {err}")


def _require(name):
    # Fail early with a clear message instead of passing None to Kafka
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} is missing from the .env file")
    return value


def get_kafka_config():
    return {
        'bootstrap.servers': _require('KAFKA_BOOTSTRAP_SERVER'),
        'security.protocol': _require('KAFKA_SECURITY_PROTOCOL'),
        'sasl.mechanism': _require('KAFKA_SASL_MECHANISM'),
        'sasl.username': _require('KAFKA_USER'),
        'sasl.password': _require('KAFKA_PASSWORD'),
        'group.id': _require('KAFKA_GROUP_ID'),
        'auto.offset.reset': 'latest',
        'error_cb': on_error,
    }


def get_kafka_topic():
    return _require('KAFKA_TOPIC')
