function AudioCard({ title }) {
    return (
    <div className="bg-white p-6 rounded-2xl shadow">
        <h2 className="font-bold text-xl mb-4">
        {title}
        </h2>

        <audio controls className="w-full">
        <source src="" type="audio/mpeg" />
        </audio>
    </div>
    );
}

export default AudioCard;