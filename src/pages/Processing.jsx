import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import api from "../services/api";
import Footer from "../components/Footer";

function Processing() {
const [progress, setProgress] = useState(0);
const navigate = useNavigate();
const location = useLocation();

const jobId = location.state?.jobId;

useEffect(() => {
    if (!jobId) {
    navigate("/");
    return;
    }

    let interval;
    let pollInterval;

    // Fake progress (UI only)
    interval = setInterval(() => {
    setProgress((prev) => {
        if (prev >= 90) return prev;
        return prev + 5;
    });
    }, 300);

    // Real backend polling
    pollInterval = setInterval(async () => {
    try {
        const res = await api.get(`/status/${jobId}`);

        if (res.data.status === "done") {
        clearInterval(interval);
        clearInterval(pollInterval);

        setProgress(100);

        setTimeout(() => {
            navigate("/results", {
            state: { result: res.data.result },
            });
        }, 500);
        }
    } catch (err) {
        console.error(err);
    }
    }, 1500);

    return () => {
    clearInterval(interval);
    clearInterval(pollInterval);
    };
}, [jobId, navigate]);

return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
    <div className="flex-grow flex items-center justify-center">
        <div className="bg-white p-10 rounded-3xl shadow-lg text-center w-[500px]">
        <div className="w-16 h-16 border-4 border-purple-700 border-t-transparent rounded-full animate-spin mx-auto mb-6"></div>

        <h1 className="text-3xl font-bold mb-4">
            Processing your video...
        </h1>

        <p className="text-gray-500 mb-8">
            Our AI is processing your request.
        </p>

        <div className="w-full bg-gray-200 rounded-full h-4">
            <div
            className="h-4 bg-purple-700 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
            ></div>
        </div>

        <p className="mt-4 text-purple-700 font-semibold">
            {progress}%
        </p>
        </div>
    </div>

    <Footer />
    </div>
);
}

export default Processing;