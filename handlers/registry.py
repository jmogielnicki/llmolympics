# handlers/registry.py
class HandlerRegistry:
    """
    Registry for phase handlers.

    Provides a way to register and retrieve handlers by name or
    by phase type. Uses a decorator pattern for registration.
    """

    _handlers = {}
    _default_handlers = {}

    @classmethod
    def register(cls, name):
        """
        Register a handler by name.

        Args:
            name (str): The name to register the handler under

        Returns:
            function: Decorator function
        """
        def decorator(handler_class):
            cls._handlers[name] = handler_class
            return handler_class
        return decorator

    @classmethod
    def register_default(cls, phase_type):
        """
        Register a default handler for a phase type.

        Args:
            phase_type (str): The phase type

        Returns:
            function: Decorator function
        """
        def decorator(handler_class):
            cls._default_handlers[phase_type] = handler_class
            return handler_class
        return decorator

    @classmethod
    def get_handler(cls, name):
        """
        Get a handler by name.

        Args:
            name (str): The handler name

        Returns:
            PhaseHandler: An instance of the handler

        Raises:
            ValueError: If no handler is registered with the given name
        """
        if name not in cls._handlers:
            raise ValueError(f"No handler registered for '{name}'")
        return cls._handlers[name]()

    @classmethod
    def get_default_handler(cls, phase_type):
        """
        Get the default handler for a phase type.

        Args:
            phase_type (str): The phase type

        Returns:
            PhaseHandler: An instance of the handler

        Raises:
            ValueError: If no default handler is registered for the phase type
        """
        if phase_type not in cls._default_handlers:
            raise ValueError(f"No default handler for phase type '{phase_type}'")
        return cls._default_handlers[phase_type]()