#pragma once
#include "WiFi.h"
// Tanda tangan mengikuti PubSubClient 2.8
#include <functional>
class PubSubClient {
 public:
  PubSubClient(WiFiClient &);
  PubSubClient &setServer(const char *, uint16_t);
  PubSubClient &setCallback(void (*)(char *, uint8_t *, unsigned int));
  bool setBufferSize(uint16_t);
  PubSubClient &setKeepAlive(uint16_t);
  bool connect(const char *id, const char *user, const char *pass, const char *willTopic,
               uint8_t willQos, bool willRetain, const char *willMessage);
  bool connected();
  bool publish(const char *topic, const char *payload, bool retained = false);
  bool subscribe(const char *topic, uint8_t qos = 0);
  bool loop();
};

