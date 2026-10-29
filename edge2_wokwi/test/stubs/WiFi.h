#pragma once
#include "Arduino.h"
#define WL_CONNECTED 3
class WiFiClient {};
struct WiFiStub {
  int status();
  void begin(const char *, const char *, int);
};
extern WiFiStub WiFi;

