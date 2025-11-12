'use client';

import Image from 'next/image';

export default function TrainingSection() {
  return (
    <section className="bg-black text-white py-20 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center gap-2 mb-8">
          <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
          <h2 className="text-2xl font-bold">Training</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="space-y-4">
            <div className="aspect-square relative">
              <Image
                src="/images/training-1.jpg"
                alt="Training 1"
                fill
                className="object-cover"
              />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-bold">Personal Training</h3>
              <p className="text-gray-400">1:1 맞춤형 트레이닝으로 목표를 달성하세요</p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="aspect-square relative">
              <Image
                src="/images/training-2.jpg"
                alt="Training 2"
                fill
                className="object-cover"
              />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-bold">Group Training</h3>
              <p className="text-gray-400">함께하는 즐거움을 느껴보세요</p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="aspect-square relative">
              <Image
                src="/images/training-3.jpg"
                alt="Training 3"
                fill
                className="object-cover"
              />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-bold">Online Training</h3>
              <p className="text-gray-400">언제 어디서나 전문가와 함께하세요</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
} 