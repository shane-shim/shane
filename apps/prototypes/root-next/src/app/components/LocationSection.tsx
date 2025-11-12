'use client';

import Image from 'next/image';

export default function LocationSection() {
  return (
    <section className="bg-black text-white py-20 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center gap-2 mb-8">
          <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
          <h2 className="text-2xl font-bold">Location</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <p className="text-lg">Address</p>
                <p className="text-gray-400">서울특별시 강남구 테헤란로 123</p>
              </div>
              <div className="flex items-center gap-4">
                <p className="text-lg">Subway</p>
                <p className="text-gray-400">2호선 강남역 4번 출구 도보 5분</p>
              </div>
              <div className="flex items-center gap-4">
                <p className="text-lg">Bus</p>
                <p className="text-gray-400">간선 146, 301, 342, 401</p>
              </div>
              <div className="flex items-center gap-4">
                <p className="text-lg">Parking</p>
                <p className="text-gray-400">건물 내 지하주차장 이용 가능</p>
              </div>
            </div>

            <div className="mt-12">
              <p className="text-lg mb-4">Operating Hours</p>
              <div className="space-y-2 text-gray-400">
                <p>평일: 06:00 - 23:00</p>
                <p>토요일: 09:00 - 18:00</p>
                <p>일요일: 10:00 - 17:00</p>
              </div>
            </div>
          </div>

          <div className="aspect-square relative">
            <Image
              src="/images/location-map.jpg"
              alt="Location Map"
              fill
              className="object-cover"
            />
          </div>
        </div>
      </div>
    </section>
  );
} 