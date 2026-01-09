import React from 'react';
import Navbar from './Navbar';

const Layout = ({ children }) => {
    return (
        <div className="flex flex-col min-h-screen bg-primary-bg font-sans text-text-main">
            <Navbar />

            {/* Added pt-20 to account for fixed navbar */}
            <main className="flex-grow w-full pt-20">
                {children}
            </main>

            <footer className="py-12 bg-white border-t border-gray-100 mt-auto">
                <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
                    <div className="text-center md:text-left">
                        <img src="/logo.png" alt="HRC Music4D Logo" className="h-8 w-auto mb-2 mx-auto md:mx-0" />
                        <p className="text-text-secondary text-sm">Empowering emotion through AI and sound.</p>
                    </div>

                    <div className="text-sm text-text-secondary">
                        &copy; {new Date().getFullYear()} HRC Music4D Project. All rights reserved.
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default Layout;
