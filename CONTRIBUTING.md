# Contributing

## Requirements

The development environment is managed by [Nix](https://nixos.org/download/).
This is the only system dependency you need to install.
It supports Linux, macOS, and Windows (WSL2).

## Entering the development environment

To enter the development environment, navigate to the project directory in your terminal and run:

```shell
nix-shell
```

The first time you run this command, it will take a longer while to download necessary dependencies.
Subsequent runs will be faster.

The opened shell is isolated from your system environment.
Because of that, you can't simply start VSCode/PyCharm from your desktop.
You must start it from within this shell:

```shell
nix-shell
# ... waiting for the nix shell to load ...
# VSCode:
code .
# PyCharm Community:
pycharm-community . >/dev/null 2>&1 &
# PyCharm Professional:
pycharm-professional . >/dev/null 2>&1 &
```

## Automating nix-shell startup

You can install [direnv](https://direnv.net/) to automatically load the nix-shell
when you enter the project directory.
This also enables shell caching that speeds up subsequent startups.
The `.envrc` file is already configured.

## Editing the development environment

The environment is defined within the `shell.nix` file.
It allows you to install system packages, write custom scripts, and change nix-shell startup behavior.
For an available list of packages, see <https://search.nixos.org/packages>.

## Managing Python packages

The Python environment is managed by [uv](https://docs.astral.sh/uv/). Here's a short cheat sheet on using it:

```shell
# Install a package:
uv add <package>
uv add <dev-package> --dev
# Remove a package:
uv remove <package>
# Update all packages:
uv sync -U
```

## Authorizing with S3

Boto3 supports
a [wide range of authentication methods](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#configuring-credentials).
We also provide an additional convenience method:
place your `credentials.json` file in the project directory (the same folder as `shell.nix`).
The credentials will be automatically loaded when nix-shell is run.
