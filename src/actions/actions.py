import json                                                                                                             
import sys

from charms.layer.basic import activate_venv

activate_venv()

from charmhelpers.core.hookenv import action_fail

def collect():
    return "Success"

def cleanup():
    return "Success"

ACTIONS = {
    "collect": collect,
    "cleanup": cleanup,
}

def main(args):
    """Run assigned action."""
    action_name = os.path.basename(args[0])
    try:
        action = ACTIONS[action_name]
    except KeyError:
        return "Action {} undefined".format(action_name)
    else:
        try:
            action(args)
        except Exception as e:
            action_fail(str(e))


if __name__ == "__main__":
    sys.exit(main(sys.argv))

