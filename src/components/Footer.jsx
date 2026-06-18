function Footer() {
    return (
    <footer className="bg-white border-t mt-16">
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col md:flex-row justify-between items-center">

        <div>
            <h3 className="font-bold text-lg text-purple-700">
            Lahja AI
            </h3>

            <p className="text-gray-500 text-sm">
            © 2026 Lahja AI. Elevating voices everywhere.
            </p>
        </div>

        <div className="flex gap-6 mt-4 md:mt-0 text-gray-600">
            <a href="#">Privacy Policy</a>
            <a href="#">Terms of Service</a>
            <a href="#">Contact</a>
        </div>

        </div>
    </footer>
    );
}

export default Footer;