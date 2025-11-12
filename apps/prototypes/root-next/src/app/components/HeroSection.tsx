'use client';

import Image from 'next/image';

export default function HeroSection() {
  return (
    <section className="relative h-screen">
      <div className="absolute inset-0">
        <Image
          src="/images/Community Section.png"
          alt="Hero Background"
          fill
          className="object-cover"
          priority
        />
      </div>
      <div className="absolute inset-0 bg-black/50" />
      <div className="relative z-10 h-full flex flex-col justify-center px-4">
        <div className="max-w-6xl mx-auto w-full">
          <div className="space-y-4">
            <div className="space-y-2">
              <p className="text-gray-400">규준한</p>
              <p className="text-gray-400">운동 라이프</p>
            </div>
            <h1 className="text-6xl font-bold text-white">
              Lagom Training
            </h1>
            <div className="flex items-center gap-2 mt-8">
              <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
              <p className="text-white">혼자 하면 지치지만</p>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
              <p className="text-white">함께하면 지속할 수 있다</p>
            </div>
            <div className="absolute bottom-32 right-32 flex items-center">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-white" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                </svg>
              </div>
              <span className="text-white ml-2">강남점</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
} 