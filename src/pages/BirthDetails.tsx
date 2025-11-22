import { useNavigate } from 'react-router-dom';
import { BirthDetailWizard, type BirthDetails } from '@/components/BirthDetailWizard';
import { birthDetails } from '@/lib/api';
import { useState } from 'react';

export const BirthDetails = () => {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  const handleComplete = async (details: BirthDetails) => {
    try {
      setError(null);
      
      // Check if user is authenticated
      const token = localStorage.getItem('token');
      if (!token || token === 'undefined' || token === 'null') {
        setError('Please login first to submit birth details');
        navigate('/login');
        return;
      }
      
      await birthDetails.submit({
        name: details.name,
        gender: details.gender,
        dob: details.dob,
        birthTime: details.birthTime,
        birthPlace: details.birthPlace,
        latitude: details.latitude,
        longitude: details.longitude,
        relationshipStatus: details.relationshipStatus,
        employmentStatus: details.employmentStatus,
      });
      
      localStorage.setItem('birthDetails', JSON.stringify(details));
      setTimeout(() => {
        navigate('/chat');
      }, 300);
    } catch (err: any) {
      if (err.code === 'ERR_NETWORK') {
        setError('Cannot connect to server. Please ensure the backend is running on http://localhost:5000');
      } else if (err.response?.status === 401) {
        setError('Authentication failed. Please login again.');
        setTimeout(() => navigate('/login'), 2000);
      } else {
        setError(err?.response?.data?.error || err?.message || 'Failed to submit birth details');
      }
    }
  };

  return (
    <div className="animate-in fade-in duration-500">
      {error && (
        <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 max-w-md w-full mx-4">
          <div className="p-4 bg-red-500/20 border border-red-500/40 rounded-lg text-red-300 text-sm shadow-lg backdrop-blur-sm">
            <div className="flex items-start gap-3">
              <span className="text-xl">⚠️</span>
              <div>
                <p className="font-semibold mb-1">Error</p>
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}
      <BirthDetailWizard onComplete={handleComplete} />
    </div>
  );
};
