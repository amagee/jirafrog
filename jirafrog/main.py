"""
Extremely basic curses-based Jira UI
"""

import curses
import getpass
import os
import webbrowser

import appdirs
from blessed import Terminal
from jira import JIRA
import toml


def main():
    server, username, token = get_config()
    term = Terminal()
    jira = JIRA(server=server, basic_auth=(username, token))
    issues = jira.search_issues("assignee = currentUser() and sprint in openSprints()")

    def draw_menu(issues, ix):
        print(term.clear)
        print(term.move_xy(0, 0))
        for i, issue in enumerate(issues):
            summary = issue.fields.summary
            status = issue.fields.status
            if status.name == "In Progress":
                color = "cadetblue"
            else:
                color = "springgreen4"

            if i == ix:
                color = color + "_on_azure3"
            print(getattr(term, color)(f"{issue.key:15} {summary[0:50]:50} {status.name:10}"))

        print(term.move_yx(20, 0))
        issue = issues[ix]
        summary = issue.fields.summary
        heading = f"{issue.key}: {issue.fields.summary}"
        print(term.mistyrose(term.bold(heading)))
        print(term.mistyrose(term.bold("=" * len(heading))))
        print("")

        description = issues[ix].fields.description or "(No description)"
        for i, line in enumerate(term.wrap(description)):
            print(term.mistyrose(line))
            if 23 + i >= term.height - 8:
                break

    def do_menu():
        ix = 0
        while True:
            draw_menu(issues, ix)
            with term.cbreak(), term.hidden_cursor():
                inp = term.inkey()
                if inp.code == curses.KEY_UP:
                    ix = max(ix - 1, 0)
                elif inp.code == curses.KEY_DOWN:
                    ix = min(ix + 1, len(issues) - 1)
                elif inp.code == curses.KEY_ENTER:
                    webbrowser.open(f"{server}/browse/{issues[ix].key}")
                elif inp == "q":
                    break

    do_menu()


def get_config():
    config_dir = appdirs.user_config_dir("jirafrog")
    config_path = os.path.join(config_dir, "config.toml")

    if os.path.exists(config_path):
        data = toml.loads(open(config_path).read())
        server = data['server']
        username = data['username']
        token = data['token']
    else:
        print("Looks like jirafrog has not been configured yet. Let's get started:")
        server = input("Enter your server URL: ")
        username = input("Enter your username: ")
        token = getpass.getpass(prompt="Enter your API key: ")

        os.makedirs(config_dir, exist_ok=True)
        with open(config_path, "w+") as f:
            f.write(toml.dumps({
                "server": server,
                "username": username,
                "token": token
            }))
        print(f"Wrote config to {config_path}")

    return (server, username, token)


if __name__ == "__main__":
    main()


