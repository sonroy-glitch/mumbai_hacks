import os
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
import assemblyai as aai

# BASIC SETUP

flask_app = Flask(__name__)
CORS(flask_app)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# AssemblyAI setup
aai.settings.api_key = "ee7668fc7e9c49139de60eeba6e14bbc"

# Gemini setup
client = genai.Client(api_key="AIzaSyAUdpxFY9iGHEDxJswq6CMLMW0EwB3SyDE")

# FRAUD DETECTION ENDPOINT

@flask_app.route("/detect", methods=["POST"])
def detect_fraud():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        audio_file = request.files["file"]

        # Save uploaded file temporarily
        _, ext = os.path.splitext(audio_file.filename)
        if ext == "":
            ext = ".wav"

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext, dir=UPLOAD_DIR) as tmp:
            tmp_path = tmp.name
            audio_file.save(tmp_path)

        # Transcription config
        config = aai.TranscriptionConfig(
            speaker_labels=True,
            speech_model=aai.SpeechModel.best
        )

        # Transcribe audio
        transcript = aai.Transcriber().transcribe(tmp_path, config)

        if transcript.status == "error":
            return jsonify({"error": transcript.error}), 500

        # Extract utterances
        utterance_list = []
        text_for_llm = []

        for u in transcript.utterances:
            item = {
                "start": u.start / 1000,
                "end": u.end / 1000,
                "speaker": u.speaker,
                "text": u.text
            }
            utterance_list.append(item)
            text_for_llm.append(
                f"TIME:{item['start']}-{item['end']} Speaker {item['speaker']}: {item['text']}"
            )

        # Gemini summary
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
Summarize the following timestamped two-person conversation.
Return ONLY a clean, natural language paragraph.
Keep a financial view of the summary . Also point our several financial problems and steps to fix them.

DATA:
{text_for_llm}
"""
        )

        summary = response.text if hasattr(response, "text") else "No summary generated."

        # Return JSON response
        return jsonify({
            "summary": summary,
            "transcript": utterance_list,
            "filename": os.path.basename(tmp_path)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        try:
            if 'tmp_path' in locals():
                os.remove(tmp_path)
        except:
            pass

# START FLASK SERVER

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=5000, debug=True)