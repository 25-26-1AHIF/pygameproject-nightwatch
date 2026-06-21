import math
from collections import deque
from game_variables.game_variables import GameVariables

NAV_NODES = GameVariables.NAV_NODES
NAV_EDGES = GameVariables.NAV_EDGES


def vec_len(dx: float, dy: float) -> float:
    """Berechnet die Länge eines 2D-Vektors."""
    return math.sqrt(dx * dx + dy * dy)


def vec_norm(dx: float, dy: float) -> tuple[float, float]:
    """Normalisiert einen Vektor auf Länge 1."""
    length = vec_len(dx, dy)
    if length == 0:
        return (0.0, 0.0)
    return (dx / length, dy / length)


def dist(ax: float, ay: float, bx: float, by: float) -> float:
    """Euklidische Distanz zwischen zwei Punkten."""
    return vec_len(bx - ax, by - ay)


def angle_between(ax: float, ay: float, bx: float, by: float) -> float:
    """Winkel in Grad von Punkt A zu Punkt B."""
    return math.degrees(math.atan2(by - ay, bx - ax)) % 360


def angle_diff(a: float, b: float) -> float:
    """Kürzeste Winkeldifferenz zwischen zwei Winkeln (in Grad, -180..180)."""
    d = (b - a) % 360
    if d > 180:
        d -= 360
    return d


def clamp(value: float, lo: float, hi: float) -> float:
    """Begrenzt einen Wert auf den Bereich [lo, hi]."""
    return max(lo, min(hi, value))


def lerp(a: float, b: float, t: float) -> float:
    """Lineare Interpolation zwischen a und b (t zwischen 0 und 1)."""
    return a + (b - a) * clamp(t, 0.0, 1.0)


def _build_adj() -> dict[int, list[int]]:
    """Erstellt eine Adjazenzliste aus den NAV_EDGES."""
    adj: dict[int, list[int]] = {nid: [] for nid in NAV_NODES}
    for a, b in NAV_EDGES:
        adj[a].append(b)
        adj[b].append(a)
    return adj


_ADJ: dict[int, list[int]] = _build_adj()


def nearest_node(x: float, y: float) -> int:
    """Findet den nächsten Navigationspunkt zur gegebenen Weltposition."""
    best_id = 0
    best_d  = float("inf")
    for nid, (nx, ny) in NAV_NODES.items():
        d = dist(x, y, nx, ny)
        if d < best_d:
            best_d  = d
            best_id = nid
    return best_id


# KI CODE ANFANG
# Claude Opus 4.8
# Prompt: "Implementiere den BFS-Algorithmus (Breadth-First Search) für ein
# Navigationsgraph-System in einem Pygame-Spiel. Der Graph ist als Adjazenzliste
# gegeben. Gibt den kürzesten Pfad als Liste von Knoten-IDs zurück, oder eine
# leere Liste wenn kein Pfad existiert. Außerdem eine next_waypoint()-Funktion
# die die Weltkoordinaten des nächsten Zwischenziels liefert."
def bfs_path(start_id: int, goal_id: int) -> list[int]:
    """Berechnet den kürzesten Pfad via BFS."""
    if start_id == goal_id:
        return [start_id]

    visited: dict[int, int | None] = {start_id: None}
    queue: deque[int] = deque([start_id])

    while queue:
        current = queue.popleft()
        if current == goal_id:
            path: list[int] = []
            node: int | None = goal_id
            while node is not None:
                path.append(node)
                node = visited[node]
            path.reverse()
            return path
        for neighbor in _ADJ[current]:
            if neighbor not in visited:
                visited[neighbor] = current
                queue.append(neighbor)

    return []


def next_waypoint(monster_x: float, monster_y: float,
                  target_x: float, target_y: float) -> tuple[float, float]:
    """Gibt die Weltkoordinaten des nächsten BFS-Zwischenziels zurück."""
    start = nearest_node(monster_x, monster_y)
    goal  = nearest_node(target_x,  target_y)
    path  = bfs_path(start, goal)

    if len(path) < 2:
        return (target_x, target_y)

    next_nid = path[1]
    return NAV_NODES[next_nid]
# KI CODE ENDE
