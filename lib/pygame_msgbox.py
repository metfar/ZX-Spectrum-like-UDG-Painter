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


def scale_value(screen, value):
    return max(1, int(round(value * screen.get_height() / 1280)));


def font(screen, points, bold=False):
    return pygame.font.SysFont("monospace", max(8, scale_value(screen, points)), bold=bold);


def wrap_text(text_font, text, max_width):
    lines = [];
    for raw_line in text.split("\n"):
        words = raw_line.split(" ");
        line = "";
        for word in words:
            candidate = word if not line else line + " " + word;
            if text_font.size(candidate)[0] <= max_width:
                line = candidate;
            else:
                if line:
                    lines.append(line);
                line = word;
        lines.append(line);
    return lines;


def draw_button(screen, target_rect, label, text_font, bg_color, fg_color):
    rendered = text_font.render(label, True, fg_color);
    pygame.draw.rect(screen, bg_color, target_rect);
    pygame.draw.rect(screen, BRIGHT_WHITE, target_rect, max(1, scale_value(screen, 3)));
    screen.blit(rendered, rendered.get_rect(center=target_rect.center));


def message_box(screen, clock, title="MESSAGE", message="", buttons=None):
    if buttons is None:
        buttons = ["OK"];
    font_big = font(screen, 30, True);
    font_small = font(screen, 20, True);
    width = screen.get_width();
    height = screen.get_height();
    panel_rect = pygame.Rect(scale_value(screen, 40), scale_value(screen, 230), width - scale_value(screen, 80), scale_value(screen, 660));
    button_h = scale_value(screen, 100);
    button_gap = scale_value(screen, 20);
    button_w = (panel_rect.width - button_gap * (len(buttons) + 1)) // len(buttons);
    button_rects = [];
    for index, label in enumerate(buttons):
        x = panel_rect.x + button_gap + index * (button_w + button_gap);
        y = panel_rect.bottom - button_h - button_gap;
        button_rects.append((label, pygame.Rect(x, y, button_w, button_h)));
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None;
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_ESCAPE, pygame.K_RETURN]:
                    return buttons[0];
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos;
                for label, target_rect in button_rects:
                    if target_rect.collidepoint(mx, my):
                        return label;
        screen.fill(BG);
        pygame.draw.rect(screen, PANEL, panel_rect);
        pygame.draw.rect(screen, BORDER, panel_rect, max(1, scale_value(screen, 4)));
        pygame.draw.rect(screen, INK2, panel_rect.inflate(-scale_value(screen, 10), -scale_value(screen, 10)), max(1, scale_value(screen, 2)));
        screen.blit(font_big.render(title, True, INK2), (panel_rect.x + scale_value(screen, 24), panel_rect.y + scale_value(screen, 28)));
        lines = wrap_text(font_small, message, panel_rect.width - scale_value(screen, 48));
        y = panel_rect.y + scale_value(screen, 100);
        for line in lines[:12]:
            screen.blit(font_small.render(line, True, INK), (panel_rect.x + scale_value(screen, 24), y));
            y += scale_value(screen, 32);
        for label, target_rect in button_rects:
            draw_button(screen, target_rect, label, font_small, BTN if label == buttons[0] else BTN2, BTN_TEXT if label == buttons[0] else INK);
        pygame.display.flip();
        clock.tick(60);


def main():
    pygame.init();
    screen = pygame.display.set_mode((720, 1280));
    clock = pygame.time.Clock();
    result = message_box(screen, clock, "ZX MESSAGE", "This is a Spectrum-style message box.", ["OK", "CANCEL"]);
    print("Result:", result);
    pygame.quit();


if __name__ == "__main__":
    main();
