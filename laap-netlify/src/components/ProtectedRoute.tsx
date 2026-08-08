import { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router';
import { getCurrentUser } from '@/lib/auth';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const location = useLocation();
  const [authenticated, setAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    let mounted = true;

    async function verify() {
      // getCurrentUser will automatically sign in as a guest when no token exists.
      const user = await getCurrentUser();
      if (mounted) {
        setAuthenticated(!!user);
      }
    }

    verify();

    return () => {
      mounted = false;
    };
  }, [location.pathname]);

  if (authenticated === null) {
    return (
      <div className="min-h-screen bg-laap-bg-primary flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-laap-gold/30 border-t-laap-gold rounded-full animate-spin" />
      </div>
    );
  }

  if (!authenticated) {
    return <Navigate to="/auth" replace state={{ from: location }} />;
  }

  return <>{children}</>;
}
