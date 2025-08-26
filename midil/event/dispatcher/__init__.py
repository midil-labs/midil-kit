"""
This is your dispatcher and handler registry.

Responsibilities:
- Allow developers to register handlers for event types (on, route)
- Track metadata: retries, backoff, timeouts, dependencies
- Validate dependencies between handlers (GraphValidator)
- When an Event arrives, determine which handlers to run and in what order

Think of this as the map of what to do when an event happens.
"""
