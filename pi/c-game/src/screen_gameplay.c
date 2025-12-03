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
// Global variable definitions
//----------------------------------------------------------------------------------
int score;


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
static int events = 0;

//static Fruit testFruit;
//static Fruit testFruit2;

#define NUM_FRUITS 3
static Fruit fruits[NUM_FRUITS];

//----------------------------------------------------------------------------------
// Gameplay Screen Functions Definition
//----------------------------------------------------------------------------------

// Gameplay Screen Initialization logic
void InitGameplayScreen(void)
{
    framesCounter = 0;
    finishScreen = 0;
    
    score = 0;
    
    
    Vector2 temp_pos = (Vector2){screenWidth/2 + 50, screenHeight/2};
    InitCursor(&right_cursor, temp_pos, PURPLE, "R");
    
    temp_pos = (Vector2){screenWidth/2 - 50, screenHeight/2};
    InitCursor(&left_cursor, temp_pos, BLUE, "L");
    
    
    
    srand(time(NULL));  // Only once!
    //InitFruit(&testFruit);
    //InitFruitDebug(&testFruit2, 0, (Vector2){screenWidth/2, screenHeight/2}, (Vector2){0, 0});
    for(int i = 0; i < NUM_FRUITS; i++){
        InitFruit(&fruits[i]);
    }
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
    #ifdef _DEBUG
    left_cursor.pos = GetMousePosition();
    left_cursor.calibrated = true;
    #elif
    if (!UpdateCursorCalibration(&left_cursor, (Vector2){left_local.accel.x, left_local.accel.y})) {
        UpdateCursorMovement(&left_cursor, (Vector2){left_local.accel.x, left_local.accel.y}, dt);
    }
    #endif
    
    // Button event: reset both cursors
    if (events > 0) {
        printf("\nResetting cursors");
        Vector2 temp_pos = (Vector2){screenWidth/2 + 50, screenHeight/2};
        ResetCursor(&right_cursor, temp_pos);
        temp_pos = (Vector2){screenWidth/2 - 50, screenHeight/2};
        ResetCursor(&left_cursor, temp_pos);
        events--;
    }
    
    
    // if(UpdateFruitPosition(&testFruit) == 2){
    //     printf("\nTest fruit offscreen");
    //     InitFruit(&testFruit);
    // }
    if(left_cursor.calibrated == 1 && right_cursor.calibrated == 1){
        for(int i = 0; i < NUM_FRUITS; i++){
            if(UpdateFruitPosition(&fruits[i]) == 2){
                InitFruit(&fruits[i]);
            }
        }
    }
    
    
    // if(CursorColision(&right_cursor, &testFruit2)){
    //     printf("\nCursor and fruit are colliding!");
    //     score++;
    // }
    
    for(int i = 0; i < NUM_FRUITS; i++){
        if(CursorColision(&right_cursor, &fruits[i])){
            
            if(fruits[i].type == BOMB){
                printf("\nHit bomb. Game over");
                finishScreen = 1; // Go to the ending screen
            } else {
                score++;
                InitFruit(&fruits[i]);
            }
        }
        
        if(CursorColision(&left_cursor, &fruits[i])){
            
            if(fruits[i].type == BOMB){
                printf("\nHit bomb. Game over");
                finishScreen = 1; // Go to the ending screen
            } else {
                score++;
                InitFruit(&fruits[i]);
            }
        }
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
    // Score counter
    sprintf(buffer, "Score: %d", score);
    DrawText(buffer, 10, 10, 30, BLACK);
    
    //FPS counter
    sprintf(buffer, "FPS: %d", GetFPS());
    DrawText(buffer, 10, screenHeight - 20, 20, BLACK);
    
    #ifdef _DEBUG
    // Right cursor debug (left side of screen)
    sprintf(buffer, "R Vel: %.1f, %.1f", right_cursor.vel.x, right_cursor.vel.y);
    DrawText(buffer, 10, 40, 16, BLACK);
    sprintf(buffer, "R Pos: %.0f, %.0f", right_cursor.pos.x, right_cursor.pos.y);
    DrawText(buffer, 10, 56, 16, BLACK);
    
    // Left cursor debug (right side of screen)
    sprintf(buffer, "L Vel: %.1f, %.1f", left_cursor.vel.x, left_cursor.vel.y);
    DrawText(buffer, 10, 76, 16, BLACK);
    sprintf(buffer, "L Pos: %.0f, %.0f", left_cursor.pos.x, left_cursor.pos.y);
    DrawText(buffer, 10, 92, 16, BLACK);
    #endif
    
    // Draw fruit
    // DrawFruit(&testFruit);
    // DrawFruit(&testFruit2);
    
    if(left_cursor.calibrated == 1 && right_cursor.calibrated == 1){
        for(int i = 0; i < NUM_FRUITS; i++){
            DrawFruit(&fruits[i]);
        }
    }
    
    // Draw cursors
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