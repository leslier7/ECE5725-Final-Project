// Created by Robbie Leslie 2025

#ifndef FRUIT_H
#define FRUIT_H

#include "raylib.h"
#include "imu_cursor.h"

typedef enum {
    APPLE,
    WATERMELON,
    PEACH,
    FRUIT_TYPE_COUNT
} FruitType;

typedef struct {
    int radius;
    Color color;
} FruitDef;

typedef struct {
    Vector2 pos;
    Vector2 vel;
    FruitType type;
} Fruit;

extern const FruitDef FRUIT_DEFS[];

void InitFruit(Fruit *fruit);

void InitFruitType(Fruit *fruit, FruitType type);

void InitFruitDebug(Fruit *fruit, FruitType type, Vector2 pos, Vector2 vel);

void DrawFruit(Fruit *fruit);

/*
 * Returns 1 normally, but 2 if the fruit goes off screen
 */
int UpdateFruitPosition(Fruit *fruit);

bool CursorColision(IMUCursor *cursor, Fruit *fruit);

#endif