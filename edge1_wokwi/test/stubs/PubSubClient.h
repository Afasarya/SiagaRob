#pragma once
#include "WiFi.h"
// Tanda tangan mengikuti PubSubClient 2.8
class PubSubClient {
 public:
  PubSubClient(WiFiClient &);
  PubSubClient &setServer(const char *, uint16_t);
  bool setBufferSize(uint16_t);
  PubSubClient &setKeepAlive(uint16_t);
  bool connect(const char *id, const char *user, const char *pass, const char *willTopic,
               uint8_t willQos, bool willRetain, const char *willMessage);
  bool connected();
  bool publish(const char *topic, const char *payload, bool retained = false);
  bool loop();
};

