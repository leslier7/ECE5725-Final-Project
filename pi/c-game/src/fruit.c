// Created by Robbie Leslie 2025

#include "fruit.h"
#include "raylib.h"
#include "screens.h"
#include "imu_cursor.h"
#include <stdlib.h>
#include <time.h>

static const float X_SPAWN_OFFSET = 50;

static const float X_VEL_LOW = -400.0; // -400
static const float X_VEL_HIGH = 400.0; //  400
static const float Y_VEL_LOW = 500.0; // 
static const float Y_VEL_HIGH = 700.0; // 700

static const float g = 600;

const FruitDef FRUIT_DEFS[] = {
    [APPLE]      = { .radius = 15, .color = RED, .score = 3 },
    [WATERMELON] = { .radius = 35, .color = GREEN, .score = 1 },
    [PEACH]      = { .radius = 20, .color = ORANGE, .score = 2 },
    [BOMB]       = { .radius = 25, .color = BLACK, .score = -1 },
};

static float randFloatInRange(float low, float high){
    return low + ((float)rand() / (float)RAND_MAX) * (high - low);
}

void InitFruit(Fruit *fruit){
    fruit->pos = (Vector2){randFloatInRange(0 + X_SPAWN_OFFSET, screenWidth - X_SPAWN_OFFSET), screenHeight};
    fruit->vel = (Vector2){randFloatInRange(X_VEL_LOW, X_VEL_HIGH), -randFloatInRange(Y_VEL_LOW, Y_VEL_HIGH)};
    fruit->wasHit = false;
    // Generate a random fruit type
    fruit->type = rand() % FRUIT_TYPE_COUNT;
}

void InitFruitType(Fruit *fruit, FruitType type){
    fruit->pos = (Vector2){randFloatInRange(0, screenWidth), screenHeight};
    fruit->vel = (Vector2){randFloatInRange(X_VEL_LOW, X_VEL_HIGH), -randFloatInRange(Y_VEL_LOW, Y_VEL_HIGH)};
    fruit->type = type;
    fruit->wasHit = false;
}

void InitFruitDebug(Fruit *fruit, FruitType type, Vector2 pos, Vector2 vel){
    fruit->pos = pos;
    fruit->vel = vel;
    fruit->type = type;
    fruit->wasHit = false;
}

void DrawFruit(Fruit *fruit){
    DrawCircle(fruit->pos.x, fruit->pos.y, FRUIT_DEFS[fruit->type].radius, FRUIT_DEFS[fruit->type].color);
}

int UpdateFruitPosition(Fruit *fruit){
    float dt = GetFrameTime();
    
    // Update velocity
    fruit->vel.y += g * dt;
    
    // Update position
    fruit->pos.x += fruit->vel.x * dt;
    fruit->pos.y += fruit->vel.y * dt;
    
    // Fruit has gone off screen
    if(fruit->pos.x > screenWidth || fruit->pos.x < 0 || fruit->pos.y > screenHeight){
        return 2;
    }
    
    return 1;
}

bool CursorColision(IMUCursor *cursor, Fruit *fruit){
    bool isColliding = CheckCollisionCircles(cursor->pos, cursor->rad, fruit->pos, FRUIT_DEFS[fruit->type].radius);
    
    bool hit = isColliding && !fruit->wasHit;
    
    fruit->wasHit = isColliding;
    
    return hit;
}