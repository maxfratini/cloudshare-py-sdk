import requests
import datetime
import typer
import json

app = typer.Typer()

# Definisci l'URL base per le richieste API v3 di CloudShare
BASE_URL = 'https://use.cloudshare.com/api/v3'

def get_expired_classes(api_id: str, api_key: str) -> list:
    """
    Ottiene la lista delle classi scadute.
    """
    url = f"{BASE_URL}/class"
    headers = {'Authorization': f'ApiKey {api_key}:{api_secret}'}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        classes = response.json()
        expired_classes = [cls for cls in classes if is_expired(cls['end_date'])]
        return expired_classes
    else:
        typer.echo(f"Errore durante il recupero delle classi: {response.status_code}")
        raise typer.Exit()

def is_expired(end_date: str) -> bool:
    """
    Verifica se una data è scaduta.
    """
    now = datetime.datetime.utcnow()
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%SZ')
    return now > end_date

def delete_class(api_key: str, api_secret: str, class_id: str) -> None:
    """
    Elimina una classe dato il suo ID.
    """
    url = f"{BASE_URL}/class/{class_id}"
    headers = {'Authorization': f'ApiKey {api_key}:{api_secret}'}
    response = requests.delete(url, headers=headers)

    if response.status_code == 204:
        typer.echo(f"Classe con ID {class_id} eliminata con successo.")
    else:
        typer.echo(f"Errore durante l'eliminazione della classe {class_id}: {response.status_code}")

@app.command()
def main(file_path: str) -> None:
    """
    Programma per eliminare le classi scadute su CloudShare.
    """
    try:
        with open(file_path) as f:
            credentials = json.load(f)
            api_key: str = credentials.get('API_KEY')
            api_secret: str = credentials.get('API_SECRET')
    except FileNotFoundError:
        typer.echo("File non trovato.")
        raise typer.Exit()
    except json.JSONDecodeError:
        typer.echo("Errore nel parsing del file JSON.")
        raise typer.Exit()

    expired_classes: list = get_expired_classes(api_key, api_secret)
    if expired_classes:
        typer.echo("Classi scadute trovate:")
        for cls in expired_classes:
            typer.echo(f"ID: {cls['id']}, Nome: {cls['name']}, Data di fine: {cls['end_date']}")
            delete_class(api_key, api_secret, cls['id'])
    else:
        typer.echo("Nessuna classe scaduta trovata.")

if __name__ == "__main__":
    app()
