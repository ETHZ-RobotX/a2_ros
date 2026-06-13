#!/usr/bin/env python3
import argparse
import os

from jinja2 import Environment, FileSystemLoader


def main():
    """
    Renders the Zenoh config template with the specified router IP
    """
    parser = argparse.ArgumentParser(description="Generate Zenoh session config from template")

    parser.add_argument("--output-file", type=str, required=True, help="Where to write the rendered config file")
    parser.add_argument("--router-ip", type=str, default="127.0.0.1", help="IP address of the Zenoh router")
    parser.add_argument("--profile", type=str, choices=["sim", "robot"], default="sim",
                        help="Which config profile to render (sim or robot)")

    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(script_dir, "..", "config", "zenoh")
    env = Environment(loader=FileSystemLoader(template_dir))

    template = env.get_template(f"zenoh-session-config.{args.profile}.json5.jinja2")

    output = template.render({"router_ip": args.router_ip})

    with open(args.output_file, "w") as f:
        f.write(output)


if __name__ == "__main__":
    main()
