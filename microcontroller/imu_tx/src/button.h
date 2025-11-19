#ifndef _BUTTON_H_
#define _BUTTON_H_

#include <zephyr/kernel.h>

#include <stdbool.h>

extern volatile bool button_pressed_flag;

int button_init(void);

bool button_is_pressed(void);

#endif