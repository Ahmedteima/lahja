import { useState } from "react";
import api from "../services/api";
import { useNavigate } from "react-router-dom";

function UploadBox() {
const [fileName, setFileName] = useState("");
const [loading, setLoading] = useState(false);

const navigate = useNavigate();

const handleFileChange = async (e) => {
    const file = e.target.files[0];

    if (!file) return;

    setFileName(file.name);

    const formData = new FormData();
    formData.append("file", file);

    try {
    setLoading(true);

    const res = await api.post("/upload", formData, {
        headers: {
        "Content-Type": "multipart/form-data",
        },
    });

    navigate("/processing", {
        state: { jobId: res.data.jobId },
    });

    } catch (error) {
        console.error(error);
    
        alert(
        error?.response?.data?.detail ||
        error?.message ||
        "Upload Failed"
        );
    }
};

return (
    <div className="w-full max-w-2xl">
    <label
        className="
        border-2 border-dashed border-purple-300
        rounded-3xl
        p-16
        flex flex-col
        items-center
        justify-center
        cursor-pointer
        hover:border-purple-600
        hover:bg-purple-50
        transition
        "
    >
        <input
        type="file"
        accept="video/*"
        className="hidden"
        onChange={handleFileChange}
        />

        <div className="text-6xl mb-4">🎥</div>

        <h2 className="text-2xl font-semibold">
        {loading ? "Uploading..." : "Drop your video here"}
        </h2>

        <p className="text-gray-500 mt-2">
        MP4, MOV or AVI
        </p>

        {fileName && (
        <p className="mt-4 text-purple-700 font-semibold">
            {fileName}
        </p>
        )}
    </label>
    </div>
);
}

export default UploadBox;