#include "button.h"
#include "raylib.h"

#ifdef _DEBUG
#include <stdio.h>
#endif

#define BUTTON_OUTLINE 14

void InitButton(Button *button, Rectangle rect, Color color, Color pressed_color, const char *text){
    // Turn middle position to corner position
    Rectangle temp_rect = {rect.x - rect.width/2, rect.y - rect.height/2, rect.width, rect.height};
    button->rect = temp_rect;
    button->color = color;
    button->pressed_color = pressed_color;
    button->text = text;
}

void DrawButton(Button *button){
    
    // Draw outside rect
    DrawRectangleRec(button->rect, button->color);
    
    // Draw inside rect
    // Rectangle temp_rect = {button->rect.x+BUTTON_OUTLINE/2, button->rect.y+BUTTON_OUTLINE/2, button->rect.width-BUTTON_OUTLINE, button->rect.height-BUTTON_OUTLINE};
    // DrawRectangleRec(temp_rect, WHITE);
    

    const int padding = 8;
    int availWidth = (int)button->rect.width - 2*padding;
    if (availWidth < 4) availWidth = 4;

    // one reference measurement
    const int refFont = 10;
    int refWidth = MeasureText(button->text, refFont);

    int fontSize;
    if (refWidth > 0) {
        // scale font size from reference (fast, single-measure)
        fontSize = (int)((double)availWidth * refFont / refWidth);
    } else {
        fontSize = refFont;
    }

    // clamp to button height
    int maxFont = (int)button->rect.height - 4;
    if (fontSize > maxFont) fontSize = maxFont;
    if (fontSize < 1) fontSize = 1;

    // estimate text width instead of calling MeasureText again (faster)
    int estTextWidth = refWidth > 0 ? (int)((double)refWidth * fontSize / refFont) : availWidth;
    int x = (int)(button->rect.x + (button->rect.width - estTextWidth) / 2.0f);
    int y = (int)(button->rect.y + (button->rect.height - fontSize) / 2.0f);

    DrawText(button->text, x, y, fontSize, BLACK);
    
}

bool IsButtonPressed(Button *button, Vector2 pos, bool clicked){
    
    if(CheckCollisionPointRec(pos, button->rect) && clicked){
        #ifdef _DEBUG
        printf("\nButton pressed");
        #endif
        return true;
    } //return true;
    
    return false;
}