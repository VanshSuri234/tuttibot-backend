import React from 'react';
import { motion } from 'framer-motion';

const Contact = () => {
    const contacts = [
        {
            title: "SpemeLab Website",
            subtitle: "Official Lab Portal",
            url: "https://labs.dimes.unical.it/speme/",
            color: "bg-[#00609c]", // Darker blue similar to screenshot
            iconColor: "text-[#00609c]",
            icon: (
                <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24" className="w-10 h-10">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
                </svg>
            )
        },
        {
            title: "YouTube",
            subtitle: "Research & Demos",
            url: "https://www.youtube.com/results?search_query=spemelab",
            color: "bg-[#ff0000]",
            iconColor: "text-[#ff0000]",
            icon: (
                <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24" className="w-10 h-10">
                    <path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z" />
                </svg>
            )
        },
        {
            title: "Contact us",
            subtitle: "Prof. Giancarlo Fortino",
            url: "mailto:giancarlo.fortino@unical.it",
            color: "bg-[#5b3c8f]", // Deep purple
            iconColor: "text-[#5b3c8f]",
            icon: (
                <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24" className="w-10 h-10">
                    <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z" />
                </svg>
            )
        }
    ];

    return (
        <div className="py-24 max-w-6xl mx-auto px-6">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className="text-center mb-20"
            >
                <h1 className="text-5xl font-bold font-heading text-text-heading mb-6">Get in <span className="text-accent-blue">Touch</span></h1>
                <p className="text-xl text-text-secondary max-w-2xl mx-auto font-light">Connect with us on our platforms or reach out directly.</p>
            </motion.div>

            <div className="grid md:grid-cols-3 gap-8">
                {contacts.map((item, index) => (
                    <motion.a
                        key={index}
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        initial={{ opacity: 0, y: 30 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.5, delay: index * 0.1 }}
                        className="glass-card block p-10 hover:shadow-2xl hover:-translate-y-2 transition-all duration-300 group relative overflow-hidden"
                    >
                        <div className={`absolute top-0 right-0 w-32 h-32 ${item.color.replace('bg-', 'bg-')} opacity-5 rounded-full blur-2xl -translate-y-8 translate-x-8 group-hover:scale-150 transition-transform duration-700`}></div>

                        <div className="flex flex-col items-center text-center relative z-10">
                            <div className={`w-24 h-24 ${item.color.replace('bg-', 'bg-opacity-10 bg-')} rounded-2xl flex items-center justify-center mb-8 transition-transform duration-300 group-hover:rotate-6 group-hover:scale-110 shadow-sm`}>
                                <div className={item.iconColor}>
                                    {item.icon}
                                </div>
                            </div>
                            <h2 className="text-2xl font-bold font-heading text-text-heading mb-3 group-hover:text-accent-blue transition-colors">{item.title}</h2>
                            <p className="text-text-secondary font-medium text-base mb-6">{item.subtitle}</p>

                            <div className="inline-flex items-center text-sm font-bold text-accent-blue/80 group-hover:text-accent-blue transition-colors uppercase tracking-wider">
                                <span>Visit Link</span>
                                <svg className="w-4 h-4 ml-2 transform group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 8l4 4m0 0l-4 4m4-4H3"></path></svg>
                            </div>
                        </div>
                    </motion.a>
                ))}
            </div>
        </div>
    );
};

export default Contact;
