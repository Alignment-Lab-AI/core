"""Generate mypy config."""
from __future__ import annotations

import configparser
import io
import os
from pathlib import Path
from typing import Final

from homeassistant.const import REQUIRED_PYTHON_VER

from .model import Config, Integration

# Modules which have type hints which known to be broken.
# If you are an author of component listed here, please fix these errors and
# remove your component from this list to enable type checks.
# Do your best to not add anything new here.
IGNORED_MODULES: Final[list[str]] = [
    "homeassistant.components.blueprint.*",
    "homeassistant.components.cloud.*",
    "homeassistant.components.config.*",
    "homeassistant.components.conversation.*",
    "homeassistant.components.deconz.*",
    "homeassistant.components.demo.*",
    "homeassistant.components.denonavr.*",
    "homeassistant.components.evohome.*",
    "homeassistant.components.fireservicerota.*",
    "homeassistant.components.firmata.*",
    "homeassistant.components.freebox.*",
    "homeassistant.components.geniushub.*",
    "homeassistant.components.google_assistant.*",
    "homeassistant.components.gree.*",
    "homeassistant.components.harmony.*",
    "homeassistant.components.hassio.*",
    "homeassistant.components.here_travel_time.*",
    "homeassistant.components.home_plus_control.*",
    "homeassistant.components.homekit.*",
    "homeassistant.components.homekit_controller.*",
    "homeassistant.components.honeywell.*",
    "homeassistant.components.icloud.*",
    "homeassistant.components.influxdb.*",
    "homeassistant.components.input_datetime.*",
    "homeassistant.components.isy994.*",
    "homeassistant.components.izone.*",
    "homeassistant.components.konnected.*",
    "homeassistant.components.kostal_plenticore.*",
    "homeassistant.components.litterrobot.*",
    "homeassistant.components.lovelace.*",
    "homeassistant.components.lutron_caseta.*",
    "homeassistant.components.lyric.*",
    "homeassistant.components.melcloud.*",
    "homeassistant.components.meteo_france.*",
    "homeassistant.components.minecraft_server.*",
    "homeassistant.components.mobile_app.*",
    "homeassistant.components.nest.legacy.*",
    "homeassistant.components.netgear.*",
    "homeassistant.components.nilu.*",
    "homeassistant.components.nzbget.*",
    "homeassistant.components.omnilogic.*",
    "homeassistant.components.onvif.*",
    "homeassistant.components.ozw.*",
    "homeassistant.components.philips_js.*",
    "homeassistant.components.plex.*",
    "homeassistant.components.profiler.*",
    "homeassistant.components.ring.*",
    "homeassistant.components.solaredge.*",
    "homeassistant.components.sonos.*",
    "homeassistant.components.spotify.*",
    "homeassistant.components.system_health.*",
    "homeassistant.components.telegram_bot.*",
    "homeassistant.components.template.*",
    "homeassistant.components.toon.*",
    "homeassistant.components.unifi.*",
    "homeassistant.components.upnp.*",
    "homeassistant.components.vizio.*",
    "homeassistant.components.withings.*",
    "homeassistant.components.xbox.*",
    "homeassistant.components.xiaomi_aqara.*",
    "homeassistant.components.xiaomi_miio.*",
    "homeassistant.components.yeelight.*",
    "homeassistant.components.zha.*",
    "homeassistant.components.zwave.*",
]

HEADER: Final = """
# Automatically generated by hassfest.
#
# To update, run python3 -m script.hassfest

""".lstrip()

GENERAL_SETTINGS: Final[dict[str, str]] = {
    "python_version": ".".join(str(x) for x in REQUIRED_PYTHON_VER[:2]),
    "show_error_codes": "true",
    "follow_imports": "silent",
    # Enable some checks globally.
    "ignore_missing_imports": "true",
    "strict_equality": "true",
    "warn_incomplete_stub": "true",
    "warn_redundant_casts": "true",
    "warn_unused_configs": "true",
    "warn_unused_ignores": "true",
}

# This is basically the list of checks which is enabled for "strict=true".
# "strict=false" in config files does not turn strict settings off if they've been
# set in a more general section (it instead means as if strict was not specified at
# all), so we need to list all checks manually to be able to flip them wholesale.
STRICT_SETTINGS: Final[list[str]] = [
    "check_untyped_defs",
    "disallow_incomplete_defs",
    "disallow_subclassing_any",
    "disallow_untyped_calls",
    "disallow_untyped_decorators",
    "disallow_untyped_defs",
    "no_implicit_optional",
    "warn_return_any",
    "warn_unreachable",
    # TODO: turn these on, address issues
    # "disallow_any_generics",
    # "no_implicit_reexport",
]

# Strict settings are already applied for core files.
# To enable granular typing, add additional settings if core files are given.
STRICT_SETTINGS_CORE: Final[list[str]] = [
    "disallow_any_generics",
]


def generate_and_validate(config: Config) -> str:
    """Validate and generate mypy config."""

    config_path = config.root / ".strict-typing"

    with config_path.open() as fp:
        lines = fp.readlines()

    # Filter empty and commented lines.
    parsed_modules: list[str] = [
        line.strip()
        for line in lines
        if line.strip() != "" and not line.startswith("#")
    ]

    strict_modules: list[str] = []
    strict_core_modules: list[str] = []
    for module in parsed_modules:
        if module.startswith("homeassistant.components"):
            strict_modules.append(module)
        else:
            strict_core_modules.append(module)

    ignored_modules_set: set[str] = set(IGNORED_MODULES)
    for module in strict_modules:
        if (
            not module.startswith("homeassistant.components.")
            and module != "homeassistant.components"
        ):
            config.add_error(
                "mypy_config", f"Only components should be added: {module}"
            )
        if module in ignored_modules_set:
            config.add_error(
                "mypy_config", f"Module '{module}' is in ignored list in mypy_config.py"
            )

    # Validate that all modules exist.
    all_modules = strict_modules + strict_core_modules + IGNORED_MODULES
    for module in all_modules:
        if module.endswith(".*"):
            module_path = Path(module[:-2].replace(".", os.path.sep))
            if not module_path.is_dir():
                config.add_error("mypy_config", f"Module '{module} is not a folder")
        else:
            module = module.replace(".", os.path.sep)
            module_path = Path(f"{module}.py")
            if module_path.is_file():
                continue
            module_path = Path(module) / "__init__.py"
            if not module_path.is_file():
                config.add_error("mypy_config", f"Module '{module} doesn't exist")

    # Don't generate mypy.ini if there're errors found because it will likely crash.
    if any(err.plugin == "mypy_config" for err in config.errors):
        return ""

    mypy_config = configparser.ConfigParser()

    general_section = "mypy"
    mypy_config.add_section(general_section)
    for key, value in GENERAL_SETTINGS.items():
        mypy_config.set(general_section, key, value)
    for key in STRICT_SETTINGS:
        mypy_config.set(general_section, key, "true")

    for core_module in strict_core_modules:
        core_section = f"mypy-{core_module}"
        mypy_config.add_section(core_section)
        for key in STRICT_SETTINGS_CORE:
            mypy_config.set(core_section, key, "true")

    # By default strict checks are disabled for components.
    components_section = "mypy-homeassistant.components.*"
    mypy_config.add_section(components_section)
    for key in STRICT_SETTINGS:
        mypy_config.set(components_section, key, "false")

    for strict_module in strict_modules:
        strict_section = f"mypy-{strict_module}"
        mypy_config.add_section(strict_section)
        for key in STRICT_SETTINGS:
            mypy_config.set(strict_section, key, "true")

    # Disable strict checks for tests
    tests_section = "mypy-tests.*"
    mypy_config.add_section(tests_section)
    for key in STRICT_SETTINGS:
        mypy_config.set(tests_section, key, "false")

    for ignored_module in IGNORED_MODULES:
        ignored_section = f"mypy-{ignored_module}"
        mypy_config.add_section(ignored_section)
        mypy_config.set(ignored_section, "ignore_errors", "true")

    with io.StringIO() as fp:
        mypy_config.write(fp)
        fp.seek(0)
        return HEADER + fp.read().strip()


def validate(integrations: dict[str, Integration], config: Config) -> None:
    """Validate mypy config."""
    config_path = config.root / "mypy.ini"
    config.cache["mypy_config"] = content = generate_and_validate(config)

    if any(err.plugin == "mypy_config" for err in config.errors):
        return

    with open(str(config_path)) as fp:
        if fp.read().strip() != content:
            config.add_error(
                "mypy_config",
                "File mypy.ini is not up to date. Run python3 -m script.hassfest",
                fixable=True,
            )


def generate(integrations: dict[str, Integration], config: Config) -> None:
    """Generate mypy config."""
    config_path = config.root / "mypy.ini"
    with open(str(config_path), "w") as fp:
        fp.write(f"{config.cache['mypy_config']}\n")
