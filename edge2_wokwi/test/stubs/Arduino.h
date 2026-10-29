#pragma once
// Stub minimal untuk cek sintaks sketch di PC. BUKAN pengganti kompilasi ESP32.
#include <stdint.h>
#include <stdio.h>
#include <math.h>
#include <stdarg.h>
#define HIGH 1
#define LOW 0
#define OUTPUT 1
#define INPUT 0
unsigned long millis();
void delay(unsigned long);
void pinMode(int, int);
void digitalWrite(int, int);
int analogRead(int);
void tone(uint8_t, unsigned int);
void noTone(uint8_t);
struct SerialStub {
  void begin(int);
  void println(const char *);
  int printf(const char *, ...);
};
extern SerialStub Serial;

