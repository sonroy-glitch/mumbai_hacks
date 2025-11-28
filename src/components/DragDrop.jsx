import React, { useState, useRef, useEffect } from "react";

const AudioDropper = ({ onFileSelect }) => {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [error, setError] = useState("");
  const inputRef = useRef(null);

  const cleanupPreview = () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
  };

  const handleFiles = (files) => {
    const selected = files[0];
    if (!selected) return;

    if (!selected.type.startsWith("audio/")) {
      setError("Please upload an audio file");
      return;
    }

    setError("");
    cleanupPreview();

    const url = URL.createObjectURL(selected);
    setFile(selected);
    setPreviewUrl(url);

    // <-- IMPORTANT: send file to parent for ANALYSE BUTTON
    onFileSelect(selected);
  };

  return (
    <div
      className="w-full h-full flex flex-col justify-center items-center cursor-pointer"
      onClick={() => inputRef.current?.click()}
      onDrop={(e) => {
        e.preventDefault();
        handleFiles(e.dataTransfer.files);
      }}
      onDragOver={(e) => e.preventDefault()}
    >
      {!file ? (
        <>
          <p className="text-zinc-500">Drop your file here</p>
          <input
            ref={inputRef}
            type="file"
            accept="audio/*"
            onChange={(e) => handleFiles(e.target.files)}
            style={{ display: "none" }}
          />
        </>
      ) : (
        <div className="text-white text-center">
          <p>{file.name}</p>
          <audio controls src={previewUrl} className="mt-2" />
        </div>
      )}

      {error && <p className="text-red-500 mt-2">{error}</p>}
    </div>
  );
};

export default AudioDropper;
