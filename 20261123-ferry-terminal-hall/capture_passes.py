"""Camera passes shared by print development and harbour registration."""

GEOMETRY_GUIDES = (("normal", ".normal.png"), ("albedo", ".albedo.png"))
GUIDE_PASSES = tuple(suffix for _, suffix in GEOMETRY_GUIDES)
HALL_PASSES = (
    ".glass.png", ".room.png", ".panes.npz", ".marks.json",
    ".concrete.npz", ".finishes.npz", ".drawdown.npz", ".berth-concrete.npz",
)
HARBOUR_DEPTH = ".harbour-depth.npz"
LARGE_PASSES = (*GUIDE_PASSES, ".direct.png", HARBOUR_DEPTH)


def print_passes(*, large):
    required = (".png", *HALL_PASSES)
    return required + LARGE_PASSES if large else required


def require_passes(source, suffixes, label):
    paths = [source.with_suffix(suffix) for suffix in suffixes]
    missing = [path.name for path in paths if not path.is_file()]
    if missing:
        raise ValueError(f"{label} is missing camera passes {', '.join(missing)}.")
