import React from 'react';
import { motion } from 'framer-motion';

const modules = [
    {
        title: "Edge Node",
        subtitle: "Sensory Processing Unit",
        desc: "On-site, low-latency pre-processing of video and audio data. Performs real-time facial and audio feature extraction before data aggregation.",
        specs: ["Low Latency", "Feature Extraction", "Data Aggregation"],
    },
    {
        title: "Micro-Edges",
        subtitle: "Distributed Array",
        desc: "Granular equipment set deployed in tandem with Edge Nodes to extend sensory coverage and distributed computing capabilities.",
        specs: ["Distributed", "Scalable", "Auxiliary Support"],
    },
    {
        title: "Central Architecture",
        subtitle: "High-Performance Server",
        desc: "Powerhouse accelerating complex audio/video processing and LLM inference. Ensures real-time performance for the entire ecosystem.",
        specs: ["Dual GPUs", "LLM Inference", "Real-time Sync"],
    },
    {
        title: "Interface Devices",
        subtitle: "Bio-Feedback Link",
        desc: "Captures audience physiological data (heart rate, movement) and brainwave activity for advanced emotion and cognitive state analysis.",
        specs: ["EEG/Brainwaves", "Heart Rate Monitor", "Motion Tracking"],
    },
    {
        title: "Neural Fabric",
        subtitle: "Networking Equipment",
        desc: "WiFi GBRouters, high-speed switches, and fiber cabling ensuring high-bandwidth, low-latency reliable communication across the entity.",
        specs: ["Gigabit Capacity", "Low Latency", "Reliable Mesh"],
    },
    {
        title: "Unitree G1",
        subtitle: "Humanoid Agent",
        desc: "A high-performance general-purpose humanoid robot featuring 360° sensory perception and advanced joint flexibility. Designed for agile movement and robust human-robot collaboration.",
        specs: ["360° LiDAR/Depth", "High Torque Motors", "AI-Driven"],
    }
];

const Equipment = () => {
    return (
        <div className="min-h-screen bg-gray-50 py-24 relative overflow-hidden">
            {/* Subtle Background Pattern */}
            <div className="absolute inset-0 bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] [background-size:16px_16px] opacity-50 pointer-events-none" />

            <div className="max-w-7xl mx-auto px-6 relative z-10">
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="text-center mb-20"
                >
                    <span className="text-accent-blue font-bold tracking-widest uppercase text-sm mb-4 block">System Infrastructure</span>
                    <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
                        Hardware Nexus
                    </h1>
                    <p className="text-gray-600 max-w-2xl mx-auto text-lg leading-relaxed">
                        The sophisticated physical architecture empowering the HRC Music4D ecosystem, from distributed sensing to central processing.
                    </p>
                </motion.div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {modules.map((item, index) => (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: index * 0.1 }}
                            viewport={{ once: true }}
                            className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-xl transition-all duration-300 border border-gray-100 group hover:-translate-y-1"
                        >
                            {/* Header */}
                            <div className="flex items-start justify-between mb-6">
                                <div>
                                    <h3 className="text-xl font-bold text-gray-900 mb-1 group-hover:text-accent-blue transition-colors">{item.title}</h3>
                                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{item.subtitle}</p>
                                </div>
                            </div>

                            {/* Description */}
                            <p className="text-gray-600 leading-relaxed mb-8 text-sm">
                                {item.desc}
                            </p>

                            {/* Specs / Tags */}
                            <div className="flex flex-wrap gap-2 mt-auto pt-6 border-t border-gray-100">
                                {item.specs.map((spec, i) => (
                                    <span key={i} className="px-3 py-1 bg-gray-50 border border-gray-200 rounded-full text-xs font-medium text-gray-600">
                                        {spec}
                                    </span>
                                ))}
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default Equipment;
