import { Routes, Route, useLocation } from 'react-router';
import Navigation from '@/components/Navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
import HomePage from '@/pages/HomePage';
import DocsPage from '@/pages/DocsPage';
import NewsPage from '@/pages/NewsPage';
import DownloadsPage from '@/pages/DownloadsPage';
import CommunityPage from '@/pages/CommunityPage';
import AuthPage from '@/pages/AuthPage';
import StudioPage from '@/pages/StudioPage';
import PodcastPage from '@/pages/PodcastPage';
import OpenHanakoPage from '@/pages/OpenHanakoPage';
import SharePage from '@/pages/SharePage';
import ProjectSharePage from '@/pages/ProjectSharePage';
import PricingPage from '@/pages/PricingPage';
import Footer from '@/sections/Footer';

export default function App() {
  const location = useLocation();
  const isStudio = location.pathname === '/studio';
  const isShare = location.pathname.startsWith('/share/');
  const isOpenHanako = location.pathname === '/openhanako';
  const hideFrame = isStudio || isShare || isOpenHanako;

  return (
    <div className="min-h-screen bg-laap-bg-primary text-laap-text-primary">
      {!hideFrame && <Navigation />}
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/docs" element={<DocsPage />} />
        <Route path="/docs/:slug" element={<DocsPage />} />
        <Route path="/news" element={<NewsPage />} />
        <Route path="/news/:id" element={<NewsPage />} />
        <Route path="/pricing" element={<PricingPage />} />
        <Route path="/downloads" element={<DownloadsPage />} />
        <Route path="/community" element={<CommunityPage />} />
        <Route path="/podcast" element={<PodcastPage />} />
        <Route path="/openhanako" element={<OpenHanakoPage />} />
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/login" element={<AuthPage />} />
        <Route path="/register" element={<AuthPage />} />
        <Route
          path="/studio"
          element={
            <ProtectedRoute>
              <StudioPage />
            </ProtectedRoute>
          }
        />
        <Route path="/share/:token" element={<SharePage />} />
        <Route path="/share/project/:token" element={<ProjectSharePage />} />
      </Routes>
      {!hideFrame && <Footer />}
    </div>
  );
}
