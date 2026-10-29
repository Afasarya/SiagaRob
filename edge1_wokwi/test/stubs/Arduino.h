#pragma once
// Stub minimal untuk cek sintaks sketch di PC. BUKAN pengganti kompilasi ESP32.
#include <stdint.h>
#include <stdio.h>
#include <stdarg.h>
#define HIGH 1
#define LOW 0
#define OUTPUT 1
#define INPUT 0
unsigned long millis();
void delay(unsigned long);
void delayMicroseconds(unsigned int);
void pinMode(int, int);
void digitalWrite(int, int);
unsigned long pulseIn(int, int, unsigned long);
struct SerialStub {
  void begin(int);
  void println(const char *);
  int printf(const char *, ...);
};
extern SerialStub Serial;

