# multicommand.py -- A multi-command CLI example for Click.
#
# This example demonstrates:
#   - A command group with two subcommands (greet and count)
#   - A shared option (--verbose) declared on the group
#   - An argument with a non-string type (INT)
#   - An option read from an environment variable (LOG_LEVEL)
#
# How to run:
#
#   $ python multicommand.py --help
#   $ python multicommand.py greet Alice
#   $ python multicommand.py --verbose greet --greeting Hi Alice
#   $ LOG_LEVEL=debug python multicommand.py count 5
#
# Expected --help output:
#
#   Usage: multicommand.py [OPTIONS] COMMAND [ARGS]...
#
#     A sample multi-command CLI that demonstrates groups, shared options, typed
#     arguments, and environment variable options.
#
#   Options:
#     --verbose  Enable verbose output.
#     --help     Show this message and exit.
#
#   Commands:
#     count  Count from 1 to N.
#     greet  Greet a user by name.

import click


@click.group()
@click.option("--verbose", is_flag=True, help="Enable verbose output.")
@click.pass_context
def cli(ctx, verbose):
    """A sample multi-command CLI that demonstrates groups, shared options,
    typed arguments, and environment variable options.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@cli.command()
@click.argument("name")
@click.option("--greeting", default="Hello", help="Word to use for the greeting.")
@click.option(
    "--log-level",
    envvar="LOG_LEVEL",
    default="info",
    help="Set the log level (reads LOG_LEVEL env var).",
)
@click.pass_context
def greet(ctx, name, greeting, log_level):
    """Greet a user by name."""
    verbose = ctx.obj["verbose"]
    if verbose:
        click.echo(f"[verbose] log_level={log_level}")
    click.echo(f"{greeting}, {name}!")


@cli.command()
@click.argument("n", type=int)
@click.option(
    "--log-level",
    envvar="LOG_LEVEL",
    default="info",
    help="Set the log level (reads LOG_LEVEL env var).",
)
@click.pass_context
def count(ctx, n, log_level):
    """Count from 1 to N."""
    verbose = ctx.obj["verbose"]
    if verbose:
        click.echo(f"[verbose] log_level={log_level}")
    for i in range(1, n + 1):
        click.echo(i)


if __name__ == "__main__":
    cli()
