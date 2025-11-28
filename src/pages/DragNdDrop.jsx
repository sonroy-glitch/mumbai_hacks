"use client";
import React, { useState } from "react";
import AudioDropper from "../components/DragDrop";
import RecordingOrb from "../components/VoiceAssistant";
import { Button } from "@/components/ui/stateful-button";

const Drag = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [showRecorder, setShowRecorder] = useState(false);
  const [loading, setLoading] = useState(false);
  const [responseData, setResponseData] = useState(null);
  const [error, setError] = useState("");

  // Called when user selects file OR finishes recording
  const handleFileSelect = (file) => {
    setSelectedFile(file);
    setResponseData(null);
    setError("");
  };

  const handleAnalyseClick = async () => {
    if (!selectedFile) {
      setError("Please upload or record an audio file first.");
      return;
    }

    setLoading(true);
    setError("");
    setResponseData(null);

    try {
      const formData = new FormData();

      // If selectedFile is a Blob, wrap into a File
      if (selectedFile instanceof Blob && !(selectedFile instanceof File)) {
        formData.append(
          "file",
          new File([selectedFile], "recording.webm", {
            type: selectedFile.type || "audio/webm",
          })
        );
      } else {
        formData.append("file", selectedFile);
      }

      const res = await fetch("http://localhost:5000/detect", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Server error: " + res.status);

      const data = await res.json();

      // 🔥 SHOW RESULTS IN CONSOLE
      console.log("SUMMARY:", data.summary);
      console.log("TRANSCRIPT:", data.transcript);

      setResponseData(data);
    } catch (err) {
      setError(err.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-6 font-sans">
      <div className="text-center mb-10">
        <h2 className="text-4xl font-semibold mb-3 tracking-tight">
          Audio Analysis
        </h2>
        <p className="text-zinc-400 text-lg font-light">
          Upload financial meeting recordings or record directly
        </p>
      </div>

      <div className="w-full max-w-3xl space-y-6">
        <div className="w-full bg-zinc-900/30 border border-zinc-800 rounded-lg py-4 px-6 text-zinc-400 flex items-center justify-center">
          <span className="font-light">
            Upload your meeting.mp3 or record a new message
          </span>
        </div>

        {/* Drop zone */}
        <div className="relative w-full h-64 border border-dashed border-zinc-800 bg-zinc-950/50 rounded-2xl">
          <AudioDropper onFileSelect={handleFileSelect} />
        </div>

        {/* OR */}
        <div className="flex items-center w-full">
          <div className="h-px bg-zinc-800 flex-1" />
          <span className="px-4 text-zinc-500 text-sm uppercase tracking-wider">
            OR
          </span>
          <div className="h-px bg-zinc-800 flex-1" />
        </div>

        {/* Record button */}
        <div className="flex items-center justify-center">
          <button
            className="bg-blue-600 rounded-full p-3 flex gap-3 text-md items-center"
            onClick={() => setShowRecorder(true)}
          >
            🎤 Click to Record
          </button>
        </div>

        {/* Recording UI */}
        {showRecorder && (
          <RecordingOrb
            onSave={(blob) => {
              handleFileSelect(blob);
              setShowRecorder(false);
            }}
            onClose={() => setShowRecorder(false)}
          />
        )}

        {/* Analyse button */}
        <div className="w-full flex justify-center">
          <Button
            className="w-full bg-[#2044a4] text-lg py-2"
            onClick={handleAnalyseClick}
            disabled={loading}
          >
            {loading ? "Analysing..." : "Analyse"}
          </Button>
        </div>

        {/* Selected file */}
        {selectedFile && (
          <div className="p-3 bg-zinc-900 rounded-md text-zinc-200">
            Selected: <strong>{selectedFile.name || "recording.webm"}</strong> —{" "}
            {((selectedFile.size || 0) / 1024 / 1024).toFixed(2)} MB
          </div>
        )}

        {error && <div className="text-red-400">{error}</div>}

        {/* Backend Response */}
        {responseData && (
          <div className="p-4 bg-zinc-900 rounded-lg text-zinc-200 space-y-3">
            <h3 className="text-lg font-semibold">Summary</h3>
            <p>{responseData.summary}</p>

            <h4 className="text-md font-semibold mt-2">Transcript</h4>
            <div className="text-sm text-zinc-400 max-h-48 overflow-auto">
              {responseData.transcript?.map((u, idx) => (
                <div key={idx} className="mb-2">
                  <strong>Speaker {u.speaker}</strong> [{u.start}s - {u.end}s]
                  <div>{u.text}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Drag;
