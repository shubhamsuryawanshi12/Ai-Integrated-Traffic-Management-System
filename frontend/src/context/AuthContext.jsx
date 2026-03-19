import React, { createContext, useContext, useState, useEffect } from "react";
import { auth } from "../services/firebase";
import { onAuthStateChanged } from "firebase/auth";

const AuthContext = createContext();

export function useAuth() {
    return useContext(AuthContext);
}

export function AuthProvider({ children }) {
    const [currentUser, setCurrentUser] = useState(null);
    const [loading, setLoading] = useState(true);

    // RBAC logic for SAMVED Hackathon
    // Roles: 'traffic_police', 'enforcement', 'admin', 'citizen', 'owner'
    const [role, setRole] = useState('citizen');

    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, (userNode) => {
            // For hackathon, if no real Firebase user, we mock one below in switchRole
            setLoading(false);
            switchRole('citizen'); // Default
        });

        return unsubscribe;
    }, []);

    const switchRole = (newRole) => {
        setRole(newRole);
        if (newRole === 'owner') {
            setCurrentUser({ id: 'OWNER_001', name: 'Ramesh Kulkarni', email: 'ramesh@owner.com' });
        } else if (newRole === 'admin') {
            setCurrentUser({ id: 'ADMIN_001', name: 'SMC Admin', email: 'admin@solapurmc.gov.in' });
        } else if (newRole === 'citizen') {
            setCurrentUser({ id: 'DRIVER_001', name: 'Anil Sharma', email: 'anil@driver.com' });
        } else {
            setCurrentUser({ id: 'STAFF_001', name: 'Staff User', email: 'staff@example.com' });
        }
        console.log(`Switched to role: ${newRole} with user:`, newRole);
    };

    const value = {
        currentUser,
        role,
        switchRole
    };

    return (
        <AuthContext.Provider value={value}>
            {!loading && children}
        </AuthContext.Provider>
    );
}
