import click
import requests
from cryptoface_client.owner import Owner
import sys
from pathlib import Path
import os

CONFIG_PATH = "./client/config.ini"
SERVER_URI = "http://127.0.0.1:4567"
DISTANCE_THRESH = 1


@click.group()
@click.option("--debug/--no-debug", default=False)
def cli(debug):
    if debug:
        click.echo("Debug mode is on")


@cli.command()
@click.argument("name")
def register(name):
    owner = Owner.create(name)
    if not os.path.exists(CONFIG_PATH):
        Path(CONFIG_PATH).parent.mkdir(parents=True, exist_ok=True)
    owner.save(CONFIG_PATH)
    data = {"name": name, "public_key": list(owner.public_key)}
    response = requests.post(f"{SERVER_URI}/api/owners", json=data)

    if response.status_code == 201:
        click.echo(f"Onwer {response.text} added")
    else:
        click.echo(f"Error inserting owner: {response.text}")


@cli.command()
@click.argument("name")
def unregister(name):
    if not os.path.exists(CONFIG_PATH):
        click.echo("Onwer not registered")

    data = {"name": name}
    response = requests.delete(f"{SERVER_URI}/api/owners", json=data)

    if response.status_code == 201:
        os.remove(CONFIG_PATH)
        click.echo(f"Onwer {response.text} added")
    else:
        click.echo(f"Error inserting owner: {response.text}")


@cli.command()
@click.argument("name")
@click.argument("picture")
def upload(name, picture):
    try:
        owner = Owner.load(CONFIG_PATH)
    except FileNotFoundError:
        click.echo("Not configured, run the register command")
        sys.exit()

    if not os.path.exists(picture):
        click.echo("Invalid picture")
        sys.exit()

    files = {"face": open(picture, "rb")}
    response = requests.put(f"{SERVER_URI}/api/{owner.name}/users/{name}", files=files)

    if response.status_code == 201:
        click.echo(f"User {name} registered")
    else:
        click.echo(f"Error uploading user: {response.text}")


@cli.command()
@click.argument("name")
def delete(name):
    try:
        owner = Owner.load(CONFIG_PATH)
    except FileNotFoundError:
        click.echo("Not configured, run the register command")
        sys.exit()

    response = requests.delete(f"{SERVER_URI}/api/{owner.name}/users/{name}")

    if response.status_code == 204:
        click.echo(f"User {name} deleted")
    else:
        click.echo(f"Error deleting user: {response.text}")


@cli.command()
@click.argument("name")
@click.argument("picture")
def authenticate(name, picture):
    try:
        owner = Owner.load(CONFIG_PATH)
    except FileNotFoundError:
        click.echo("Not configured, run the register command")
        sys.exit()

    if not os.path.exists(picture):
        click.echo("Invalid picture")
        sys.exit()

    files = {"face": open(picture, "rb")}
    response = requests.post(f"{SERVER_URI}/api/{owner.name}/auth/{name}", files=files)

    if response.status_code == 200:
        distance = response.json()["distance"]
        dec_dist = owner.decrypt(distance)
        if dec_dist < DISTANCE_THRESH:
            click.echo("User Confirmed!")
        else:
            click.echo("User not Confirmed!")
    else:
        click.echo(f"Error fetching user: {response.text}")


@cli.command()
@click.argument("picture")
def recognize(picture):
    try:
        owner = Owner.load(CONFIG_PATH)
    except FileNotFoundError:
        click.echo("Not configured, run the register command")
        sys.exit()

    if not os.path.exists(picture):
        click.echo("Invalid picture")
        sys.exit()

    files = {"face": open(picture, "rb")}
    response = requests.post(f"{SERVER_URI}/api/{owner.name}/recognition", files=files)

    if response.status_code == 200:
        distances = response.json()["distances"]
        if len(distances) < 1:
            click.echo("No users found")
            sys.exit()

        dec_dists = [
            {"name": distance["name"], "distance": owner.decrypt(distance["distance"])}
            for distance in distances
        ]
        dec_dists.sort(key=lambda x: x["distance"])

        podium_size = min(len(dec_dists), 3)
        click.echo(
            (
                f"Most likely candidate is {dec_dists[0]['name']}"
                f" (distance: {dec_dists[0]['distance']})"
            )
        )
        if podium_size > 1:
            click.echo("  Other likely candidates:")
            for candidate in dec_dists[1:podium_size]:
                click.echo(
                    f"   - {candidate['name']} (distance: {candidate['distance']})"
                )
    else:
        click.echo(f"Error fetching user: {response.text}")
