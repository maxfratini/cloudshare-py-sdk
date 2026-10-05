# mxCyclopts.py - Utility module for Cyclopts command line interface

# This module provides utilities for working with the Cyclopts CLI framework, including:
# - CommonOpts dataclass for shared command options
# - with_common_opts decorator for automatically adding common options to commands
# - Helper functions for CLI parameter handling

# The main components are:
# - CommonOpts: Dataclass containing common CLI options like url, timeout, verbose
# - with_common_opts: Decorator to add CommonOpts to any Cyclopts command
# - app: Main Cyclopts App instance for registering commands


import inspect
import threading
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import ClassVar, TypeVar, cast, get_type_hints

from cyclopts import App, Parameter

# Tipo generico per mxCommonOpts
CO = TypeVar("CO")  # , bound=CommonOpts)
# Tipo generico per la funzione decorata
T = TypeVar("T")


# Definizione della classe base mxCommonOpts
@Parameter(name="*", group="Common Options", help="Options for all commands")
@dataclass
class CommonOpts:
    """
    Base class for common command line options.
    This class is used to define common options that can be shared across multiple commands.
    Implements the Singleton pattern to ensure only one instance of each subclass is created.
    """

    # Dizionario per memorizzare le istanze singleton per ciascuna sottoclasse
    _instances: ClassVar[dict[type["CommonOpts"], "CommonOpts"]] = {}
    _initialized: ClassVar[dict[type["CommonOpts"], bool]] = {}
    _creation_lock: ClassVar[threading.RLock] = threading.RLock()

    def __init__(self, *args, **kwargs):
        # Thread-local per memorizzare le opzioni in modo thread-safe
        self._thread_local = threading.local()

    def __post_init__(self):
        # print(f"CommonOpts.__post_init__(): {self.__class__.__name__}")
        pass

    def initialize(self):
        """
        Inizializza l'applicazione con queste opzioni.
        Può essere sovrascritto dalle sottoclassi.
        """
        pass

    @classmethod
    def get_instance(cls: type[CO]) -> CO:
        """
        Ottiene l'istanza singleton di questa classe.
        Se non esiste ancora, la crea e la inizializza.
        """
        # Fast path - controlla senza lock
        if cls in CommonOpts._instances and CommonOpts._initialized.get(cls, False):
            return cast(T, CommonOpts._instances[cls])

        # Slow path - acquisisce il lock
        with CommonOpts._creation_lock:
            # Controlla di nuovo per evitare race condition
            if cls not in CommonOpts._instances:
                # Crea l'istanza
                instance = cls()
                # Registra l'istanza
                CommonOpts._instances[cls] = instance
                # L'inizializzazione viene fatta qui, non in __post_init__
                try:
                    instance.initialize()
                    CommonOpts._initialized[cls] = True
                except Exception as e:
                    print(f"Warning: Failed to initialize {cls.__name__}: {e}")
                    # Ancora marchiamo come inizializzata per evitare ripetuti tentativi
                    CommonOpts._initialized[cls] = True
            elif not CommonOpts._initialized.get(cls, False):
                # L'istanza esiste ma non è ancora inizializzata
                try:
                    CommonOpts._instances[cls].initialize()
                    CommonOpts._initialized[cls] = True
                except Exception as e:
                    print(f"Warning: existing instance, but failed to initialize {cls.__name__}: {e}")
                    CommonOpts._initialized[cls] = True

            return cast(T, CommonOpts._instances[cls])

    @classmethod
    def set_instance(cls: type[CO], instance: CO) -> None:
        """
        Imposta manualmente l'istanza singleton.
        Utile per i test o per contesti speciali.
        """
        with CommonOpts._creation_lock:
            old_instance = cls._instances.get(cls, None)
            CommonOpts._instances[cls] = instance

            # Se l'istanza è nuova, esegui l'inizializzazione
            if instance is not old_instance:
                try:
                    instance.initialize()
                    CommonOpts._initialized[cls] = True
                except Exception as e:
                    print(f"Warning: Failed to initialize manually set instance: {e}")
                    CommonOpts._initialized[cls] = True


class mxCycloptsApp(App):
    """Versione personalizzata di App con comando che aggiunge automaticamente CommonOpts."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Thread-local per memorizzare le opzioni in modo thread-safe
        self._thread_local = threading.local()
        self._thread_local.current_opts = None
        self._thread_local.current_opts_class = None

    def command_with_commonopts(self, opts_class: type[CO] = CommonOpts):
        """
        Decoratore che aggiunge opzioni comuni a un comando.

        Può essere chiamato in vari modi:
        - @app.command_with_common_opts(ApiOpts)
        - @app.command_with_common_opts(opts_class=ApiOpts)

        Args:
            opts_class: Classe di opzioni (keyword only)
            **kwargs: Altri argomenti da passare a @app.command

        Returns:
            Un decoratore o la funzione decorata
        """

        # Crea e restituisci il decoratore
        def decorator(func: Callable[..., T], **kwargs) -> Callable[..., T]:
            return self._apply_commonopts(func, opts_class, **kwargs)

        return decorator

    def _apply_commonopts(self, func: Callable[..., T], opts_class, **kwargs) -> Callable[..., T]:

        print(f"_apply_commonopts() - opts_class: {opts_class}")

        # set common opts variable name
        commonopts_var_name = "common_opts"
        # Ottieni la firma della funzione originale
        sig = inspect.signature(func)
        parameters = list(sig.parameters.values())

        #  print all signature details for existing func
        for p in parameters:
            print(f"Func Parameter: {p}")

        # Controlla se un'istanza di mxCommonOpts è già presente
        has_common = any(p.name == commonopts_var_name and issubclass(opts_class, p.annotation) for p in parameters)
        if has_common:
            # Se opts è già presente, registra semplicemente la funzione
            # return app.command(func)
            return self.command(**kwargs)(func)

        # Crea una nuova funzione wrapper che include le opzioni
        @wraps(func)
        def wrapper(*args, **cmd_kwargs):
            # Ottieni o crea l'istanza di opzioni
            if hasattr(opts_class, "get_instance"):
                # Per le classi singleton (CommonOpts e sottoclassi)
                opts = opts_class.get_instance()
            else:
                # Per le classi non-singleton
                opts = cmd_kwargs.get(commonopts_var_name, opts_class())

            print(f"wrapper() - opts: {opts}")

            # Memorizza le opzioni correnti in modo thread-safe
            # Salva i valori precedenti, se esistono
            # old_opts = getattr(self._thread_local, "current_opts", None)
            # old_opts_class = getattr(self._thread_local, "current_opts_class", None)

            # Imposta i nuovi valori
            self._thread_local.current_opts = opts
            self._thread_local.current_opts_class = opts_class

            try:
                # Crea una copia dei parametri da passare alla funzione originale
                # Rimuovendo common_opts se non presente nella firma originale
                call_kwargs = cmd_kwargs.copy()

                # Aggiunge common_opts solo se la funzione lo accetta
                if commonopts_var_name in sig.parameters:
                    call_kwargs[commonopts_var_name] = opts
                else:
                    # Rimuovi il parametro se presente ma non accettato dalla funzione
                    call_kwargs.pop(commonopts_var_name, None)

                # Chiamata alla funzione originale con i parametri adeguati
                return func(*args, **call_kwargs)

            finally:
                #     # Ripristina i valori precedenti
                #     if old_opts is not None:
                #         self._thread_local.current_opts = old_opts
                #     else:
                #         if hasattr(self._thread_local, "current_opts"):
                #             delattr(self._thread_local, "current_opts")

                #     if old_opts_class is not None:
                #         self._thread_local.current_opts_class = old_opts_class
                #     else:
                #         if hasattr(self._thread_local, "current_opts_class"):
                #             delattr(self._thread_local, "current_opts_class")
                pass

        # Aggiorna la firma della funzione
        new_params = parameters + [inspect.Parameter(name=commonopts_var_name, kind=inspect.Parameter.KEYWORD_ONLY, annotation=opts_class, default=inspect.Parameter.empty)]

        wrapper.__signature__ = sig.replace(parameters=new_params)

        # Aggiorna le annotazioni dei tipi
        hints = get_type_hints(func)
        hints[commonopts_var_name] = opts_class
        wrapper.__annotations__ = hints

        #  print all signature details for new func
        parameters = list(wrapper.__signature__.parameters.values())
        for p in parameters:
            print(f"New Parameter: {p}")

        # Registra la funzione wrapper come comando
        return self.command(**kwargs)(wrapper)

    def get_commonopts(self) -> CO:
        """
        Ottiene l'istanza corrente delle opzioni comuni.
        Questa funzione deve essere chiamata all'interno di una funzione
        decorata con @app.command_with_common_opts o simili.

        Returns:
            L'istanza corrente delle opzioni comuni

        Raises:
            RuntimeError: Se chiamata al di fuori di una funzione decorata
        """
        print(f"get_common_opts() - current_opts: {self._thread_local.current_opts}")
        if not hasattr(self._thread_local, "current_opts"):
            raise RuntimeError("get_common_opts() chiamata al di fuori di una funzione decorata " "con @app.command_with_common_opts o simili.")

        # Cast necessario per far funzionare correttamente il type checking
        return cast(CO, self._thread_local.current_opts)

    def get_commonopts_class(self) -> type[CO]:
        """
        Ottiene la classe delle opzioni comuni correnti.

        Returns:
            La classe delle opzioni comuni correnti

        Raises:
            RuntimeError: Se chiamata al di fuori di una funzione decorata
        """
        if not hasattr(self._thread_local, "current_opts_class"):
            raise RuntimeError("get_common_opts_class() chiamata al di fuori di una funzione decorata " "con @app.command_with_common_opts o simili.")

        return cast(type[CO], self._thread_local.current_opts_class)
