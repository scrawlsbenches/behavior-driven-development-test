"""
Service Container - Dependency Management
==========================================

The service container manages service registration and resolution.
It's a simple dependency injection container that:

1. REGISTERS services (what implements what)
2. RESOLVES services (get an instance of something)
3. MANAGES lifetimes (singleton vs transient)

WHY A CONTAINER
---------------

Without a container:
    # Every class creates its own dependencies
    class SearchHandler:
        def __init__(self):
            self.logger = StructuredLogger()  # Hardcoded!
            self.generator = LLMGenerator()   # Hardcoded!

With a container:
    # Dependencies are declared, container provides them
    class SearchHandler:
        def __init__(self, logger: Logger, generator: Generator):
            self.logger = logger
            self.generator = generator

    # Registration (once, at startup)
    container.register(Logger, StructuredLogger)
    container.register(Generator, LLMGenerator)

    # Resolution
    handler = container.resolve(SearchHandler)  # Gets wired up

Benefits:
- Swap implementations without changing code
- Test with mock implementations
- Single source of truth for what's used

LIFETIME MANAGEMENT
-------------------

SINGLETON: Same instance every time
    container.register_singleton(Logger, StructuredLogger)

TRANSIENT: New instance every time
    container.register_transient(Context, Context)

FACTORY: Custom creation logic
    container.register_factory(Generator, lambda c: LLMGenerator(c.resolve(Logger)))

DESIGN DECISIONS
----------------

1. WHY NOT USE AN EXISTING DI LIBRARY?

   Python DI libraries (dependency_injector, injector, etc.) are heavy.
   We need a simple container that:
   - Registers protocol → implementation mappings
   - Resolves by protocol type
   - Handles singleton vs transient

   ~100 lines of code vs. a dependency.

2. WHY PROTOCOL-BASED?

   We register protocols, not classes:
       container.register(Logger, StructuredLogger)  # Logger is protocol

   This enforces the abstraction boundary. You can't accidentally
   depend on StructuredLogger - only on Logger.

3. WHY EXPLICIT REGISTRATION?

   Some containers use auto-wiring (scan for classes). We don't because:
   - Explicit is better than implicit
   - Auto-wiring hides what's happening
   - Manual registration documents the architecture

"""

from typing import TypeVar, Any, Callable, Dict, Type, Protocol, get_type_hints
from enum import Enum, auto

T = TypeVar("T")


class Lifetime(Enum):
    """Service lifetime options."""
    SINGLETON = auto()  # One instance forever
    TRANSIENT = auto()  # New instance each time
    SCOPED = auto()     # One instance per scope (not implemented yet)


class ServiceContainer:
    """
    Simple dependency injection container.

    Manages service registration and resolution with lifetime control.

    Example:
        container = ServiceContainer()

        # Register services
        container.register(Logger, StructuredLogger)
        container.register_singleton(MetricsCollector, InMemoryMetrics)
        container.register_factory(Generator, lambda c: LLMGenerator(
            api_key=os.getenv("OPENAI_KEY"),
            logger=c.resolve(Logger),
        ))

        # Resolve services
        logger = container.resolve(Logger)
        generator = container.resolve(Generator)

    Thread Safety:
        This container is NOT thread-safe. In multi-threaded scenarios,
        either use a thread-local container or add locking.
    """

    def __init__(self) -> None:
        """Create an empty container."""
        # Protocol type → (implementation, lifetime)
        self._registrations: Dict[type, tuple[Any, Lifetime]] = {}
        # Singleton instances cache
        self._singletons: Dict[type, Any] = {}

    # =========================================================================
    # REGISTRATION
    # =========================================================================

    def register(
        self,
        protocol: type,
        implementation: type | Callable[["ServiceContainer"], Any],
        lifetime: Lifetime = Lifetime.TRANSIENT,
    ) -> "ServiceContainer":
        """
        Register a service implementation.

        Args:
            protocol: The protocol/interface type.
            implementation: The concrete type or factory function.
            lifetime: How long instances live.

        Returns:
            Self for chaining.

        Example:
            container.register(Logger, StructuredLogger)
            container.register(Generator, LLMGenerator, Lifetime.SINGLETON)
        """
        self._registrations[protocol] = (implementation, lifetime)
        return self

    def register_singleton(
        self,
        protocol: type,
        implementation: type | Callable[["ServiceContainer"], Any],
    ) -> "ServiceContainer":
        """
        Register a singleton service.

        Convenience method for register(..., Lifetime.SINGLETON).

        Example:
            container.register_singleton(Logger, StructuredLogger)
        """
        return self.register(protocol, implementation, Lifetime.SINGLETON)

    def register_transient(
        self,
        protocol: type,
        implementation: type | Callable[["ServiceContainer"], Any],
    ) -> "ServiceContainer":
        """
        Register a transient service.

        Convenience method for register(..., Lifetime.TRANSIENT).

        Example:
            container.register_transient(Context, Context)
        """
        return self.register(protocol, implementation, Lifetime.TRANSIENT)

    def register_instance(
        self,
        protocol: type,
        instance: Any,
    ) -> "ServiceContainer":
        """
        Register an existing instance as a singleton.

        Use when you already have an instance to share.

        Example:
            logger = StructuredLogger()
            container.register_instance(Logger, logger)
        """
        self._registrations[protocol] = (lambda c: instance, Lifetime.SINGLETON)
        self._singletons[protocol] = instance
        return self

    def register_factory(
        self,
        protocol: type,
        factory: Callable[["ServiceContainer"], Any],
        lifetime: Lifetime = Lifetime.TRANSIENT,
    ) -> "ServiceContainer":
        """
        Register a factory function for custom creation.

        The factory receives the container for resolving dependencies.

        Example:
            container.register_factory(Generator, lambda c: LLMGenerator(
                api_key=os.getenv("API_KEY"),
                logger=c.resolve(Logger),
            ))
        """
        return self.register(protocol, factory, lifetime)

    # =========================================================================
    # RESOLUTION
    # =========================================================================

    def resolve(self, protocol: type) -> Any:
        """
        Resolve a service by its protocol type.

        Args:
            protocol: The protocol type to resolve.

        Returns:
            An instance of a type implementing the protocol.

        Raises:
            KeyError: If protocol is not registered.

        Example:
            logger = container.resolve(Logger)
        """
        if protocol not in self._registrations:
            raise KeyError(f"No registration for {protocol.__name__}")

        implementation, lifetime = self._registrations[protocol]

        # Check singleton cache
        if lifetime == Lifetime.SINGLETON and protocol in self._singletons:
            return self._singletons[protocol]

        # Create instance
        if callable(implementation) and not isinstance(implementation, type):
            # It's a factory function
            instance = implementation(self)
        else:
            # It's a type, try to construct with dependencies
            instance = self._construct(implementation)

        # Cache if singleton
        if lifetime == Lifetime.SINGLETON:
            self._singletons[protocol] = instance

        return instance

    def _construct(self, cls: type) -> Any:
        """
        Construct an instance, resolving dependencies from type hints.

        This is basic auto-wiring: looks at __init__ type hints and
        resolves them from the container.
        """
        try:
            hints = get_type_hints(cls.__init__)
        except Exception:
            # No type hints, try no-arg construction
            return cls()

        # Remove 'return' hint if present
        hints.pop("return", None)

        # Resolve dependencies
        kwargs = {}
        for name, hint in hints.items():
            if hint in self._registrations:
                kwargs[name] = self.resolve(hint)

        return cls(**kwargs)

    # =========================================================================
    # INTROSPECTION
    # =========================================================================

    def is_registered(self, protocol: type) -> bool:
        """Check if a protocol is registered."""
        return protocol in self._registrations

    def get_lifetime(self, protocol: type) -> Lifetime | None:
        """Get the lifetime of a registered service."""
        if protocol not in self._registrations:
            return None
        return self._registrations[protocol][1]

    def clear(self) -> None:
        """Clear all registrations and cached singletons."""
        self._registrations.clear()
        self._singletons.clear()

    def __contains__(self, protocol: type) -> bool:
        """Support 'in' operator."""
        return self.is_registered(protocol)
