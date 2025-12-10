/**********************************************************************************************
*
*   raylib - Advance Game template
*
*   Ending Screen Functions Definitions (Init, Update, Draw, Unload)
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
#include <pthread.h>

//----------------------------------------------------------------------------------
// Global variable definitions
//----------------------------------------------------------------------------------
int local_high_score;

//----------------------------------------------------------------------------------
// Module Variables Definition (local)
//----------------------------------------------------------------------------------
static int framesCounter = 0;
static int finishScreen = 0;

// Two cursors
static IMUCursor right_cursor;
static IMUCursor left_cursor;

//Buttons
static Button play_again_button;
static Button quit_button;

extern pthread_mutex_t pkt_mutex;
extern struct dp_packet right_pkt;
extern struct dp_packet left_pkt;  // Add this extern
static int right_events = 0;
static int left_events = 0;

//----------------------------------------------------------------------------------
// Ending Screen Functions Definition
//----------------------------------------------------------------------------------

// Ending Screen Initialization logic
void InitEndingScreen(void)
{
    framesCounter = 0;
    finishScreen = 0;
    
    // Init buttons
    Rectangle temp_rect = (Rectangle){screenWidth/2, screenHeight/2 + 130, 200, 80};
    InitButton(&play_again_button, temp_rect, BLUE, RED, "Play Again");
    
    temp_rect = (Rectangle){screenWidth/2 + 250, screenHeight/2 + 130, 200, 80};
    InitButton(&quit_button, temp_rect, RED, BLUE, "Quit");
    
    //Init cursors
    InitCursors(&right_cursor, &left_cursor);
    
    if(score > local_high_score){
        local_high_score = score;
    }
}

// Ending Screen Update logic
void UpdateEndingScreen(void)
{
    struct dp_packet right_local, left_local;

    pthread_mutex_lock(&pkt_mutex);
    right_local = right_pkt;
    left_local = left_pkt;
    right_events += right_button_events;
    right_button_events = 0;
    left_events += left_button_events;
    left_button_events = 0;
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
        left_events++;
    }
    #endif
    
    bool right_pressed = false;
    if(right_events > 0){
        right_pressed = true;
        right_events--;
    }
    
    bool left_pressed = false;
    if(left_events > 0){
        left_pressed = true;
        left_events--;
    }
    
    bool play_again_r = IsButtonPressed(&play_again_button, right_cursor.pos, right_pressed);
    bool play_again_l = IsButtonPressed(&play_again_button, left_cursor.pos, left_pressed);
    
    bool play_again = play_again_l || play_again_r;
    
    bool quit_r = IsButtonPressed(&quit_button, right_cursor.pos, right_pressed);
    bool quit_l = IsButtonPressed(&quit_button, left_cursor.pos, left_pressed);
    
    bool quit = quit_l || quit_r;
    
    if(quit){
        playing = false;
    }
    
    // Press enter or tap to return to TITLE screen
    // IsGestureDetected(GESTURE_TAP)
    if (IsKeyPressed(KEY_ENTER) || play_again)
    {
        finishScreen = 1; //1 is start screen
        //PlaySound(fxCoin);
    }
}

// Ending Screen Draw logic
void DrawEndingScreen(void)
{
    // Draw background
    DrawRectangle(0, 0, GetScreenWidth(), GetScreenHeight(), WHITE);
    
    if (!right_cursor.calibrated && !left_cursor.calibrated) {
        DrawText("Calibrating IMUs - Keep Still!", screenWidth / 2 - 150, 150, 20, MAROON);
    }
    
    char buffer[64];
    // Score counter
    int fontSize = 60;
    sprintf(buffer, "Score: %d", score);
    int textWidth = MeasureText(buffer, fontSize);
    int x = (screenWidth - textWidth) / 2;
    DrawText(buffer, x, 100, fontSize, BLACK);
    
    // local high score counter
    fontSize = 30;
    sprintf(buffer, "Local High Score: %d", local_high_score);
    textWidth = MeasureText(buffer, fontSize);
    x = (screenWidth - textWidth) / 2;
    DrawText(buffer, x, 170, fontSize, BLACK);
    
    // Draw buttons
    DrawButton(&play_again_button);
    DrawButton(&quit_button);
    
    DrawCursor(&left_cursor);
    DrawCursor(&right_cursor);
    }

// Ending Screen Unload logic
void UnloadEndingScreen(void)
{
    // TODO: Unload ENDING screen variables here!
}

// Ending Screen should finish?
int FinishEndingScreen(void)
{
    return finishScreen;
}