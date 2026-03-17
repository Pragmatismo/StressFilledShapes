#!/usr/bin/env python3
"""Goblin Grange Terrain Set Generator (v1.1 draft implementation)."""

from __future__ import annotations

import json
import math
import os
import random
import shutil
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pygame

try:
    import tkinter as tk
    from tkinter import filedialog
except Exception:
    tk = None
    filedialog = None


WINDOW_W, WINDOW_H = 1400, 900
CONTROL_W = 440
TAB_H = 40
TILE_W, TILE_H = 512, 256

ENTRY_EDGES = ["south", "north", "east", "west"]
GROUND_TYPES = [
    "solid",
    "soft",
    "rough",
    "muddy",
    "shallow_water",
    "deep_water",
    "steep",
    "slippery",
    "unstable",
]
OBSTACLE_TYPES = ["block", "climb", "jump", "trip", "break", "tangle", "slow"]
ANCHOR_TYPES = ["none", "play", "eat", "rest", "water", "hide", "admire"]


@dataclass
class TerrainLayer:
    terrain_type: str
    name: str
    description: str = ""
    noise_scale: float = 0.08
    threshold: float = 0.5
    noise_offset: float = 0.0
    ground_type: str = "solid"
    intensity: float = 1.0
    colour: List[int] = field(default_factory=lambda: [100, 180, 100])
    frame_count: int = 1
    autotile: bool = False


@dataclass
class FeatureRule:
    feature_id: str
    name: str
    description: str = ""
    place_on: List[str] = field(default_factory=list)
    min_spacing: int = 2
    min_count: int = 0
    max_count: int = 30
    min_depth_row: int = 0
    density_gradient: Dict[str, float] = field(default_factory=lambda: {"south": 0.35, "north": 0.35})
    tile_width: float = 0.8
    tile_height: float = 0.8
    tile_depth: float = 1.2
    frame_count: int = 1
    obstacle_type: str = "block"
    anchor_type: str = "none"
    anchor_intensity: float = 0.0
    destructible: bool = False
    colour: List[int] = field(default_factory=lambda: [130, 100, 80])


@dataclass
class LocationConfig:
    id: str = "new_location"
    name: str = "New Location"
    description: str = ""
    grid_width: int = 48
    grid_height: int = 16
    default_terrain: str = "new_location_ground"
    entry_edge: str = "south"
    clear_edge_depth: int = 3
    clear_edge_terrain: str = "new_location_path"
    view_distance: int = -1
    terrain_layers: List[TerrainLayer] = field(default_factory=list)
    feature_rules: List[FeatureRule] = field(default_factory=list)
    atmosphere: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "grid_width": self.grid_width,
            "grid_height": self.grid_height,
            "default_terrain": self.default_terrain,
            "entry_edge": self.entry_edge,
            "clear_edge_depth": self.clear_edge_depth,
            "clear_edge_terrain": self.clear_edge_terrain,
            "view_distance": self.view_distance,
            "terrain_layers": [asdict(t) for t in self.terrain_layers],
            "feature_rules": [asdict(f) for f in self.feature_rules],
            "atmosphere": self.atmosphere,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LocationConfig":
        cfg = cls()
        for key in [
            "id",
            "name",
            "description",
            "grid_width",
            "grid_height",
            "default_terrain",
            "entry_edge",
            "clear_edge_depth",
            "clear_edge_terrain",
            "view_distance",
            "atmosphere",
        ]:
            if key in data:
                setattr(cfg, key, data[key])
        cfg.terrain_layers = [TerrainLayer(**t) for t in data.get("terrain_layers", [])]
        cfg.feature_rules = [FeatureRule(**f) for f in data.get("feature_rules", [])]
        return cfg


class TerrainPackageManager:
    def __init__(self, root: Path):
        self.locations_dir = root / "content" / "locations"
        self.locations_dir.mkdir(parents=True, exist_ok=True)

    def list_packages(self) -> List[str]:
        if not self.locations_dir.exists():
            return []
        return sorted([p.name for p in self.locations_dir.iterdir() if (p / "location.json").exists()])

    def package_path(self, package_id: str) -> Path:
        return self.locations_dir / package_id

    def create_package(self, package_id: str) -> Path:
        p = self.package_path(package_id)
        (p / "assets").mkdir(parents=True, exist_ok=True)
        (p / "saves").mkdir(parents=True, exist_ok=True)
        return p


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def make_default_config(package_id: str) -> LocationConfig:
    base = package_id
    ground_id = f"{base}_ground"
    path_id = f"{base}_path"
    tree_id = f"{base}_tree"
    return LocationConfig(
        id=base,
        name=base.replace("_", " ").title(),
        description="A new wilderness package.",
        default_terrain=ground_id,
        clear_edge_terrain=path_id,
        terrain_layers=[
            TerrainLayer(terrain_type=ground_id, name="Ground", threshold=0.0, colour=[96, 140, 90]),
            TerrainLayer(terrain_type=path_id, name="Path", threshold=0.62, colour=[164, 132, 92], autotile=True),
        ],
        feature_rules=[
            FeatureRule(feature_id=tree_id, name="Tree", place_on=[ground_id], tile_depth=2.5, anchor_type="hide", anchor_intensity=2.8),
        ],
    )


def iso_points(cx: int, cy: int, half_w: int = TILE_W // 2, half_h: int = TILE_H // 2):
    return [(cx, cy - half_h), (cx + half_w, cy), (cx, cy + half_h), (cx - half_w, cy)]


def draw_terrain_template(path: Path, terrain: TerrainLayer):
    color = tuple(terrain.colour)
    if terrain.autotile:
        surf = pygame.Surface((TILE_W * 4, TILE_H * 4), pygame.SRCALPHA)
        for i in range(16):
            x = (i % 4) * TILE_W
            y = (i // 4) * TILE_H
            frame = pygame.Surface((TILE_W, TILE_H), pygame.SRCALPHA)
            pygame.draw.polygon(frame, color, iso_points(TILE_W // 2, TILE_H // 2))
            pygame.draw.polygon(frame, (25, 25, 25), iso_points(TILE_W // 2, TILE_H // 2), 3)
            font = pygame.font.SysFont("arial", 30, bold=True)
            txt = font.render(str(i), True, (255, 255, 255))
            frame.blit(txt, txt.get_rect(center=(TILE_W // 2, TILE_H // 2)))
            surf.blit(frame, (x, y))
    elif terrain.frame_count > 1:
        surf = pygame.Surface((TILE_W * terrain.frame_count, TILE_H), pygame.SRCALPHA)
        font = pygame.font.SysFont("arial", 28, bold=True)
        for i in range(terrain.frame_count):
            frame_col = tuple(clamp(c + i * 8, 0, 255) for c in terrain.colour)
            cx = i * TILE_W + TILE_W // 2
            pygame.draw.polygon(surf, frame_col, iso_points(cx, TILE_H // 2))
            pygame.draw.polygon(surf, (25, 25, 25), iso_points(cx, TILE_H // 2), 3)
            txt = font.render(f"F{i}", True, (255, 255, 255))
            surf.blit(txt, txt.get_rect(center=(cx, TILE_H // 2)))
    else:
        surf = pygame.Surface((TILE_W, TILE_H), pygame.SRCALPHA)
        pygame.draw.polygon(surf, color, iso_points(TILE_W // 2, TILE_H // 2))
        pygame.draw.polygon(surf, (25, 25, 25), iso_points(TILE_W // 2, TILE_H // 2), 3)

    font = pygame.font.SysFont("arial", 24, bold=True)
    label = font.render(terrain.terrain_type, True, (255, 255, 255))
    surf.blit(label, (10, 10))
    pygame.image.save(surf, path)


def feature_dimensions_px(f: FeatureRule) -> Tuple[int, int]:
    w = int(math.ceil((f.tile_width + f.tile_height) * 256 + 4))
    h = int(math.ceil((f.tile_width + f.tile_height) * 128 + f.tile_depth * 128 + 4))
    return w, h


def draw_feature_box(surface: pygame.Surface, rect: pygame.Rect, f: FeatureRule, label: str = ""):
    c = tuple(f.colour)
    dark = tuple(clamp(int(v * 0.65), 0, 255) for v in c)
    light = tuple(clamp(int(v * 1.15), 0, 255) for v in c)

    cx = rect.centerx
    ground_y = rect.bottom - 4
    half_w = int(f.tile_width * 128)
    half_h = int(f.tile_height * 64)
    depth_px = int(f.tile_depth * 128)

    bottom = [(cx, ground_y - half_h), (cx + half_w, ground_y), (cx, ground_y + half_h), (cx - half_w, ground_y)]
    top = [(x, y - depth_px) for (x, y) in bottom]

    left_face = [top[3], top[0], bottom[0], bottom[3]]
    right_face = [top[0], top[1], bottom[1], bottom[0]]

    pygame.draw.polygon(surface, light + (140,), left_face)
    pygame.draw.polygon(surface, dark + (170,), right_face)
    pygame.draw.polygon(surface, (255, 255, 255), top, 2)
    pygame.draw.polygon(surface, (180, 180, 180), bottom, 2)

    for i in range(4):
        pygame.draw.line(surface, (220, 220, 220), top[i], bottom[i], 2)

    font = pygame.font.SysFont("arial", 20, bold=True)
    l = font.render(label or f.feature_id, True, (255, 255, 255))
    dims = font.render(f"{f.tile_width}x{f.tile_height}x{f.tile_depth}", True, (255, 230, 120))
    surface.blit(l, l.get_rect(center=(rect.centerx, rect.centery - depth_px // 3)))
    surface.blit(dims, dims.get_rect(center=(rect.centerx, rect.bottom - 16)))


def draw_feature_template(path: Path, feature: FeatureRule, destroyed: bool = False):
    w, h = feature_dimensions_px(feature)
    frame_count = max(1, feature.frame_count)
    surf = pygame.Surface((w * frame_count, h), pygame.SRCALPHA)
    use_feature = FeatureRule(**asdict(feature))
    if destroyed:
        use_feature.tile_depth = max(0.1, feature.tile_depth * 0.2)
        use_feature.colour = [clamp(int(c * 0.6), 0, 255) for c in feature.colour]

    for i in range(frame_count):
        rect = pygame.Rect(i * w, 0, w, h)
        frame_f = FeatureRule(**asdict(use_feature))
        frame_f.colour = [clamp(c + i * 6, 0, 255) for c in use_feature.colour]
        draw_feature_box(surf, rect, frame_f, label=f"{feature.feature_id} F{i}")

    pygame.image.save(surf, path)


class TerrainSetTool:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
        pygame.display.set_caption("Goblin Grange - Terrain Set Generator")
        self.clock = pygame.time.Clock()
        self.root = Path(__file__).resolve().parents[2]
        self.pkg_mgr = TerrainPackageManager(self.root)

        self.tabs = ["Location", "Terrain", "Generate", "Validate"]
        self.active_tab = 0
        self.package_input = ""
        self.selected_package: Optional[str] = None
        self.location = make_default_config("new_location")

        self.seed = random.randint(1, 999999)
        self.biases: Dict[str, float] = {}
        self.generated_grid = None
        self.placed_features = []
        self.show_grid = True
        self.show_features = True
        self.show_anchors = False

        self.camera_x = 0
        self.camera_y = -120
        self.zoom = 0.30
        self.dragging = False
        self.status = "Ready"

    def save_location(self):
        if not self.selected_package:
            return
        pkg_path = self.pkg_mgr.package_path(self.selected_package)
        pkg_path.mkdir(parents=True, exist_ok=True)
        with open(pkg_path / "location.json", "w", encoding="utf-8") as f:
            json.dump(self.location.to_dict(), f, indent=2)

    def load_location(self, package_id: str):
        path = self.pkg_mgr.package_path(package_id) / "location.json"
        if not path.exists():
            return
        self.selected_package = package_id
        with open(path, "r", encoding="utf-8") as f:
            self.location = LocationConfig.from_dict(json.load(f))
        self.status = f"Loaded {package_id}"

    def create_package(self, package_id: str):
        package_id = package_id.strip().lower().replace(" ", "_")
        if not package_id:
            return
        self.pkg_mgr.create_package(package_id)
        self.selected_package = package_id
        self.location = make_default_config(package_id)
        self.save_location()
        self.status = f"Created package: {package_id}"

    def create_assets(self):
        if not self.selected_package:
            self.status = "Create or load a package first."
            return
        self.save_location()
        assets_dir = self.pkg_mgr.package_path(self.selected_package) / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        generated = 0
        for t in self.location.terrain_layers:
            p = assets_dir / f"{t.terrain_type}.png"
            if not p.exists():
                draw_terrain_template(p, t)
                generated += 1
        for f in self.location.feature_rules:
            p = assets_dir / f"{f.feature_id}.png"
            if not p.exists():
                draw_feature_template(p, f)
                generated += 1
            if f.destructible:
                pd = assets_dir / f"{f.feature_id}_destroyed.png"
                if not pd.exists():
                    draw_feature_template(pd, f, destroyed=True)
                    generated += 1
        self.status = f"Created {generated} new templates."

    def import_image(self, target_id: str):
        if not self.selected_package:
            self.status = "Create/load package first."
            return
        if not filedialog or not tk:
            self.status = "tkinter file dialog unavailable in this environment."
            return
        root = tk.Tk()
        root.withdraw()
        chosen = filedialog.askopenfilename(filetypes=[("PNG", "*.png")])
        root.destroy()
        if not chosen:
            return
        dest = self.pkg_mgr.package_path(self.selected_package) / "assets" / f"{target_id}.png"
        shutil.copy(chosen, dest)
        self.status = f"Imported {Path(chosen).name} -> {dest.name}"

    def hash_noise(self, x: int, y: int, seed: int, offset: float = 0.0) -> float:
        n = math.sin((x * 127.1 + y * 311.7 + seed * 0.131 + offset * 101.3)) * 43758.5453
        return n - math.floor(n)

    def apply_clear_edge(self, grid):
        depth = self.location.clear_edge_depth
        terrain = self.location.clear_edge_terrain
        w, h = self.location.grid_width, self.location.grid_height
        entry = self.location.entry_edge

        for y in range(h):
            for x in range(w):
                if entry == "south":
                    dist = y
                elif entry == "north":
                    dist = h - 1 - y
                elif entry == "west":
                    dist = x
                else:
                    dist = w - 1 - x

                if dist == 0:
                    grid[y][x]["terrain_type"] = terrain
                    grid[y][x]["is_clear_edge"] = True
                elif 0 < dist <= depth:
                    p = 1.0 - (dist / (depth + 1))
                    if self.hash_noise(x, y, self.seed, 17.3) < p:
                        grid[y][x]["terrain_type"] = terrain
                        grid[y][x]["is_clear_edge"] = True

    def generate_map(self):
        self.save_location()
        w, h = self.location.grid_width, self.location.grid_height
        terrain_lookup = {t.terrain_type: t for t in self.location.terrain_layers}
        default_id = self.location.default_terrain or (self.location.terrain_layers[0].terrain_type if self.location.terrain_layers else "")

        grid = [[{"terrain_type": default_id, "feature_id": None, "anchor_type": "none", "anchor_intensity": 0.0, "is_clear_edge": False} for _ in range(w)] for _ in range(h)]

        for layer in self.location.terrain_layers:
            bias = self.biases.get(layer.terrain_type, 0.0)
            eff = clamp(layer.threshold - (bias * 0.3), 0.0, 1.0)
            for y in range(h):
                for x in range(w):
                    n = self.hash_noise(int(x * (1 / max(0.01, layer.noise_scale))), int(y * (1 / max(0.01, layer.noise_scale))), self.seed, layer.noise_offset)
                    if n >= eff:
                        grid[y][x]["terrain_type"] = layer.terrain_type

        self.apply_clear_edge(grid)
        self.place_features(grid)
        self.generated_grid = grid
        self.status = f"Generated seed {self.seed}"

    def place_features(self, grid):
        w, h = self.location.grid_width, self.location.grid_height
        placed = []
        occupied = set()

        for rule in self.location.feature_rules:
            candidates = []
            fw = math.ceil(rule.tile_width)
            fh = math.ceil(rule.tile_height)
            for y in range(h):
                for x in range(w):
                    if x + fw > w or y + fh > h:
                        continue
                    if y < rule.min_depth_row:
                        continue
                    valid = True
                    for yy in range(y, y + fh):
                        for xx in range(x, x + fw):
                            cell = grid[yy][xx]
                            if cell["is_clear_edge"] or cell["terrain_type"] not in rule.place_on or (xx, yy) in occupied:
                                valid = False
                    if not valid:
                        continue
                    t = y / max(1, h - 1)
                    density = (1 - t) * rule.density_gradient.get("north", 0.0) + t * rule.density_gradient.get("south", 0.0)
                    if self.hash_noise(x, y, self.seed, 53.0) <= density:
                        candidates.append((x, y))

            rng = random.Random(self.seed + sum(ord(c) for c in rule.feature_id))
            rng.shuffle(candidates)
            target = min(rule.max_count, len(candidates))
            for (x, y) in candidates:
                if len([p for p in placed if p["feature_id"] == rule.feature_id]) >= target:
                    break
                spacing_ok = True
                for p in placed:
                    if abs(p["x"] - x) + abs(p["y"] - y) < rule.min_spacing:
                        spacing_ok = False
                        break
                if not spacing_ok:
                    continue
                for yy in range(y, y + fh):
                    for xx in range(x, x + fw):
                        occupied.add((xx, yy))
                        grid[yy][xx]["feature_id"] = rule.feature_id
                        grid[yy][xx]["anchor_type"] = rule.anchor_type
                        grid[yy][xx]["anchor_intensity"] = rule.anchor_intensity
                placed.append({"feature_id": rule.feature_id, "x": x, "y": y, "w": fw, "h": fh})

        self.placed_features = placed

    def validate(self) -> List[str]:
        errors = []
        warnings = []
        cfg = self.location
        if not cfg.id:
            errors.append("id is required")
        if not (8 <= cfg.grid_width <= 128):
            errors.append("grid_width must be 8..128")
        if not (8 <= cfg.grid_height <= 64):
            errors.append("grid_height must be 8..64")
        if cfg.entry_edge not in ENTRY_EDGES:
            errors.append("entry_edge invalid")
        assets_dir = self.pkg_mgr.package_path(self.selected_package or cfg.id) / "assets"
        for t in cfg.terrain_layers:
            if not (0.01 <= t.noise_scale <= 0.5):
                errors.append(f"{t.terrain_type}: noise_scale out of range")
            if not (0.0 <= t.threshold <= 1.0):
                errors.append(f"{t.terrain_type}: threshold out of range")
            if not (assets_dir / f"{t.terrain_type}.png").exists():
                warnings.append(f"Missing image assets/{t.terrain_type}.png")
        for f in cfg.feature_rules:
            if not (assets_dir / f"{f.feature_id}.png").exists():
                warnings.append(f"Missing image assets/{f.feature_id}.png")
            if f.destructible and not (assets_dir / f"{f.feature_id}_destroyed.png").exists():
                warnings.append(f"Missing destroyed image assets/{f.feature_id}_destroyed.png")

        return [*(f"ERROR: {x}" for x in errors), *(f"WARNING: {w}" for w in warnings)] or ["✅ Validation passed."]

    def draw_ui(self):
        w, h = self.screen.get_size()
        self.screen.fill((24, 28, 34))
        pygame.draw.rect(self.screen, (33, 38, 48), (0, 0, CONTROL_W, h))

        tab_w = CONTROL_W // len(self.tabs)
        for i, tab in enumerate(self.tabs):
            r = pygame.Rect(i * tab_w, 0, tab_w, TAB_H)
            pygame.draw.rect(self.screen, (64, 88, 120) if i == self.active_tab else (48, 54, 68), r)
            self.draw_text(tab, r.centerx, r.centery, center=True)

        if self.active_tab == 0:
            self.draw_location_tab()
        elif self.active_tab == 1:
            self.draw_terrain_tab()
        elif self.active_tab == 2:
            self.draw_generate_tab()
        else:
            self.draw_validate_tab()

        self.draw_preview_panel()
        self.draw_text(self.status, 10, h - 18, color=(200, 220, 140))

    def draw_location_tab(self):
        y = TAB_H + 10
        self.draw_text("Package ID:", 16, y)
        pygame.draw.rect(self.screen, (70, 70, 80), (120, y - 4, 180, 24), 1)
        self.draw_text(self.package_input or "(type and press Enter)", 124, y)
        self.draw_text("[C] Create", 310, y, color=(120, 220, 140))
        y += 30
        self.draw_text("Packages:", 16, y)
        y += 22
        for pkg in self.pkg_mgr.list_packages()[:12]:
            col = (210, 220, 230) if pkg != self.selected_package else (255, 210, 130)
            self.draw_text(pkg, 24, y, color=col)
            y += 18

        y += 10
        self.draw_text(f"Name: {self.location.name}", 16, y)
        y += 18
        self.draw_text(f"Grid: {self.location.grid_width}x{self.location.grid_height}", 16, y)
        y += 18
        self.draw_text(f"Entry: {self.location.entry_edge} | Clear depth: {self.location.clear_edge_depth}", 16, y)
        y += 18
        self.draw_text(f"View Distance: {self.location.view_distance}", 16, y)
        y += 18
        self.draw_text("Keyboard shortcuts: [S] save  [G] generate", 16, y, color=(150, 180, 220))

    def draw_terrain_tab(self):
        y = TAB_H + 12
        self.draw_text("[T] +Terrain  [F] +Feature  [A] Create Assets  [I] Import First Terrain", 10, y, color=(150, 220, 170))
        y += 26
        self.draw_text("Terrain Layers", 12, y, color=(220, 210, 150))
        y += 18
        for t in self.location.terrain_layers[:8]:
            pygame.draw.rect(self.screen, tuple(t.colour), (12, y + 3, 10, 10))
            self.draw_text(f"{t.name} ({t.terrain_type}) th={t.threshold:.2f} ns={t.noise_scale:.2f}", 28, y)
            y += 17

        y += 10
        self.draw_text("Features", 12, y, color=(220, 210, 150))
        y += 18
        for f in self.location.feature_rules[:8]:
            pygame.draw.rect(self.screen, tuple(f.colour), (12, y + 3, 10, 10))
            self.draw_text(f"{f.name} ({f.feature_id}) {f.tile_width}x{f.tile_height}x{f.tile_depth}", 28, y)
            y += 17

    def draw_generate_tab(self):
        y = TAB_H + 12
        self.draw_text("[G] Generate  [R] Random Seed", 12, y, color=(150, 220, 170))
        y += 22
        self.draw_text(f"Seed: {self.seed}", 12, y, color=(255, 210, 120))
        y += 22
        self.draw_text(f"Overlay Grid[{self.show_grid}] Features[{self.show_features}] Anchors[{self.show_anchors}]", 12, y)
        y += 24
        self.draw_text("Biases:", 12, y)
        y += 18
        for t in self.location.terrain_layers:
            b = self.biases.get(t.terrain_type, 0.0)
            self.draw_text(f"{t.name:<12} {b:+.2f}", 16, y)
            y += 16

    def draw_validate_tab(self):
        y = TAB_H + 12
        self.draw_text("[V] Run Validation", 12, y, color=(150, 220, 170))
        y += 24
        for msg in self.validate()[:26]:
            col = (230, 90, 90) if msg.startswith("ERROR") else (220, 190, 90) if msg.startswith("WARNING") else (120, 220, 140)
            self.draw_text(msg, 12, y, color=col)
            y += 16

    def draw_preview_panel(self):
        origin_x = CONTROL_W + (self.screen.get_width() - CONTROL_W) // 2 + self.camera_x
        origin_y = self.screen.get_height() // 4 + self.camera_y
        if not self.generated_grid:
            self.draw_text("Press Generate to preview map.", CONTROL_W + 40, 70, color=(160, 180, 200))
            return

        w, h = self.location.grid_width, self.location.grid_height
        terrain_color = {t.terrain_type: tuple(t.colour) for t in self.location.terrain_layers}

        for y in range(h):
            for x in range(w):
                sx = origin_x + int((x - y) * (TILE_W // 2) * self.zoom)
                sy = origin_y + int((x + y) * (TILE_H // 2) * self.zoom)
                col = terrain_color.get(self.generated_grid[y][x]["terrain_type"], (90, 90, 90))
                pts = [
                    (sx, sy - int((TILE_H // 2) * self.zoom)),
                    (sx + int((TILE_W // 2) * self.zoom), sy),
                    (sx, sy + int((TILE_H // 2) * self.zoom)),
                    (sx - int((TILE_W // 2) * self.zoom), sy),
                ]
                pygame.draw.polygon(self.screen, col, pts)
                if self.show_grid:
                    pygame.draw.polygon(self.screen, (18, 18, 18), pts, 1)
                if self.generated_grid[y][x]["is_clear_edge"]:
                    pygame.draw.polygon(self.screen, (245, 230, 140), pts, 1)

        if self.show_features:
            for p in self.placed_features:
                x, y = p["x"], p["y"]
                sx = origin_x + int((x - y) * (TILE_W // 2) * self.zoom)
                sy = origin_y + int((x + y) * (TILE_H // 2) * self.zoom)
                pygame.draw.circle(self.screen, (255, 220, 120), (sx, sy - int(20 * self.zoom)), 4)

    def draw_text(self, text, x, y, color=(230, 230, 230), center=False):
        font = pygame.font.SysFont("arial", 16)
        s = font.render(str(text), True, color)
        r = s.get_rect()
        if center:
            r.center = (x, y)
        else:
            r.topleft = (x, y)
        self.screen.blit(s, r)

    def handle_event(self, e):
        if e.type == pygame.QUIT:
            return False
        if e.type == pygame.VIDEORESIZE:
            self.screen = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
        if e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 1:
                mx, my = e.pos
                if my < TAB_H and mx < CONTROL_W:
                    tab_w = CONTROL_W // len(self.tabs)
                    self.active_tab = clamp(mx // tab_w, 0, len(self.tabs) - 1)
                elif mx > CONTROL_W:
                    self.dragging = True
            elif e.button == 4:
                self.zoom = clamp(self.zoom + 0.03, 0.08, 1.3)
            elif e.button == 5:
                self.zoom = clamp(self.zoom - 0.03, 0.08, 1.3)
        if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.dragging = False
        if e.type == pygame.MOUSEMOTION and self.dragging:
            dx, dy = e.rel
            self.camera_x += dx
            self.camera_y += dy
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                return False
            if self.active_tab == 0:
                if e.key == pygame.K_RETURN and self.package_input:
                    self.create_package(self.package_input)
                elif e.key == pygame.K_BACKSPACE:
                    self.package_input = self.package_input[:-1]
                elif e.unicode.isalnum() or e.unicode in ["_", "-"]:
                    self.package_input += e.unicode.lower()
                elif e.key == pygame.K_c:
                    self.create_package(self.package_input)
                elif e.key == pygame.K_1:
                    pkgs = self.pkg_mgr.list_packages()
                    if pkgs:
                        self.load_location(pkgs[0])
            if e.key == pygame.K_s:
                self.save_location()
                self.status = "Saved location.json"
            elif e.key == pygame.K_t:
                idx = len(self.location.terrain_layers)
                tid = f"{self.location.id}_terrain_{idx}"
                self.location.terrain_layers.append(TerrainLayer(terrain_type=tid, name=f"Terrain {idx}", threshold=0.5))
            elif e.key == pygame.K_f:
                idx = len(self.location.feature_rules)
                fid = f"{self.location.id}_feature_{idx}"
                place = [self.location.terrain_layers[0].terrain_type] if self.location.terrain_layers else []
                self.location.feature_rules.append(FeatureRule(feature_id=fid, name=f"Feature {idx}", place_on=place))
            elif e.key == pygame.K_a:
                self.create_assets()
            elif e.key == pygame.K_i and self.location.terrain_layers:
                self.import_image(self.location.terrain_layers[0].terrain_type)
            elif e.key == pygame.K_g:
                self.generate_map()
            elif e.key == pygame.K_r:
                self.seed = random.randint(1, 999999)
                self.generate_map()
            elif e.key == pygame.K_v:
                result = self.validate()
                self.status = result[0]
            elif e.key == pygame.K_3:
                self.show_grid = not self.show_grid
            elif e.key == pygame.K_4:
                self.show_features = not self.show_features
            elif e.key == pygame.K_5:
                self.show_anchors = not self.show_anchors
        return True

    def run(self):
        running = True
        while running:
            for e in pygame.event.get():
                running = self.handle_event(e)
                if not running:
                    break
            self.draw_ui()
            pygame.display.flip()
            self.clock.tick(60)


if __name__ == "__main__":
    TerrainSetTool().run()
