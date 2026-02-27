import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, MapPin, CheckCircle2, AlertCircle, Send, X } from 'lucide-react';
import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Component to handle map center updates
const RecenterMap = ({ center }) => {
    const map = useMap();
    useEffect(() => {
        if (center) map.setView([center.lat, center.lng]);
    }, [center, map]);
    return null;
};

// Fix for default marker icon in Leaflet + React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const CitizenPortal = () => {
    const [step, setStep] = useState(1);
    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [loading, setLoading] = useState(false);
    const [aiResult, setAiResult] = useState(null);
    const [apiError, setApiError] = useState(false);
    const [location, setLocation] = useState({ lat: 12.9716, lng: 77.5946 }); // Default to Bangalore
    const [formData, setFormData] = useState({
        name: '',
        phone: '',
        ward: '',
        damage_type: '',
        description: ''
    });
    const [locationStatus, setLocationStatus] = useState('idle'); // idle, searching, success, error
    const [imageDims, setImageDims] = useState({ width: 1, height: 1 });

    const getCurrentLocation = () => {
        if (navigator.geolocation) {
            setLocationStatus('searching');
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const currentPos = { lat: position.coords.latitude, lng: position.coords.longitude };
                    setLocation(currentPos);
                    setLocationStatus('success');
                },
                (error) => {
                    setLocationStatus('error');
                    alert("Location Error: " + error.message + ". Please verify that your browser has location permissions enabled for this site.");
                },
                { enableHighAccuracy: true, timeout: 8000 }
            );
        } else {
            alert("Geolocation is not supported by this browser.");
        }
    };

    useEffect(() => {
        getCurrentLocation();
    }, []);

    const handleFileChange = async (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile) {
            setFile(selectedFile);
            setPreview(URL.createObjectURL(selectedFile));
            validateImage(selectedFile);
        }
    };

    const validateImage = async (file) => {
        setLoading(true);
        const data = new FormData();
        data.append('file', file);

        try {
            const response = await axios.post(`/api/validate-image`, data);
            setAiResult(response.data.ai_result);

            // CRITICAL: PRIORITIZE PHOTO GPS DATA
            if (response.data.gps_data && response.data.gps_data.latitude) {
                console.log("✅ Using Photo's Capture Location:", response.data.gps_data);
                setLocation({
                    lat: response.data.gps_data.latitude,
                    lng: response.data.gps_data.longitude
                });
            } else {
                console.log("❌ Photo has no GPS data. User must set location on map.");
            }

            if (response.data.ai_result.result === "Road Damage Detected") {
                setFormData(prev => ({ ...prev, damage_type: response.data.ai_result.type }));
            }
        } catch (error) {
            console.error("Error validating image:", error);
            setApiError(true);
            setAiResult({ status: "error", result: "Backend Connection Error" });
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        const data = new FormData();
        Object.keys(formData).forEach(key => data.append(key, formData[key]));
        data.append('image', file);
        data.append('latitude', location.lat);
        data.append('longitude', location.lng);

        try {
            const response = await axios.post(`/api/report`, data);
            alert(`Success! Complaint ID: ${response.data.complaint_id}`);
            setStep(4);
        } catch (error) {
            alert("Submission failed. Check console.");
        } finally {
            setLoading(false);
        }
    };

    const LocationPicker = () => {
        useMapEvents({
            click(e) {
                setLocation(e.latlng);
            },
        });
        return location ? <Marker position={location} /> : null;
    };

    return (
        <div className="min-h-screen bg-[#0f172a] text-white p-4 md:p-8 flex items-center justify-center">
            <motion.div
                layout
                className="glass w-full max-w-4xl rounded-3xl overflow-hidden flex flex-col md:flex-row min-h-[600px]"
            >
                {/* Progress Sidebar */}
                <div className="w-full md:w-1/3 bg-blue-600/10 p-8 border-b md:border-b-0 md:border-r border-white/5">
                    <h2 className="text-2xl font-bold mb-8">Report Damage</h2>
                    <div className="space-y-6">
                        {[
                            { id: 1, label: 'Upload Photo' },
                            { id: 2, label: 'Detection & Location' },
                            { id: 3, label: 'Details' }
                        ].map(s => (
                            <div key={s.id} className={`flex items-center gap-4 ${step >= s.id ? 'text-blue-400' : 'text-slate-500'}`}>
                                <div className={`w-8 h-8 rounded-full border-2 flex items-center justify-center font-bold ${step >= s.id ? 'border-blue-400 bg-blue-400/10' : 'border-slate-700'}`}>
                                    {step > s.id ? <CheckCircle2 size={16} /> : s.id}
                                </div>
                                <span className="font-semibold">{s.label}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Content Area */}
                <div className="flex-1 p-8 md:p-12 overflow-y-auto">
                    <AnimatePresence mode="wait">
                        {step === 1 && (
                            <motion.div
                                key="step1"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                className="h-full flex flex-col justify-center"
                            >
                                <h3 className="text-3xl font-bold mb-4 text-white">Share what's wrong</h3>
                                <p className="text-slate-400 mb-8">Our AI will automatically detect damage and extract coordinates from your photo.</p>

                                <label className="border-2 border-dashed border-white/10 rounded-3xl p-12 flex flex-col items-center justify-center cursor-pointer hover:border-blue-500/50 transition-all group">
                                    <input type="file" className="hidden" onChange={handleFileChange} accept="image/*" />
                                    <Upload size={48} className="text-slate-500 group-hover:text-blue-400 mb-4 transition-colors" />
                                    <span className="text-lg font-medium">Click to upload or drag & drop</span>
                                    <span className="text-sm text-slate-500 mt-2">JPG, PNG up to 10MB</span>
                                </label>

                                {file && (
                                    <div className="mt-8 flex items-center justify-between glass p-4 rounded-2xl">
                                        <div className="flex items-center gap-4">
                                            {preview && <img src={preview} alt="Preview" className="w-12 h-12 rounded-lg object-cover" />}
                                            <span className="font-medium truncate max-w-[200px]">{file.name}</span>
                                        </div>
                                        <button onClick={() => setStep(2)} className="bg-blue-600 hover:bg-blue-500 px-6 py-2 rounded-xl font-bold transition-all">
                                            Continue
                                        </button>
                                    </div>
                                )}
                            </motion.div>
                        )}

                        {step === 2 && (
                            <motion.div
                                key="step2"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                className="space-y-8"
                            >
                                <div className="flex items-center justify-between">
                                    <h3 className="text-2xl font-bold">AI Verification</h3>
                                    <button onClick={() => setStep(1)} className="text-slate-400 hover:text-white flex items-center gap-2">
                                        <X size={18} /> Change Photo
                                    </button>
                                </div>

                                {loading ? (
                                    <div className="flex flex-col items-center py-12">
                                        <div className="w-16 h-16 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin mb-4" />
                                        <p className="text-slate-400">Analyzing image and extracting metadata...</p>
                                    </div>
                                ) : (
                                    <>
                                        <div className={`p-6 rounded-3xl flex items-center gap-4 ${apiError ? 'bg-red-500/20 border border-red-500/50' : aiResult?.result === "Road Damage Detected" ? 'bg-emerald-500/10 border border-emerald-500/30' : 'bg-slate-500/10 border border-white/10'}`}>
                                            {apiError ? (
                                                <AlertCircle size={32} className="text-red-400" />
                                            ) : aiResult?.result === "Road Damage Detected" ? (
                                                <CheckCircle2 size={32} className="text-emerald-400" />
                                            ) : (
                                                <div className="w-8 h-8 border-2 border-blue-500/20 border-t-blue-500 rounded-full animate-spin" />
                                            )}
                                            <div className="flex-1">
                                                <p className="font-bold text-lg">
                                                    {apiError ? "Backend Server Offline" : aiResult?.result || "Analyzing..."}
                                                </p>
                                                <p className="text-sm opacity-70">
                                                    {apiError ? "The AI service is unreachable. Ensure the backend is running." : `Detection Confidence: ${aiResult?.confidence ? (aiResult.confidence * 100).toFixed(1) : "0.0"}%`}
                                                </p>
                                                {!aiResult?.gps_data && !apiError && (
                                                    <p className="text-xs mt-2 text-amber-400 font-medium">⚠️ Photo capture location not found. Defaulting to Bangalore or your picker selection.</p>
                                                )}
                                            </div>
                                        </div>

                                        {/* IMAGE WITH BBOX OVERLAY */}
                                        <div className="relative group overflow-hidden rounded-3xl border border-white/10 mx-auto max-w-sm">
                                            <img
                                                src={preview}
                                                alt="Detection Result"
                                                className="w-full h-auto"
                                                onLoad={(e) => {
                                                    setImageDims({
                                                        width: e.target.naturalWidth,
                                                        height: e.target.naturalHeight
                                                    });
                                                }}
                                            />
                                            {aiResult?.bbox && (
                                                <div
                                                    className="absolute border-4 border-emerald-400 shadow-[0_0_15px_rgba(52,211,153,0.5)] flex flex-col justify-start"
                                                    style={{
                                                        left: `${(aiResult.bbox[0] / imageDims.width) * 100}%`,
                                                        top: `${(aiResult.bbox[1] / imageDims.height) * 100}%`,
                                                        width: `${((aiResult.bbox[2] - aiResult.bbox[0]) / imageDims.width) * 100}%`,
                                                        height: `${((aiResult.bbox[3] - aiResult.bbox[1]) / imageDims.height) * 100}%`
                                                    }}
                                                >
                                                    <span className="bg-emerald-400 text-black text-[10px] font-bold px-1 w-fit uppercase">
                                                        {aiResult.type} ({(aiResult.confidence * 100).toFixed(0)}%)
                                                    </span>
                                                </div>
                                            )}
                                        </div>

                                        <div className="flex justify-between items-center px-2">
                                            <div className="flex flex-col">
                                                <p className="text-sm font-semibold text-slate-300">Target Location:</p>
                                                <p className="text-[10px] text-slate-500 font-mono">{location.lat.toFixed(4)}, {location.lng.toFixed(4)}</p>
                                            </div>
                                            <button
                                                onClick={getCurrentLocation}
                                                disabled={locationStatus === 'searching'}
                                                className={`text-xs px-3 py-1 rounded-full border transition-all flex items-center gap-1 ${locationStatus === 'searching'
                                                    ? 'bg-slate-700 border-slate-600 text-slate-400 cursor-wait'
                                                    : 'bg-blue-600/20 hover:bg-blue-600/40 text-blue-400 border-blue-400/30'
                                                    }`}
                                            >
                                                <MapPin size={12} className={locationStatus === 'searching' ? 'animate-pulse' : ''} />
                                                {locationStatus === 'searching' ? 'Detecting...' : 'Use My Current Location'}
                                            </button>
                                        </div>

                                        <div className="h-64 rounded-3xl overflow-hidden border border-white/10">
                                            <MapContainer center={[location.lat, location.lng]} zoom={15} style={{ height: '100%', width: '100%' }}>
                                                <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                                                <RecenterMap center={location} />
                                                <LocationPicker />
                                            </MapContainer>
                                        </div>
                                        <p className="text-xs text-slate-500 text-center italic">Tip: Click on map to adjust location if GPS was not found</p>

                                        <button
                                            onClick={() => setStep(3)}
                                            disabled={aiResult?.result !== "Road Damage Detected"}
                                            className={`w-full py-4 rounded-2xl font-bold transition-all ${aiResult?.result === "Road Damage Detected" ? 'bg-blue-600 hover:bg-blue-500 shadow-lg shadow-blue-600/20' : 'bg-slate-700 cursor-not-allowed opacity-50'}`}
                                        >
                                            Process Complaint
                                        </button>
                                    </>
                                )}
                            </motion.div>
                        )}

                        {step === 3 && (
                            <motion.div
                                key="step3"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                className="space-y-6"
                            >
                                <h3 className="text-2xl font-bold">Complaint Details</h3>
                                <form onSubmit={handleSubmit} className="space-y-4">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium text-slate-400">Full Name</label>
                                            <input
                                                required
                                                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 focus:outline-none focus:border-blue-500 transition-all"
                                                placeholder="John Doe"
                                                value={formData.name}
                                                onChange={e => setFormData({ ...formData, name: e.target.value })}
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium text-slate-400">Phone</label>
                                            <input
                                                required
                                                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 focus:outline-none focus:border-blue-500 transition-all"
                                                placeholder="+91 98765 43210"
                                                value={formData.phone}
                                                onChange={e => setFormData({ ...formData, phone: e.target.value })}
                                            />
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium text-slate-400">Ward Number</label>
                                            <input
                                                required
                                                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 focus:outline-none focus:border-blue-500 transition-all"
                                                placeholder="Ward 12"
                                                value={formData.ward}
                                                onChange={e => setFormData({ ...formData, ward: e.target.value })}
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium text-slate-400">Damage Type</label>
                                            <select
                                                className="w-full bg-[#1e293b] border border-white/10 rounded-xl px-4 py-3 focus:outline-none focus:border-blue-500 transition-all"
                                                value={formData.damage_type}
                                                onChange={e => setFormData({ ...formData, damage_type: e.target.value })}
                                            >
                                                <option value="Pothole">Pothole</option>
                                                <option value="Crack">Crack</option>
                                                <option value="Surface Damage">Surface Damage</option>
                                                <option value="Water Logging">Water Logging</option>
                                            </select>
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-slate-400">Description</label>
                                        <textarea
                                            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 focus:outline-none focus:border-blue-500 transition-all h-24"
                                            placeholder="Give more details about the location or severity..."
                                            value={formData.description}
                                            onChange={e => setFormData({ ...formData, description: e.target.value })}
                                        />
                                    </div>

                                    <button
                                        type="submit"
                                        disabled={loading}
                                        className="w-full bg-emerald-600 hover:bg-emerald-500 py-4 rounded-2xl font-bold flex items-center justify-center gap-2 transition-all shadow-lg shadow-emerald-600/20"
                                    >
                                        {loading ? "Submitting..." : <><Send size={18} /> Submit Complaint</>}
                                    </button>
                                </form>
                            </motion.div>
                        )}

                        {step === 4 && (
                            <motion.div
                                key="step4"
                                initial={{ scale: 0.9, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                className="h-full flex flex-col items-center justify-center text-center space-y-6"
                            >
                                <div className="w-24 h-24 bg-emerald-500/20 rounded-full flex items-center justify-center mb-4">
                                    <CheckCircle2 size={48} className="text-emerald-400" />
                                </div>
                                <h3 className="text-3xl font-bold">Complaint Registered Successfully</h3>
                                <p className="text-slate-400 max-w-sm">We've received your report. Officials will review it shortly. You'll receive updates on your provided phone number.</p>
                                <button
                                    onClick={() => window.location.href = '/'}
                                    className="bg-blue-600 hover:bg-blue-500 px-8 py-3 rounded-xl font-bold transition-all"
                                >
                                    Return to Home
                                </button>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </motion.div>
        </div>
    );
};

export default CitizenPortal;
