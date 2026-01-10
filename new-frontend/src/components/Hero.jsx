import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// Import carousel images
import heroBg1 from '../assets/UNICAL.jpg';
import heroBg2 from '../assets/UNICAL_flags-1280x853.jpg';
import heroBg3 from '../assets/images-2.jpeg';
import heroBg4 from '../assets/images.jpeg';

const backgrounds = [heroBg1, heroBg2, heroBg3, heroBg4];



const Hero = () => {
    const [currentIndex, setCurrentIndex] = useState(0);

    useEffect(() => {
        const timer = setInterval(() => {
            setCurrentIndex((prevIndex) => (prevIndex + 1) % backgrounds.length);
        }, 5000);

        return () => clearInterval(timer);
    }, []);

    return (
        <section className="relative h-screen min-h-[600px] w-full overflow-hidden bg-gray-900">
            {/* Background Image Carousel */}
            <AnimatePresence mode="wait">
                <motion.div
                    key={currentIndex}
                    initial={{ opacity: 0, scale: 1.1 }}
                    animate={{ opacity: 0.5, scale: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 1.5, ease: "easeOut" }}
                    className="absolute inset-0 bg-cover bg-center"
                    style={{
                        backgroundImage: `url(${backgrounds[currentIndex]})`,
                    }}
                />
            </AnimatePresence>

            {/* Gradient Overlay */}
            <div className="absolute inset-0 bg-gradient-to-b from-black/80 via-black/40 to-black/80" />

            {/* Content */}
            <div className="relative z-10 h-full flex flex-col items-center justify-center text-center px-4">
                <div className="max-w-5xl">
                    <motion.div
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 1, ease: "easeOut" }}
                    >
                        <h1 className="text-6xl md:text-8xl font-bold font-heading text-white mb-6 tracking-tight leading-tight">
                            HRC MUSIC<span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-600">4D</span>
                        </h1>
                    </motion.div>

                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, delay: 0.3, ease: "easeOut" }}
                        className="text-xl md:text-3xl text-gray-200 font-light max-w-3xl mx-auto leading-relaxed"
                    >
                        Artificial Intelligence that <span className="italic text-blue-200">hears</span> your emotions.
                    </motion.p>

                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.5, delay: 0.6 }}
                        className="mt-12"
                    >
                        <a
                            href="#project-overview"
                            className="group relative inline-flex items-center justify-center px-8 py-4 text-white font-medium transition-all duration-200 focus:outline-none"
                        >
                            <span className="absolute inset-0 w-full h-full rounded-full bg-accent-blue/80 backdrop-blur-sm group-hover:bg-accent-blue transition-colors duration-300 shadow-[0_0_20px_rgba(37,99,235,0.5)]"></span>
                            <span className="relative z-10 text-lg tracking-wide">Explore Project</span>
                        </a>
                    </motion.div>
                </div>
            </div>

            {/* Scroll Indicator */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1, y: [0, 10, 0] }}
                transition={{ delay: 1, duration: 2, repeat: Infinity }}
                className="absolute bottom-10 left-1/2 transform -translate-x-1/2 text-white/50"
            >
                <div className="w-[1px] h-16 bg-gradient-to-b from-transparent via-white/50 to-transparent mx-auto"></div>
                <span className="text-xs uppercase tracking-[0.2em] mt-2 block">Scroll</span>
            </motion.div>
        </section>
    );
};

export default Hero;
