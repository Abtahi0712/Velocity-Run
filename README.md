# 🚀 Velocity Run

> A 3D endless runner built with OpenGL — survive the corridor, beat the clock, outrun the chaos.

![OpenGL](https://img.shields.io/badge/OpenGL-3D%20Graphics-blue?style=flat-square)
![C++](https://img.shields.io/badge/Language-C%2B%2B-orange?style=flat-square)
![Status](https://img.shields.io/badge/Status-In%20Development-yellow?style=flat-square)

---

## 📖 Overview

**Velocity Run** is a three-dimensional endless runner where the player navigates a procedurally generated corridor filled with hazards, collectibles, and power-ups. The objective is simple — survive as long as possible while the world accelerates around you.

Built on core 3D graphics principles using **OpenGL transformations**, **projection**, and **hierarchical modeling**, every visual element is composed of simple geometric primitives: cuboids, spheres, and cylinders.

---


## 🎮 Gameplay

The player character runs automatically forward through a **three-lane corridor** set in a space environment. Obstacles spawn ahead and speed gradually increases. Players must dodge, jump, crouch, shoot, and collect to survive.

### Core Loop
- Avoid obstacles → maintain health
- Collect gems → increase score
- Shoot obstacles → clear your lane
- Grab power-ups → gain temporary advantages
- Survive longer → face greater speed

---

## ✨ Features

### 🏃 Player Mechanics

| Action | Key | Description |
|--------|-----|-------------|
| Lane Switch | `A` / `D` | Move left or right between three lanes |
| Jump | `Space` | Follow a parabolic arc to clear floor barriers |
| Crouch | `X` | Reduce collision height to pass under low obstacles |
| Shoot | `Left Mouse Button` | Fire a projectile forward along the current lane |

- **Auto-Forward Movement** — the player is continuously translated along the Z-axis with no input required
- **Smooth lane switching** constrained to left, center, and right lanes

---

### 🧱 Obstacles & Environment

- **Static Barriers** — Stationary cuboids and pillars blocking single or multiple lanes
- **Dynamic Obstacles** — Rotating cylinders (spinning bars) that swing unpredictably across lanes
- **Looping Floor System** — Cuboid tiles are recycled once passed, creating an infinite corridor with minimal memory usage
- **Arena Boundaries** — Parallel cuboid walls keep the player within the track
- **Space Environment** — Stars scattered throughout and a large sphere planet in the distance

#### Collision Consequences
| Obstacle Type | Penalty |
|--------------|---------|
| Jump/lane-avoidable cuboid | −20 HP + speed reduction for 3 seconds |
| Rotating bar | −20 HP + speed reduction for 3 seconds |
| Lane-only cuboid (wall) | **Full health lost** |

---

### 💎 Collectibles & Power-Ups

- **Gems (Spheres)** — Scattered along lanes; each collected gem increases the score
- **Random Ability Gem** — A rare gem granting one randomized temporary effect:
  - 🔼 Increased jump height
  - ✖️ Score multiplier (2× for limited duration)
  - 🔫 Multi-shot firing (three bullets per trigger)
- **First Aid Kit** — A red cube with a white plus sign; restores **+40 HP**

---

### 🔫 Offensive System

- Bullets are represented as small cubes and travel along the lane axis
- **10 bullet hits** destroy an obstacle entirely, allowing safe passage
- Shooting is managed via **Left Mouse Button**

---

### 📊 Gameplay Systems

- **Health Bar** — Starts at 100 HP; displayed as a proportional HUD bar that decreases on damage and turns dark red at 0 HP
- **Scoring System** — Score grows with distance; bonus points awarded for gem collection; multipliers apply when active
- **Speed Scaling** — Forward speed and obstacle spawn rate increase progressively over time
- **Game Over & Restart** — Game ends when HP reaches zero; press `R` to restart

---

### 👾 Cheat Mode

Activate with `C` · Deactivate with `C`

| Feature | Key | Effect |
|---------|-----|--------|
| Flying | `F` | Places the player in the sky, avoiding all obstacles |
| Magnetic Pull | `V` | Draws all nearby gems toward the player automatically |

---

### 📷 Camera & Visuals

| Control | Action |
|---------|--------|
| `↑` / `↓` Arrow Keys | Move camera up/down |
| `←` / `→` Arrow Keys | Rotate camera around the track |
| `Right Mouse Button` | Toggle third-person ↔ first-person view |

- **Third-person view** — broader awareness of lanes and upcoming obstacles
- **First-person view** — immersive, reaction-based gameplay

#### HUD Elements
- Score counter (top corner)
- Health bar (proportional horizontal bar)
- Active ability status (text display)
- Game over message

---

## 🕹️ Controls Summary

```
A / D           →  Switch lanes left / right
Space           →  Jump
X               →  Crouch / slide
Left Click      →  Shoot projectile
Right Click     →  Toggle camera view
↑ / ↓          →  Move camera up / down
← / →          →  Rotate camera
C               →  Toggle Cheat Mode
F               →  Fly (Cheat Mode only)
V               →  Magnetic gem pull (Cheat Mode only)
R               →  Restart game
```

---

## 🛠️ Technical Details

- **Graphics API:** OpenGL
- **Rendering:** Hierarchical modeling using geometric primitives (cuboids, spheres, cylinders)
- **Environment:** Procedurally generated corridor with recycled floor tiles
- **Projection:** 3D perspective with switchable camera views

---

## 📌 Project Status

This project is being developed as part of a university graphics course (Summer 2025). Features are subject to change as development progresses.
