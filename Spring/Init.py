import importlib

_MODULE_NAME = "SpringTest"

try:
    SpringTest = importlib.import_module(_MODULE_NAME)
except ImportError as exc:
    raise ImportError(
        f"Unable to import the {_MODULE_NAME} module. Ensure the C++ bindings are built."
    ) from exc


def make_point(x, y):
    """Create a gp_Pnt2d via the C++ helper and return the coordinates."""
    return SpringTest.make_point(x, y)


def describe_point(x, y):
    """Return a human readable string for a gp_Pnt2d."""
    return SpringTest.describe_point(x, y)
