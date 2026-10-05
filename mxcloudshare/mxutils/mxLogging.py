# File: typer_logger.py
import logging

from rich import print as rich_print


class mxLogger(logging.Logger):
    """
    Gestore di logging che integra il logging standard di Python con rich formatting.
    Permette di avere output semplici su console e dettagliati su file.
    Inoltre introduce un nuovo livello di logging denominato PRINT (25), che è superiore a INFO ma inferiore a WARNING.
    Questo livello può essere usato per messaggi applicativi formattati, che non sono errori.
    Esempio di utilizzo:
        logger.print("Questo è un [bold blue]messaggio[/bold blue] di print.")
    """

    # Definisci un livello di logging personalizzato per PRINT, superiore ad info ma inferiore a warning
    # Questo livello può essere usato per sostituire la print per messaggi applicativi che non sono errori
    PRINT = 25
    PRINT_NAME = "PRINT"

    valid_levels = {
        "DEBUG": logging.DEBUG,
        "PRINT": PRINT,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    class mxLogHandler(logging.Handler):
        """Handler di logging personalizzato che utilizza rich_print con messaggi concisi"""

        def emit(self, record):
            # Estrai solo il messaggio senza formattazione timestamp/livello
            msg = record.getMessage()

            # Usa colori diversi in base al livello di log
            if record.levelno >= logging.CRITICAL:
                rich_print(f"[bold magenta]CRITICAL:[/bold magenta] {msg}")  # Critical in viola
            elif record.levelno >= logging.ERROR:
                rich_print(f"[bold red]ERROR:[/bold red] {msg}")  # Errori in rosso
            elif record.levelno >= logging.WARNING:
                rich_print(f"[bold yellow]WARNING:[/bold yellow] {msg}")  # Warning in giallo
            elif record.levelno >= mxLogger.PRINT:
                rich_print(f"{msg}")  # Nuovo livello PRINT a console, non colorato (si lascia le colorazione a chi lo usa)
            elif record.levelno >= logging.INFO:
                rich_print(f"[bold gray]INFO:[/bold gray] {msg}")  # Info in grigio
            else:  # DEBUG
                rich_print(f"[bold white]DEBUG:[/bold white] {msg}")  # Debug in bianco

    def __init__(self, name: str | None = None, log_file: str | None = None, log_level: str = "INFO", file_mode: str = "a"):
        """
        Inizializza il logger.

        Args:
            name (str, optional): Nome del logger. Se None, usa il logger root.
            log_file (str, optional): Percorso del file di log. Se None, scrive solo su console.
            log_level (int, optional): Livello di logging. Default è INFO.
            file_mode (str, optional): Modalità apertura file ('a' per append, 'w' per sovrascrivere).
        """
        # print(f"INIT: {name} - log_file: {log_file} - log_level: {log_level} - file_mode: {file_mode}")
        # if name is None:
        #     raise ValueError("Il nome del logger è obbligatorio.")

        # Inizializza il logger base
        super().__init__(name)

        # Add PRINT level
        logging.addLevelName(self.PRINT, self.PRINT_NAME)
        logging.Logger.print = self.print

        # Ottieni il logger (root o specifico)
        if name:
            self.logger = logging.getLogger(name)
        else:
            self.logger = logging.getLogger()

        # Rimuovi tutti gli handler esistenti
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # Aggiungi sempre un handler per la console
        console_handler = self.mxLogHandler()

        # Nessun formatter per il console_handler - userà solo il messaggio puro
        self.logger.addHandler(console_handler)

        self.setup_mxLogger(log_file=log_file, log_level=log_level, file_mode=file_mode)

        return

    def get_logger(self):
        """Restituisce l'oggetto logger configurato"""
        return self.logger

    def setup_mxLogger(
        self,
        log_file: str | None = None,
        log_level: str | None = None,
        file_mode: str = "a",
    ):
        """
        Configura il logger con i parametri specificati.
        Args:
            log_file (str, optional): Percorso del file di log. Se None, scrive solo su console.
            loglevel (str, optional): Livello di logging. Default è INFO.
            file_mode (str, optional): Modalità apertura file ('a' per append, 'w' per sovrascrivere).
        """
        # controlla il livello di logging
        self.log_level = self.valid_levels.get(log_level.upper(), logging.INFO)
        self.logger.setLevel(self.log_level)

        self.log_file = log_file
        if log_file:
            # Se è specificato un file, crea un FileHandler con formatter completo
            file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            file_handler = logging.FileHandler(log_file, mode=file_mode)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

        return self.logger

    def print(self, message, *args, **kwargs):
        """
        Log 'msg % args' with severity 'PRINT'.
        """
        self.logger.log(self.PRINT, message)


def getLogger(name: str | None = None):
    """
    Ottieni un logger con il nome specificato.
    """
    if name is None:
        name = "root"

    return mxLogger(name)
