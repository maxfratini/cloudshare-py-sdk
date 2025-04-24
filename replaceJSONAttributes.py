import json
import typer

app = typer.Typer()

def merge_json(json1: str, json2: str):
    with open(json1, 'r') as file1:
        data1 = json.load(file1)
    
    with open(json2, 'r') as file2:
        data2 = json.load(file2)
    
    # Sostituisci gli attributi comuni presenti in json1 con quelli di json2
    for key in data1:
        if key in data2:
            data1[key] = data2[key]
    
    return data1

@app.command()
def main(json1: str, json2: str):
    """
    Programma per unire due file JSON sostituendo gli attributi comuni del primo con quelli del secondo.
    """
    # Merge dei due JSON
    merged_data = merge_json(json1, json2)

    # Stampa il JSON risultante
    typer.echo(json.dumps(merged_data, indent=4))

if __name__ == "__main__":
    app()
