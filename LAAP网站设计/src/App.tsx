import Navigation from '@/components/Navigation';
import HeroSection from '@/sections/HeroSection';
import FeaturesSection from '@/sections/FeaturesSection';
import ChatExperienceSection from '@/sections/ChatExperienceSection';
import ArchitectureSection from '@/sections/ArchitectureSection';
import DocumentationSection from '@/sections/DocumentationSection';
import SecuritySection from '@/sections/SecuritySection';
import Footer from '@/sections/Footer';

export default function App() {
  return (
    <div className="min-h-screen bg-laap-bg-primary text-white">
      <Navigation />
      <main>
        <HeroSection />
        <FeaturesSection />
        <ChatExperienceSection />
        <ArchitectureSection />
        <DocumentationSection />
        <SecuritySection />
      </main>
      <Footer />
    </div>
  );
}
