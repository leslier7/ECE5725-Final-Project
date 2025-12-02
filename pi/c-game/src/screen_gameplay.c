/**********************************************************************************************
*
*   raylib - Advance Game template
*
*   Gameplay Screen Functions Definitions (Init, Update, Draw, Unload)
*
*   Copyright (c) 2014-2022 Ramon Santamaria (@raysan5)
* 
*   Modified by Robbie Leslie 2025
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
#include "fruit.h"
#include <stdio.h>
#include <math.h>
#include <pthread.h>
#include <time.h>
#include <stdlib.h>

//----------------------------------------------------------------------------------
// Module Variables Definition (local)
//----------------------------------------------------------------------------------
static int framesCounter = 0;
static int finishScreen = 0;

// Two cursors
static IMUCursor right_cursor;
static IMUCursor left_cursor;

extern pthread_mutex_t pkt_mutex;
extern struct dp_packet right_pkt;
extern struct dp_packet left_pkt;  // Add this extern
int events = 0;

static Fruit testFruit;
static Fruit testFruit2;

//----------------------------------------------------------------------------------
// Gameplay Screen Functions Definition
//----------------------------------------------------------------------------------

// Gameplay Screen Initialization logic
void InitGameplayScreen(void)
{
    framesCounter = 0;
    finishScreen = 0;
    
    InitCursor(&right_cursor, BLACK);
    InitCursor(&left_cursor, BLUE);
    
    // Debug
    left_cursor.pos = (Vector2){300, 300};
    
    srand(time(NULL));  // Only once!
    InitFruit(&testFruit);
    InitFruitDebug(&testFruit2, 0, (Vector2){screenWidth/2, screenHeight/2}, (Vector2){0, 0});
}

void UpdateGameplayScreen(void)
{
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
    if (!UpdateCursorCalibration(&right_cursor, (Vector2){right_local.accel.x, right_local.accel.y})) {
        UpdateCursorMovement(&right_cursor, (Vector2){right_local.accel.x, right_local.accel.y}, dt);
    }
    
    // Update left cursor
    if (!UpdateCursorCalibration(&left_cursor, (Vector2){left_local.accel.x, left_local.accel.y})) {
        UpdateCursorMovement(&left_cursor, (Vector2){left_local.accel.x, left_local.accel.y}, dt);
    }
    
    // Button event: reset both cursors
    if (events > 0) {
        printf("\nResetting cursors");
        ResetCursor(&right_cursor);
        ResetCursor(&left_cursor);
        events--;
    }
    
    
    if(UpdateFruitPosition(&testFruit) == 2){
        printf("\nTest fruit offscreen");
        InitFruit(&testFruit);
    }
    
    
    if(CursorColision(&right_cursor, &testFruit2)){
        printf("\nCursor and fruit are colliding!");
    } else {
        printf("\nNo collision");
    }
}

void DrawGameplayScreen(void)
{   
    // Draw background
    DrawRectangle(0, 0, GetScreenWidth(), GetScreenHeight(), WHITE);
    
    if (!right_cursor.calibrated || !left_cursor.calibrated) {
        DrawText("Calibrating IMUs - Keep Still!", screenWidth / 2 - 150, 150, 20, MAROON);
    }
    
    char buffer[64];
    sprintf(buffer, "FPS: %d", GetFPS());
    DrawText(buffer, 10, 10, 20, BLACK);
    
    // Right cursor debug (left side of screen)
    sprintf(buffer, "R Vel: %.1f, %.1f", right_cursor.vel.x, right_cursor.vel.y);
    DrawText(buffer, 10, 30, 16, BLACK);
    sprintf(buffer, "R Pos: %.0f, %.0f", right_cursor.pos.x, right_cursor.pos.y);
    DrawText(buffer, 10, 46, 16, BLACK);
    
    // Left cursor debug (right side of screen)
    sprintf(buffer, "L Vel: %.1f, %.1f", left_cursor.vel.x, left_cursor.vel.y);
    DrawText(buffer, 10, 66, 16, BLACK);
    sprintf(buffer, "L Pos: %.0f, %.0f", left_cursor.pos.x, left_cursor.pos.y);
    DrawText(buffer, 10, 82, 16, BLACK);
    
    // Draw fruit
    DrawFruit(&testFruit);
    DrawFruit(&testFruit2);
    
    // Draw cursors with different colors
    DrawCursor(&right_cursor);
    DrawCursor(&left_cursor);
}

// Gameplay Screen Unload logic
void UnloadGameplayScreen(void)
{
    // TODO: Unload GAMEPLAY screen variables here!
}

// Gameplay Screen should finish?
int FinishGameplayScreen(void)
{
    return finishScreen;
}