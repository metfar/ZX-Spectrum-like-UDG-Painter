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

import os;
import pygame;


BLACK = (0, 0, 0);
BLUE = (0, 0, 205);
BRIGHT_CYAN = (0, 255, 255);
BRIGHT_YELLOW = (255, 255, 0);
BRIGHT_WHITE = (255, 255, 255);
BG = BLACK;
PANEL = BLUE;
INK = BRIGHT_WHITE;
INK2 = BRIGHT_YELLOW;
BORDER = BRIGHT_CYAN;
BTN = BRIGHT_YELLOW;
BTN2 = BLUE;
BTN_TEXT = BLACK;
ERROR = (255, 0, 0);
DIR_COLOR = (0, 255, 255);
NAV_REPEAT_DELAY = 320;
NAV_REPEAT_INTERVAL = 90;


def scale_value(screen, value):
    return max(1, int(round(value * screen.get_height() / 1280)));


def font(screen, points, bold=False):
    return pygame.font.SysFont("monospace", max(8, scale_value(screen, points)), bold=bold);


def draw_button(screen, target_rect, label, text_font, bg_color, fg_color):
    rendered = text_font.render(label, True, fg_color);
    pygame.draw.rect(screen, bg_color, target_rect);
    pygame.draw.rect(screen, BRIGHT_WHITE, target_rect, max(1, scale_value(screen, 3)));
    screen.blit(rendered, rendered.get_rect(center=target_rect.center));


def normalize_extensions(extension):
    if extension is None:
        return [];

    if isinstance(extension, str):
        if extension in ("", "*", "*.*"):
            return [];
        return [extension.lower()];

    return [item.lower() for item in extension];


def extension_matches(filename, extensions):
    if not extensions:
        return True;

    lower_name = filename.lower();
    return any(lower_name.endswith(item) for item in extensions);


def get_entries(directory=".", extension=".udg", show_dirs=True):
    entries = [];
    extensions = normalize_extensions(extension);
    directory = os.path.abspath(directory);

    parent = os.path.abspath(os.path.join(directory, os.pardir));

    if show_dirs and parent != directory:
        entries.append({"kind": "parent", "name": "..", "path": parent, "label": "[..]"});

    try:
        names = os.listdir(directory);
    except OSError:
        return entries;

    dirs = [];
    files = [];

    for filename in names:
        path = os.path.join(directory, filename);

        if show_dirs and os.path.isdir(path):
            dirs.append({"kind": "dir", "name": filename, "path": path, "label": "[" + filename + "/]"});
        elif os.path.isfile(path) and extension_matches(filename, extensions):
            files.append({"kind": "file", "name": filename, "path": path, "label": filename});

    dirs.sort(key=lambda item: item["name"].lower());
    files.sort(key=lambda item: item["name"].lower());
    entries.extend(dirs);
    entries.extend(files);
    return entries;


def short_path(path, max_chars=48):
    text = os.path.abspath(path);

    if len(text) <= max_chars:
        return text;

    return "..." + text[-(max_chars - 3):];


def clamp_index(index, count):
    if count <= 0:
        return 0;

    return max(0, min(count - 1, index));


def keep_visible(selected, scroll, visible):
    if selected < scroll:
        scroll = selected;

    if selected >= scroll + visible:
        scroll = selected - visible + 1;

    return max(0, scroll);


def enter_directory(current_directory, new_directory):
    try:
        return os.path.abspath(new_directory), 0, 0;
    except OSError:
        return os.path.abspath(current_directory), 0, 0;


def select_file(screen, clock, directory=".", extension=".udg", title="SELECT FILE", allow_dirs=True):
    font_big = font(screen, 32, True);
    font_small = font(screen, 21, True);
    font_tiny = font(screen, 15, True);
    width = screen.get_width();
    current_directory = os.path.abspath(directory);
    selected = 0;
    scroll = 0;
    cancel_rect = pygame.Rect(scale_value(screen, 70), scale_value(screen, 1120), width - scale_value(screen, 140), scale_value(screen, 105));
    top = scale_value(screen, 220);
    row_h = scale_value(screen, 88);
    visible_rows = 9;
    pressed_dir = None;
    pressed_since = 0;
    last_repeat = 0;
    status = "";

    while True:
        entries = get_entries(current_directory, extension, allow_dirs);
        selected = clamp_index(selected, len(entries));
        scroll = keep_visible(selected, scroll, visible_rows);
        now = pygame.time.get_ticks();

        if pressed_dir is not None and entries and now - pressed_since >= NAV_REPEAT_DELAY and now - last_repeat >= NAV_REPEAT_INTERVAL:
            if pressed_dir == "UP":
                selected = clamp_index(selected - 1, len(entries));
            elif pressed_dir == "DOWN":
                selected = clamp_index(selected + 1, len(entries));
            elif pressed_dir == "PAGEUP":
                selected = clamp_index(selected - visible_rows, len(entries));
            elif pressed_dir == "PAGEDOWN":
                selected = clamp_index(selected + visible_rows, len(entries));

            last_repeat = now;

        row_rects = [];

        for index, entry in enumerate(entries[scroll:scroll + visible_rows]):
            real_index = scroll + index;
            rect = pygame.Rect(scale_value(screen, 50), top + index * row_h, width - scale_value(screen, 100), row_h - scale_value(screen, 10));
            row_rects.append((real_index, rect, entry));

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None;

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None;

                if event.key == pygame.K_UP and entries:
                    selected = clamp_index(selected - 1, len(entries));

                elif event.key == pygame.K_DOWN and entries:
                    selected = clamp_index(selected + 1, len(entries));

                elif event.key == pygame.K_PAGEUP and entries:
                    selected = clamp_index(selected - visible_rows, len(entries));

                elif event.key == pygame.K_PAGEDOWN and entries:
                    selected = clamp_index(selected + visible_rows, len(entries));

                elif event.key == pygame.K_HOME and entries:
                    selected = 0;

                elif event.key == pygame.K_END and entries:
                    selected = len(entries) - 1;

                elif event.key in (pygame.K_BACKSPACE, pygame.K_LEFT):
                    parent = os.path.abspath(os.path.join(current_directory, os.pardir));
                    if parent != current_directory:
                        current_directory, selected, scroll = enter_directory(current_directory, parent);
                        status = "UP: " + short_path(current_directory, 40);

                elif event.key == pygame.K_RIGHT and entries:
                    entry = entries[selected];
                    if entry["kind"] in ("dir", "parent"):
                        current_directory, selected, scroll = enter_directory(current_directory, entry["path"]);
                        status = "DIR: " + short_path(current_directory, 40);

                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE) and entries:
                    entry = entries[selected];
                    if entry["kind"] in ("dir", "parent"):
                        current_directory, selected, scroll = enter_directory(current_directory, entry["path"]);
                        status = "DIR: " + short_path(current_directory, 40);
                    elif entry["kind"] == "file":
                        return entry["path"];

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos;

                if cancel_rect.collidepoint(mx, my):
                    return None;

                for real_index, target_rect, entry in row_rects:
                    if target_rect.collidepoint(mx, my):
                        selected = real_index;

                        if entry["kind"] in ("dir", "parent"):
                            current_directory, selected, scroll = enter_directory(current_directory, entry["path"]);
                            status = "DIR: " + short_path(current_directory, 40);
                        else:
                            return entry["path"];

                if my < top and entries:
                    selected = clamp_index(selected - 1, len(entries));
                    pressed_dir = "UP";
                    pressed_since = now;
                    last_repeat = now;
                elif my > top + visible_rows * row_h and entries:
                    selected = clamp_index(selected + 1, len(entries));
                    pressed_dir = "DOWN";
                    pressed_since = now;
                    last_repeat = now;

            if event.type == pygame.MOUSEBUTTONUP:
                pressed_dir = None;

        screen.fill(BG);
        title_rect = pygame.Rect(scale_value(screen, 20), scale_value(screen, 20), width - scale_value(screen, 40), scale_value(screen, 150));
        pygame.draw.rect(screen, PANEL, title_rect);
        pygame.draw.rect(screen, BORDER, title_rect, max(1, scale_value(screen, 4)));
        pygame.draw.rect(screen, INK2, title_rect.inflate(-scale_value(screen, 10), -scale_value(screen, 10)), max(1, scale_value(screen, 2)));
        screen.blit(font_big.render(title, True, INK2), (scale_value(screen, 45), scale_value(screen, 48)));
        screen.blit(font_small.render(short_path(current_directory, 42), True, INK), (scale_value(screen, 45), scale_value(screen, 102)));
        hint = "UP/DOWN SELECT  ENTER OPEN  LEFT/BACKSPACE PARENT";
        screen.blit(font_tiny.render(hint, True, INK2), (scale_value(screen, 45), scale_value(screen, 140)));

        if status:
            screen.blit(font_tiny.render(status, True, INK), (scale_value(screen, 55), scale_value(screen, 182)));

        if not entries:
            screen.blit(font_small.render("No entries found.", True, ERROR), (scale_value(screen, 60), top));

        for real_index, target_rect, entry in row_rects:
            selected_row = real_index == selected;
            color = BTN if selected_row else BTN2;
            text_color = BTN_TEXT if selected_row else (DIR_COLOR if entry["kind"] in ("dir", "parent") else INK);
            draw_button(screen, target_rect, entry["label"], font_small, color, text_color);

        if scroll > 0:
            screen.blit(font_small.render("^", True, INK2), (width - scale_value(screen, 50), top - scale_value(screen, 35)));

        if scroll + visible_rows < len(entries):
            screen.blit(font_small.render("v", True, INK2), (width - scale_value(screen, 50), top + visible_rows * row_h));

        draw_button(screen, cancel_rect, "CANCEL", font_big, BTN2, INK);
        pygame.display.flip();
        clock.tick(60);


def main():
    pygame.init();
    screen = pygame.display.set_mode((720, 1280));
    pygame.display.set_caption("ZX File Dialog");
    clock = pygame.time.Clock();
    result = select_file(screen, clock, ".", [".udg", ".bin", ".xpm", ".ico"], "SELECT FILE");
    print("Selected file:", result);
    pygame.quit();


if __name__ == "__main__":
    main();


def strip_extension(filename, extension):
    extensions = normalize_extensions(extension);

    for item in extensions:
        if filename.lower().endswith(item):
            return filename[:-len(item)];

    return filename;


def ensure_extension(filename, extension):
    extensions = normalize_extensions(extension);

    if not extensions:
        return filename;

    if extension_matches(filename, extensions):
        return filename;

    return filename + extensions[0];


def confirm_overwrite(screen, clock, filename):
    from .pygame_msgbox import message_box;

    return message_box(
        screen,
        clock,
        title="FILE EXISTS",
        message="Overwrite this file?\n" + filename,
        buttons=["OVERWRITE", "RENAME", "CANCEL"],
    );


def edit_save_name(screen, clock, current_name, extension):
    from .pygame_input_txt import input_line;

    clean_name = strip_extension(current_name, extension);
    result = input_line(
        screen,
        clock,
        title="SAVE AS",
        prompt="Write filename. Extension is added automatically.",
        default_text=clean_name,
        placeholder="FILENAME",
        allowed_chars="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_- .",
        max_length=64,
    );

    return result;


def save_file_dialog(screen, clock, directory=".", extension=".udg", title="SAVE FILE", default_name="graphic", allow_dirs=True):
    font_big = font(screen, 32, True);
    font_small = font(screen, 21, True);
    font_tiny = font(screen, 15, True);
    width = screen.get_width();
    current_directory = os.path.abspath(directory);
    filename = strip_extension(default_name, extension);
    selected = 0;
    scroll = 0;
    top = scale_value(screen, 210);
    row_h = scale_value(screen, 74);
    visible_rows = 8;
    name_rect = pygame.Rect(scale_value(screen, 50), scale_value(screen, 820), width - scale_value(screen, 100), scale_value(screen, 86));
    save_rect = pygame.Rect(scale_value(screen, 50), scale_value(screen, 930), width - scale_value(screen, 100), scale_value(screen, 96));
    cancel_rect = pygame.Rect(scale_value(screen, 50), scale_value(screen, 1045), width - scale_value(screen, 100), scale_value(screen, 96));
    pressed_dir = None;
    pressed_since = 0;
    last_repeat = 0;
    status = "ENTER opens dirs/files. E edits name. S saves.";

    while True:
        entries = get_entries(current_directory, extension, allow_dirs);
        selected = clamp_index(selected, len(entries));
        scroll = keep_visible(selected, scroll, visible_rows);
        now = pygame.time.get_ticks();

        if pressed_dir is not None and entries and now - pressed_since >= NAV_REPEAT_DELAY and now - last_repeat >= NAV_REPEAT_INTERVAL:
            if pressed_dir == "UP":
                selected = clamp_index(selected - 1, len(entries));
            elif pressed_dir == "DOWN":
                selected = clamp_index(selected + 1, len(entries));
            elif pressed_dir == "PAGEUP":
                selected = clamp_index(selected - visible_rows, len(entries));
            elif pressed_dir == "PAGEDOWN":
                selected = clamp_index(selected + visible_rows, len(entries));

            last_repeat = now;

        row_rects = [];

        for index, entry in enumerate(entries[scroll:scroll + visible_rows]):
            real_index = scroll + index;
            rect = pygame.Rect(scale_value(screen, 50), top + index * row_h, width - scale_value(screen, 100), row_h - scale_value(screen, 8));
            row_rects.append((real_index, rect, entry));

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None;

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None;

                if event.key == pygame.K_UP and entries:
                    selected = clamp_index(selected - 1, len(entries));

                elif event.key == pygame.K_DOWN and entries:
                    selected = clamp_index(selected + 1, len(entries));

                elif event.key == pygame.K_PAGEUP and entries:
                    selected = clamp_index(selected - visible_rows, len(entries));

                elif event.key == pygame.K_PAGEDOWN and entries:
                    selected = clamp_index(selected + visible_rows, len(entries));

                elif event.key == pygame.K_HOME and entries:
                    selected = 0;

                elif event.key == pygame.K_END and entries:
                    selected = len(entries) - 1;

                elif event.key in (pygame.K_BACKSPACE, pygame.K_LEFT):
                    parent = os.path.abspath(os.path.join(current_directory, os.pardir));
                    if parent != current_directory:
                        current_directory, selected, scroll = enter_directory(current_directory, parent);
                        status = "UP: " + short_path(current_directory, 40);

                elif event.key == pygame.K_RIGHT and entries:
                    entry = entries[selected];
                    if entry["kind"] in ("dir", "parent"):
                        current_directory, selected, scroll = enter_directory(current_directory, entry["path"]);
                        status = "DIR: " + short_path(current_directory, 40);

                elif event.key == pygame.K_e:
                    new_name = edit_save_name(screen, clock, filename, extension);
                    if new_name is not None:
                        filename = new_name;

                elif event.key == pygame.K_s:
                    target = os.path.join(current_directory, ensure_extension(filename.strip(), extension));
                    if os.path.exists(target):
                        answer = confirm_overwrite(screen, clock, target);
                        if answer == "OVERWRITE":
                            return target;
                        if answer == "RENAME":
                            new_name = edit_save_name(screen, clock, filename, extension);
                            if new_name is not None:
                                filename = new_name;
                        if answer == "CANCEL" or answer is None:
                            status = "SAVE CANCELLED";
                    else:
                        return target;

                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    if entries:
                        entry = entries[selected];
                        if entry["kind"] in ("dir", "parent"):
                            current_directory, selected, scroll = enter_directory(current_directory, entry["path"]);
                            status = "DIR: " + short_path(current_directory, 40);
                        elif entry["kind"] == "file":
                            filename = strip_extension(entry["name"], extension);
                            status = "NAME: " + filename;

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos;

                if name_rect.collidepoint(mx, my):
                    new_name = edit_save_name(screen, clock, filename, extension);
                    if new_name is not None:
                        filename = new_name;

                elif save_rect.collidepoint(mx, my):
                    target = os.path.join(current_directory, ensure_extension(filename.strip(), extension));
                    if os.path.exists(target):
                        answer = confirm_overwrite(screen, clock, target);
                        if answer == "OVERWRITE":
                            return target;
                        if answer == "RENAME":
                            new_name = edit_save_name(screen, clock, filename, extension);
                            if new_name is not None:
                                filename = new_name;
                        if answer == "CANCEL" or answer is None:
                            status = "SAVE CANCELLED";
                    else:
                        return target;

                elif cancel_rect.collidepoint(mx, my):
                    return None;

                else:
                    for real_index, target_rect, entry in row_rects:
                        if target_rect.collidepoint(mx, my):
                            selected = real_index;

                            if entry["kind"] in ("dir", "parent"):
                                current_directory, selected, scroll = enter_directory(current_directory, entry["path"]);
                                status = "DIR: " + short_path(current_directory, 40);
                            else:
                                filename = strip_extension(entry["name"], extension);
                                status = "NAME: " + filename;

                    if my < top and entries:
                        selected = clamp_index(selected - 1, len(entries));
                        pressed_dir = "UP";
                        pressed_since = now;
                        last_repeat = now;
                    elif my > top + visible_rows * row_h and my < name_rect.y and entries:
                        selected = clamp_index(selected + 1, len(entries));
                        pressed_dir = "DOWN";
                        pressed_since = now;
                        last_repeat = now;

            if event.type == pygame.MOUSEBUTTONUP:
                pressed_dir = None;

        screen.fill(BG);
        title_rect = pygame.Rect(scale_value(screen, 20), scale_value(screen, 20), width - scale_value(screen, 40), scale_value(screen, 145));
        pygame.draw.rect(screen, PANEL, title_rect);
        pygame.draw.rect(screen, BORDER, title_rect, max(1, scale_value(screen, 4)));
        pygame.draw.rect(screen, INK2, title_rect.inflate(-scale_value(screen, 10), -scale_value(screen, 10)), max(1, scale_value(screen, 2)));
        screen.blit(font_big.render(title, True, INK2), (scale_value(screen, 45), scale_value(screen, 45)));
        screen.blit(font_small.render(short_path(current_directory, 42), True, INK), (scale_value(screen, 45), scale_value(screen, 96)));
        screen.blit(font_tiny.render(status, True, INK2), (scale_value(screen, 45), scale_value(screen, 132)));

        if not entries:
            screen.blit(font_small.render("No entries found.", True, ERROR), (scale_value(screen, 60), top));

        for real_index, target_rect, entry in row_rects:
            selected_row = real_index == selected;
            color = BTN if selected_row else BTN2;
            text_color = BTN_TEXT if selected_row else (DIR_COLOR if entry["kind"] in ("dir", "parent") else INK);
            draw_button(screen, target_rect, entry["label"], font_small, color, text_color);

        if scroll > 0:
            screen.blit(font_small.render("^", True, INK2), (width - scale_value(screen, 50), top - scale_value(screen, 30)));

        if scroll + visible_rows < len(entries):
            screen.blit(font_small.render("v", True, INK2), (width - scale_value(screen, 50), top + visible_rows * row_h));

        pygame.draw.rect(screen, PANEL, name_rect);
        pygame.draw.rect(screen, BORDER, name_rect, max(1, scale_value(screen, 3)));
        screen.blit(font_small.render("NAME: " + ensure_extension(filename, extension), True, INK), (name_rect.x + scale_value(screen, 18), name_rect.y + scale_value(screen, 26)));
        draw_button(screen, save_rect, "SAVE HERE", font_big, BTN, BTN_TEXT);
        draw_button(screen, cancel_rect, "CANCEL", font_big, BTN2, INK);
        pygame.display.flip();
        clock.tick(60);
