import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, LineChart, Line
} from 'recharts';
import {
    Shield, Users, ClipboardList, CheckCircle2, Clock, BarChart3,
    Settings, LogOut, Search, Map as MapIcon, MoreVertical, ExternalLink
} from 'lucide-react';

const MunicipalityDashboard = () => {
    const [stats, setStats] = useState({ total: 0, pending: 0, in_progress: 0, resolved: 0 });
    const [complaints, setComplaints] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('dashboard');

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [statsRes, complaintsRes] = await Promise.all([
                axios.get(`/api/analytics`),
                axios.get(`/api/complaints`)
            ]);
            setStats(statsRes.data);
            setComplaints(complaintsRes.data);
        } catch (error) {
            console.error("Error fetching admin data:", error);
        } finally {
            setLoading(false);
        }
    };

    const updateStatus = async (id, newStatus) => {
        try {
            const formData = new FormData();
            formData.append('status', newStatus);
            await axios.patch(`/api/complaints/${id}`, formData);
            fetchData();
        } catch (err) {
            alert("Failed to update status");
        }
    };

    const pieData = [
        { name: 'Pending', value: stats.pending, color: '#f59e0b' },
        { name: 'In Progress', value: stats.in_progress, color: '#2563eb' },
        { name: 'Resolved', value: stats.resolved, color: '#10b981' },
    ];

    const menuItems = [
        { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
        { id: 'complaints', label: 'Complaints', icon: ClipboardList },
        { id: 'contractors', label: 'Contractors', icon: Users },
        { id: 'settings', label: 'Settings', icon: Settings },
    ];

    return (
        <div className="min-h-screen bg-[#020617] text-slate-200 flex">
            {/* Sidebar */}
            <div className="w-64 bg-[#0f172a] border-r border-white/5 p-6 flex flex-col">
                <div className="flex items-center gap-3 mb-12">
                    <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
                        <Shield size={20} className="text-white" />
                    </div>
                    <span className="font-bold text-xl tracking-tight">ADMIN PANEL</span>
                </div>

                <nav className="flex-1 space-y-2">
                    {menuItems.map((item) => (
                        <div
                            key={item.id}
                            onClick={() => setActiveTab(item.id)}
                            className={`p-3 rounded-xl flex items-center gap-3 cursor-pointer transition-all ${activeTab === item.id
                                ? 'bg-blue-600/10 text-blue-400 font-semibold'
                                : 'hover:bg-white/5 text-slate-400'
                                }`}
                        >
                            <item.icon size={20} />
                            <span>{item.label}</span>
                        </div>
                    ))}
                </nav>

                <div className="mt-auto pt-6 border-t border-white/5">
                    <button
                        onClick={() => {
                            localStorage.removeItem('isAuthenticated');
                            window.location.reload();
                        }}
                        className="flex items-center gap-3 text-red-400 hover:text-red-300 transition-colors w-full"
                    >
                        <LogOut size={20} /> <span>Logout</span>
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 p-8 overflow-y-auto">
                <header className="flex justify-between items-center mb-12">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">
                            {activeTab === 'dashboard' ? 'Municipality Overview' :
                                activeTab === 'complaints' ? 'Direct Complaints' :
                                    activeTab === 'contractors' ? 'Contractor Management' : 'System Settings'}
                        </h1>
                        <p className="text-slate-500">
                            {activeTab === 'dashboard' ? 'Managing road health across Ward 1-20' :
                                activeTab === 'complaints' ? 'Reviewing and processing citizen reports' :
                                    activeTab === 'contractors' ? 'Managing external work orders' : 'Configure platform preferences'}
                        </p>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                            <input
                                className="bg-[#0f172a] border border-white/10 rounded-xl pl-10 pr-4 py-2 w-64 focus:outline-none focus:border-blue-500 transition-all font-medium"
                                placeholder="Search..."
                            />
                        </div>
                        <div className="w-10 h-10 bg-slate-800 rounded-full border border-white/10" />
                    </div>
                </header>

                {activeTab === 'dashboard' && (
                    <>
                        {/* Stats Cards */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                            {[
                                { label: 'Total Reports', val: stats.total, icon: ClipboardList, color: 'text-blue-400', bg: 'bg-blue-400/10' },
                                { label: 'Pending', val: stats.pending, icon: Clock, color: 'text-amber-400', bg: 'bg-amber-400/10' },
                                { label: 'In Progress', val: stats.in_progress, icon: BarChart3, color: 'text-indigo-400', bg: 'bg-indigo-400/10' },
                                { label: 'Resolved', val: stats.resolved, icon: CheckCircle2, color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
                            ].map((s, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: i * 0.1 }}
                                    className="glass p-6 rounded-3xl border border-white/5"
                                >
                                    <div className={`w-12 h-12 ${s.bg} ${s.color} rounded-2xl flex items-center justify-center mb-4`}>
                                        <s.icon size={24} />
                                    </div>
                                    <p className="text-slate-500 font-medium">{s.label}</p>
                                    <h3 className="text-3xl font-bold text-white mt-1">{s.val}</h3>
                                </motion.div>
                            ))}
                        </div>

                        {/* Charts Section */}
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-12">
                            <div className="lg:col-span-2 glass p-8 rounded-3xl border border-white/5">
                                <h3 className="text-xl font-bold mb-8">Damage Trends</h3>
                                <div className="h-64">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={[
                                            { name: 'Mon', count: 4 }, { name: 'Tue', count: 7 }, { name: 'Wed', count: 5 },
                                            { name: 'Thu', count: 12 }, { name: 'Fri', count: 8 }, { name: 'Sat', count: 3 },
                                            { name: 'Sun', count: 5 }
                                        ]}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                                            <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#64748b' }} />
                                            <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b' }} />
                                            <Tooltip
                                                contentStyle={{ backgroundColor: '#0f172a', border: 'none', borderRadius: '12px', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.5)' }}
                                            />
                                            <Bar dataKey="count" fill="#2563eb" radius={[4, 4, 0, 0]} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                            <div className="glass p-8 rounded-3xl border border-white/5">
                                <h3 className="text-xl font-bold mb-8">Resolution Split</h3>
                                <div className="h-64 relative">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie
                                                data={pieData}
                                                innerRadius={60}
                                                outerRadius={80}
                                                paddingAngle={5}
                                                dataKey="value"
                                            >
                                                {pieData.map((entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                                ))}
                                            </Pie>
                                            <Tooltip
                                                contentStyle={{ backgroundColor: '#0f172a', border: 'none', borderRadius: '12px' }}
                                            />
                                        </PieChart>
                                    </ResponsiveContainer>
                                    <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                                        <span className="text-2xl font-bold">{stats.total}</span>
                                        <span className="text-xs text-slate-500 uppercase">Total</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </>
                )}

                {(activeTab === 'dashboard' || activeTab === 'complaints') && (
                    /* Management Table */
                    <div className="glass rounded-3xl border border-white/5 overflow-hidden">
                        <div className="p-8 border-b border-white/5 flex justify-between items-center">
                            <h3 className="text-xl font-bold">Recent Complaints</h3>
                            {activeTab === 'dashboard' && (
                                <button onClick={() => setActiveTab('complaints')} className="text-blue-400 text-sm font-semibold hover:underline">
                                    View All
                                </button>
                            )}
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left">
                                <thead>
                                    <tr className="bg-white/5 text-slate-400 text-sm font-medium uppercase tracking-wider">
                                        <th className="px-8 py-4">ID</th>
                                        <th className="px-8 py-4">Citizen</th>
                                        <th className="px-8 py-4">Damage Type</th>
                                        <th className="px-8 py-4">AI Confidence</th>
                                        <th className="px-8 py-4">Ward</th>
                                        <th className="px-8 py-4">Location</th>
                                        <th className="px-8 py-4">Photo</th>
                                        <th className="px-8 py-4">Status</th>
                                        <th className="px-8 py-4 text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5">
                                    {complaints.map((c) => (
                                        <tr key={c.complaint_id} className="hover:bg-white/[0.02] transition-colors">
                                            <td className="px-8 py-6 font-mono text-blue-400 text-sm">#{c.complaint_id}</td>
                                            <td className="px-8 py-6 font-medium text-white">{c.citizen_name}</td>
                                            <td className="px-8 py-6">
                                                <span className="bg-slate-800 px-3 py-1 rounded-full text-xs text-slate-300">
                                                    {c.damage_type}
                                                </span>
                                            </td>
                                            <td className="px-8 py-6">
                                                {c.ai_confidence ? (
                                                    <span className={`font-bold text-sm ${c.ai_confidence > 0.8 ? 'text-emerald-400' : 'text-amber-400'}`}>
                                                        {(c.ai_confidence * 100).toFixed(1)}%
                                                    </span>
                                                ) : (
                                                    <span className="text-slate-600 text-xs">-</span>
                                                )}
                                            </td>
                                            <td className="px-8 py-6 text-slate-400">{c.ward}</td>
                                            <td className="px-8 py-6">
                                                {c.latitude && c.longitude ? (
                                                    <a
                                                        href={`https://www.google.com/maps?q=${c.latitude},${c.longitude}`}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors"
                                                    >
                                                        <MapIcon size={16} />
                                                        <span className="text-xs font-medium">View Map</span>
                                                        <ExternalLink size={12} />
                                                    </a>
                                                ) : (
                                                    <span className="text-slate-600 text-xs italic">No GPS Data</span>
                                                )}
                                            </td>
                                            <td className="px-8 py-6">
                                                {c.image_path ? (
                                                    <a
                                                        href={`/${c.image_path}`}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="w-12 h-12 block group relative overflow-hidden rounded-lg border border-white/10"
                                                    >
                                                        <img
                                                            src={`/${c.image_path}`}
                                                            alt="Road Damage"
                                                            className="w-full h-full object-cover transition-transform group-hover:scale-110"
                                                        />
                                                        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                                                            <Search size={14} className="text-white" />
                                                        </div>
                                                    </a>
                                                ) : (
                                                    <span className="text-slate-600 text-xs italic">No Photo</span>
                                                )}
                                            </td>
                                            <td className="px-8 py-6">
                                                <select
                                                    className={`text-xs font-bold px-3 py-1 rounded-full bg-opacity-10 border border-current focus:outline-none cursor-pointer ${c.status === 'Pending' ? 'text-amber-400' :
                                                        c.status === 'In Progress' ? 'text-blue-400' : 'text-emerald-400'
                                                        }`}
                                                    value={c.status}
                                                    onChange={(e) => updateStatus(c.complaint_id, e.target.value)}
                                                >
                                                    <option value="Pending" className="bg-[#0f172a]">Pending</option>
                                                    <option value="In Progress" className="bg-[#0f172a]">In-Progress</option>
                                                    <option value="Resolved" className="bg-[#0f172a]">Resolved</option>
                                                </select>
                                            </td>
                                            <td className="px-8 py-6 text-right">
                                                <button className="text-slate-500 hover:text-white transition-colors">
                                                    <MoreVertical size={20} />
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                    {complaints.length === 0 && (
                                        <tr>
                                            <td colSpan="8" className="px-8 py-12 text-center text-slate-500">
                                                No complaints reported yet.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {activeTab === 'contractors' && (
                    <div className="flex flex-col items-center justify-center py-20 bg-white/5 rounded-3xl border border-dashed border-white/10">
                        <Users size={48} className="text-slate-600 mb-4" />
                        <h3 className="text-xl font-bold text-white">Contractor Portal</h3>
                        <p className="text-slate-500">This module is part of the next phase implementation.</p>
                    </div>
                )}

                {activeTab === 'settings' && (
                    <div className="flex flex-col items-center justify-center py-20 bg-white/5 rounded-3xl border border-dashed border-white/10">
                        <Settings size={48} className="text-slate-600 mb-4" />
                        <h3 className="text-xl font-bold text-white">System Settings</h3>
                        <p className="text-slate-500">Administrative settings and permissions.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default MunicipalityDashboard;
