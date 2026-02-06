// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyA4QbIr-ySNWQYFXtGFIkgOxf2o5BjCK2I",
  authDomain: "trafficmanagementsystem-e8b34.firebaseapp.com",
  projectId: "trafficmanagementsystem-e8b34",
  storageBucket: "trafficmanagementsystem-e8b34.firebasestorage.app",
  messagingSenderId: "975508489149",
  appId: "1:975508489149:web:ce04250e7dd03470d8c8d4",
  measurementId: "G-3DWBSYVSZ0"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);