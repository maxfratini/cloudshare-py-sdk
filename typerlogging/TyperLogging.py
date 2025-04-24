# File: typer_logger.py
import logging
import sys
from typing import Optional

import typer


class TyperLogging:
    """
    Gestore di logging che integra il logging standard di Python con typer.echo.
    Permette di avere output semplici su console e dettagliati su file.
    """

    class TyperLogHandler(logging.Handler):
        """Handler di logging personalizzato che utilizza typer.echo con messaggi concisi"""

        def emit(self, record):
            # Estrai solo il messaggio senza formattazione timestamp/livello
            msg = record.getMessage()

            # Usa colori diversi in base al livello di log
            if record.levelno >= logging.ERROR:
                typer.echo(f"ERROR: {msg}", err=True, color=True)  # Errori in rosso su stderr
            elif record.levelno >= logging.WARNING:
                typer.echo(f"WARNING: {msg}", color=True)  # Warning con colore (giallo)
            elif record.levelno >= logging.INFO:
                typer.echo(msg)  # Info normali
            else:  # DEBUG
                typer.echo(f"DEBUG: {msg}", color=True)  # Debug in blu

    def __init__(self, name: Optional[str] = None, log_file: Optional[str] = None, log_level: int = logging.INFO, file_mode: str = "a"):
        """
        Inizializza il logger.

        Args:
            name (str, optional): Nome del logger. Se None, usa il logger root.
            log_file (str, optional): Percorso del file di log. Se None, scrive solo su console.
            log_level (int, optional): Livello di logging. Default è INFO.
            file_mode (str, optional): Modalità apertura file ('a' per append, 'w' per sovrascrivere).
        """
        self.log_file = log_file
        self.log_level = log_level

        # Ottieni il logger (root o specifico)
        if name:
            self.logger = logging.getLogger(name)
        else:
            self.logger = logging.getLogger()

        self.logger.setLevel(log_level)

        # Rimuovi tutti gli handler esistenti
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        if log_file:
            # Se è specificato un file, crea un FileHandler con formatter completo
            file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            file_handler = logging.FileHandler(log_file, mode=file_mode)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

        # Aggiungi sempre un handler per la console che usa typer.echo
        console_handler = self.TyperLogHandler()
        # Nessun formatter per il console_handler - userà solo il messaggio puro
        self.logger.addHandler(console_handler)

    def get_logger(self):
        """Restituisce l'oggetto logger configurato"""
        return self.logger

    @classmethod
    def setup_from_typer(
        cls,
        log_file: Optional[str] = typer.Option(None, "--log-file", "-l", help="File di log. Se non specificato, scrive solo su console."),
        loglevel: bool = typer.Option(False, "--loglevel", "-v", help="Set logging level"),
        name: Optional[str] = None,
        file_mode: str = "a",
    ):
        """
        Crea un logger da parametri Typer.

        Args:
            log_file: Opzione Typer per il file di log
            verbose: Opzione Typer per abilitare la modalità verbosa
            name: Nome del logger
            file_mode: Modalità di apertura del file

        Returns:
            logging.Logger: Il logger configurato
        """
        valid_levels = {"DEBUG": logging.DEBUG, "INFO": logging.INFO, "WARNING": logging.WARNING, "ERROR": logging.ERROR, "CRITICAL": logging.CRITICAL}

        log_level = valid_levels.get(loglevel.upper(), logging.INFO)

        logger_manager = cls(name, log_file, log_level, file_mode)
        return logger_manager.get_logger()
