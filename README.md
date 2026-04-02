# AI Maze Solver & Pathfinding Visualizer

## Overview

The AI Maze Solver & Pathfinding Visualizer is an interactive application that demonstrates classical search algorithms used in artificial intelligence for pathfinding problems.

The project allows users to create a custom maze environment and visualize how different algorithms explore the search space and find the optimal path between a start and goal node.

---

## Objectives

* To understand and implement graph search algorithms
* To visualize how algorithms explore nodes in real time
* To compare performance of different search strategies
* To build an interactive tool for learning AI concepts

---

## Features

* 🟩 Interactive grid-based maze (20×20)
* 🧱 Wall creation using mouse clicks
* 🟢 Start node selection
* 🔴 Goal node selection
* 🔵 Visualization of explored nodes
* 🟡 Highlighting of final shortest path
* ▶️ Algorithm execution via on-screen buttons
* 📊 Performance metrics:

  * Nodes expanded
  * Path length
  * Execution time

---

## Algorithms Implemented

### 1. Breadth-First Search (BFS)

* Explores nodes level by level
* Guarantees shortest path in an unweighted graph
* Expands nodes uniformly in all directions

### 2. A* Search Algorithm

* Uses heuristic-based search
* Formula: `f(n) = g(n) + h(n)`
* Heuristic used: Manhattan Distance
* More efficient than BFS in most cases

---

## Tech Stack

* **Language:** Python 3.11
* **Library:** Pygame
* **Concepts Used:**

  * Graph Theory
  * Search Algorithms
  * Heuristic Functions
  * Event-driven Programming

---

## Installation & Setup

### 1. Clone the repository

```bash
git clone <your-repo-link>
cd AI_Maze_Project
```

### 2. Install dependencies

```bash
pip install pygame
```

### 3. Run the application

```bash
python main.py
```

---

## How to Use

### Maze Setup

* Left click → Create walls
* Press **S** → Set Start node
* Press **G** → Set Goal node

### Run Algorithms

* Click **Run BFS** → Execute Breadth-First Search
* Click **Run A*** → Execute A* Search

---

## Output Visualization

* 🔵 Blue cells → Explored nodes
* 🟡 Yellow cells → Final shortest path
* 🟩 Green → Start node
* 🔴 Red → Goal node

---

## Performance Analysis

The application displays:

* Number of nodes explored
* Time taken to compute the path
* Length of the final path

This allows comparison between uninformed and informed search strategies.

---

## Key Learnings

* Difference between uninformed and informed search
* Importance of heuristics in optimization
* Trade-off between completeness and efficiency
* Visualization of algorithm behavior in real-time

---

## Limitations

* Grid size is fixed (20×20)
* Only 4-directional movement allowed
* No weighted edges
* Limited to BFS and A* (extendable)

---

## Future Improvements

* Add DFS and Dijkstra’s Algorithm
* Implement diagonal movement
* Add weighted grids
* Animate step-by-step execution
* Add random maze generation
* Speed control for visualization

---

## Executable Version

The project can be packaged into a standalone `.exe` file using PyInstaller for easy distribution without requiring Python installation.

---

## Author

* Konishko Majumdar

---

## License

This project is for academic and educational purposes.
