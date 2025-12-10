#ifndef BUTTON_H
#define BUTTON_H

#include "raylib.h"

typedef struct {
    Rectangle rect;
    Color color;
    Color pressed_color;
    const char *text;
} Button;


// Parameters
// Rectangle with position centered
void InitButton(Button *button, Rectangle rect, Color color, Color pressed_color, const char *text);

void DrawButton(Button *button);

bool IsButtonPressed(Button *button, Vector2 pos, bool clicked);

#endif