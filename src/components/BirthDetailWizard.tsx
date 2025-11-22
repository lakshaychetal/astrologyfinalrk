import { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowRight, ChevronLeft } from 'lucide-react';
import { CosmicBackground } from '@/components/CosmicBackground';

export interface BirthDetails {
  name: string;
  gender: string;
  dob: string;
  birthTime: string;
  birthPlace: string;
  latitude: number;
  longitude: number;
  relationshipStatus: string;
  employmentStatus: string;
}

const genders = ['Female', 'Male', 'Non-binary', 'Prefer not to say'];
const relationshipOptions = ['Single', 'Married', 'Partnered', 'In transition'];
const employmentOptions = ['Employed', 'Self-employed', 'Founder', 'Student', 'Creator'];

const stepMeta = [
  { title: 'Your Name', subtitle: 'What should we call you?' },
  { title: 'Date of Birth', subtitle: 'When were you born?' },
  { title: 'Birth Time', subtitle: 'What time were you born?' },
  { title: 'Birth Place', subtitle: 'Where were you born?' },
  { title: 'Relationship', subtitle: 'Your current relationship status' },
  { title: 'Employment', subtitle: 'Your current work status' },
];

export const BirthDetailWizard = ({
  onComplete,
}: {
  onComplete: (details: BirthDetails) => void;
}) => {
  const totalSteps = stepMeta.length;
  const [step, setStep] = useState(0);
  const [details, setDetails] = useState<BirthDetails>({
    name: '',
    gender: '',
    dob: '',
    birthTime: '',
    birthPlace: '',
    latitude: 0,
    longitude: 0,
    relationshipStatus: '',
    employmentStatus: '',
  });
  const [locationQuery, setLocationQuery] = useState('');
  const [locationSuggestions, setLocationSuggestions] = useState<Array<{ name: string; lat: number; lon: number }>>([]);
  const [locationLoading, setLocationLoading] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (step !== 3) {
      setLocationSuggestions([]);
      setLocationError(null);
      return;
    }

    if (locationQuery.trim().length < 3) {
      setLocationSuggestions([]);
      setLocationError(null);
      return;
    }

    const key = import.meta.env.VITE_GEOAPIFY_API_KEY;
    if (!key) {
      setLocationSuggestions([]);
      setLocationError('Geoapify API key is missing.');
      return;
    }

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(async () => {
      if (abortRef.current) {
        abortRef.current.abort();
      }
      const controller = new AbortController();
      abortRef.current = controller;
      setLocationLoading(true);
      setLocationError(null);

      try {
        const response = await fetch(
          `https://api.geoapify.com/v1/geocode/search?text=${encodeURIComponent(locationQuery)}&limit=5&apiKey=${key}`,
          { signal: controller.signal }
        );
        if (!response.ok) {
          throw new Error('Unable to fetch locations');
        }
        const data = await response.json();
        const features = Array.isArray(data.features)
          ? (data.features as { properties?: { formatted?: string; lat?: number; lon?: number } }[])
          : [];
        const formatted = features
          .map((feature) => ({
            name: feature.properties?.formatted || '',
            lat: feature.properties?.lat || 0,
            lon: feature.properties?.lon || 0,
          }))
          .filter((item) => item.name.length > 0);
        setLocationSuggestions(formatted);
      } catch (error) {
        if ((error as DOMException).name === 'AbortError') {
          return;
        }
        setLocationSuggestions([]);
        setLocationError('Failed to fetch places.');
      } finally {
        setLocationLoading(false);
      }
    }, 400);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
      if (abortRef.current) {
        abortRef.current.abort();
      }
    };
  }, [locationQuery, step]);

  const currentMeta = stepMeta[step];
  const progress = ((step + 1) / totalSteps) * 100;

  const isStepValid = useMemo(() => {
    switch (step) {
      case 0:
        return details.name.trim().length >= 2 && Boolean(details.gender);
      case 1:
        return Boolean(details.dob);
      case 2:
        return Boolean(details.birthTime);
      case 3:
        return details.birthPlace.trim().length >= 3;
      case 4:
        return Boolean(details.relationshipStatus);
      case 5:
        return Boolean(details.employmentStatus);
      default:
        return false;
    }
  }, [details, step]);

  const handleNext = () => {
    if (!isStepValid) return;
    if (step === totalSteps - 1) {
      onComplete(details);
      return;
    }
    setStep((prev) => prev + 1);
  };

  const handleBack = () => {
    if (step === 0) return;
    setStep((prev) => prev - 1);
  };

  const renderStepContent = () => {
    const inputClass = 'w-full rounded-lg border border-white/20 bg-white/5 px-4 py-3 text-white placeholder:text-white/40 outline-none focus:border-white/50 transition-all';

    switch (step) {
      case 0:
        return (
          <div className="space-y-5">
            <div>
              <label className="text-sm text-white/60 mb-2 block">Full name</label>
              <input
                type="text"
                placeholder="Enter your name"
                value={details.name}
                onChange={(e) => setDetails((prev) => ({ ...prev, name: e.target.value }))}
                className={inputClass}
              />
            </div>

            <div>
              <p className="text-sm text-white/60 mb-3">Gender</p>
              <div className="grid grid-cols-2 gap-2">
                {genders.map((option) => (
                  <button
                    key={option}
                    type="button"
                    onClick={() => setDetails((prev) => ({ ...prev, gender: option }))}
                    className={`rounded-lg border px-4 py-3 text-sm transition-all ${
                      details.gender === option
                        ? 'border-white bg-white text-black'
                        : 'border-white/20 bg-white/5 text-white hover:bg-white/10'
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>
          </div>
        );
      case 1:
        return (
          <div>
            <p className="text-sm text-white/60 mb-3">Date of birth</p>
            <input
              type="date"
              value={details.dob}
              onChange={(e) => setDetails((prev) => ({ ...prev, dob: e.target.value }))}
              className={inputClass}
            />
          </div>
        );
      case 2:
        return (
          <div>
            <p className="text-sm text-white/60 mb-3">Time of birth</p>
            <input
              type="time"
              value={details.birthTime}
              onChange={(e) => setDetails((prev) => ({ ...prev, birthTime: e.target.value }))}
              className={inputClass}
            />
          </div>
        );
      case 3:
        return (
          <div>
            <p className="text-sm text-white/60 mb-3">Place of birth</p>
            <div className="relative">
              <input
                type="text"
                placeholder="City, Country"
                value={details.birthPlace}
                onChange={(e) => {
                  setDetails((prev) => ({ ...prev, birthPlace: e.target.value }));
                  setLocationQuery(e.target.value);
                }}
                className={inputClass}
              />
              {(locationLoading || locationSuggestions.length > 0 || locationError) && (
                <div className="absolute top-full mt-2 w-full rounded-lg border border-white/20 bg-black/95 p-3 shadow-xl z-10">
                  {locationLoading && <p className="text-sm text-white/60">Searching...</p>}
                  {locationError && <p className="text-sm text-red-400">{locationError}</p>}
                  {!locationLoading && locationSuggestions.length > 0 && (
                    <ul className="space-y-1">
                      {locationSuggestions.map((location) => (
                        <li key={location.name}>
                          <button
                            type="button"
                            onMouseDown={() => {
                              setDetails((prev) => ({ 
                                ...prev, 
                                birthPlace: location.name,
                                latitude: location.lat,
                                longitude: location.lon,
                              }));
                              setLocationSuggestions([]);
                            }}
                            className="w-full text-left rounded px-3 py-2 text-sm text-white/80 hover:bg-white/10 transition-all"
                          >
                            {location.name}
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          </div>
        );
      case 4:
        return (
          <div>
            <p className="text-sm text-white/60 mb-3">Relationship status</p>
            <div className="grid grid-cols-2 gap-2">
              {relationshipOptions.map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => setDetails((prev) => ({ ...prev, relationshipStatus: option }))}
                  className={`rounded-lg border px-4 py-3 text-sm transition-all ${
                    details.relationshipStatus === option
                      ? 'border-white bg-white text-black'
                      : 'border-white/20 bg-white/5 text-white hover:bg-white/10'
                  }`}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>
        );
      case 5:
        return (
          <div>
            <p className="text-sm text-white/60 mb-3">Employment status</p>
            <div className="grid grid-cols-2 gap-2">
              {employmentOptions.map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => setDetails((prev) => ({ ...prev, employmentStatus: option }))}
                  className={`rounded-lg border px-4 py-3 text-sm transition-all ${
                    details.employmentStatus === option
                      ? 'border-white bg-white text-black'
                      : 'border-white/20 bg-white/5 text-white hover:bg-white/10'
                  }`}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-black text-white">
      <CosmicBackground />
      <div className="relative z-10 min-h-screen flex items-center justify-center px-4 py-8">
        <div className="w-full max-w-2xl">
          <div className="mb-6 text-center">
            <p className="text-xs uppercase tracking-wider text-white/50 mb-2">Step {step + 1} of {totalSteps}</p>
            <h1 className="text-3xl sm:text-4xl font-bold text-white mb-2">{currentMeta.title}</h1>
            <p className="text-sm text-white/60">{currentMeta.subtitle}</p>
          </div>

          <div className="mb-6">
            <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500" 
                style={{ width: `${progress}%` }} 
              />
            </div>
          </div>

          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-6 sm:p-8">
            {renderStepContent()}

            <div className="flex items-center justify-between gap-4 mt-8 pt-6 border-t border-white/10">
              <button
                type="button"
                onClick={handleBack}
                disabled={step === 0}
                className="flex items-center gap-2 px-6 py-2.5 rounded-full border border-white/20 bg-white/5 text-sm text-white/70 hover:text-white hover:bg-white/10 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-4 w-4" />
                Back
              </button>
              <button
                type="button"
                onClick={handleNext}
                disabled={!isStepValid}
                className="flex items-center gap-2 px-8 py-2.5 rounded-full bg-white text-sm font-semibold text-black hover:bg-white/90 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {step === totalSteps - 1 ? 'Complete' : 'Continue'}
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
