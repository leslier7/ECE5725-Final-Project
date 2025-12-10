// Created by Robbie Leslie 2025

#ifndef IMU_CURSOR_H
#define IMU_CURSOR_H

#include "raylib.h"

//----------------------------------------------------------------------------------
// Cursor State Structure
//----------------------------------------------------------------------------------
typedef struct {
    Vector2 pos;
    Vector2 vel;
    Vector2 bias;
    Vector2 calib_accum;
    Vector2 lp_accel;
    int calib_count;
    int calibrated;
    int gravity_initialized;
    int rad;
    Color color;
    const char *text;
    
    // Debug
    float debug_ax, debug_ay;
    float debug_linear_ax, debug_linear_ay;
} IMUCursor;

void InitCursor(IMUCursor *cursor, Vector2 pos, Color color, const char *text);

void InitCursors(IMUCursor *right_cursor, IMUCursor *left_cursor);

int UpdateCursorCalibration(IMUCursor *cursor, Vector2 accel);

void UpdateCursorMovement(IMUCursor *cursor, Vector2 accel, float dt);

void ResetCursor(IMUCursor *cursor, Vector2 pos);

void DrawCursor(IMUCursor *cursor);

#endif