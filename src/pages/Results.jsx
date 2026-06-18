import Navbar from "../components/Navbar";
import AudioCard from "../components/AudioCard";
import Footer from "../components/Footer";

function Results() {
return (
    <div className="min-h-screen bg-gray-50">

    <Navbar />

    <div className="max-w-6xl mx-auto px-6 py-12">

        {/* Header */}
        <div className="mb-12">
        <h1 className="text-5xl font-bold mb-4">
            Your conversion is ready 
        </h1>

        <p className="text-gray-600 text-lg">
            We've enhanced your audio while preserving the natural tone
            of your voice.
        </p>
        </div>

        {/* Audio Comparison */}
        <div className="grid md:grid-cols-2 gap-8">

        <AudioCard title="Original Audio" />

        <AudioCard title="Converted Audio" />

        </div>

        {/* Transcript */}
        <div className="bg-white rounded-3xl shadow-lg p-8 mt-12">

        <h2 className="text-2xl font-bold mb-4">
            Transcription
        </h2>

        <p className="text-gray-700 leading-8">
            Hello everyone, and welcome to our weekly design sync.
            Today we're looking at the new results screen for the Lahja AI
            platform. The goal was to create a space that feels both highly
            technical and incredibly human-centric.
        </p>

        </div>

        {/* Buttons */}
        <div className="flex flex-col md:flex-row justify-center gap-4 mt-10">

        <button className="px-8 py-3 bg-purple-700 text-white rounded-full hover:bg-purple-800 transition">
            Download Audio
        </button>

        <button className="px-8 py-3 bg-gray-200 rounded-full hover:bg-gray-300 transition">
            Try Another Video
        </button>

        </div>

    </div>
    <Footer />
    </div>
);
}

export default Results;