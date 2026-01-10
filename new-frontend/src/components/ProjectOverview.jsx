import React from "react";
import { motion } from "framer-motion";
import frameworkImg from '../assets/framework1.png';

const ProjectOverview = () => {
    return (
        <section id="project-overview" className="py-24 relative overflow-hidden bg-primary-bg">
            {/* Background Decor */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-100/30 rounded-full blur-3xl" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-100/30 rounded-full blur-3xl" />
            </div>

            <div className="max-w-7xl mx-auto px-6 relative z-10">

                {/* Header Section */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                    className="text-center mb-20"
                >
                    <h2 className="text-5xl md:text-6xl font-bold font-heading text-text-heading mb-6 tracking-tight">
                        Project <span className="text-accent-blue">Overview</span>
                    </h2>
                    <p className="text-xl md:text-2xl text-text-secondary font-light max-w-4xl mx-auto leading-relaxed">
                        Investigating <strong className="text-text-main font-semibold">Multi-Agent Human–Robot Teaming (MA-HRT)</strong> in a musical orchestral environment—a paradigm shift towards robots as equal creative partners.
                    </p>
                </motion.div>

                {/* Main Content & Figure */}
                <div className="grid lg:grid-cols-2 gap-16 items-center mb-24">

                    {/* Text Content */}
                    <motion.div
                        initial={{ opacity: 0, x: -30 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.8 }}
                    >
                        <p className="text-lg text-text-secondary leading-relaxed mb-6 text-justify">
                            The orchestral domain serves as a rich, unstructured, and expressive setting to study coordination, communication, control, and collective creativity.
                        </p>
                        <p className="text-lg text-text-secondary leading-relaxed mb-6 text-justify">
                            Aligned with the vision of <strong className="text-text-heading">Industry 5.0</strong>, our framework promotes human-centric, intelligent, and collaborative systems where human ingenuity and machine intelligence coexist and co-evolve.
                        </p>
                        <div className="flex gap-4 mt-8">
                            <div className="px-6 py-3 rounded-full bg-white/50 border border-white shadow-sm text-accent-blue font-semibold text-sm uppercase tracking-wider backdrop-blur-sm">
                                Human-Centric
                            </div>
                            <div className="px-6 py-3 rounded-full bg-white/50 border border-white shadow-sm text-accent-blue font-semibold text-sm uppercase tracking-wider backdrop-blur-sm">
                                Intelligent
                            </div>
                        </div>
                    </motion.div>

                    {/* Figure with Glass Frame */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, rotate: 1 }}
                        whileInView={{ opacity: 1, scale: 1, rotate: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.8 }}
                        className="relative"
                    >
                        {/* Glow effect */}
                        <div className="absolute inset-0 bg-gradient-to-tr from-blue-500/10 to-indigo-500/10 rounded-2xl blur-2xl transform scale-110" />

                        <div className="glass-card p-4 md:p-6 rounded-2xl relative bg-white/60 backdrop-blur-xl border border-white/40 shadow-2xl">
                            <img
                                src={frameworkImg}
                                alt="MA-HRT Orchestra Framework"
                                className="w-full h-auto rounded-lg shadow-inner border border-gray-100"
                            />
                            <div className="mt-4 pt-4 border-t border-gray-100 text-center">
                                <p className="text-xs font-bold tracking-widest text-text-secondary uppercase">Proposed MA-HRT Orchestra Framework</p>
                            </div>
                        </div>
                    </motion.div>
                </div>

                {/* The 4C's Grid */}
                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="mb-16"
                >
                    <h3 className="text-3xl font-bold font-heading text-center mb-12 text-text-heading">The 4 Foundation Dimensions</h3>

                    <div className="grid md:grid-cols-2 gap-8">
                        {/* Card 1: Coexistence */}
                        <div className="glass-card p-8 hover:-translate-y-2 hover:shadow-2xl transition-all duration-300 border-t-4 border-t-emerald-500 group">
                            <h4 className="flex items-center gap-3 text-xl font-bold font-heading text-emerald-600 mb-4">
                                <span className="text-2xl opacity-80 group-hover:scale-110 transition-transform"></span>
                                Coexistence
                            </h4>
                            <p className="text-text-secondary leading-relaxed">
                                Defines the composition and structure of the team. Supports heterogeneous teams where humans and robots <strong>co-presence</strong> in the same workspace, influencing perception, roles, and emotional responses.
                            </p>
                        </div>

                        {/* Card 2: Collaboration */}
                        <div className="glass-card p-8 hover:-translate-y-2 hover:shadow-2xl transition-all duration-300 border-t-4 border-t-blue-500 group">
                            <h4 className="flex items-center gap-3 text-xl font-bold font-heading text-blue-600 mb-4">
                                <span className="text-2xl opacity-80 group-hover:scale-110 transition-transform"></span>
                                Collaboration
                            </h4>
                            <p className="text-text-secondary leading-relaxed">
                                Focuses on communication and synchronization. Utilizes <strong>multimodal interaction</strong> (visual, auditory, gestures) and distributed control for real-time coordination, rhythm alignment, and improvisation.
                            </p>
                        </div>

                        {/* Card 3: Control */}
                        <div className="glass-card p-8 hover:-translate-y-2 hover:shadow-2xl transition-all duration-300 border-t-4 border-t-indigo-500 group">
                            <h4 className="flex items-center gap-3 text-xl font-bold font-heading text-indigo-600 mb-4">
                                <span className="text-2xl opacity-80 group-hover:scale-110 transition-transform"></span>
                                Control
                            </h4>
                            <p className="text-text-secondary leading-relaxed">
                                Addresses decision-making and safety. A sleek sensor ecosystem enables robots to perceive the environment and <strong>continuously adapt</strong> behavior, allowing for safe leadership in tempo and dynamics.
                            </p>
                        </div>

                        {/* Card 4: Cooperation */}
                        <div className="glass-card p-8 hover:-translate-y-2 hover:shadow-2xl transition-all duration-300 border-t-4 border-t-rose-500 group">
                            <h4 className="flex items-center gap-3 text-xl font-bold font-heading text-rose-600 mb-4">
                                <span className="text-2xl opacity-80 group-hover:scale-110 transition-transform"></span>
                                Cooperation
                            </h4>
                            <p className="text-text-secondary leading-relaxed">
                                The highest level of teaming: sharing situational awareness and <strong>emotional understanding</strong>. Robots recognize emotions to achieve collective virtuosity and enhanced audience engagement.
                            </p>
                        </div>
                    </div>
                </motion.div>

            </div>
        </section>
    );
};

export default ProjectOverview;
