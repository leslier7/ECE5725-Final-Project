/*******************************************************************************************
*
*   raylib game template
*
*   <Game title>
*   <Game description>
*
*   This game has been created using raylib (www.raylib.com)
*   raylib is licensed under an unmodified zlib/libpng license (View raylib.h for details)
*
*   Copyright (c) 2021 Ramon Santamaria (@raysan5)
*
********************************************************************************************/

#include "raylib.h"
#include "screens.h"    // NOTE: Declares global (extern) variables and screens functions
#include "dongleparse.h"
#include <stdio.h>
#include <pthread.h>
#include <time.h>

pthread_t dongle_thread;
pthread_mutex_t pkt_mutex = PTHREAD_MUTEX_INITIALIZER;
static volatile int dongle_thread_run = 1;

#if defined(PLATFORM_WEB)
    #include <emscripten/emscripten.h>
#endif

//----------------------------------------------------------------------------------
// Shared Variables Definition (global)
// NOTE: Those variables are shared between modules through screens.h
//----------------------------------------------------------------------------------
GameScreen currentScreen = LOGO;
Font font = { 0 };
Music music = { 0 };
Sound fxCoin = { 0 };
const int screenWidth = 800;
const int screenHeight = 450;

struct dp_packet dongle_pkt;
struct dp_packet right_pkt, left_pkt;
int right_button_events = 0;
int left_button_events  = 0;

//----------------------------------------------------------------------------------
// Global Variables Definition (local to this module)
//----------------------------------------------------------------------------------

// Required variables to manage screen transitions (fade-in, fade-out)
static float transAlpha = 0.0f;
static bool onTransition = false;
static bool transFadeOut = false;
static int transFromScreen = -1;
static GameScreen transToScreen = UNKNOWN;

bool right_connected = true;
bool left_connected =true;

static time_t prev_time_r;
static time_t prev_time_l;

//----------------------------------------------------------------------------------
// Module Functions Declaration
//----------------------------------------------------------------------------------
static void ChangeToScreen(int screen);     // Change to screen, no transition effect

static void TransitionToScreen(int screen); // Request transition to next screen
static void UpdateTransition(void);         // Update transition effect
static void DrawTransition(void);           // Draw transition effect (full-screen rectangle)

static void UpdateDrawFrame(void);          // Update and draw one frame

// thread function: reads packets and updates right_pkt/left_pkt
static void *dongle_thread_fn(void *arg)
{
    int fd = *(int*)arg;
    struct dp_packet pkt;
    
    int prev_seq_r = 0;
    int prev_seq_l = 0;
    
    while (dongle_thread_run) {
        int r = dp_read_packet(fd, &pkt);
        if (r == 1) {
            //printf("\nseq=%u pipe=%u button=%u", pkt.seq, pkt.pipe, pkt.button);
            if(pkt.button){
                printf("\nButton Pressed");
            }
            pthread_mutex_lock(&pkt_mutex);
            switch (pkt.pipe) {
                case 1:
                    right_pkt = pkt;
                    prev_seq_r = pkt.seq;
                    prev_time_r = time(NULL);
                    if (pkt.button) right_button_events++;
                    break;
                case 2:
                    left_pkt = pkt;
                    prev_seq_l = pkt.seq;
                    prev_time_l = time(NULL);
                    if (pkt.button) left_button_events++;
                    break;
                default: break;
            }
            pthread_mutex_unlock(&pkt_mutex);
        } else if (r == 0) {
            // EOF -> stop
            break;
        } else {
            // error -> optionally sleep then retry
            //usleep(10000);
        }
        
        //Determine if the controllers are connected
        time_t now = time(NULL);
        if (now - prev_time_r > 3) { // Longer than 3 seconds since last right packet
            printf("Right controller not connected\n");
        }
        if (now - prev_time_l > 3) { // Longer than 3 seconds since last left packet
            printf("Left controller not connected\n");
        }
    }
    return NULL;
}

//----------------------------------------------------------------------------------
// Program main entry point
//----------------------------------------------------------------------------------
int main(void)
{
    // Initialization
    //---------------------------------------------------------
    InitWindow(screenWidth, screenHeight, "test");
    
    #ifdef _DEBUG
    printf("\nStarting game in debug mode");
    #endif

    InitAudioDevice();      // Initialize audio device

    // Load global data (assets that must be available in all screens, i.e. font)
    font = LoadFont("resources/mecha.png");
    //music = LoadMusicStream("resources/ambient.ogg"); // TODO: Load music
    //fxCoin = LoadSound("resources/coin.wav");

    //SetMusicVolume(music, 1.0f);
    //PlayMusicStream(music);

    // Setup and init first screen
    currentScreen = TITLE;
    InitTitleScreen();
    //InitGameplayScreen();
    //InitLogoScreen();


#if defined(PLATFORM_WEB)
    emscripten_set_main_loop(UpdateDrawFrame, 60, 1);
#else
    SetTargetFPS(60);       // Set our game to run at 60 frames-per-second
    //--------------------------------------------------------------------------------------
    
    
    // Set up dongle reader
    
    bool dongle_init = FileExists("/dev/ttyACM0");
    
    while(!dongle_init && !WindowShouldClose()){
        dongle_init = FileExists("/dev/ttyACM0");
        BeginDrawing();
        DrawRectangle(0, 0, GetScreenWidth(), GetScreenHeight(), WHITE);
        DrawText("Dongle not plugged in. Please plug in dongle!", 15, screenHeight/2, 35, BLACK);
        EndDrawing();
    }
    
    int dongle = dp_open("/dev/ttyACM0", 115200);
    if (dongle < 0) {
        printf("\nUnable to connect to dongle");
        return 1;
    }
    
     // start reader thread (pass fd by value)
    int dongle_fd = dongle;
    if (pthread_create(&dongle_thread, NULL, dongle_thread_fn, &dongle_fd) != 0) {
        printf("Failed to start dongle thread\n");
        dp_close(dongle);
        return 1;
    }

    // Main game loop
    while (!WindowShouldClose())    // Detect window close button or ESC key
    {

        time_t now = time(NULL);
        pthread_mutex_lock(&pkt_mutex);
        time_t last_r = prev_time_r;
        time_t last_l = prev_time_l;
        pthread_mutex_unlock(&pkt_mutex);

        if (last_r == 0 || now - last_r > 3) {
            if (right_connected) {
                printf("Right controller not connected\n");
                right_connected = false;
            }
        } else {
            if (!right_connected) {
                printf("Right controller connected\n");
                right_connected = true;
            }
        }

        if (last_l == 0 || now - last_l > 3) {
            if (left_connected) {
                printf("Left controller not connected\n");
                left_connected = false;
            }
        } else {
            if (!left_connected) {
                printf("Left controller connected\n");
                left_connected = true;
            }
        }

        UpdateDrawFrame();

    }
#endif

    // De-Initialization
    //--------------------------------------------------------------------------------------
    // Unload current screen data before closing
    switch (currentScreen)
    {
        case LOGO: UnloadLogoScreen(); break;
        case TITLE: UnloadTitleScreen(); break;
        case OPTIONS: UnloadOptionsScreen(); break;
        case GAMEPLAY: UnloadGameplayScreen(); break;
        case ENDING: UnloadEndingScreen(); break;
        default: break;
    }

    // shutdown: stop thread, close fd to unblock read, join
    dongle_thread_run = 0;
    dp_close(dongle);               // causes dp_read_packet to return / unblock
    pthread_join(dongle_thread, NULL);
    pthread_mutex_destroy(&pkt_mutex);

    // Unload global data loaded
    UnloadFont(font);
    UnloadMusicStream(music);
    UnloadSound(fxCoin);

    CloseAudioDevice();     // Close audio context

    CloseWindow();          // Close window and OpenGL context
    //--------------------------------------------------------------------------------------

    return 0;
}

//----------------------------------------------------------------------------------
// Module Functions Definition
//----------------------------------------------------------------------------------
// Change to next screen, no transition
static void ChangeToScreen(int screen)
{
    // Unload current screen
    switch (currentScreen)
    {
        case LOGO: UnloadLogoScreen(); break;
        case TITLE: UnloadTitleScreen(); break;
        case OPTIONS: UnloadOptionsScreen(); break;
        case GAMEPLAY: UnloadGameplayScreen(); break;
        case ENDING: UnloadEndingScreen(); break;
        default: break;
    }

    // Init next screen
    switch (screen)
    {
        case LOGO: InitLogoScreen(); break;
        case TITLE: InitTitleScreen(); break;
        case OPTIONS: InitOptionsScreen(); break;
        case GAMEPLAY: InitGameplayScreen(); break;
        case ENDING: InitEndingScreen(); break;
        default: break;
    }

    currentScreen = screen;
}

// Request transition to next screen
static void TransitionToScreen(int screen)
{
    onTransition = true;
    transFadeOut = false;
    transFromScreen = currentScreen;
    transToScreen = screen;
    transAlpha = 0.0f;
}

// Update transition effect (fade-in, fade-out)
static void UpdateTransition(void)
{
    if (!transFadeOut)
    {
        transAlpha += 0.05f;

        // NOTE: Due to float internal representation, condition jumps on 1.0f instead of 1.05f
        // For that reason we compare against 1.01f, to avoid last frame loading stop
        if (transAlpha > 1.01f)
        {
            transAlpha = 1.0f;

            // Unload current screen
            switch (transFromScreen)
            {
                case LOGO: UnloadLogoScreen(); break;
                case TITLE: UnloadTitleScreen(); break;
                case OPTIONS: UnloadOptionsScreen(); break;
                case GAMEPLAY: UnloadGameplayScreen(); break;
                case ENDING: UnloadEndingScreen(); break;
                default: break;
            }

            // Load next screen
            switch (transToScreen)
            {
                case LOGO: InitLogoScreen(); break;
                case TITLE: InitTitleScreen(); break;
                case OPTIONS: InitOptionsScreen(); break;
                case GAMEPLAY: InitGameplayScreen(); break;
                case ENDING: InitEndingScreen(); break;
                default: break;
            }

            currentScreen = transToScreen;

            // Activate fade out effect to next loaded screen
            transFadeOut = true;
        }
    }
    else  // Transition fade out logic
    {
        transAlpha -= 0.02f;

        if (transAlpha < -0.01f)
        {
            transAlpha = 0.0f;
            transFadeOut = false;
            onTransition = false;
            transFromScreen = -1;
            transToScreen = UNKNOWN;
        }
    }
}

// Draw transition effect (full-screen rectangle)
static void DrawTransition(void)
{
    DrawRectangle(0, 0, GetScreenWidth(), GetScreenHeight(), Fade(BLACK, transAlpha));
}

// Update and draw game frame
static void UpdateDrawFrame(void)
{
    // Update
    //----------------------------------------------------------------------------------
    //UpdateMusicStream(music);       // NOTE: Music keeps playing between screens

    if (!onTransition)
    {
        switch(currentScreen)
        {
            case LOGO:
            {
                UpdateLogoScreen();

                if (FinishLogoScreen()) TransitionToScreen(TITLE);

            } break;
            case TITLE:
            {
                UpdateTitleScreen();

                if (FinishTitleScreen() == 1) TransitionToScreen(OPTIONS);
                else if (FinishTitleScreen() == 2) TransitionToScreen(GAMEPLAY);

            } break;
            case OPTIONS:
            {
                UpdateOptionsScreen();

                if (FinishOptionsScreen()) TransitionToScreen(TITLE);

            } break;
            case GAMEPLAY:
            {
                UpdateGameplayScreen();

                if (FinishGameplayScreen() == 1) TransitionToScreen(ENDING);
                //else if (FinishGameplayScreen() == 2) TransitionToScreen(TITLE);

            } break;
            case ENDING:
            {
                UpdateEndingScreen();

                if (FinishEndingScreen() == 1) TransitionToScreen(TITLE);

            } break;
            default: break;
        }
    }
    else UpdateTransition();    // Update transition (fade-in, fade-out)
    //----------------------------------------------------------------------------------

    // Draw
    //----------------------------------------------------------------------------------
    BeginDrawing();

        ClearBackground(RAYWHITE);

        switch(currentScreen)
        {
            case LOGO: DrawLogoScreen(); break;
            case TITLE: DrawTitleScreen(); break;
            case OPTIONS: DrawOptionsScreen(); break;
            case GAMEPLAY: DrawGameplayScreen(); break;
            case ENDING: DrawEndingScreen(); break;
            default: break;
        }

        // Draw full screen rectangle in front of everything
        if (onTransition) DrawTransition();

        //DrawFPS(10, 10);

    EndDrawing();
    //----------------------------------------------------------------------------------
}
