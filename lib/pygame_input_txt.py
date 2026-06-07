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

import pygame;


BLACK = (0, 0, 0);
BLUE = (0, 0, 205);
CYAN = (0, 205, 205);
BRIGHT_RED = (255, 0, 0);
BRIGHT_GREEN = (0, 255, 0);
BRIGHT_CYAN = (0, 255, 255);
BRIGHT_YELLOW = (255, 255, 0);
BRIGHT_WHITE = (255, 255, 255);
BG = BLACK;
PAPER = BLUE;
PAPER2 = (0, 0, 90);
INK = BRIGHT_WHITE;
INK2 = BRIGHT_YELLOW;
MUTED = CYAN;
BORDER = BRIGHT_CYAN;
BTN = BRIGHT_YELLOW;
BTN2 = BLUE;
BTN_TEXT = BLACK;
NAV_REPEAT_DELAY = 320;
NAV_REPEAT_INTERVAL = 70;
DEFAULT_ALLOWED_CHARS = "aáâāàäbcçdeéêēèëfghiíîīìïjklmnñoóôōòöpqrstuúûūùüvwxyzAÁÂĀÀÄBCÇDEÉÊĒÈËFGHIÍÎĪÌÏJKLMNÑOÓÔŌÒÖPQRSTUÚÛŪÙÜVWXYZ0123456789_- %|=[]<>{}@#$&+()*\"':;!?,.¡¿/|' ";


def scale_value(screen, value):
    height = screen.get_height();
    return max(1, int(round(value * height / 1280)));


def font(screen, points, bold=False):
    return pygame.font.SysFont("monospace", max(8, scale_value(screen, points)), bold=bold);


def rect(screen, x, y, w, h):
    return pygame.Rect(scale_value(screen, x), scale_value(screen, y), scale_value(screen, w), scale_value(screen, h));


def draw_spectrum_frame(screen, target_rect, color=BORDER):
    pygame.draw.rect(screen, color, target_rect, max(1, scale_value(screen, 4)));
    pygame.draw.rect(screen, INK2, target_rect.inflate(-scale_value(screen, 10), -scale_value(screen, 10)), max(1, scale_value(screen, 2)));


def draw_button(screen, target_rect, label, text_font, bg_color, fg_color):
    rendered = text_font.render(label, True, fg_color);
    pygame.draw.rect(screen, bg_color, target_rect);
    pygame.draw.rect(screen, BRIGHT_WHITE, target_rect, max(1, scale_value(screen, 3)));
    screen.blit(rendered, rendered.get_rect(center=target_rect.center));


def draw_header(screen, font_big, font_small, title, prompt):
    header_rect = rect(screen, 20, 20, 680, 130);
    screen.fill(BG);
    pygame.draw.rect(screen, PAPER2, header_rect);
    draw_spectrum_frame(screen, header_rect);
    screen.blit(font_big.render(title, True, INK2), (scale_value(screen, 45), scale_value(screen, 45)));
    screen.blit(font_small.render(prompt, True, INK), (scale_value(screen, 45), scale_value(screen, 95)));


def allowed(char, allowed_chars):
    return allowed_chars is None or char in allowed_chars;


def get_visible_line(text_font, text_value, cursor_pos, max_width):
    start = 0;
    while text_font.size(text_value[start:cursor_pos])[0] > max_width and start < cursor_pos:
        start += 1;
    end = cursor_pos;
    while end < len(text_value) and text_font.size(text_value[start:end + 1])[0] <= max_width:
        end += 1;
    return text_value[start:end], start;


def make_nav_buttons(screen, y):
    labels = ["LEFT", "RIGHT", "UP", "DOWN", "INS", "DEL", "HOME", "END"];
    buttons = [];
    width = screen.get_width();
    margin = scale_value(screen, 20);
    gap = scale_value(screen, 6);
    btn_w = (width - margin * 2 - gap * (len(labels) - 1)) // len(labels);
    btn_h = scale_value(screen, 116);
    for i, label in enumerate(labels):
        x = margin + i * (btn_w + gap);
        buttons.append((label, pygame.Rect(x, y, btn_w, btn_h)));
    return buttons;


def draw_nav_buttons(screen, buttons, text_font, insert_mode=True, pressed_label=None):
    for label, target_rect in buttons:
        color = BTN2;
        if label == "INS":
            color = BRIGHT_GREEN if insert_mode else BRIGHT_RED;
        if label == pressed_label:
            color = BRIGHT_CYAN;
        draw_button(screen, target_rect, label, text_font, color, INK);


def get_nav_label_at_pos(buttons, mx, my):
    for label, target_rect in buttons:
        if target_rect.collidepoint(mx, my):
            return label;
    return None;


def should_repeat_nav(pressed_label, pressed_since, last_repeat):
    now = pygame.time.get_ticks();
    if pressed_label is None or pressed_label == "INS":
        return False, last_repeat;
    if now - pressed_since < NAV_REPEAT_DELAY:
        return False, last_repeat;
    if now - last_repeat >= NAV_REPEAT_INTERVAL:
        return True, now;
    return False, last_repeat;


def nav_action_line(label, text_value, cursor_pos, insert_mode):
    if label == "LEFT":
        cursor_pos = max(0, cursor_pos - 1);
    elif label == "RIGHT":
        cursor_pos = min(len(text_value), cursor_pos + 1);
    elif label == "INS":
        insert_mode = not insert_mode;
    elif label == "DEL" and cursor_pos < len(text_value):
        text_value = text_value[:cursor_pos] + text_value[cursor_pos + 1:];
    elif label == "HOME":
        cursor_pos = 0;
    elif label == "END":
        cursor_pos = len(text_value);
    return text_value, cursor_pos, insert_mode;


def nav_action_area(label, lines, cursor_row, cursor_col, insert_mode):
    if label == "LEFT":
        if cursor_col > 0:
            cursor_col -= 1;
        elif cursor_row > 0:
            cursor_row -= 1;
            cursor_col = len(lines[cursor_row]);
    elif label == "RIGHT":
        if cursor_col < len(lines[cursor_row]):
            cursor_col += 1;
        elif cursor_row + 1 < len(lines):
            cursor_row += 1;
            cursor_col = 0;
    elif label == "UP" and cursor_row > 0:
        cursor_row -= 1;
        cursor_col = min(cursor_col, len(lines[cursor_row]));
    elif label == "DOWN" and cursor_row + 1 < len(lines):
        cursor_row += 1;
        cursor_col = min(cursor_col, len(lines[cursor_row]));
    elif label == "INS":
        insert_mode = not insert_mode;
    elif label == "DEL":
        line = lines[cursor_row];
        if cursor_col < len(line):
            lines[cursor_row] = line[:cursor_col] + line[cursor_col + 1:];
        elif cursor_row + 1 < len(lines):
            lines[cursor_row] += lines[cursor_row + 1];
            lines.pop(cursor_row + 1);
    elif label == "HOME":
        cursor_col = 0;
    elif label == "END":
        cursor_col = len(lines[cursor_row]);
    return lines, cursor_row, cursor_col, insert_mode;


def ensure_cursor_visible(cursor_row, scroll_row, visible_rows):
    if cursor_row < scroll_row:
        return cursor_row;
    if cursor_row >= scroll_row + visible_rows:
        return cursor_row - visible_rows + 1;
    return scroll_row;


def input_line(screen, clock, title="SPECTRUM INPUT LINE", prompt="Use Android keyboard or touch cursor keys.", default_text="", placeholder="", allowed_chars=DEFAULT_ALLOWED_CHARS, max_length=-1):
    font_big = font(screen, 30, True);
    font_small = font(screen, 18, True);
    width = screen.get_width();
    height = screen.get_height();
    text_value = default_text;
    cursor_pos = len(text_value);
    cursor_visible = True;
    cursor_timer = 0;
    insert_mode = True;
    input_rect = rect(screen, 40, 500, 640, 84);
    ok_rect = rect(screen, 70, 660, 260, 112);
    cancel_rect = pygame.Rect(width - scale_value(screen, 330), scale_value(screen, 660), scale_value(screen, 260), scale_value(screen, 112));
    nav_buttons = make_nav_buttons(screen, scale_value(screen, 805));
    pressed_label = None;
    pressed_since = 0;
    last_repeat = 0;
    pygame.key.start_text_input();
    pygame.key.set_text_input_rect(input_rect);
    while True:
        cursor_timer += clock.get_time();
        if cursor_timer >= 500:
            cursor_visible = not cursor_visible;
            cursor_timer = 0;
        repeat, last_repeat = should_repeat_nav(pressed_label, pressed_since, last_repeat);
        if repeat:
            text_value, cursor_pos, insert_mode = nav_action_line(pressed_label, text_value, cursor_pos, insert_mode);
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.key.stop_text_input();
                return None;
            if event.type == pygame.TEXTINPUT:
                for char in event.text:
                    if not allowed(char, allowed_chars):
                        continue;
                    if max_length != -1 and len(text_value) >= max_length:
                        continue;
                    if insert_mode or cursor_pos >= len(text_value):
                        text_value = text_value[:cursor_pos] + char + text_value[cursor_pos:];
                    else:
                        text_value = text_value[:cursor_pos] + char + text_value[cursor_pos + 1:];
                    cursor_pos += 1;
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.key.stop_text_input();
                    return None;
                if event.key == pygame.K_RETURN:
                    pygame.key.stop_text_input();
                    return text_value;
                if event.key == pygame.K_BACKSPACE and cursor_pos > 0:
                    text_value = text_value[:cursor_pos - 1] + text_value[cursor_pos:];
                    cursor_pos -= 1;
                if event.key == pygame.K_DELETE:
                    text_value, cursor_pos, insert_mode = nav_action_line("DEL", text_value, cursor_pos, insert_mode);
                if event.key == pygame.K_LEFT:
                    text_value, cursor_pos, insert_mode = nav_action_line("LEFT", text_value, cursor_pos, insert_mode);
                if event.key == pygame.K_RIGHT:
                    text_value, cursor_pos, insert_mode = nav_action_line("RIGHT", text_value, cursor_pos, insert_mode);
                if event.key == pygame.K_HOME:
                    text_value, cursor_pos, insert_mode = nav_action_line("HOME", text_value, cursor_pos, insert_mode);
                if event.key == pygame.K_END:
                    text_value, cursor_pos, insert_mode = nav_action_line("END", text_value, cursor_pos, insert_mode);
                if event.key == pygame.K_INSERT:
                    insert_mode = not insert_mode;
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos;
                if input_rect.collidepoint(mx, my):
                    pygame.key.start_text_input();
                    pygame.key.set_text_input_rect(input_rect);
                if ok_rect.collidepoint(mx, my):
                    pygame.key.stop_text_input();
                    return text_value;
                if cancel_rect.collidepoint(mx, my):
                    pygame.key.stop_text_input();
                    return None;
                label = get_nav_label_at_pos(nav_buttons, mx, my);
                if label is not None:
                    text_value, cursor_pos, insert_mode = nav_action_line(label, text_value, cursor_pos, insert_mode);
                    pressed_label = label;
                    pressed_since = pygame.time.get_ticks();
                    last_repeat = pressed_since;
            if event.type == pygame.MOUSEBUTTONUP:
                pressed_label = None;
        draw_header(screen, font_big, font_small, title, prompt);
        pygame.draw.rect(screen, PAPER, input_rect);
        draw_spectrum_frame(screen, input_rect);
        text_x = input_rect.x + scale_value(screen, 18);
        text_y = input_rect.y + scale_value(screen, 24);
        max_text_width = input_rect.width - scale_value(screen, 36);
        if text_value:
            visible_text, view_start = get_visible_line(font_big, text_value, cursor_pos, max_text_width);
            before_cursor = text_value[view_start:cursor_pos];
            screen.blit(font_big.render(visible_text, True, INK), (text_x, text_y));
            cursor_x = text_x + font_big.size(before_cursor)[0] + scale_value(screen, 4);
        else:
            screen.blit(font_big.render(placeholder, True, MUTED), (text_x, text_y));
            cursor_x = text_x + scale_value(screen, 4);
        if cursor_visible:
            pygame.draw.rect(screen, INK2, pygame.Rect(cursor_x, text_y + scale_value(screen, 2), scale_value(screen, 5), font_big.get_height() - scale_value(screen, 4)));
        mode_label = "INSERT" if insert_mode else "OVERWRITE";
        screen.blit(font_small.render("MODE: " + mode_label + "   LEN: " + str(len(text_value)), True, INK2), (scale_value(screen, 45), input_rect.bottom + scale_value(screen, 14)));
        draw_button(screen, ok_rect, "OK", font_big, BTN, BTN_TEXT);
        draw_button(screen, cancel_rect, "CANCEL", font_big, BTN2, INK);
        draw_nav_buttons(screen, nav_buttons, font_small, insert_mode, pressed_label);
        pygame.display.flip();
        clock.tick(60);


def input_area(screen, clock, title="SPECTRUM TEXT AREA", prompt="Multiline editor. OK accepts. CANCEL exits.", default_text="", allowed_chars=DEFAULT_ALLOWED_CHARS, max_lines=-1, max_cols=-1, visible_rows=8):
    font_big = font(screen, 25, True);
    font_small = font(screen, 17, True);
    width = screen.get_width();
    height = screen.get_height();
    lines = default_text.split("\n") if default_text else [""];
    cursor_row = len(lines) - 1;
    cursor_col = len(lines[cursor_row]);
    scroll_row = 0;
    cursor_visible = True;
    cursor_timer = 0;
    insert_mode = True;
    area_rect = rect(screen, 35, 180, 650, visible_rows * 36 + 30);
    ok_rect = rect(screen, 70, 980, 260, 112);
    cancel_rect = pygame.Rect(width - scale_value(screen, 330), scale_value(screen, 980), scale_value(screen, 260), scale_value(screen, 112));
    nav_buttons = make_nav_buttons(screen, scale_value(screen, 1120));
    pressed_label = None;
    pressed_since = 0;
    last_repeat = 0;
    pygame.key.start_text_input();
    pygame.key.set_text_input_rect(area_rect);
    while True:
        cursor_timer += clock.get_time();
        if cursor_timer >= 500:
            cursor_visible = not cursor_visible;
            cursor_timer = 0;
        scroll_row = ensure_cursor_visible(cursor_row, scroll_row, visible_rows);
        repeat, last_repeat = should_repeat_nav(pressed_label, pressed_since, last_repeat);
        if repeat:
            lines, cursor_row, cursor_col, insert_mode = nav_action_area(pressed_label, lines, cursor_row, cursor_col, insert_mode);
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.key.stop_text_input();
                return None;
            if event.type == pygame.TEXTINPUT:
                for char in event.text:
                    if not allowed(char, allowed_chars):
                        continue;
                    if max_cols != -1 and len(lines[cursor_row]) >= max_cols:
                        continue;
                    line = lines[cursor_row];
                    if insert_mode or cursor_col >= len(line):
                        lines[cursor_row] = line[:cursor_col] + char + line[cursor_col:];
                    else:
                        lines[cursor_row] = line[:cursor_col] + char + line[cursor_col + 1:];
                    cursor_col += 1;
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.key.stop_text_input();
                    return None;
                if event.key == pygame.K_TAB:
                    pygame.key.stop_text_input();
                    return "\n".join(lines);
                if event.key == pygame.K_RETURN:
                    if max_lines == -1 or len(lines) < max_lines:
                        current = lines[cursor_row];
                        lines[cursor_row] = current[:cursor_col];
                        lines.insert(cursor_row + 1, current[cursor_col:]);
                        cursor_row += 1;
                        cursor_col = 0;
                if event.key == pygame.K_BACKSPACE:
                    if cursor_col > 0:
                        line = lines[cursor_row];
                        lines[cursor_row] = line[:cursor_col - 1] + line[cursor_col:];
                        cursor_col -= 1;
                    elif cursor_row > 0:
                        previous_len = len(lines[cursor_row - 1]);
                        lines[cursor_row - 1] += lines[cursor_row];
                        lines.pop(cursor_row);
                        cursor_row -= 1;
                        cursor_col = previous_len;
                key_to_label = {pygame.K_DELETE: "DEL", pygame.K_LEFT: "LEFT", pygame.K_RIGHT: "RIGHT", pygame.K_UP: "UP", pygame.K_DOWN: "DOWN", pygame.K_HOME: "HOME", pygame.K_END: "END"};
                if event.key in key_to_label:
                    lines, cursor_row, cursor_col, insert_mode = nav_action_area(key_to_label[event.key], lines, cursor_row, cursor_col, insert_mode);
                if event.key == pygame.K_INSERT:
                    insert_mode = not insert_mode;
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos;
                if area_rect.collidepoint(mx, my):
                    pygame.key.start_text_input();
                    pygame.key.set_text_input_rect(area_rect);
                if ok_rect.collidepoint(mx, my):
                    pygame.key.stop_text_input();
                    return "\n".join(lines);
                if cancel_rect.collidepoint(mx, my):
                    pygame.key.stop_text_input();
                    return None;
                label = get_nav_label_at_pos(nav_buttons, mx, my);
                if label is not None:
                    lines, cursor_row, cursor_col, insert_mode = nav_action_area(label, lines, cursor_row, cursor_col, insert_mode);
                    pressed_label = label;
                    pressed_since = pygame.time.get_ticks();
                    last_repeat = pressed_since;
            if event.type == pygame.MOUSEBUTTONUP:
                pressed_label = None;
        draw_header(screen, font_big, font_small, title, prompt);
        pygame.draw.rect(screen, PAPER, area_rect);
        draw_spectrum_frame(screen, area_rect);
        text_x = area_rect.x + scale_value(screen, 18);
        text_y = area_rect.y + scale_value(screen, 15);
        line_height = scale_value(screen, 36);
        max_text_width = area_rect.width - scale_value(screen, 36);
        shown_lines = lines[scroll_row:scroll_row + visible_rows];
        for i, line in enumerate(shown_lines):
            real_row = scroll_row + i;
            y = text_y + i * line_height;
            if real_row == cursor_row:
                visible_text, view_start = get_visible_line(font_big, line, cursor_col, max_text_width);
                before_cursor = line[view_start:cursor_col];
                cursor_x = text_x + font_big.size(before_cursor)[0] + scale_value(screen, 4);
            else:
                visible_text, unused = get_visible_line(font_big, line, 0, max_text_width);
            screen.blit(font_big.render(visible_text, True, INK), (text_x, y));
            if real_row == cursor_row and cursor_visible:
                pygame.draw.rect(screen, INK2, pygame.Rect(cursor_x, y + scale_value(screen, 2), scale_value(screen, 5), font_big.get_height() - scale_value(screen, 4)));
        mode_label = "INSERT" if insert_mode else "OVERWRITE";
        counter = "MODE: " + mode_label + "  ROW: " + str(cursor_row + 1) + "  COL: " + str(cursor_col);
        screen.blit(font_small.render(counter, True, INK2), (scale_value(screen, 40), area_rect.bottom + scale_value(screen, 12)));
        draw_button(screen, ok_rect, "OK", font_big, BTN, BTN_TEXT);
        draw_button(screen, cancel_rect, "CANCEL", font_big, BTN2, INK);
        draw_nav_buttons(screen, nav_buttons, font_small, insert_mode, pressed_label);
        pygame.display.flip();
        clock.tick(60);


def main():
    pygame.init();
    screen = pygame.display.set_mode((720, 1280));
    pygame.display.set_caption("ZX Spectrum Text Widgets");
    clock = pygame.time.Clock();
    result_line = input_line(screen, clock, title="ZX INPUT LINE", prompt="Hold cursor buttons to repeat.", placeholder="READY", max_length=-1);
    print("LINE RESULT:");
    print(result_line);
    result_area = input_area(screen, clock, title="ZX TEXT AREA", prompt="Hold arrows. Android keyboard writes.", default_text="10 PRINT \"HELLO\"\n20 GO TO 10", max_lines=-1, max_cols=-1, visible_rows=8);
    print("AREA RESULT:");
    print(result_area);
    pygame.quit();


if __name__ == "__main__":
    main();
