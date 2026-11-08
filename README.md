<div align="center"><img src="https://raw.githubusercontent.com/pallets/click/refs/heads/stable/docs/_static/click-name.svg" alt="" height="150"></div>

# Click

Click is a Python package for creating beautiful command line interfaces
in a composable way with as little code as necessary. It's the "Command
Line Interface Creation Kit". It's highly configurable but comes with
sensible defaults out of the box.

It aims to make the process of writing command line tools quick and fun
while also preventing any frustration caused by the inability to
implement an intended CLI API.

Click in three points:

-   Arbitrary nesting of commands
-   Automatic help page generation
-   Supports lazy loading of subcommands at runtime


## A Simple Example

```python
import click

@click.command()
@click.option("--count", default=1, help="Number of greetings.")
@click.option("--name", prompt="Your name", help="The person to greet.")
def hello(count, name):
    """Simple program that greets NAME for a total of COUNT times."""
    for _ in range(count):
        click.echo(f"Hello, {name}!")

if __name__ == '__main__':
    hello()
```

```
$ python hello.py --count=3
Your name: Click
Hello, Click!
Hello, Click!
Hello, Click!
```


## Donate

The Pallets organization develops and supports Click and other popular
packages. In order to grow the community of contributors and users, and
allow the maintainers to devote more time to the projects, [please
donate today][].

[please donate today]: https://palletsprojects.com/donate

## Contributing

See our [detailed contributing documentation][contrib] for many ways to
contribute, including reporting issues, requesting features, asking or answering
questions, and making PRs.

[contrib]: https://palletsprojects.com/contributing/

## Secret scanning

The `secret-scan` GitHub Actions workflow runs [gitleaks](https://github.com/gitleaks/gitleaks)
over the full git history to detect exposed secrets and credentials.

- Hourly (`0 * * * *`), on pull requests, on pushes to `main`, and on manual dispatch.
- Weekly (`0 6 * * 1`, Monday 06:00 UTC): the same scan, plus a summary in the run
  and a report artifact retained for 90 days for the weekly security review.

Reports are redacted. To triage a finding, download the `gitleaks-report` artifact,
locate the file and commit, and revoke and rotate the credential first. Removing it from
history is secondary. If it is a confirmed false positive, add a documented entry to
`.gitleaks.toml`.
