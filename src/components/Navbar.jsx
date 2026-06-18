function Navbar() {
    return (
    <nav className="flex justify-between items-center p-6 shadow-sm">
        <h1 className="text-2xl font-bold text-purple-700">
        Lahja
        </h1>

        <div className="flex gap-6">
        <button>How it Works</button>
        <button>Pricing</button>
        </div>
    </nav>
    );
}

export default Navbar;