import UploadBox from "../components/UploadBox";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

function Home() {
const navigate = useNavigate();

return (
    <div>
    <Navbar />

    <section className="min-h-[80vh] flex flex-col items-center justify-center text-center px-6">
        <h1 className="text-6xl font-bold mb-4">
        Lahja – AI Accent Converter
        </h1>

        <p className="text-gray-600 max-w-2xl">
        Upload your video to convert speech accents into a clear,
        neutral English accent while preserving the original voice.
        </p>

        <div className="mt-10">
        <UploadBox />
        </div>

        <button
        onClick={() => navigate("/processing")}
        className="mt-8 px-8 py-3 bg-purple-700 text-white rounded-full"
        >
        Upload Video
        </button>

        <div className="grid md:grid-cols-3 gap-6 mt-16">
        <div className="bg-white p-6 rounded-2xl shadow">
            <h3 className="font-bold">AI Conversion</h3>
            <p>Preserves speaker identity.</p>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow">
            <h3 className="font-bold">Fast Processing</h3>
            <p>Results in under a minute.</p>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow">
            <h3 className="font-bold">Clear English</h3>
            <p>Neutral professional accent.</p>
        </div>
        
        </div>
    </section>
    <Footer />
    </div>
);
}

export default Home;