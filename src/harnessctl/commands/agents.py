import typer
from rich.console import Console
from rich.tree import Tree

console = Console()

agents_app = typer.Typer(help="Manage and view agent topology.")


@agents_app.command(name="show")
def show_cmd(ctx: typer.Context):
    """Render the agent topology as a tree."""
    spec = ctx.obj.spec

    hubs = [n for n, a in spec.agents.items() if a.role.value == "hub"]
    if not hubs:
        console.print("[red]No hub agent defined.[/red]")
        return

    hub_name = hubs[0]
    hub_agent = spec.agents[hub_name]

    tree = Tree(f"[bold cyan]Hub: {hub_name}[/bold cyan] ({hub_agent.tier})")

    def add_delegates(parent_node, agent_name):
        agent = spec.agents[agent_name]
        for delegate in agent.can_delegate:
            if delegate not in spec.agents:
                parent_node.add(f"[red]Undefined: {delegate}[/red]")
                continue

            d_agent = spec.agents[delegate]
            label = f"[yellow]Worker: {delegate}[/yellow] ({d_agent.tier})"
            if d_agent.delegate_via == "cli":
                label += " [magenta](via CLI)[/magenta]"

            child_node = parent_node.add(label)
            add_delegates(child_node, delegate)

    add_delegates(tree, hub_name)
    console.print(tree)
