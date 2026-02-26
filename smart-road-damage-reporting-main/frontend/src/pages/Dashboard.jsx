import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { User, Shield, MapPin, Camera, BarChart3, Clock } from 'lucide-react';

const Dashboard = () => {
    return (
        <div className="min-h-screen bg-[#0f172a] text-white p-6 md:p-12 lg:p-24 flex flex-col items-center justify-center relative overflow-hidden">
            {/* Decorative Circles */}
            <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/20 rounded-full blur-[100px]" />
            <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-emerald-600/20 rounded-full blur-[100px]" />

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="z-10 text-center max-w-4xl"
            >
                <div className="mb-8 flex justify-center">
                    <img src="/logo.png" alt="SMC Logo" className="w-24 h-24 object-contain shadow-2xl rounded-2xl bg-white p-2" />
                </div>

                <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
                    Smart Road Damage Reporting
                </h1>
                <p className="text-xl text-slate-400 mb-12 max-w-2xl mx-auto">
                    Empowering citizens and municipalities to build safer roads together with AI-driven detection and real-time management.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-3xl mx-auto">
                    <Link to="/citizen">
                        <motion.div
                            whileHover={{ scale: 1.05, translateY: -5 }}
                            whileTap={{ scale: 0.95 }}
                            className="glass p-8 rounded-3xl border border-white/10 hover:border-blue-500/50 transition-all cursor-pointer group card-gradient"
                        >
                            <div className="mb-6 w-16 h-16 bg-blue-500/20 rounded-2xl flex items-center justify-center group-hover:bg-blue-500/30 transition-colors">
                                <User size={32} className="text-blue-400" />
                            </div>
                            <h2 className="text-2xl font-bold mb-3">Citizen Portal</h2>
                            <p className="text-slate-400">Report damage, upload photos, and track repair status in your neighborhood.</p>
                            <div className="mt-6 flex items-center text-blue-400 font-semibold">
                                Get Started <Clock size={18} className="ml-2" />
                            </div>
                        </motion.div>
                    </Link>

                    <Link to="/municipality">
                        <motion.div
                            whileHover={{ scale: 1.05, translateY: -5 }}
                            whileTap={{ scale: 0.95 }}
                            className="glass p-8 rounded-3xl border border-white/10 hover:border-emerald-500/50 transition-all cursor-pointer group"
                        >
                            <div className="mb-6 w-16 h-16 bg-emerald-500/20 rounded-2xl flex items-center justify-center group-hover:bg-emerald-500/30 transition-colors">
                                <Shield size={32} className="text-emerald-400" />
                            </div>
                            <h2 className="text-2xl font-bold mb-3">Municipality Portal</h2>
                            <p className="text-slate-400">Analyze reports, manage workflows, and assign contractors efficiently.</p>
                            <div className="mt-6 flex items-center text-emerald-400 font-semibold">
                                Admin Access <BarChart3 size={18} className="ml-2" />
                            </div>
                        </motion.div>
                    </Link>
                </div>
            </motion.div>

            <div className="mt-24 grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-16 opacity-50 grayscale hover:grayscale-0 transition-all">
                {/* Placeholder Logos */}
                <div className="text-lg font-bold">SMART CITY</div>
                <div className="text-lg font-bold">URBAN TECH</div>
                <div className="text-lg font-bold">SAFE ROADS</div>
                <div className="text-lg font-bold">AI GOV</div>
            </div>
        </div>
    );
};

export default Dashboard;
