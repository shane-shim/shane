'use client';

import Header from "./components/Header";
import HeroSection from "./components/HeroSection";
import TrainingSection from "./components/TrainingSection";
import CollaborationSection from "./components/CollaborationSection";
import LocationSection from "./components/LocationSection";
import Footer from "./components/Footer";

export default function Home() {
  return (
    <>
      <Header />
      <main>
        <HeroSection />
        <TrainingSection />
        <CollaborationSection />
        <LocationSection />
      </main>
      <Footer />
    </>
  );
} 