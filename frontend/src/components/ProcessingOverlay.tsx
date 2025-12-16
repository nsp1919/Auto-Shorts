'use client';

import { useEffect, useState } from 'react';

interface ProcessingOverlayProps {
    isVisible: boolean;
    language?: string;
}

const steps = [
    { icon: '🎬', text: 'Loading video' },
    { icon: '🎧', text: 'Extracting audio' },
    { icon: '🧠', text: 'Understanding Telugu speech' },
    { icon: '✍️', text: 'Converting to Roman Telugu' },
    { icon: '🔥', text: 'Styling captions for virality' },
    { icon: '🚀', text: 'Rendering final short' },
];

const stepsEnglish = [
    { icon: '🎬', text: 'Loading video' },
    { icon: '🎧', text: 'Extracting audio' },
    { icon: '🧠', text: 'Understanding speech' },
    { icon: '✨', text: 'Generating captions' },
    { icon: '🔥', text: 'Styling for virality' },
    { icon: '🚀', text: 'Rendering final short' },
];

export default function ProcessingOverlay({ isVisible, language = 'en' }: ProcessingOverlayProps) {
    const [activeStep, setActiveStep] = useState(0);
    const [particles, setParticles] = useState<Array<{ id: number; x: number; y: number; size: number; delay: number }>>([]);

    const currentSteps = language === 'te' ? steps : stepsEnglish;

    // Cycle through steps
    useEffect(() => {
        if (!isVisible) {
            setActiveStep(0);
            return;
        }

        const interval = setInterval(() => {
            setActiveStep((prev) => (prev + 1) % currentSteps.length);
        }, 1500);

        return () => clearInterval(interval);
    }, [isVisible, currentSteps.length]);

    // Generate particles on mount
    useEffect(() => {
        const newParticles = Array.from({ length: 30 }, (_, i) => ({
            id: i,
            x: Math.random() * 100,
            y: Math.random() * 100,
            size: Math.random() * 4 + 2,
            delay: Math.random() * 5,
        }));
        setParticles(newParticles);
    }, []);

    if (!isVisible) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center overflow-hidden">
            {/* Gradient Background */}
            <div
                className="absolute inset-0"
                style={{
                    background: 'linear-gradient(135deg, #0a0a0a 0%, #1a0a2e 30%, #0a1628 70%, #0a0a0a 100%)',
                }}
            />

            {/* Animated gradient overlay */}
            <div
                className="absolute inset-0 opacity-30"
                style={{
                    background: 'radial-gradient(circle at 50% 50%, rgba(139, 92, 246, 0.3) 0%, transparent 50%)',
                    animation: 'pulse 4s ease-in-out infinite',
                }}
            />

            {/* Floating Particles */}
            {particles.map((particle) => (
                <div
                    key={particle.id}
                    className="absolute rounded-full bg-purple-500/30"
                    style={{
                        left: `${particle.x}%`,
                        top: `${particle.y}%`,
                        width: `${particle.size}px`,
                        height: `${particle.size}px`,
                        animation: `float ${8 + particle.delay}s ease-in-out infinite`,
                        animationDelay: `${particle.delay}s`,
                    }}
                />
            ))}

            {/* Sound Wave Animation */}
            <div className="absolute bottom-20 left-1/2 -translate-x-1/2 flex items-end gap-1">
                {Array.from({ length: 12 }).map((_, i) => (
                    <div
                        key={i}
                        className="w-1 bg-gradient-to-t from-purple-500 to-blue-500 rounded-full opacity-50"
                        style={{
                            height: '20px',
                            animation: `soundWave 1s ease-in-out infinite`,
                            animationDelay: `${i * 0.1}s`,
                        }}
                    />
                ))}
            </div>

            {/* Main Content */}
            <div className="relative z-10 flex flex-col items-center">
                {/* Title */}
                <h2
                    className="text-3xl font-bold text-white mb-12 tracking-wide"
                    style={{
                        animation: 'fadeInSlide 0.8s ease-out',
                        textShadow: '0 0 30px rgba(139, 92, 246, 0.5)',
                    }}
                >
                    Creating Your Viral Short
                </h2>

                {/* Step Timeline */}
                <div className="flex flex-col gap-4">
                    {currentSteps.map((step, index) => {
                        const isActive = index === activeStep;
                        const isCompleted = index < activeStep;

                        return (
                            <div
                                key={index}
                                className={`flex items-center gap-4 transition-all duration-500 ${isActive ? 'scale-110' : isCompleted ? 'opacity-50' : 'opacity-30'
                                    }`}
                                style={{
                                    animation: isActive ? 'fadeInSlide 0.5s ease-out' : undefined,
                                }}
                            >
                                {/* Timeline dot/line */}
                                <div className="relative flex flex-col items-center">
                                    <div
                                        className={`w-10 h-10 rounded-full flex items-center justify-center text-xl transition-all duration-300 ${isActive
                                                ? 'bg-gradient-to-br from-purple-500 to-blue-500 shadow-lg shadow-purple-500/50'
                                                : isCompleted
                                                    ? 'bg-green-500/50'
                                                    : 'bg-white/10'
                                            }`}
                                        style={{
                                            animation: isActive ? 'glow 2s ease-in-out infinite' : undefined,
                                        }}
                                    >
                                        {isCompleted ? '✓' : step.icon}
                                    </div>
                                    {index < currentSteps.length - 1 && (
                                        <div
                                            className={`w-0.5 h-6 ${isCompleted ? 'bg-green-500/50' : 'bg-white/10'
                                                }`}
                                        />
                                    )}
                                </div>

                                {/* Step text */}
                                <span
                                    className={`text-lg font-medium transition-all duration-300 ${isActive ? 'text-white' : 'text-white/60'
                                        }`}
                                    style={{
                                        textShadow: isActive ? '0 0 20px rgba(139, 92, 246, 0.8)' : undefined,
                                    }}
                                >
                                    {step.text}
                                </span>

                                {/* Active indicator */}
                                {isActive && (
                                    <div className="flex gap-1">
                                        <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0s' }} />
                                        <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                                        <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>

                {/* Subtext */}
                <p className="mt-12 text-white/50 text-sm animate-pulse">
                    This may take a minute...
                </p>
            </div>

            {/* CSS Animations */}
            <style jsx>{`
                @keyframes float {
                    0%, 100% { transform: translateY(0) translateX(0); }
                    25% { transform: translateY(-20px) translateX(10px); }
                    50% { transform: translateY(-10px) translateX(-10px); }
                    75% { transform: translateY(-30px) translateX(5px); }
                }

                @keyframes glow {
                    0%, 100% { box-shadow: 0 0 20px rgba(139, 92, 246, 0.5); }
                    50% { box-shadow: 0 0 40px rgba(139, 92, 246, 0.8), 0 0 60px rgba(59, 130, 246, 0.5); }
                }

                @keyframes fadeInSlide {
                    from {
                        opacity: 0;
                        transform: translateY(20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                @keyframes soundWave {
                    0%, 100% { height: 10px; }
                    50% { height: 40px; }
                }

                @keyframes pulse {
                    0%, 100% { opacity: 0.3; transform: scale(1); }
                    50% { opacity: 0.5; transform: scale(1.1); }
                }
            `}</style>
        </div>
    );
}
