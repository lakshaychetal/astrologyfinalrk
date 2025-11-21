import { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowRight, ChevronLeft } from 'lucide-react';
import { CosmicBackground } from '@/components/CosmicBackground';
import { PlanetOrbit } from '@/components/PlanetOrbit';

export interface BirthDetails {
  name: string;
  gender: string;
  dob: string;
  birthTime: string;
  birthPlace: string;
  relationshipStatus: string;
  employmentStatus: string;
}

const genders = ['Female', 'Male', 'Non-binary', 'Prefer not to say'];
const relationshipOptions = ['Single', 'Married', 'Partnered', 'In transition'];
const employmentOptions = ['Employed', 'Self-employed', 'Founder', 'Student', 'Creator'];

const stepMeta = [
  { title: 'Identity', subtitle: 'Your name and gender', hint: 'This lets the chart call you by name.' },
  { title: 'Date of birth', subtitle: 'Precise day on the wheel', hint: 'Use the calendar to lock the right date.' },
  { title: 'Time of birth', subtitle: 'Exact hour the planets watched', hint: 'Even an approximate time keeps your map sharp.' },
  { title: 'Place of birth', subtitle: 'Where you entered the world', hint: 'City, town, or metro is fine.' },
  { title: 'Relationship status', subtitle: 'Single, married, unbound, etc.', hint: 'Choose the label that feels most honest.' },
  { title: 'Work mode', subtitle: 'Employment or vocation', hint: 'Skip the title—just your mode.' },
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
    relationshipStatus: '',
    employmentStatus: '',
  });
  const [locationQuery, setLocationQuery] = useState('');
  const [locationSuggestions, setLocationSuggestions] = useState<string[]>([]);
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
      setLocationError('Geoapify API key is missing. Set VITE_GEOAPIFY_API_KEY.');
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
          ? (data.features as { properties?: { formatted?: string } }[])
          : [];
        const formatted = features
          .map((feature) => feature.properties?.formatted)
          .filter((value): value is string => typeof value === 'string' && value.length > 0);
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
    const inputClass =
      'mt-2 w-full rounded-[24px] border border-white/20 bg-white/5 px-4 py-3 text-lg font-semibold text-white placeholder:text-white/40 outline-none focus:border-white/60';

    switch (step) {
      case 0:
        return (
          <div className="space-y-6">
            <div>
              <label className="text-[0.65rem] uppercase tracking-[0.4em] text-white/50" htmlFor="name-input">
                Full name
              </label>
              <input
                id="name-input"
                type="text"
                placeholder="Aanya Kapoor"
                value={details.name}
                onChange={(e) => setDetails((prev) => ({ ...prev, name: e.target.value }))}
                className={inputClass}
              />
            </div>

            <div>
              <p className="text-[0.65rem] uppercase tracking-[0.4em] text-white/50">Gender</p>
              <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
                {genders.map((option) => (
                  <button
                    key={option}
                    type="button"
                    onClick={() => setDetails((prev) => ({ ...prev, gender: option }))}
                    className={`rounded-2xl border px-4 py-3 text-sm font-semibold transition focus-visible:outline-none ${
                      details.gender === option
                        ? 'border-white bg-white text-black'
                        : 'border-white/20 bg-white/5 text-white/70'
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
          <div className="space-y-4">
            <p className="text-sm text-white/60">Select the date you were born.</p>
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
          <div className="space-y-4">
            <p className="text-sm text-white/60">Hour and minute of your birth give the chart its contours.</p>
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
          <div className="space-y-4">
            <p className="text-sm text-white/60">City, town, or metro area of birth.</p>
            <div className="relative">
              <input
                type="text"
                placeholder="Mumbai, India"
                value={details.birthPlace}
                onChange={(e) => {
                  setDetails((prev) => ({ ...prev, birthPlace: e.target.value }));
                  setLocationQuery(e.target.value);
                }}
                className={inputClass}
              />
              {(locationLoading || locationSuggestions.length > 0 || locationError) && (
                <div className="absolute top-full mt-2 w-full rounded-[20px] border border-white/10 bg-black/70 p-3 shadow-[0_20px_40px_rgba(0,0,0,0.7)]">
                  {locationLoading && <p className="text-xs text-white/60">Looking up locations…</p>}
                  {locationError && <p className="text-xs text-rose-300">{locationError}</p>}
                  {!locationLoading && locationSuggestions.length > 0 && (
                    <ul className="space-y-2">
                      {locationSuggestions.map((location) => (
                        <li key={location}>
                          <button
                            type="button"
                            onMouseDown={() => {
                              setDetails((prev) => ({ ...prev, birthPlace: location }));
                              setLocationSuggestions([]);
                            }}
                            className="w-full text-left text-sm text-white/80 transition hover:text-white"
                          >
                            {location}
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                  {!locationLoading && locationSuggestions.length === 0 && !locationError && locationQuery.length > 2 && (
                    <p className="text-xs text-white/50">No matching places yet.</p>
                  )}
                </div>
              )}
            </div>
          </div>
        );
      case 4:
        return (
          <div className="space-y-4">
            <p className="text-sm text-white/60">Status of the heart.</p>
            <div className="grid grid-cols-2 gap-3">
              {relationshipOptions.map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => setDetails((prev) => ({ ...prev, relationshipStatus: option }))}
                  className={`rounded-2xl border px-4 py-4 text-sm font-semibold transition ${
                    details.relationshipStatus === option
                      ? 'border-white bg-white text-black'
                      : 'border-white/20 bg-white/5 text-white/70'
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
          <div className="space-y-4">
            <p className="text-sm text-white/60">How you show up in your work.</p>
            <div className="grid grid-cols-2 gap-3">
              {employmentOptions.map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => setDetails((prev) => ({ ...prev, employmentStatus: option }))}
                  className={`rounded-2xl border px-4 py-4 text-sm font-semibold transition ${
                    details.employmentStatus === option
                      ? 'border-white bg-white text-black'
                      : 'border-white/20 bg-white/5 text-white/70'
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
    <div className="min-h-screen relative overflow-hidden bg-black text-white">
      <CosmicBackground />
      <div className="absolute inset-0 opacity-80 bg-gradient-to-br from-black via-slate-950 to-slate-900" aria-hidden />
      <div className="relative z-10 flex h-screen w-full flex-col gap-6 px-6 py-10 sm:px-10">
        <header className="flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-[0.6rem] uppercase tracking-[0.6em] text-white/40">Birth inputs</p>
            <div className="flex items-center gap-2 text-3xl font-semibold tracking-tight">
              <PlanetOrbit size="sm" className="text-white/70" />
              <span>Chart setup</span>
            </div>
          </div>
          <div className="text-right text-xs uppercase tracking-[0.6em] text-white/30">Step {step + 1} / {totalSteps}</div>
        </header>

  <div className="space-y-5 w-full rounded-[40px] border border-white/20 bg-black/60 p-8 shadow-[0_35px_120px_rgba(3,7,18,0.85)] backdrop-blur-3xl">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-semibold tracking-tight text-white">{currentMeta.title}</h1>
              <p className="text-sm uppercase tracking-[0.4em] text-white/50">{currentMeta.subtitle}</p>
            </div>
            <p className="text-sm text-white/40">Hint: {currentMeta.hint}</p>
          </div>

          <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
            <div className="h-full rounded-full bg-gradient-to-r from-rose-500 via-fuchsia-500 to-cyan-400" style={{ width: `${progress}%` }} />
          </div>

          <p className="text-xs uppercase tracking-[0.4em] text-white/40" aria-live="polite">
            {`Step ${step + 1} of ${totalSteps} — ${currentMeta.title}`}
          </p>

          <div className="rounded-[32px] border border-white/10 bg-black/60 p-8 shadow-[0_25px_60px_rgba(0,0,0,0.45)]">
            {renderStepContent()}
          </div>

          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={handleBack}
              disabled={step === 0}
              className="flex items-center gap-2 rounded-full border border-white/20 px-5 py-2 text-xs font-semibold uppercase tracking-[0.4em] text-white/40 transition disabled:opacity-40"
            >
              <ChevronLeft className="h-4 w-4" />
              Back
            </button>
            <button
              type="button"
              onClick={handleNext}
              disabled={!isStepValid}
              className="flex items-center gap-2 rounded-full bg-white/90 px-6 py-2 text-xs font-semibold uppercase tracking-[0.4em] text-slate-900 transition disabled:opacity-40"
            >
              {step === totalSteps - 1 ? 'Launch insights' : 'Continue'}
              <ArrowRight className="h-4 w-4 text-slate-900" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};