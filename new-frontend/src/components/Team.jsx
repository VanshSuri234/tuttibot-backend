import React from 'react';
import { motion } from 'framer-motion';

import imgFortino from '../assets/Fortino-3.jpg';
import imgPupo from '../assets/Pupo-1.jpeg';
import imgMolinaro from '../assets/Molinaro-768x768.jpeg';
import imgKhan from '../assets/Khan-264x300-2-150x150.jpg';
import imgPresta from '../assets/MattiaPresta.png';
import imgChawla from '../assets/Chwalla-768x768.jpeg';
import imgPerri from '../assets/Perri.png';

import imgLongo from '../assets/rlongo_pic.bmp';

// Department Logos
import logoDimes from '../assets/logo_dimes_Q.png';
import badgeSpeme from '../assets/HCR-Ribbon_Social_215x335_ForInstitutions-193x300.png';

const Team = () => {
    // Grouping team members for hierarchy
    const tier1 = [
        { name: 'Giancarlo Fortino', role: 'Professor / Researcher', linkedin: 'https://projects.dimes.unical.it/music4d/il-team/', image: imgFortino, affiliation: "Full Professor at University of Calabria & CEO at Sensyscal S.r.l. & IEEE Fellow" }
    ];

    const tier2 = [
        { name: 'Francesco Pupo', role: 'Researcher', linkedin: 'https://projects.dimes.unical.it/music4d/il-team/', image: imgPupo, affiliation: "Associate Professor at University of Calabria" },
        { name: 'Raffaele Longo', role: 'Music Expert', linkedin: 'https://www.linkedin.com/in/raffaele-longo-897560b7', image: imgLongo, affiliation: "Full Professor of Music Theory ‘Luigi Cherubini” State Conservatory of Music FLORENCE" },
        { name: 'Rashmi Chawla', role: 'Researcher', linkedin: 'https://www.linkedin.com/in/rashmi-chawla-710348128/', image: imgChawla, affiliation: "Associate Professor at JC Bose University, YMCA, India & Post Doc. Researcher at University of Calabria" }
    ];

    const tier3 = [
        { name: 'Pasquale Molinaro', role: 'Team Member', linkedin: 'https://www.linkedin.com/in/pasquale-molinaro-8654021aa/', image: imgMolinaro, affiliation: "Generative AI and Machine Learning Engineer Specialist & Research fellow at University of Calabria" },
        { name: 'Caterina Perri', role: 'Team Member', linkedin: null, image: imgPerri, affiliation: "Ph. D, Post doc at University of Calabria" },
        { name: 'Akhtar Khan', role: 'Team Member', linkedin: null, image: imgKhan, affiliation: "Ph. D at University of Calabria" },
        { name: 'Mattia Presta', role: 'Team Member', linkedin: 'https://www.linkedin.com/in/mattia-presta-66488939a/', image: imgPresta, affiliation: "Generative AI and Machine Learning Engineer Specialist & Research fellow at University of Calabria" }
    ];

    const MemberCard = ({ member, size = "md" }) => {
        const isLarge = size === "lg";
        return (
            <motion.div
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                whileHover={{ y: -8 }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
                className={`group relative bg-white rounded-3xl shadow-soft hover:shadow-2xl transition-all duration-300 border border-gray-100/50 overflow-hidden ${isLarge ? 'p-10 max-w-lg mx-auto' : 'p-6'}`}
            >
                {/* Decorative background blur */}
                <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-b from-gray-50 to-transparent opacity-50 transition-opacity group-hover:opacity-100" />

                <div className="relative z-10 flex flex-col items-center text-center">
                    <div className={`${isLarge ? 'w-48 h-48 border-4' : 'w-32 h-32 border-[3px]'} mb-6 rounded-full overflow-hidden border-white shadow-lg group-hover:scale-105 transition-transform duration-500`}>
                        <img
                            src={member.image}
                            alt={member.name}
                            className="w-full h-full object-cover rounded-full"
                        />
                    </div>

                    <h3 className={`${isLarge ? 'text-3xl' : 'text-xl'} font-bold font-heading text-text-heading mb-2 group-hover:text-accent-blue transition-colors`}>{member.name}</h3>
                    <p className={`${isLarge ? 'text-base' : 'text-xs'} text-accent-blue font-bold uppercase tracking-widest mb-3`}>{member.role}</p>
                    <p className="text-text-secondary text-sm font-medium leading-relaxed max-w-[90%]">{member.affiliation}</p>

                    {member.linkedin && (
                        <a
                            href={member.linkedin}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="mt-6 inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gray-50 text-gray-600 hover:bg-[#0077b5] hover:text-white transition-all duration-300 text-sm font-semibold group/link"
                        >
                            <span>LinkedIn Profile</span>
                            <svg className="w-4 h-4 transform group-hover/link:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                        </a>
                    )}
                </div>
            </motion.div>
        );
    };

    return (
        <div className="py-24 bg-primary-bg min-h-screen">
            <div className="max-w-7xl mx-auto px-6">

                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="text-center mb-20"
                >
                    <h1 className="text-5xl md:text-6xl font-bold font-heading text-text-heading mb-6 tracking-tight">Our <span className="text-accent-blue">Team</span></h1>
                    <p className="text-xl text-text-secondary max-w-2xl mx-auto font-light leading-relaxed">
                        A multidisciplinary collective of researchers and engineers bridging the gap between <span className="font-medium text-text-main">AI</span> and <span className="font-medium text-text-main">Human Emotion</span>.
                    </p>
                </motion.div>

                {/* DIMES Department (Primary) */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="glass-card p-12 mb-16 flex flex-col md:flex-row items-center gap-12 relative overflow-hidden group"
                >
                    <div className="absolute top-0 right-0 w-64 h-64 bg-accent-blue/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:bg-accent-blue/10 transition-colors duration-700" />

                    <div className="w-full md:w-1/3 flex justify-center relative z-10">
                        <img src={logoDimes} alt="DIMES Logo" className="max-w-[280px] drop-shadow-sm transform hover:scale-105 transition-transform duration-500" />
                    </div>
                    <div className="w-full md:w-2/3 text-left relative z-10">
                        <h2 className="text-3xl font-bold font-heading text-text-heading mb-2">DIMES Department</h2>
                        <h3 className="text-xl text-text-secondary font-medium mb-6">University of Calabria</h3>
                        <p className="text-lg text-text-secondary leading-relaxed mb-8 text-justify">
                            The DIMES (Department of Computer Engineering, Modeling, Electronics, and System Engineering) includes 78 professors and researchers, promoting cutting-edge research in computer engineering, modeling, electronics, and telecommunications.
                        </p>
                        <a href="https://www2.dimes.unical.it/" target="_blank" rel="noopener noreferrer" className="group inline-flex items-center text-accent-blue font-bold text-lg hover:text-blue-700 transition-colors">
                            Visit DIMES
                            <span className="ml-2 transform group-hover:translate-x-1 transition-transform duration-300">→</span>
                        </a>
                    </div>
                </motion.div>

                {/* SPEME Lab (Secondary) */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="glass-card p-10 mb-24 flex flex-col md:flex-row-reverse items-center gap-12"
                >
                    <div className="w-full md:w-1/4 flex justify-center">
                        <img src={badgeSpeme} alt="Highly Cited Researchers" className="max-w-[140px] drop-shadow-md" />
                    </div>
                    <div className="w-full md:w-3/4">
                        <h2 className="text-3xl font-bold font-heading text-text-heading mb-4">SPEME Lab at work</h2>
                        <p className="text-lg text-text-secondary leading-relaxed mb-6 text-justify">
                            The SPEME (Smart, PErvasive and Mobile systems Engineering) Lab focuses on trustworthy, distributed, intelligent, and multi-sensorial systems. Steps into Internet of Things and Smart Systems of Systems domains.
                        </p>
                        <a href="https://labs.dimes.unical.it/speme/" target="_blank" rel="noopener noreferrer" className="group inline-flex items-center text-accent-blue font-bold text-lg hover:text-blue-700 transition-colors">
                            Explore SPEME Lab
                            <span className="ml-2 transform group-hover:translate-x-1 transition-transform duration-300">→</span>
                        </a>
                    </div>
                </motion.div>

                {/* Team Hierarchy */}
                <div className="space-y-16">
                    {/* Tier 1: Lead */}
                    <div className="flex justify-center">
                        {tier1.map((member, idx) => <MemberCard key={idx} member={member} size="lg" />)}
                    </div>

                    {/* Tier 2: Key Researchers */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
                        {tier2.map((member, idx) => <MemberCard key={idx} member={member} />)}
                    </div>

                    {/* Tier 3: Team Members */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                        {tier3.map((member, idx) => <MemberCard key={idx} member={member} />)}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Team;
