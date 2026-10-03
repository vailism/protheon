#ifndef SERVOS_H
#define SERVOS_H

#include <Arduino.h>
#include <Servo.h>

void servos_init();
void servos_set(int finger_idx, int angle);
int  servos_get_angle(int finger_idx);
void servos_stop();
void servos_detach_all();

#endif // SERVOS_H
