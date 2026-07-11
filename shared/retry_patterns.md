# Retry Patterns

Retry only errors likely to be transient:

- temporary filesystem or network failures;
- throttling;
- service unavailability.

Do not retry deterministic contract failures such as:

- missing required columns;
- duplicate business keys;
- invalid domain values;
- negative quantities.

The local `retry` decorator uses bounded exponential delay. Framework examples
also set finite retry counts to avoid infinite failure loops.
