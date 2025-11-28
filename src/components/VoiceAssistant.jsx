"use client";

import { motion } from "framer-motion";
import { Mic, MicOff, X } from "lucide-react";
import { useState, useRef, useEffect } from "react";

export default function RecordingOrb({ onSave, onClose }) {
  const [isListening, setIsListening] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState(null);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // 🔥 Disable scrolling behind modal
  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "auto";
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: "audio/webm",
      });

      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        setRecordedBlob(blob);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorderRef.current = mediaRecorder;

      setTimeout(() => mediaRecorder.start(), 200);

      setRecordedBlob(null);
      setIsListening(true);
    } catch (err) {
      console.error(err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
    }
    setIsListening(false);
  };

  const handleClose = () => {
    let blob = recordedBlob;

    if (isListening) stopRecording();

    if (blob && onSave) onSave(blob);
    if (onClose) onClose();
  };

  const toggleMic = () => {
    if (isListening) stopRecording();
    else startRecording();
  };

  return (
    <div
      className="
        fixed inset-0 w-screen h-screen 
        z-[99999]
        flex flex-col items-center justify-center 
        bg-black/95 backdrop-blur-md
      "
    >
      <div className="relative h-80 w-80 flex items-center justify-center">
        {isListening && (
          <motion.div
            animate={{ scale: [1, 1.3], opacity: [0.8, 0] }}
            transition={{ repeat: Infinity, duration: 2 }}
            className="absolute inset-0 rounded-full border-2 border-teal-400/40"
          />
        )}

        {/* Beautiful gradient orb */}
        <div
          className="
            h-48 w-48 rounded-full shadow-2xl 
            bg-gradient-to-r from-[#2dd4bf] to-[#1f2937]
          "
        />
      </div>

      <div className="flex gap-6 mt-6">
        <button
          onClick={toggleMic}
          className="h-16 w-16 rounded-full bg-white/10 text-white border border-white/30 flex items-center justify-center"
        >
          {isListening ? <MicOff /> : <Mic />}
        </button>

        <button
          onClick={handleClose}
          className="h-16 w-16 rounded-full bg-white/10 text-white border border-white/30 flex items-center justify-center"
        >
          <X />
        </button>
      </div>

      <p className="text-teal-400 text-sm mt-4">
        {isListening ? "Recording..." : recordedBlob ? "Saved!" : "Click mic"}
      </p>

      {recordedBlob && (
        <audio
          controls
          src={URL.createObjectURL(recordedBlob)}
          className="mt-4"
        />
      )}
    </div>
  );
}
