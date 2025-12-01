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

const static float pos_2_pix = 3;

static Vector2 imu_vel;
static Vector2 imu_pos;

const float g = 9.81;

// calibration state
static Vector2 imu_bias;
static Vector2 imu_calib_accum;
static int imu_calib_count;
static const int IMU_CALIB_SAMPLES = 120; /* ~2s @60Hz */
static int imu_calibrated;

extern pthread_mutex_t pkt_mutex;
extern struct dp_packet right_pkt;

//----------------------------------------------------------------------------------
// Gameplay Screen Functions Definition
//----------------------------------------------------------------------------------

// Gameplay Screen Initialization logic
void InitGameplayScreen(void)
{
    // TODO: Initialize GAMEPLAY screen variables here!
    framesCounter = 0;
    finishScreen = 0;
    player_pos = (Vector2){(screenWidth/2.0), (screenHeight/2.0)};
    imu_vel = (Vector2){0, 0};
    imu_pos = (Vector2){0, 0};

    /* calibration init */
    imu_bias = (Vector2){0, 0};
    imu_calib_accum = (Vector2){0, 0};
    imu_calib_count = 0;
    imu_calibrated = 0;
}

// Gameplay Screen Update logic
void UpdateGameplayScreen(void)
{
    float dt = GetFrameTime();

    // copy shared packet under lock (avoid data races / torn reads)
    struct dp_packet pkt_local;
    pthread_mutex_lock(&pkt_mutex);
    pkt_local = right_pkt;
    pthread_mutex_unlock(&pkt_mutex);

    // raw accel from local copy
    float arx = pkt_local.accel.x;
    float ary = pkt_local.accel.y;

    // persistent state for filters / units
    static int gravity_init = 0;
    static Vector2 gravity_est = {0,0};
    static float imu_acc_scale = 1.0f;   // set to 9.81 if device reports in g
    static int unit_checked = 0;

    // high-pass state (to react to quick movements only)
    static float prev_ax = 0.0f;
    static float prev_ay = 0.0f;
    static float hp_ax = 0.0f;
    static float hp_ay = 0.0f;
    // Tunables: higher HP_ALPHA -> less low freq (less tilt), lower -> more tilt leaked through
    const float GRAV_ALPHA = 0.98f;      // low-pass for gravity estimate
    const float HP_ALPHA   = 0.90f;      // high-pass coefficient (0..1)
    const float ACCEL_DEADZONE = 0.15f;  // ignore tiny noise after filtering
    const float IMPULSE_GAIN = 20.0f;    // scale HP accel -> velocity impulse (tune)
    const float PIXELS_PER_VEL = 40.0f; // map velocity to pixels (tune)
    const float VELOCITY_DAMP = 0.90f;   // stronger damping so motion stops quickly

    // seed gravity estimate and prev samples
    if (!gravity_init) {
        gravity_est.x = arx;
        gravity_est.y = ary;
        prev_ax = arx;
        prev_ay = ary;
        gravity_init = 1;
        return; // skip movement first frame
    }

    // detect units once from gravity_est magnitude (approx 1.0 if in g)
    if (!unit_checked) {
        float mag = sqrtf(gravity_est.x*gravity_est.x + gravity_est.y*gravity_est.y);
        if (mag > 0.5f && mag < 1.5f) imu_acc_scale = g;
        else imu_acc_scale = 1.0f;
        unit_checked = 1;
    }

    // update gravity estimate (low-pass) - used only for unit detection here
    gravity_est.x = GRAV_ALPHA * gravity_est.x + (1.0f - GRAV_ALPHA) * arx;
    gravity_est.y = GRAV_ALPHA * gravity_est.y + (1.0f - GRAV_ALPHA) * ary;

    // convert units if necessary
    float a_x = arx * imu_acc_scale;
    float a_y = ary * imu_acc_scale;

    // high-pass filter (one-step form): hp = alpha*(hp_prev + (x - x_prev))
    hp_ax = HP_ALPHA * (hp_ax + (a_x - prev_ax));
    hp_ay = HP_ALPHA * (hp_ay + (a_y - prev_ay));

    // store sample for next iteration
    prev_ax = a_x;
    prev_ay = a_y;

    // deadzone on hp output
    if (fabsf(hp_ax) < ACCEL_DEADZONE) hp_ax = 0.0f;
    if (fabsf(hp_ay) < ACCEL_DEADZONE) hp_ay = 0.0f;

    // treat high-passed accel as an impulse -> add to velocity (mouse-like)
    imu_vel.x += hp_ax * IMPULSE_GAIN;
    imu_vel.y += hp_ay * IMPULSE_GAIN;

    // apply strong damping so velocity decays quickly when no impulses
    imu_vel.x *= VELOCITY_DAMP;
    imu_vel.y *= VELOCITY_DAMP;

    // convert velocity -> pixel displacement
    Vector2 delta_pos = { imu_vel.x * dt * PIXELS_PER_VEL, imu_vel.y * dt * PIXELS_PER_VEL };

    // small clamp to avoid sub-pixel jitter
    if (fabsf(delta_pos.x) < 1e-4f) delta_pos.x = 0.0f;
    if (fabsf(delta_pos.y) < 1e-4f) delta_pos.y = 0.0f;

    // update positions (apply directly per-frame delta)
    imu_pos.x += delta_pos.x;
    imu_pos.y += delta_pos.y;

    player_pos.x += delta_pos.x;
    player_pos.y += delta_pos.y;

    // clamp inside screen
    if (player_pos.x < 0) player_pos.x = 0;
    if (player_pos.y < 0) player_pos.y = 0;
    if (player_pos.x > GetScreenWidth()) player_pos.x = GetScreenWidth();
    if (player_pos.y > GetScreenHeight()) player_pos.y = GetScreenHeight();
    
    //printf("\n\nDelta x: %f | Delta y: %f", delta_pos.x, delta_pos.y);
    
    // Press enter or tap to change to ENDING screen
    // if (IsKeyPressed(KEY_ENTER) || IsGestureDetected(GESTURE_TAP))
    // {
    //     finishScreen = 1;
    //     PlaySound(fxCoin);
    // }
}

// Gameplay Screen Draw logic
void DrawGameplayScreen(void)
{
    // TODO: Draw GAMEPLAY screen here!
     
    // Draw Background
    DrawRectangle(0, 0, GetScreenWidth(), GetScreenHeight(), PURPLE);
    
    Vector2 pos = { 20, 10 };
    DrawTextEx(font, "GAMEPLAY SCREEN", pos, font.baseSize*3.0f, 4, MAROON);
    
    // if(!imu_calibrated){
    //     DrawText("Calibrating IMU", screenWidth/2 - 50, 150, 20, MAROON);
    // }
    char buffer[5];
    sprintf(buffer, "%d", GetFPS());
    DrawText(buffer, 10, 10, 20, BLACK);
    
    //DrawText("PRESS ENTER or TAP to JUMP to ENDING SCREEN", 130, 220, 20, MAROON);
    
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