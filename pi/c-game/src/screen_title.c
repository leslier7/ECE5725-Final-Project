/**********************************************************************************************
*
*   raylib - Advance Game template
*
*   Title Screen Functions Definitions (Init, Update, Draw, Unload)
*
*   Copyright (c) 2014-2022 Ramon Santamaria (@raysan5)
*
*   This software is provided "as-is", without any express or implied warranty. In no event
*   will the authors be held liable for any damages arising from the use of this software.
*
*   Permission is granted to anyone to use this software for any purpose, including commercial
*   applications, and to alter it and redistribute it freely, subject to the following restrictions:
*
*     1. The origin of this software must not be misrepresented; you must not claim that you
*     wrote the original software. If you use this software in a product, an acknowledgment
*     in the product documentation would be appreciated but is not required.
*
*     2. Altered source versions must be plainly marked as such, and must not be misrepresented
*     as being the original software.
*
*     3. This notice may not be removed or altered from any source distribution.
*
**********************************************************************************************/

#include "raylib.h"
#include "screens.h"
#include "imu_cursor.h"
#include "button.h"
#include <stdio.h>
#include <math.h>
#include <pthread.h>
#include <stdlib.h>

//----------------------------------------------------------------------------------
// Module Variables Definition (local)
//----------------------------------------------------------------------------------
static int framesCounter = 0;
static int finishScreen = 0;

// Two cursors
static IMUCursor right_cursor;
static IMUCursor left_cursor;

// Buttons
static Button start_button;

extern pthread_mutex_t pkt_mutex;
extern struct dp_packet right_pkt;
extern struct dp_packet left_pkt;  // Add this extern
static int events = 0;

//----------------------------------------------------------------------------------
// Title Screen Functions Definition
//----------------------------------------------------------------------------------

// Title Screen Initialization logic
void InitTitleScreen(void)
{
    framesCounter = 0;
    finishScreen = 0;
    
    // Init cursors
    Vector2 temp_pos = (Vector2){screenWidth/2 + 50, screenHeight/2};
    InitCursor(&right_cursor, temp_pos, PURPLE, "R");
    
    temp_pos = (Vector2){screenWidth/2 - 50, screenHeight/2};
    InitCursor(&left_cursor, temp_pos, BLUE, "L");
    
    // Init buttons
    Rectangle temp_rect = (Rectangle){screenWidth/2, screenHeight/2 + 130, 150, 80};
    InitButton(&start_button, temp_rect, BLUE, RED, "Start");
}

// Title Screen Update logic
void UpdateTitleScreen(void)
{
    // TODO: Update TITLE screen variables here!
    struct dp_packet right_local, left_local;
    
    pthread_mutex_lock(&pkt_mutex);
    right_local = right_pkt;
    left_local = left_pkt;
    events = right_button_events;
    right_button_events = 0;
    pthread_mutex_unlock(&pkt_mutex);
    
    float dt = GetFrameTime();
    if (dt > 0.1f) dt = 0.016f;
    
    // Update right cursor
    if(right_connected){
        if (!UpdateCursorCalibration(&right_cursor, (Vector2){right_local.accel.x, right_local.accel.y})) {
            UpdateCursorMovement(&right_cursor, (Vector2){right_local.accel.x, right_local.accel.y}, dt);
        }
    }
    
    // Update left cursor
    if(left_connected){
        if (!UpdateCursorCalibration(&left_cursor, (Vector2){left_local.accel.x, left_local.accel.y})) {
            UpdateCursorMovement(&left_cursor, (Vector2){left_local.accel.x, left_local.accel.y}, dt);
        }
    }
    
    //Use mouse for left cursor control
    #ifdef _DEBUG
    left_cursor.pos = GetMousePosition();
    if(IsGestureDetected(GESTURE_TAP)){
        events++;
    }
    #endif
    
    bool imu_button_pressed = false;
    if(events > 0){
        imu_button_pressed = true;
        events--;
    }
    
    bool start_game = IsButtonPressed(&start_button, left_cursor.pos, imu_button_pressed);
    
    // Press start button or press enter
    if (IsKeyPressed(KEY_ENTER) || start_game)
    {
        //finishScreen = 1;   // OPTIONS
        finishScreen = 2;   // GAMEPLAY
        //PlaySound(fxCoin);
    }
}

// Title Screen Draw logic
void DrawTitleScreen(void)
{
    // Draw background
    DrawRectangle(0, 0, GetScreenWidth(), GetScreenHeight(), WHITE);
    
    // Draw Buttons
    DrawButton(&start_button);
    
    if(right_connected && left_connected){
        if (!right_cursor.calibrated && !left_cursor.calibrated) {
            DrawText("Calibrating IMUs - Keep Still!", screenWidth / 2 - 150, 150, 20, MAROON);
        }
    } else {
        const char *text = "Please plug both controllers in!";
        int fontSize = 30;
        int textWidth = MeasureText(text, fontSize);
        int x = (screenWidth - textWidth) / 2;
        DrawText(text, x, 150, fontSize, BLACK);
    }
    
    // Draw cursors
    DrawCursor(&right_cursor);
    DrawCursor(&left_cursor);
    
    // Draw Title
    //DrawText("Fruit Ninja Clone!", screenWidth / 2 - 210, 70, 55, BLACK);
    const char *title = "Fruit Ninja Clone!";
    int fontSize = 55;
    int textWidth = MeasureText(title, fontSize);
    int x = (screenWidth - textWidth) / 2;
    DrawText(title, x, 70, fontSize, BLACK);
}

// Title Screen Unload logic
void UnloadTitleScreen(void)
{
    // TODO: Unload TITLE screen variables here!
}

// Title Screen should finish?
int FinishTitleScreen(void)
{
    return finishScreen;
}
