import typer
import asyncio
import httpx
import webbrowser
import time
from typing import Optional
from rich.console import Console
from rich.table import Table
from harnessctl.providers.manager import SecretsManager

console = Console()
auth_app = typer.Typer(help="Manage provider authentication.")
secrets_manager = SecretsManager()

# Common providers and their associated environment variables + Key generation URLs
PROVIDERS = {
    "github": {
        "env": "GITHUB_TOKEN",
        "url": "https://github.com/settings/tokens",
        "help": "GitHub Personal Access Token or Browser Login",
        "type": "oauth",
    },
    "openrouter": {
        "env": "OPENROUTER_API_KEY",
        "url": "https://openrouter.ai/keys",
        "help": "OpenRouter API Key",
        "type": "apikey",
    },
    "openai": {
        "env": "OPENAI_API_KEY",
        "url": "https://platform.openai.com/api-keys",
        "help": "OpenAI API Key",
        "type": "apikey",
    },
    "anthropic": {
        "env": "ANTHROPIC_API_KEY",
        "url": "https://console.anthropic.com/settings/keys",
        "help": "Anthropic API Key",
        "type": "apikey",
    },
    "google": {
        "env": "GOOGLE_API_KEY",
        "url": "https://aistudio.google.com/app/apikey",
        "help": "Google AI Studio API Key",
        "type": "apikey",
    },
    "groq": {
        "env": "GROQ_API_KEY",
        "url": "https://console.groq.com/keys",
        "help": "Groq API Key",
        "type": "apikey",
    },
}

# GitHub Device Flow Constants
GITHUB_CLIENT_ID = "Iv1.b507a08c87ecfe98"  # VS Code Client ID
GITHUB_DEVICE_CODE_URL = "https://github.com/login/device/code"
GITHUB_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"


async def github_device_flow():
    """Implements GitHub Device Flow for browser-based login."""
    async with httpx.AsyncClient() as client:
        # 1. Request device code
        response = await client.post(
            GITHUB_DEVICE_CODE_URL,
            json={
                "client_id": GITHUB_CLIENT_ID,
                "scope": "read:user repo",  # repo might be needed for some marketplace features
            },
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        data = response.json()

        device_code = data["device_code"]
        user_code = data["user_code"]
        verification_uri = data["verification_uri"]
        interval = data["interval"]
        expires_in = data["expires_in"]

        console.print("\n[bold]GitHub Authentication Required[/bold]")
        console.print(f"1. Copy this code: [bold cyan]{user_code}[/bold cyan]")
        console.print(f"2. Open your browser at: [blue]{verification_uri}[/blue]")

        # Try to open browser automatically
        webbrowser.open(verification_uri)

        console.print(
            f"\n[dim]Waiting for authorization (expires in {expires_in}s)...[/dim]"
        )

        # 2. Poll for access token
        start_time = time.time()
        while time.time() - start_time < expires_in:
            await asyncio.sleep(interval)

            token_response = await client.post(
                GITHUB_ACCESS_TOKEN_URL,
                json={
                    "client_id": GITHUB_CLIENT_ID,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
                headers={"Accept": "application/json"},
            )

            token_data = token_response.json()

            if "access_token" in token_data:
                return token_data["access_token"]

            error = token_data.get("error")
            if error == "authorization_pending":
                continue
            elif error == "slow_down":
                interval += 5
            elif error == "expired_token":
                console.print(
                    "[red]The device code has expired. Please try again.[/red]"
                )
                return None
            elif error == "access_denied":
                console.print("[red]Access denied by user.[/red]")
                return None
            else:
                console.print(f"[red]Authentication failed: {error}[/red]")
                return None

    return None


@auth_app.command(name="login")
def login(
    provider: str = typer.Argument(
        ..., help="Provider to login to (e.g. github, openrouter)."
    ),
    token: Optional[str] = typer.Option(
        None,
        "--token",
        help="API token/key. If not provided, will prompt or use browser if supported.",
    ),
    browser: bool = typer.Option(
        False, "--browser", help="Force browser-based login/redirect."
    ),
):
    """Store credentials for a provider."""
    provider = provider.lower()
    if provider not in PROVIDERS:
        console.print(f"[red]Unknown provider: {provider}[/red]")
        console.print(f"Supported providers: {', '.join(PROVIDERS.keys())}")
        raise typer.Exit(1)

    info = PROVIDERS[provider]

    # Special handling for GitHub Browser login (Device Flow)
    if provider == "github" and (browser or not token):
        token = asyncio.run(github_device_flow())
        if not token:
            console.print("[red]GitHub login failed or cancelled.[/red]")
            raise typer.Exit(1)
    elif not token:
        # For other providers, if browser is requested or no token, offer to open the URL
        if browser or typer.confirm(
            f"Would you like to open the {provider} API keys page in your browser?",
            default=True,
        ):
            console.print(f"Opening [blue]{info['url']}[/blue]...")
            webbrowser.open(info["url"])

        token = typer.prompt(f"Enter your {provider} token/key", hide_input=True)

    try:
        secrets_manager.set_token(provider, token)

        console.print(f"[green]Successfully logged into {provider}.[/green]")
        console.print(f"[dim]Token stored in {secrets_manager.auth_file}[/dim]")
    except Exception as e:
        console.print(f"[red]Failed to save token: {e}[/red]")


@auth_app.command(name="list")
def list_auth():
    """List providers with active authentication."""
    table = Table(title="Authenticated Providers")
    table.add_column("Provider", style="cyan")
    table.add_column("Status", style="green")

    statuses = secrets_manager.list_providers()
    for provider, is_auth in statuses.items():
        status = "[green]Authenticated[/green]" if is_auth else "[dim]Not Set[/dim]"
        table.add_row(provider, status)

    console.print(table)


@auth_app.command(name="logout")
def logout(provider: str = typer.Argument(..., help="Provider to logout from.")):
    """Remove credentials for a provider."""
    provider = provider.lower()
    try:
        secrets_manager.remove_token(provider)
        console.print(f"[green]Logged out from {provider}.[/green]")
    except Exception as e:
        console.print(f"[red]Failed to remove token: {e}[/red]")
