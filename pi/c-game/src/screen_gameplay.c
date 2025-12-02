/**********************************************************************************************
*
*   raylib - Advance Game template
*
*   Gameplay Screen Functions Definitions (Init, Update, Draw, Unload)
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
#include <stdio.h>
#include <math.h>
#include <pthread.h>

//----------------------------------------------------------------------------------
// Module Variables Definition (local)
//----------------------------------------------------------------------------------
static int framesCounter = 0;
static int finishScreen = 0;

static Vector2 player_pos;
static Vector2 imu_vel;

// calibration state
static Vector2 imu_bias;
static Vector2 imu_calib_accum;
static int imu_calib_count;
static const int IMU_CALIB_SAMPLES = 120; /* ~2s @60Hz */
static int imu_calibrated;

// Complementary filter for gravity estimation
static Vector2 gravity_est = {0, 0};
static int gravity_initialized = 0;

// Low-pass filtered accel (for gravity tracking)
static Vector2 lp_accel = {0, 0};

// Debug output
static float debug_ax = 0, debug_ay = 0;
static float debug_linear_ax = 0, debug_linear_ay = 0;

extern pthread_mutex_t pkt_mutex;
extern struct dp_packet right_pkt;
int events = 0;

//----------------------------------------------------------------------------------
// Gameplay Screen Functions Definition
//----------------------------------------------------------------------------------

// Gameplay Screen Initialization logic
void InitGameplayScreen(void)
{
    framesCounter = 0;
    finishScreen = 0;
    player_pos = (Vector2){(screenWidth/2.0), (screenHeight/2.0)};
    imu_vel = (Vector2){0, 0};

    /* calibration init */
    imu_bias = (Vector2){0, 0};
    imu_calib_accum = (Vector2){0, 0};
    imu_calib_count = 0;
    imu_calibrated = 0;
    
    gravity_est = (Vector2){0, 0};
    gravity_initialized = 0;
    lp_accel = (Vector2){0, 0};
    
    debug_ax = debug_ay = 0;
    debug_linear_ax = debug_linear_ay = 0;
}

// Gameplay Screen Update logic
void UpdateGameplayScreen(void)
{
    // copy shared packet under lock (avoid data races / torn reads)
        struct dp_packet pkt_local;
        pthread_mutex_lock(&pkt_mutex);
        pkt_local = right_pkt;
        events = right_button_events;
        right_button_events = 0; // clear after copying
        pthread_mutex_unlock(&pkt_mutex);
        
        float dt = GetFrameTime();
        if (dt > 0.1f) dt = 0.016f; // Clamp dt to reasonable value
        
        // ----------------- calibration -----------------
        if (!imu_calibrated) {
            imu_calib_accum.x += pkt_local.accel.x;
            imu_calib_accum.y += pkt_local.accel.y;
            imu_calib_count++;
            if (imu_calib_count >= IMU_CALIB_SAMPLES) {
                imu_bias.x = imu_calib_accum.x / (float)IMU_CALIB_SAMPLES;
                imu_bias.y = imu_calib_accum.y / (float)IMU_CALIB_SAMPLES;
                
                printf("Calibration complete: bias = (%.3f, %.3f)\n", imu_bias.x, imu_bias.y);
                
                imu_calibrated = 1;
            }
            // don't run movement until calibrated
            return;
        }
        
        // ----------------- parameters (tune these) -----------------
        const float ACCEL_SCALE         = 2700.0f; // Higher for more responsiveness
        const float VELOCITY_DAMPING    = 0.9f;   // More damping to stop faster when you stop moving
        const float VELOCITY_DEADZONE   = 8.0f;    // Stop drift
        const float ACCEL_DEADZONE      = 0.05f;   // Lower to catch more real motion
        const float MAX_VEL             = 2500.0f; // Higher max velocity
        
        // High-pass filter alpha (closer to 1.0 = more responsive, less gravity removal)
        const float HP_ALPHA            = 0.995f;    
        
        // ----------------- get acceleration and subtract bias -----------------
        float ax = pkt_local.accel.x - imu_bias.x;
        float ay = pkt_local.accel.y - imu_bias.y;
        
        // Flipping signs for orientation
        //ax = ax; 
        ay = -ay;  // Keep Y inverted
        
        // Store for debug (raw after bias removal and sign adjustment)
        debug_ax = ax;
        debug_ay = ay;
        
        // Initialize on first frame after calibration
        if (!gravity_initialized) {
            lp_accel.x = ax;
            lp_accel.y = ay;
            gravity_initialized = 1;
            return;
        }
        
        // ----------------- Simple high-pass filter for gravity removal -----------------
        // This is more responsive than the two-stage approach
        // lp_accel tracks the "DC" component (gravity + drift)
        lp_accel.x = HP_ALPHA * lp_accel.x + (1.0f - HP_ALPHA) * ax;
        lp_accel.y = HP_ALPHA * lp_accel.y + (1.0f - HP_ALPHA) * ay;
        
        // Linear acceleration = raw - low-pass (high-pass filter)
        float linear_ax = ax - lp_accel.x;
        float linear_ay = ay - lp_accel.y;
        
        // Store for debug
        debug_linear_ax = linear_ax;
        debug_linear_ay = linear_ay;
        
        // Apply deadzone to linear acceleration
        if (fabsf(linear_ax) < ACCEL_DEADZONE) linear_ax = 0.0f;
        if (fabsf(linear_ay) < ACCEL_DEADZONE) linear_ay = 0.0f;
        
        // ----------------- Integrate acceleration to velocity -----------------
        imu_vel.x += linear_ax * ACCEL_SCALE * dt;
        imu_vel.y += linear_ay * ACCEL_SCALE * dt;
        
        // Apply damping to prevent unbounded drift
        imu_vel.x *= VELOCITY_DAMPING;
        imu_vel.y *= VELOCITY_DAMPING;
        
        // Stop very small velocities
        if (fabsf(imu_vel.x) < VELOCITY_DEADZONE) imu_vel.x = 0.0f;
        if (fabsf(imu_vel.y) < VELOCITY_DEADZONE) imu_vel.y = 0.0f;
        
        // Clamp maximum velocity
        if (fabsf(imu_vel.x) > MAX_VEL) imu_vel.x = copysignf(MAX_VEL, imu_vel.x);
        if (fabsf(imu_vel.y) > MAX_VEL) imu_vel.y = copysignf(MAX_VEL, imu_vel.y);
        
        // ----------------- Integrate velocity to position -----------------
        player_pos.x += imu_vel.x * dt;
        player_pos.y += imu_vel.y * dt;
    
    // Clamp to screen bounds
    if (player_pos.x < 0) {
        player_pos.x = 0;
        imu_vel.x = 0; // stop at boundary
    }
    if (player_pos.y < 0) {
        player_pos.y = 0;
        imu_vel.y = 0;
    }
    if (player_pos.x > GetScreenWidth()) {
        player_pos.x = GetScreenWidth();
        imu_vel.x = 0;
    }
    if (player_pos.y > GetScreenHeight()) {
        player_pos.y = GetScreenHeight();
        imu_vel.y = 0;
    }
    
    // Button event: reset position and velocity
    if(events > 0){
        printf("\nResetting player pos");
        player_pos = (Vector2){(screenWidth/2.0), (screenHeight/2.0)};
        imu_vel = (Vector2){0, 0};
        events--;
    }
}

// Gameplay Screen Draw logic
void DrawGameplayScreen(void)
{
    // Draw Background
    DrawRectangle(0, 0, GetScreenWidth(), GetScreenHeight(), PURPLE);
    
    Vector2 pos = { 20, 10 };
    DrawTextEx(font, "GAMEPLAY SCREEN", pos, font.baseSize*3.0f, 4, MAROON);
    
    if(!imu_calibrated){
        DrawText("Calibrating IMU - Keep Still!", screenWidth/2 - 150, 150, 20, MAROON);
    }
    
    // FPS counter
    char buffer[64];
    sprintf(buffer, "FPS: %d", GetFPS());
    DrawText(buffer, 10, 10, 20, BLACK);
    
    // Debug info
    sprintf(buffer, "Vel: %.1f, %.1f", imu_vel.x, imu_vel.y);
    DrawText(buffer, 10, 30, 20, BLACK);
    
    sprintf(buffer, "Pos: %.0f, %.0f", player_pos.x, player_pos.y);
    DrawText(buffer, 10, 50, 20, BLACK);
    
    sprintf(buffer, "Accel: %.3f, %.3f", debug_ax, debug_ay);
    DrawText(buffer, 10, 70, 20, BLACK);
    
    sprintf(buffer, "Linear: %.3f, %.3f", debug_linear_ax, debug_linear_ay);
    DrawText(buffer, 10, 90, 20, BLACK);
    
    // Draw Player
    DrawCircleV(player_pos, 10, BLACK);
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