import React from 'react';
import { motion } from 'framer-motion';
import RobotShowcase from './RobotShowcase';

const Article = ({ date, title, children, delay = 0 }) => (
    <motion.article
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay }}
        viewport={{ once: true, margin: "-50px" }}
        className="mb-32 last:mb-0"
    >
        <div className="flex flex-col md:flex-row gap-8 md:gap-16">
            <div className="md:w-1/4 shrink-0">
                <span className="inline-block py-2 px-4 rounded-full bg-white border border-gray-100 shadow-sm text-accent-blue text-xs font-bold font-heading uppercase tracking-widest mb-4 md:mb-0">
                    {date}
                </span>
            </div>
            <div className="md:w-3/4">
                <h2 className="text-3xl md:text-5xl font-bold font-heading text-text-heading mb-8 leading-tight tracking-tight">{title}</h2>
                <div className="text-lg text-text-main leading-relaxed space-y-6 text-justify font-light">
                    {children}
                </div>
            </div>
        </div>
    </motion.article>
);

const HomeContent = () => {
    return (
        <div className="bg-primary-bg border-t border-gray-100">

            {/* Full Width Robot Showcase - Moved to Top */}
            <div id="project-overview">
                <RobotShowcase />
            </div>

            <div className="py-24 max-w-6xl mx-auto px-6">

                {/* Article 1: From Soloists to Symphony */}
                <Article date="17 Dicembre 2025" title="From Soloists to Symphony: The Evolution of Human-Robot Teaming">
                    <p>
                        <strong className="text-text-heading font-semibold">SPEME Lab</strong> is proud to share its latest research contribution,
                        which pushes the boundaries of how humans and machines operate together.
                    </p>
                    <p className="italic text-text-secondary pl-6 border-l-4 border-accent-blue/30 bg-white/50 py-2 rounded-r-lg">
                        "The traversing of Human Robot Interaction (HRI) to Human Robot Teaming (HRT) has seen huge transformation
                        from human-robots working in collaboration to working as teammates. The progress in automation, network connectivity,
                        and HRI represent a transformative shift to embrace Industry 5.0."
                    </p>

                    <h3 className="text-2xl font-bold font-heading text-text-heading mt-10 mb-4">Why an Orchestra?</h3>
                    <p>
                        The authors identify the musical orchestra as the ultimate testbed for complex dynamics. In this setting,
                        precision isn't enough; the system requires <strong className="text-accent-blue">"entitativity"</strong> —
                        the state where individual agents (human and robotic) feel and act as a single, cohesive unit.
                    </p>
                    <p>
                        Authored by <strong>Rashmi Chawla, Francesco Pupo, and Giancarlo Fortino</strong>, the paper proposes a conceptual review
                        that defines HRT through the framework of the "4Cs":
                    </p>

                    {/* Updated 4Cs Styling (consistent with Tech Vision) */}
                    <ul className="grid grid-cols-1 sm:grid-cols-2 gap-6 mt-8">
                        {[
                            { label: 'Communication', desc: 'Multimodal sensory modalities (visual, auditory, tactile).', borderColor: 'border-l-blue-400' },
                            { label: 'Coordination', desc: 'Syncing actions in real-time.', borderColor: 'border-l-indigo-400' },
                            { label: 'Cooperation', desc: 'Working towards a shared goal.', borderColor: 'border-l-purple-400' },
                            { label: 'Command/Control', desc: 'Dynamic leadership fluidly shifting.', borderColor: 'border-l-pink-400' }
                        ].map((c, i) => (
                            <li key={i} className={`glass-card p-6 rounded-2xl border-l-4 ${c.borderColor} hover:shadow-xl hover:-translate-y-1 transition-all duration-300 group overflow-hidden relative`}>
                                <div className={`absolute top-0 right-0 w-24 h-24 bg-current opacity-5 rounded-full blur-2xl -translate-y-1/2 translate-x-1/2 group-hover:opacity-10 transition-opacity duration-500`} style={{ color: 'var(--accent-base)' }} />
                                <h4 className="text-lg font-bold font-heading text-text-heading mb-3 tracking-wide uppercase relative z-10">{c.label}</h4>
                                <p className="text-text-secondary text-base leading-relaxed relative z-10 group-hover:text-text-main transition-colors">{c.desc}</p>
                            </li>
                        ))}
                    </ul>
                </Article>

                <hr className="my-24 border-gray-200/60" />

                {/* Article 2: HRC Music4D Project */}
                <Article date="7 Maggio 2025" title="HRC Music4D: When Music Meets Artificial Intelligence in the Heart of the Mediterranean">
                    <p>
                        The <strong>HRC Music4D</strong> project, approved within the framework of the "Notice for the granting of funding for the internationalisation
                        of AFAM institutions," represents a global initiative that achieved first place in score and order of funding among
                        the projects approved by the Ministry of University and Research.
                    </p>
                    <p>
                        Coordinated by the <strong>Palermo Conservatory</strong>, the consortium involves all AFAM
                        institutions in Sicily and Sardinia, along with the University of Palermo and the University of Calabria,
                        for a total of <strong>13 partners and nearly 6 million euros in funding</strong>.
                    </p>

                    <h3 className="text-2xl font-bold font-heading text-text-heading mt-10 mb-4">Technical Vision</h3>
                    <p>
                        The project aims to develop an integrated system that combines large-scale deep learning models, advanced sensory capabilities,
                        and a high-performance robotic platform. Central to this vision is the use of a robot capable of analyzing and processing,
                        in real-time, complex signals from the surrounding environment.
                    </p>

                    <div className="grid md:grid-cols-2 gap-8 mt-8">
                        {/* Robotic Platform Card */}
                        <div className="glass-card p-8 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-l-4 border-l-accent-blue relative overflow-hidden group">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-accent-blue/5 rounded-full blur-2xl -translate-y-1/2 translate-x-1/2 group-hover:bg-accent-blue/10 transition-colors duration-500" />
                            <h4 className="text-lg font-bold font-heading text-text-heading mb-3 tracking-wide uppercase relative z-10">Robotic Platform</h4>
                            <p className="text-text-secondary text-base leading-relaxed relative z-10">
                                From a hardware perspective, the <strong className="text-text-heading">NVIDIA Groot N1 platform</strong> will be utilized, allowing for advanced
                                management of movement, perception, and autonomous control. The integration involves collecting data from
                                vision, posture, sound, and environmental sensors.
                            </p>
                        </div>

                        {/* AI Models Card */}
                        <div className="glass-card p-8 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-l-4 border-l-indigo-500 relative overflow-hidden group">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 rounded-full blur-2xl -translate-y-1/2 translate-x-1/2 group-hover:bg-indigo-500/10 transition-colors duration-500" />
                            <h4 className="text-lg font-bold font-heading text-text-heading mb-3 tracking-wide uppercase relative z-10">AI Models</h4>
                            <p className="text-text-secondary text-base leading-relaxed relative z-10">
                                The computational component is based on models of <strong className="text-text-heading">7-8 billion parameters</strong>, designed to ensure
                                a balance between processing power and adaptability. These models continuously learn to capture
                                emotional and behavioral nuances in a performative context.
                            </p>
                        </div>
                    </div>
                </Article>

            </div>
        </div>
    );
};

export default HomeContent;
