import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import CategorySetupStep from '../../components/parking/CategorySetupStep';
import PricingSetupStep from '../../components/parking/PricingSetupStep';

// Red map pin icon
const customIcon = L.icon({
    iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.3.1/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

const LocationPicker = ({ position, setPosition, setAddress }) => {
    useMapEvents({
        click: async (e) => {
            const { lat, lng } = e.latlng;
            setPosition([lat, lng]);
            try {
                const res = await api.get(`/parking/geocode/reverse?lat=${lat}&lng=${lng}`);
                const data = res.data;
                if (data.display_name) {
                    setAddress(data.display_name);
                }
            } catch (err) {
                console.error('Geocoding error', err);
            }
        }
    });

    return position === null ? null : (
        <Marker position={position} icon={customIcon} />
    );
};

const AddParkingPage = () => {
    const navigate = useNavigate();
    const { currentUser } = useAuth();

    // Wizard Step Management
    const [step, setStep] = useState(1);

    // Step 1: Basic Lot Details
    const [name, setName] = useState('');
    const [address, setAddress] = useState('');
    const [position, setPosition] = useState(null);
    const [totalCapacity, setTotalCapacity] = useState('');

    // Step 2: Categories
    const [categories, setCategories] = useState({});

    // Step 3: Pricing
    const [priceData, setPriceData] = useState({});

    const [loading, setLoading] = useState(false);

    const handleSubmit = async () => {
        setLoading(true);
        try {
            // Prepare the v2.0 body
            const formattedCategories = Object.keys(categories).map(catId => ({
                category: catId,
                total_slots: categories[catId].total_slots,
                available_slots: categories[catId].total_slots, // brand new lot
                has_ev_charging: categories[catId].has_ev_charging,
                slot_width_m: catId.includes('large') ? 2.8 : 2.5,
                slot_length_m: catId.includes('large') ? 5.5 : 5.0,
                ...priceData[catId]
            }));

            // Register Owner first, then Lot
            const ownerPayload = {
                name: currentUser.name,
                email: currentUser.email,
                phone: currentUser.phone || "9999999999",
                business_name: name,
                role: "owner"
            };

            const lotPayload = {
                lot_name: name,
                address: address,
                city: "Pune",
                total_capacity: parseInt(totalCapacity, 10),
                categories: formattedCategories,
                latitude: position[0],
                longitude: position[1]
            };

            await api.post('/owner/register', {
                owner: ownerPayload,
                lot: lotPayload
            });

            alert('Parking Lot v2.0 successfully registered and live!');
            navigate('/owner/dashboard');
        } catch (err) {
            console.error(err);
            alert('Failed to register parking lot.');
        } finally {
            setLoading(false);
        }
    };

    const isStepValid = () => {
        if (step === 1) return name && address && position && totalCapacity > 0;
        if (step === 2) {
            const assigned = Object.values(categories).reduce((sum, c) => sum + c.total_slots, 0);
            return assigned === parseInt(totalCapacity, 10);
        }
        if (step === 3) {
            const activeCats = Object.keys(categories);
            return activeCats.every(catId => priceData[catId]?.price_per_hour > 0);
        }
        return true;
    };

    return (
        <div className="p-10 bg-slate-950 min-h-screen text-slate-100 font-inter">
            <div className="max-w-4xl mx-auto">
                <div className="flex justify-between items-center mb-10">
                    <h1 className="text-3xl font-black bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent">
                        Setup Your Smart Parking v2.0
                    </h1>
                    <div className="flex gap-2">
                        {[1, 2, 3].map(s => (
                            <div key={s} className={`w-10 h-2 rounded-full transition-all duration-500 ${step >= s ? 'bg-blue-500 shadow-lg shadow-blue-500/20' : 'bg-slate-800'}`} />
                        ))}
                    </div>
                </div>

                {step === 1 && (
                    <div className="grid md:grid-cols-2 gap-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <section className="bg-slate-900/50 p-8 rounded-2xl border border-slate-800 backdrop-blur-sm space-y-6">
                            <h2 className="text-xl font-bold mb-4">📍 Basic Information</h2>
                            <div>
                                <label className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2 block">Business / Lot Name</label>
                                <input
                                    type="text"
                                    value={name} onChange={e => setName(e.target.value)}
                                    placeholder="e.g. Green Park Plaza"
                                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-white focus:border-blue-500 transition-all focus:ring-4 focus:ring-blue-500/10 outline-none"
                                />
                            </div>
                            <div>
                                <label className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2 block">Total Lot Capacity (Slots)</label>
                                <input
                                    type="number"
                                    value={totalCapacity} onChange={e => setTotalCapacity(e.target.value)}
                                    placeholder="e.g. 150"
                                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-white focus:border-blue-500 transition-all outline-none"
                                />
                            </div>
                            <div>
                                <label className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2 block">Address</label>
                                <textarea
                                    value={address} onChange={e => setAddress(e.target.value)}
                                    rows="4"
                                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-white focus:border-blue-500 transition-all outline-none"
                                />
                            </div>
                        </section>

                        <section className="bg-slate-900/50 p-6 rounded-2xl border border-slate-800 overflow-hidden">
                            <h2 className="text-sm font-bold text-slate-500 mb-4 px-2">Tap to mark location</h2>
                            <div className="h-[350px] rounded-xl overflow-hidden grayscale hover:grayscale-0 transition-all duration-700">
                                <MapContainer center={[17.6868, 75.9060]} zoom={13} style={{ height: '100%', width: '100%' }}>
                                    <TileLayer
                                        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                                        attribution='&copy; OpenStreetMap'
                                    />
                                    <LocationPicker position={position} setPosition={setPosition} setAddress={setAddress} />
                                </MapContainer>
                            </div>
                        </section>
                    </div>
                )}

                {step === 2 && (
                    <div className="bg-slate-900/50 p-8 rounded-2xl border border-slate-800 animate-in fade-in slide-in-from-right-8 duration-500">
                        <CategorySetupStep
                            categories={categories}
                            setCategories={setCategories}
                            totalCapacity={parseInt(totalCapacity)}
                        />
                    </div>
                )}

                {step === 3 && (
                    <div className="bg-slate-900/50 p-8 rounded-2xl border border-slate-800 animate-in fade-in zoom-in-95 duration-500">
                        <PricingSetupStep
                            priceData={priceData}
                            setPriceData={setPriceData}
                            categories={categories}
                        />
                    </div>
                )}

                <div className="flex justify-between mt-12 bg-slate-900/80 p-6 rounded-2xl border border-slate-800 sticky bottom-10 backdrop-blur-md">
                    <button
                        onClick={() => step > 1 ? setStep(step - 1) : navigate(-1)}
                        className="px-8 py-3 rounded-xl font-bold text-slate-400 hover:text-white transition-all uppercase text-sm tracking-widest"
                    >
                        {step === 1 ? 'Cancel Setup' : 'Previous Step'}
                    </button>
                    <button
                        onClick={() => step < 3 ? setStep(step + 1) : handleSubmit()}
                        disabled={loading || !isStepValid()}
                        className="px-10 py-3 rounded-xl font-black bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-30 disabled:grayscale transition-all shadow-xl shadow-blue-900/20 uppercase text-sm tracking-widest"
                    >
                        {loading ? 'Processing...' : (step === 3 ? 'Publish & Go Live 🚀' : 'Next Step →')}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AddParkingPage;
