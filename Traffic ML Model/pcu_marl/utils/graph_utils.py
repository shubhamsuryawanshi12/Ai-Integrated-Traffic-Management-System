"""
Graph utilities for PCU-MARL++.

Helper functions for junction adjacency and distance calculations.
"""

from typing import List, Tuple, Optional
import numpy as np
import networkx as nx


def get_adjacent_junctions(
    jid: int,
    n_rows: int = 3,
    n_cols: int = 4,
) -> List[int]:
    """
    Get adjacent junction IDs.
    
    Args:
        jid: Junction ID
        n_rows: Number of rows
        n_cols: Number of columns
        
    Returns:
        List of adjacent junction IDs
    """
    row = jid // n_cols
    col = jid % n_cols
    
    adjacent = []
    
    # North (up)
    if row > 0:
        adjacent.append((row - 1) * n_cols + col)
    
    # South (down)
    if row < n_rows - 1:
        adjacent.append((row + 1) * n_cols + col)
    
    # East (right)
    if col < n_cols - 1:
        adjacent.append(row * n_cols + (col + 1))
    
    # West (left)
    if col > 0:
        adjacent.append(row * n_cols + (col - 1))
    
    return adjacent


def get_junction_grid_position(
    jid: int,
    n_cols: int = 4,
) -> Tuple[int, int]:
    """
    Get (row, col) position of junction.
    
    Args:
        jid: Junction ID
        n_cols: Number of columns
        
    Returns:
        (row, col) tuple
    """
    return jid // n_cols, jid % n_cols


def get_junction_id(
    row: int,
    col: int,
    n_cols: int = 4,
) -> int:
    """
    Get junction ID from (row, col).
    
    Args:
        row: Row index
        col: Column index
        n_cols: Number of columns
        
    Returns:
        Junction ID
    """
    return row * n_cols + col


def compute_distance_matrix(
    positions: List[Tuple[float, float]],
) -> np.ndarray:
    """
    Compute pairwise distance matrix.
    
    Args:
        positions: List of (x, y) positions
        
    Returns:
        Distance matrix
    """
    n = len(positions)
    distances = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i + 1, n):
            dist = np.sqrt(
                (positions[i][0] - positions[j][0]) ** 2 +
                (positions[i][1] - positions[j][1]) ** 2
            )
            distances[i, j] = dist
            distances[j, i] = dist
    
    return distances


def compute_adjacency_from_distance(
    positions: List[Tuple[float, float]],
    threshold: float = 800.0,
) -> np.ndarray:
    """
    Compute adjacency matrix from positions based on distance threshold.
    
    Args:
        positions: List of (x, y) positions
        threshold: Distance threshold in meters
        
    Returns:
        Adjacency matrix
    """
    distances = compute_distance_matrix(positions)
    adj = (distances > 0) & (distances <= threshold)
    return adj.astype(np.float32)


def build_road_graph(
    n_rows: int = 3,
    n_cols: int = 4,
    spacing: float = 800.0,
) -> nx.DiGraph:
    """
    Build road network graph.
    
    Args:
        n_rows: Number of rows
        n_cols: Number of columns
        spacing: Junction spacing in meters
        
    Returns:
        NetworkX DiGraph
    """
    G = nx.DiGraph()
    
    # Add nodes
    for row in range(n_rows):
        for col in range(n_cols):
            jid = row * n_cols + col
            x = col * spacing
            y = row * spacing
            G.add_node(jid, pos=(x, y), row=row, col=col)
    
    # Add edges
    for row in range(n_rows):
        for col in range(n_cols):
            jid = row * n_cols + col
            
            # Right neighbor
            if col < n_cols - 1:
                neighbor = row * n_cols + (col + 1)
                G.add_edge(jid, neighbor, weight=spacing)
                G.add_edge(neighbor, jid, weight=spacing)
            
            # Bottom neighbor
            if row < n_rows - 1:
                neighbor = (row + 1) * n_cols + col
                G.add_edge(jid, neighbor, weight=spacing)
                G.add_edge(neighbor, jid, weight=spacing)
    
    return G


def find_shortest_path(
    G: nx.Graph,
    start: int,
    end: int,
) -> List[int]:
    """
    Find shortest path between junctions.
    
    Args:
        G: Road network graph
        start: Start junction
        end: End junction
        
    Returns:
        List of junction IDs in path
    """
    try:
        return nx.shortest_path(G, start, end)
    except nx.NetworkXNoPath:
        return []


def compute_shortest_path_matrix(
    G: nx.Graph,
    n_junctions: int,
) -> np.ndarray:
    """
    Compute shortest path distance matrix.
    
    Args:
        G: Road network graph
        n_junctions: Number of junctions
        
    Returns:
        Shortest path distance matrix
    """
    distances = np.zeros((n_junctions, n_junctions))
    
    for i in range(n_junctions):
        for j in range(n_junctions):
            try:
                path = nx.shortest_path(G, i, j, weight='weight')
                dist = sum(G[path[k]][path[k+1]]['weight'] for k in range(len(path)-1))
                distances[i, j] = dist
            except nx.NetworkXNoPath:
                distances[i, j] = float('inf')
    
    return distances


def get_neighborhood(
    jid: int,
    adjacency_matrix: np.ndarray,
    radius: int = 1,
) -> List[int]:
    """
    Get neighborhood of a junction.
    
    Args:
        jid: Junction ID
        adjacency_matrix: Adjacency matrix
        radius: Neighborhood radius
        
    Returns:
        List of neighboring junction IDs
    """
    neighbors = [jid]
    current = {jid}
    
    for _ in range(radius):
        next_neighbors = set()
        for n in current:
            for j in range(len(adjacency_matrix)):
                if adjacency_matrix[n, j] > 0 and j not in neighbors:
                    next_neighbors.add(j)
        neighbors.extend(list(next_neighbors))
        current = next_neighbors
    
    return neighbors


def normalize_adjacency(adj: np.ndarray) -> np.ndarray:
    """
    Normalize adjacency matrix (symmetric normalization).
    
    Args:
        adj: Adjacency matrix
        
    Returns:
        Normalized adjacency matrix
    """
    # Degree matrix
    degree = np.sum(adj, axis=1)
    degree_inv_sqrt = np.power(degree, -0.5)
    degree_inv_sqrt[np.isinf(degree_inv_sqrt)] = 0
    
    # Normalized
    D_inv_sqrt = np.diag(degree_inv_sqrt)
    normalized = D_inv_sqrt @ adj @ D_inv_sqrt
    
    return normalized
