import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Shield, Key, User, ArrowRight } from 'lucide-react';

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleLogin = (e) => {
        e.preventDefault();
        console.log("Login Attempt:", { username, password });

        // Simplified check for troubleshooting
        if (username.trim().toLowerCase() === 'admin' && password === 'admin123') {
            console.log("Login Success");
            localStorage.setItem('isAuthenticated', 'true');
            // Force a small delay to ensure storage is set before navigation
            setTimeout(() => {
                window.location.href = '/municipality';
            }, 100);
        } else {
            console.log("Login Failed");
            setError('Invalid credentials. Hint: admin/admin123');
        }
    };

    return (
        <div className="min-h-screen bg-[#020617] text-white p-6 flex items-center justify-center relative overflow-hidden">
            {/* Decorative Blur */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px]" />

            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass w-full max-w-md p-8 md:p-12 rounded-[2rem] border border-white/5 relative z-10"
            >
                <div className="flex flex-col items-center mb-10 text-center">
                    <div className="w-16 h-16 bg-blue-600/20 rounded-2xl flex items-center justify-center mb-6 border border-blue-500/30">
                        <Shield size={32} className="text-blue-400" />
                    </div>
                    <h1 className="text-3xl font-bold mb-2">Internal Access</h1>
                    <p className="text-slate-500">Municipality Portal - SMC Digital</p>
                </div>

                <form onSubmit={handleLogin} className="space-y-6">
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-400 ml-1">Username</label>
                        <div className="relative">
                            <User className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                            <input
                                required
                                className="w-full bg-white/5 border border-white/10 rounded-2xl pl-12 pr-4 py-4 focus:outline-none focus:border-blue-500 transition-all font-medium placeholder:text-slate-700"
                                placeholder="Official Username"
                                value={username}
                                onChange={e => setUsername(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-400 ml-1">Password</label>
                        <div className="relative">
                            <Key className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                            <input
                                required
                                type="password"
                                className="w-full bg-white/5 border border-white/10 rounded-2xl pl-12 pr-4 py-4 focus:outline-none focus:border-blue-500 transition-all font-medium placeholder:text-slate-700"
                                placeholder="••••••••"
                                value={password}
                                onChange={e => setPassword(e.target.value)}
                            />
                        </div>
                    </div>

                    {error && <p className="text-red-400 text-sm text-center font-medium bg-red-400/10 py-2 rounded-lg border border-red-400/20">{error}</p>}

                    <button
                        type="submit"
                        className="w-full bg-blue-600 hover:bg-blue-500 py-4 rounded-2xl font-bold flex items-center justify-center gap-2 transition-all shadow-lg shadow-blue-600/20 group text-lg"
                    >
                        Authenticate <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                    </button>
                </form>

                <p className="mt-10 text-center text-slate-600 text-xs">
                    This system is restricted to authorized personnel only. <br /> All access is logged and monitored.
                </p>
            </motion.div>
        </div>
    );
};

export default Login;
