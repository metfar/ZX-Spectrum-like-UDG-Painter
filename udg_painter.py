#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#pylint:disable=W0301
#  
#  Copyright 2018- William Martinez Bas <metfar@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#

import ast;
import json;
import os;
import sys;

import pygame;

try:
    from PIL import Image;
except ImportError:
    Image = None;

from lib.pygame_file_dialog import select_file, save_file_dialog;
from lib.pygame_input_txt import input_line;
from lib.pygame_msgbox import message_box;
from lib.pygame_menu import touch_menu;


BASE_WIDTH = 720;
BASE_HEIGHT = 1280;

#HEIGHT = 960;   # tablet
#HEIGHT = 1280;  # celular
HEIGHT = 720;   # computer

WIDTH = int(BASE_WIDTH * (HEIGHT / BASE_HEIGHT));

ROWS = 14;
COLS = 14;
MIN_GRID_SIZE = 1;
MAX_GRID_SIZE = 64;


UDG_EXT = ".udg";
BIN_EXT = ".bin";
XPM_EXT = ".xpm";
ICO_EXT = ".ico";
SAVE_MODES = ["COLOR", "BINARY", "XPM", "ICO"];
SAVE_EXTENSIONS = {"COLOR": UDG_EXT, "BINARY": BIN_EXT, "XPM": XPM_EXT, "ICO": ICO_EXT};

BG = (10, 30, 32);
GRID_BG = (28, 48, 54);
GRID_LINE = (55, 75, 85);
TEXT = (235, 245, 250);
BTN = (140, 220, 40);
BTN2 = (60, 100, 120);
BTN_TEXT = (10, 25, 30);
ERROR = (255, 100, 100);

SPECTRUM_COLORS = [
    (0, 0, 0),
    (0, 0, 205),
    (205, 0, 0),
    (205, 0, 205),
    (0, 205, 0),
    (0, 205, 205),
    (205, 205, 0),
    (205, 205, 205),
    (22, 22, 22),
    (0, 0, 255),
    (255, 0, 0),
    (255, 0, 255),
    (0, 255, 0),
    (0, 255, 255),
    (255, 255, 0),
    (255, 255, 255),
];


class Scale:
    def __init__(self, width, height):
        self.width = width;
        self.height = height;
        self.scale = height / BASE_HEIGHT;

    def v(self, value):
        return max(1, int(round(value * self.scale)));

    def rect(self, x, y, w, h):
        return pygame.Rect(self.v(x), self.v(y), self.v(w), self.v(h));

    def font(self, points, bold=False):
        return pygame.font.SysFont("monospace", max(8, self.v(points)), bold=bold);


class Layout:
    def __init__(self, screen):
        width, height = screen.get_size();
        self.s = Scale(width, height);
        self.width = width;
        self.height = height;
        self.margin = self.s.v(36);
        self.top = self.s.v(180);
        self.row_gap = self.s.v(10);
        self.button_h = self.s.v(78);
        self.palette_rects = self.make_palette_rects();
        self.palette_top = min([rect.y for rect in self.palette_rects]);
        self.buttons = {};
        self.make_buttons();
        self.buttons_top = min([rect.y for rect in self.buttons.values()]);
        self.grid_bottom = self.buttons_top - self.s.v(22);
        self.grid_size = min(width - self.margin * 2, max(self.s.v(160), self.grid_bottom - self.top));
        self.cell = max(2, self.grid_size // max(COLS, ROWS));
        self.grid_w = self.cell * COLS;
        self.grid_h = self.cell * ROWS;
        self.grid_x = (width - self.grid_w) // 2;
        self.grid_y = self.top;

    def row_rects(self, y, labels):
        rects = {};
        gap = self.s.v(12);
        x0 = self.margin;
        total_gap = gap * (len(labels) - 1);
        button_w = (self.width - self.margin * 2 - total_gap) // len(labels);

        for index, label in enumerate(labels):
            x = x0 + index * (button_w + gap);
            rects[label] = pygame.Rect(x, y, button_w, self.button_h);

        return rects;

    def make_buttons(self):
        row4_y = self.palette_top - self.s.v(18) - self.button_h;
        row3_y = row4_y - self.row_gap - self.button_h;
        row2_y = row3_y - self.row_gap - self.button_h;
        row1_y = row2_y - self.row_gap - self.button_h;
        self.buttons.update(self.row_rects(row1_y, ["CLEAR", "SAVE", "LOAD"]));
        self.buttons.update(self.row_rects(row2_y, ["FORMAT"]));
        self.buttons.update(self.row_rects(row3_y, ["CAN-", "CAN+", "SCL-", "SCL+"]));
        self.buttons.update(self.row_rects(row4_y, ["SHL", "SHU", "SHD", "SHR"]));
        self.clear_rect = self.buttons["CLEAR"];
        self.save_rect = self.buttons["SAVE"];
        self.load_rect = self.buttons["LOAD"];
        self.mode_rect = self.buttons["FORMAT"];

    def make_palette_rects(self):
        rects = [];
        px = self.margin;
        gap = self.s.v(8);
        max_ps = (self.width - self.margin * 2 - gap * 7) // 8;
        ps = min(self.s.v(70), max(8, max_ps));
        py = self.height - self.margin - (ps * 2 + gap);

        for i in range(16):
            x = px + (i % 8) * (ps + gap);
            y = py + (i // 8) * (ps + gap);
            rects.append(pygame.Rect(x, y, ps, ps));

        return rects;

def empty_grid():
    return [[-1 for _ in range(COLS)] for _ in range(ROWS)];


def clone_grid(grid):
    return [list(row) for row in grid if isinstance(row, list)];


def set_grid_size(size):
    global ROWS;
    global COLS;

    size = max(MIN_GRID_SIZE, min(MAX_GRID_SIZE, int(size)));
    ROWS = size;
    COLS = size;


def resize_grid_to_size(grid, size):
    old_rows = len(grid);
    old_cols = max([len(row) for row in grid if isinstance(row, list)] + [0]);
    set_grid_size(size);
    new_grid = empty_grid();

    for row in range(min(ROWS, old_rows)):
        if not isinstance(grid[row], list):
            continue;

        for col in range(min(COLS, old_cols, len(grid[row]))):
            value = grid[row][col];

            if isinstance(value, int) and -1 <= value <= 15:
                new_grid[row][col] = value;

    return new_grid;


def map_scaled_index(target_index, target_count, source_count):
    if source_count <= 1 or target_count <= 1:
        return 0;

    return int(round(target_index * (source_count - 1) / (target_count - 1)));


def get_nearest_resample_filter():
    if Image is None:
        return None;

    if hasattr(Image, "Resampling"):
        return Image.Resampling.NEAREST;

    return Image.NEAREST;


def grid_to_rgba_image_any_size(grid):
    if Image is None:
        return None;

    rows = len(grid);
    cols = max([len(row) for row in grid if isinstance(row, list)] + [0]);

    if rows <= 0 or cols <= 0:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0));

    image = Image.new("RGBA", (cols, rows), (0, 0, 0, 0));
    pixels = image.load();

    for row in range(rows):
        if not isinstance(grid[row], list):
            continue;

        for col in range(min(cols, len(grid[row]))):
            value = grid[row][col];

            if isinstance(value, int) and 0 <= value <= 15:
                rgb = SPECTRUM_COLORS[value];
                pixels[col, row] = (rgb[0], rgb[1], rgb[2], 255);

    return image;


def rgba_image_to_current_grid_exact(image):
    rgba = image.convert("RGBA");
    grid = empty_grid();

    for row in range(ROWS):
        for col in range(COLS):
            r, g, b, a = rgba.getpixel((col, row));

            if a < 64:
                grid[row][col] = -1;
            else:
                grid[row][col] = nearest_spectrum_color((r, g, b));

    return grid;


def resize_grid_scaled_fallback(grid, size):
    old_rows = len(grid);
    old_cols = max([len(row) for row in grid if isinstance(row, list)] + [0]);
    set_grid_size(size);

    if old_rows <= 0 or old_cols <= 0:
        return empty_grid();

    new_grid = empty_grid();

    for row in range(ROWS):
        source_row = min(old_rows - 1, int((row + 0.5) * old_rows / ROWS));

        for col in range(COLS):
            source_col = min(old_cols - 1, int((col + 0.5) * old_cols / COLS));

            if source_col < len(grid[source_row]):
                value = grid[source_row][source_col];

                if isinstance(value, int) and -1 <= value <= 15:
                    new_grid[row][col] = value;

    return new_grid;


def resize_grid_scaled(grid, size):
    target_size = max(MIN_GRID_SIZE, min(MAX_GRID_SIZE, int(size)));
    old_rows = len(grid);
    old_cols = max([len(row) for row in grid if isinstance(row, list)] + [0]);

    if old_rows <= 0 or old_cols <= 0:
        set_grid_size(target_size);
        return empty_grid();

    # Scale through an in-memory RGBA image and convert back to the
    # nearest Spectrum palette index. This avoids the destructive
    # area-voting/majority effect that eats thin pixel-art details
    # when shrinking. NEAREST is intentional: this is UDG/pixel art,
    # not a photo.
    if Image is not None:
        source_image = grid_to_rgba_image_any_size(grid);
        resize_filter = get_nearest_resample_filter();
        scaled_image = source_image.resize((target_size, target_size), resize_filter);
        set_grid_size(target_size);
        return rgba_image_to_current_grid_exact(scaled_image);

    return resize_grid_scaled_fallback(grid, target_size);

def shift_grid_wrap(grid, dx, dy):
    rows = len(grid);
    cols = max([len(row) for row in grid if isinstance(row, list)] + [0]);

    if rows <= 0 or cols <= 0:
        return grid;

    new_grid = [[-1 for _ in range(cols)] for _ in range(rows)];

    for row in range(rows):
        if not isinstance(grid[row], list):
            continue;

        for col in range(min(cols, len(grid[row]))):
            new_row = (row + dy) % rows;
            new_col = (col + dx) % cols;
            new_grid[new_row][new_col] = grid[row][col];

    return normalize_grid_to_current(new_grid);


def normalize_grid_to_current(grid):
    clean = empty_grid();

    for row in range(min(ROWS, len(grid))):
        if not isinstance(grid[row], list):
            continue;

        for col in range(min(COLS, len(grid[row]))):
            value = grid[row][col];

            if isinstance(value, int) and -1 <= value <= 15:
                clean[row][col] = value;

    return clean;


def detect_grid_size_from_matrix(grid):
    rows = len(grid) if isinstance(grid, list) else 0;
    cols = 0;

    if isinstance(grid, list):
        cols = max([len(row) for row in grid if isinstance(row, list)] + [0]);

    return max(MIN_GRID_SIZE, min(MAX_GRID_SIZE, max(rows, cols, 1)));


def grid_to_binary_rows(grid):
    rows = [];

    for row in grid:
        value = 0;

        for cell in row:
            bit = 1 if cell >= 0 else 0;
            value = (value << 1) | bit;

        rows.append(value);

    return rows;


def grid_to_binary_bytes(grid):
    bytes_per_row = (COLS + 7) // 8;
    output = bytearray();

    for row in grid:
        padded = list(row) + [-1 for _ in range(bytes_per_row * 8 - COLS)];

        for start in range(0, len(padded), 8):
            value = 0;

            for cell in padded[start:start + 8]:
                bit = 1 if cell >= 0 else 0;
                value = (value << 1) | bit;

            output.append(value);

    return bytes(output);


def infer_binary_square_size(data):
    data_len = len(data);

    for size in range(MAX_GRID_SIZE, MIN_GRID_SIZE - 1, -1):
        if size * ((size + 7) // 8) == data_len:
            return size;

    return max(ROWS, COLS);


def binary_bytes_to_grid(data):
    bytes_per_row = (COLS + 7) // 8;
    grid = [];

    for row_index in range(ROWS):
        row = [];
        start = row_index * bytes_per_row;
        row_bytes = data[start:start + bytes_per_row];

        if len(row_bytes) < bytes_per_row:
            row_bytes = row_bytes + bytes([0 for _ in range(bytes_per_row - len(row_bytes))]);

        for value in row_bytes:
            for bit_index in range(7, -1, -1):
                if len(row) < COLS:
                    bit = (value >> bit_index) & 1;
                    row.append(15 if bit else -1);

        grid.append(row);

    return grid;


def binary_rows_to_grid(rows):
    grid = [];

    for value in rows[:ROWS]:
        row = [];

        for bit_index in range(COLS - 1, -1, -1):
            bit = (int(value) >> bit_index) & 1;
            row.append(15 if bit else -1);

        grid.append(row);

    while len(grid) < ROWS:
        grid.append([-1 for _ in range(COLS)]);

    return grid;


def color_to_hex(color):
    return "#{:02X}{:02X}{:02X}".format(color[0], color[1], color[2]);


def grid_to_xpm_text(grid):
    symbols = [".", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F"];
    lines = [];
    lines.append("/* XPM */");
    lines.append("static char * udg_image[] = {");
    lines.append('"' + str(COLS) + ' ' + str(ROWS) + ' 17 1",');
    lines.append('". c None",');

    for color_index in range(16):
        comma = "," if color_index < 15 else ",";
        lines.append('"' + symbols[color_index + 1] + ' c ' + color_to_hex(SPECTRUM_COLORS[color_index]) + '"' + comma);

    for row_index, row in enumerate(grid):
        text_row = "";

        for cell in row:
            if isinstance(cell, int) and 0 <= cell <= 15:
                text_row += symbols[cell + 1];
            else:
                text_row += ".";

        comma = "," if row_index < ROWS - 1 else "";
        lines.append('"' + text_row + '"' + comma);

    lines.append("};");
    lines.append("");
    return "\n".join(lines);


def grid_to_rgba_image(grid):
    if Image is None:
        raise RuntimeError("Pillow is required for ICO export.");

    image = Image.new("RGBA", (COLS, ROWS), (0, 0, 0, 0));
    pixels = image.load();

    for row in range(ROWS):
        for col in range(COLS):
            color_index = grid[row][col];

            if isinstance(color_index, int) and 0 <= color_index <= 15:
                rgb = SPECTRUM_COLORS[color_index];
                pixels[col, row] = (rgb[0], rgb[1], rgb[2], 255);

    return image;


def nearest_spectrum_color(rgb):
    best_index = 0;
    best_distance = None;

    for index, color in enumerate(SPECTRUM_COLORS):
        distance = (
            (int(rgb[0]) - color[0]) ** 2 +
            (int(rgb[1]) - color[1]) ** 2 +
            (int(rgb[2]) - color[2]) ** 2
        );

        if best_distance is None or distance < best_distance:
            best_distance = distance;
            best_index = index;

    return best_index;


def image_to_grid(image):
    rgba = image.convert("RGBA");
    source_w, source_h = rgba.size;
    target_size = max(MIN_GRID_SIZE, min(MAX_GRID_SIZE, max(source_w, source_h, 1)));
    set_grid_size(target_size);
    grid = empty_grid();

    for row in range(ROWS):
        for col in range(COLS):
            x0 = int(col * source_w / COLS);
            x1 = int((col + 1) * source_w / COLS);
            y0 = int(row * source_h / ROWS);
            y1 = int((row + 1) * source_h / ROWS);
            total_alpha = 0;
            total_r = 0;
            total_g = 0;
            total_b = 0;
            count = 0;

            for y in range(y0, max(y0 + 1, y1)):
                for x in range(x0, max(x0 + 1, x1)):
                    r, g, b, a = rgba.getpixel((min(x, source_w - 1), min(y, source_h - 1)));
                    total_alpha += a;
                    total_r += r;
                    total_g += g;
                    total_b += b;
                    count += 1;

            if count <= 0 or total_alpha / count < 64:
                grid[row][col] = -1;
            else:
                avg = (total_r // count, total_g // count, total_b // count);
                grid[row][col] = nearest_spectrum_color(avg);

    return grid;


def parse_xpm_color(value):
    value = value.strip();

    if value.lower() == "none":
        return None;

    if value.startswith("#") and len(value) >= 7:
        try:
            return (int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16));
        except ValueError:
            return None;

    names = {
        "black": (0, 0, 0),
        "blue": (0, 0, 255),
        "red": (255, 0, 0),
        "magenta": (255, 0, 255),
        "green": (0, 255, 0),
        "cyan": (0, 255, 255),
        "yellow": (255, 255, 0),
        "white": (255, 255, 255),
        "gray": (205, 205, 205),
        "grey": (205, 205, 205),
    };

    return names.get(value.lower());


def extract_xpm_strings(text):
    strings = [];

    for line in text.splitlines():
        line = line.strip();

        if '"' not in line:
            continue;

        start = line.find('"');
        end = line.rfind('"');

        if end > start:
            strings.append(line[start + 1:end]);

    return strings;


def xpm_text_to_grid(text):
    strings = extract_xpm_strings(text);

    if not strings:
        raise ValueError("No XPM string data found.");

    header = strings[0].split();

    if len(header) < 4:
        raise ValueError("Invalid XPM header.");

    width = int(header[0]);
    height = int(header[1]);
    colors = int(header[2]);
    cpp = int(header[3]);
    palette = {};

    for index in range(colors):
        item = strings[index + 1];
        key = item[:cpp];
        rest = item[cpp:].strip().split();
        color_value = None;

        for pos, token in enumerate(rest):
            if token == "c" and pos + 1 < len(rest):
                color_value = parse_xpm_color(rest[pos + 1]);
                break;

        if color_value is None:
            palette[key] = -1;
        else:
            palette[key] = nearest_spectrum_color(color_value);

    rows = strings[1 + colors:1 + colors + height];
    raw_grid = [];

    for row_text in rows:
        row = [];

        for col in range(width):
            key = row_text[col * cpp:(col + 1) * cpp];
            row.append(palette.get(key, -1));

        raw_grid.append(row);

    target_size = max(MIN_GRID_SIZE, min(MAX_GRID_SIZE, max(width, height, 1)));
    set_grid_size(target_size);
    return resample_grid(raw_grid, width, height);


def resample_grid(source_grid, source_w, source_h):
    grid = empty_grid();

    for row in range(ROWS):
        source_row = min(source_h - 1, map_scaled_index(row, ROWS, source_h));

        for col in range(COLS):
            source_col = min(source_w - 1, map_scaled_index(col, COLS, source_w));
            value = source_grid[source_row][source_col];

            if isinstance(value, int) and -1 <= value <= 15:
                grid[row][col] = value;

    return grid;


def load_ico_file(filename):
    if Image is None:
        raise RuntimeError("Pillow is required for ICO load.");

    with Image.open(filename) as image:
        if hasattr(image, "ico"):
            sizes = sorted(image.ico.sizes(), key=lambda item: (item[0] * item[1], item[0], item[1]));

            if sizes:
                image = image.ico.getimage(sizes[0]);

        return image_to_grid(image), "LOADED ICO: " + filename;


def normalize_grid(grid):
    clean = empty_grid();

    for row in range(min(ROWS, len(grid))):
        if not isinstance(grid[row], list):
            continue;

        for col in range(min(COLS, len(grid[row]))):
            value = grid[row][col];

            if isinstance(value, int) and -1 <= value <= 15:
                clean[row][col] = value;

    return clean;


def list_udg_files():
    files = [];

    for filename in os.listdir("."):
        if filename.lower().endswith(UDG_EXT):
            files.append(filename);

    files.sort();
    return files;


def apply_extension(filename, save_mode):
    extension = SAVE_EXTENSIONS.get(save_mode, UDG_EXT);

    if not filename.lower().endswith(extension):
        filename += extension;

    return filename;


def save_udg_file(filename, grid, save_mode):
    if not filename.strip():
        return "EMPTY FILENAME";

    filename = apply_extension(filename.strip(), save_mode);

    if save_mode == "COLOR":
        data = {
            "format": "UDG_COLOR_MATRIX",
            "rows": ROWS,
            "cols": COLS,
            "palette": "ZX_SPECTRUM_16",
            "grid": grid,
        };

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4);

    elif save_mode == "BINARY":
        with open(filename, "wb") as file:
            file.write(grid_to_binary_bytes(grid));

    elif save_mode == "XPM":
        with open(filename, "w", encoding="utf-8") as file:
            file.write(grid_to_xpm_text(grid));

    elif save_mode == "ICO":
        image = grid_to_rgba_image(grid);
        image.save(filename, format="ICO", sizes=[(COLS, ROWS)]);

    else:
        return "UNKNOWN SAVE MODE";

    return "SAVED " + save_mode + ": " + filename;


def load_udg_file(filename):
    lower_name = filename.lower();

    if lower_name.endswith(BIN_EXT):
        with open(filename, "rb") as file:
            data = file.read();

        set_grid_size(infer_binary_square_size(data));
        return binary_bytes_to_grid(data), "LOADED BINARY: " + filename;

    if lower_name.endswith(XPM_EXT):
        with open(filename, "r", encoding="utf-8") as file:
            return xpm_text_to_grid(file.read()), "LOADED XPM: " + filename;

    if lower_name.endswith(ICO_EXT):
        return load_ico_file(filename);

    with open(filename, "r", encoding="utf-8") as file:
        text = file.read();

    try:
        data = json.loads(text);
    except json.JSONDecodeError:
        data = ast.literal_eval(text);

    if isinstance(data, dict) and data.get("format") == "UDG_COLOR_MATRIX":
        file_rows = int(data.get("rows", len(data.get("grid", []))));
        file_cols = int(data.get("cols", 0));
        if file_cols <= 0:
            file_cols = detect_grid_size_from_matrix(data.get("grid", []));
        set_grid_size(max(file_rows, file_cols));
        return normalize_grid(data["grid"]), "LOADED COLOR: " + filename;

    if isinstance(data, dict) and data.get("format") == "ZX_SPECTRUM_BINARY_ROWS":
        file_rows = int(data.get("rows", len(data.get("bytes", []))));
        file_cols = int(data.get("cols", file_rows));
        set_grid_size(max(file_rows, file_cols));
        return binary_rows_to_grid(data["bytes"]), "LOADED BINARY: " + filename;

    if isinstance(data, list):
        if all(isinstance(row, list) for row in data):
            set_grid_size(detect_grid_size_from_matrix(data));
            return normalize_grid(data), "LOADED MATRIX: " + filename;

        set_grid_size(len(data));
        return binary_rows_to_grid(data), "LOADED BINARY LIST: " + filename;

    return None, "UNKNOWN FORMAT";


def cell_from_pos(mx, my, layout):
    if not layout.grid_x <= mx < layout.grid_x + layout.grid_w:
        return None;

    if not layout.grid_y <= my < layout.grid_y + layout.grid_h:
        return None;

    col = (mx - layout.grid_x) // layout.cell;
    row = (my - layout.grid_y) // layout.cell;

    return int(row), int(col);


def draw_button(screen, rect, text, font, bg_color, fg_color, scale):
    rendered = font.render(text, True, fg_color);
    pygame.draw.rect(screen, bg_color, rect, border_radius=scale.v(20));
    screen.blit(rendered, rendered.get_rect(center=rect.center));


def mode_from_filename(filename, fallback="COLOR"):
    lower_name = filename.lower();

    for mode, extension in SAVE_EXTENSIONS.items():
        if lower_name.endswith(extension):
            return mode;

    return fallback;


def basename_without_known_extension(filename):
    base = os.path.basename(filename) if filename else "graphic";
    lower_base = base.lower();

    for extension in SAVE_EXTENSIONS.values():
        if lower_base.endswith(extension):
            return base[:-len(extension)];

    return base;


def directory_from_filename(filename):
    if filename:
        directory = os.path.dirname(os.path.abspath(filename));

        if os.path.isdir(directory):
            return directory;

    return ".";


def pygame_save_dialog(screen, clock, scale, font_big, font_small, save_mode, current_filename=None):
    extension = SAVE_EXTENSIONS.get(save_mode, UDG_EXT);
    filename = save_file_dialog(
        screen,
        clock,
        directory=directory_from_filename(current_filename),
        extension=extension,
        title="SAVE " + save_mode + " FILE",
        default_name=basename_without_known_extension(current_filename),
        allow_dirs=True,
    );

    if filename is None:
        return "CANCEL", None;

    return "SAVE", filename;


def pygame_load_dialog(screen, clock, scale, font_big, font_small, current_filename=None):
    file_type = touch_menu(
        screen,
        clock,
        "LOAD FORMAT",
        [
            (UDG_EXT, "COLOR .UDG"),
            (BIN_EXT, "BINARY .BIN"),
            (XPM_EXT, "XPM .XPM"),
            (ICO_EXT, "ICON .ICO"),
        ],
    );

    if file_type is None:
        return "CANCEL", None;

    filename = select_file(screen, clock, directory_from_filename(current_filename), file_type, "LOAD " + file_type.upper() + " FILE");

    if filename is None:
        return "CANCEL", None;

    return "LOAD", filename;




def describe_key_event(event):
    mods = pygame.key.get_mods() | getattr(event, "mod", 0);
    flags = [];

    if mods & pygame.KMOD_LSHIFT:
        flags.append("LSHIFT");
    if mods & pygame.KMOD_RSHIFT:
        flags.append("RSHIFT");
    if mods & pygame.KMOD_SHIFT:
        flags.append("SHIFT");
    if mods & pygame.KMOD_CTRL:
        flags.append("CTRL");
    if mods & pygame.KMOD_ALT:
        flags.append("ALT");

    unicode_value = getattr(event, "unicode", "");

    return (
        "KEY=" + str(event.key) +
        " NAME=" + pygame.key.name(event.key) +
        " UNICODE=" + repr(unicode_value) +
        " MOD=" + str(mods) +
        " FLAGS=" + ("|".join(flags) if flags else "NONE")
    );

def event_has_shift(event):
    mods = pygame.key.get_mods() | getattr(event, "mod", 0);
    return bool(mods & pygame.KMOD_SHIFT);


def event_is_plus(event):
    unicode_value = getattr(event, "unicode", "");
    return (
        event.key == 43 or
        event.key == pygame.K_PLUS or
        event.key == pygame.K_EQUALS or
        event.key == pygame.K_KP_PLUS or
        unicode_value == "+" or
        pygame.key.name(event.key) == "+"
    );


def event_is_minus(event):
    unicode_value = getattr(event, "unicode", "");
    return (
        event.key == 45 or
        event.key == pygame.K_MINUS or
        event.key == pygame.K_KP_MINUS or
        unicode_value == "-" or
        unicode_value == "_" or
        pygame.key.name(event.key) == "-"
    );


def event_requests_scale(event):
    return event_has_shift(event);


def resize_grid_by_delta(grid, delta, scale_image=False):
    target_size = max(MIN_GRID_SIZE, min(MAX_GRID_SIZE, max(ROWS, COLS) + delta));

    if target_size == max(ROWS, COLS):
        return grid;

    if scale_image:
        return resize_grid_scaled(grid, target_size);

    return resize_grid_to_size(grid, target_size);


def clamp_cursor(cursor_row, cursor_col):
    cursor_row = max(0, min(ROWS - 1, cursor_row));
    cursor_col = max(0, min(COLS - 1, cursor_col));
    return cursor_row, cursor_col;


def apply_grid_delta(grid, delta):
    target_size = max(MIN_GRID_SIZE, min(MAX_GRID_SIZE, max(ROWS, COLS) + delta));

    if target_size == max(ROWS, COLS):
        return grid;

    return resize_grid_to_size(grid, target_size);


def select_color_from_key(event, selected_color):
    key_map = {
        pygame.K_0: 0,
        pygame.K_1: 1,
        pygame.K_2: 2,
        pygame.K_3: 3,
        pygame.K_4: 4,
        pygame.K_5: 5,
        pygame.K_6: 6,
        pygame.K_7: 7,
    };

    if event.key not in key_map:
        return selected_color;

    value = key_map[event.key];

    if event_has_shift(event):
        value += 8;

    return value;


def toggle_cursor_pixel(grid, cursor_row, cursor_col, selected_color):
    if grid[cursor_row][cursor_col] == -1:
        grid[cursor_row][cursor_col] = selected_color;
    else:
        grid[cursor_row][cursor_col] = -1;

    return grid;


def draw_main_screen(screen, layout, font_big, font_small, grid, selected_color, save_mode, status, cursor_row, cursor_col, debug_key, current_filename):
    scale = layout.s;
    screen.fill(BG);
    screen.blit(font_big.render("SPECTRUM UDG PAINTER", True, TEXT), (scale.v(40), scale.v(70)));
    screen.blit(font_small.render("Arrows cursor. Shift+arrows shift image. +/- canvas. Shift+/- scale.", True, TEXT), (scale.v(40), scale.v(105)));
    screen.blit(font_small.render(status, True, TEXT), (scale.v(40), scale.v(125)));
    shown_name = os.path.basename(current_filename) if current_filename else "UNTITLED";
    screen.blit(font_small.render("FILE: " + shown_name, True, TEXT), (scale.v(40), scale.v(144)));
    debug_key=False;

    if debug_key:
        debug_text = debug_key;
        if len(debug_text) > 84:
            debug_text = debug_text[:84];
        screen.blit(font_small.render(debug_text, True, ERROR), (scale.v(40), scale.v(192)));
    pygame.draw.rect(screen, GRID_BG, (layout.grid_x, layout.grid_y, layout.grid_w, layout.grid_h), border_radius=scale.v(24));

    for row in range(ROWS):
        for col in range(COLS):
            x = layout.grid_x + col * layout.cell;
            y = layout.grid_y + row * layout.cell;
            color_index = grid[row][col];

            if color_index >= 0:
                pygame.draw.rect(screen, SPECTRUM_COLORS[color_index], (x + scale.v(2), y + scale.v(2), layout.cell - scale.v(4), layout.cell - scale.v(4)));

            pygame.draw.rect(screen, GRID_LINE, (x, y, layout.cell, layout.cell), max(1, scale.v(2)));

    pygame.draw.rect(screen, GRID_LINE, (layout.grid_x, layout.grid_y, layout.grid_w, layout.grid_h), max(1, scale.v(5)), border_radius=scale.v(22));

    cursor_x = layout.grid_x + cursor_col * layout.cell;
    cursor_y = layout.grid_y + cursor_row * layout.cell;
    pygame.draw.rect(screen, (255, 255, 255), (cursor_x, cursor_y, layout.cell, layout.cell), max(2, scale.v(5)));
    pygame.draw.rect(screen, (255, 255, 0), (cursor_x + scale.v(4), cursor_y + scale.v(4), layout.cell - scale.v(8), layout.cell - scale.v(8)), max(1, scale.v(2)));

    draw_button(screen, layout.clear_rect, "CLEAR", font_big, BTN, BTN_TEXT, scale);
    draw_button(screen, layout.save_rect, "SAVE", font_big, BTN, BTN_TEXT, scale);
    draw_button(screen, layout.load_rect, "LOAD", font_big, BTN, BTN_TEXT, scale);
    draw_button(screen, layout.mode_rect, "FORMAT: " + save_mode, font_big, BTN2, TEXT, scale);
    draw_button(screen, layout.buttons["CAN-"], "CAN-", font_small, BTN2, TEXT, scale);
    draw_button(screen, layout.buttons["CAN+"], "CAN+", font_small, BTN2, TEXT, scale);
    draw_button(screen, layout.buttons["SCL-"], "SCL-", font_small, BTN2, TEXT, scale);
    draw_button(screen, layout.buttons["SCL+"], "SCL+", font_small, BTN2, TEXT, scale);
    draw_button(screen, layout.buttons["SHL"], "SHL", font_small, BTN2, TEXT, scale);
    draw_button(screen, layout.buttons["SHU"], "SHU", font_small, BTN2, TEXT, scale);
    draw_button(screen, layout.buttons["SHD"], "SHD", font_small, BTN2, TEXT, scale);
    draw_button(screen, layout.buttons["SHR"], "SHR", font_small, BTN2, TEXT, scale);

    for i, rect in enumerate(layout.palette_rects):
        pygame.draw.rect(screen, SPECTRUM_COLORS[i], rect, border_radius=scale.v(8));
        border = TEXT if i == selected_color else GRID_LINE;
        pygame.draw.rect(screen, border, rect, max(1, scale.v(4)), border_radius=scale.v(8));


def handle_load(screen, clock, layout, font_big, font_small, current_filename=None):
    action, filename = pygame_load_dialog(screen, clock, layout.s, font_big, font_small, current_filename);

    if action == "LOAD" and filename:
        try:
            loaded_grid, status = load_udg_file(filename);
            return (loaded_grid, status, filename), False;
        except Exception as exc:
            return (None, "LOAD ERROR: " + str(exc), current_filename), False;

    if action == "QUIT":
        return (None, "LOAD QUIT", current_filename), True;

    return (None, "LOAD CANCELLED", current_filename), False;


def handle_save(screen, clock, layout, font_big, font_small, grid, save_mode, current_filename=None):
    action, filename = pygame_save_dialog(screen, clock, layout.s, font_big, font_small, save_mode, current_filename);

    if action == "SAVE" and filename:
        status = save_udg_file(filename, grid, save_mode);
        return status, False, apply_extension(filename, save_mode);

    if action == "QUIT":
        return "SAVE QUIT", True, current_filename;

    return "SAVE CANCELLED", False, current_filename;


def main():
    pygame.init();
    screen = pygame.display.set_mode((WIDTH, HEIGHT));
    pygame.display.set_caption("Spectrum UDG Painter");
    clock = pygame.time.Clock();
    layout = Layout(screen);
    font_big = layout.s.font(32, bold=True);
    font_small = layout.s.font(20, bold=True);
    grid = empty_grid();
    selected_color = 14;
    save_mode = "COLOR";
    cursor_row = 0;
    cursor_col = 0;
    painting = False;
    paint_value = selected_color;
    last_cell = None;
    status = "READY";
    debug_key = "NO KEY YET";
    scale_reference_grid = None;
    current_filename = None;
    running = True;

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False;

            if event.type == pygame.KEYDOWN:
                debug_key = describe_key_event(event);
                #print(debug_key);

                if event.key == pygame.K_ESCAPE:
                    running = False;

                elif event.key == pygame.K_LEFT:
                    if event.mod & pygame.KMOD_SHIFT:
                        scale_reference_grid = None;
                        grid = shift_grid_wrap(grid, -1, 0);
                        status = "IMAGE SHIFT LEFT";
                    else:
                        cursor_col = max(0, cursor_col - 1);
                        status = "CURSOR: " + str(cursor_row) + "," + str(cursor_col);

                elif event.key == pygame.K_RIGHT:
                    if event.mod & pygame.KMOD_SHIFT:
                        scale_reference_grid = None;
                        grid = shift_grid_wrap(grid, 1, 0);
                        status = "IMAGE SHIFT RIGHT";
                    else:
                        cursor_col = min(COLS - 1, cursor_col + 1);
                        status = "CURSOR: " + str(cursor_row) + "," + str(cursor_col);

                elif event.key == pygame.K_UP:
                    if event.mod & pygame.KMOD_SHIFT:
                        scale_reference_grid = None;
                        grid = shift_grid_wrap(grid, 0, -1);
                        status = "IMAGE SHIFT UP";
                    else:
                        cursor_row = max(0, cursor_row - 1);
                        status = "CURSOR: " + str(cursor_row) + "," + str(cursor_col);

                elif event.key == pygame.K_DOWN:
                    if event.mod & pygame.KMOD_SHIFT:
                        scale_reference_grid = None;
                        grid = shift_grid_wrap(grid, 0, 1);
                        status = "IMAGE SHIFT DOWN";
                    else:
                        cursor_row = min(ROWS - 1, cursor_row + 1);
                        status = "CURSOR: " + str(cursor_row) + "," + str(cursor_col);

                elif event.key == pygame.K_SPACE:
                    scale_reference_grid = None;
                    grid = toggle_cursor_pixel(grid, cursor_row, cursor_col, selected_color);
                    status = "PIXEL TOGGLED";

                elif event_is_plus(event):
                    scale_image = event_requests_scale(event);

                    if scale_image:
                        if scale_reference_grid is None:
                            scale_reference_grid = clone_grid(grid);

                        target_size = max(MIN_GRID_SIZE, min(MAX_GRID_SIZE, max(ROWS, COLS) + 1));
                        grid = resize_grid_scaled(scale_reference_grid, target_size);
                        status = "GRID SCALED UP FROM REFERENCE: " + str(ROWS) + "x" + str(COLS) + " KEY=" + str(event.key);
                    else:
                        scale_reference_grid = None;
                        grid = resize_grid_by_delta(grid, 1, False);
                        status = "GRID CANVAS UP: " + str(ROWS) + "x" + str(COLS) + " KEY=" + str(event.key);

                    layout = Layout(screen);
                    font_big = layout.s.font(32, bold=True);
                    font_small = layout.s.font(20, bold=True);
                    cursor_row, cursor_col = clamp_cursor(cursor_row, cursor_col);

                elif event_is_minus(event):
                    scale_image = event_requests_scale(event);

                    if scale_image:
                        if scale_reference_grid is None:
                            scale_reference_grid = clone_grid(grid);

                        target_size = max(MIN_GRID_SIZE, min(MAX_GRID_SIZE, max(ROWS, COLS) - 1));
                        grid = resize_grid_scaled(scale_reference_grid, target_size);
                        status = "GRID SCALED DOWN FROM REFERENCE: " + str(ROWS) + "x" + str(COLS) + " KEY=" + str(event.key);
                    else:
                        scale_reference_grid = None;
                        grid = resize_grid_by_delta(grid, -1, False);
                        status = "GRID CANVAS DOWN: " + str(ROWS) + "x" + str(COLS) + " KEY=" + str(event.key);

                    layout = Layout(screen);
                    font_big = layout.s.font(32, bold=True);
                    font_small = layout.s.font(20, bold=True);
                    cursor_row, cursor_col = clamp_cursor(cursor_row, cursor_col);

                elif event.key in (pygame.K_0, pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7):
                    selected_color = select_color_from_key(event, selected_color);
                    status = "COLOR: " + str(selected_color);

                elif event.key == pygame.K_c:
                    scale_reference_grid = None;
                    grid = empty_grid();
                    status = "CLEARED";

                elif event.key == pygame.K_s:
                    status, quit_requested, current_filename = handle_save(screen, clock, layout, font_big, font_small, grid, save_mode, current_filename);
                    running = running and not quit_requested;

                elif event.key == pygame.K_l:
                    result, quit_requested = handle_load(screen, clock, layout, font_big, font_small, current_filename);
                    loaded_grid, status, loaded_filename = result;
                    running = running and not quit_requested;

                    if loaded_grid is not None:
                        scale_reference_grid = None;
                        current_filename = loaded_filename;
                        save_mode = mode_from_filename(current_filename, save_mode);
                        grid = loaded_grid;
                        layout = Layout(screen);
                        font_big = layout.s.font(32, bold=True);
                        font_small = layout.s.font(20, bold=True);
                        cursor_row, cursor_col = clamp_cursor(cursor_row, cursor_col);

                elif event.key == pygame.K_m:
                    save_mode = SAVE_MODES[(SAVE_MODES.index(save_mode) + 1) % len(SAVE_MODES)];
                    status = "MODE: " + save_mode;

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos;

                if layout.clear_rect.collidepoint(mx, my):
                    scale_reference_grid = None;
                    grid = empty_grid();
                    status = "CLEARED";

                elif layout.save_rect.collidepoint(mx, my):
                    status, quit_requested, current_filename = handle_save(screen, clock, layout, font_big, font_small, grid, save_mode, current_filename);
                    running = running and not quit_requested;

                elif layout.load_rect.collidepoint(mx, my):
                    result, quit_requested = handle_load(screen, clock, layout, font_big, font_small, current_filename);
                    loaded_grid, status, loaded_filename = result;
                    running = running and not quit_requested;

                    if loaded_grid is not None:
                        scale_reference_grid = None;
                        current_filename = loaded_filename;
                        save_mode = mode_from_filename(current_filename, save_mode);
                        grid = loaded_grid;
                        layout = Layout(screen);
                        font_big = layout.s.font(32, bold=True);
                        font_small = layout.s.font(20, bold=True);
                        cursor_row, cursor_col = clamp_cursor(cursor_row, cursor_col);

                elif layout.mode_rect.collidepoint(mx, my):
                    selected_mode = touch_menu(
                        screen,
                        clock,
                        "SAVE FORMAT",
                        [(mode, mode + " " + SAVE_EXTENSIONS[mode].upper()) for mode in SAVE_MODES],
                    );

                    if selected_mode is not None:
                        save_mode = selected_mode;
                        status = "MODE: " + save_mode;
                    else:
                        status = "MODE CANCELLED";

                elif layout.buttons["CAN-"].collidepoint(mx, my):
                    scale_reference_grid = None;
                    grid = resize_grid_by_delta(grid, -1, False);
                    layout = Layout(screen);
                    font_big = layout.s.font(32, bold=True);
                    font_small = layout.s.font(20, bold=True);
                    cursor_row, cursor_col = clamp_cursor(cursor_row, cursor_col);
                    status = "CANVAS DOWN: " + str(ROWS) + "x" + str(COLS);

                elif layout.buttons["CAN+"].collidepoint(mx, my):
                    scale_reference_grid = None;
                    grid = resize_grid_by_delta(grid, 1, False);
                    layout = Layout(screen);
                    font_big = layout.s.font(32, bold=True);
                    font_small = layout.s.font(20, bold=True);
                    cursor_row, cursor_col = clamp_cursor(cursor_row, cursor_col);
                    status = "CANVAS UP: " + str(ROWS) + "x" + str(COLS);

                elif layout.buttons["SCL-"].collidepoint(mx, my):
                    if scale_reference_grid is None:
                        scale_reference_grid = clone_grid(grid);
                    target_size = max(MIN_GRID_SIZE, min(MAX_GRID_SIZE, max(ROWS, COLS) - 1));
                    grid = resize_grid_scaled(scale_reference_grid, target_size);
                    layout = Layout(screen);
                    font_big = layout.s.font(32, bold=True);
                    font_small = layout.s.font(20, bold=True);
                    cursor_row, cursor_col = clamp_cursor(cursor_row, cursor_col);
                    status = "SCALE DOWN: " + str(ROWS) + "x" + str(COLS);

                elif layout.buttons["SCL+"].collidepoint(mx, my):
                    if scale_reference_grid is None:
                        scale_reference_grid = clone_grid(grid);
                    target_size = max(MIN_GRID_SIZE, min(MAX_GRID_SIZE, max(ROWS, COLS) + 1));
                    grid = resize_grid_scaled(scale_reference_grid, target_size);
                    layout = Layout(screen);
                    font_big = layout.s.font(32, bold=True);
                    font_small = layout.s.font(20, bold=True);
                    cursor_row, cursor_col = clamp_cursor(cursor_row, cursor_col);
                    status = "SCALE UP: " + str(ROWS) + "x" + str(COLS);

                elif layout.buttons["SHL"].collidepoint(mx, my):
                    scale_reference_grid = None;
                    grid = shift_grid_wrap(grid, -1, 0);
                    status = "IMAGE SHIFT LEFT";

                elif layout.buttons["SHR"].collidepoint(mx, my):
                    scale_reference_grid = None;
                    grid = shift_grid_wrap(grid, 1, 0);
                    status = "IMAGE SHIFT RIGHT";

                elif layout.buttons["SHU"].collidepoint(mx, my):
                    scale_reference_grid = None;
                    grid = shift_grid_wrap(grid, 0, -1);
                    status = "IMAGE SHIFT UP";

                elif layout.buttons["SHD"].collidepoint(mx, my):
                    scale_reference_grid = None;
                    grid = shift_grid_wrap(grid, 0, 1);
                    status = "IMAGE SHIFT DOWN";

                else:
                    for i, rect in enumerate(layout.palette_rects):
                        if rect.collidepoint(mx, my):
                            selected_color = i;
                            status = "COLOR: " + str(i);

                    found = cell_from_pos(mx, my, layout);

                    if found is not None:
                        row, col = found;
                        cursor_row = row;
                        cursor_col = col;
                        painting = True;
                        last_cell = found;

                        if grid[row][col] == -1:
                            paint_value = selected_color;
                        else:
                            paint_value = -1;

                        scale_reference_grid = None;
                        grid[row][col] = paint_value;

            if event.type == pygame.MOUSEMOTION and painting:
                mx, my = event.pos;
                found = cell_from_pos(mx, my, layout);

                if found is not None and found != last_cell:
                    row, col = found;
                    cursor_row = row;
                    cursor_col = col;
                    scale_reference_grid = None;
                    grid[row][col] = paint_value;
                    last_cell = found;

            if event.type == pygame.MOUSEBUTTONUP:
                painting = False;
                last_cell = None;

        draw_main_screen(screen, layout, font_big, font_small, grid, selected_color, save_mode, status, cursor_row, cursor_col, debug_key, current_filename);
        pygame.display.flip();
        clock.tick(60);

    pygame.quit();
    sys.exit(0);


if __name__ == "__main__":
    main();
