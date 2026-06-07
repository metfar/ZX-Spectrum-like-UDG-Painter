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
NAV_REPEAT_DELAY = 320;
NAV_REPEAT_INTERVAL = 90;


def scale_value(screen, value):
    return max(1, int(round(value * screen.get_height() / 1280)));


def font(screen, points, bold=False):
    return pygame.font.SysFont("monospace", max(8, scale_value(screen, points)), bold=bold);


def draw_button(screen, target_rect, label, text_font, selected=False):
    rendered = text_font.render(label, True, BTN_TEXT if selected else INK);
    pygame.draw.rect(screen, BTN if selected else BTN2, target_rect);
    pygame.draw.rect(screen, BRIGHT_WHITE, target_rect, max(1, scale_value(screen, 3)));
    screen.blit(rendered, rendered.get_rect(center=target_rect.center));


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


def move_selected(selected, delta, count):
    return clamp_index(selected + delta, count);


def touch_menu(screen, clock, title="MENU", items=None):
    if items is None:
        items = [("OK", "OK")];

    if not items:
        items = [(None, "NO OPTIONS")];

    font_big = font(screen, 32, True);
    font_small = font(screen, 22, True);
    width = screen.get_width();
    selected = 0;
    scroll = 0;
    visible = 8;
    top = scale_value(screen, 210);
    row_h = scale_value(screen, 105);
    cancel_rect = pygame.Rect(scale_value(screen, 70), scale_value(screen, 1120), width - scale_value(screen, 140), scale_value(screen, 105));
    pressed_dir = None;
    pressed_since = 0;
    last_repeat = 0;

    while True:
        now = pygame.time.get_ticks();

        if pressed_dir is not None and now - pressed_since >= NAV_REPEAT_DELAY and now - last_repeat >= NAV_REPEAT_INTERVAL:
            if pressed_dir == "UP":
                selected = move_selected(selected, -1, len(items));
            elif pressed_dir == "DOWN":
                selected = move_selected(selected, 1, len(items));
            elif pressed_dir == "PAGEUP":
                selected = move_selected(selected, -visible, len(items));
            elif pressed_dir == "PAGEDOWN":
                selected = move_selected(selected, visible, len(items));

            last_repeat = now;

        scroll = keep_visible(selected, scroll, visible);
        row_rects = [];

        for index, item in enumerate(items[scroll:scroll + visible]):
            real_index = scroll + index;
            row_rects.append((real_index, pygame.Rect(scale_value(screen, 50), top + index * row_h, width - scale_value(screen, 100), row_h - scale_value(screen, 12))));

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None;

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None;

                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    return items[selected][0];

                if event.key == pygame.K_UP:
                    selected = move_selected(selected, -1, len(items));

                elif event.key == pygame.K_DOWN:
                    selected = move_selected(selected, 1, len(items));

                elif event.key == pygame.K_PAGEUP:
                    selected = move_selected(selected, -visible, len(items));

                elif event.key == pygame.K_PAGEDOWN:
                    selected = move_selected(selected, visible, len(items));

                elif event.key == pygame.K_HOME:
                    selected = 0;

                elif event.key == pygame.K_END:
                    selected = len(items) - 1;

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos;

                if cancel_rect.collidepoint(mx, my):
                    return None;

                for real_index, target_rect in row_rects:
                    if target_rect.collidepoint(mx, my):
                        selected = real_index;
                        return items[selected][0];

                if my < top:
                    pressed_dir = "UP";
                    selected = move_selected(selected, -1, len(items));
                    pressed_since = now;
                    last_repeat = now;
                elif my > top + visible * row_h:
                    pressed_dir = "DOWN";
                    selected = move_selected(selected, 1, len(items));
                    pressed_since = now;
                    last_repeat = now;

            if event.type == pygame.MOUSEBUTTONUP:
                pressed_dir = None;

        screen.fill(BG);
        title_rect = pygame.Rect(scale_value(screen, 20), scale_value(screen, 20), width - scale_value(screen, 40), scale_value(screen, 140));
        pygame.draw.rect(screen, PANEL, title_rect);
        pygame.draw.rect(screen, BORDER, title_rect, max(1, scale_value(screen, 4)));
        pygame.draw.rect(screen, INK2, title_rect.inflate(-scale_value(screen, 10), -scale_value(screen, 10)), max(1, scale_value(screen, 2)));
        screen.blit(font_big.render(title, True, INK2), (scale_value(screen, 45), scale_value(screen, 62)));

        for real_index, target_rect in row_rects:
            draw_button(screen, target_rect, items[real_index][1], font_small, real_index == selected);

        draw_button(screen, cancel_rect, "CANCEL", font_big, False);

        if scroll > 0:
            screen.blit(font_small.render("^", True, INK2), (width - scale_value(screen, 50), top - scale_value(screen, 35)));

        if scroll + visible < len(items):
            screen.blit(font_small.render("v", True, INK2), (width - scale_value(screen, 50), top + visible * row_h));

        hint = "ARROWS SELECT   ENTER/SPACE OK   ESC CANCEL";
        screen.blit(font(screen, 15, True).render(hint, True, INK), (scale_value(screen, 45), scale_value(screen, 165)));
        pygame.display.flip();
        clock.tick(60);


def main():
    pygame.init();
    screen = pygame.display.set_mode((720, 1280));
    clock = pygame.time.Clock();
    result = touch_menu(screen, clock, "ZX MENU", [("NEW", "NEW FILE"), ("LOAD", "LOAD FILE"), ("QUIT", "QUIT")]);
    print("Result:", result);
    pygame.quit();


if __name__ == "__main__":
    main();
