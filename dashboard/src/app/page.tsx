"use client";

import React, { useState } from "react";
import { Sidebar, NavTab } from "@/components/Sidebar";
import { Topbar } from "@/components/Topbar";
import { OverviewView } from "@/components/views/OverviewView";
import { MapRiskView } from "@/components/views/MapRiskView";
import { TelemetryView } from "@/components/views/TelemetryView";
import { PredictionView } from "@/components/views/PredictionView";
import { ActuatorView } from "@/components/views/ActuatorView";
import { ExternalDataView } from "@/components/views/ExternalDataView";
import { TestingInfoView } from "@/components/views/TestingInfoView";
import { useMqttLive } from "@/hooks/useMqttLive";

export default function DashboardHome() {
  const [currentTab, setCurrentTab] = useState<NavTab>("overview");

  // Inisialisasi koneksi live MQTT di level dashboard
  const {
    connectionStatus,
    connectionError,
    edge1State,
    edge2State,
    aiPrediction,
    chartData,
    commandFeedback,
    sendCommand,
  } = useMqttLive();

  const renderContent = () => {
    switch (currentTab) {
      case "overview":
        return (
          <OverviewView
            edge1State={edge1State}
            edge2State={edge2State}
            aiPrediction={aiPrediction}
            chartData={chartData}
            connectionStatus={connectionStatus}
            connectionError={connectionError}
          />
        );
      case "map-risk":
        return <MapRiskView edge1State={edge1State} edge2State={edge2State} />;
      case "telemetry":
        return (
          <TelemetryView
            edge1State={edge1State}
            edge2State={edge2State}
            chartData={chartData}
          />
        );
      case "prediction":
        return <PredictionView aiPrediction={aiPrediction} />;
      case "actuator":
        return (
          <ActuatorView
            edge2State={edge2State}
            commandFeedback={commandFeedback}
            sendCommand={sendCommand}
            isConnected={connectionStatus === "connected"}
          />
        );
      case "external-data":
        return <ExternalDataView />;
      case "testing-info":
        return <TestingInfoView />;
      default:
        return (
          <OverviewView
            edge1State={edge1State}
            edge2State={edge2State}
            aiPrediction={aiPrediction}
            chartData={chartData}
            connectionStatus={connectionStatus}
            connectionError={connectionError}
          />
        );
    }
  };

  return (
    <div className="flex min-h-screen bg-neutral-100/60 font-sans text-neutral-900">
      {/* Sidebar Navigasi Kiri */}
      <Sidebar currentTab={currentTab} onSelectTab={setCurrentTab} />

      {/* Area Konten Utama */}
      <div className="flex-1 flex flex-col min-w-0">
        <Topbar
          currentTab={currentTab}
          connectionStatus={connectionStatus}
          connectionError={connectionError}
        />
        <main className="flex-1 p-8 overflow-y-auto max-w-7xl w-full mx-auto">
          {renderContent()}
        </main>
      </div>
    </div>
  );
}
