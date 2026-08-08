import { useEffect } from 'react';
import { useLocation } from 'react-router';
import HeroSection from '@/sections/HeroSection';
import CinemaSection from '@/sections/CinemaSection';
import FeaturesSection from '@/sections/FeaturesSection';
import InnovationSection from '@/sections/InnovationSection';
import SolutionsSection from '@/sections/SolutionsSection';
import FoundationSection from '@/sections/FoundationSection';
import ChatExperienceSection from '@/sections/ChatExperienceSection';
import ArchitectureSection from '@/sections/ArchitectureSection';
import SecuritySection from '@/sections/SecuritySection';

export default function HomePage() {
  const location = useLocation();

  useEffect(() => {
    if (location.hash) {
      const id = location.hash.slice(1);
      const el = document.getElementById(id);
      if (el) {
        setTimeout(() => {
          el.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      }
    }
  }, [location]);

  return (
    <main>
      <HeroSection />
      <CinemaSection />
      <FeaturesSection />
      <InnovationSection />
      <SolutionsSection />
      <FoundationSection />
      <ChatExperienceSection />
      <ArchitectureSection />
      <SecuritySection />
    </main>
  );
}
