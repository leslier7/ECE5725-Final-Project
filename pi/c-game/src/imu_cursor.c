// Created by Robbie Leslie 2025

#include "imu_cursor.h"
#include "raylib.h"
#include "screens.h"
#include <stdio.h>
#include <math.h>
#include <pthread.h>

// Shared tuning parameters
static const int IMU_CALIB_SAMPLES   = 120;
static const float ACCEL_SCALE       = 2700.0f;
static const float VELOCITY_DAMPING  = 0.9f;
static const float VELOCITY_DEADZONE = 8.0f;
static const float ACCEL_DEADZONE    = 0.05f;
static const float MAX_VEL           = 2500.0f;
static const float HP_ALPHA          = 0.995f;

void InitCursor(IMUCursor *cursor, Color color, const char *text)
{
    cursor->pos = (Vector2){screenWidth / 2.0f, screenHeight / 2.0f};
    cursor->vel = (Vector2){0, 0};
    cursor->bias = (Vector2){0, 0};
    cursor->calib_accum = (Vector2){0, 0};
    cursor->lp_accel = (Vector2){0, 0};
    cursor->calib_count = 0;
    cursor->calibrated = 0;
    cursor->gravity_initialized = 0;
    cursor->debug_ax = cursor->debug_ay = 0;
    cursor->debug_linear_ax = cursor->debug_linear_ay = 0;
    cursor->rad = 10;
    cursor->color = color;
    cursor->text = text; // Single char to tell which cursor this is
}

// Returns 1 if still calibrating, 0 if ready to process
int UpdateCursorCalibration(IMUCursor *cursor, Vector2 accel)
{
    if (cursor->calibrated) return 0;
    
    cursor->calib_accum.x += accel.x;
    cursor->calib_accum.y += accel.y;
    cursor->calib_count++;
    
    if (cursor->calib_count >= IMU_CALIB_SAMPLES) {
        cursor->bias.x = cursor->calib_accum.x / (float)IMU_CALIB_SAMPLES;
        cursor->bias.y = cursor->calib_accum.y / (float)IMU_CALIB_SAMPLES;
        cursor->calibrated = 1;
    }
    return 1; // Still calibrating
}

void UpdateCursorMovement(IMUCursor *cursor, Vector2 accel, float dt)
{
    // Subtract bias and apply orientation correction
    float ax = accel.x - cursor->bias.x;
    float ay = -(accel.y - cursor->bias.y);  // Invert Y
    
    cursor->debug_ax = ax;
    cursor->debug_ay = ay;
    
    // Initialize gravity filter
    if (!cursor->gravity_initialized) {
        cursor->lp_accel.x = ax;
        cursor->lp_accel.y = ay;
        cursor->gravity_initialized = 1;
        return;
    }
    
    // High-pass filter for gravity removal
    cursor->lp_accel.x = HP_ALPHA * cursor->lp_accel.x + (1.0f - HP_ALPHA) * ax;
    cursor->lp_accel.y = HP_ALPHA * cursor->lp_accel.y + (1.0f - HP_ALPHA) * ay;
    
    float linear_ax = ax - cursor->lp_accel.x;
    float linear_ay = ay - cursor->lp_accel.y;
    
    cursor->debug_linear_ax = linear_ax;
    cursor->debug_linear_ay = linear_ay;
    
    // Apply deadzone
    if (fabsf(linear_ax) < ACCEL_DEADZONE) linear_ax = 0.0f;
    if (fabsf(linear_ay) < ACCEL_DEADZONE) linear_ay = 0.0f;
    
    // Integrate to velocity
    cursor->vel.x += linear_ax * ACCEL_SCALE * dt;
    cursor->vel.y += linear_ay * ACCEL_SCALE * dt;
    
    // Damping
    cursor->vel.x *= VELOCITY_DAMPING;
    cursor->vel.y *= VELOCITY_DAMPING;
    
    // Velocity deadzone
    if (fabsf(cursor->vel.x) < VELOCITY_DEADZONE) cursor->vel.x = 0.0f;
    if (fabsf(cursor->vel.y) < VELOCITY_DEADZONE) cursor->vel.y = 0.0f;
    
    // Clamp velocity
    if (fabsf(cursor->vel.x) > MAX_VEL) cursor->vel.x = copysignf(MAX_VEL, cursor->vel.x);
    if (fabsf(cursor->vel.y) > MAX_VEL) cursor->vel.y = copysignf(MAX_VEL, cursor->vel.y);
    
    // Integrate to position
    cursor->pos.x += cursor->vel.x * dt;
    cursor->pos.y += cursor->vel.y * dt;
    
    // Clamp to screen
    if (cursor->pos.x < 0) { cursor->pos.x = 0; cursor->vel.x = 0; }
    if (cursor->pos.y < 0) { cursor->pos.y = 0; cursor->vel.y = 0; }
    if (cursor->pos.x > GetScreenWidth()) { cursor->pos.x = GetScreenWidth(); cursor->vel.x = 0; }
    if (cursor->pos.y > GetScreenHeight()) { cursor->pos.y = GetScreenHeight(); cursor->vel.y = 0; }
}

void ResetCursor(IMUCursor *cursor)
{
    cursor->pos = (Vector2){screenWidth / 2.0f, screenHeight / 2.0f};
    cursor->vel = (Vector2){0, 0};
}

void DrawCursor(IMUCursor *cursor){
    DrawCircleV(cursor->pos, cursor->rad, cursor->color);
    DrawText(cursor->text, cursor->pos.x-5, cursor->pos.y-5, 15, BLACK);
}